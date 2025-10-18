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

#ifndef BOOSTER_PREDICTOR
#define BOOSTER_PREDICTOR

#include "Predictor.hpp"
#include "BoosterModelInt.hpp"
#include "TreeEnsembleModel.hpp"
#include "ComprTreeEnsembleModel.hpp"

#ifdef Z14_SIMD
#include "MBITreeEnsembleModel.hpp"
#endif

#include "RBFSampler.hpp"

namespace tree {

class BoosterPredictor : public Predictor {

public:
    BoosterPredictor(const std::shared_ptr<BoosterModel> model)
        : model_(model)
    {
    }

    ~BoosterPredictor() { }

    void apply(glm::DenseDataset* const data, uint32_t* const leaf_idx, float* const leaf_lab,
               uint32_t num_threads = 1) const
    {
        omp_set_num_threads(num_threads);

        if (model_->compr_tree_ensemble_models.size()) {
            throw std::runtime_error("Apply is not supported for compressed ensembles.");
        }

#ifdef Z14_SIMD
        if (model_->mbi_tree_ensemble_models.size()) {
            throw std::runtime_error("Apply is not supported for mbit ensembles.");
        }
#endif

        uint32_t num_ex      = data->get_num_ex();
        uint32_t num_trees   = model_->tree_ensemble_models[0]->get_num_trees();
        uint32_t num_classes = model_->num_classes;

        OMP::parallel_for<int32_t>(
            0, num_ex, [this, &data, &leaf_idx, &leaf_lab, &num_trees, &num_classes](const int32_t& ex) {
                for (uint32_t tree = 0; tree < num_trees; tree++) {
                    if (num_classes > 2) {
                        uint32_t* const this_idx = &leaf_idx[ex * (num_trees * num_classes) + tree * num_classes];
                        float* const    this_lab = &leaf_lab[ex * (num_trees * num_classes) + tree * num_classes];
                        for (uint32_t cls = 0; cls < num_classes; cls++) {
                            model_->tree_ensemble_models[cls]->apply(data, ex, tree, this_idx[cls], this_lab[cls]);
                        }
                    } else {
                        model_->tree_ensemble_models[0]->apply(data, ex, tree, leaf_idx[ex * num_trees + tree],
                                                               leaf_lab[ex * num_trees + tree]);
                    }
                }
            });
    }

    void predict(glm::DenseDataset* const data, double* const preds, uint32_t num_threads = 1) const override
    {

        omp_set_num_threads(num_threads);

        uint32_t num_ex = data->get_num_ex();

        std::vector<float> data_p;

        if (model_->kr_ensemble_models.size()) {
            data_p = transform(data, num_threads);
        }

        if (model_->task == snapml::task_t::regression) {

            predict_margin(data, data_p, preds, 0, num_threads);

            // transform if poisson
            if (model_->objective == snapml::objective_t::poisson) {
                OMP::parallel_for<int32_t>(0, num_ex, [&preds](const int32_t& ex) { preds[ex] = std::exp(preds[ex]); });
            }

        } else {

            uint32_t num_classes = model_->num_classes;

            if (num_classes == 2) {
                predict_margin(data, data_p, preds, 0, num_threads);
                OMP::parallel_for<int32_t>(0, num_ex,
                                           [&preds](const int32_t& ex) { preds[ex] = (preds[ex] > 0.0) ? 1.0 : -1.0; });

            } else {

                std::vector<double>   best_margin(num_ex, -std::numeric_limits<double>::max());
                std::vector<uint32_t> best_cls(num_ex, 0);

                for (uint32_t cls = 0; cls < num_classes; cls++) {
                    predict_margin(data, data_p, preds, cls, num_threads);

                    OMP::parallel_for<int32_t>(0, num_ex, [&preds, &best_margin, &best_cls, &cls](const int32_t& ex) {
                        if (preds[ex] > best_margin[ex]) {
                            best_margin[ex] = preds[ex];
                            best_cls[ex]    = cls;
                        }
                    });
                }

                OMP::parallel_for<int32_t>(0, num_ex, [&preds, &best_cls](const int32_t& ex) {
                    preds[ex] = static_cast<double>(best_cls[ex]);
                });
            }
        }
    }

