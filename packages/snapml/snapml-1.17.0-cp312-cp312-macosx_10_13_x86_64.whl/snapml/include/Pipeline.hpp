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
class Pipeline {
public:
    Pipeline();
    ~Pipeline();
    void                            import(std::string json_filename);
    snapml::DenseDataset            transform(snapml::AnyDataset& dataset);
    snapml::DenseDataset            fit_transform(snapml::AnyDataset& dataset);
    snapml::DenseDataset            fit(snapml::AnyDataset& dataset);
    snapml::DataSchema              get_schema();
    std::vector<std::vector<float>> get_vec(snapml::AnyDataset& dataset);

private:
    void get_data_schema(rapidjson::Document& doc);
    void get_normalizer(rapidjson::SizeType i, const rapidjson::Value& value, std::set<uint32_t>& index_list);
    void get_function_transformer(rapidjson::SizeType i, const rapidjson::Value& value, std::set<uint32_t>& index_list);
    void get_k_bins_discretizer(rapidjson::SizeType i, const rapidjson::Value& value, std::set<uint32_t>& index_list);
    void get_one_hot_encoder(rapidjson::SizeType i, const rapidjson::Value& value, std::set<uint32_t>& index_list);
    void get_ordinal_encoder(rapidjson::SizeType i, const rapidjson::Value& value, std::set<uint32_t>& index_list);
    void get_target_encoder(rapidjson::SizeType i, const rapidjson::Value& value, std::set<uint32_t>& index_list);
    void get_gfp_encoder(rapidjson::SizeType i, const rapidjson::Value& value, std::set<uint32_t>& index_list);

    std::vector<snapml::Transformer*> preprocessing_steps;
    snapml::DataSchema                data_schema;
};

}
