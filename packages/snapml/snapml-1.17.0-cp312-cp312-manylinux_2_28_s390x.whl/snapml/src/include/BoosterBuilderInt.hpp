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
 *                Jan van Lunteren
 *                Milos Stanisavljevic
 *
 * End Copyright
 ********************************************************************/

#ifndef BOOSTER_BUILDER
#define BOOSTER_BUILDER

#include "Builder.hpp"
#include "BoosterParams.hpp"
#include "DenseDatasetInt.hpp"
#include "TreeInvariants.hpp"
#include "TreeNode.hpp"
#include "HistSolver.hpp"
#include "HistSolverGPUFactory.hpp"
#include "ExactTreeBuilder.hpp"
#include "CpuHistTreeBuilder.hpp"
#include "GpuHistTreeBuilder.hpp"
#include "TreeBuilderFactory.hpp"
#include "KernelRidgeEnsembleModel.hpp"
#include "BoosterModelInt.hpp"
#include "TreeEnsembleModel.hpp"
#include "RBFSampler.hpp"
#include "RidgeClosed.hpp"

#define MIN_VAL_HESSIAN 1e-20

namespace tree {

class BoosterBuilder : public Builder<BoosterModel> {

public:
    using reduction_t = RBFSampler::reduction_t;

    typedef std::chrono::high_resolution_clock             Clock;
    typedef std::chrono::high_resolution_clock::time_point CurTime;

    BoosterBuilder(glm::DenseDataset* data, glm::DenseDataset* val_data, snapml::BoosterParams params)
        : Builder(static_cast<glm::Dataset*>(data), params.num_classes)
        , val_data_(val_data)
        , params_(params)
        , random_state_(0)
        , rbf_random_state_(0)
    {
        if ((params_.objective == snapml::BoosterParams::objective_t::softmax) && (num_classes_ == 2)) {
            throw std::runtime_error("For binary classification please use logloss objective.");
        }

        if ((params_.objective == snapml::BoosterParams::objective_t::logloss) && (num_classes_ > 2)) {
            throw std::runtime_error("For multi-class classification please use softmax objective.");
        }

        // Poisson objective log link function
        if (params_.objective == snapml::BoosterParams::objective_t::poisson) {
            if (params_.base_prediction > 0.0)
                params_.base_prediction = std::log(params_.base_prediction);
            else {
                throw std::runtime_error("For poisson regression the base score must be strictly positive");
            }
            if (params_.max_delta_step == 0.0)
                params_.max_delta_step = 0.7;
        }

        if (params_.gpu_ids.size() > 0) {
            params_.use_gpu = true;
        }

        if (params_.use_gpu && params_.gpu_ids.size() == 0) {
            params_.gpu_ids = { 0 };
        }

        if (params_.use_gpu) {
            if (!params_.use_histograms)
                throw std::runtime_error("GPU acceleration only supported for histograms");
        }

        regressors_per_round_ = (params_.objective == snapml::BoosterParams::objective_t::softmax) ? num_classes_ : 1;

        if (params_.gpu_ids.size() > 1 && regressors_per_round_ == 1) {
            throw std::runtime_error("Multi-GPU is not supported for binary classification / regression");
        }

        if (params_.gpu_ids.size() > regressors_per_round_) {
            std::cout << "[Warning] Will not use more GPUs than the number of classes." << std::endl;
        }

        if (params_.n_threads < params_.gpu_ids.size()) {
            throw std::runtime_error("Need at least one thread per GPU");
        }

        // Next, we define the number of outer threads (which run in parallel over the regressors per round)
        if (params_.use_gpu) {
            // in GPU training mode
            // if there are less GPUs than the # regressors per round, then we spawn an outer thread per GPU and
            // partition the regressors across them
            n_outer_threads_ = std::min(static_cast<uint32_t>(params_.gpu_ids.size()), regressors_per_round_);
        } else {
            // in CPU training mode
            // if there are less threads than the # regressors per round, we will partition the regressors across the
            // outer threads
            n_outer_threads_ = std::min(params_.n_threads, regressors_per_round_);
        }

        // If there are threads remaining, we split them across the outer threads for parallelizing tree-building and/or
        // ridge-building
        n_inner_threads_ = std::max(params_.n_threads / n_outer_threads_, 1U);
    }

    void init() override { init_impl(); }

    void build(const float* const sample_weight, const float* const sample_weight_val = nullptr,
               const double* const labels = nullptr) override
    {
        build_impl(sample_weight, sample_weight_val);
    }

    size_t get_full_feature_importances_size() override { return cls_feature_importances_[0].size(); }

