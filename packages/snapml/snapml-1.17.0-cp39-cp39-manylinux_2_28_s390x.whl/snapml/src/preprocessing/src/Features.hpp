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

#pragma once

namespace snapml {

struct Features {
    std::vector<std::vector<float>>                     numerical_features;
    std::vector<std::vector<double>>                    gfp_data;
    std::vector<std::vector<std::string>>               categorical_features;
    std::vector<std::map<uint32_t, std::vector<float>>> enc_features;
    snapml::DataSchema                                  data_schema;
    uint32_t                                            num_ex;
    std::mutex                                          mtx;
    struct IndexLists {
        std::set<uint32_t> num_index_list;
        std::set<uint32_t> cat_index_list;
    };
    IndexLists           get_index_lists(std::set<uint32_t> index_list);
    std::vector<float>&  get_data() { return data_; }
    std::vector<float>&  get_labs() { return labs_; }
    snapml::DenseDataset toDenseDataset();

private:
    std::vector<float> data_;
    std::vector<float> labs_;
};

/*!
 * A set of features are part of an AnyDataset object. A user of the API should not have access to this information: it
 * is only internally used. Therefore, it shouldn't be part as a member variable of the AnyDataset class. The idea is to
 * store this information within a global variable. Since an API user can create multiple AnyDataset objects a std::map
 * is used to store pairs of the memory address of the AnyDataset object and the corresponding Features object.
 */
extern std::map<uint64_t, std::shared_ptr<Features>> feature_list;

}
