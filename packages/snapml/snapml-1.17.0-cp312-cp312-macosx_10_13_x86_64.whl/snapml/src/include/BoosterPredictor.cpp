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
 * Authors      :
 *
 * End Copyright
 ********************************************************************/

#include <mutex>

#include "BoosterPredictor.hpp"
#include "BoosterPredictorInt.hpp"
#include "BoosterModelInt.hpp"

namespace snapml {

BoosterPredictor::BoosterPredictor(const snapml::BoosterModel model)
    : predictor_(std::make_shared<tree::BoosterPredictor>(
        tree::BoosterPredictor(static_cast<const tree::BoosterModelInt*>(&model)->get_internal())))
    , mtx_(std::shared_ptr<std::mutex>(new std::mutex()))
{
}

void BoosterPredictor::apply(snapml::DenseDataset data, uint32_t* const leaf_idx, float* const leaf_lab,
                             uint32_t num_threads) const
{
    std::unique_lock<std::mutex> lock(*mtx_);
    predictor_->apply(data.get().get(), leaf_idx, leaf_lab, num_threads);
}

void BoosterPredictor::predict(snapml::DenseDataset data, double* const preds, uint32_t num_threads) const
{
    std::unique_lock<std::mutex> lock(*mtx_);
    predictor_->predict(data.get().get(), preds, num_threads);
}

void BoosterPredictor::predict_proba(snapml::DenseDataset data, double* const preds, uint32_t num_threads) const
{
    std::unique_lock<std::mutex> lock(*mtx_);
    predictor_->predict_proba(data.get().get(), preds, num_threads);
}
}