    void get_full_feature_importances(double* const out, uint32_t len) override
    {

        assert(len == cls_feature_importances_[0].size());

        uint32_t num_sets = cls_feature_importances_[0].size() / num_ft_;

        for (uint32_t set = 0; set < num_sets; set++) {

            double* const this_out = &out[set * num_ft_];

            for (uint32_t i = 0; i < num_ft_; i++) {
                this_out[i] = 0.0;
            }

            for (uint32_t cls = 0; cls < cls_feature_importances_.size(); cls++) {
                for (uint32_t i = 0; i < num_ft_; i++) {
                    this_out[i] += cls_feature_importances_[cls][set * num_ft_ + i];
                }
            }
        }
    }

private:
    void init_impl()
    {

        omp_set_num_threads(params_.n_threads);

        rng_.seed(params_.random_state);

        CurTime t0, t1;

        if (omp_get_thread_num() == 0)
            t0 = Clock::now();

        // setting the random state of the kernel and ridge components
        rbf_random_state_ = rng_();

        uint32_t pred_size = regressors_per_round_ * num_ex_;

        // if the number of classes gets large, this could get very large
        running_pred_.resize(pred_size, params_.base_prediction);

        weights_.resize(pred_size, 1.0);
        target_.resize(pred_size, 0.0);

        pred_tmp_.resize(n_outer_threads_ * num_ex_, 0.0);

        if (val_data_ != nullptr) {
            uint32_t num_ex_val    = val_data_->get_num_ex();
            uint32_t val_pred_size = regressors_per_round_ * num_ex_val;
            running_val_pred_.resize(val_pred_size, params_.base_prediction);
            pred_val_tmp_.resize(n_outer_threads_ * num_ex_val, 0.0);
        }

        float* labs_ptr = this->data_->get_labs();

        labs_.resize(num_ex_);
        OMP::parallel_for<int32_t>(0, num_ex_, [this, &labs_ptr](const int32_t& ex) { labs_[ex] = labs_ptr[ex]; });

        if (params_.objective == snapml::BoosterParams::objective_t::logloss) {
            OMP::parallel_for<int32_t>(0, num_ex_,
                                       [this](const int32_t& ex) { labs_[ex] = (labs_[ex] > 0) ? +1.0 : -1.0; });
        }

        // poisson loss - labels must be >0
        if (params_.objective == snapml::BoosterParams::objective_t::poisson) {
            OMP::parallel_for<int32_t>(0, num_ex_, [this](const int32_t& ex) {
                if (labs_[ex] < 0.0)
                    throw std::runtime_error("Poisson Objective: Labels cannot be negative");
            });
        }

        // decide up-front which regressors will be trees and which will be krrs
        std::uniform_real_distribution<float> learner_dist(0, 1);
        learner_types_.resize(params_.n_regressors);
        uint32_t n_trees = 0;
        for (uint32_t it = 0; it < params_.n_regressors; it++)
            if (learner_dist(rng_) < params_.select_probability)
                n_trees++;
            else
                learner_types_[it]++;
        uint32_t n_linear = params_.n_regressors - n_trees;

        cls_feature_importances_.resize(regressors_per_round_);
        for (uint32_t cls = 0; cls < regressors_per_round_; cls++) {
            if (params_.aggregate_importances) {
                cls_feature_importances_[cls].resize(num_ft_, 0.0);
            } else {
                cls_feature_importances_[cls].resize(n_trees * num_ft_, 0.0);
            }
        }

        if (omp_get_thread_num() == 0)
            t1 = Clock::now();
        profile_.t_init_booster = t_elapsed(t0, t1);

        // initialize trees
        if (omp_get_thread_num() == 0)
            t0 = Clock::now();

        // initailize trees
        init_trees(n_trees);

        if (omp_get_thread_num() == 0)
            t1 = Clock::now();
        profile_.t_init_trees = t_elapsed(t0, t1);

        // initialize linear_models
        if (omp_get_thread_num() == 0)
            t0 = Clock::now();
        init_linear(n_linear);
        if (omp_get_thread_num() == 0)
            t1 = Clock::now();
        profile_.t_init_linear = t_elapsed(t0, t1);
    }

    void init_trees(uint32_t n_trees)
    {

        if (n_trees == 0) {
            return;
        }

        // construct tree invariants
        tree_invariants_ = std::make_shared<glm::TreeInvariants<glm::DenseDataset>>();

        // construct hist solver gpu
        if (params_.gpu_ids.size()) {
#ifdef WITH_CUDA
            for (const uint32_t gpu_id : params_.gpu_ids) {
                hist_solvers_gpu_.push_back(
                    std::make_shared<HistSolverGPUFactory>()->make<RegTreeNode>(tree_invariants_, gpu_id));
            }
#else
            throw std::runtime_error("Snap ML was not compiled with GPU support.");
#endif
        }

        tree_invariants_->init(data_, snapml::task_t::regression, params_.n_threads, 2);

        if (params_.use_histograms) {
            tree_invariants_->init_hist(data_, snapml::task_t::regression, params_.hist_nbins, false);

            for (auto& hist_solver_gpu : hist_solvers_gpu_) {
                random_state_ = rng_();
                hist_solver_gpu->init(data_, getTreeParams());
            }

            // Sorted matrix not used beyond this point _for_ histograms
            tree_invariants_->clear_sorted_matrix();
        }

        // random generators used for the depth of the tree learners
        std::uniform_int_distribution<uint32_t> depth_dist(params_.min_max_depth, params_.max_max_depth);

        // initialize all TreeParams
        tree_param_array_.resize(n_trees * regressors_per_round_, getTreeParams());
        for (uint32_t tree = 0; tree < n_trees; tree++) {
            uint32_t this_depth = depth_dist(rng_);
            for (uint32_t cls = 0; cls < regressors_per_round_; cls++) {
                tree_param_array_[tree * regressors_per_round_ + cls].max_depth    = this_depth;
                tree_param_array_[tree * regressors_per_round_ + cls].random_state = rng_();
            }
        }

        for (uint32_t cls = 0; cls < regressors_per_round_; cls++) {
            tree_ensemble_models_.push_back(std::make_shared<TreeEnsembleModel>(snapml::task_t::regression, 2));
        }
    }

