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

#include "BoosterBuilder.hpp"
#include "BoosterBuilderInt.hpp"

namespace snapml {

BoosterBuilder::BoosterBuilder(snapml::DenseDataset data, snapml::DenseDataset val_data, snapml::BoosterParams params)
    : builder_(std::make_shared<tree::BoosterBuilder>(data.get().get(), val_data.get().get(), params))
    , mtx_(std::shared_ptr<std::mutex>(new std::mutex()))
{
}

void BoosterBuilder::init()
{
    std::unique_lock<std::mutex> lock(*mtx_);
    builder_->init();
}

double BoosterBuilder::get_feature_importance(uint32_t ft)
{
    std::unique_lock<std::mutex> lock(*mtx_);
    return builder_->get_feature_importance(ft);
}

void BoosterBuilder::get_feature_importances(double* const out, uint32_t num_ft_chk)
{
    std::unique_lock<std::mutex> lock(*mtx_);
    builder_->get_feature_importances(out, num_ft_chk);
}

size_t BoosterBuilder::get_full_feature_importances_size()
{
    std::unique_lock<std::mutex> lock(*mtx_);
    return builder_->get_full_feature_importances_size();
}

void BoosterBuilder::get_full_feature_importances(double* const out, uint32_t len)
{
    std::unique_lock<std::mutex> lock(*mtx_);
    builder_->get_full_feature_importances(out, len);
}

void BoosterBuilder::build(const float* const sample_weight, const float* const sample_weight_val,
                           const double* const labels)
{
    std::unique_lock<std::mutex> lock(*mtx_);
    builder_->build(sample_weight, sample_weight_val, labels);
}

snapml::BoosterModel BoosterBuilder::get_model()
{
    std::unique_lock<std::mutex> lock(*mtx_);
    tree::BoosterModelInt        bmi = tree::BoosterModelInt(builder_->get_model());
    return *static_cast<snapml::BoosterModel*>(&bmi);
}

}