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

#ifndef TREE_BUILDER
#define TREE_BUILDER

#include "DecisionTreeParams.hpp"
#include "Builder.hpp"
#include "Dataset.hpp"
#include "TreeNode.hpp"
#include "TreePredictor.hpp"
#include "TreeInvariants.hpp"
#include <cmath>
#include <random>

namespace tree {

template <class N> class DecisionTreeBuilder : public Builder<TreeModel> {

public:
    typedef N node_type;

    // ctor without TreeInvariants (for standalone use)
    DecisionTreeBuilder<N>(glm::Dataset* data, snapml::DecisionTreeParams params)
        : Builder(data, params.num_classes)
        , params_(params)
        , tree_invariants_(std::make_shared<glm::TreeInvariants<glm::DenseDataset>>())
        , num_ex_effective_(0)
        , labs_(tree_invariants_->get_labs())
    {
        validate_parameters();
    }

    // ctor with TreeInvariants (for use within an ensemble)
    DecisionTreeBuilder<N>(glm::Dataset* data, snapml::DecisionTreeParams params,
                           const std::shared_ptr<glm::TreeInvariants<glm::DenseDataset>> tree_invariants)
        : Builder(data, params.num_classes)
        , params_(params)
        , tree_invariants_(tree_invariants)
        , num_ex_effective_(0)
        , labs_(tree_invariants_->get_labs())
    {
        validate_parameters();
    }

    // virtual dtor
    virtual ~DecisionTreeBuilder<N>() { }

    void init() override { init_impl(); }

    void build(const float* const sample_weight, const float* const sample_weight_val = nullptr,
               const double* const labels = nullptr) override
    {

        omp_set_num_threads(params_.n_threads);

#ifdef TIME_PROFILE
        CurTime t1, t2;
        if (omp_get_thread_num() == 0)
            t1 = Clock::now();
#endif

        if (labels) {
            labs_ = labels;
        } else {
            labs_ = tree_invariants_->get_labs();
        }

        build_tree_impl(sample_weight);

#ifdef TIME_PROFILE
        if (omp_get_thread_num() == 0) {
            t2            = Clock::now();
            auto   dur    = t2 - t1;
            double t_elap = (double)dur.count() / 1.0e9;
            printf("[DecisionTreeBuilder::build_tree] t_elap = %f\n", t_elap);
        }
#endif
    }

protected:
    virtual void build_tree_impl(const float* const sample_weight) = 0;
    virtual void init_invariants()                                 = 0;

    void validate_parameters()
    {

        max_depth_    = params_.max_depth;
        max_features_ = (params_.max_features == 0) ? num_ft_ : params_.max_features;

        if (params_.subsample < 0 || 1.0 < params_.subsample || params_.colsample_bytree < 0
            || 1.0 < params_.colsample_bytree) {
            throw std::runtime_error("invalid sample parameters given.");
        }

        if (params_.max_features != 0 && params_.subsample < 1.0) {
            throw std::runtime_error("only one of subsample or max_features parameter can be set.");
        }

        if (params_.bootstrap != 0 && params_.subsample < 1.0) {
            throw std::runtime_error("only one of subsample or bootstrap parameter can be set.");
        }

        if (params_.colsample_bytree < 1.0) {
            max_features_ = std::min(uint32_t(params_.colsample_bytree * num_ft_), num_ft_);
            max_features_ = std::max(1U, max_features_); // cannot be 0
        }

        subsample_size_ = std::min(num_ex_, uint32_t(params_.subsample * num_ex_));

        if (params_.task == snapml::task_t::classification) {
            if (params_.split_criterion != snapml::split_t::gini) {
                throw std::runtime_error("Valid splitting criteria for classification are: [gini]");
            }
        }

        if (params_.task == snapml::task_t::regression) {
            if (params_.split_criterion != snapml::split_t::mse) {
                throw std::runtime_error("Valid splitting criteria for regression are: [mse]");
            }
        }
    }

    void init_impl()
    {

        rng_ = std::mt19937(params_.random_state);

        omp_set_num_threads(params_.n_threads);

        // subsampling mode (boosting mode only TODO)
        if (subsample_size_ < data_->get_num_ex()) {

            indices_.resize(subsample_size_);

            std::vector<uint32_t> indices_subsampled(num_ex_);
            OMP::parallel_for<int32_t>(0, num_ex_,
                                       [&indices_subsampled](const int32_t& i) { indices_subsampled[i] = i; });
            // std::shuffle(indices_subsampled.begin(), indices_subsampled.end(), rng_);
            fisher_yates(indices_subsampled, rng_);

            OMP::parallel_for<int32_t>(0, indices_.size(), [this, &indices_subsampled](const int32_t& i) {
                indices_[i] = indices_subsampled[i];
            });
            std::sort(indices_.begin(), indices_.end());

        } else if (params_.bootstrap) {
            // bootstraping mode
            // the user should use either bootstrap or subsampling

            indices_.resize(num_ex_, 0);
            std::uniform_int_distribution<uint32_t> uniform_dist(0, num_ex_ - 1);
            // bootstrap sample of indices
            for (uint32_t i = 0; i < num_ex_; i++) {
                indices_[i] = uniform_dist(rng_);
            }
            std::sort(indices_.begin(), indices_.end());
        }

        fts_.resize(num_ft_);
        for (uint32_t ft = 0; ft < fts_.size(); ft++)
            fts_[ft] = ft;
        if (params_.colsample_bytree < 1.0) {
            fisher_yates(fts_, rng_);
            fts_.erase(fts_.begin() + max_features_, fts_.end());
            assert(max_features_ == fts_.size() && max_features_ <= num_ft_);
            fts_.shrink_to_fit();
        }

        // the effective number of examples used during training
        // it is required for subsampling in build_tree_impl_with_histograms
        num_ex_effective_ = (0 == indices_.size()) ? num_ex_ : indices_.size();

        if (!params_.tree_in_ensemble) {
            init_invariants();
        }
    }

    void create_model(const uint32_t num_nodes)
    {

        model_ = std::make_shared<TreeModel>(params_.task, num_classes_, num_nodes);

        create_tree(0);
    }

    void create_tree(const uint32_t node_index);

    const snapml::DecisionTreeParams                              params_;
    const std::shared_ptr<glm::TreeInvariants<glm::DenseDataset>> tree_invariants_;

    std::vector<N> node_info_;

    std::mt19937          rng_;
    std::vector<uint32_t> indices_;
    std::vector<uint32_t> fts_;

    uint32_t max_depth_;
    uint32_t max_features_;
    uint32_t subsample_size_;
    uint32_t num_ex_effective_;

    const double* labs_;
};

template <> inline void DecisionTreeBuilder<RegTreeNode>::create_tree(const uint32_t node_index)
{

    const uint32_t num_nodes = model_->num_nodes;

    const RegTreeNode* const p = reinterpret_cast<const RegTreeNode*>(&node_info_[node_index]);
    assert(node_index < num_nodes);

    TreeModel::node_t& node = model_->nodes[node_index];
    node.feature            = p->get_best_feature();
    node.threshold          = p->get_best_threshold();

    /* one node has 0 or 2 children, cannot have only 1 child */
    if (p->get_left_child() == -1) {
        node.is_leaf = true;
        node.feature = 0;
        double dw    = p->get_sum() / (p->get_wnum() + params_.lambda);
        if (params_.max_delta_step > 0.0) {
            if (std::abs(dw) > params_.max_delta_step)
                dw = std::copysign(params_.max_delta_step, dw);
        }
        node.leaf_label = dw;
        node.leaf_proba = nullptr;
        model_->num_leaves += node.is_leaf;
        return;
    }

    assert(-1 != p->get_right_child());
    node.is_leaf = false;
    assert((uint32_t)p->get_left_child() < num_nodes && (uint32_t)p->get_right_child() < num_nodes);
    node.left_child  = p->get_left_child();
    node.right_child = p->get_right_child();

    assert(-1 != p->get_best_feature());
    feature_importances_[p->get_best_feature()] -= p->get_best_score();

    DecisionTreeBuilder<RegTreeNode>::create_tree(p->get_left_child());
    DecisionTreeBuilder<RegTreeNode>::create_tree(p->get_right_child());
}

template <> inline void DecisionTreeBuilder<ClTreeNode>::create_tree(const uint32_t node_index)
{

    const uint32_t num_nodes = model_->num_nodes;

    const ClTreeNode* const p = reinterpret_cast<const ClTreeNode*>(&node_info_[node_index]);
    assert(node_index < num_nodes);

    TreeModel::node_t& node = model_->nodes[node_index];
    node.feature            = p->get_best_feature();
    node.threshold          = p->get_best_threshold();

    /* one node has 0 or 2 children, cannot have only 1 child */
    if (p->get_left_child() == -1) {
        node.is_leaf    = true;
        node.feature    = 0;
        node.leaf_label = p->get_wnum_pos() * (double)1.0 / (p->get_wnum_pos() + p->get_wnum_neg());
        node.leaf_proba = nullptr;
        model_->num_leaves += node.is_leaf;
        return;
    }

    assert(-1 != p->get_right_child());
    node.is_leaf = false;
    assert((uint32_t)p->get_left_child() < num_nodes && (uint32_t)p->get_right_child() < num_nodes);
    node.left_child  = p->get_left_child();
    node.right_child = p->get_right_child();

    assert(-1 != p->get_best_feature());
    feature_importances_[p->get_best_feature()] -= p->get_best_score();

    DecisionTreeBuilder<ClTreeNode>::create_tree(p->get_left_child());
    DecisionTreeBuilder<ClTreeNode>::create_tree(p->get_right_child());
}

template <> inline void DecisionTreeBuilder<MultiClTreeNode>::create_tree(const uint32_t node_index)
{

    const uint32_t num_nodes = model_->num_nodes;

    const MultiClTreeNode* const p = reinterpret_cast<const MultiClTreeNode*>(&node_info_[node_index]);
    assert(node_index < num_nodes);

    TreeModel::node_t& node = model_->nodes[node_index];
    node.feature            = p->get_best_feature();
    node.threshold          = p->get_best_threshold();

    /* one node has 0 or 2 children, cannot have only 1 child */
    if (p->get_left_child() == -1) {
        node.is_leaf = true;
        node.feature = 0;
        float wnum   = 0.0;
        for (uint32_t i = 0; i < num_classes_; i++) {
            wnum += p->get_wnum()[i];
        }
        model_->num_leaves += node.is_leaf;
        node.leaf_proba = new float[num_classes_ - 1];
        for (uint32_t i = 0; i < num_classes_ - 1; i++) {
            node.leaf_proba[i] = p->get_wnum()[i] * (double)1.0 / wnum;
        }
        return;
    }

    assert(-1 != p->get_right_child());
    node.is_leaf = false;
    assert((uint32_t)p->get_left_child() < num_nodes && (uint32_t)p->get_right_child() < num_nodes);
    node.left_child  = p->get_left_child();
    node.right_child = p->get_right_child();

    assert(-1 != p->get_best_feature());
    feature_importances_[p->get_best_feature()] -= p->get_best_score();

    DecisionTreeBuilder<MultiClTreeNode>::create_tree(p->get_left_child());
    DecisionTreeBuilder<MultiClTreeNode>::create_tree(p->get_right_child());
}

}

#endif
