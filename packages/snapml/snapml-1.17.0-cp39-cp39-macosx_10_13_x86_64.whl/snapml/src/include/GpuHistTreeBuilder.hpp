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

#ifndef GPU_HIST_TREE_BUILDER
#define GPU_HIST_TREE_BUILDER

#include "HistTreeBuilder.hpp"
#include "TreeInvariants.hpp"
#include "TreeNode.hpp"
#include "HistSolverGPUFactory.hpp"

#include <stack>
#include <atomic>

namespace tree {

template <class N> class GpuHistTreeBuilder : public HistTreeBuilder<N> {

public:
    typedef std::chrono::high_resolution_clock             Clock;
    typedef std::chrono::high_resolution_clock::time_point CurTime;
    typedef typename N::hist_bin_t                         hist_bin_t;

    // ctor without TreeInvariants (for standalone use)
    GpuHistTreeBuilder<N>(glm::DenseDataset* data, snapml::DecisionTreeParams params)
        : HistTreeBuilder<N>(data, params)
    {
        // construct hist solver gpu
        if (this->params_.use_gpu) {
#ifdef WITH_CUDA
            hist_solver_gpu_
                = std::make_shared<HistSolverGPUFactory>()->make<N>(this->tree_invariants_, this->params_.gpu_id);
#else
            throw std::runtime_error("Snap ML was not compiled with GPU support.");
#endif
        }
    }

    // ctor with TreeInvariants and HistSolver (for use within an ensemble)
    GpuHistTreeBuilder<N>(glm::DenseDataset* data, snapml::DecisionTreeParams params,
                          const std::shared_ptr<glm::TreeInvariants<glm::DenseDataset>> tree_invariants,
                          const std::shared_ptr<HistSolver<N>>                          hist_solver_gpu)
        : HistTreeBuilder<N>(data, params, tree_invariants)
        , hist_solver_gpu_(hist_solver_gpu)

    {
    }

    ~GpuHistTreeBuilder<N>() { }

private:
    void init_invariants() override
    {
        this->tree_invariants_->init(this->data_, this->params_.task, this->params_.n_threads,
                                     this->params_.num_classes);
        this->tree_invariants_->init_hist(this->data_, this->params_.task, this->hist_nbins_);
        hist_solver_gpu_->init(this->data_, this->params_);
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
        double  gpu_steps[10] = { 0.0 };
        CurTime t1, t2, t3;
        if (omp_get_thread_num() == 0)
            t1 = Clock::now();
#endif

        this->training_predictions_.resize(this->num_ex_, std::numeric_limits<double>::max());
        this->go_left_.resize(this->num_ex_);

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

        // glm::cuda_safe(cudaHostRegister(node_ex_p.get()->data(), this->num_ex_effective_*sizeof(ex_lab_t),
        // cudaHostRegisterMapped), "[build_tree_impl_with_historams] could not pin host memory");
        N* const root = &this->node_info_[0];

        hist_solver_gpu_->set_thread_context();
        hist_solver_gpu_->init_fts(
            this->fts_, this->max_features_ < this->num_ft_ ? this->max_features_ : this->fts_.size(), this->rng_());
        hist_solver_gpu_->init_nex_labs(this->indices_, sample_weight, this->labs_);

        const bool shuffle = this->max_features_ < this->num_ft_ && 1.0 == this->params_.colsample_bytree;
        if (shuffle)
            hist_solver_gpu_->update_node_size(0 /* just shuffle */, shuffle);
        hist_solver_gpu_->process_initial_node(this->num_ex_effective_, 0, root);
        assert(root->get_num() == this->num_ex_effective_);
        // find the best split
        // root->pretty_print(0);
        const bool stop = (this->max_depth_ <= tot_depth) || (1 == root->get_num());
        if (stop) {
            if (this->params_.compute_training_predictions)
                hist_solver_gpu_->update_training_preds(root, 0, tot_depth);
        } else {
            assert(3 <= this->node_info_.size());
            std::atomic<uint32_t> num_active_ex(this->num_ex_effective_);
            std::atomic<uint32_t> idx_alloc(1);
            std::atomic<uint32_t> stack_nr(0);
            split_node_gpu(0, tot_depth, num_active_ex, idx_alloc, stack_nr, lifo, mtx);

            num_nodes = idx_alloc;
            tot_depth += 1;
        }

        // not used beyond init
        this->indices_.clear();
        this->indices_.shrink_to_fit();

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

        const uint32_t old_n_threads = omp_get_max_threads();
        omp_set_num_threads(std::min(MAX_STREAM_NR, this->params_.n_threads));
        // GPU BFS Solver
        uint32_t              prev_node = 1;
        std::atomic<uint32_t> num_active_ex(this->num_ex_effective_);
        std::atomic<bool>     exit_th(false);
        std::atomic<uint32_t> idx_alloc(num_nodes);
        std::atomic<uint32_t> stack_nr(lifo.size());
        uint32_t              cpu_tot_depth = tot_depth;
        std::thread           cpu_th;
        {
            const uint32_t max_nodes_alloc = this->max_depth_ < 63
                                                 ? std::min(1ULL << (this->max_depth_ + 1), 2ULL * this->num_ex_)
                                                 : 2 * this->num_ex_;
            this->node_info_.resize(max_nodes_alloc);
        }
        cpu_th = std::thread([&]() {
            std::stack<std::tuple<uint32_t, uint32_t, std::unique_ptr<std::vector<ex_lab_t>>,
                                  std::unique_ptr<std::vector<std::vector<hist_bin_t>>>>>
                                                     lifo_local; // (node_idx, depth, exs) stack
            const std::vector<std::vector<uint8_t>>& ex_to_bin      = this->tree_invariants_->get_ex_to_bin();
            const std::vector<std::vector<float>>&   hist_val       = this->tree_invariants_->get_hist_val();
            uint32_t                                 node_alloc_idx = this->node_info_.size();
            omp_set_num_threads(MAX_STREAM_NR < this->params_.n_threads ? this->params_.n_threads - MAX_STREAM_NR : 1U);

            while (!exit_th || 0 < stack_nr) {
                if (0 == stack_nr)
                    continue;
                if (exit_th)
                    omp_set_num_threads(this->params_.n_threads);
                mtx.lock();
                lifo_local.push(std::move(lifo.top()));
                lifo.pop();
                stack_nr--;
                mtx.unlock();
                while (!lifo_local.empty()) {
                    const uint32_t node_idx                      = std::get<0>(lifo_local.top());
                    const uint32_t depth                         = std::get<1>(lifo_local.top());
                    cpu_tot_depth                                = std::max(depth, cpu_tot_depth);
                    std::unique_ptr<std::vector<ex_lab_t>> nex_p = std::move(std::get<2>(lifo_local.top()));
                    lifo_local.pop();
                    std::unique_ptr<std::vector<std::vector<hist_bin_t>>> hist_bins_p(
                        new std::vector<std::vector<hist_bin_t>>(
                            this->num_ft_, std::vector<hist_bin_t>(this->hist_nbins_, this->num_classes_)));
                    N* node = &this->node_info_[node_idx];
                    // stopping criterion : depth
                    assert(node->get_num() <= this->num_ex_effective_);
#ifdef DEBUG_VERIFY
                    printf("popped node=%u,%ulen,%iparent from cpu stack\n", node_idx, node->get_num(),
                           node->get_parent());
#endif

                    const bool stop = this->max_depth_ <= depth || node->stopping_criterion() || node->get_num() < 2;
                    // fprintf(stdout, "num_nodes=%u depth=%u node=%p nidx=%u num=%u stop=%d pred=%lf\n",
                    //         num_nodes, depth, nex_p.get(), node_idx, node->get_num(), stop,
                    //         node->get_pred_val());
                    if (stop) {
                        if (this->params_.compute_training_predictions) {
                            // node->pretty_print(node_idx);
                            HistTreeBuilder<N>::update_training_predictions(node, nex_p);
                        }
                        continue;
                    }
                    assert(nullptr != hist_bins_p.get());

                    // added support for colsample_bytree
                    if (this->max_features_ < this->num_ft_ && 1.0 == this->params_.colsample_bytree) {
                        fisher_yates(this->fts_, this->rng_);
                    }

                    HistTreeBuilder<N>::template recompute_hist_bin<false>(*nex_p, ex_to_bin, hist_bins_p,
                                                                           this->max_features_);
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
                    if (-1 == node->get_best_feature()) {
                        if (this->params_.compute_training_predictions) {
                            // node->pretty_print(node_idx);
                            HistTreeBuilder<N>::update_training_predictions(node, nex_p);
                        }
                        continue; // no split found
                    }
                    // perform the split
                    assert(idx_alloc <= node_alloc_idx - 2);
                    const uint32_t left_idx  = node_alloc_idx - 2;
                    const uint32_t right_idx = left_idx + 1;
                    node_alloc_idx -= 2;
                    node->update_parent(left_idx, right_idx);

                    N* const left  = &this->node_info_[left_idx];
                    N* const right = &this->node_info_[right_idx];

                    left->update_left_child(node, node_idx);
                    right->update_right_child(node, node_idx);
                    const uint32_t left_num  = left->get_num();
                    const uint32_t right_num = right->get_num();
                    assert(left_num <= this->num_ex_effective_);
                    assert(right_num <= this->num_ex_effective_);
                    assert(left_num + right_num == node->get_num());

                    const bool     left_gt   = right_num < left_num;
                    const uint32_t new_ex_nr = std::min(left_num, right_num);

                    assert(0 < new_ex_nr);
                    std::unique_ptr<std::vector<ex_lab_t>> new_ex(new std::vector<ex_lab_t>(new_ex_nr));
                    std::unique_ptr<std::vector<ex_lab_t>> left_ex;
                    std::unique_ptr<std::vector<ex_lab_t>> right_ex;
                    if (left_gt) {
                        left_ex  = std::move(nex_p);
                        right_ex = std::move(new_ex);
                    } else {
                        left_ex  = std::move(new_ex);
                        right_ex = std::move(nex_p);
                    }

                    const uint32_t best_ft       = node->get_best_feature();
                    const float    best_thr      = node->get_best_threshold();
                    const uint32_t len           = left_num + right_num;
                    uint32_t       left_fill_idx = 0, right_fill_idx = 0;
                    for (uint32_t idx = 0; idx < len; ++idx) {
                        const auto&    ex      = left_gt ? (*left_ex)[idx] : (*right_ex)[idx];
                        const uint32_t bin_idx = ex_to_bin[best_ft][ex.idx];
                        if (hist_val[best_ft][bin_idx] < best_thr)
                            (*left_ex)[left_fill_idx++] = ex;
                        else
                            (*right_ex)[right_fill_idx++] = ex;
                    }
                    assert(left_num == left_fill_idx);
                    assert(right_num == right_fill_idx);

                    const bool stop_all = (this->max_depth_ <= depth + 1) || (left_num <= 1 && right_num <= 1);
                    if (stop_all) {
                        cpu_tot_depth = std::max(depth + 1, cpu_tot_depth);
                        if (this->params_.compute_training_predictions) {
                            // left->pretty_print(left_idx);
                            // right->pretty_print(right_idx);
                            HistTreeBuilder<N>::update_training_predictions(left, left_ex);
                            HistTreeBuilder<N>::update_training_predictions(right, right_ex);
                        }
                        continue;
                    }
                    // trim unused space from the larger array, all
                    // those examples are in the smaller one now
                    if (left_gt)
                        left_ex->erase(left_ex->begin() + left_fill_idx, left_ex->end());
                    else
                        right_ex->erase(right_ex->begin() + right_fill_idx, right_ex->end());

                    lifo_local.push(std::make_tuple(right_idx, depth + 1, std::move(right_ex), nullptr));
                    lifo_local.push(std::make_tuple(left_idx, depth + 1, std::move(left_ex), nullptr));

                } // local_stack loop
            }     // outer stack loop
        });
        while (this->num_ex_effective_ >= 2 * this->params_.min_samples_leaf && prev_node < num_nodes
               && tot_depth < this->max_depth_) {
            const uint32_t node_min = prev_node;
            const uint32_t node_max = num_nodes;
            prev_node               = num_nodes;
            {
                const uint32_t num_new_nodes = (node_max - node_min) * 2U;
                if (this->node_info_.size() < num_nodes + num_new_nodes) {
                    assert(0);
                    this->node_info_.resize(this->node_info_.size() + num_new_nodes + 1024U);
                }
                // added support for colsample_bytree
                const bool shuffle = this->max_features_ < this->num_ft_ && 1.0 == this->params_.colsample_bytree;
                hist_solver_gpu_->update_node_size(this->node_info_.size(), shuffle);
            }
            idx_alloc = node_max;
            assert(node_max == idx_alloc);

#ifdef TIME_PROFILE
            if (omp_get_thread_num() == 0) {
                t2       = Clock::now();
                auto dur = t2 - t1;
                gpu_steps[1] += (double)dur.count() / 1.0e9;
                t1 = t2;
            }
#endif

            assert(2 <= node_max - node_min && (node_max - node_min) % 2 == 0);
            OMP::parallel_for_sched_dynamic<int32_t>(
                node_min, node_max - 1, 2,
                [this, &tot_depth, &node_min, &mtx, &lifo, &stack_nr, &num_active_ex, &idx_alloc](int32_t node_idx) {
                    N* const       pleft      = &this->node_info_[node_idx];
                    N* const       pright     = &this->node_info_[node_idx + 1];
                    const uint32_t pleft_idx  = node_idx;
                    const uint32_t pright_idx = node_idx + 1;
                    const uint32_t pleft_num = pleft->get_num(), pright_num = pright->get_num();
                    if (1 < pleft_num && pleft_num * this->fts_.size() < GPU_MIN_EXFT_ && 1 < pright_num
                        && pright_num * this->fts_.size() < GPU_MIN_EXFT_)
                        return;
                    bool stop_pleft  = this->max_depth_ <= tot_depth || pleft_num < 2;
                    bool stop_pright = this->max_depth_ <= tot_depth || pright_num < 2;
                    hist_solver_gpu_->set_thread_context();
                    assert(pleft->get_parent() == pright->get_parent() && (uint32_t)pleft->get_parent() < node_min);
                    if (!stop_pleft && !stop_pright) {
                        // pair
                        int rc = hist_solver_gpu_->process_node_pair(tot_depth, pleft->get_parent(), node_idx,
                                                                     node_idx + 1, pleft, pright);
                        if (0 != rc) {
                            std::unique_ptr<std::vector<ex_lab_t>> lnex_p(new std::vector<ex_lab_t>(pleft->get_num()));
                            std::unique_ptr<std::vector<ex_lab_t>> rnex_p(new std::vector<ex_lab_t>(pright->get_num()));
                            hist_solver_gpu_->retrieve_nex(pleft, pleft_idx, tot_depth, lnex_p);
                            hist_solver_gpu_->retrieve_nex(pright, pright_idx, tot_depth, rnex_p);
                            mtx.lock();
                            lifo.push(std::make_tuple(pleft_idx, tot_depth, std::move(lnex_p), nullptr));
                            lifo.push(std::make_tuple(pright_idx, tot_depth, std::move(rnex_p), nullptr));
                            stack_nr += 2;
                            mtx.unlock(); // get it out and into the stack
                            return;
                        }
#ifdef TIME_PROFILE
                        if (omp_get_thread_num() == 0) {
                            t2       = Clock::now();
                            auto dur = t2 - t1;
                            gpu_steps[2] += (double)dur.count() / 1.0e9;
                            t1 = t2;
                        }
#endif
                        // splits
                        split_node_gpu(node_idx, tot_depth, num_active_ex, idx_alloc, stack_nr, lifo, mtx);
                        split_node_gpu(node_idx + 1, tot_depth, num_active_ex, idx_alloc, stack_nr, lifo, mtx);
                    } else if (stop_pright) {
                        // left
                        int rc = hist_solver_gpu_->process_single_node(pleft->get_num(), tot_depth, node_idx, pleft);
                        if (0 != rc) {
                            std::unique_ptr<std::vector<ex_lab_t>> lnex_p(new std::vector<ex_lab_t>(pleft->get_num()));
                            hist_solver_gpu_->retrieve_nex(pleft, pleft_idx, tot_depth, lnex_p);
                            mtx.lock();
                            lifo.push(std::make_tuple(pleft_idx, tot_depth, std::move(lnex_p), nullptr));
                            stack_nr += 1;
                            mtx.unlock(); // get it out and into the stack
                            return;
                        }

#ifdef TIME_PROFILE
                        if (omp_get_thread_num() == 0) {
                            t2       = Clock::now();
                            auto dur = t2 - t1;
                            gpu_steps[2] += (double)dur.count() / 1.0e9;
                            t1 = t2;
                        }
#endif

                        split_node_gpu(node_idx, tot_depth, num_active_ex, idx_alloc, stack_nr, lifo, mtx);
                        num_active_ex -= pright_num;
                        if (this->params_.compute_training_predictions)
                            hist_solver_gpu_->update_training_preds(pright, node_idx + 1, tot_depth);
                    } else if (stop_pleft) {
                        // right
                        int rc
                            = hist_solver_gpu_->process_single_node(pright->get_num(), tot_depth, node_idx + 1, pright);
                        if (0 != rc) {
                            std::unique_ptr<std::vector<ex_lab_t>> rnex_p(new std::vector<ex_lab_t>(pright->get_num()));
                            hist_solver_gpu_->retrieve_nex(pright, pright_idx, tot_depth, rnex_p);
                            mtx.lock();
                            lifo.push(std::make_tuple(pright_idx, tot_depth, std::move(rnex_p), nullptr));
                            stack_nr += 1;
                            mtx.unlock(); // get it out and into the stack
                            return;
                        }

#ifdef TIME_PROFILE
                        if (omp_get_thread_num() == 0) {
                            t2       = Clock::now();
                            auto dur = t2 - t1;
                            gpu_steps[2] += (double)dur.count() / 1.0e9;
                            t1 = t2;
                        }
#endif

                        split_node_gpu(node_idx + 1, tot_depth, num_active_ex, idx_alloc, stack_nr, lifo, mtx);
                        num_active_ex -= pleft_num;
                        if (this->params_.compute_training_predictions)
                            hist_solver_gpu_->update_training_preds(pleft, node_idx, tot_depth);
                    } else {
                        // stop both
                        num_active_ex -= pleft_num + pright_num;
                        if (this->params_.compute_training_predictions) {
                            // node->pretty_print(node_idx);
                            hist_solver_gpu_->update_training_preds(pleft, node_idx, tot_depth);
                            hist_solver_gpu_->update_training_preds(pright, node_idx + 1, tot_depth);
                        }
                    }
                // splits

#ifdef TIME_PROFILE
                    if (omp_get_thread_num() == 0) {
                        t2       = Clock::now();
                        auto dur = t2 - t1;
                        gpu_steps[3] += (double)dur.count() / 1.0e9;
                        t1 = t2;
                    }
#endif
                });
            num_nodes = idx_alloc;

            tot_depth++;
        }
        omp_set_num_threads(old_n_threads);
        assert(num_active_ex <= this->num_ex_effective_ || lifo.empty());
        if (this->params_.compute_training_predictions) { // && (this->subsample_size_ == num_ex_)) {
            const double* const gpu_preds = hist_solver_gpu_->retrieve_preds();
            OMP::parallel_for<int32_t>(0, this->num_ex_, [this, &gpu_preds](const int32_t& ex) {
                if (gpu_preds[ex] != std::numeric_limits<double>::max()) {
                    assert(this->training_predictions_[ex] == std::numeric_limits<double>::max());
                    this->training_predictions_[ex] = gpu_preds[ex];
                }
            });
        }

#ifdef TIME_PROFILE
        if (omp_get_thread_num() == 0) {
            t2       = Clock::now();
            auto dur = t2 - t1;
            gpu_steps[7] += (double)dur.count() / 1.0e9;
            t1 = t2;
        }
#endif

        exit_th = true;
        if (cpu_th.joinable())
            cpu_th.join();
        assert(lifo.empty());
        tot_depth = std::max(tot_depth, cpu_tot_depth);
        num_nodes = this->node_info_.size();

#ifdef TIME_PROFILE
        if (omp_get_thread_num() == 0) {
            t2       = Clock::now();
            auto dur = t2 - t1;
            gpu_steps[8] += (double)dur.count() / 1.0e9;
            dur = t2 - t2;
            gpu_steps[9] += (double)dur.count() / 1.0e9;
            t1 = t2;
        }
#endif

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
            if (this->params_.use_gpu) {
                printf("[BinaryDecisionTree::build_tree_impl_with_histograms] GPU1: %e [update nodes]\n", gpu_steps[0]);
                printf("[BinaryDecisionTree::build_tree_impl_with_histograms] GPU2: %e [resize]\n", gpu_steps[1]);
                printf("[BinaryDecisionTree::build_tree_impl_with_histograms] GPU3: %e [recompute]\n", gpu_steps[2]);
                printf("[BinaryDecisionTree::build_tree_impl_with_histograms] GPU4: %e [split]\n", gpu_steps[3]);
                printf("[BinaryDecisionTree::build_tree_impl_with_histograms] GPU5: %e [update training preds]\n",
                       gpu_steps[4]);
                printf("[BinaryDecisionTree::build_tree_impl_with_histograms] GPU5: %e [split sibling]\n",
                       gpu_steps[5]);
                printf("[BinaryDecisionTree::build_tree_impl_with_histograms] GPU5: %e [retrieve nex and post]\n",
                       gpu_steps[6]);
                printf("[BinaryDecisionTree::build_tree_impl_with_histograms] GPU6: %e [retrieve preds]\n",
                       gpu_steps[7]);
                printf("[BinaryDecisionTree::build_tree_impl_with_histograms] GPU6: %e [wait CPU thread]\n",
                       gpu_steps[8]);
                printf("[BinaryDecisionTree::build_tree_impl_with_histograms] GPU7: %e [total GPU]\n", gpu_steps[9]);
            }
        }
#endif
    }

