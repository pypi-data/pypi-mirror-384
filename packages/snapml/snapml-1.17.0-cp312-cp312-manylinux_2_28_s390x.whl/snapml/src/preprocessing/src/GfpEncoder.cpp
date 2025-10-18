/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2022
 * IBM Zurich Research Laboratory - Infrastructure AIOPS Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Ravinder Rawat
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
#include "GfpEncoder.hpp"
#include <memory>

namespace snapml {

GfpEncoder::GfpEncoder(const snapml::GfpEncoder::Params& params)
    : num_rows(0)
    , num_cols_in(0)
    , num_cols_out(0)
    , features_in(nullptr)
    , features_out(nullptr)
    , params(params)
    , gp(new GraphFeatures::GraphFeaturePreprocessor())
    , X_G(*new std::vector<std::vector<double>>())
{
}

GfpEncoder::~GfpEncoder() { delete &X_G; }

void GfpEncoder::initialize(snapml::AnyDataset& dataset)
{
    std::vector<std::vector<float>>& X_N = feature_list[reinterpret_cast<uint64_t>(&dataset)]->numerical_features;
    num_rows                = feature_list[reinterpret_cast<uint64_t>(&dataset)]->numerical_features.size();
    Features::IndexLists il = feature_list[reinterpret_cast<uint64_t>(&dataset)]->get_index_lists(params.index_list);
    const std::lock_guard<std::mutex> lock(feature_list[reinterpret_cast<uint64_t>(&dataset)]->mtx);
    gp->setParams(params.intParams, params.vecParams);
    num_cols_in  = X_N.empty() ? 0 : X_N[0].size();
    num_cols_out = gp->getNumEngineeredFeatures() + num_cols_in;
    features_in  = std::unique_ptr<double[]>(new double[num_cols_in * num_rows]);
    features_out = std::unique_ptr<double[]>(new double[num_cols_out * num_rows]);
    if (il.num_index_list.size() == 0)
        throw std::runtime_error("Invalid index list size zero.");
    else if (index_list_valid(il.num_index_list, num_cols_in) == false)
        throw std::runtime_error("Invalid index list.");

    for (size_t i = 0; i < X_N.size(); ++i) {
        for (size_t j = 0; j < X_N[i].size(); ++j) {
            features_in[i * num_cols_in + j] = static_cast<double>(X_N[i][j]);
        }
    }
}

void GfpEncoder::fit(snapml::AnyDataset& dataset)
{
    initialize(dataset);
    gp->loadGraph(features_in.get(), num_rows, num_cols_in);
}

void GfpEncoder::fit_transform(snapml::AnyDataset& dataset)
{
    initialize(dataset);
    gp->loadGraph(features_in.get(), num_rows, num_cols_in);
    gp->enrichFeatureVectors(num_rows, features_in.get(), num_cols_in, features_out.get(), num_cols_out);

#ifdef GFP_TEST
    std::vector<std::vector<double>>& X_G = feature_list[reinterpret_cast<uint64_t>(&dataset)]->gfp_data;
    X_G.resize(num_rows, std::vector<double>(num_cols_out));
    for (int i = 0; i < num_rows; ++i) {
        // Assign values from features_out into the corresponding row of X_G
        for (int j = 0; j < num_cols_out; ++j) {
            X_G[i][j] = features_out[i * num_cols_out + j];
        }
    }
#endif
}
// Transform function: Applies transformations on the dataset
void GfpEncoder::transform(snapml::AnyDataset& dataset)
{
    initialize(dataset);
    gp->enrichFeatureVectors(num_rows, features_in.get(), num_cols_in, features_out.get(), num_cols_out);

#ifdef GFP_TEST
    std::vector<std::vector<double>>& X_G = feature_list[reinterpret_cast<uint64_t>(&dataset)]->gfp_data;
    X_G.resize(num_rows, std::vector<double>(num_cols_out));
    for (int i = 0; i < num_rows; ++i) {
        // Assign values from features_out into the corresponding row of X_G
        for (int j = 0; j < num_cols_out; ++j) {
            X_G[i][j] = features_out[i * num_cols_out + j];
        }
    }
#endif
}

} // namespace snapml