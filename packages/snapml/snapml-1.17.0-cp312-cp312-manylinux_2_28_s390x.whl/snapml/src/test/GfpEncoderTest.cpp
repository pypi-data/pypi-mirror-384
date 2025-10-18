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

#include "PreProcessingTestUtils.hpp"

std::vector<std::vector<double>> two_data_set = { { 1, 6, 0, 2 }, { 2, 7, 2, 0 } };
std::vector<std::vector<double>> four_data_set
    = { { 45, 78, 12, 34 }, { 56, 89, 23, 67 }, { 14, 95, 36, 88 }, { 22, 44, 68, 99 } };

std::vector<std::vector<double>> eight_data_set
    = { { 12, 34, 56, 78 }, { 90, 23, 45, 67 }, { 89, 12, 34, 56 }, { 78, 90, 23, 45 },
        { 56, 78, 90, 12 }, { 34, 56, 78, 90 }, { 23, 45, 67, 89 }, { 12, 34, 56, 78 } };
std::vector<std::vector<double>> ten_data_set
    = { { 1.23, 4.56, 7.89, 0.12 }, { 3.45, 6.78, 9.01, 2.34 }, { 5.67, 8.90, 1.23, 4.56 }, { 7.89, 0.12, 3.45, 6.78 },
        { 9.01, 2.34, 5.67, 8.90 }, { 0.12, 3.45, 6.78, 9.01 }, { 2.34, 5.67, 8.90, 1.23 }, { 4.56, 7.89, 0.12, 3.45 },
        { 6.78, 9.01, 2.34, 5.67 }, { 8.90, 1.23, 4.56, 7.89 } };

void compare_transform(const std::string& result, const std::vector<std::vector<double>>& input)
{
    std::stringstream sstr;
    sstr << R"(
import os    
import sys
import warnings
# Ignore numpy warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
pd.options.display.max_columns = None
if "__file__" not in globals():
    __file__ = os.path.abspath(sys.argv[0])
gfp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if gfp_dir not in sys.path:
    sys.path.append(gfp_dir)

from snapml.GraphFeaturePreprocessor import GraphFeaturePreprocessor

if __name__ == '__main__':
    result = np.array()"
         << result << R"().astype(float)
    print(f"Result dimensions: {result.shape}")
    input = np.array([)"
         << std::endl;

    for (const auto& row : input) {
        sstr << "        [";
        for (size_t i = 0; i < row.size(); ++i) {
            sstr << row[i];
            if (i < row.size() - 1) {
                sstr << ", ";
            }
        }
        sstr << "]," << std::endl;
    }
    sstr << R"(    ])    
    df = pd.DataFrame(
        input, columns=['transactionID', 'sourceAccountID', 'targetAccountID', 'timestamp']
    )
    params = {
        'num_threads': 4,
        'time_window': 16,
        'max_no_edges': -1,
        'vertex_stats': True,
        'vertex_stats_tw': 1728000,
        'vertex_stats_cols': [3],
        'vertex_stats_feats': [0, 1, 2, 3, 4, 8, 9, 10],
        'fan': True,
        'fan_tw': 16,
        'fan_bins': [y + 2 for y in range(2)],
        'degree': True,
        'degree_tw': 16,
        'degree_bins': [y + 2 for y in range(2)],
        'scatter-gather': True,
        'scatter-gather_tw': 16,
        'scatter-gather_bins': [y + 2 for y in range(2)],
        'temp-cycle': True,
        'temp-cycle_tw': 16,
        'temp-cycle_bins': [y + 2 for y in range(2)],
        'lc-cycle': False,
        'lc-cycle_tw': 16,
        'lc-cycle_len': 8,
        'lc-cycle_bins': [y + 2 for y in range(2)],
    }
    graph_preprocessor = GraphFeaturePreprocessor()
    graph_preprocessor.set_params(params)
    expected = graph_preprocessor.transform(df.astype('float64'))
    print(f"Expected dimensions: {expected.shape}")
    if not np.allclose(result, expected):
        raise Exception(f'result {result} does not match the expected {expected}')
)";

    if (PyRun_SimpleString(sstr.str().c_str())) {
        std::cout << "Comparison Failed for GraphFeaturePreprocessor transform" << std::endl;
        assert(0);
    } else {
        std::cout << "Comparison Succeeded for GraphFeaturePreprocessor transform" << std::endl;
    }
}

