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
#include <iostream>

#include "DenseDataset.hpp"
#include "DataSchema.hpp"
#include "AnyDataset.hpp"
#include "Features.hpp"
#include "Transformer.hpp"

#include "KBinsDiscretizer.hpp"

namespace snapml {

KBinsDiscretizer::KBinsDiscretizer(const snapml::KBinsDiscretizer::Params _params)
    : params(_params)
{
    for (std::vector<float> b : params.bin_edges)
        if (b.size() < 2)
            throw std::runtime_error("The number of bins is  not valid.");
}

void KBinsDiscretizer::transform(snapml::AnyDataset& dataset)

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

    uint32_t index = 0;
    for (uint32_t i = 0; i < size; i++) {
        if (check_index == false || il.num_index_list.find(i) != il.num_index_list.end()) {
            for (uint32_t j = 0; j < X.size(); j++) {
                int k = 0;
                try {
                    while ((k < params.bin_edges.at(index).size() - 2)
                           && (X[j][i] >= params.bin_edges.at(index)[k + 1]))
                        k++;
                    X[j][i] = k;
                } catch (const std::out_of_range& e) {
                    // This can only happen if params.bin_edges.at(index) is out of range.
                    throw std::runtime_error(
                        "The number of bin_edges does not correspond to the input data: "
                        + std::to_string((check_index == false ? X[j].size() : il.num_index_list.size())) + " vs. "
                        + std::to_string(params.bin_edges.size()) + ".");
                }
            }
            index++;
        }
    }
}

}