    void split_node_gpu(const uint32_t node_idx, const uint32_t tot_depth, std::atomic<uint32_t>& num_active_ex,
                        std::atomic<uint32_t>& idx_alloc, std::atomic<uint32_t>& stack_nr,
                        std::stack<std::tuple<uint32_t, uint32_t, std::unique_ptr<std::vector<ex_lab_t>>,
                                              std::unique_ptr<std::vector<std::vector<hist_bin_t>>>>>& lifo,
                        std::mutex&                                                                    mtx)
    {
        N* const   node = &this->node_info_[node_idx];
        const bool stop = node->stopping_criterion() || -1 == node->get_best_feature();
        if (stop) {
            num_active_ex -= node->get_num();
            if (this->params_.compute_training_predictions) {
                // node->pretty_print(node_idx);
                hist_solver_gpu_->update_training_preds(node, node_idx, tot_depth);
            }
            return; // no split needed, this is a leaf node
        }
        const uint32_t left_idx  = idx_alloc.fetch_add(2U);
        const uint32_t right_idx = left_idx + 1;
        N* const       left      = &this->node_info_[left_idx];
        N* const       right     = &this->node_info_[right_idx];
        node->update_parent(left_idx, right_idx);
        left->update_left_child(node, node_idx);
        right->update_right_child(node, node_idx);
        assert(left->get_num() + right->get_num() == node->get_num());
        assert(node->get_num() <= this->num_ex_effective_ && left->get_num() < this->num_ex_effective_
               && right->get_num() < this->num_ex_effective_);
#ifdef DEBUG_VERIFY
        node->pretty_print(node_idx);
#endif
        hist_solver_gpu_->split_single_node(node->get_best_feature(), node->get_best_threshold(), tot_depth, left,
                                            right, node_idx, left_idx, right_idx);
        if (this->max_depth_ <= tot_depth + 1) {
            num_active_ex -= left->get_num() + right->get_num();
            if (this->params_.compute_training_predictions) {
                // left->pretty_print(left_idx);
                // right->pretty_print(right_idx);
                hist_solver_gpu_->update_training_preds(left, left_idx, tot_depth + 1);
                hist_solver_gpu_->update_training_preds(right, right_idx, tot_depth + 1);
            }
        } else if (1 < left->get_num() && left->get_num() * this->fts_.size() < GPU_MIN_EXFT_ && 1 < right->get_num()
                   && right->get_num() * this->fts_.size() < GPU_MIN_EXFT_) {
            std::unique_ptr<std::vector<ex_lab_t>> lnex_p(new std::vector<ex_lab_t>(left->get_num()));
            std::unique_ptr<std::vector<ex_lab_t>> rnex_p(new std::vector<ex_lab_t>(right->get_num()));
            hist_solver_gpu_->retrieve_nex(left, left_idx, tot_depth + 1, lnex_p);
            hist_solver_gpu_->retrieve_nex(right, right_idx, tot_depth + 1, rnex_p);
#ifdef DEBUG_VERIFY
            printf("pushed l=%u,%ulen r=%u,%ulen nodes into cpu stack\n", left_idx, left->get_num(), right_idx,
                   right->get_num());
#endif
            mtx.lock();
            lifo.push(std::make_tuple(left_idx, tot_depth + 1, std::move(lnex_p), nullptr));
            lifo.push(std::make_tuple(right_idx, tot_depth + 1, std::move(rnex_p), nullptr));
            stack_nr += 2;
            mtx.unlock(); // get it out and into the stack

            // } else {
            //     if (1 < left->get_num() && left->get_num() * num_ft_effective_ < GPU_MIN_EXFT_) {
            //         std::unique_ptr<std::vector<ex_lab_t>> nex_p (new std::vector<ex_lab_t> (left->get_num()));
            //         hist_solver_gpu_->retrieve_nex(left, left_idx, tot_depth + 1, nex_p);
            //         mtx.lock();
            //         lifo.push(std::make_tuple(left_idx, tot_depth + 1, std::move(nex_p), left_gt ?
            //         std::move(new_hist_gt) : std::move(new_hist_lt))); mtx.unlock();
            //     }
            //     if (1 < right->get_num() && right->get_num() * fts_.size() < GPU_MIN_EXFT_) {
            //         std::unique_ptr<std::vector<ex_lab_t>> nex_p (new std::vector<ex_lab_t> (right->get_num()));
            //         hist_solver_gpu_->retrieve_nex(right, right_idx, tot_depth + 1, nex_p);
            //         mtx.lock();
            //         lifo.push(std::make_tuple(right_idx, tot_depth + 1, std::move(nex_p), left_gt ?
            //         std::move(new_hist_lt) : std::move(new_hist_gt))); mtx.unlock();// get it out and into the stack
            //     }
        }
    }

    static constexpr uint32_t      GPU_MIN_EXFT_ = 10000;
    std::shared_ptr<HistSolver<N>> hist_solver_gpu_;
};

}

#endif
