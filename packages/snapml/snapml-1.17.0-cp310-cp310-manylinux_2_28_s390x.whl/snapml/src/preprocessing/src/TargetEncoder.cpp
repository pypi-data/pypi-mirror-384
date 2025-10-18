/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2023, 2024.
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

#include "DenseDataset.hpp"
#include "DataSchema.hpp"
#include "AnyDataset.hpp"
#include "Features.hpp"
#include "Transformer.hpp"

#include "TargetEncoder.hpp"

namespace snapml {

TargetEncoder::TargetEncoder(const snapml::TargetEncoder::Params _params)
    : params(_params)
{
}

void TargetEncoder::transform(snapml::AnyDataset& dataset)

{
    std::vector<std::vector<std::string>>& X = feature_list[reinterpret_cast<uint64_t>(&dataset)]->categorical_features;
    std::vector<std::map<uint32_t, std::vector<float>>>& ENC
        = feature_list[reinterpret_cast<uint64_t>(&dataset)]->enc_features;
    const uint32_t size        = X[0].size();
    bool           check_index = true;

    Features::IndexLists il = feature_list[reinterpret_cast<uint64_t>(&dataset)]->get_index_lists(params.index_list);

    if (il.cat_index_list.size() == 0)
        check_index = false;
    else if (index_list_valid(il.cat_index_list, size) == false)
        throw std::runtime_error("Invalid index list.");

    const std::lock_guard<std::mutex> lock(feature_list[reinterpret_cast<uint64_t>(&dataset)]->mtx);

    // check that the input has the appropriate number of features
    // create the final index_list in case it does not exist
    std::set<uint32_t> index_list;
    uint32_t           index = 0;
    for (uint32_t i = 0; i < size; i++) { // feature
        if (check_index == false || il.cat_index_list.find(i) != il.cat_index_list.end()) {
            index_list.insert(i);
            index++;
        }
    }
    if (index != params.categories.size())
        throw std::runtime_error("Input has " + std::to_string(index) + " features, but TargetEncoder is expecting "
                                 + std::to_string(params.categories.size()) + " features as input.");

    index = 0;
    for (uint32_t i : index_list) {               // feature
        for (uint32_t j = 0; j < X.size(); j++) { // transaction
            std::map<std::string, float>::iterator it = params.categories[index].find(X[j][i]);
            if (it != params.categories[index].end()) {
                ENC[j][i].push_back(it->second);
            } else
                ENC[j][i].push_back(params.target_mean);
        }
        index++;
    }
}

}
