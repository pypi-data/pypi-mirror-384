/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2018, 2020, 2021
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Celestine Duenner
 *                Andreea Anghel
 *                Thomas Parnell
 *                Nikolas Ioannou
 *                Nikolaos Papandreou
 *                Milos Stanisavljevic
 *
 * End Copyright
 ********************************************************************/

#ifndef TREE_PREDICTOR
#define TREE_PREDICTOR

#include <thread>

#include "Predictor.hpp"
#include "TreeModel.hpp"
#include "DenseDatasetInt.hpp"

namespace tree {

class TreePredictor : public Predictor {

public:
    TreePredictor(const std::shared_ptr<TreeModel> model)
        : model_(model)
    {
    }

    ~TreePredictor() { }

    void predict(glm::DenseDataset* const data, double* const preds, uint32_t num_threads = 1) const override
    {
        predict_impl(data, preds, false, num_threads);
    }

    void predict_proba(glm::DenseDataset* const data, double* const preds, uint32_t num_threads = 1) const override
    {
        predict_impl(data, preds, true, num_threads);
    }

    template <class T> void predict(glm::DenseDataset* const data, const uint32_t ex, T* const preds) const
    {
        if (model_->task == snapml::task_t::regression) {
            predict_impl(data, ex, &preds[ex], false);
        } else {

            if (model_->num_classes == 2) {
                predict_impl(data, ex, &preds[ex], false);
                preds[ex] = preds[ex] > 0.5 ? +1.0 : -1.0;
            } else {

                std::vector<T> class_proba(model_->num_classes - 1);
                predict_impl(data, ex, class_proba.data(), true);

                uint32_t best_cls   = 0;
                T        best_proba = 0.0;
                T        proba_sum  = 0;
                for (uint32_t i = 0; i < model_->num_classes - 1; i++) {
                    if (class_proba[i] > best_proba) {
                        best_proba = class_proba[i];
                        best_cls   = i;
                    }
                    proba_sum += class_proba[i];
                }
                if ((1.0 - proba_sum) > best_proba) {
                    best_cls = model_->num_classes - 1;
                }
                preds[ex] = best_cls;
            }
        }
    }

    void apply(glm::DenseDataset* const data, const uint32_t ex, uint32_t& leaf_idx, float& leaf_label) const
    {

        const uint64_t pos = glm::DenseDataset::get_ex_pt(data->get_data(), ex);

        uint32_t idx = 0;

        const TreeModel::node_t* node = &model_->nodes[idx];

        while (!node->is_leaf) {

            const float val = glm::DenseDataset::lookup_w_pos(data->get_data(), ex, pos, node->feature);

            if (val < node->threshold)
                idx = node->left_child;
            else
                idx = node->right_child;

            node = &model_->nodes[idx];
        }

        leaf_idx   = idx;
        leaf_label = node->leaf_label;
    }

    template <class T> void predict_proba(glm::DenseDataset* const data, const uint32_t ex, T* const preds) const
    {

        assert(model_->task == snapml::task_t::classification);
        if (model_->num_classes > 2) {
            predict_impl(data, ex, &preds[ex * (model_->num_classes - 1)], true);
        } else {
            predict_impl(data, ex, &preds[ex], false);
        }
    }

private:
    const std::shared_ptr<TreeModel> model_;

    void predict_impl(glm::DenseDataset* const data, double* const preds, bool proba, uint32_t num_threads = 1) const
    {

        uint32_t num_ex  = data->get_num_ex();
        uint32_t num_out = proba ? num_ex * (model_->num_classes - 1) : num_ex;

        std::fill_n(preds, num_out, 0.0);

        if (num_threads == 0) {
            num_threads = std::thread::hardware_concurrency();
        }

        omp_set_num_threads(num_threads);

        OMP::parallel_for<int32_t>(0, num_ex, [this, &preds, &data, &proba](const int32_t& ex) {
            if (proba) {
                predict_proba(data, ex, preds);
            } else {
                predict(data, ex, preds);
            }
        });
    }

    template <class T>
    void predict_impl(glm::DenseDataset* const data, const uint32_t ex, T* const preds, bool proba) const
    {

        const uint64_t pos = glm::DenseDataset::get_ex_pt(data->get_data(), ex);

        const TreeModel::node_t* node = &model_->nodes[0];

        while (!node->is_leaf) {

            const float val = glm::DenseDataset::lookup_w_pos(data->get_data(), ex, pos, node->feature);

            if (val < node->threshold)
                node = &model_->nodes[node->left_child];
            else
                node = &model_->nodes[node->right_child];
        }

        if (proba) {
            for (uint32_t i = 0; i < model_->num_classes - 1; i++) {
                preds[i] += node->leaf_proba[i];
            }
        } else {
            preds[0] += node->leaf_label;
        }
    }
};

}

#endif