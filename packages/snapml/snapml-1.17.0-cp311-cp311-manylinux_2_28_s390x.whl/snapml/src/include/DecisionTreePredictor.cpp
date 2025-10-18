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

#include "DecisionTreePredictor.hpp"
#include "TreeModel.hpp"
#include "TreePredictor.hpp"

namespace snapml {

DecisionTreePredictor::DecisionTreePredictor(const snapml::DecisionTreeModel model)
    : predictor_(std::make_shared<tree::TreePredictor>(
        tree::TreePredictor(static_cast<const tree::DecisionTreeModelInt*>(&model)->get_internal())))
    , mtx_(std::shared_ptr<std::mutex>(new std::mutex()))

{
}

void DecisionTreePredictor::apply(snapml::DenseDataset data, const uint32_t ex, uint32_t& leaf_idx,
                                  float& leaf_label) const
{
    std::unique_lock<std::mutex> lock(*mtx_);
    predictor_->apply(data.get().get(), ex, leaf_idx, leaf_label);
}

void DecisionTreePredictor::predict(snapml::DenseDataset data, double* const preds, uint32_t num_threads) const
{
    std::unique_lock<std::mutex> lock(*mtx_);
    predictor_->predict(data.get().get(), preds, num_threads);
}

void DecisionTreePredictor::predict_proba(snapml::DenseDataset data, double* const preds, uint32_t num_threads) const
{
    std::unique_lock<std::mutex> lock(*mtx_);
    predictor_->predict_proba(data.get().get(), preds, num_threads);
}

}