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
 *
 * End Copyright
 ********************************************************************/

#ifndef FOREST_BUILDER
#define FOREST_BUILDER

#include "Builder.hpp"
#include "RandomForestParams.hpp"
#include "TreeInvariants.hpp"
#include "HistSolver.hpp"
#include "ExactTreeBuilder.hpp"
#include "CpuHistTreeBuilder.hpp"
#include "GpuHistTreeBuilder.hpp"
#include "ForestModel.hpp"
#include "TreeEnsembleModel.hpp"
#include "HistSolverGPUFactory.hpp"
#include "TreeBuilderFactory.hpp"

namespace tree {

template <class N> class RandomForestBuilder : public Builder<ForestModel> {

public:
    RandomForestBuilder<N>(glm::DenseDataset* data, snapml::RandomForestParams _params)
        : Builder(static_cast<glm::Dataset*>(data), _params.num_classes)
        , params_(_params)
    {

        // construct tree invariants
        tree_invariants_ = std::make_shared<glm::TreeInvariants<glm::DenseDataset>>();

        // construct hist_solvers_gpu
        if (params_.use_gpu) {
#ifdef WITH_CUDA
            if (num_classes_ == 2) {
                auto factory = std::make_shared<HistSolverGPUFactory>();
                for (uint32_t i = 0; i < params_.gpu_ids.size(); i++) {
                    hist_solvers_gpu_.push_back(factory->make<N>(tree_invariants_, params_.gpu_ids[i]));
                }
            } else {
                throw std::runtime_error("RandomForestBuilder only supports GPU acceleration for regression or "
                                         "binary classification tasks");
            }
#else
            throw std::runtime_error("Snap ML was not compiled with GPU support");
#endif
        }

        random_state_ = params_.random_state;

        for (uint32_t i = 0; i < params_.n_trees; i++) {

            random_state_ += i;

            auto hist_solver_gpu = params_.use_gpu ? hist_solvers_gpu_[i % hist_solvers_gpu_.size()] : nullptr;

            if (params_.use_gpu) {
                assert(hist_solver_gpu != nullptr);
            }

            auto factory = std::make_shared<TreeBuilderFactory>();
            if (!params_.use_histograms) {
                builders_.push_back(factory->make<ExactTreeBuilder<N>>(static_cast<glm::DenseDataset*>(data_),
                                                                       getTreeParams(), tree_invariants_));
            } else {
                if (params_.use_gpu && num_classes_ == 2) {
                    builders_.push_back(factory->make<GpuHistTreeBuilder<N>>(
                        static_cast<glm::DenseDataset*>(data_), getTreeParams(), tree_invariants_, hist_solver_gpu));
                } else {
                    builders_.push_back(factory->make<CpuHistTreeBuilder<N>>(static_cast<glm::DenseDataset*>(data_),
                                                                             getTreeParams(), tree_invariants_));
                }
            }
        }
    }

    ~RandomForestBuilder<N>() { }

    void init() override { init_impl(); }

    void build(const float* const sample_weight, const float* const sample_weight_val = nullptr,
               const double* const labels = nullptr) override
    {
        build_impl(sample_weight);
    }

private:
    void init_impl()
    {

        tree_invariants_->init(data_, params_.task, params_.n_threads, num_classes_);

        if (params_.use_histograms) {
            tree_invariants_->init_hist(data_, params_.task, params_.hist_nbins);

            if (params_.use_gpu) {

                omp_set_num_threads(params_.gpu_ids.size());
                glm::Dataset* const tmp = data_;
                OMP::parallel_for<int32_t>(0, hist_solvers_gpu_.size(), [this, &tmp](const int32_t& solver_idx) {
                    hist_solvers_gpu_[solver_idx]->init(tmp, getTreeParams());
                });
            }

            // Sorted matrix not used beyond this point _for_ histograms
            tree_invariants_->clear_sorted_matrix();
        }
    }

    void build_impl(const float* const sample_weight)
    {

        if (params_.use_gpu) {
            omp_set_num_threads(params_.gpu_ids.size());
            omp_set_nested(true);
            OMP::parallel_for<int32_t>(0, params_.gpu_ids.size(), [this, &sample_weight](const int32_t& g) {
                for (uint32_t i = g; i < params_.n_trees; i += params_.gpu_ids.size()) {
                    builders_[i]->init();
                    builders_[i]->build(sample_weight);
                }
            });
            omp_set_nested(false);
        } else {
            OMP::parallel_for<int32_t>(0, params_.n_trees, [this, &sample_weight](const int32_t& i) {
                builders_[i]->init();
                builders_[i]->build(sample_weight);
            });
        }

        auto tree_ensemble_model = std::make_shared<TreeEnsembleModel>(params_.task, num_classes_);
        for (uint32_t i = 0; i < builders_.size(); i++) {
            tree_ensemble_model->insert_tree(builders_[i]->get_model());
        }
        model_ = std::make_shared<ForestModel>(tree_ensemble_model);

        // compute feature importances
        for (uint32_t i = 0; i < builders_.size(); i++) {
            for (uint32_t j = 0; j < num_ft_; j++) {
                feature_importances_[j] += builders_[i]->get_feature_importance(j);
            }
        }
    }

    snapml::DecisionTreeParams getTreeParams()
    {
        snapml::DecisionTreeParams tree_params;

        tree_params.task             = params_.task;
        tree_params.split_criterion  = params_.split_criterion;
        tree_params.max_depth        = params_.max_depth;
        tree_params.min_samples_leaf = params_.min_samples_leaf;
        tree_params.max_features     = params_.max_features;
        tree_params.bootstrap        = params_.bootstrap;
        tree_params.verbose          = params_.verbose;
        tree_params.use_histograms   = params_.use_histograms;
        tree_params.hist_nbins       = params_.hist_nbins;
        tree_params.num_classes      = params_.num_classes;
        tree_params.bootstrap        = true;
        tree_params.tree_in_ensemble = true;
        tree_params.random_state     = random_state_;

        if (tree_params.use_gpu) {
            if (!tree_params.use_histograms)
                throw std::runtime_error("GPU acceleration only supported for histograms");
            if (params_.gpu_ids.size() == 0)
                throw std::runtime_error("No GPU ids have been supplied as a parameter");

            tree_params.n_threads = std::max((uint32_t)params_.n_threads / (uint32_t)params_.gpu_ids.size(), 1U);

        } else {
            tree_params.n_threads = 1;
        }

        return tree_params;
    }

    snapml::RandomForestParams                              params_;
    uint32_t                                                random_state_;
    std::shared_ptr<glm::TreeInvariants<glm::DenseDataset>> tree_invariants_;
    std::vector<std::shared_ptr<HistSolver<N>>>             hist_solvers_gpu_;
    std::vector<std::shared_ptr<DecisionTreeBuilder<N>>>    builders_;
};

}

#endif
