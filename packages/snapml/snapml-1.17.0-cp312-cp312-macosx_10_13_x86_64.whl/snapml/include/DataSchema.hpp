/*********************************************************************
 *
 * Licensed Materials - Property of IBM
 *
 * (C) Copyright IBM Corp. 2022, 2023. All Rights Reserved.

 * US Government Users Restricted Rights - Use, duplication or
 * disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
 *
 ********************************************************************/

#pragma once
namespace snapml {

//! @ingroup c-api
struct DataSchema {
    DataSchema()
        : indices_num_features({})
        , indices_cat_features({})
        , num_features(0)
        , index_to_feature_name({})
        , enforce_byteswap(false)
    {
    }
    DataSchema(std::vector<uint32_t> _indices_num_features, std::vector<uint32_t> _indices_cat_features,
               uint32_t _num_features, std::map<uint32_t, std::string> _index_to_feature_name,
               bool enforce_byteswap = false)
        : indices_num_features(_indices_num_features)
        , indices_cat_features(_indices_cat_features)
        , num_features(_num_features)
        , index_to_feature_name(_index_to_feature_name)
        , enforce_byteswap(enforce_byteswap)
    {
    }
    std::vector<uint32_t>           indices_num_features;
    std::vector<uint32_t>           indices_cat_features;
    uint32_t                        num_features;
    std::map<uint32_t, std::string> index_to_feature_name;

    // when true, the numerical bytes in input buffer will be byte-swapped.
    // When this code is running on Big-Endian, Input Buffer is sent in Little-Endian format, set to True
    bool enforce_byteswap;
};

}