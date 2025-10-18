
/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2018, 2019, 2020, 2021
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Andreea Anghel
 *                Celestine Duenner
 *                Thomas Parnell
 *                Nikolas Ioannou
 *                Milos Stanisavljevic
 *                Jan van Lunteren
 *
 * End Copyright
 ********************************************************************/

#ifndef TREE_ENSEMBLE_MODEL
#define TREE_ENSEMBLE_MODEL

#include "Model.hpp"
#include "TreeModel.hpp"
#include "TreePredictor.hpp"
#include "ModelImport.hpp"

namespace tree {

struct TreeEnsembleModel : public Model {

public:
    TreeEnsembleModel(snapml::task_t task_, uint32_t num_classes_)
        : task(task_)
        , num_classes(num_classes_)
    {
    }

    TreeEnsembleModel() { }

    uint32_t get_num_trees() { return trees.size(); }

    void insert_tree(const std::shared_ptr<TreeModel> tree)
    {
        assert(tree->task == task);
        assert(tree->num_classes == num_classes);
        trees.push_back(tree);
        predictors_.push_back(std::make_shared<TreePredictor>(tree));
    }

    void resize(uint32_t size)
    {
        trees.resize(size);
        predictors_.resize(size);
    }

    void import(const std::shared_ptr<ModelImport> parser, uint32_t num_subsets, uint32_t subset_index)
    {

        uint32_t num_trees = parser->get_num_trees() / num_subsets;

        for (uint32_t k = 0; k < num_trees; k++) {
            uint32_t i = k + subset_index * num_trees;

            uint32_t num_nodes = parser->get_num_nodes(i);
            auto     tree      = std::make_shared<TreeModel>(task, num_classes, num_nodes);

            std::vector<float>*              node_threshold   = parser->get_node_threshold(i);
            std::vector<uint32_t>*           node_feature     = parser->get_node_feature(i);
            std::vector<bool>*               node_is_leaf     = parser->get_node_is_leaf(i);
            std::vector<uint32_t>*           node_left_child  = parser->get_node_left_child(i);
            std::vector<uint32_t>*           node_right_child = parser->get_node_right_child(i);
            std::vector<std::vector<float>>* node_leaf_label  = parser->get_node_leaf_label(i);

            for (uint32_t j = 0; j < num_nodes; j++) {
                tree->nodes[j].threshold = (*node_threshold)[j];
                tree->nodes[j].feature   = (*node_feature)[j];
                tree->nodes[j].is_leaf   = (*node_is_leaf)[j];
                if (tree->nodes[j].is_leaf) {
                    tree->num_leaves++;
                    if (num_classes <= 2) {
                        tree->nodes[j].leaf_label = (*node_leaf_label)[j][0];
                        tree->nodes[j].leaf_proba = nullptr;
                    } else {
                        tree->nodes[j].leaf_label = 0.0;
                        tree->nodes[j].leaf_proba = new float[num_classes - 1];
                        for (uint32_t k = 0; k < num_classes - 1; k++)
                            tree->nodes[j].leaf_proba[k] = (*node_leaf_label)[j][k];
                    }
                } else {
                    tree->nodes[j].left_child  = (*node_left_child)[j];
                    tree->nodes[j].right_child = (*node_right_child)[j];
                }
            }

            trees.push_back(tree);
            predictors_.push_back(std::make_shared<TreePredictor>(tree));
        }
    }

    void get(tree::Model::Getter& getter) override
    {
        getter.add(task);
        getter.add(num_classes);

        uint64_t num_trees = trees.size();
        getter.add(num_trees);

        std::vector<std::vector<uint8_t>> vec = {};

        for (uint32_t i = 0; i < num_trees; i++) {
            vec.push_back({});
            tree::Model::Getter m_getter(vec[i]);
            trees[i]->get(m_getter);
            getter.add(m_getter.size());
        }

        for (uint32_t i = 0; i < num_trees; i++) {
            getter.add(vec[i]);
        }
    }

    void put(tree::Model::Setter& setter, const uint64_t len) override
    {
        const uint64_t offset_begin = setter.get_offset();

        setter.check_before(len);

        setter.get(&task);
        setter.get(&num_classes);

        uint64_t num_trees;
        setter.get(&num_trees);

        std::vector<uint64_t> tree_sizes(num_trees);
        setter.get(tree_sizes.data(), num_trees * sizeof(uint64_t));

        for (uint32_t i = 0; i < num_trees; i++) {
            auto tree = std::make_shared<TreeModel>();
            tree->put(setter, tree_sizes[i]);
            insert_tree(tree);
        }

        setter.check_after(offset_begin, len);
    }