    void init_linear(uint32_t n_linear)
    {

        if (n_linear == 0) {
            return;
        }

        for (uint32_t cls = 0; cls < regressors_per_round_; cls++) {
            kr_ensemble_models_.push_back(std::make_shared<KernelRidgeEnsembleModel>(getRFBParams().n_components));
        }

        uint32_t rbf_threads = getRFBParams().n_threads;
        assert(rbf_threads == params_.n_threads);

        auto rbf_obj = std::make_shared<RBFSampler>(getRFBParams());

        // generate the kernel map of size (num_ft, n_components)
        rbf_obj->fit(num_ft_);

        new_data_ = rbf_obj->transform(static_cast<glm::DenseDataset*>(data_));

        if (val_data_ != nullptr) {
            new_val_data_ = rbf_obj->transform(static_cast<glm::DenseDataset*>(val_data_));
        }
    }

    void build_tree(const bool use_sample_weights, const uint32_t tree_idx, const uint32_t n_outer_threads,
                    const uint32_t outer_thd_id, const uint32_t n_inner_threads)
    {
        try {
            omp_set_num_threads(n_inner_threads_);

            for (uint32_t cls = outer_thd_id; cls < regressors_per_round_; cls += n_outer_threads) {

                snapml::DecisionTreeParams& tree_params = tree_param_array_[tree_idx * regressors_per_round_ + cls];

                assert(tree_params.n_threads == n_inner_threads_);

                auto factory = std::make_shared<TreeBuilderFactory>();

                std::shared_ptr<DecisionTreeBuilder<RegTreeNode>> tree_builder;

                if (params_.use_histograms) {
                    if (params_.gpu_ids.size()) {
                        tree_builder = factory->make<GpuHistTreeBuilder<RegTreeNode>>(
                            static_cast<glm::DenseDataset*>(data_), tree_params, tree_invariants_,
                            hist_solvers_gpu_[outer_thd_id]);
                    } else {
                        tree_builder = factory->make<CpuHistTreeBuilder<RegTreeNode>>(
                            static_cast<glm::DenseDataset*>(data_), tree_params, tree_invariants_, nullptr);
                    }
                } else {
                    tree_builder = factory->make<ExactTreeBuilder<RegTreeNode>>(static_cast<glm::DenseDataset*>(data_),
                                                                                tree_params, tree_invariants_, nullptr);
                }

                tree_builder->init();
                if (use_sample_weights) {
                    tree_builder->build(&weights_[cls * num_ex_], nullptr, &target_[cls * num_ex_]);
                } else {
                    tree_builder->build(nullptr, nullptr, &target_[cls * num_ex_]);
                }

                auto model = tree_builder->get_model();

                if (params_.use_histograms) {

                    auto hist_tree_builder = static_cast<HistTreeBuilder<RegTreeNode>*>(tree_builder.get());

                    const double* const training_predictions = hist_tree_builder->get_training_predictions();

                    double* const this_running_pred = &running_pred_[cls * num_ex_];
                    OMP::parallel_for<int32_t>(
                        0, num_ex_, [this, &training_predictions, &this_running_pred](const int32_t& ex) {
                            this_running_pred[ex] += params_.learning_rate * training_predictions[ex];
                        });

                } else {

                    auto predictor = std::make_shared<TreePredictor>(model);

                    double* const this_pred_tmp     = &pred_tmp_[outer_thd_id * num_ex_];
                    double* const this_running_pred = &running_pred_[cls * num_ex_];

                    std::fill_n(this_pred_tmp, num_ex_, 0.0);
                    predictor->predict(static_cast<glm::DenseDataset*>(data_), this_pred_tmp, n_inner_threads);

                    OMP::parallel_for<int32_t>(0, num_ex_,
                                               [this, &this_running_pred, &this_pred_tmp](const int32_t& ex) {
                                                   this_running_pred[ex] += params_.learning_rate * this_pred_tmp[ex];
                                               });
                }

                // update validation predictions
                if (val_data_ != nullptr) {

                    auto predictor = std::make_shared<TreePredictor>(model);

                    const uint32_t val_num_ex            = val_data_->get_num_ex();
                    double* const  this_pred_val_tmp     = &pred_val_tmp_[outer_thd_id * val_num_ex];
                    double* const  this_running_val_pred = &running_val_pred_[cls * val_num_ex];

                    std::fill_n(this_pred_val_tmp, val_num_ex, 0.0);
                    predictor->predict(val_data_, this_pred_val_tmp, n_inner_threads);

                    OMP::parallel_for<int32_t>(
                        0, val_num_ex, [this, &this_running_val_pred, &this_pred_val_tmp](const int32_t& ex) {
                            this_running_val_pred[ex] += params_.learning_rate * this_pred_val_tmp[ex];
                        });
                }

                tree_ensemble_models_[cls]->insert_tree(model);

                if (params_.aggregate_importances) {
                    for (uint32_t j = 0; j < num_ft_; j++) {
                        cls_feature_importances_[cls][j] += tree_builder->get_feature_importance(j);
                    }
                } else {
                    for (uint32_t j = 0; j < num_ft_; j++) {
                        cls_feature_importances_[cls][tree_idx * num_ft_ + j] = tree_builder->get_feature_importance(j);
                    }
                }
            }
        } catch (...) {
            eptr = std::current_exception();
        }
    }

