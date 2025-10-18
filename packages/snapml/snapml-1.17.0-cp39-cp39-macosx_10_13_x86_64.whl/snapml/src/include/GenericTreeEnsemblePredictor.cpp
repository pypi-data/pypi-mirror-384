/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2023
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Thomas Parnell
 *
 * End Copyright
 ********************************************************************/

#include "GenericTreeEnsemblePredictor.hpp"
#include "BoosterPredictor.hpp"
#include "RandomForestPredictor.hpp"

namespace snapml {

GenericTreeEnsemblePredictor::GenericTreeEnsemblePredictor(const snapml::GenericTreeEnsembleModel model)
{
    if (model.get_ensemble_type() == snapml::ensemble_t::boosting) {
        booster_predictor_ = std::make_shared<snapml::BoosterPredictor>(*model.get_booster_model());
        rf_predictor_      = nullptr;
    } else {
        booster_predictor_ = nullptr;
        rf_predictor_      = std::make_shared<snapml::RandomForestPredictor>(*model.get_rf_model());
    }
}

void GenericTreeEnsemblePredictor::predict(snapml::DenseDataset data, double* const preds, uint32_t num_threads) const
{
    if (booster_predictor_ == nullptr) {
        return rf_predictor_->predict(data, preds, num_threads);
    } else {
        return booster_predictor_->predict(data, preds, num_threads);
    }
}

void GenericTreeEnsemblePredictor::predict_proba(snapml::DenseDataset data, double* const preds,
                                                 uint32_t num_threads) const
{
    if (booster_predictor_ == nullptr) {
        return rf_predictor_->predict_proba(data, preds, num_threads);
    } else {
        return booster_predictor_->predict_proba(data, preds, num_threads);
    }
}

}