    void aggregate(glm::DenseDataset* data, double* preds, bool prob, uint32_t num_threads = 1) const
    {
        aggregate_impl(data, preds, prob, num_threads);
    }

    void apply(glm::DenseDataset* data, const uint32_t ex, const uint32_t tree_idx, uint32_t& leaf_idx,
               float& leaf_lab) const
    {
        apply_impl(data, ex, tree_idx, leaf_idx, leaf_lab);
    }

    snapml::task_t                          task;
    uint32_t                                num_classes;
    std::vector<std::shared_ptr<TreeModel>> trees;

private:
    std::vector<std::shared_ptr<TreePredictor>> predictors_;

    void apply_impl(glm::DenseDataset* data, const uint32_t ex, const uint32_t tree_idx, uint32_t& leaf_idx,
                    float& leaf_label) const
    {
        if (tree_idx < predictors_.size()) {
            predictors_[tree_idx]->apply(data, ex, leaf_idx, leaf_label);
        } else {
            throw std::runtime_error("Invalid tree index.");
        }
    }

    void aggregate_impl(glm::DenseDataset* data, double* preds, bool prob, uint32_t num_threads = 1) const
    {

        uint32_t num_extra_classes        = num_classes - 1;
        uint32_t n_trees                  = trees.size();
        uint32_t num_ex                   = data->get_num_ex();
        uint32_t num_returned_pred_values = num_ex * num_extra_classes;

        omp_set_num_threads(num_threads);

        // single-record inference
        if (num_ex == 1) {

            // are there enough trees to warrant parallelism?
            if (n_trees >= num_threads) {

                // parallel over trees (single-example)

                OMP::parallel([this, &num_extra_classes, &n_trees, &prob, &data, &preds](std::exception_ptr& eptr) {
                    std::vector<double> preds_private(num_extra_classes, 0.0);
                    OMP::_for_nowait<int32_t>(0, n_trees, eptr, [&](int32_t tree) {
                        if (prob) {
                            predictors_[tree]->predict_proba(data, 0, &preds_private[0]);
                        } else {
                            predictors_[tree]->predict(data, 0, &preds_private[0]);
                        }
                    });
                    OMP::critical([&]() {
                        for (int32_t i = 0; i < num_extra_classes; i++) {
                            preds[i] += preds_private[i];
                        }
                        // is this really needed??
                        std::vector<double>().swap(preds_private);
                    });
                });

            } else {

                // no parallelism (single-example)
                for (auto const& p : predictors_) {
                    if (prob) {
                        p->predict_proba(data, 0, &preds[0]);
                    } else {
                        p->predict(data, 0, &preds[0]);
                    }
                }
            }

        } else if (n_trees >= num_threads && num_threads > 1) {

            // parallel over trees (multi-example)
            OMP::parallel(
                [this, &num_returned_pred_values, &n_trees, &num_ex, &prob, &data, &preds](std::exception_ptr& eptr) {
                    std::vector<double> preds_private(num_returned_pred_values, 0.0);
                    OMP::_for_nowait<int32_t>(0, n_trees, eptr, [&](int32_t tree) {
                        for (int32_t ex = 0; ex < num_ex; ex++) {
                            if (prob) {
                                predictors_[tree]->predict_proba(data, ex, &preds_private[0]);
                            } else {
                                predictors_[tree]->predict(data, ex, &preds_private[0]);
                            }
                        }
                    });
                    OMP::critical([&]() {
                        for (int32_t i = 0; i < num_returned_pred_values; i++) {
                            preds[i] += preds_private[i];
                        }
                        // is this really needed??
                        std::vector<double>().swap(preds_private);
                    });
                });

        } else if (num_ex >= num_threads && num_threads > 1) {
            // parallel over examples
            OMP::parallel_for<int32_t>(0, num_ex, [this, &preds, &data, n_trees, prob](const int32_t& ex) {
                for (int32_t tree = 0; tree < n_trees; tree++) {
                    if (prob) {
                        predictors_[tree]->predict_proba(data, ex, &preds[0]);
                    } else {
                        predictors_[tree]->predict(data, ex, &preds[0]);
                    }
                }
            });
        } else {
            // no parallelism (multi-example)
            for (int32_t tree = 0; tree < n_trees; tree++) {
                for (int32_t ex = 0; ex < num_ex; ex++) {
                    if (prob) {
                        predictors_[tree]->predict_proba(data, ex, &preds[0]);
                    } else {
                        predictors_[tree]->predict(data, ex, &preds[0]);
                    }
                }
            }
        }
    }
};

}

#endif