    void build_linear(const bool use_sample_weights, const uint32_t tree_idx, const uint32_t n_outer_threads,
                      const uint32_t outer_thd_id, const uint32_t n_inner_threads)
    {
        try {
            omp_set_num_threads(n_inner_threads);

            std::shared_ptr<glm::RidgeClosed::profile_t> ridge_profile
                = std::make_shared<glm::RidgeClosed::profile_t>();

            for (uint32_t cls = outer_thd_id; cls < regressors_per_round_; cls += n_outer_threads) {
                auto ridge = std::make_shared<glm::RidgeClosed>(getRidgeParams(), ridge_profile);
                if (use_sample_weights) {
                    ridge->fit(num_ex_, new_data_, &target_[cls * num_ex_], &weights_[cls * num_ex_]);
                } else {
                    ridge->fit(num_ex_, new_data_, &target_[cls * num_ex_]);
                }

                double* const this_pred_tmp     = &pred_tmp_[outer_thd_id * num_ex_];
                double* const this_running_pred = &running_pred_[cls * num_ex_];

                ridge->predict(new_data_, this_pred_tmp);
                OMP::parallel_for<int32_t>(0, num_ex_, [this, &this_running_pred, &this_pred_tmp](const int32_t& ex) {
                    this_running_pred[ex] += params_.learning_rate * this_pred_tmp[ex];
                });

                // update validation predictions
                if (val_data_ != nullptr) {

                    uint32_t      num_ex_val            = val_data_->get_num_ex();
                    double* const this_pred_val_tmp     = &pred_val_tmp_[outer_thd_id * num_ex_val];
                    double* const this_running_val_pred = &running_val_pred_[cls * num_ex_val];

                    ridge->predict(new_val_data_, this_pred_val_tmp);
                    OMP::parallel_for<int32_t>(
                        0, num_ex_val, [this, &this_running_val_pred, &this_pred_val_tmp](const int32_t& ex) {
                            this_running_val_pred[ex] += params_.learning_rate * this_pred_val_tmp[ex];
                        });
                }

                kr_ensemble_models_[cls]->insert_linear(ridge->get_intercept(), ridge->get_coef());
            }
        } catch (...) {
            eptr = std::current_exception();
        }
    }