void compare_fit_transform(const std::string& result, const std::vector<std::vector<double>>& input)
{
    std::stringstream sstr;
    sstr << R"(
import os    
import sys
import warnings
# Ignore numpy warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
pd.options.display.max_columns = None
if "__file__" not in globals():
    __file__ = os.path.abspath(sys.argv[0])
gfp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if gfp_dir not in sys.path:
    sys.path.append(gfp_dir)

from snapml.GraphFeaturePreprocessor import GraphFeaturePreprocessor

if __name__ == '__main__':
    result = np.array()"
         << result << R"().astype(float)
    print(f"Result dimensions: {result.shape}")
    input = np.array([)"
         << std::endl;

    for (const auto& row : input) {
        sstr << "        [";
        for (size_t i = 0; i < row.size(); ++i) {
            sstr << row[i];
            if (i < row.size() - 1) {
                sstr << ", ";
            }
        }
        sstr << "]," << std::endl;
    }
    sstr << R"(    ])    
    df = pd.DataFrame(
        input, columns=['transactionID', 'sourceAccountID', 'targetAccountID', 'timestamp']
    )
    params = {
        'num_threads': 4,
        'time_window': 16,
        'max_no_edges': -1,
        'vertex_stats': True,
        'vertex_stats_tw': 1728000,
        'vertex_stats_cols': [3],
        'vertex_stats_feats': [0, 1, 2, 3, 4, 8, 9, 10],
        'fan': True,
        'fan_tw': 16,
        'fan_bins': [y + 2 for y in range(2)],
        'degree': True,
        'degree_tw': 16,
        'degree_bins': [y + 2 for y in range(2)],
        'scatter-gather': True,
        'scatter-gather_tw': 16,
        'scatter-gather_bins': [y + 2 for y in range(2)],
        'temp-cycle': True,
        'temp-cycle_tw': 16,
        'temp-cycle_bins': [y + 2 for y in range(2)],
        'lc-cycle': False,
        'lc-cycle_tw': 16,
        'lc-cycle_len': 8,
        'lc-cycle_bins': [y + 2 for y in range(2)],
    }
    graph_preprocessor = GraphFeaturePreprocessor()
    graph_preprocessor.set_params(params)
    expected = graph_preprocessor.fit_transform(df.astype('float64'))
    print(f"Expected dimensions: {expected.shape}")
    if not np.allclose(result, expected):
        raise Exception(f'result {result} does not match the expected {expected}')
)";

    if (PyRun_SimpleString(sstr.str().c_str())) {
        std::cout << "Comparison Failed for GraphFeaturePreprocessor fit_transform" << std::endl;
        assert(0);
    } else {
        std::cout << "Comparison Succeeded for GraphFeaturePreprocessor fit_transform" << std::endl;
    }
}

void custom_compare_transform(const std::string& result)
{
    std::stringstream sstr;
    sstr << R"(
import os    
import sys
import warnings
# Ignore numpy warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
pd.options.display.max_columns = None
if "__file__" not in globals():
    __file__ = os.path.abspath(sys.argv[0])
gfp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",".."))
if gfp_dir not in sys.path:
    sys.path.append(gfp_dir)
from snapml.GraphFeaturePreprocessor import GraphFeaturePreprocessor
test_graph_path = "../test/data/aml_custom_test.txt"
train_graph_path = "../test/data/aml_custom_train.txt"
X_train = np.loadtxt(
    train_graph_path,
    dtype=np.float64,
    delimiter=" ",
    comments="#",
    usecols=range(4),
)
X_test = np.loadtxt(
    test_graph_path,
    dtype=np.float64,
    delimiter=" ",
    comments="#",
    usecols=range(4),
)
if __name__ == '__main__':
    result = np.array()"
         << result << R"().astype(float)
print(f"Result dimensions: {result.shape}")         
params = {
    'num_threads': 4,
    'time_window': 16,
    'max_no_edges': -1,
    'vertex_stats': True,
    'vertex_stats_tw': 1728000,
    'vertex_stats_cols': [3],
    'vertex_stats_feats': [0, 1, 2, 3, 4, 8, 9, 10],
    'fan': True,
    'fan_tw': 16,
    'fan_bins': [y + 2 for y in range(2)],
    'degree': True,
    'degree_tw': 16,
    'degree_bins': [y + 2 for y in range(2)],
    'scatter-gather': True,
    'scatter-gather_tw': 16,
    'scatter-gather_bins': [y + 2 for y in range(2)],
    'temp-cycle': True,
    'temp-cycle_tw': 16,
    'temp-cycle_bins': [y + 2 for y in range(2)],
    'lc-cycle': True,
    'lc-cycle_tw': 16,
    'lc-cycle_len': 8,
    'lc-cycle_bins': [y + 2 for y in range(4)],
}
# Graph preprocessor that uses fit on the train set and transform on the test set
gp_ft = GraphFeaturePreprocessor()
gp_ft.set_params(params)
# Fit train data using gp_ft
gp_ft.fit(X_train)
expected = gp_ft.transform(X_test)
print(f"Expected dimensions: {expected.shape}")
if not np.allclose(result, expected):
    raise Exception(f'result {result} does not match the expected {expected}')
)";
    if (PyRun_SimpleString(sstr.str().c_str())) {
        std::cout << "Comparison Failed for GraphFeaturePreprocessor custom transform" << std::endl;
        assert(0);
    } else {
        std::cout << "Comparison Succeeded for GraphFeaturePreprocessor custom transform" << std::endl;
    }
}

