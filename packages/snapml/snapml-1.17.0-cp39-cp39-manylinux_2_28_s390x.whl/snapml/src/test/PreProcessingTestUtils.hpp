#ifndef _PREPROCESSING_TEST_UTILS_H_
#define _PREPROCESSING_TEST_UTILS_H_

#include <assert.h>
#include <unistd.h>
#include <Python.h>

#include <vector>
#include <map>
#include <set>
#include <string>
#include <fstream>
#include <sstream>
#include <iostream>
#include <thread>
#include <functional>
#include <cstring>
#include <cmath>

#include <rapidjson/document.h>
#include <rapidjson/filereadstream.h>

#include "DenseDataset.hpp"
#include "DataSchema.hpp"
#include "AnyDataset.hpp"
#include "Transformer.hpp"
#include "Normalizer.hpp"
#include "KBinsDiscretizer.hpp"
#include "FunctionTransformer.hpp"
#include "OneHotEncoder.hpp"
#include "OrdinalEncoder.hpp"
#include "TargetEncoder.hpp"
#include "Pipeline.hpp"
#include "DenseDatasetInt.hpp"
#include "Features.hpp"
#include "Constants.hpp"
#include "GfpEncoder.hpp"

#define VCR(CSTR) std::vector<char>((char*)CSTR, (char*)CSTR + sizeof(CSTR) - 1)

#if defined(__BYTE_ORDER__) && (__BYTE_ORDER__ == __ORDER_BIG_ENDIAN__)
#define IS_HOST_LITTLE_ENDIAN false
#else
#define IS_HOST_LITTLE_ENDIAN true
#endif

class AnyDatasetTest : public snapml::AnyDataset {
public:
    AnyDatasetTest(const std::vector<char> input_vector, const snapml::DataSchema schema,
                   const std::string delimiter = "")
        : AnyDataset(input_vector, schema) {};

    AnyDatasetTest() = default;
    ~AnyDatasetTest() { }
    std::string get_final_features();

    std::string get_numerical_features();

    std::string get_categorical_features();

    std::string get_enc_features();

    std::string get_gfp_data();
};

struct TestCase {
    TestCase(const std::vector<char> _input_buffer, const snapml::DataSchema _schema, bool _success,
             std::string _message)
        : input_buffer(_input_buffer)
        , schema(_schema)
        , success(_success)
        , message(_message)
    {
    }
    const std::vector<char>  input_buffer;
    const snapml::DataSchema schema;
    bool                     success;
    std::string              message;
};

std::vector<char> to_octal_length_prefix(size_t value);
std::vector<char> replace_delimiter_with_octal_prefix(const std::vector<char>&, char delimiter = ',');
bool              is_enforce_byteswap(bool is_data_little_endian);

#endif