    void build_impl(const float* const sample_weight, const float* const sample_weight_val)
    {

        omp_set_num_threads(params_.n_threads);

        CurTime t0, t1;

        double sample_weights_sum     = 0.0;
        double sample_weights_val_sum = 0.0;

        if (params_.verbose) {

            if (sample_weight != nullptr) {
                OMP::parallel_for_reduction<int32_t>(0, num_ex_, sample_weights_sum,
                                                     [&sample_weight](int32_t ex, double& sample_weights_sum) {
                                                         sample_weights_sum = sample_weights_sum + sample_weight[ex];
                                                     });
            } else {
                sample_weights_sum = num_ex_;
            }
        }

        if (val_data_ != nullptr) {

            if (sample_weight_val != nullptr) {
                OMP::parallel_for_reduction<int32_t>(0, val_data_->get_num_ex(), sample_weights_val_sum,
                                                     [&sample_weight_val](int32_t ex, double& sample_weights_val_sum) {
                                                         sample_weights_val_sum
                                                             = sample_weights_val_sum + sample_weight_val[ex];
                                                     });
            } else {
                sample_weights_val_sum = val_data_->get_num_ex();
            }
        }

        uint32_t tree_idx          = 0;
        uint32_t linear_idx        = 0;
        double   best_val_loss     = 0.0;
        uint32_t it_since_best_val = 0;
        uint32_t tree_idx_stop     = 0;
        uint32_t linear_idx_stop   = 0;
        bool     early_stop        = false;

        // should sample weights be used?
        const bool use_sample_weights
            = ((params_.objective != snapml::BoosterParams::objective_t::mse) || (sample_weight != nullptr));

        for (uint32_t it = 0; it < params_.n_regressors; it++) {

            if (early_stop) {

                if (omp_get_thread_num() == 0)
                    t0 = Clock::now();
                if (params_.verbose) {
                    printf("Stopping early after %u boosting rounds with validation loss: %e\n", it, best_val_loss);
                }

                for (auto te : tree_ensemble_models_) {
                    te->resize(tree_idx_stop);
                }

                for (auto kr : kr_ensemble_models_) {
                    kr->resize(linear_idx_stop);
                }

                for (auto fi : cls_feature_importances_) {
                    fi.resize(tree_idx_stop * num_ft_);
                }

                if (omp_get_thread_num() == 0)
                    t1 = Clock::now();
                profile_.t_stop += t_elapsed(t0, t1);

                break;
            }

            // compute target and weights
            if (omp_get_thread_num() == 0)
                t0 = Clock::now();
            compute_target_weights(sample_weight);
            if (omp_get_thread_num() == 0)
                t1 = Clock::now();
            profile_.t_target += t_elapsed(t0, t1);

            if (learner_types_[it] == 0) {

                if (omp_get_thread_num() == 0)
                    t0 = Clock::now();

                if (regressors_per_round_ > 1) {

                    // multi-class classification
                    std::vector<std::thread> thds;

                    for (uint32_t thd = 0; thd < n_outer_threads_; thd++) {
                        thds.push_back(std::thread(&BoosterBuilder::build_tree, this, use_sample_weights, tree_idx,
                                                   n_outer_threads_, thd, n_inner_threads_));
                    }

                    for (uint32_t thd = 0; thd < n_outer_threads_; thd++) {
                        thds[thd].join();
                    }

                } else {

                    build_tree(use_sample_weights, tree_idx, 1, 0, params_.n_threads);
                }

                if (omp_get_thread_num() == 0)
                    t1 = Clock::now();

                profile_.t_tree_fit += t_elapsed(t0, t1);

                tree_idx++;

            } else {

                if (omp_get_thread_num() == 0)
                    t0 = Clock::now();

                if (regressors_per_round_ > 1) {

                    // multi-class classification
                    std::vector<std::thread> thds;

                    for (uint32_t thd = 0; thd < n_outer_threads_; thd++) {
                        thds.push_back(std::thread(&BoosterBuilder::build_linear, this, use_sample_weights, linear_idx,
                                                   n_outer_threads_, thd, n_inner_threads_));
                    }

                    for (uint32_t thd = 0; thd < n_outer_threads_; thd++) {
                        thds[thd].join();
                    }

                } else {

                    build_linear(use_sample_weights, linear_idx, 1, 0, params_.n_threads);
                }

                if (omp_get_thread_num() == 0)
                    t1 = Clock::now();

                profile_.t_linear_fit += t_elapsed(t0, t1);

                linear_idx++;
            }

            if (eptr)
                std::rethrow_exception(eptr);

            double loss_val = 0.0;

            // compute validation loss
            if (val_data_ != nullptr) {

                if (omp_get_thread_num() == 0)
                    t0 = Clock::now();

                loss_val = compute_loss(val_data_->get_num_ex(), running_val_pred_, sample_weight_val,
                                        val_data_->get_labs(), sample_weights_val_sum);

                double diff = (best_val_loss - loss_val) / best_val_loss;
                if (diff > 0.000001 || it == 0) {
                    best_val_loss     = loss_val;
                    it_since_best_val = 0;
                    tree_idx_stop     = tree_idx;
                    linear_idx_stop   = linear_idx;
                } else {
                    it_since_best_val++;
                }

                // stop early
                if (it_since_best_val == params_.early_stopping_rounds) {
                    early_stop = true;
                }

                if (omp_get_thread_num() == 0)
                    t1 = Clock::now();

                profile_.t_val_loss += t_elapsed(t0, t1);
            }

            if (params_.verbose) {

                double loss_train
                    = compute_loss(num_ex_, running_pred_, sample_weight, this->data_->get_labs(), sample_weights_sum);

                if (val_data_ != nullptr) {
                    printf("it: %6u, learner: %c, loss_train: %e, loss_val: %e, it_since_best: %6u \n", it,
                           learner_types_[it] ? 'k' : 't', loss_train, loss_val, it_since_best_val);
                } else {
                    printf("it: %6u, learner: %c, loss_train: %e\n", it, learner_types_[it] ? 'k' : 't', loss_train);
                }
            }
        }

        // end of boosting
        if (params_.enable_profile) {
            profile_.report();
        }

        // populate model
        snapml::task_t      task;
        snapml::objective_t objective = snapml::objective_t::mse;
        if (params_.objective == snapml::BoosterParams::objective_t::logloss
            || params_.objective == snapml::BoosterParams::objective_t::softmax) {
            task = snapml::task_t::classification;
        } else {
            task = snapml::task_t::regression;
            if (params_.objective == snapml::BoosterParams::objective_t::poisson)
                objective = snapml::objective_t::poisson;
        }

        model_ = std::make_shared<BoosterModel>(
            task, objective, num_classes_, params_.base_prediction, params_.learning_rate, getRFBParams().random_state,
            getRFBParams().n_components, getRFBParams().gamma, tree_ensemble_models_, kr_ensemble_models_);

        // compute feature importances
        if (params_.aggregate_importances) {
            for (uint32_t cls = 0; cls < regressors_per_round_; cls++) {
                for (uint32_t j = 0; j < num_ft_; j++) {
                    feature_importances_[j] += cls_feature_importances_[cls][j];
                }
            }
        }
    }