int main(int argc, char* argv[])
{
    Py_Initialize();

    // Add reference to __main__ module
    PyObject* main_module = PyImport_AddModule("__main__");
    if (main_module == NULL) {
        PyErr_Print();
        return -1;
    }

    PyObject* globals = PyModule_GetDict(main_module);
    if (globals == NULL) {
        PyErr_Print();
        return -1;
    }

    const std::vector<char> input_vector_two
        = VCR("\004\000\000\0000001\004\000\000\0000006\004\000\000\0000000\004\000\000\0000002"
              "\004\000\000\0000002\004\000\000\0000007\004\000\000\0000002\004\000\000\0000000");

    const std::vector<char> input_vector_four
        = VCR("\004\000\000\0000045\004\000\000\0000078\004\000\000\0000012\004\000\000\0000034"
              "\004\000\000\0000056\004\000\000\0000089\004\000\000\0000023\004\000\000\0000067\004"
              "\000\000\0000014\004\000\000\0000095\004\000\000\0000036\004\000\000\0000088\004"
              "\000\000\0000022\004\000\000\0000044\004\000\000\0000068\004\000\000\0000099");

    const std::vector<char> input_vector_eight
        = VCR("\004\000\000\0000012\004\000\000\0000034\004\000\000\0000056\004\000\000\0000078\004\000\000\0000090"
              "\004\000\000\0000023\004\000\000\0000045\004\000\000\0000067\004\000\000\0000089\004\000\000\0000012"
              "\004\000\000\0000034\004\000\000\0000056\004\000\000\0000078\004\000\000\0000090\004\000\000\0000023"
              "\004\000\000\0000045\004\000\000\0000056\004\000\000\0000078\004\000\000\0000090\004\000\000\0000012"
              "\004\000\000\0000034\004\000\000\0000056\004\000\000\0000078\004\000\000\0000090\004\000\000\0000023"
              "\004\000\000\0000045\004\000\000\0000067\004\000\000\0000089\004\000\000\0000012\004\000\000\0000034"
              "\004\000\000\0000056\004\000\000\0000078");

    const std::vector<char> input_vector_ten
        = VCR("\004\000\000\0001.23\004\000\000\0004.56\004\000\000\0007.89\004\000\000\0000.12\004\000\000\0003.45"
              "\004\000\000\0006.78\004\000\000\0009.01\004\000\000\0002.34\004\000\000\0005.67\004\000\000\0008.90"
              "\004\000\000\0001.23\004\000\000\0004.56\004\000\000\0007.89\004\000\000\0000.12\004\000\000\0003.45"
              "\004\000\000\0006.78\004\000\000\0009.01\004\000\000\0002.34\004\000\000\0005.67\004\000\000\0008.90"
              "\004\000\000\0000.12\004\000\000\0003.45\004\000\000\0006.78\004\000\000\0009.01\004\000\000\0002.34"
              "\004\000\000\0005.67\004\000\000\0008.90\004\000\000\0001.23\004\000\000\0004.56\004\000\000\0007.89"
              "\004\000\000\0000.12\004\000\000\0003.45\004\000\000\0006.78\004\000\000\0009.01\004\000\000\0002.34"
              "\004\000\000\0005.67\004\000\000\0008.90\004\000\000\0001.23\004\000\000\0004.56\004\000\000\0007.89");

    const std::vector<char> aml_custom_train
        = VCR("\004\000\000\0000000\004\000\000\0000000\004\000\000\0000001\004\000\000\0000000"
              "\004\000\000\0000000\004\000\000\0000000\004\000\000\0000001\004\000\000\0000000"
              "\004\000\000\0000000\004\000\000\0000000\004\000\000\0000001\004\000\000\0000000"
              "\004\000\000\0000001\004\000\000\0000001\004\000\000\0000002\004\000\000\0000001"
              "\004\000\000\0000002\004\000\000\0000002\004\000\000\0000003\004\000\000\0000002"
              "\004\000\000\0000003\004\000\000\0000001\004\000\000\0000003\004\000\000\0000003"
              "\004\000\000\0000004\004\000\000\0000003\004\000\000\0000001\004\000\000\0000004"
              "\004\000\000\0000004\004\000\000\0000003\004\000\000\0000001\004\000\000\0000004"
              "\004\000\000\0000004\004\000\000\0000003\004\000\000\0000001\004\000\000\0000004"
              "\004\000\000\0000005\004\000\000\0000003\004\000\000\0000000\004\000\000\0000005"
              "\004\000\000\0000006\004\000\000\0000000\004\000\000\0000002\004\000\000\0000006"
              "\004\000\000\0000007\004\000\000\0000002\004\000\000\0000000\004\000\000\0000007");

    const std::vector<char> aml_custom_test
        = VCR("\004\000\000\0000008\004\000\000\0000008\004\000\000\0000009\004\000\000\0000008"
              "\004\000\000\0000009\004\000\000\0000009\004\000\000\0000010\004\000\000\0000009"
              "\004\000\000\0000010\004\000\000\0000010\004\000\000\0000011\004\000\000\0000010"
              "\004\000\000\0000011\004\000\000\0000009\004\000\000\0000011\004\000\000\0000011"
              "\004\000\000\0000012\004\000\000\0000011\004\000\000\0000009\004\000\000\0000012"
              "\004\000\000\0000013\004\000\000\0000011\004\000\000\0000008\004\000\000\0000013"
              "\004\000\000\0000014\004\000\000\0000008\004\000\000\0000010\004\000\000\0000014"
              "\004\000\000\0000015\004\000\000\0000010\004\000\000\0000008\004\000\000\0000015");

    snapml::DataSchema data_schema = { { 0, 1, 2, 3 }, {}, 4, {}, false };
    data_schema.enforce_byteswap   = is_enforce_byteswap(true);

    AnyDatasetTest   dataset(input_vector_two, data_schema);
    snapml::Pipeline pl;
    try {

        pl.import("../test/data/pipeline_gfp.json");

    } catch (const std::exception& e) {
        std::cout << "Error importing pipeline_gfp information: " << e.what() << std::endl;
        assert(0);
    }
    pl.get_schema();

    try {
        pl.transform(dataset);
    } catch (const std::exception& e) {
        std::cout << "Error running transformers: " << e.what() << std::endl;
        assert(0);
    }
    try {
        compare_transform(dataset.get_gfp_data(), two_data_set);
    } catch (const std::exception& e) {

        std::cout << "Exception occurred compare_transform: " << e.what() << std::endl;
    }

    /* tansfor and fit_transform for  2X4 data */
    AnyDatasetTest dataset_fit(input_vector_two, data_schema);
    try {

        pl.fit_transform(dataset_fit);

    } catch (const std::exception& e) {

        std::cout << "Error running fit_transformers: " << e.what() << std::endl;
        assert(0);
    }
    try {
        compare_fit_transform(dataset_fit.get_gfp_data(), two_data_set);

    } catch (const std::exception& e) {

        std::cout << "Exception occurred compare_fit_transform: " << e.what() << std::endl;
    }

    /* tansfor and fit_transform for  4X4 data */
    AnyDatasetTest dataset_four(input_vector_four, data_schema);
    try {

        pl.transform(dataset_four);

    } catch (const std::exception& e) {

        std::cout << "Error running fit_transformers: " << e.what() << std::endl;
        assert(0);
    }
    try {
        compare_transform(dataset_four.get_gfp_data(), four_data_set);

    } catch (const std::exception& e) {

        std::cout << "Exception occurred compare_fit_transform: " << e.what() << std::endl;
    }
    AnyDatasetTest dataset_four_fit(input_vector_four, data_schema);
    try {

        pl.fit_transform(dataset_four_fit);

    } catch (const std::exception& e) {

        std::cout << "Error running fit_transformers: " << e.what() << std::endl;
        assert(0);
    }
    try {
        compare_fit_transform(dataset_four_fit.get_gfp_data(), four_data_set);

    } catch (const std::exception& e) {

        std::cout << "Exception occurred compare_fit_transform: " << e.what() << std::endl;
    }

    /* tansfor and fit_transform for 8X4 data */
    AnyDatasetTest dataset_egt(input_vector_eight, data_schema);
    try {

        pl.transform(dataset_egt);

    } catch (const std::exception& e) {

        std::cout << "Error running fit_transformers: " << e.what() << std::endl;
        assert(0);
    }
    try {
        compare_transform(dataset_egt.get_gfp_data(), eight_data_set);

    } catch (const std::exception& e) {

        std::cout << "Exception occurred compare_fit_transform: " << e.what() << std::endl;
    }

    AnyDatasetTest dataset_egt_fit(input_vector_eight, data_schema);
    try {

        pl.fit_transform(dataset_egt_fit);

    } catch (const std::exception& e) {

        std::cout << "Error running fit_transformers: " << e.what() << std::endl;
        assert(0);
    }
    try {
        compare_fit_transform(dataset_egt_fit.get_gfp_data(), eight_data_set);

    } catch (const std::exception& e) {

        std::cout << "Exception occurred compare_fit_transform: " << e.what() << std::endl;
    }

    /* tansform and fit_transform for  10X4 data */
    AnyDatasetTest dataset_ten(input_vector_ten, data_schema);
    try {

        pl.transform(dataset_ten);

    } catch (const std::exception& e) {

        std::cout << "Error running transformers: " << e.what() << std::endl;
        assert(0);
    }
    try {
        compare_transform(dataset_ten.get_gfp_data(), ten_data_set);

    } catch (const std::exception& e) {

        std::cout << "Exception occurred compare_transform: " << e.what() << std::endl;
    }
    AnyDatasetTest dataset_ten_fit(input_vector_ten, data_schema);
    try {

        pl.fit_transform(dataset_ten_fit);

    } catch (const std::exception& e) {

        std::cout << "Error running fit_transformers: " << e.what() << std::endl;
        assert(0);
    }
    try {
        compare_fit_transform(dataset_ten_fit.get_gfp_data(), ten_data_set);

    } catch (const std::exception& e) {

        std::cout << "Exception occurred compare_fit_transform: " << e.what() << std::endl;
    }
    /* this test case for aml_custom_train (use c++ fit api )and aml_custom_test (use c++ transform api) */
    snapml::Pipeline pl_custom;
    try {

        pl_custom.import("../test/data/pipeline_gfp_custom.json");

    } catch (const std::exception& e) {
        std::cout << "Error importing pipeline_gfp_custom information: " << e.what() << std::endl;
        assert(0);
    }
    pl_custom.get_schema();
    AnyDatasetTest train_dataset(aml_custom_train, data_schema);
    try {

        pl_custom.fit(train_dataset);
    } catch (const std::exception& e) {
        std::cout << "Error running C++ API Fit: " << e.what() << std::endl;
        assert(0);
    }
    AnyDatasetTest test_dataset(aml_custom_test, data_schema);
    try {

        pl_custom.transform(test_dataset);
    } catch (const std::exception& e) {
        std::cout << "Error running C++ API Fit: " << e.what() << std::endl;
        assert(0);
    }
    try {
        custom_compare_transform(test_dataset.get_gfp_data());

    } catch (const std::exception& e) {

        std::cout << "Exception occurred compare_transform: " << e.what() << std::endl;
    }

    if (Py_FinalizeEx() < 0) {
        exit(120);
    }
    return 0;
}