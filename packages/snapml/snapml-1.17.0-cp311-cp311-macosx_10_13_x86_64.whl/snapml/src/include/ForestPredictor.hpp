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

#ifndef FOREST_PREDICTOR
#define FOREST_PREDICTOR

#include "Predictor.hpp"
#include "ForestModel.hpp"

namespace tree {

class ForestPredictor : public Predictor {

public:
    ForestPredictor(const std::shared_ptr<ForestModel> model)
        : model_(model)
    {
    }

    ~ForestPredictor() { }

    void predict(glm::DenseDataset* const data, double* const preds, uint32_t num_threads = 1) const override
    {

        omp_set_num_threads(num_threads);

        if (model_->task == snapml::task_t::regression) {

            predict_impl(data, preds, false, num_threads);

        } else {

            uint32_t num_ex      = data->get_num_ex();
            uint32_t num_classes = model_->num_classes;

            if (num_classes == 2) {
                predict_impl(data, preds, true, num_threads);
                OMP::parallel_for<int32_t>(0, num_ex,
                                           [&preds](const int32_t& ex) { preds[ex] = (preds[ex] > 0.5) ? 1.0 : -1.0; });

            } else {

                uint32_t num_extra_classes = model_->num_classes - 1;

                std::vector<double> probs(num_ex * num_extra_classes, 0.0);
                predict_impl(data, &probs[0], true, num_threads);

                OMP::parallel_for<int32_t>(0, num_ex, [&preds, probs, num_extra_classes](const int32_t& ex) {
                    double   last_cls_proba = 1.0;
                    uint32_t max_cls        = 0;
                    double   max_proba      = 0.0;

                    for (uint32_t cl = 0; cl < num_extra_classes; cl++) {
                        if (probs[cl + ex * num_extra_classes] > max_proba) {
                            max_proba = probs[cl + ex * num_extra_classes];
                            max_cls   = cl;
                        }
                        last_cls_proba -= probs[cl + ex * num_extra_classes];
                    }

                    preds[ex] = (last_cls_proba > max_proba) ? num_extra_classes : max_cls;
                });
            }
        }
    }

    void predict_proba(glm::DenseDataset* const data, double* const preds, uint32_t num_threads = 1) const override
    {
        uint32_t num_ex      = data->get_num_ex();
        uint32_t num_classes = model_->num_classes;
        omp_set_num_threads(num_threads);
        predict_impl(data, preds, true, num_threads);
        if (num_classes == 2) {
            std::vector<double> probs(num_ex);
            std::copy(preds, preds + num_ex, probs.begin());
            OMP::parallel_for<int32_t>(0, num_ex, [&preds, &probs, num_classes](const int32_t& ex) {
                preds[ex * num_classes]     = 1 - probs[ex];
                preds[ex * num_classes + 1] = probs[ex];
            });
        }
    }

private:
    const std::shared_ptr<ForestModel> model_;

    template <class T>
    void predict_impl(glm::DenseDataset* const data, T* const preds, bool proba, uint32_t num_threads = 1) const
    {

        uint32_t num_out = data->get_num_ex() * (model_->num_classes - 1);

        std::fill_n(preds, num_out, 0.0);

        uint32_t num_trees = 0;

        if (model_->tree_ensemble_model != nullptr) {
            model_->tree_ensemble_model->aggregate(data, preds, proba, num_threads);
            num_trees += model_->tree_ensemble_model->get_num_trees();
        }

        if (model_->compr_tree_ensemble_model != nullptr) {
            model_->compr_tree_ensemble_model->aggregate(data, preds, proba, num_threads);
            num_trees += model_->compr_tree_ensemble_model->get_num_trees();
        }

#ifdef Z14_SIMD
        if (model_->mbi_tree_ensemble_model != nullptr) {
            model_->mbi_tree_ensemble_model->aggregate(data, preds, proba, num_threads);
            num_trees += model_->mbi_tree_ensemble_model->get_num_trees();
        }
#endif
        OMP::parallel_for<int32_t>(0, num_out,
                                   [&preds, &num_trees](const int32_t& ex) { preds[ex] /= static_cast<T>(num_trees); });
    }
};

}

#endif