    double compute_loss(uint32_t num_ex, const std::vector<double>& running_pred, const float* const sample_weights,
                        float* labs, double weights_sum)
    {

        // compute loss
        double loss = 0.0;
        switch (params_.objective) {
        // mse
        case snapml::BoosterParams::objective_t::mse: {
            if (sample_weights == nullptr) {
                for (uint32_t i = 0; i < num_ex; i++) {
                    double tmp = labs[i] - running_pred[i];
                    loss += tmp * tmp;
                }
            } else {
                for (uint32_t i = 0; i < num_ex; i++) {
                    double tmp = labs[i] - running_pred[i];
                    loss += tmp * tmp * sample_weights[i];
                }
            }
            break;
        }
        // poisson
        case snapml::BoosterParams::objective_t::poisson: {
            if (sample_weights == nullptr) {
                for (uint32_t i = 0; i < num_ex; i++) {
                    double tmp  = std::exp(running_pred[i]) - labs[i] * running_pred[i];
                    double tmp1 = lgamma(labs[i] + 1.0);
                    loss += (tmp1 + tmp);
                }
            } else {
                for (uint32_t i = 0; i < num_ex; i++) {
                    double tmp  = std::exp(running_pred[i]) - labs[i] * running_pred[i];
                    double tmp1 = lgamma(labs[i] + 1.0);
                    loss += (tmp1 + tmp) * sample_weights[i];
                }
            }
            break;
        }
        // quantile
        case snapml::BoosterParams::objective_t::quantile: {
            if (sample_weights == nullptr) {
                for (uint32_t i = 0; i < num_ex; i++) {
                    double tmp;
                    double diff = labs[i] - running_pred[i];
                    if (diff >= 0.0)
                        tmp = std::log(std::cosh(params_.alpha * diff));

                    else
                        tmp = std::log(std::cosh((params_.alpha - 1) * diff));
                    loss += tmp;
                }
            } else {
                for (uint32_t i = 0; i < num_ex; i++) {
                    double tmp;
                    double diff = labs[i] - running_pred[i];
                    if (diff >= 0.0)
                        tmp = std::log(std::cosh(params_.alpha * diff));
                    else
                        tmp = std::log(std::cosh((params_.alpha - 1) * diff));
                    loss += tmp * sample_weights[i];
                }
            }
            break;
        }

        // logloss
        case snapml::BoosterParams::objective_t::logloss: {
            if (sample_weights == nullptr) {
                for (uint32_t i = 0; i < num_ex; i++) {
                    double tmp = labs[i] > 0 ? +1 : -1;
                    loss += std::log(1.0 + std::exp(-running_pred[i] * tmp));
                }
            } else {
                for (uint32_t i = 0; i < num_ex; i++) {
                    double tmp = labs[i] > 0 ? +1 : -1;
                    loss += std::log(1.0 + std::exp(-running_pred[i] * tmp)) * sample_weights[i];
                }
            }
            break;
        }
        // cross-entropy
        case snapml::BoosterParams::objective_t::cross_entropy: {
            if (sample_weights == nullptr) {
                for (uint32_t i = 0; i < num_ex; i++) {
                    double tmp = 1.0 / (1.0 + std::exp(-running_pred[i]));
                    loss -= labs[i] * std::log(tmp) + (1.0 - labs[i]) * std::log(1.0 - tmp);
                }
            } else {
                for (uint32_t i = 0; i < num_ex; i++) {
                    double tmp  = 1.0 / (1.0 + std::exp(-running_pred[i]));
                    double tmp2 = labs[i] * std::log(tmp) + (1.0 - labs[i]) * std::log(1.0 - tmp);
                    loss -= tmp2 * sample_weights[i];
                }
            }
            break;
        }

        // Softmax (multi-class classification)
        case snapml::BoosterParams::objective_t::softmax: {

            for (uint32_t i = 0; i < num_ex; i++) {

                std::vector<double> this_running_pred(num_classes_);
                for (uint32_t cls = 0; cls < num_classes_; cls++) {
                    this_running_pred[cls] = running_pred[cls * num_ex + i];
                }

                double pmax = -std::numeric_limits<double>::max();
                for (uint32_t cls = 0; cls < num_classes_; cls++) {
                    pmax = std::max(pmax, this_running_pred[cls]);
                }
                double pnorm = 0.0;
                for (uint32_t cls = 0; cls < num_classes_; cls++) {
                    this_running_pred[cls] = std::exp(this_running_pred[cls] - pmax);
                    pnorm += this_running_pred[cls];
                }

                double prob = this_running_pred[labs[i]] / pnorm;

                if (sample_weights == nullptr) {
                    loss -= std::log(prob);
                } else {
                    loss -= sample_weights[i] * std::log(prob);
                }
            }

            break;
        }

        default:
            throw std::runtime_error("Invalid objective");
        }

        // if sample_weights are not used, weights_sum is the sum of number of examples
        loss /= weights_sum;

        return loss;
    }

