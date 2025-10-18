/*********************************************************************
 *
 * Licensed Materials - Property of IBM
 *
 * (C) Copyright IBM Corp. 2022, 2023. All Rights Reserved.

 * US Government Users Restricted Rights - Use, duplication or
 * disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
 *
 ********************************************************************/

#pragma once

#include <mutex>

#include "BoosterModel.hpp"
#include "DenseDataset.hpp"

namespace tree {
class BoosterPredictor;
}

namespace snapml {

//! @ingroup c-api
class BoosterPredictor {
public:
    BoosterPredictor(const snapml::BoosterModel model);
    void apply(snapml::DenseDataset data, uint32_t* const leaf_idx, float* const leaf_lab,
               uint32_t num_threads = 1) const;
    void predict(snapml::DenseDataset data, double* const preds, uint32_t num_threads = 1) const;
    void predict_proba(snapml::DenseDataset data, double* const preds, uint32_t num_threads = 1) const;

private:
    const std::shared_ptr<tree::BoosterPredictor> predictor_;
    std::shared_ptr<std::mutex>                   mtx_;
};

}
