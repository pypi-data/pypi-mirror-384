/*********************************************************************
 *
 * Licensed Materials - Property of IBM
 *
 * (C) Copyright IBM Corp. 2023. All Rights Reserved.

 * US Government Users Restricted Rights - Use, duplication or
 * disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
 *
 ********************************************************************/

#pragma once

#include "GenericTreeEnsembleModel.hpp"
#include "DenseDataset.hpp"

namespace snapml {

class BoosterPredictor;
class RandomForestPredictor;

//! @ingroup c-api
class GenericTreeEnsemblePredictor {
public:
    GenericTreeEnsemblePredictor(const snapml::GenericTreeEnsembleModel model);

    void predict(snapml::DenseDataset data, double* const preds, uint32_t num_threads = 1) const;
    void predict_proba(snapml::DenseDataset data, double* const preds, uint32_t num_threads = 1) const;

private:
    std::shared_ptr<snapml::BoosterPredictor>      booster_predictor_;
    std::shared_ptr<snapml::RandomForestPredictor> rf_predictor_;
};

}