    void compute_target_weights(const float* const sample_weight)
    {

        omp_set_num_threads(params_.n_threads);

        uint32_t num_ex = labs_.size();

        switch (params_.objective) {
        // MSE objective (regression)
        case snapml::BoosterParams::objective_t::mse: {
            OMP::parallel_for<int32_t>(0, num_ex, [this](const int32_t& ex) {
                double g     = 2.0 * (running_pred_[ex] - labs_[ex]);
                double h     = 2.0;
                target_[ex]  = -g / h;
                weights_[ex] = h;
            });
            break;
        }
        // Poisson objective (regression)
        case snapml::BoosterParams::objective_t::poisson: {
            OMP::parallel_for<int32_t>(0, num_ex, [this](const int32_t& ex) {
                double g = std::exp(running_pred_[ex]) - labs_[ex];
                double h = std::exp(running_pred_[ex] + params_.max_delta_step);
                if (h < MIN_VAL_HESSIAN)
                    h = MIN_VAL_HESSIAN;
                target_[ex]  = -g / h;
                weights_[ex] = h;
            });
            break;
        }
        // Quantile objective (regression)
        case snapml::BoosterParams::objective_t::quantile: {
            OMP::parallel_for<int32_t>(0, num_ex, [this](const int32_t& ex) {
                double diff = (labs_[ex] - running_pred_[ex]);
                double g;
                double h;
                if (diff < 0) {
                    diff            = (params_.alpha - 1) * diff;
                    g               = (1 - params_.alpha) * std::tanh(diff);
                    double tmp_cosh = (std::exp(2 * diff) + 1.0) / (2.0 * std::exp(diff));
                    h               = std::pow((params_.alpha - 1), 2) / std::pow(tmp_cosh, 2);
                } else {
                    diff            = params_.alpha * diff;
                    g               = -(params_.alpha) * std::tanh(diff);
                    double tmp_cosh = (std::exp(-2 * diff) + 1.0) / (2.0 * std::exp(-diff));
                    h               = std::pow(params_.alpha, 2) / std::pow(tmp_cosh, 2);
                }
                if (h < MIN_VAL_HESSIAN)
                    h = MIN_VAL_HESSIAN;

                if (h < params_.min_h_quantile)
                    h = params_.min_h_quantile;
                target_[ex]  = -g / h;
                weights_[ex] = h;
            });
            break;
        }
        // LogLoss objective (binary classification)
        case snapml::BoosterParams::objective_t::logloss: {
            OMP::parallel_for<int32_t>(0, num_ex, [this](const int32_t& ex) {
                double tmp  = std::exp(-running_pred_[ex] * labs_[ex]);
                double tmp2 = tmp / (1.0 + tmp);

                double g = -labs_[ex] * tmp2;
                double h = tmp2 * (1.0 - tmp2);
                if (h < MIN_VAL_HESSIAN)
                    h = MIN_VAL_HESSIAN;
                target_[ex]  = -g / h;
                weights_[ex] = h;
            });
            break;
        }
        // Cross entropy (regression)
        case snapml::BoosterParams::objective_t::cross_entropy: {

            OMP::parallel_for<int32_t>(0, num_ex, [this](const int32_t& ex) {
                double tmp = 1.0 / (1.0 + std::exp(-running_pred_[ex]));

                double g = tmp - labs_[ex];
                double h = tmp * (1.0 - tmp);

                if (h < MIN_VAL_HESSIAN)
                    h = MIN_VAL_HESSIAN;

                target_[ex]  = -g / h;
                weights_[ex] = h;
            });
            break;
        }
        // Softmax (multi-class classification)
        case snapml::BoosterParams::objective_t::softmax: {

            OMP::parallel_for<int32_t>(0, num_ex, [this, &num_ex](const int32_t& ex) {
                std::vector<double> this_running_pred(num_classes_);
                for (uint32_t cls = 0; cls < num_classes_; cls++) {
                    this_running_pred[cls] = running_pred_[cls * num_ex_ + ex];
                }

                double pmax = -std::numeric_limits<double>::max();
                for (uint32_t cls = 0; cls < num_classes_; cls++) {
                    pmax = std::max(pmax, this_running_pred[cls]);
                }
                double pnorm = 0.0;
                for (uint32_t cls = 0; cls < num_classes_; cls++) {
                    this_running_pred[cls] = std::exp(this_running_pred[cls] - pmax);
                    pnorm += this_running_pred[cls];
                }

                for (uint32_t cls = 0; cls < num_classes_; cls++) {
                    double prob = this_running_pred[cls] / pnorm;
                    double g    = (labs_[ex] == cls) ? (prob - 1.0) : prob;
                    double h    = 2.0 * prob * (1.0 - prob);

                    if (h < MIN_VAL_HESSIAN)
                        h = MIN_VAL_HESSIAN;

                    target_[cls * num_ex + ex]  = -g / h;
                    weights_[cls * num_ex + ex] = h;
                }
            });
            break;
        }

        default:
            throw std::runtime_error("Invalid objective");
        }

        if (sample_weight != nullptr) {
            for (uint32_t cls = 0; cls < regressors_per_round_; cls++) {
                float* const this_weights = &weights_[cls * num_ex];
                OMP::parallel_for<int32_t>(0, num_ex, [&sample_weight, &this_weights](const int32_t& ex) {
                    this_weights[ex] = sample_weight[ex] * this_weights[ex];
                });
            }
        }
    }

    inline double t_elapsed(const CurTime& t0, const CurTime& t1)
    {
        auto dur = t1 - t0;
        return static_cast<double>(dur.count()) / 1.0e9;
    }

    snapml::DecisionTreeParams getTreeParams()
    {
        snapml::DecisionTreeParams tree_params;

        tree_params.use_histograms               = params_.use_histograms;
        tree_params.hist_nbins                   = params_.hist_nbins;
        tree_params.colsample_bytree             = params_.colsample_bytree;
        tree_params.subsample                    = params_.subsample;
        tree_params.select_probability           = params_.select_probability;
        tree_params.lambda                       = params_.lambda;
        tree_params.max_delta_step               = params_.max_delta_step;
        tree_params.n_threads                    = n_inner_threads_;
        tree_params.task                         = snapml::task_t::regression;
        tree_params.num_classes                  = 2;
        tree_params.max_depth                    = params_.max_max_depth;
        tree_params.split_criterion              = snapml::split_t::mse;
        tree_params.tree_in_ensemble             = true;
        tree_params.compute_training_predictions = true;
        tree_params.use_gpu                      = params_.use_gpu;
        tree_params.random_state                 = random_state_;

        return tree_params;
    }

