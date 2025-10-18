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

#include "RandomForestPredictor.hpp"
#include "ForestPredictor.hpp"

namespace snapml {

RandomForestPredictor::RandomForestPredictor(const snapml::RandomForestModel model)
    : predictor_(std::make_shared<tree::ForestPredictor>(
        tree::ForestPredictor(static_cast<const tree::RandomForestModelInt*>(&model)->get_internal())))
    , mtx_(std::shared_ptr<std::mutex>(new std::mutex()))
{
}

void RandomForestPredictor::predict(snapml::DenseDataset data, double* const preds, uint32_t num_threads) const
{
    std::unique_lock<std::mutex> lock(*mtx_);
    predictor_->predict(data.get().get(), preds, num_threads);
}

void RandomForestPredictor::predict_proba(snapml::DenseDataset data, double* const preds, uint32_t num_threads) const
{
    std::unique_lock<std::mutex> lock(*mtx_);
    predictor_->predict_proba(data.get().get(), preds, num_threads);
}

}