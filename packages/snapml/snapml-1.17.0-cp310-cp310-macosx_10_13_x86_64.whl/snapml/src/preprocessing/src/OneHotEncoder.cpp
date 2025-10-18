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

#include "DenseDataset.hpp"
#include "DataSchema.hpp"
#include "AnyDataset.hpp"
#include "Features.hpp"
#include "Transformer.hpp"

#include "OneHotEncoder.hpp"

namespace snapml {

OneHotEncoder::OneHotEncoder(const snapml::OneHotEncoder::Params _params)
    : params(_params)
{
}

void OneHotEncoder::transform(snapml::AnyDataset& dataset)

{
    std::vector<std::vector<std::string>>& X = feature_list[reinterpret_cast<uint64_t>(&dataset)]->categorical_features;
    std::vector<std::map<uint32_t, std::vector<float>>>& OHE
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
    uint32_t index = 0;
    for (uint32_t i = 0; i < size; i++) { // feature
        if (check_index == false || il.cat_index_list.find(i) != il.cat_index_list.end()) {
            index++;
        }
    }

    if (index != params.categories.size())
        throw std::runtime_error("Input has " + std::to_string(index) + " features, but OneHotEncoder is expecting "
                                 + std::to_string(params.categories.size()) + " features as input.");

    for (uint32_t j = 0; j < X.size(); j++) { // transaction
        index = 0;
        for (uint32_t i = 0; i < size; i++) { // feature
            if (check_index == false || il.cat_index_list.find(i) != il.cat_index_list.end()) {
                OHE[j][i].resize(params.categories[index].size(), 0);
                std::map<std::string, int>::iterator it = params.categories[index].find(X[j][i]);
                if (it != params.categories[index].end())
                    OHE[j][i][it->second] = 1;
                index++;
            }
        }
    }
}

}