    glm::RidgeClosed::param_t getRidgeParams()
    {
        glm::RidgeClosed::param_t ridge_params;

        ridge_params.n_threads     = n_inner_threads_;
        ridge_params.regularizer   = params_.regularizer;
        ridge_params.fit_intercept = params_.fit_intercept;

        return ridge_params;
    }

    RBFSamplerParams getRFBParams()
    {
        RBFSamplerParams rbf_params;

        // RBF transform is done once in the begining, so it can use the global thread count
        rbf_params.n_threads    = params_.n_threads;
        rbf_params.gamma        = params_.gamma;
        rbf_params.n_components = params_.n_components;
        rbf_params.random_state = rbf_random_state_;

        return rbf_params;
    }

    struct profile_t {

        double t_init_booster = 0.0;
        double t_init_trees   = 0.0;
        double t_init_linear  = 0.0;
        double t_target       = 0.0;
        double t_tree_fit     = 0.0;
        double t_tree_pred    = 0.0;
        double t_tree_val     = 0.0;
        double t_linear_fit   = 0.0;
        double t_linear_save  = 0.0;
        double t_linear_pred  = 0.0;
        double t_linear_val   = 0.0;
        double t_stop         = 0.0;
        double t_val_loss     = 0.0;
        double t_free         = 0.0;

        std::shared_ptr<glm::RidgeClosed::profile_t> ridge_profile;

        profile_t() { ridge_profile = std::make_shared<glm::RidgeClosed::profile_t>(); }

        void report()
        {
            double t_tot = t_init_booster + t_init_trees + t_init_linear + t_target + +t_tree_fit + t_tree_pred
                           + t_tree_val + +t_linear_fit + t_linear_save + t_linear_pred + t_linear_val + t_stop
                           + t_val_loss + t_free;

            printf("TreeBooster::profile\n");
            printf("t_init_booster: %e (%4.1f%%)\n", t_init_booster, 100 * t_init_booster / t_tot);
            printf("t_init_trees:   %e (%4.1f%%)\n", t_init_trees, 100 * t_init_trees / t_tot);
            printf("t_init_linear:  %e (%4.1f%%)\n", t_init_linear, 100 * t_init_linear / t_tot);
            printf("t_target:       %e (%4.1f%%)\n", t_target, 100 * t_target / t_tot);
            printf("t_tree_fit:     %e (%4.1f%%)\n", t_tree_fit, 100 * t_tree_fit / t_tot);
            printf("t_tree_pred:    %e (%4.1f%%)\n", t_tree_pred, 100 * t_tree_pred / t_tot);
            printf("t_tree_val:     %e (%4.1f%%)\n", t_tree_val, 100 * t_tree_val / t_tot);
            printf("t_linear_fit:   %e (%4.1f%%)\n", t_linear_fit, 100 * t_linear_fit / t_tot);
            printf("t_linear_save:  %e (%4.1f%%)\n", t_linear_save, 100 * t_linear_save / t_tot);
            printf("t_linear_pred:  %e (%4.1f%%)\n", t_linear_pred, 100 * t_linear_pred / t_tot);
            printf("t_linear_val:   %e (%4.1f%%)\n", t_linear_val, 100 * t_linear_val / t_tot);
            printf("t_val_loss:     %e (%4.1f%%)\n", t_val_loss, 100 * t_val_loss / t_tot);
            printf("t_stop:         %e (%4.1f%%)\n", t_stop, 100 * t_stop / t_tot);
            printf("t_free:         %e (%4.1f%%)\n", t_free, 100 * t_free / t_tot);
            printf(">> t_tot:       %e\n", t_tot);

            if (t_linear_fit > 0) {
                ridge_profile->report();
            }
        }
    };

    glm::DenseDataset*    val_data_;
    snapml::BoosterParams params_;
    std::mt19937          rng_;

    std::shared_ptr<glm::TreeInvariants<glm::DenseDataset>> tree_invariants_;
    std::vector<std::shared_ptr<HistSolver<RegTreeNode>>>   hist_solvers_gpu_;

    profile_t profile_;

    uint32_t regressors_per_round_;
    uint32_t n_inner_threads_;
    uint32_t n_outer_threads_;

    uint32_t random_state_;
    uint32_t rbf_random_state_;

    std::exception_ptr eptr;

    std::vector<double> running_pred_;
    std::vector<double> running_val_pred_;
    std::vector<float>  weights_;
    std::vector<double> target_;
    std::vector<double> labs_;

    std::vector<double> pred_tmp_;
    std::vector<double> pred_val_tmp_;

    // todo: these variables do not seem to be used
    // double sample_weights_sum_;
    // double sample_weights_val_sum_;

    std::vector<uint8_t> learner_types_;

    std::vector<float> new_data_;
    std::vector<float> new_val_data_;

    std::vector<snapml::DecisionTreeParams> tree_param_array_;

    std::vector<std::shared_ptr<TreeEnsembleModel>>        tree_ensemble_models_;
    std::vector<std::shared_ptr<KernelRidgeEnsembleModel>> kr_ensemble_models_;

    std::vector<std::vector<double>> cls_feature_importances_;
};

}

#endif
