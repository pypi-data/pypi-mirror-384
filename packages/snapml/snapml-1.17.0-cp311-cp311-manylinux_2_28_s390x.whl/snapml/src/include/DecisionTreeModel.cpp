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

#include <stdint.h>
#include <memory>

#include "DecisionTreeModel.hpp"
#include "TreeModel.hpp"

namespace snapml {

DecisionTreeModel::DecisionTreeModel()
    : mtx_(std::shared_ptr<std::mutex>(new std::mutex()))
{
    model_ = std::make_shared<tree::TreeModel>();
}

void DecisionTreeModel::get(std::vector<uint8_t>& vec)
{
    std::unique_lock<std::mutex> lock(*mtx_);
    tree::Model::Getter          getter(vec);
    model_->get(getter);
}

void DecisionTreeModel::put(const std::vector<uint8_t>& vec)
{
    std::unique_lock<std::mutex> lock(*mtx_);
    tree::Model::Setter          setter(vec);
    model_->put(setter, vec.size());
}

}