    void predict_proba(glm::DenseDataset* const data, double* const preds, uint32_t num_threads = 1) const override
    {
        omp_set_num_threads(num_threads);

        std::vector<float> data_p;

        if (model_->kr_ensemble_models.size()) {
            data_p = transform(data, num_threads);
        }

        uint32_t num_ex      = data->get_num_ex();
        uint32_t num_classes = model_->num_classes;

        if (num_classes == 2) {
            predict_margin(data, data_p, preds, 0, num_threads);
            std::vector<double> probs(num_ex);
            std::copy(preds, preds + num_ex, probs.begin());
            OMP::parallel_for<int32_t>(0, num_ex, [&preds, &probs, num_classes](const int32_t& ex) {
                double this_prob            = 1.0 / (1.0 + std::exp(-probs[ex]));
                preds[ex * num_classes]     = 1 - this_prob;
                preds[ex * num_classes + 1] = this_prob;
            });
        } else {

            std::vector<double> pmax(num_ex, -std::numeric_limits<double>::max());
            std::vector<double> pnorm(num_ex, 0.0);

            for (uint32_t cls = 0; cls < num_classes; cls++) {

                double* const this_preds = &preds[cls * num_ex];
                predict_margin(data, data_p, this_preds, cls, num_threads);

                OMP::parallel_for<int32_t>(0, num_ex, [&this_preds, &pmax](const int32_t& ex) {
                    pmax[ex] = std::max(this_preds[ex], pmax[ex]);
                });
            }

            for (uint32_t cls = 0; cls < num_classes; cls++) {
                double* const this_preds = &preds[cls * num_ex];
                OMP::parallel_for<int32_t>(0, num_ex, [&this_preds, &pmax, &pnorm](const int32_t& ex) {
                    this_preds[ex] = std::exp(this_preds[ex] - pmax[ex]);
                    pnorm[ex] += this_preds[ex];
                });
            }

            for (uint32_t cls = 0; cls < num_classes; cls++) {
                double* const this_preds = &preds[cls * num_ex];
                OMP::parallel_for<int32_t>(0, num_ex,
                                           [&this_preds, &pnorm](const int32_t& ex) { this_preds[ex] /= pnorm[ex]; });
            }
        }
    }

private:
    const std::shared_ptr<BoosterModel> model_;

    std::vector<float> transform(glm::DenseDataset* const data, uint32_t num_threads = 1) const
    {

        RBFSamplerParams params;
        params.gamma        = model_->gamma;
        params.n_components = model_->n_components;
        params.random_state = model_->random_state;
        params.n_threads    = num_threads;

        auto rbf_obj = std::make_shared<RBFSampler>(params);

        // regenerate the weights and offsets (the RBF projection)
        rbf_obj->fit(data->get_num_ft());

        return rbf_obj->transform(data, num_threads);
    }

    template <class T>
    void predict_margin(glm::DenseDataset* const data, const std::vector<float> data_p, T* const preds, uint32_t cls,
                        uint32_t num_threads = 1) const
    {
        uint32_t num_ex = data->get_num_ex();

        // initialize predictions scaled with 1/learning rate
        double scaled_base_prediction = model_->base_prediction / model_->learning_rate;

        std::fill_n(preds, num_ex, scaled_base_prediction);

        if (model_->tree_ensemble_models.size()) {
            model_->tree_ensemble_models[cls]->aggregate(data, preds, false, num_threads);
        }

        if (model_->compr_tree_ensemble_models.size()) {
            model_->compr_tree_ensemble_models[cls]->aggregate(data, preds, false, num_threads);
        }

#ifdef Z14_SIMD
        if (model_->mbi_tree_ensemble_models.size()) {
            model_->mbi_tree_ensemble_models[cls]->aggregate(data, preds, false, num_threads);
        }
#endif

        if (model_->kr_ensemble_models.size()) {
            model_->kr_ensemble_models[cls]->aggregate(data_p, preds, num_threads);
        }

        OMP::parallel_for<int32_t>(0, num_ex,
                                   [this, &preds](const int32_t& ex) { preds[ex] *= model_->learning_rate; });
    }
};

}

#endif
