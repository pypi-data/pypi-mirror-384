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

#include "DenseDataset.hpp"
#include "DenseDatasetInt.hpp"

namespace snapml {

DenseDataset::DenseDataset()
    : mtx_(std::shared_ptr<std::mutex>(new std::mutex()))
{
}

DenseDataset::DenseDataset(uint32_t num_ex, uint32_t num_ft, float* data, float* labs)
    : mtx_(std::shared_ptr<std::mutex>(new std::mutex()))
{
    data_ = std::make_shared<glm::DenseDataset>(num_ex, num_ft, data, labs);
}

DenseDataset::DenseDataset(std::vector<float>& data, std::vector<float>& labs)
    : mtx_(std::shared_ptr<std::mutex>(new std::mutex()))
{
    uint32_t num_ex;
    uint32_t num_ft;

    std::unique_lock<std::mutex> lock(*mtx_);

    if (data.size() == 0 || labs.size() == 0) {
        std::runtime_error(
            "Wrong dimensions: the number of rows and columns of the training input samples must be larger than 0.");
    }

    num_ex = labs.size();
    num_ft = data.size() / num_ex;

    if (num_ex * num_ft != data.size()) {
        std::runtime_error("Inconsistent dimensions: the size of training input samples must be a multiple of the size "
                           "of the target values.");
    }

    data_ = std::make_shared<glm::DenseDataset>(num_ex, num_ft, data.data(), labs.data());
}
}