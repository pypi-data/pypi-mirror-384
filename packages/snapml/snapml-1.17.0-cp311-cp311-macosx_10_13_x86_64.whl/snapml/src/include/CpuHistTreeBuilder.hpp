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

#ifndef CPU_HIST_TREE_BUILDER
#define CPU_HIST_TREE_BUILDER

#include "HistTreeBuilder.hpp"
#include "TreeInvariants.hpp"
#include "TreeNode.hpp"

#include <stack>
#include <mutex>

namespace tree {

template <class N> class CpuHistTreeBuilder : public HistTreeBuilder<N> {

public:
    typedef std::chrono::high_resolution_clock             Clock;
    typedef std::chrono::high_resolution_clock::time_point CurTime;
    typedef typename N::hist_bin_t                         hist_bin_t;

    // ctor without TreeInvariants (for standalone use)
    CpuHistTreeBuilder<N>(glm::DenseDataset* data, snapml::DecisionTreeParams params)
        : HistTreeBuilder<N>(data, params)

    {
    }

    // ctor with TreeInvariants (for use within an ensemble)
    CpuHistTreeBuilder<N>(glm::DenseDataset* data, snapml::DecisionTreeParams params,
                          const std::shared_ptr<glm::TreeInvariants<glm::DenseDataset>> tree_invariants)
        : HistTreeBuilder<N>(data, params, tree_invariants)

    {
    }

    ~CpuHistTreeBuilder<N>() { }

private:
    void init_invariants() override
    {
        this->tree_invariants_->init(this->data_, this->params_.task, this->params_.n_threads,
                                     this->params_.num_classes);
        this->tree_invariants_->init_hist(this->data_, this->params_.task, this->hist_nbins_);
    }

    void build_tree_impl(const float* const sample_weight) override
    {
        constexpr uint32_t MAX_DEPTH  = 100U;
        constexpr uint32_t INIT_DEPTH = 10U;
        constexpr uint32_t INIT_NODES = 1U << (INIT_DEPTH + 1);

        std::vector<ex_md_t> ex_weights;
        omp_set_num_threads(this->params_.n_threads);

#ifdef TIME_PROFILE
        double  step0 = 0, step1 = 0, step2 = 0, step3 = 0, step4 = 0, step5 = 0, step6 = 0, step7 = 0, step8 = 0;
        CurTime t1, t2, t3;
        if (omp_get_thread_num() == 0)
            t1 = Clock::now();
#endif

        this->training_predictions_.resize(this->num_ex_, std::numeric_limits<double>::max());
        this->go_left_.resize(this->num_ex_);

        const std::vector<std::vector<float>>& hist_val = this->tree_invariants_->get_hist_val();

        if (!this->params_.tree_in_ensemble) {
            this->tree_invariants_->clear_sorted_matrix();
        }

        // changed data structure for regression

        if (this->max_depth_ == 0)
            this->max_depth_ = MAX_DEPTH;
        this->max_depth_ = std::min(this->max_depth_, MAX_DEPTH);

        {
            const uint32_t init_nodes
                = std::min(this->max_depth_ < 31 ? 1U << (this->max_depth_ + 1) : 1U << (31), 2 * this->num_ex_ - 1);
            this->node_info_.resize(std::min(INIT_NODES, init_nodes)); // TODO: place it in the constructor
        }

        uint32_t tot_depth = 0;
        uint32_t num_nodes = 1;

        std::stack<std::tuple<uint32_t, uint32_t, std::unique_ptr<std::vector<ex_lab_t>>,
                              std::unique_ptr<std::vector<std::vector<hist_bin_t>>>>>
                       lifo; // (node_idx, depth, exs) stack
        std::mutex     mtx;
        std::vector<N> per_th_node(omp_get_max_threads());

        std::unique_ptr<std::vector<std::vector<hist_bin_t>>> hist_bins_p(new std::vector<std::vector<hist_bin_t>>(
            this->num_ft_, std::vector<hist_bin_t>(this->hist_nbins_, hist_bin_t(this->num_classes_))));

        std::vector<ex_lab_t> ex_labs(this->num_ex_effective_);
        OMP::parallel_for<int32_t>(0, this->num_ex_effective_, [this, &ex_labs, &sample_weight](const int32_t& ex) {
            const uint32_t idx        = 0 != this->indices_.size() ? this->indices_[ex] : ex;
            ex_labs[ex].idx           = idx;
            ex_labs[ex].sample_weight = (sample_weight == nullptr) ? 1.0 : sample_weight[idx];
            ex_labs[ex].lab = (this->params_.task == snapml::task_t::classification && this->num_classes_ == 2)
                                  ? (0 < this->labs_[idx] ? 1 : 0)
                                  : this->labs_[idx]; // TODO: do a specific impl
        });

        std::unique_ptr<std::vector<ex_lab_t>> node_ex_p(new std::vector<ex_lab_t>(std::move(ex_labs)));
        uint32_t UNUSED                        tot_bins_lt;

        if (!(this->params_.bootstrap || this->subsample_size_ < this->num_ex_)) {
            const std::vector<std::vector<uint32_t>>& hist_initial_weights
                = this->tree_invariants_->get_hist_initial_weights();
            const std::vector<std::vector<uint8_t>>& ex_to_bin = this->tree_invariants_->get_ex_to_bin();

            // using DecisionTreeBuilder<D, N>::num_classes_;
            uint32_t num_classes = this->num_classes_;

            OMP::parallel_for<int32_t>(
                0, this->num_ft_, [&hist_bins_p, &hist_val, &hist_initial_weights, &num_classes](const int32_t& ft) {
                    (*hist_bins_p)[ft].resize(hist_val[ft].size(), hist_bin_t(num_classes));
                    for (uint32_t bin_idx = 0; bin_idx < (*hist_bins_p)[ft].size(); ++bin_idx) {
                        (*hist_bins_p)[ft][bin_idx].weight = hist_initial_weights[ft][bin_idx];
                    }
                });

            tot_bins_lt = HistTreeBuilder<N>::template recompute_hist_bin<true>(*node_ex_p, ex_to_bin, hist_bins_p,
                                                                                this->fts_.size());

        } else {
            const std::vector<std::vector<uint8_t>>& ex_to_bin = this->tree_invariants_->get_ex_to_bin();
            tot_bins_lt = HistTreeBuilder<N>::template recompute_hist_bin<false>(*node_ex_p, ex_to_bin, hist_bins_p,
                                                                                 this->fts_.size());
        }

        this->node_info_[0].init_with_hist((*hist_bins_p)[this->fts_[0]], this->num_classes_);
        assert(this->node_info_[0].get_num() == this->num_ex_effective_);
        lifo.push(std::make_tuple(0, 0, std::move(node_ex_p), std::move(hist_bins_p)));

        // not used beyond init
        this->indices_.clear();
        this->indices_.shrink_to_fit();

#ifdef TIME_PROFILE
        if (omp_get_thread_num() == 0) {
            t2       = Clock::now();
            auto dur = t2 - t1;
            step0    = (double)dur.count() / 1.0e9;
            t1       = t2;
            t3       = t1;
        }
#endif

        while (this->num_ex_effective_ >= 2 * this->params_.min_samples_leaf && !lifo.empty()) {

#ifdef TIME_PROFILE
            if (omp_get_thread_num() == 0) {
                t2       = Clock::now();
                auto dur = t2 - t1;
                step1 += (double)dur.count() / 1.0e9;
                t1 = t2;
            }
#endif

            const uint32_t                                        node_idx    = std::get<0>(lifo.top());
            const uint32_t                                        depth       = std::get<1>(lifo.top());
            std::unique_ptr<std::vector<ex_lab_t>>                nex_p       = std::move(std::get<2>(lifo.top()));
            std::unique_ptr<std::vector<std::vector<hist_bin_t>>> hist_bins_p = std::move(std::get<3>(lifo.top()));
            lifo.pop();

            N* node   = &this->node_info_[node_idx];
            tot_depth = std::max(depth, tot_depth);
            // stopping criterion : depth
            assert(node->get_num() <= this->num_ex_effective_);

            const bool stop = this->max_depth_ <= depth || node->stopping_criterion() || node->get_num() < 2;
            // fprintf(stdout, "num_nodes=%u depth=%u node=%p nidx=%u num=%u stop=%d pred=%lf\n",
            //         num_nodes, depth, nex_p.get(), node_idx, node->get_num(), stop, node->get_pred_val());
            if (stop) {
                if (this->params_.compute_training_predictions) {
                    // node->pretty_print(node_idx);
                    HistTreeBuilder<N>::update_training_predictions(node, nex_p);
                }

#ifdef TIME_PROFILE
                if (omp_get_thread_num() == 0) {
                    t2       = Clock::now();
                    auto dur = t2 - t1;
                    step2 += (double)dur.count() / 1.0e9;
                    t1 = t2;
                }
#endif
                continue;
            }
            assert(nullptr != hist_bins_p.get());

#ifdef DEBUG_VERIFY
            {
                for (uint32_t ftp = 0; ftp < this->fts_.size(); ++ftp) {
                    const uint32_t ft  = this->fts_[ftp];
                    uint32_t       sum = 0;
                    for (uint32_t bin_idx = 0; bin_idx < (*hist_bins_p)[ft].size(); ++bin_idx) {
                        sum += (*hist_bins_p)[ft][bin_idx].weight;
                    }
                    assert((*nex_p).size() == sum);
                }
            }
#endif

            // added support for colsample_bytree
            if (this->max_features_ < this->num_ft_ && 1.0 == this->params_.colsample_bytree) {
                fisher_yates(this->fts_, this->rng_);
            }

#ifdef TIME_PROFILE
            if (omp_get_thread_num() == 0) {
                t2       = Clock::now();
                auto dur = t2 - t1;
                step2 += (double)dur.count() / 1.0e9;
                t1 = t2;
            }
#endif
            assert(-1 == node->get_best_feature()); // make sure this node has not been seen before

            // find the best split
            OMP::parallel([this, &per_th_node, &node, &hist_bins_p, &hist_val](std::exception_ptr& eptr) {
                const int tid     = omp_get_thread_num();
                N* const  my_node = &per_th_node[tid];
                my_node->copy_node(node);
                OMP::_for<int32_t>(0, this->max_features_, eptr, [&](int32_t ftp) {
                    my_node->reset();
                    uint32_t ft = this->fts_[ftp];

                    for (uint32_t bin_idx = 0; bin_idx < (*hist_bins_p)[ft].size(); ++bin_idx) {
                        const auto& bin = (*hist_bins_p)[ft][bin_idx];
                        const float val = hist_val[ft][bin_idx]; // bin.val

                        if (0 == bin.weight)
                            continue;

                        my_node->update_best_hist(ft, val, this->params_.min_samples_leaf,
                                                  this->params_.split_criterion, this->params_.lambda);
                        my_node->post_update_best_hist(bin);
                    }
                });
            });
            for (uint32_t t = 0; t < per_th_node.size(); ++t) {
                node->update_best(&per_th_node[t]);
            }
            // node->pretty_print(node_idx);
#ifdef TIME_PROFILE
            if (omp_get_thread_num() == 0) {
                t2       = Clock::now();
                auto dur = t2 - t1;
                step3 += (double)dur.count() / 1.0e9;
                t1 = t2;
            }
#endif

            if (-1 == node->get_best_feature()) {
                if (this->params_.compute_training_predictions) {
                    // node->pretty_print(node_idx);
                    HistTreeBuilder<N>::update_training_predictions(node, nex_p);
                }

#ifdef TIME_PROFILE
                if (omp_get_thread_num() == 0) {
                    t2       = Clock::now();
                    auto dur = t2 - t1;
                    step4 += (double)dur.count() / 1.0e9;
                    t1 = t2;
                }
#endif
                continue; // no split found
            }

            if (this->node_info_.size() < num_nodes + 2) {
                this->node_info_.resize(this->node_info_.size() + 16384U);
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
            const uint32_t left_num  = left->get_num();
            const uint32_t right_num = right->get_num();
            assert(left_num <= this->num_ex_effective_);
            assert(right_num <= this->num_ex_effective_);

#ifdef TIME_PROFILE
            if (omp_get_thread_num() == 0) {
                t2       = Clock::now();
                auto dur = t2 - t1;
                step4 += (double)dur.count() / 1.0e9;
                t1 = t2;
            }
#endif
            assert(left_num + right_num == node->get_num());

            const bool     left_gt   = right_num < left_num;
            const uint32_t new_ex_nr = std::min(left_num, right_num);

            assert(0 < new_ex_nr);
            std::unique_ptr<std::vector<ex_lab_t>> new_ex(new std::vector<ex_lab_t>(new_ex_nr));
            // cudaHostRegister(new_ex.get(), new_ex_nr*sizeof(ex_lab_t), cudaHostRegisterMapped);

            std::unique_ptr<std::vector<ex_lab_t>> left_ex;
            std::unique_ptr<std::vector<ex_lab_t>> right_ex;
            if (left_gt) {
                left_ex  = std::move(nex_p);
                right_ex = std::move(new_ex);
            } else {
                left_ex  = std::move(new_ex);
                right_ex = std::move(nex_p);
            }

#ifdef TIME_PROFILE
            if (omp_get_thread_num() == 0) {
                t2       = Clock::now();
                auto dur = t2 - t1;
                step5 += (double)dur.count() / 1.0e9;
                t1 = t2;
            }
#endif
            const uint32_t                                        best_ft  = node->get_best_feature();
            const float                                           best_thr = node->get_best_threshold();
            std::unique_ptr<std::vector<std::vector<hist_bin_t>>> new_hist_lt;
            std::unique_ptr<std::vector<std::vector<hist_bin_t>>> new_hist_gt;

            const bool stop_all = (this->max_depth_ <= depth + 1) || (left_num <= 1 && right_num <= 1);
            split_ex_and_recompute_hist_bins(best_ft, best_thr, left_gt,
                                             stop_all, // should we break after split
                                             left, right, left_ex, right_ex, hist_bins_p, new_hist_lt, new_hist_gt);
            if (stop_all) {
                tot_depth = std::max(depth + 1, tot_depth);
                if (this->params_.compute_training_predictions) {
                    // left->pretty_print(left_idx);
                    // right->pretty_print(right_idx);
                    HistTreeBuilder<N>::update_training_predictions(left, left_ex);
                    HistTreeBuilder<N>::update_training_predictions(right, right_ex);
                }

#ifdef TIME_PROFILE
                if (omp_get_thread_num() == 0) {
                    t2       = Clock::now();
                    auto dur = t2 - t1;
                    step6 += (double)dur.count() / 1.0e9;
                    t1 = t2;
                }
#endif

                continue;
            }

            if (1 < left_num && 1 < right_num) // only compute sibling if it's going to be used
                recompute_hist_bin_sibling(*new_hist_lt, new_hist_gt);
            if (left_num <= 1 || right_num <= 1) {
                assert(nullptr == new_hist_lt.get());
            }
            assert(nullptr != new_hist_gt.get());

#ifdef TIME_PROFILE
            if (omp_get_thread_num() == 0) {
                t2       = Clock::now();
                auto dur = t2 - t1;
                step6 += (double)dur.count() / 1.0e9;
                t1 = t2;
            }
#endif

            // push new nodes into the DFS stack
            // stopping criteria (for classification is if the nodes are pure) - any other criteria?
            // number of bins - is it necessary here or it will be taken care of in the next round?
            if (left_gt) {
                lifo.push(std::make_tuple(right_idx, depth + 1, std::move(right_ex), std::move(new_hist_lt)));
                lifo.push(std::make_tuple(left_idx, depth + 1, std::move(left_ex), std::move(new_hist_gt)));
            } else {
                lifo.push(std::make_tuple(left_idx, depth + 1, std::move(left_ex), std::move(new_hist_lt)));
                lifo.push(std::make_tuple(right_idx, depth + 1, std::move(right_ex), std::move(new_hist_gt)));
            }

#ifdef TIME_PROFILE
            if (omp_get_thread_num() == 0) {
                t2       = Clock::now();
                auto dur = t2 - t1;
                step7 += (double)dur.count() / 1.0e9;
                t1 = t2;
            }
#endif
        }

        // std::cout << "[BDT] num_nodes " << num_nodes << std::endl;
        this->create_model(num_nodes);

        // update predictions for the examples that were not used during training
        // should be enabled only in subsample mode
        if ((this->params_.compute_training_predictions) && (this->subsample_size_ < this->num_ex_)) {
            auto predictor = std::make_shared<TreePredictor>(this->model_);
            OMP::parallel_for<int32_t>(0, this->num_ex_, [this, &predictor](const int32_t& ex) {
                if (this->training_predictions_[ex] == std::numeric_limits<double>::max()) {
                    this->training_predictions_[ex] = 0.0;
                    predictor->predict(static_cast<glm::DenseDataset*>(this->data_), ex,
                                       this->training_predictions_.data());
                }
            });
        }

        this->node_info_.clear();
        this->node_info_.shrink_to_fit();
        this->go_left_.clear();
        this->go_left_.shrink_to_fit();

        if (!this->params_.tree_in_ensemble) {
            this->tree_invariants_->clear_ex_to_bin();
        }

        // fprintf(stdout, "num_nodes=%u depth=%u\n", num_nodes, tot_depth);
#ifdef TIME_PROFILE
        if (omp_get_thread_num() == 0) {
            t2       = Clock::now();
            auto dur = t2 - t1;
            step8    = (double)dur.count() / 1.0e9;

            fprintf(stdout, "num_nodes=%u depth=%u\n", num_nodes, tot_depth);
            // std::cout << "num_ex : " << get_number_of_examples(0) << " num_pos : " << get_number_of_examples(1) << "
            // num_neg : " << get_number_of_examples(-1) <<std::endl;

            printf("[BinaryDecisionTree::build_tree_impl_with_histograms] step 0: %e [init]\n", step0);
            printf("[BinaryDecisionTree::build_tree_impl_with_histograms] step 1: %e [lifo.empty()]\n", step1);
            printf("[BinaryDecisionTree::build_tree_impl_with_histograms] step 2: %e [lifo.pop()]\n", step2);
            printf("[BinaryDecisionTree::build_tree_impl_with_histograms] step 3: %e [find best split]\n", step3);
            printf("[BinaryDecisionTree::build_tree_impl_with_histograms] step 4: %e [update node stats]\n", step4);
            printf("[BinaryDecisionTree::build_tree_impl_with_histograms] step 5: %e [alloc mem for new exs]\n", step5);
            printf("[BinaryDecisionTree::build_tree_impl_with_histograms] step 6: %e [split ex and recompute]\n",
                   step6);
            printf("[BinaryDecisionTree::build_tree_impl_with_histograms] step 7: %e [lifo.push()]\n", step7);
            printf("[BinaryDecisionTree::build_tree_impl_with_histograms] step 8: %e [create tree]\n", step8);
            printf("[BinaryDecisionTree::build_tree_impl_with_histograms]  total: %e\n",
                   step0 + step1 + step2 + step3 + step4 + step5 + step6 + step7 + step8);
        }
#endif
    }

    void split_ex_and_recompute_hist_bins( // input variables
        const uint32_t best_ft, const float best_thr, const bool left_gt, const bool ret_after_split,
        const N* const left, const N* const right,
        // input/output variables
        std::unique_ptr<std::vector<ex_lab_t>>& left_ex, std::unique_ptr<std::vector<ex_lab_t>>& right_ex,
        std::unique_ptr<std::vector<std::vector<hist_bin_t>>>& hist_bins_p,
        std::unique_ptr<std::vector<std::vector<hist_bin_t>>>& new_hist_lt,
        std::unique_ptr<std::vector<std::vector<hist_bin_t>>>& new_hist_gt)
    {

#ifdef TIME_PROFILE
        CurTime t1, t2;
        if (omp_get_thread_num() == 0)
            t1 = Clock::now();
#endif

        const uint32_t                           left_num      = left->get_num();
        const uint32_t                           right_num     = right->get_num();
        const uint32_t                           len           = left_num + right_num;
        const std::vector<std::vector<uint8_t>>& ex_to_bin     = this->tree_invariants_->get_ex_to_bin();
        const std::vector<std::vector<float>>&   hist_val      = this->tree_invariants_->get_hist_val();
        uint32_t                                 left_fill_idx = 0, right_fill_idx = 0;
        if (len < 1000) {
            for (uint32_t idx = 0; idx < len; ++idx) {
                const auto&    ex      = left_gt ? (*left_ex)[idx] : (*right_ex)[idx];
                const uint32_t bin_idx = ex_to_bin[best_ft][ex.idx];
                if (hist_val[best_ft][bin_idx] < best_thr)
                    (*left_ex)[left_fill_idx++] = ex;
                else
                    (*right_ex)[right_fill_idx++] = ex;
            }
        } else {
            OMP::parallel_for<int32_t>(
                0, len,
                [this, &left_gt, &left_ex, &right_ex, &ex_to_bin, &best_ft, &hist_val, &best_thr](const int32_t& idx) {
                    const auto&    ex      = left_gt ? (*left_ex)[idx] : (*right_ex)[idx];
                    const uint32_t bin_idx = ex_to_bin[best_ft][ex.idx];
                    this->go_left_[idx]    = hist_val[best_ft][bin_idx] < best_thr;
                });

            for (uint32_t idx = 0; idx < len; ++idx) {
                // printf("%d %d\n", idx, (int)go_left[idx]);
                const auto& ex = left_gt ? (*left_ex)[idx] : (*right_ex)[idx];
                if (this->go_left_[idx]) {
                    (*left_ex)[left_fill_idx++] = ex;
                } else {
                    (*right_ex)[right_fill_idx++] = ex;
                }
            }
        }

        assert(left_num == left_fill_idx);
        assert(right_num == right_fill_idx);

        // trim unused space from the larger array, all
        // those examples are in the smaller one now
        if (left_gt)
            left_ex->erase(left_ex->begin() + left_fill_idx, left_ex->end());
        else
            right_ex->erase(right_ex->begin() + right_fill_idx, right_ex->end());

        if (ret_after_split)
            return;
        assert(left_ex->size() == left_num);
        assert(right_ex->size() == right_num);
        new_hist_gt = std::move(hist_bins_p);
        assert(1 < left_num || 1 < right_num);
        if (1 < left_num && 1 < right_num) {
            // allocate and compute child histograms
            new_hist_lt.reset(new std::vector<std::vector<hist_bin_t>>(
                this->num_ft_, std::vector<hist_bin_t>(this->hist_nbins_, hist_bin_t(this->num_classes_))));
            for (uint32_t ft = 0; ft < this->num_ft_; ++ft)
                (*new_hist_lt)[ft].resize((*new_hist_gt)[ft].size(), hist_bin_t(this->num_classes_));
            HistTreeBuilder<N>::template recompute_hist_bin<false>(left_gt ? *right_ex : *left_ex, ex_to_bin,
                                                                   new_hist_lt, this->fts_.size());
        } else if (left_num <= 1) { // do right only
            assert(!left_gt);
            // TODO : figure out a better way to reset hist_bins
            new_hist_gt.reset(new std::vector<std::vector<hist_bin_t>>(
                this->num_ft_, std::vector<hist_bin_t>(this->hist_nbins_, hist_bin_t(this->num_classes_))));
            HistTreeBuilder<N>::template recompute_hist_bin<false>(*right_ex, ex_to_bin, new_hist_gt,
                                                                   this->fts_.size());
        } else if (right_num <= 1) { // do left only
            assert(left_gt);
            new_hist_gt.reset(new std::vector<std::vector<hist_bin_t>>(
                this->num_ft_, std::vector<hist_bin_t>(this->hist_nbins_, hist_bin_t(this->num_classes_))));
            HistTreeBuilder<N>::template recompute_hist_bin<false>(*left_ex, ex_to_bin, new_hist_gt, this->fts_.size());
        } else {
            assert(0);
        }

#ifdef TIME_PROFILE
        CurTime t1, t2, t3;
        if (omp_get_thread_num() == 0) {
            t2            = Clock::now();
            auto   dur    = t2 - t1;
            double t_elap = (double)dur.count() / 1.0e9;
            printf("[BinaryDecisionTree::split_ex_and_recompute_hist_bins() t_elap = %f\n", t_elap);
        }
#endif
    }

    inline uint32_t recompute_hist_bin_sibling(
        const std::vector<std::vector<hist_bin_t>>&            hist_bins_sibling,
        std::unique_ptr<std::vector<std::vector<hist_bin_t>>>& hist_bins_p /* input (parent) and output*/)
    {
        // std::vector<uint32_t> nonempty_bins(num_ft_, 0);
        // omp_set_nested(true);
        // omp_set_num_threads(params_.n_threads);
        OMP::parallel_for<int32_t>(0, this->fts_.size(), [this, &hist_bins_p, &hist_bins_sibling](const int32_t& ftp) {
            const uint32_t ft = this->fts_[ftp];
            for (uint32_t bin_idx = 0; bin_idx < (*hist_bins_p)[ft].size(); ++bin_idx) {
                auto& parent         = (*hist_bins_p)[ft][bin_idx];
                auto& sibling        = hist_bins_sibling[ft][bin_idx];
                auto& output         = (*hist_bins_p)[ft][bin_idx];
                output.weight        = parent.weight - sibling.weight;
                output.sample_weight = parent.sample_weight - sibling.sample_weight;
                output.lab_sum       = parent.lab_sum - sibling.lab_sum;
                output.num_pos       = parent.num_pos - sibling.num_pos;
                // if (0 != output.weight)
                //     nonempty_bins[ft]++;
            }
        });
        // stopping criterion : each feature has only one non-empty
        // bin <-> for each feature, all examples fall in the same bin
        // uint32_t tot_bins = 0;
        // for (uint32_t ftp = 0; ftp < fts_.size(); ++ftp) {
        //     const uint32_t ft = fts_[ftp];
        //     assert(1 <= nonempty_bins[ft]); // at least one non empty
        //     tot_bins += nonempty_bins[ft];
        // }
        // return tot_bins;
        return 2 * this->num_ft_;
    }
};

template <>
inline uint32_t CpuHistTreeBuilder<MultiClTreeNode>::recompute_hist_bin_sibling(
    const std::vector<std::vector<MultiClTreeNode::hist_bin_t>>&            hist_bins_sibling,
    std::unique_ptr<std::vector<std::vector<MultiClTreeNode::hist_bin_t>>>& hist_bins_p /* input (parent) and output*/)
{
    // std::vector<uint32_t> nonempty_bins(num_ft_, 0);
    // OMP_MAX_LVL(1);
    // omp_set_num_threads(params_.n_threads);
    OMP::parallel_for<int32_t>(0, fts_.size(), [this, &hist_bins_p, &hist_bins_sibling](const int32_t& ftp) {
        const uint32_t ft = fts_[ftp];
        for (uint32_t bin_idx = 0; bin_idx < (*hist_bins_p)[ft].size(); ++bin_idx) {
            auto& parent         = (*hist_bins_p)[ft][bin_idx];
            auto& sibling        = hist_bins_sibling[ft][bin_idx];
            auto& output         = (*hist_bins_p)[ft][bin_idx];
            output.weight        = parent.weight - sibling.weight;
            output.sample_weight = parent.sample_weight - sibling.sample_weight;
            output.lab_sum       = parent.lab_sum - sibling.lab_sum;
            for (uint32_t cl = 0; cl < this->num_classes_; cl++) {
                // output.num_pos = parent.num_pos - sibling.num_pos;
                output.num[cl] = parent.num[cl] - sibling.num[cl];
                // output.lab_sum = parent.lab_sum - sibling.lab_sum;
                output.wnum[cl] = parent.wnum[cl] - sibling.wnum[cl];
            }
            // if (0 != output.weight)
            //     nonempty_bins[ft]++;
        }
    });
    // stopping criterion : each feature has only one non-empty
    // bin <-> for each feature, all examples fall in the same bin
    // uint32_t tot_bins = 0;
    // for (uint32_t ftp = 0; ftp < fts_.size(); ++ftp) {
    //     const uint32_t ft = fts_[ftp];
    //     assert(1 <= nonempty_bins[ft]); // at least one non empty
    //     tot_bins += nonempty_bins[ft];
    // }
    // return tot_bins;
    return 2 * this->num_ft_;
}

}

#endif