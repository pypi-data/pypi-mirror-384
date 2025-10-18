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

#ifndef EXACT_TREE_BUILDER
#define EXACT_TREE_BUILDER

#include "DecisionTreeBuilderInt.hpp"
#include "TreeInvariants.hpp"
#include "TreeNode.hpp"

#include <stack>

namespace tree {

template <class N> class ExactTreeBuilder : public DecisionTreeBuilder<N> {

public:
    typedef std::chrono::high_resolution_clock             Clock;
    typedef std::chrono::high_resolution_clock::time_point CurTime;

    // ctor without TreeInvariants (for standalone use)
    ExactTreeBuilder<N>(glm::DenseDataset* data, snapml::DecisionTreeParams params)
        : DecisionTreeBuilder<N>(static_cast<glm::Dataset*>(data), params)

    {
    }

    // ctor with TreeInvariants (for use within an ensemble)
    ExactTreeBuilder<N>(glm::DenseDataset* data, snapml::DecisionTreeParams params,
                        const std::shared_ptr<glm::TreeInvariants<glm::DenseDataset>> tree_invariants)
        : DecisionTreeBuilder<N>(static_cast<glm::Dataset*>(data), params, tree_invariants)

    {
    }

    ~ExactTreeBuilder<N>() { }

private:
    typedef typename glm::TreeInvariants<glm::DenseDataset>::ex_info_t glm_ex_info_t;

    void init_invariants() override
    {
        this->tree_invariants_->init(this->data_, this->params_.task, this->params_.n_threads,
                                     this->params_.num_classes);
    }

    void build_tree_impl(const float* const sample_weight) override
    {
        constexpr uint32_t MAX_DEPTH          = 100U;
        constexpr uint32_t INIT_DEPTH         = 10U;
        constexpr uint32_t INIT_NODES         = 1U << (INIT_DEPTH + 1);
        constexpr double   BFS_TO_DFS_PCT_THR = 5.0;

        auto                                           data = static_cast<glm::DenseDataset*>(this->data_)->get_data();
        const std::vector<std::vector<glm_ex_info_t>>& sorted_ex = this->tree_invariants_->get_sorted_matrix();

        const uint32_t num_ex_effective = (this->params_.bootstrap || this->subsample_size_ < this->num_ex_)
                                              ? this->indices_.size()
                                              : this->num_ex_;

        uint32_t num_used = num_ex_effective;

#ifdef TIME_PROFILE
        double  step_init = 0, step0 = 0, step1 = 0, step2 = 0, step3 = 0, dfs_time = 0, dfs_prep_time = 0.0;
        CurTime t1, t2;
        if (omp_get_thread_num() == 0)
            t1 = Clock::now();
#endif
        std::vector<ex_md_t> ex_weights(this->num_ex_);
        if (this->params_.bootstrap || this->subsample_size_ < this->num_ex_)
            for (uint32_t i = 0; i < this->indices_.size(); ++i)
                ex_weights[this->indices_[i]].weight++;
        else
            for (uint32_t i = 0; i < this->num_ex_; ++i)
                ex_weights[i].weight++;

        this->node_info_.resize(std::min(INIT_NODES, 2 * this->num_ex_ - 1)); // TODO: place it in the constructor
        // std::vector<RegTreeNode> node_info (INIT_NODES);

        double sum_weights = 0.0;

        if (sample_weight != nullptr) {
            if (this->params_.bootstrap || this->subsample_size_ < this->num_ex_) {
                for (uint32_t i = 0; i < num_ex_effective; i++) {
                    sum_weights += sample_weight[this->indices_[i]];
                }
            } else {
                for (uint32_t i = 0; i < num_ex_effective; i++) {
                    sum_weights += sample_weight[i];
                }
            }
        }

        this->node_info_[0].init(ex_weights, sample_weight, this->labs_, this->indices_, this->num_ex_,
                                 this->num_classes_, sum_weights);

        if (this->max_depth_ == 0) {
            this->max_depth_ = MAX_DEPTH;
        }
        this->max_depth_ = std::min(this->max_depth_, MAX_DEPTH);

#ifdef TIME_PROFILE
        if (omp_get_thread_num() == 0) {
            t2       = Clock::now();
            auto dur = t2 - t1;
            step_init += (double)dur.count() / 1.0e9;
        }
#endif

        uint32_t depth               = 0;
        int32_t  last_processed_node = -1;
        uint32_t num_nodes           = 1;
        while (this->num_ex_ >= 2 * this->params_.min_samples_leaf && depth < this->max_depth_) {

#ifdef TIME_PROFILE
            if (omp_get_thread_num() == 0)
                t1 = Clock::now();
#endif

            // added support for colsample_bytree
            if (this->max_features_ < this->num_ft_ && 1.0 == this->params_.colsample_bytree) {
                for (uint32_t ft = 0; ft < this->fts_.size(); ft++)
                    this->fts_[ft] = ft;

                // std::shuffle(fts.begin(), fts.end(), this->rng_);
                fisher_yates(this->fts_, this->rng_);
            }

#ifdef TIME_PROFILE
            if (omp_get_thread_num() == 0) {
                t2       = Clock::now();
                auto dur = t2 - t1;
                step0 += (double)dur.count() / 1.0e9;
                t1 = Clock::now();
            }
#endif

            /* find best split across all nodes and features */
            for (uint32_t* ftp = &this->fts_[0]; ftp < &this->fts_[this->max_features_]; ++ftp) {
                const uint32_t ft = *ftp;

                for (uint32_t node = last_processed_node + 1; node < num_nodes; node++) {
                    this->node_info_[node].reset();
                }

                // assert(sorted_ex[ft].size() == num_ex_)
                for (uint32_t ex = 0; ex < sorted_ex[ft].size(); ex++) {
                    // sorted index of original data
                    const uint32_t orig_idx = sorted_ex[ft][ex].idx;
                    const float    val      = sorted_ex[ft][ex].val;
                    const float    lab      = get_lab_val(sorted_ex[ft][ex]);
                    // labs_[orig_idx]; //Classification sorted_ex[ft][ex].label;

                    // what is the weight on this example in the bootstrap sample
                    const uint32_t weight = ex_weights[orig_idx].weight;

                    if (ex < sorted_ex[ft].size() - 3) {
                        PREFETCH((void*)&ex_weights[sorted_ex[ft][ex + 3].idx]);
                    }

                    // if it is not present, we can skip it
                    if (weight == 0)
                        continue;

                    // look up node for this unique_index
                    const int32_t node = ex_weights[orig_idx].node;

                    if (node <= last_processed_node)
                        continue;

                    // check for pure nodes, and ignore this ex in such case
                    // TODO: regression case - is purity check required? what if all examples have the same value
                    if (this->node_info_[node].stopping_criterion())
                        continue;

                    /* handle the case when we have duplicates */
                    if ((this->node_info_[node].get_prev_ex() != -1)
                        && are_different(val, this->node_info_[node].get_prev_val()))
                        this->node_info_[node].update_best(ft, val, this->params_.min_samples_leaf,
                                                           this->params_.split_criterion, this->params_.lambda);

                    if (sample_weight == nullptr) {
                        this->node_info_[node].post_update_best(weight, (double)lab, 1, orig_idx, val);
                    } else {
                        this->node_info_[node].post_update_best(weight, (double)lab, sample_weight[orig_idx], orig_idx,
                                                                val);
                    }
                }
            }

#ifdef TIME_PROFILE
            if (omp_get_thread_num() == 0) {
                t2       = Clock::now();
                auto dur = t2 - t1;
                step1 += (double)dur.count() / 1.0e9;
                t1 = Clock::now();
            }
#endif

            uint32_t previous_num_nodes = num_nodes;
            uint32_t num_new_nodes      = 0;

            for (uint32_t node = last_processed_node + 1; node < previous_num_nodes; node++) {
                if (this->node_info_[node].get_best_feature() == -1)
                    continue;
                num_new_nodes += 2;
            }

            if (this->node_info_.size() < num_nodes + num_new_nodes)
                this->node_info_.resize(num_nodes + std::max(num_new_nodes, INIT_NODES));

            /* perform split */
            for (uint32_t node = last_processed_node + 1; node < previous_num_nodes; node++) {
                if (this->node_info_[node].get_best_feature() == -1)
                    continue;
                this->node_info_[node].update_parent(num_nodes, num_nodes + 1);
                this->node_info_[num_nodes].update_left_child(&this->node_info_[node], node);
                this->node_info_[num_nodes + 1].update_right_child(&this->node_info_[node], node);
                num_nodes += 2;
            }

            /* assign examples to nodes after the split */
            for (uint32_t i = 0; i < this->num_ex_; i++) {

                // what is the weight on this example in the bootstrap sample
                uint32_t weight = ex_weights[i].weight;

                // if it it not present, we can skip it
                if (weight == 0)
                    continue;

                uint32_t node = ex_weights[i].node;
                if (this->node_info_[node].get_left_child() == -1) {
                    num_used -= ex_weights[i].weight;
                    ex_weights[i].weight = 0;
                    continue;
                }

                if (glm::DenseDataset::lookup2D(data, i, this->node_info_[node].get_best_feature())
                    < this->node_info_[node].get_best_threshold())
                    ex_weights[i].node = this->node_info_[node].get_left_child();
                else
                    ex_weights[i].node = this->node_info_[node].get_right_child();
            }

#ifdef TIME_PROFILE
            if (omp_get_thread_num() == 0) {
                t2       = Clock::now();
                auto dur = t2 - t1;
                step2 += (double)dur.count() / 1.0e9;
            }
#endif

            last_processed_node = previous_num_nodes - 1;
            depth++;

            if (num_nodes == previous_num_nodes)
                break; // no new nodes created, stop

            if ((double)num_used <= BFS_TO_DFS_PCT_THR * this->num_ex_ / 100.0) {

#ifdef TIME_PROFILE
                if (omp_get_thread_num() == 0) {
                    // fprintf(stdout, "switching to dfs, depth=%u num_used=%u num_ex=%u num_nodes=%u
                    // prev_num_nodes=%u\n",
                    //         depth, num_used, num_ex_, num_nodes, previous_num_nodes);
                    t1 = Clock::now();
                }
#endif

                // pre-processing before kicking off DFS: create one sorted 2D array per node
                std::vector<std::unique_ptr<std::vector<std::vector<glm_ex_info_t>>>> node_ex(num_nodes
                                                                                              - previous_num_nodes);
                for (uint32_t node = previous_num_nodes; node < num_nodes; ++node) {
                    const uint32_t ex_nr = this->node_info_[node].get_num();
                    assert(0 < ex_nr);
                    node_ex[node - previous_num_nodes].reset(
                        new std::vector<std::vector<glm_ex_info_t>>(this->num_ft_, std::vector<glm_ex_info_t>(ex_nr)));
                }

                for (uint32_t ftp = 0; ftp < this->fts_.size(); ++ftp) {
                    const uint32_t        ft = this->fts_[ftp];
                    std::vector<uint32_t> node_fill_idx(num_nodes - previous_num_nodes, 0);

                    for (uint32_t ex = 0; ex < this->num_ex_; ex++) {
                        // sorted index of original data
                        const uint32_t orig_idx = sorted_ex[ft][ex].idx;

                        // what is the weight on this example in the bootstrap sample
                        const uint32_t weight = ex_weights[orig_idx].weight;

                        if (ex < this->num_ex_ - 1)
                            PREFETCH((void*)&ex_weights[sorted_ex[ft][ex + 1].idx]);

                        // if it it not present, we can skip it
                        if (0 == weight)
                            continue;

                        const uint32_t node = ex_weights[orig_idx].node;
                        assert(previous_num_nodes <= node);
                        if (this->node_info_[node].stopping_criterion())
                            continue;

                        for (uint32_t i = 0; i < ex_weights[orig_idx].weight; ++i) {
                            (*node_ex[node - previous_num_nodes])[ft][node_fill_idx[node - previous_num_nodes]++]
                                = sorted_ex[ft][ex];
                        }
                    }
#ifndef NDEBUG
                    if (sample_weight == nullptr)
                        for (uint32_t node = previous_num_nodes; node < num_nodes; ++node) {
                            if (this->node_info_[node].stopping_criterion())
                                continue;
                            assert(node_fill_idx[node - previous_num_nodes] == this->node_info_[node].get_num());
                        }
#endif
                }

                ex_weights.clear();
                ex_weights.shrink_to_fit();

#ifdef TIME_PROFILE
                if (omp_get_thread_num() == 0) {
                    t2       = Clock::now();
                    auto dur = t2 - t1;
                    dfs_prep_time += (double)dur.count() / 1.0e9;
                    t1 = Clock::now();
                }
#endif

                // run dfs, left to right
                const uint32_t old_num_nodes = num_nodes;
                uint32_t       max_depth     = depth;

                for (uint32_t node = previous_num_nodes; node < old_num_nodes; ++node) {
                    // num_nodes passed by reference!
                    // TODO: find a better way to retrieve the final number of nodes
                    const uint32_t new_depth = node_dfs(node, depth, std::move(node_ex[node - previous_num_nodes]),
                                                        num_nodes, sample_weight);
                    max_depth                = std::max(max_depth, new_depth);
                }

#ifdef TIME_PROFILE
                if (omp_get_thread_num() == 0) {
                    t2       = Clock::now();
                    auto dur = t2 - t1;
                    dfs_time += (double)dur.count() / 1.0e9;
                }
#endif

                depth = max_depth;
                break;
            }
        }

#ifdef TIME_PROFILE
        if (omp_get_thread_num() == 0)
            t1 = Clock::now();
#endif

        this->create_model(num_nodes);
        this->node_info_.clear();
        this->node_info_.shrink_to_fit();
        this->indices_.clear();
        this->indices_.shrink_to_fit();

#ifdef TIME_PROFILE
        if (omp_get_thread_num() == 0) {
            t2       = Clock::now();
            auto dur = t2 - t1;
            step3 += (double)dur.count() / 1.0e9;
        }
#endif

        if (!this->params_.tree_in_ensemble) {
            this->tree_invariants_->clear_sorted_matrix();
            this->tree_invariants_->clear_ex_to_bin();
        }
    }

    // Given a particular node_idx as starting point, and a sorted 2D
    // array of features to examples that are valid only for this
    // node, grow the tree graph using a Depth-First Search algorithm
    uint32_t node_dfs(uint32_t node_idx, uint32_t depth,
                      std::unique_ptr<std::vector<std::vector<glm_ex_info_t>>>&& sorted_ex_infos_ptr,
                      uint32_t& num_nodes, const float* const sample_weight = nullptr)
    {

        if (this->max_depth_ < depth)
            return this->max_depth_;

        uint32_t   tot_max_depth = depth;
        const auto data          = static_cast<glm::DenseDataset*>(this->data_)->get_data();
        std::stack<std::tuple<uint32_t, uint32_t, std::unique_ptr<std::vector<std::vector<glm_ex_info_t>>>>> lifo;
        lifo.push(std::make_tuple(node_idx, depth, std::move(sorted_ex_infos_ptr)));

        while (!lifo.empty()) {
            node_idx = std::get<0>(lifo.top());
            depth    = std::get<1>(lifo.top());
            std::unique_ptr<std::vector<std::vector<glm_ex_info_t>>> sei_ptr(std::move(std::get<2>(lifo.top())));
            lifo.pop();

            /* stopping criterion */
            if (this->max_depth_ < depth)
                continue; // do not process node if max_depth reached

            tot_max_depth = std::max(depth, tot_max_depth);
            N* node       = &this->node_info_[node_idx]; // not const cause it might change in case of a resize

            if (node->stopping_criterion())
                continue;

            // added support for colsample_bytree
            if (this->max_features_ < this->num_ft_ && 1.0 == this->params_.colsample_bytree) {
                fisher_yates(this->fts_, this->rng_);
            }

            assert(-1 == node->get_best_feature()); // make sure this node has not been seen before

            // find the best split
            for (uint32_t* ft = &this->fts_[0]; ft < &this->fts_[this->max_features_]; ++ft) {
                node->reset();

                for (const auto& ex : (*sei_ptr)[*ft]) {
                    if ((node->get_prev_ex() != -1) && are_different(ex.val, node->get_prev_val())) {
                        // std::cout << node->get_best_feature() << " index=" << node_idx << " index_feature=" << *ft <<
                        // " index_example=" << ex.idx << " index_value=" << ex.val << std::endl;
                        node->update_best(*ft, ex.val, this->params_.min_samples_leaf, this->params_.split_criterion,
                                          this->params_.lambda);
                        // std::cout << node->get_best_feature() << " index=" << node_idx << " index_feature=" << *ft <<
                        // " index_example=" << ex.idx << " index_value=" << ex.val << std::endl;
                    }

                    double label = get_lab_val(ex);
                    if (sample_weight == nullptr) {
                        node->post_update_best(1, label, 1, ex.idx, ex.val);
                    } else {
                        node->post_update_best(1, label, sample_weight[ex.idx], ex.idx, ex.val);
                    }
                }
            }

            if (-1 == node->get_best_feature())
                continue; // no split found

            if (this->node_info_.size() < num_nodes + 2) {
                this->node_info_.resize(this->node_info_.size() + 131072U);
                // pointer has to be updated to the new vector
                // location, only node_idx is guaranteed to be valid
                node = &this->node_info_[node_idx];
            }

            // perform the split
            const uint32_t left_idx  = num_nodes;
            const uint32_t right_idx = num_nodes + 1;

            node->update_parent(left_idx, right_idx);
            num_nodes += 2; // two more nodes

            N* const left  = &this->node_info_[left_idx];
            N* const right = &this->node_info_[right_idx];
            left->update_left_child(node, node_idx);
            right->update_right_child(node, node_idx);
            // assert(left->num + left->num_neg + right->num_pos + right->num_neg == node->num_pos + node->num_neg);

            // propagate the sorted array to left and right
            // nodes. We perform an optimization here that
            // probably deserves some explanation: instead of
            // allocating two new arrays for the left and right
            // nodes, and copying the data from the parent, we
            // re-use the parent array for the larger of the two
            // nodes (left or right) and only create one new array
            // for the smaller of the two nodes.

            const bool     left_gt   = right->get_num() < left->get_num();
            const uint32_t new_ex_nr = std::min(left->get_num(), right->get_num());
            std::unique_ptr<std::vector<std::vector<glm_ex_info_t>>> new_ex(
                new std::vector<std::vector<glm_ex_info_t>>(this->num_ft_, std::vector<glm_ex_info_t>(new_ex_nr)));

            const uint32_t len = (*sei_ptr)[this->fts_[0]].size();

            std::unique_ptr<std::vector<std::vector<glm_ex_info_t>>> left_ex;
            std::unique_ptr<std::vector<std::vector<glm_ex_info_t>>> right_ex;
            if (left_gt) {
                left_ex  = std::move(sei_ptr);
                right_ex = std::move(new_ex);
            } else {
                left_ex  = std::move(new_ex);
                right_ex = std::move(sei_ptr);
            }

            for (uint32_t ftp = 0; ftp < this->fts_.size(); ++ftp) {
                const uint32_t ft            = this->fts_[ftp];
                uint32_t       left_fill_idx = 0, right_fill_idx = 0;

                for (uint32_t idx = 0; idx < len; ++idx) {
                    const auto&  ex  = left_gt ? (*left_ex)[ft][idx] : (*right_ex)[ft][idx];
                    const double val = glm::DenseDataset::lookup2D(data, ex.idx, node->get_best_feature());

                    if (val < node->get_best_threshold()) {
                        (*left_ex)[ft][left_fill_idx++] = ex;
                    } else
                        (*right_ex)[ft][right_fill_idx++] = ex;
                }

                assert(left->get_num() == left_fill_idx);
                assert(right->get_num() == right_fill_idx);

                // trim unused space from the larger array, all
                // those examples are in the smaller one now
                if (left_gt)
                    (*left_ex)[ft].erase((*left_ex)[ft].begin() + left_fill_idx, (*left_ex)[ft].end());
                else
                    (*right_ex)[ft].erase((*right_ex)[ft].begin() + right_fill_idx, (*right_ex)[ft].end());
            }

            if (this->max_depth_ < depth + 1)
                continue;

            // push new nodes into the DFS stack
            if (!left->stopping_criterion()) {
                lifo.push(std::make_tuple(left_idx, depth + 1, std::move(left_ex)));
            }
            if (!right->stopping_criterion()) {
                lifo.push(std::make_tuple(right_idx, depth + 1, std::move(right_ex)));
            }
        }

        return tot_max_depth;
    }

    // this default is used for classification
    float GLM_INLINE get_lab_val(const glm_ex_info_t& ex_info) const { return ex_info.label; }
};

// for regression, get the label from the input
template <> inline float ExactTreeBuilder<RegTreeNode>::get_lab_val(const glm_ex_info_t& ex_info) const
{
    return this->labs_[ex_info.idx];
}

}

#endif