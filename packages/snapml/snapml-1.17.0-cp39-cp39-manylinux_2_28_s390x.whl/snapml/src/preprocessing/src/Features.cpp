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

#include <algorithm>
#include <vector>
#include <set>
#include <string>
#include <map>
#include <mutex>
#include <memory>

#include "DataSchema.hpp"
#include "DenseDataset.hpp"
#include "Features.hpp"

namespace snapml {

/*!
 * Within the JSON description of the pipeline a schema can look like the following:
 * { { 3, 5, 6, 8, 9 }, { 0, 1, 2, 4, 7, 10, 11 }, 12, {} }
 * means 3, 5, 6, 8, and 9 are numerical features and 0, 1, 2, 4, 7, 10, 11 are categorical features. E.g. if a
 * Normalizer is provided with an index list, e.g. to only process the 5th and 8th element this needs to be mapped to
 * the 2nd and 4th element of the numerical vector. This function provides this mapping.
 */
Features::IndexLists Features::get_index_lists(std::set<uint32_t> index_list)
{
    Features::IndexLists il {};
    uint32_t             n_i = 0;
    uint32_t             c_i = 0;

    for (uint32_t i : index_list) {
        for (n_i = 0; n_i < data_schema.indices_num_features.size() && i != data_schema.indices_num_features[n_i];
             n_i++)
            ;
        if (n_i < data_schema.indices_num_features.size()) {
            il.num_index_list.insert(n_i);
        } else {
            for (c_i = 0; c_i < data_schema.indices_cat_features.size() && i != data_schema.indices_cat_features[c_i];
                 c_i++)
                ;
            if (c_i < data_schema.indices_cat_features.size()) {
                il.cat_index_list.insert(c_i);
            } else {
                throw std::runtime_error("unable to find index " + std::to_string(i) + ".");
            }
        }
    }

    return il;
}

snapml::DenseDataset Features::toDenseDataset()

{
    uint32_t num_feature_pos;
    uint32_t cat_feature_pos;

    uint32_t            num_transactions = numerical_features.size();
    snapml::DataSchema& ds               = data_schema;

    data_.clear();
    labs_.clear();

    for (uint32_t t = 0; t < num_transactions; t++) {
        num_feature_pos = 0;
        cat_feature_pos = 0;
        for (uint32_t f = 0; f < ds.num_features; f++) {
            if (std::find(ds.indices_num_features.begin(), ds.indices_num_features.end(), f)
                != std::end(ds.indices_num_features)) {
                data_.push_back(numerical_features[t][num_feature_pos]);
                num_feature_pos++;
            } else if (std::find(ds.indices_cat_features.begin(), ds.indices_cat_features.end(), f)
                       != std::end(ds.indices_cat_features)) {

                if (enc_features[t].find(cat_feature_pos) != enc_features[t].end()) {
                    for (float x : enc_features[t][cat_feature_pos]) {
                        data_.push_back(x);
                    }
                    cat_feature_pos++;
                } else {
                    throw std::runtime_error("Non-numeric value in pre-processed data: "
                                             + categorical_features[t][cat_feature_pos]);
                }
            }
        }
    }

    labs_.resize(num_transactions, 0);

    return snapml::DenseDataset(data_, labs_);
}

}
