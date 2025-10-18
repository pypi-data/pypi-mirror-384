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
#include <algorithm>
#include <sstream>
#include <mutex>
#include <unordered_set>
#include <cstring>

#include "DenseDataset.hpp"
#include "DataSchema.hpp"
#include "AnyDataset.hpp"
#include "Features.hpp"
#include <memory>

namespace snapml {

std::map<uint64_t, std::shared_ptr<Features>> feature_list;
std::mutex                                    mtx;

AnyDataset::AnyDataset() { }

AnyDataset::~AnyDataset()
{
    std::lock_guard<std::mutex> lock(mtx);
    feature_list.erase(reinterpret_cast<uint64_t>(this));
}

// check if it is valid float number
bool validate_numerical_data(const std::string& str)
{
    std::istringstream iss(str);
    double             value;
    iss >> std::noskipws >> value;   // Read the value, ignoring whitespace
    return iss.eof() && !iss.fail(); // Check if the entire string was consumed and no errors occurred
}
// Function to check if a string is alphanumeric
bool validate_categorical_data(const std::string& str)
{
    for (char c : str) {
        if (!std::isalnum(static_cast<unsigned char>(c))) {
            return false;
        }
    }
    return true;
}

// Function to extract the length.
// If enforce_byteswap, the bytes are swapped. Set enforce_byteswap to True, if buffer is in different Endian than host
uint32_t extract_feature_length(const char* buffer, size_t length_of_length, bool enforce_byteswap = false)
{
    uint32_t length = 0;
    std::memcpy(&length, buffer, length_of_length);
    // ByteSwap is not needed unless specified since data is usually sent in host endian format.
    if (enforce_byteswap)
        length = __builtin_bswap32(length);
    return length;
}
void build_features(const std::vector<char> input_vector, std::shared_ptr<Features> features)
{
    /*
    This method builds the numerical and categorical features
    The build features are push_back to features->numerical_features and features->categorical_features
    This method assumes the delimiter is \x\x\x\x representing length of characters
     */
    const snapml::DataSchema     data_schema  = features->data_schema;
    int                          featureCount = -1;
    std::string                  currentString;
    std::vector<float>           current_numerical_features   = {};
    std::vector<std::string>     current_categorical_features = {};
    std::string                  prefix;
    std::unordered_set<uint32_t> indices_cat_features(data_schema.indices_cat_features.begin(),
                                                      data_schema.indices_cat_features.end());
    std::unordered_set<uint32_t> indices_num_features(data_schema.indices_num_features.begin(),
                                                      data_schema.indices_num_features.end());
    size_t                       length_of_length = sizeof(uint32_t);
    size_t                       i                = 0;
    try {

        if (data_schema.num_features != indices_cat_features.size() + indices_num_features.size()) {
            throw std::runtime_error("Incorrect data schema.");
        }
        while (i < input_vector.size()) {

            /*
                Read the length of feature.
                Read the feature by reading upto the length
                Repeat till data_schema.num_features
            */

            // Ensure that we're not reading past the end of the vector
            if (i + length_of_length > input_vector.size()) {
                throw std::runtime_error("The feature length is invalid.");
            }
            // Read length from the next 4 bytes (octal format, endian)
            uint32_t length_feature
                = extract_feature_length(&input_vector[i], length_of_length, data_schema.enforce_byteswap);
            if (length_feature == 0) {
                throw std::runtime_error("Length of feature should be greater than 0.");
            }
            i += length_of_length;

            // Ensure that we're not reading past the end of the vector
            if (i + length_feature > input_vector.size()) {
                throw std::runtime_error("The input data is invalid and cannot be read upto the specified length.");
            }

            currentString.assign(&input_vector[i], length_feature);
            i += length_feature;
            featureCount++;
            if (indices_num_features.find(featureCount) != indices_num_features.end()) { // check for numerical feature
                if (!validate_numerical_data(currentString))
                    throw std::runtime_error(currentString + " is specified as a numerical feature.");
                current_numerical_features.push_back(std::stod(currentString));
            } else if (indices_cat_features.find(featureCount)
                       != indices_cat_features.end()) { // check for categorical feature
                if (!validate_categorical_data(currentString))
                    throw std::runtime_error("Input buffer contains feature with invalid characters, token: "
                                             + currentString);
                current_categorical_features.push_back(currentString);
            } else {
                throw std::runtime_error(currentString + " is not categorized in schema.");
            }

            if (featureCount == (data_schema.num_features - 1)) {

                if (data_schema.num_features
                    != current_numerical_features.size() + current_categorical_features.size()) {
                    std::stringstream sstr;
                    sstr << "The data_schema contains a different number of features: " << data_schema.num_features
                         << " vs. " << (current_numerical_features.size() + current_categorical_features.size());
                    throw std::runtime_error(sstr.str());
                }
                features->categorical_features.push_back(current_categorical_features);
                features->numerical_features.push_back(current_numerical_features);
                featureCount = -1;

                current_numerical_features   = {};
                current_categorical_features = {};
            }
        }
    } catch (const std::exception& e) {
        std::stringstream sstr;
        sstr << "AnyDataset: " << e.what();
        throw std::runtime_error(sstr.str());
    }
}

AnyDataset::AnyDataset(const std::vector<char> input_vector, const snapml::DataSchema data_schema)
{
    if (input_vector.size() == 0) {
        throw std::runtime_error("AnyDataset: Input buffer is empty.");
    }
    std::shared_ptr<Features> features = std::make_shared<Features>();
    features->data_schema              = data_schema;
    build_features(input_vector, features);

    if (features->numerical_features.size() > 0) {
        features->num_ex = features->numerical_features.size();
    } else if (features->categorical_features.size() > 0) {
        features->num_ex = features->categorical_features.size();
    } else {
        std::stringstream sstr;
        sstr << "The data_schema contains a different number of features: " << data_schema.num_features << " vs. 0";
        throw std::runtime_error(sstr.str());
    }

    features->enc_features.resize(features->num_ex);

    std::lock_guard<std::mutex> lock(mtx);
    feature_list[reinterpret_cast<uint64_t>(this)] = features;
}

snapml::DenseDataset AnyDataset::convertToDenseDataset()

{
    return feature_list[reinterpret_cast<uint64_t>(this)]->toDenseDataset();
}

uint32_t AnyDataset::get_num_ex() { return feature_list[reinterpret_cast<uint64_t>(this)]->num_ex; }

std::vector<std::vector<float>> AnyDataset::get_vec_data()
{
    std::vector<std::vector<float>> result({ snapml::feature_list[reinterpret_cast<uint64_t>(this)]->get_data() });
    return result;
}

}
