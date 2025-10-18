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
 * Authors      :
 *
 * End Copyright
 ********************************************************************/

#include <vector>
#include <map>
#include <set>
#include <string>
#include <functional>
#include <mutex>

#include "DenseDataset.hpp"
#include "DataSchema.hpp"
#include "AnyDataset.hpp"
#include "Features.hpp"
#include "Transformer.hpp"
#include "FunctionTransformer.hpp"

namespace snapml {

FunctionTransformer::FunctionTransformer(const snapml::FunctionTransformer::Params _params)
    : params(_params)
{
}

void FunctionTransformer::transform(snapml::AnyDataset& dataset)

{
    std::vector<std::vector<float>>& X    = feature_list[reinterpret_cast<uint64_t>(&dataset)]->numerical_features;
    const uint32_t                   size = X[0].size();
    bool                             check_index = true;

    Features::IndexLists il = feature_list[reinterpret_cast<uint64_t>(&dataset)]->get_index_lists(params.index_list);

    if (il.num_index_list.size() == 0)
        check_index = false;
    else if (index_list_valid(il.num_index_list, size) == false)
        throw std::runtime_error("Invalid index list.");

    const std::lock_guard<std::mutex> lock(feature_list[reinterpret_cast<uint64_t>(&dataset)]->mtx);
    for (uint32_t i = 0; i < size; i++) {
        if (check_index == false || il.num_index_list.find(i) != il.num_index_list.end()) {
            for (uint32_t j = 0; j < X.size(); j++) {
                X[j][i] = params.func(X[j][i]);
            }
        }
    }
}

}