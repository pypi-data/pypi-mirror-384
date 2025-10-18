#include "PreProcessingTestUtils.hpp"

template <typename T> std::string to_string(std::vector<std::vector<T>>& X)
{
    std::vector<T>    vec;
    std::stringstream sstr;
    sstr << "[";
    for (uint32_t i = 0; i < X.size() - 1; i++) {
        sstr << "[";
        vec = X[i];
        for (uint32_t j = 0; j < vec.size() - 1; j++)
            sstr << vec[j] << ", ";
        sstr << vec[vec.size() - 1] << "], ";
    }
    if (X.size() > 0) {
        vec = X[X.size() - 1];
        sstr << "[";
        for (uint32_t j = 0; j < vec.size() - 1; j++)
            sstr << vec[j] << ", ";
        sstr << vec[vec.size() - 1] << "]";
        sstr << "]";
    }
    return sstr.str();
}

std::string AnyDatasetTest::get_final_features()
{
    snapml::feature_list[reinterpret_cast<uint64_t>(this)]->toDenseDataset();
    std::vector<std::vector<float>> result({ snapml::feature_list[reinterpret_cast<uint64_t>(this)]->get_data() });
    return to_string(result);
}

std::string AnyDatasetTest::get_numerical_features()
{
    return to_string(snapml::feature_list[reinterpret_cast<uint64_t>(this)]->numerical_features);
}

std::string AnyDatasetTest::get_categorical_features()
{
    return to_string(snapml::feature_list[reinterpret_cast<uint64_t>(this)]->categorical_features);
}

std::string AnyDatasetTest::get_enc_features()
{
    std::vector<std::map<uint32_t, std::vector<float>>> X
        = snapml::feature_list[reinterpret_cast<uint64_t>(this)]->enc_features;

    std::map<uint32_t, std::vector<float>> m;
    uint32_t                               j;
    std::stringstream                      sstr;
    sstr << "[";
    for (uint32_t i = 0; i + 1 < X.size(); i++) {
        sstr << "[";
        m = X[i];
        std::vector<float> vec;
        for (std::pair<uint32_t, std::vector<float>> p : m)
            for (float d : p.second)
                vec.push_back(d);
        for (j = 0; j < vec.size() - 1; j++)
            sstr << vec[j] << ", ";
        sstr << vec[j] << "], ";
    }
    if (X.size() > 0) {
        sstr << "[";
        m = X[X.size() - 1];
        std::vector<float> vec;
        for (std::pair<uint32_t, std::vector<float>> p : m)
            for (float d : p.second)
                vec.push_back(d);
        for (j = 0; j < vec.size() - 1; j++)
            sstr << vec[j] << ", ";
        sstr << vec[j] << "]";
    }
    sstr << "]";

    return sstr.str();
}
std::string AnyDatasetTest::get_gfp_data()
{
    return to_string(snapml::feature_list[reinterpret_cast<uint64_t>(this)]->gfp_data);
}
// Function to return the length as a 4-byte vector
std::vector<char> to_octal_length_prefix(size_t value)
{
    std::vector<char> octal_length(4, '\0'); // Allocate 4 bytes for the length
    for (int i = 0; i < 4; ++i) {
        octal_length[i] = static_cast<char>((value >> (i * 8)) & 0xFF);
    }
    return octal_length;
}

// Updated function to replace delimiters and prefix tokens with octal length in binary form
std::vector<char> replace_delimiter_with_octal_prefix(const std::vector<char>& input, char delimiter)
{
    std::vector<char> result;
    std::string       current_token;

    // Process each character in the vector
    for (char c : input) {
        if (c == delimiter || c == '\n') { // Check for the specified delimiter or newline
            if (!current_token.empty()) {
                // Add the octal length prefix for the current token
                std::vector<char> prefixed_token = to_octal_length_prefix(current_token.size());
                result.insert(result.end(), prefixed_token.begin(), prefixed_token.end());
                result.insert(result.end(), current_token.begin(), current_token.end());
                current_token.clear(); // Clear the current token
            }
        } else {
            current_token += c; // Build the current token
        }
    }

    // Add the last token if there's any
    if (!current_token.empty()) {
        std::vector<char> prefixed_token = to_octal_length_prefix(current_token.size());
        result.insert(result.end(), prefixed_token.begin(), prefixed_token.end());
        result.insert(result.end(), current_token.begin(), current_token.end());
    }

    return result;
}

bool is_enforce_byteswap(bool is_data_little_endian = IS_HOST_LITTLE_ENDIAN)
{
    // This helps to run tests in both little endian and big endian machines.

    // (is_data_little_endian && !is_host_little_endian) || (!is_data_little_endian && is_host_little_endian)
    return is_data_little_endian ^ IS_HOST_LITTLE_ENDIAN;
}
