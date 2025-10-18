#include "PreProcessingTestUtils.hpp"

bool test(TestCase tc)

{
    bool success = true;
    try {
        AnyDatasetTest ad(tc.input_buffer, tc.schema);
        if (tc.success == false) {
            std::cout << "Expected the test failing but it passed." << std::endl;
            success = false;
        }
    } catch (const std::exception& e) {
        if (tc.success == true) {
            success = false;
            std::cout << "Expected the test passing but it failed." << std::endl << std::endl;
        } else {
            if (e.what() != tc.message) {
                std::cout << "message: " << e.what() << ", expected message: " << tc.message << std::endl;
                success = false;
            }
        }
    }

    return success;
}

// \000\000\000\000
void test_input()
{
    std::vector<TestCase> tcs {
        { VCR(""), {}, false, "AnyDataset: Input buffer is empty." }, // empty buffer
        { VCR("\000\000\000\000"),
          { { 0 }, {}, 1, {}, is_enforce_byteswap(true) },
          false,
          "AnyDataset: Length of feature should be greater than 0." }, // empty buffer with single feature
        { VCR("\000\000\000\000"),
          { { 0 }, {}, 2, {}, is_enforce_byteswap(true) },
          false,
          "AnyDataset: Incorrect data schema." }, // empty buffer with multiple feature
        { VCR("\004\000\000\0002abd\001\000\000\0007"),
          { { 1 }, { 0 }, 2, {}, is_enforce_byteswap(true) },
          true,
          "" }, // OK (two features)
        { VCR("\000\000\000\0152littleEndian\000\000\000\0017"),
          { { 1 }, { 0 }, 2, {}, is_enforce_byteswap(false) },
          true,
          "" }, // OK Big Endian (two features)
        { VCR("\004\000\000\0003cde"),
          { {}, { 0 }, 1, {}, is_enforce_byteswap(true) },
          true,
          "" }, // OK (single feature)
        { VCR("\040\000\000\000abcdefghijabcdefghijabcdefghijab"),
          { {}, { 0 }, 1, {}, is_enforce_byteswap(true) },
          true,
          "" }, // OK (long feature)
        // Try reading beyond the vector size. Provide feature length as way greater than actual feature input
        { VCR("\005\000\000\0003cde"),
          { {}, { 0 }, 1, {}, is_enforce_byteswap(true) },
          false,
          "AnyDataset: The input data is invalid and cannot be read upto the specified length." },
        // Try reading within the vector size. Provide feature length as way lesser than actual feature input
        { VCR("\002\000\000\000ab77"),
          { {}, { 0 }, 1, {}, is_enforce_byteswap(true) },
          false,
          "AnyDataset: The feature length is invalid." },
        // Try reading within the vector size. Provide lesser feature length with more than 4 characters remaining
        { VCR("\003\000\000\000cde77777"),
          { {}, { 0 }, 1, {}, is_enforce_byteswap(true) },
          false,
          "AnyDataset: The input data is invalid and cannot be read upto the specified length." },
        // Try reading within the vector size. Provide lesser feature length with more than 4 characters remaining
        { VCR("\001\000\000\000a\007\000\000\000"),
          { {}, { 0 }, 1, {}, is_enforce_byteswap(true) },
          false,
          "AnyDataset: The input data is invalid and cannot be read upto the specified length." },
        { VCR("\004\000\000\0004abd\001\000\000\0007"),
          { {}, { 0 }, 2, {}, is_enforce_byteswap(true) },
          false,
          "AnyDataset: Incorrect data schema." }, // incorrect number of features
        { VCR("\004\000\000\0005cde\001\000\000\0008"),
          { { 0 }, { 1 }, 2, {}, is_enforce_byteswap(true) },
          false,
          "AnyDataset: 5cde is specified as a numerical feature." }, // wrong feature categorization
        { VCR("\011\000\000\0009sdfdfsdf\003\000\000\00078s\007\000\000\000swfgswg\004\000\000\00015."
              "3\007\000\000\000jdadasc\004\000\000\0001E-"
              "5\003\000\000\000001\005\000\000\000sddjd\002\000\000\00011\004\000\000\000-1."
              "2\003\000\000\000GGG\001\000\000\000A"),
          { { 3, 5, 6, 8, 9 }, { 0, 1, 2, 4, 7, 10, 11 }, 12, {}, is_enforce_byteswap(true) },
          true,
          "" }, // OK
        { VCR("\012\000\000\00010sdfdfsdf\003\000\000\00078s\007\000\000\000swfgswg\005\000\000\00015.3"
              "*\007\000\000\000jdadasc\004\000\000\0001E-5\003\000\000\000001\005\000\000\000sddjd\002\000\000\0001"
              "1\004\000\000\000-1.2\003\000\000\000GGG\001\000\000\000A"),
          { { 3, 5, 6, 8, 9 }, { 0, 1, 2, 4, 7, 10, 11 }, 12, {}, is_enforce_byteswap(true) },
          false,
          "AnyDataset: 15.3* is specified as a numerical feature." }, // invalid characters
        { VCR("\012\000\000\00011sdfdfsdf\003\000\000\00078s\007\000\000\000swfgswg\004\000\000\00015."
              "3\007\000\000\000jdadasc\004\000\000\0001E-5\003\000\000\000001\005\000\000\000sddjd\002\000\000\00011"
              "\004\000\000\000-1.2\003\000\000\000GGG\001\000\000\000A"),
          { { 3, 5, 6, 8, 9 }, { 0, 1, 2, 4, 7, 10, 11 }, 12, {}, is_enforce_byteswap(true) },
          true,
          "" }, // OK
        { VCR("\012\000\000\00012httpfsdf\003\000\000\00078s\007\000\000\000swfgswg\004\000\000\00015."
              "3\007\000\000\000jdadasc\004\000\000\0001E-"
              "5\003\000\000\000001\005\000\000\000sddjd\003\000\000\000011\004\000\000\000-1."
              "2\003\000\000\000GGG\001\000\000\000A"),
          { { 3, 5, 6, 8, 9 }, { 0, 1, 2, 4, 7, 10, 11 }, 12, {}, is_enforce_byteswap(true) },
          true,
          "" }, // OK
        { VCR("\012\000\000\00012grpcfsdf\003\000\000\00078s\007\000\000\000swfgswg\004\000\000\00015."
              "3\007\000\000\000jdadasc\004\000\000\0001E-"
              "5\003\000\000\000001\005\000\000\000sddjd\002\000\000\00011\004\000\000\000-1."
              "2\003\000\000\000GGG\001\000\000\000A"),
          { { 3, 5, 6, 8, 9 }, { 0, 1, 2, 4, 7, 10, 11 }, 12, {}, is_enforce_byteswap(true) },
          true,
          "" }, // OK
        { VCR("\012\000\000\00013sdfdfsdf\003\000\000\00078s\007\000\000\000jwfgswg\005\000\000\000 15."
              "3\007\000\000\000jdadasc\004\000\000\0001E-5\003\000\000\000001\005\000\000\000sddjd\002\000\000\00011"
              "\004\000\000\000-1.2\003\000\000\000GGG\001\000\000\000A"),
          { { 3, 5, 6, 8, 9 }, { 0, 1, 2, 4, 7, 10, 11 }, 12, {}, is_enforce_byteswap(true) },
          false,
          "AnyDataset:  15.3 is specified as a numerical feature." }, // invalid characters
        { VCR("\013\000\000\00014sdfdfsdf*\003\000\000\00078s\007\000\000\000swfgswg"
              "\004\000\000\00015.3\007\000\000\000jdadasc\004\000\000\0001E-5\003\000\000\000001\005\000\000\000sddjd"
              "\002\000\000\00011\004\000\000\000-1.2\003\000\000\000GGG\001\000\000\000A"),
          { { 3, 5, 6, 8, 9 }, { 0, 1, 2, 4, 7, 10, 11 }, 12, {}, is_enforce_byteswap(true) },
          false,
          "AnyDataset: Input buffer contains feature with invalid characters, token: 14sdfdfsdf*" }, // invalid
                                                                                                     // characters
        { VCR("\006\000\000\00016http\003\000\000\000cdf"),
          { {}, { 0 }, 1, {}, is_enforce_byteswap(true) },
          true,
          "" }, // OK (two lines)
        { VCR("\006\000\000\00016grpc\003\000\000\000cdf"),
          { {}, { 0 }, 1, {}, is_enforce_byteswap(true) },
          true,
          "" }, // OK (two lines)
        { VCR("\005\000\000\00017cde\002\000\000\00021"),
          { {}, { 0 }, 1, {}, is_enforce_byteswap(true) },
          true,
          "" }, // because of the schema "21" is handles as a numerical feature
        { VCR("\004\000\000\00018.0\004\000\000\0002cde"),
          { { 0, 1 }, {}, 2, {}, is_enforce_byteswap(true) },
          false,
          "AnyDataset: 2cde is specified as a numerical feature." }, // second line does not contain a numerical feature
        { VCR("\004\000\000\00019.0\004\000\000\0002cde"),
          { { 0 }, { 2 }, 2, {}, is_enforce_byteswap(true) },
          false,
          "AnyDataset: 2cde is not categorized in schema." }, // schema is incorrect
        { VCR("\004\000\000\00020.0\004\000\000\0002cde"),
          { { 0, 2 }, { 1, 3 }, 2, {}, is_enforce_byteswap(true) },
          false,
          "AnyDataset: Incorrect data schema." }, // schema is incorrect
    };

    for (TestCase tc : tcs) {
        std::cout << "test: " << std::string(tc.input_buffer.begin(), tc.input_buffer.end()) << std::endl;
        assert(test(tc) == true);
    }

    std::cout << std::endl;
}

void compare_sklearn_func(const std::string input, const std::string function, const std::string expected)
{
    std::stringstream sstr;
    sstr << R"(
import sys
import warnings
# there were numpy warnings like:
# UserWarning: The value of the smallest subnormal for <class 'numpy.float64'> type is zero.
warnings.filterwarnings("ignore")
import numpy as np
from sklearn.preprocessing import FunctionTransformer

if __name__ == '__main__':
    expected = np.array()"
         << expected << R"()
    X = np.array()"
         << input << R"()
    transformer = FunctionTransformer()"
         << function << R"()
    result = np.array(transformer.transform(X))
    if np.allclose(result, expected) == False:
        raise Exception('result ' + str(result) + ' does not match the expected ' + str(expected))
)";
    if (PyRun_SimpleString(sstr.str().c_str())) {
        std::cout << "comparison to scikit-learn failed for FunctionTransformer" << std::endl;
        assert(0);
    } else {
        std::cout << "comparison to scikit-learn succeeded for FunctionTransformer" << std::endl << std::endl;
    }
}

void compare_sklearn_norm(const std::string input, snapml::Normalizer::Params::Norm norm, const std::string expected)
{
    std::string normstr = "";

    if (norm == snapml::Normalizer::Params::Norm::l1)
        normstr = "'l1'";
    else if (norm == snapml::Normalizer::Params::Norm::max)
        normstr = "'max'";

    std::stringstream sstr;
    sstr << R"(
import sys
import warnings
# there were numpy warnings like:
# UserWarning: The value of the smallest subnormal for <class 'numpy.float64'> type is zero.
warnings.filterwarnings("ignore")
import numpy as np
from sklearn.preprocessing import Normalizer

if __name__ == '__main__':
    expected = np.array()"
         << expected << R"()
    X = np.array()"
         << input << R"()
    transformer = Normalizer()"
         << normstr << R"().fit(X)
    result = np.array(transformer.transform(X))
    if np.allclose(result, expected) == False:
        raise Exception('result ' + str(result) + ' does not match the expected ' + str(expected))
)";
    if (PyRun_SimpleString(sstr.str().c_str())) {
        std::cout << "comparison to scikit-learn failed for Normalizer" << std::endl;
        assert(0);
    } else {
        std::cout << "comparison to scikit-learn succeeded for Normalizer" << std::endl << std::endl;
    }
}

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
    vec = X[X.size() - 1];
    sstr << "[";
    for (uint32_t j = 0; j < vec.size() - 1; j++)
        sstr << vec[j] << ", ";
    sstr << vec[vec.size() - 1] << "]]";
    return sstr.str();
}

void compare_sklearn_kbins(const std::string input, uint32_t n_bins, std::vector<std::vector<float>>& bin_edges,
                           const std::string expected)
{
    std::string normstr = "";

    // convert std::vector<std::vector<float>> to Python list
    std::string bin_edges_str = to_string(bin_edges);

    std::stringstream sstr;
    sstr << R"(
import sys
import warnings
# there were numpy warnings like:
# UserWarning: The value of the smallest subnormal for <class 'numpy.float64'> type is zero.
warnings.filterwarnings("ignore")
import numpy as np
from sklearn.preprocessing import KBinsDiscretizer

if __name__ == '__main__':
    n_bins = )"
         << n_bins << R"(
    bin_edges = np.array()"
         << bin_edges_str << R"()
    expected = np.array()"
         << expected << R"()
    X = np.array()"
         << input << R"()
    est = KBinsDiscretizer(encode='ordinal', n_bins=n_bins, strategy='uniform')
    # old, different X: 
    # est.fit(X)
    # # convert to np.array
    # # est.bin_edges_ has a format like the following:
    # # array([array([-2., -1.,  0.,  1.]), array([1., 2., 3., 4.]),
    # #     array([-4., -3., -2., -1.]), array([-1. , -0.5,  0.5,  2. ])],
    # #     dtype=object)
    # B = np.array([r.tolist() for r in est.bin_edges_.tolist()])
    # compare bin_edges since this is the input for snapml.KBinsDiscretizer
    # if np.allclose(B, bin_edges) == False:
    #     raise Exception('There is a difference between the bin_edges provided by snapml and scikit-learn: ' 
    #                     + str(bin_edges.tolist()) + ' vs. ' + str(B.tolist()))
    est.bin_edges_ = bin_edges
    result = np.array(est.transform(X))
    if np.allclose(result, expected) == False:
        raise Exception('result ' + str(result) + ' does not match the expected ' + str(expected))
)";
    if (PyRun_SimpleString(sstr.str().c_str())) {
        std::cout << "comparison to scikit-learn failed for KBinsDiscretizer" << std::endl;
        assert(0);
    } else {
        std::cout << "comparison to scikit-learn succeeded for KBinsDiscretizer" << std::endl << std::endl;
    }
}

void compare_sklearn_ohe(const std::string input, const std::string X, const std::string expected)
{
    std::stringstream sstr;
    sstr << R"(
import sys
import warnings
# there were numpy warnings like:
# UserWarning: The value of the smallest subnormal for <class 'numpy.float64'> type is zero.
warnings.filterwarnings("ignore")
import numpy as np
from sklearn.preprocessing import OneHotEncoder

if __name__ == '__main__':
    expected = np.array()"
         << expected << R"()
    X = )"
         << X << R"(
    enc = OneHotEncoder(handle_unknown='ignore')
    X = np.array(X).transpose()
    enc.fit(X)
    result = enc.transform()"
         << input << R"().toarray()

    if np.allclose(result, expected) == False:
        raise Exception('result ' + str(result) + ' does not match the expected ' + str(expected))
)";
    if (PyRun_SimpleString(sstr.str().c_str())) {
        std::cout << "comparison to scikit-learn failed for OneHotEncoder" << std::endl;
        assert(0);
    } else {
        std::cout << "comparison to scikit-learn succeeded for OneHotEncoder" << std::endl << std::endl;
    }
}

void compare_sklearn_ord(const std::string input, const std::string X, const std::string expected)
{
    std::stringstream sstr;
    sstr << R"(
import sys
import warnings
# there were numpy warnings like:
# UserWarning: The value of the smallest subnormal for <class 'numpy.float64'> type is zero.
warnings.filterwarnings("ignore")
import numpy as np
from sklearn.preprocessing import OrdinalEncoder

if __name__ == '__main__':
    expected = np.array()"
         << expected << R"()
    X = )"
         << X << R"(
    enc = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
    X = np.array(X).transpose()
    enc.fit(X)
    result = enc.transform()"
         << input << R"()

    if np.allclose(result, expected) == False:
        raise Exception('result ' + str(result) + ' does not match the expected ' + str(expected))
)";
    if (PyRun_SimpleString(sstr.str().c_str())) {
        std::cout << "comparison to scikit-learn failed for OrdinalEncoder" << std::endl;
        assert(0);
    } else {
        std::cout << "comparison to scikit-learn succeeded for OrdinalEncoder" << std::endl << std::endl;
    }
}

void compare_sklearn_target(const std::string input, const std::string categories, const std::string encodings,
                            float target_mean, const std::string expected)
{
    std::stringstream sstr;
    sstr << R"(
import sys
import warnings
# there were numpy warnings like:
# UserWarning: The value of the smallest subnormal for <class 'numpy.float64'> type is zero.
warnings.filterwarnings("ignore")
import numpy as np
import sklearn.preprocessing

if 'TargetEncoder' in sklearn.preprocessing.__dict__:
	from sklearn.preprocessing import TargetEncoder
	
	if __name__ == '__main__':
		expected = np.array()"
         << expected << R"()
		categories = )"
         << categories << R"(
		encodings = )"
         << encodings << R"(
		target_mean = )"
         << target_mean << R"(
		input = )"
         << input << R"(
		enc = TargetEncoder()
		input = np.array(input)
		#enc.fit(X)
		enc.encodings_ = np.array(encodings)
		enc.categories_ = np.array(categories)
		enc.target_mean_ = target_mean
		enc._infrequent_enabled = False
		enc.target_type_ = 'auto'
		result = enc.transform(input)
	
		if np.allclose(result, expected) == False:
			raise Exception('result ' + str(result) + ' does not match the expected ' + str(expected))
)";
    if (PyRun_SimpleString(sstr.str().c_str())) {
        std::cout << "comparison to scikit-learn failed for TargetEncoder" << std::endl;
        assert(0);
    } else {
        std::cout << "test succeeded for TargetEncoder" << std::endl << std::endl;
    }
}

std::string encodings_to_json(std::vector<std::map<std::string, float>> X)
{
    std::map<std::string, float> m;
    uint32_t                     j;
    std::stringstream            sstr;
    std::ostringstream           ss;

    sstr << "[";
    for (uint32_t i = 0; i < X.size() - 1; i++) {
        sstr << "[";
        m = X[i];
        std::vector<std::string> vec;
        for (std::pair<std::string, float> p : m) {
            ss << p.second;
            vec.push_back(ss.str());
            ss.str("");
        }
        for (j = 0; j < vec.size() - 1; j++)
            sstr << "'" << vec[j] << "', ";
        sstr << "'" << vec[j] << "'], ";
    }
    sstr << "[";
    m = X[X.size() - 1];
    std::vector<std::string> vec;
    for (std::pair<std::string, float> p : m) {
        ss << p.second;
        vec.push_back(ss.str());
        ss.str("");
    }
    for (j = 0; j < vec.size() - 1; j++)
        sstr << "'" << vec[j] << "', ";
    sstr << "'" << vec[j] << "']]";

    return sstr.str();
}

template <typename T> std::string categories_to_json(std::vector<std::map<std::string, T>> X)
{
    std::map<std::string, T> m;
    uint32_t                 j;
    std::stringstream        sstr;
    sstr << "[";
    for (uint32_t i = 0; i < X.size() - 1; i++) {
        sstr << "[";
        m = X[i];
        std::vector<std::string> vec;
        for (std::pair<std::string, T> p : m)
            vec.push_back(p.first);
        for (j = 0; j < vec.size() - 1; j++)
            sstr << "'" << vec[j] << "', ";
        sstr << "'" << vec[j] << "'], ";
    }
    sstr << "[";
    m = X[X.size() - 1];
    std::vector<std::string> vec;
    for (std::pair<std::string, T> p : m)
        vec.push_back(p.first);
    for (j = 0; j < vec.size() - 1; j++)
        sstr << "'" << vec[j] << "', ";
    sstr << "'" << vec[j] << "']]";

    return sstr.str();
}

void test_transformer()
{
    std::string expected = "";

    try {
        std::cout << "FunctionTransformer: Testing logarithm of base 2." << std::endl;
        AnyDatasetTest ad(VCR("\001\000\000\0002\001\000\000\0004\001\000\000\0008\002\000\000\0001"
                              "6\001\000\000\0004\001\000\000\0008\002\000\000\00016\002\000\000\00032"),
                          { { 0, 1, 2, 3 }, {}, 4, {}, is_enforce_byteswap(true) });
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::FunctionTransformer::Params p2;
        p2.func = [](float x) { return std::log2(x); };
        snapml::FunctionTransformer t2(p2);
        t2.transform(ad);
        std::cout << ad.get_numerical_features() << std::endl;
        expected = "[[1, 2, 3, 4], [2, 3, 4, 5]]";
        if (ad.get_numerical_features() != expected)
            throw std::runtime_error(ad.get_numerical_features() + " != " + expected);
        if (ad.get_num_ex() != 2)
            throw std::runtime_error(std::to_string(ad.get_num_ex()) + " != 2");
        compare_sklearn_func("[[2,4,8,16],[4,8,16,32]]", "np.log2", expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        AnyDatasetTest ad(VCR("\001\000\000\0001\001\000\000\0004\001\000\000\0005"
                              "\001\000\000\0002\001\000\000\0006\001\000\000\0002"
                              "\004\000\000\000-3.5\002\000\000\000-1\003\000\000\0000.5"),
                          { { 0, 1, 2 }, {}, 3, {}, is_enforce_byteswap(true) });
        std::cout << "Normalizer: Testing normalization with L1-norm." << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::Normalizer::Params p;
        p.norm = snapml::Normalizer::Params::Norm::l1;
        snapml::Normalizer t(p);
        t.transform(ad);
        std::cout << ad.get_numerical_features() << std::endl;
        expected = "[[0.1, 0.4, 0.5], [0.2, 0.6, 0.2], [-0.7, -0.2, 0.1]]";
        if (ad.get_numerical_features() != expected)
            throw std::runtime_error(ad.get_numerical_features() + " != " + expected);
        if (ad.get_num_ex() != 3)
            throw std::runtime_error(std::to_string(ad.get_num_ex()) + " != 3");
        compare_sklearn_norm("[[1,4,5],[2,6,2],[-3.5,-1,0.5]]", p.norm, expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        AnyDatasetTest ad(VCR("\001\000\000\0001\001\000\000\0004\001\000\000\0005\001\000\000\0002\001\000\000"
                              "\0006\001\000\000\0002\004\000\000\000-3.5\002\000\000\000-1\003\000\000\0000.5"),
                          { { 0, 1, 2 }, {}, 3, {}, is_enforce_byteswap(true) });
        std::cout << "Normalizer: Testing normalization with L1-norm, http input." << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::Normalizer::Params p;
        p.norm = snapml::Normalizer::Params::Norm::l1;
        snapml::Normalizer t(p);
        t.transform(ad);
        std::cout << ad.get_numerical_features() << std::endl;
        expected = "[[0.1, 0.4, 0.5], [0.2, 0.6, 0.2], [-0.7, -0.2, 0.1]]";
        if (ad.get_numerical_features() != expected)
            throw std::runtime_error(ad.get_numerical_features() + " != " + expected);
        compare_sklearn_norm("[[1,4,5],[2,6,2],[-3.5,-1,0.5]]", p.norm, expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        AnyDatasetTest ad(VCR("\001\000\000\0001\001\000\000\0004\001\000\000\0005\001\000\000\0002\001\000\000"
                              "\0006\001\000\000\0002\004\000\000\000-3.5\002\000\000\000-1\003\000\000\0000.5"),
                          { { 0, 1, 2 }, {}, 3, {}, is_enforce_byteswap(true) });
        std::cout << "Normalizer: Testing normalization with L1-norm, gRPC input." << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::Normalizer::Params p;
        p.norm = snapml::Normalizer::Params::Norm::l1;
        snapml::Normalizer t(p);
        t.transform(ad);
        std::cout << ad.get_numerical_features() << std::endl;
        expected = "[[0.1, 0.4, 0.5], [0.2, 0.6, 0.2], [-0.7, -0.2, 0.1]]";
        if (ad.get_numerical_features() != expected)
            throw std::runtime_error(ad.get_numerical_features() + " != " + expected);
        compare_sklearn_norm("[[1,4,5],[2,6,2],[-3.5,-1,0.5]]", p.norm, expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        AnyDatasetTest ad(VCR("\002\000\000\00010\002\000\000\000-4\001\000\000\0005"
                              "\001\000\000\0006\003\000\000\000-10\001\000\000\0003"
                              "\004\000\000\000-2.7\005\000\000\000-10.8\003\000\000\0005.4"),
                          { { 0, 1, 2 }, {}, 3, {}, is_enforce_byteswap(true) });
        std::cout << "Normalizer: Testing normalization with L∞-norm." << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::Normalizer::Params p;
        p.norm = snapml::Normalizer::Params::Norm::max;
        snapml::Normalizer t(p);
        t.transform(ad);
        std::cout << ad.get_numerical_features() << std::endl;
        expected = "[[1, -0.4, 0.5], [0.6, -1, 0.3], [-0.25, -1, 0.5]]";
        if (ad.get_numerical_features() != expected)
            throw std::runtime_error(ad.get_numerical_features() + " != " + expected);
        compare_sklearn_norm("[[10,-4,5],[6,-10,3],[-2.7,-10.8,5.4]]", p.norm, expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        AnyDatasetTest ad(VCR("\002\000\000\00010\002\000\000\000-4\001\000\000\0005"
                              "\001\000\000\0006\003\000\000\000-10\001\000\000\0003"
                              "\004\000\000\000-2.7\005\000\000\000-10.8\003\000\000\0005.4"),
                          { { 0, 1, 2 }, {}, 3, {}, is_enforce_byteswap(true) });
        std::cout << "Normalizer: Testing normalization with L∞-norm, http input." << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::Normalizer::Params p;
        p.norm = snapml::Normalizer::Params::Norm::max;
        snapml::Normalizer t(p);
        t.transform(ad);
        std::cout << ad.get_numerical_features() << std::endl;
        expected = "[[1, -0.4, 0.5], [0.6, -1, 0.3], [-0.25, -1, 0.5]]";
        if (ad.get_numerical_features() != expected)
            throw std::runtime_error(ad.get_numerical_features() + " != " + expected);
        compare_sklearn_norm("[[10,-4,5],[6,-10,3],[-2.7,-10.8,5.4]]", p.norm, expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        AnyDatasetTest ad(VCR("\002\000\000\00010\002\000\000\000-4\001\000\000\0005"
                              "\001\000\000\0006\003\000\000\000-10\001\000\000\0003"
                              "\004\000\000\000-2.7\005\000\000\000-10.8\003\000\000\0005.4"),
                          { { 0, 1, 2 }, {}, 3, {}, is_enforce_byteswap(true) });
        std::cout << "Normalizer: Testing normalization with L∞-norm, gRPC input." << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::Normalizer::Params p;
        p.norm = snapml::Normalizer::Params::Norm::max;
        snapml::Normalizer t(p);
        t.transform(ad);
        std::cout << ad.get_numerical_features() << std::endl;
        expected = "[[1, -0.4, 0.5], [0.6, -1, 0.3], [-0.25, -1, 0.5]]";
        if (ad.get_numerical_features() != expected)
            throw std::runtime_error(ad.get_numerical_features() + " != " + expected);
        compare_sklearn_norm("[[10,-4,5],[6,-10,3],[-2.7,-10.8,5.4]]", p.norm, expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    // use ad1 for the next three tests
    AnyDatasetTest ad1(
        VCR("\003\000\000\0001.5\003\000\000\0003.0\003\000\000\0007"
            ".5\003\000\000\0003.5\003\000\000\0004.5\003\000\000\0002.5\003\000\000\0003.5\003\000\000\0006.5"
            "\003\000\000\0005.5\003\000\000\0003.0"),
        { { 0, 1, 2, 3, 4 }, {}, 5, {}, is_enforce_byteswap(true) });

    try {
        std::cout << "Normalizer: Testing normalization." << std::endl;
        ;
        std::cout << ad1.get_numerical_features() << " ⮕ ";
        snapml::Normalizer::Params p1;
        snapml::Normalizer         t1(p1);
        t1.transform(ad1);
        std::cout << ad1.get_numerical_features() << std::endl;
        expected = "[[0.15, 0.3, 0.75, 0.35, 0.45], [0.25, 0.35, 0.65, 0.55, 0.3]]";
        if (ad1.get_numerical_features() != expected)
            throw std::runtime_error(ad1.get_numerical_features() + " != " + expected);
        compare_sklearn_norm("[[1.5,3.0,7.5,3.5,4.5],[2.5,3.5,6.5,5.5,3.0]]", p1.norm, expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        std::cout << "FunctionTransformer: Testing the default identity function." << std::endl;
        std::cout << ad1.get_numerical_features() << " ⮕ ";
        snapml::FunctionTransformer::Params p2;
        snapml::FunctionTransformer         t2(p2);
        t2.transform(ad1);
        std::cout << ad1.get_numerical_features() << std::endl;
        expected = "[[0.15, 0.3, 0.75, 0.35, 0.45], [0.25, 0.35, 0.65, 0.55, 0.3]]";
        if (ad1.get_numerical_features() != expected)
            throw std::runtime_error(ad1.get_numerical_features() + " != " + expected);
        compare_sklearn_func("[[0.15, 0.3, 0.75, 0.35, 0.45], [0.25, 0.35, 0.65, 0.55, 0.3]]", "", expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        std::cout << "FunctionTransformer: Testing two times incrementing by one." << std::endl;
        std::cout << ad1.get_numerical_features() << " ⮕ ";
        snapml::FunctionTransformer::Params p3;
        p3.func = [](float x) { return x + 1; };
        snapml::FunctionTransformer t3(p3);
        t3.transform(ad1);
        std::cout << ad1.get_numerical_features() << " ⮕ ";
        expected = "[[1.15, 1.3, 1.75, 1.35, 1.45], [1.25, 1.35, 1.65, 1.55, 1.3]]";
        if (ad1.get_numerical_features() != expected)
            throw std::runtime_error(ad1.get_numerical_features() + " != " + expected);
        t3.transform(ad1);
        std::cout << ad1.get_numerical_features() << std::endl;
        expected = "[[2.15, 2.3, 2.75, 2.35, 2.45], [2.25, 2.35, 2.65, 2.55, 2.3]]";
        if (ad1.get_numerical_features() != expected)
            throw std::runtime_error(ad1.get_numerical_features() + " != " + expected);
        compare_sklearn_func("[[0.15, 0.3, 0.75, 0.35, 0.45], [0.25, 0.35, 0.65, 0.55, 0.3]]",
                             "lambda X: np.array(X)+2", expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        AnyDatasetTest ad(
            VCR("\001\000\000\0001\001\000\000\0001\001\000\000\0001\001\000\000\0001\001\000\000\0002"
                "\001\000\000\0002\001\000\000\0002\001\000\000\0002\001\000\000\0003\001\000\000\0003\001\000\000\0003"
                "\001\000\000\0003"),
            { { 0, 1, 2, 3 }, {}, 4, {}, is_enforce_byteswap(true) });
        std::cout << "FunctionTransformer: Testing an index list that applies to all." << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::FunctionTransformer::Params p;
        p.func       = [](float x) { return x + 1; };
        p.index_list = { 0, 1, 2, 3 };
        snapml::FunctionTransformer t(p);
        t.transform(ad);
        std::cout << ad.get_numerical_features() << std::endl;
        expected = "[[2, 2, 2, 2], [3, 3, 3, 3], [4, 4, 4, 4]]";
        if (ad.get_numerical_features() != expected)
            throw std::runtime_error(ad.get_numerical_features() + " != " + expected);
        compare_sklearn_func("[[1, 1, 1, 1], [2, 2, 2, 2], [3, 3, 3, 3]]", "lambda X: np.array(X)+1", expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        AnyDatasetTest ad(VCR("\001\000\000\0001\001\000\000\0001\001\000\000\0001\001\000\000\0001\001\000\000\0002"
                              "\001\000\000\0002\001\000\000\0002\001\000\000\0002\001\000\000\0003\001\000\000\0003"
                              "\001\000\000\0003\001\000\000\0003"),
                          { { 0, 1, 2, 3 }, {}, 4, {}, is_enforce_byteswap(true) });
        std::cout << "FunctionTransformer: Testing an index list that applies to 1 and 3." << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::FunctionTransformer::Params p;
        p.func       = [](float x) { return x + 1; };
        p.index_list = { 1, 3 };
        snapml::FunctionTransformer t(p);
        t.transform(ad);
        std::cout << ad.get_numerical_features() << std::endl;
        expected = "[[1, 2, 1, 2], [2, 3, 2, 3], [3, 4, 3, 4]]";
        if (ad.get_numerical_features() != expected)
            throw std::runtime_error(ad.get_numerical_features() + " != " + expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        AnyDatasetTest ad(VCR("\001\000\000\0001\001\000\000\0001\001\000\000\0001\001\000\000\0001\001\000\000"
                              "\0002\001\000\000\0002\001\000\000\0002\001\000\000\0002\001\000\000\0003\001\000"
                              "\000\0003\001\000\000\0003\001\000\000\0003"),
                          { { 0, 1, 2, 3 }, {}, 4, {}, is_enforce_byteswap(true) });
        std::cout << "FunctionTransformer: Testing an index list that applies to 1 and 3, http input." << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::FunctionTransformer::Params p;
        p.func       = [](float x) { return x + 1; };
        p.index_list = { 1, 3 };
        snapml::FunctionTransformer t(p);
        t.transform(ad);
        std::cout << ad.get_numerical_features() << std::endl;
        expected = "[[1, 2, 1, 2], [2, 3, 2, 3], [3, 4, 3, 4]]";
        if (ad.get_numerical_features() != expected)
            throw std::runtime_error(ad.get_numerical_features() + " != " + expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        AnyDatasetTest ad(VCR("\001\000\000\0001\001\000\000\0001\001\000\000\0001\001\000\000\0001\001\000\000"
                              "\0002\001\000\000\0002\001\000\000\0002\001\000\000\0002\001\000\000\0003\001\000"
                              "\000\0003\001\000\000\0003\001\000\000\0003"),
                          { { 0, 1, 2, 3 }, {}, 4, {}, is_enforce_byteswap(true) });
        std::cout << "FunctionTransformer: Testing an index list that applies to 1 and 3, gRPC input." << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::FunctionTransformer::Params p;
        p.func       = [](float x) { return x + 1; };
        p.index_list = { 1, 3 };
        snapml::FunctionTransformer t(p);
        t.transform(ad);
        std::cout << ad.get_numerical_features() << std::endl;
        expected = "[[1, 2, 1, 2], [2, 3, 2, 3], [3, 4, 3, 4]]";
        if (ad.get_numerical_features() != expected)
            throw std::runtime_error(ad.get_numerical_features() + " != " + expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        AnyDatasetTest ad(VCR("\001\000\000\0001\001\000\000\0001\001\000\000\0001\001\000\000\0001\001\000\000\0002"
                              "\001\000\000\0002\001\000\000\0002\001\000\000\0002\001\000\000\0003\001\000\000\0003"
                              "\001\000\000\0003\001\000\000\0003"),
                          { { 0, 1, 2, 3 }, {}, 4, {}, is_enforce_byteswap(true) });
        std::cout << "FunctionTransformer: Testing an index list containing a wrong value." << std::endl;
        snapml::FunctionTransformer::Params p;
        p.func       = [](float x) { return x + 1; };
        p.index_list = { 1, 4 };
        snapml::FunctionTransformer t(p);
        t.transform(ad);
        std::cout << "Test was expected to generate an error.";
        assert(0);
    } catch (const std::exception& e) {
        if (std::string(e.what()).compare("unable to find index 4.")) {
            std::cout << "Test failed with message '" << e.what()
                      << "', but was expected to fail with message: 'unable to find index 4.'" << std::endl;
            assert(0);
        } else {
            std::cout << "Test succeeded with message encodings_to_json(categories_3)'" << e.what() << "'" << std::endl
                      << std::endl;
        }
    }

    try {
        AnyDatasetTest ad(
            VCR("\001\000\000\0001\001\000\000\0001\001\000\000\0001\001\000\000\0001\001\000\000\0002"
                "\001\000\000\0002\001\000\000\0002\001\000\000\0002\001\000\000\0003\001\000\000\0003\001\000\000\0003"
                "\001\000\000\0003"),
            { { 0, 1, 2, 3 }, {}, 4, {}, is_enforce_byteswap(true) });
        std::cout << "FunctionTransformer: Testing an index list containing too many values." << std::endl;
        snapml::FunctionTransformer::Params p;
        p.func       = [](float x) { return x + 1; };
        p.index_list = { 0, 1, 2, 3, 4, 5, 6, 7 };
        snapml::FunctionTransformer t(p);
        t.transform(ad);
        std::cout << "Test was expected to generate an error.";
        assert(0);
    } catch (const std::exception& e) {
        if (std::string(e.what()).compare("unable to find index 4.")) {
            std::cout << "Test failed with message '" << e.what()
                      << "', but was expected to fail with message: 'unable to find index 4.'" << std::endl;
            assert(0);
        } else {
            std::cout << "Test succeeded with message '" << e.what() << "'" << std::endl << std::endl;
        }
    }

    try {
        AnyDatasetTest ad(VCR("\001\000\000\0001\001\000\000\000a\001\000\000\0004\001\000\000\0005\001\000\000\0002"
                              "\001\000\000\000b\001\000\000\0006\001\000\000\0002\004\000\000\000-3."
                              "5\001\000\000\000c\002\000\000\000-1\003\000\000\0000.5"),
                          { { 0, 2, 3 }, { 1 }, 4, {}, is_enforce_byteswap(true) });
        std::cout << "Normalizer: One additional categorical feature included." << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::Normalizer::Params p;
        p.norm = snapml::Normalizer::Params::Norm::l1;
        snapml::Normalizer t(p);
        t.transform(ad);
        std::cout << ad.get_numerical_features() << std::endl;
        expected = "[[0.1, 0.4, 0.5], [0.2, 0.6, 0.2], [-0.7, -0.2, 0.1]]";
        if (ad.get_numerical_features() != expected)
            throw std::runtime_error(ad.get_numerical_features() + " != " + expected);
        compare_sklearn_norm("[[1,4,5],[2,6,2],[-3.5,-1,0.5]]", p.norm, expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        AnyDatasetTest ad(VCR("\001\000\000\0001\001\000\000\000a\001\000\000\0004\001\000\000\0005\001\000\000\0002"
                              "\001\000\000\000b\001\000\000\0006\001\000\000\0002\004\000\000\000-3."
                              "5\001\000\000\000c\002\000\000\000-1"
                              "\003\000\000\0000.5"),
                          { { 0, 2, 3 }, { 1 }, 4, {}, is_enforce_byteswap(true) });
        std::cout << "Normalizer: Categorical feature in index list" << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::Normalizer::Params p;
        p.norm       = snapml::Normalizer::Params::Norm::l1;
        p.index_list = { 0, 1, 2, 3 };
        snapml::Normalizer t(p);
        t.transform(ad);
        std::cout << ad.get_numerical_features() << std::endl;
        expected = "[[0.1, 0.4, 0.5], [0.2, 0.6, 0.2], [-0.7, -0.2, 0.1]]";
        if (ad.get_numerical_features() != expected)
            throw std::runtime_error(ad.get_numerical_features() + " != " + expected);
        if (ad.get_num_ex() != 3)
            throw std::runtime_error(std::to_string(ad.get_num_ex()) + " != 3");
        compare_sklearn_norm("[[1,4,5],[2,6,2],[-3.5,-1,0.5]]", p.norm, expected);
    } catch (const std::exception& e) {
        if (std::string(e.what()).compare("Normalizer: categorical index specified")) {
            std::cout << "Test failed with message '" << e.what()
                      << "', but was expected to fail with message: 'Normalizer: categorical index specified'"
                      << std::endl;
            assert(0);
        } else {
            std::cout << "Test succeeded with message '" << e.what() << "'" << std::endl << std::endl;
        }
    }

    try {
        AnyDatasetTest ad(VCR("\001\000\000\0001\001\000\000\000a\001\000\000\0004\001\000\000\0005\001\000\000\0002"
                              "\001\000\000\000b\001\000\000\0006\001\000\000\0002\004\000\000\000-3."
                              "5\001\000\000\000c\002\000\000\000-1"
                              "\003\000\000\0000.5"),
                          { { 0, 2, 3 }, { 1 }, 4, {}, is_enforce_byteswap(true) });
        std::cout << "Normalizer: One additional categorical feature included, index list unordered." << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::Normalizer::Params p;
        p.norm       = snapml::Normalizer::Params::Norm::l1;
        p.index_list = { 0, 2, 3 };
        snapml::Normalizer t(p);
        t.transform(ad);
        std::cout << ad.get_numerical_features() << std::endl;
        expected = "[[0.1, 0.4, 0.5], [0.2, 0.6, 0.2], [-0.7, -0.2, 0.1]]";
        if (ad.get_numerical_features() != expected)
            throw std::runtime_error(ad.get_numerical_features() + " != " + expected);
        compare_sklearn_norm("[[1,4,5],[2,6,2],[-3.5,-1,0.5]]", p.norm, expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        AnyDatasetTest ad(VCR("\001\000\000\0001\001\000\000\0009\001\000\000\0005\001\000\000\0005"
                              "\001\000\000\0007\001\000\000\0004\001\000\000\0009\001\000\000\0002"
                              "\001\000\000\0004\001\000\000\0008\001\000\000\0001"
                              "\001\000\000\0009\001\000\000\0007\001\000\000\0007\001\000\000\0001"),
                          { { 0, 1, 2, 3, 4 }, {}, 5, {}, is_enforce_byteswap(true) });
        std::cout << "Normalizer: Testing an index list that applies to 0, 2, 3, and 4." << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::Normalizer::Params p;
        p.index_list = { 0, 2, 3, 4 };
        snapml::Normalizer t(p);
        t.transform(ad);
        std::cout << ad.get_numerical_features() << std::endl;
        expected = "[[0.1, 9, 0.5, 0.5, 0.7], [0.4, 9, 0.2, 0.4, 0.8], [0.1, 9, 0.7, 0.7, 0.1]]";
        if (ad.get_numerical_features() != expected)
            throw std::runtime_error(ad.get_numerical_features() + " != " + expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    std::cout << std::endl;

    try {
        AnyDatasetTest ad(
            VCR("\001\000\000\0001\001\000\000\0009\001\000\000\0005\001\000\000\0005\001\000\000\0007\001\000\000"
                "\0004\001\000\000\0009\001\000\000\0002\001\000\000\0004\001\000\000\0008\001\000\000\0001\001\000"
                "\000\0009\001\000\000\0007\001\000\000\0007\001\000\000\0001"),
            { { 0, 1, 2, 3, 4 }, {}, 5, {}, is_enforce_byteswap(true) });
        std::cout << "Normalizer: Testing an index list that applies to 0, 2, 3, and 4, http input." << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::Normalizer::Params p;
        p.index_list = { 0, 2, 3, 4 };
        snapml::Normalizer t(p);
        t.transform(ad);
        std::cout << ad.get_numerical_features() << std::endl;
        expected = "[[0.1, 9, 0.5, 0.5, 0.7], [0.4, 9, 0.2, 0.4, 0.8], [0.1, 9, 0.7, 0.7, 0.1]]";
        if (ad.get_numerical_features() != expected)
            throw std::runtime_error(ad.get_numerical_features() + " != " + expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        AnyDatasetTest ad(
            VCR("\001\000\000\0001\001\000\000\0009\001\000\000\0005\001\000\000\0005\001\000\000\0007\001\000\000"
                "\0004\001\000\000\0009\001\000\000\0002\001\000\000\0004\001\000\000\0008\001\000\000\0001\001\000"
                "\000\0009\001\000\000\0007\001\000\000\0007\001\000\000\0001"),
            { { 0, 1, 2, 3, 4 }, {}, 5, {}, is_enforce_byteswap(true) });
        std::cout << "Normalizer: Testing an index list that applies to 0, 2, 3, and 4, gRPC input." << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::Normalizer::Params p;
        p.index_list = { 0, 2, 3, 4 };
        snapml::Normalizer t(p);
        t.transform(ad);
        std::cout << ad.get_numerical_features() << std::endl;
        expected = "[[0.1, 9, 0.5, 0.5, 0.7], [0.4, 9, 0.2, 0.4, 0.8], [0.1, 9, 0.7, 0.7, 0.1]]";
        if (ad.get_numerical_features() != expected)
            throw std::runtime_error(ad.get_numerical_features() + " != " + expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    std::cout << std::endl;

    try {
        AnyDatasetTest ad(
            VCR("\002\000\000\000-4\002\000\000\000-4\002\000\000\000-4\002\000\000\000-4\002\000\000\000-3"
                "\002\000\000\000-3\002\000\000\000-3\002\000\000\000-3\002\000\000\000-2\002\000\000\000-"
                "2\002\000\000\000-2\002\000\000\000-2\001\000\000\0000"
                "\001\000\000\0000\001\000\000\0000\001\000\000\0000\001\000\000\0001\001\000\000\0001\001\000\000\0001"
                "\001\000\000\0001"),
            { { 0, 1, 2, 3 }, {}, 4, {}, is_enforce_byteswap(true) });
        std::cout << "KBinsDiscretizer:" << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::KBinsDiscretizer::Params p;
        p.n_bins    = 3;
        p.bin_edges = { { -2, -1, 0, 1 }, { 1, 2, 3, 4 }, { -4, -3, -2, -1 }, { -1, -0.5, 0.5, 2 } };
        snapml::KBinsDiscretizer t(p);
        t.transform(ad);
        std::cout << ad.get_numerical_features() << std::endl;
        expected = "[[0, 0, 0, 0], [0, 0, 1, 0], [0, 0, 2, 0], [2, 0, 2, 1], [2, 0, 2, 2]]";
        if (ad.get_numerical_features() != expected)
            throw std::runtime_error(ad.get_numerical_features() + " != " + expected);
        compare_sklearn_kbins("[[-4,-4,-4,-4],[-3,-3,-3,-3],[-2,-2,-2,-2],[0,0,0,0],[1,1,1,1]]", p.n_bins, p.bin_edges,
                              expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    std::cout << std::endl;

    try {
        AnyDatasetTest ad(
            VCR("\002\000\000\000-4\002\000\000\000-4\002\000\000\000-4\002\000\000\000-4\002\000\000\000-3"
                "\002\000\000\000-3\002\000\000\000-3\002\000\000\000-3\002\000\000\000-2\002\000\000\000-"
                "2\002\000\000\000-2\002\000\000\000-2\001\000\000\0000"
                "\001\000\000\0000\001\000\000\0000\001\000\000\0000\001\000\000\0001\001\000\000\0001\001\000\000\0001"
                "\001\000\000\0001"),
            { { 0, 1, 2, 3 }, {}, 4, {}, is_enforce_byteswap(true) });
        std::cout << "KBinsDiscretizer: test to small bins" << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::KBinsDiscretizer::Params p;
        p.n_bins    = 3;
        p.bin_edges = { { -2 }, { -1 }, { 0 }, { 1 } };
        snapml::KBinsDiscretizer t(p);
        std::cout << "Test was expected to generate an error.";
        assert(0);
    } catch (const std::exception& e) {
        if (std::string(e.what()).compare("The number of bins is  not valid.")) {
            std::cout << "Test failed with message '" << e.what()
                      << "', but was expected to fail with message: 'The number of bins is  not valid.'" << std::endl;
            assert(0);
        } else {
            std::cout << "Test succeeded with message '" << e.what() << "'" << std::endl << std::endl;
        }
    }

    std::cout << std::endl;

    try {
        AnyDatasetTest ad(
            VCR("\002\000\000\000-4\002\000\000\000-4\002\000\000\000-4\002\000\000\000-4\002\000\000\000-3"
                "\002\000\000\000-3\002\000\000\000-3\002\000\000\000-3\002\000\000\000-2\002\000\000\000-"
                "2\002\000\000\000-2\002\000\000\000-2\001\000\000\0000"
                "\001\000\000\0000\001\000\000\0000\001\000\000\0000\001\000\000\0001\001\000\000\0001\001\000\000\0001"
                "\001\000\000\0001"),
            { { 0, 1, 2, 3 }, {}, 4, {}, is_enforce_byteswap(true) });
        std::cout << "KBinsDiscretizer: test to small bin_edges" << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::KBinsDiscretizer::Params p;
        p.n_bins    = 3;
        p.bin_edges = { { -2, -1, 0, 1 }, { 1, 2, 3, 4 }, { -4, -3, -2, -1 } };
        snapml::KBinsDiscretizer t(p);
        t.transform(ad);
        std::cout << "Test was expected to generate an error.";
        assert(0);
    } catch (const std::exception& e) {
        if (std::string(e.what()).compare("The number of bin_edges does not correspond to the input data: 4 vs. 3.")) {
            std::cout << "Test failed with message '" << e.what()
                      << "', but was expected to fail with message: 'The number of bin_edges does not correspond to "
                         "the input data: 4 vs. 3.'"
                      << std::endl;
            assert(0);
        } else {
            std::cout << "Test succeeded with message '" << e.what() << "'" << std::endl << std::endl;
        }
    }

    std::cout << std::endl;

    try {
        AnyDatasetTest ad(
            VCR("\002\000\000\000-4\002\000\000\000-4\002\000\000\000-4\002\000\000\000-4\002\000\000\000-3"
                "\002\000\000\000-3\002\000\000\000-3\002\000\000\000-3\002\000\000\000-2\002\000\000\000-"
                "2\002\000\000\000-2\002\000\000\000-2"
                "\001\000\000\0000\001\000\000\0000\001\000\000\0000\001\000\000\0000\001\000\000\0001\001\000\000\0001"
                "\001\000\000"
                "\0001\001\000\000\0001"),
            { { 0, 1, 2, 3 }, {}, 4, {}, is_enforce_byteswap(true) });
        std::cout << "KBinsDiscretizer: columns 0,2, and 3" << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::KBinsDiscretizer::Params p;
        p.n_bins     = 3;
        p.bin_edges  = { { -2, -1, 0, 1 }, { -4, -3, -2, -1 }, { -1, -0.5, 0.5, 2 } };
        p.index_list = { 0, 2, 3 };
        snapml::KBinsDiscretizer t(p);
        t.transform(ad);
        std::cout << ad.get_numerical_features() << std::endl;
        expected = "[[0, -4, 0, 0], [0, -3, 1, 0], [0, -2, 2, 0], [2, 0, 2, 1], [2, 1, 2, 2]]";
        if (ad.get_numerical_features() != expected)
            throw std::runtime_error(ad.get_numerical_features() + " != " + expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    std::cout << std::endl;

    try {
        AnyDatasetTest ad(VCR("\002\000\000\000-4\002\000\000\000-4\002\000\000\000-4\002\000\000\000-4\002\000\000\000"
                              "-3\002\000\000\000-3\002\000\000\000-3\002\000\000\000-3\002\000\000\000-"
                              "2\002\000\000\000-2\002\000\000\000-2"
                              "\002\000\000\000-"
                              "2\001\000\000\0000\001\000\000\0000\001\000\000\0000\001\000\000\0000\001\000\000\0001"
                              "\001\000\000\0001\001\000\000\0001"
                              "\001\000\000\0001"),
                          { { 0, 1, 2, 3 }, {}, 4, {}, is_enforce_byteswap(true) });
        std::cout << "KBinsDiscretizer: columns 0,1, and 2" << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::KBinsDiscretizer::Params p;
        p.n_bins     = 3;
        p.bin_edges  = { { -2, -1, 0, 1 }, { 1, 2, 3, 4 }, { -4, -3, -2, -1 } };
        p.index_list = { 0, 1, 2 };
        snapml::KBinsDiscretizer t(p);
        t.transform(ad);
        std::cout << ad.get_numerical_features() << std::endl;
        expected = "[[0, 0, 0, -4], [0, 0, 1, -3], [0, 0, 2, -2], [2, 0, 2, 0], [2, 0, 2, 1]]";
        if (ad.get_numerical_features() != expected)
            throw std::runtime_error(ad.get_numerical_features() + " != " + expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    std::cout << std::endl;

    try {
        AnyDatasetTest ad(
            VCR("\002\000\000\000-4\002\000\000\000-4\002\000\000\000-4\002\000\000\000-4"
                "\002\000\000\000-3\002\000\000\000-3\002\000\000\000-3\002\000\000\000-3\002\000\000\000-2"
                "\002\000\000\000-2\002\000\000\000-2\002\000\000\000-2\001\000\000\0000\001\000\000\0000"
                "\001\000\000\0000\001\000\000\0000\001\000\000\0001\001\000\000\0001"
                "\001\000\000\0001\001\000\000\0001"),
            { { 0, 1, 2, 3 }, {}, 4, {}, is_enforce_byteswap(true) });
        std::cout << "KBinsDiscretizer: columns 1,2, and 3" << std::endl;
        std::cout << ad.get_numerical_features() << " ⮕ ";
        snapml::KBinsDiscretizer::Params p;
        p.n_bins     = 3;
        p.bin_edges  = { { 1, 2, 3, 4 }, { -4, -3, -2, -1 }, { -1, -0.5, 0.5, 2 } };
        p.index_list = { 1, 2, 3 };
        snapml::KBinsDiscretizer t(p);
        t.transform(ad);
        std::cout << ad.get_numerical_features() << std::endl;
        expected = "[[-4, 0, 0, 0], [-3, 0, 1, 0], [-2, 0, 2, 0], [0, 0, 2, 1], [1, 0, 2, 2]]";
        if (ad.get_numerical_features() != expected)
            throw std::runtime_error(ad.get_numerical_features() + " != " + expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    std::cout << std::endl;

    std::vector<std::map<std::string, int>> categories_1
        = { { { "abrm", 0 },  { "ceut", 1 },  { "eemq", 2 },  { "efzn", 3 },  { "ffph", 4 },  { "flou", 5 },
              { "fxwy", 6 },  { "geqh", 7 },  { "gjgr", 8 },  { "guxq", 9 },  { "ibxq", 10 }, { "ickf", 11 },
              { "mvlr", 12 }, { "oahc", 13 }, { "plnb", 14 }, { "pndb", 15 }, { "poef", 16 }, { "sncr", 17 },
              { "sote", 18 }, { "svwn", 19 }, { "taga", 20 }, { "tmcs", 21 }, { "uipy", 22 }, { "vebx", 23 },
              { "vgcv", 24 }, { "vqwf", 25 }, { "vymq", 26 }, { "xdyf", 27 }, { "zhqv", 28 }, { "zwnz", 29 } },
            { { "afvm", 0 },  { "astw", 1 },  { "bjyi", 2 },  { "cmbe", 3 },  { "cwxh", 4 },  { "ezee", 5 },
              { "fwji", 6 },  { "ghrk", 7 },  { "hwle", 8 },  { "icph", 9 },  { "igec", 10 }, { "kllj", 11 },
              { "kugl", 12 }, { "lznv", 13 }, { "obfr", 14 }, { "piud", 15 }, { "pogc", 16 }, { "qbwd", 17 },
              { "qedx", 18 }, { "qfak", 19 }, { "qhgd", 20 }, { "tali", 21 }, { "ukod", 22 }, { "vaej", 23 },
              { "vrpu", 24 }, { "wbkx", 25 }, { "wxit", 26 }, { "xtmq", 27 }, { "ycvz", 28 }, { "yyib", 29 } },
            { { "bcqe", 0 },  { "cjsj", 1 },  { "cwpp", 2 },  { "dvxp", 3 },  { "dzkn", 4 },  { "fpof", 5 },
              { "furq", 6 },  { "iyqw", 7 },  { "kgmz", 8 },  { "khzy", 9 },  { "nash", 10 }, { "ncoe", 11 },
              { "nkgc", 12 }, { "nrmo", 13 }, { "nwef", 14 }, { "rals", 15 }, { "ripd", 16 }, { "undn", 17 },
              { "uoyw", 18 }, { "vjqi", 19 }, { "vupr", 20 }, { "wmzh", 21 }, { "wqrd", 22 }, { "yrkm", 23 },
              { "ysgi", 24 }, { "yxix", 25 }, { "zawo", 26 }, { "zgaf", 27 }, { "zqyg", 28 }, { "zuni", 29 } },
            { { "absk", 0 },  { "aocd", 1 },  { "benn", 2 },  { "dkzu", 3 },  { "dpff", 4 },  { "dtst", 5 },
              { "dxsw", 6 },  { "fbmn", 7 },  { "fewv", 8 },  { "ffjb", 9 },  { "gimg", 10 }, { "huke", 11 },
              { "jurz", 12 }, { "lszm", 13 }, { "miqj", 14 }, { "mjez", 15 }, { "oftf", 16 }, { "qjim", 17 },
              { "qmxv", 18 }, { "rbkg", 19 }, { "rrcq", 20 }, { "rwuz", 21 }, { "ssvg", 22 }, { "uarc", 23 },
              { "uskn", 24 }, { "uwkm", 25 }, { "vbsh", 26 }, { "wdjn", 27 }, { "xqbc", 28 }, { "xwmq", 29 } } };

    try {
        AnyDatasetTest ad(VCR("\004\000\000\000plnb\004\000\000\000ukod\004\000\000\000nash\004\000\000\000benn"),
                          { {}, { 0, 1, 2, 3 }, 4, {}, is_enforce_byteswap(true) });
        std::cout << "OrdinalEncoder: one transaction" << std::endl;
        std::cout << ad.get_categorical_features() << " ⮕ ";
        snapml::OrdinalEncoder::Params p;
        p.categories = categories_1;
        snapml::OrdinalEncoder t(p);
        t.transform(ad);
        std::cout << ad.get_enc_features() << std::endl;
        expected = "[[14, 22, 10, 2]]";
        if (ad.get_enc_features() != expected)
            throw std::runtime_error(ad.get_enc_features() + " != " + expected);
        if (ad.get_num_ex() != 1)
            throw std::runtime_error(std::to_string(ad.get_num_ex()) + " != 1");
        compare_sklearn_ord("[['plnb','ukod','nash','benn']]", categories_to_json(categories_1), expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    std::cout << std::endl;

    try {
        AnyDatasetTest ad(
            VCR("\004\000\000\000ffph\004\000\000\000ezee\004\000\000\000wqrd"
                "\04\000\000\000lszm\004\000\000\000taga\004\000\000\000ghrk\004\000\000\000cjsj\004\000\000\000uwkm"),
            { {}, { 0, 1, 2, 3 }, 4, {}, is_enforce_byteswap(true) });
        std::cout << "OrdinalEncoder: two transactions" << std::endl;
        std::cout << ad.get_categorical_features() << " ⮕ ";
        snapml::OrdinalEncoder::Params p;
        p.categories = categories_1;
        snapml::OrdinalEncoder t(p);
        t.transform(ad);
        std::cout << ad.get_enc_features() << std::endl;
        expected = "[[4, 5, 22, 13], [20, 7, 1, 25]]";
        if (ad.get_enc_features() != expected)
            throw std::runtime_error(ad.get_enc_features() + " != " + expected);
        if (ad.get_num_ex() != 2)
            throw std::runtime_error(std::to_string(ad.get_num_ex()) + " != 2");
        compare_sklearn_ord("[['ffph','ezee','wqrd','lszm'],['taga','ghrk','cjsj','uwkm']]",
                            categories_to_json(categories_1), expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        AnyDatasetTest ad(
            VCR("\004\000\000\000ffph\004\000\000\000ezee\004\000\000\000xxxx"
                "\004\000\000\000lszm\004\000\000\000taga\004\000\000\000yyyy\004\000\000\000cjsj\004\000\000\000uwkm"),
            { {}, { 0, 1, 2, 3 }, 4, {}, is_enforce_byteswap(true) });
        std::cout << "OrdinalEncoder: two transactions with input that cannot be categorized" << std::endl;
        std::cout << ad.get_categorical_features() << " ⮕ ";
        snapml::OrdinalEncoder::Params p;
        p.categories = categories_1;
        snapml::OrdinalEncoder t(p);
        t.transform(ad);
        std::cout << ad.get_enc_features() << std::endl;
        expected = "[[4, 5, -1, 13], [20, -1, 1, 25]]";
        if (ad.get_enc_features() != expected)
            throw std::runtime_error(ad.get_enc_features() + " != " + expected);
        compare_sklearn_ord("[['ffph','ezee','xxxx','lszm'],['taga','yyyy','cjsj','uwkm']]",
                            categories_to_json(categories_1), expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        AnyDatasetTest ad(VCR("\004\000\000\000ffph\004\000\000\000ezee\004\000\000\000wqrd\004\000\000\000taga"
                              "\004\000\000\000ghrk\004\000\000\000cjsj"),
                          { {}, { 0, 1, 2 }, 3, {}, is_enforce_byteswap(true) });
        std::cout << "OrdinalEncoder: two transactions, testing with a wrong number of features as input" << std::endl;
        std::cout << ad.get_categorical_features() << " ⮕ ";
        snapml::OrdinalEncoder::Params p;
        p.categories = categories_1;
        snapml::OrdinalEncoder t(p);
        t.transform(ad);
        std::cout << "Test was expected to generate an error.";
        assert(0);
    } catch (const std::exception& e) {
        if (std::string(e.what()).compare(
                "Input has 3 features, but OrdinalEncoder is expecting 4 features as input.")) {
            std::cout << "Test failed with message '" << e.what()
                      << "', but was expected to fail with message: 'Input has 3 features, but OrdinalEncoder is "
                         "expecting 4 features as input.'"
                      << std::endl;
            assert(0);
        } else {
            std::cout << "Test succeeded with message '" << e.what() << "'" << std::endl << std::endl;
        }
    }

    std::vector<std::map<std::string, int>> categories_1_1
        = { { { "afvm", 0 },  { "astw", 1 },  { "bjyi", 2 },  { "cmbe", 3 },  { "cwxh", 4 },  { "ezee", 5 },
              { "fwji", 6 },  { "ghrk", 7 },  { "hwle", 8 },  { "icph", 9 },  { "igec", 10 }, { "kllj", 11 },
              { "kugl", 12 }, { "lznv", 13 }, { "obfr", 14 }, { "piud", 15 }, { "pogc", 16 }, { "qbwd", 17 },
              { "qedx", 18 }, { "qfak", 19 }, { "qhgd", 20 }, { "tali", 21 }, { "ukod", 22 }, { "vaej", 23 },
              { "vrpu", 24 }, { "wbkx", 25 }, { "wxit", 26 }, { "xtmq", 27 }, { "ycvz", 28 }, { "yyib", 29 } },
            { { "absk", 0 },  { "aocd", 1 },  { "benn", 2 },  { "dkzu", 3 },  { "dpff", 4 },  { "dtst", 5 },
              { "dxsw", 6 },  { "fbmn", 7 },  { "fewv", 8 },  { "ffjb", 9 },  { "gimg", 10 }, { "huke", 11 },
              { "jurz", 12 }, { "lszm", 13 }, { "miqj", 14 }, { "mjez", 15 }, { "oftf", 16 }, { "qjim", 17 },
              { "qmxv", 18 }, { "rbkg", 19 }, { "rrcq", 20 }, { "rwuz", 21 }, { "ssvg", 22 }, { "uarc", 23 },
              { "uskn", 24 }, { "uwkm", 25 }, { "vbsh", 26 }, { "wdjn", 27 }, { "xqbc", 28 }, { "xwmq", 29 } } };

    try {
        AnyDatasetTest ad(VCR("\004\000\000\000ffph\004\000\000\000ezee\004\000\000\000wqrd\004\000\000\000lszm"
                              "\004\000\000\000taga\004\000\000\000ghrk\004\000\000\000cjsj\004\000\000\000uwkm"),
                          { {}, { 0, 1, 2, 3 }, 4, {}, is_enforce_byteswap(true) });
        std::cout << "OrdinalEncoder: two transactions and an index list: { 1, 3 }" << std::endl;
        std::cout << ad.get_categorical_features() << " ⮕ ";
        snapml::OrdinalEncoder::Params p;
        p.categories = categories_1_1;
        p.index_list = { 1, 3 };
        snapml::OrdinalEncoder t(p);
        t.transform(ad);
        std::cout << ad.get_enc_features() << std::endl;
        expected = "[[5, 13], [7, 25]]";
        if (ad.get_enc_features() != expected)
            throw std::runtime_error(ad.get_enc_features() + " != " + expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    std::cout << std::endl;

    std::vector<std::map<std::string, int>> categories_1_2
        = { { { "abrm", 0 },  { "ceut", 1 },  { "eemq", 2 },  { "efzn", 3 },  { "ffph", 4 },  { "flou", 5 },
              { "fxwy", 6 },  { "geqh", 7 },  { "gjgr", 8 },  { "guxq", 9 },  { "ibxq", 10 }, { "ickf", 11 },
              { "mvlr", 12 }, { "oahc", 13 }, { "plnb", 14 }, { "pndb", 15 }, { "poef", 16 }, { "sncr", 17 },
              { "sote", 18 }, { "svwn", 19 }, { "taga", 20 }, { "tmcs", 21 }, { "uipy", 22 }, { "vebx", 23 },
              { "vgcv", 24 }, { "vqwf", 25 }, { "vymq", 26 }, { "xdyf", 27 }, { "zhqv", 28 }, { "zwnz", 29 } },
            { { "bcqe", 0 },  { "cjsj", 1 },  { "cwpp", 2 },  { "dvxp", 3 },  { "dzkn", 4 },  { "fpof", 5 },
              { "furq", 6 },  { "iyqw", 7 },  { "kgmz", 8 },  { "khzy", 9 },  { "nash", 10 }, { "ncoe", 11 },
              { "nkgc", 12 }, { "nrmo", 13 }, { "nwef", 14 }, { "rals", 15 }, { "ripd", 16 }, { "undn", 17 },
              { "uoyw", 18 }, { "vjqi", 19 }, { "vupr", 20 }, { "wmzh", 21 }, { "wqrd", 22 }, { "yrkm", 23 },
              { "ysgi", 24 }, { "yxix", 25 }, { "zawo", 26 }, { "zgaf", 27 }, { "zqyg", 28 }, { "zuni", 29 } } };

    try {
        AnyDatasetTest ad(VCR("\004\000\000\000ffph\004\000\000\000ezee\004\000\000\000wqrd\004\000\000\000lszm"
                              "\004\000\000\000taga\004\000\000\000ghrk\004\000\000\000cjsj\004\000\000\000uwkm"),
                          { {}, { 0, 1, 2, 3 }, 4, {}, is_enforce_byteswap(true) });
        std::cout << "OrdinalEncoder: two transactions and an index list: { 0, 2 }" << std::endl;
        std::cout << ad.get_categorical_features() << " ⮕ ";
        snapml::OrdinalEncoder::Params p;
        p.categories = categories_1_2;
        p.index_list = { 0, 2 };
        snapml::OrdinalEncoder t(p);
        t.transform(ad);
        std::cout << ad.get_enc_features() << std::endl;
        expected = "[[4, 22], [20, 1]]";
        if (ad.get_enc_features() != expected)
            throw std::runtime_error(ad.get_enc_features() + " != " + expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    std::cout << std::endl;

    try {
        AnyDatasetTest ad(VCR("\004\000\000\000plnb\004\000\000\000ukod\004\000\000\000nash\004\000\000\000benn"),
                          { {}, { 0, 1, 2, 3 }, 4, {}, is_enforce_byteswap(true) }, ",");
        std::cout << "OneHotEncoder: one transaction" << std::endl;
        std::cout << ad.get_categorical_features() << " ⮕ ";
        snapml::OneHotEncoder::Params p;
        p.categories = categories_1;
        snapml::OneHotEncoder t(p);
        t.transform(ad);
        std::cout << ad.get_enc_features() << std::endl;
        expected = "[[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]";
        if (ad.get_enc_features() != expected)
            throw std::runtime_error(ad.get_enc_features() + " != " + expected);
        if (ad.get_num_ex() != 1)
            throw std::runtime_error(std::to_string(ad.get_num_ex()) + " != 1");
        compare_sklearn_ohe("[['plnb','ukod','nash','benn']]", categories_to_json(categories_1), expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;

        assert(0);
    }

    std::cout << std::endl;

    try {
        AnyDatasetTest ad(VCR("\004\000\000\000ffph\004\000\000\000ezee\004\000\000\000wqrd\004\000\000\000lszm"
                              "\004\000\000\000taga\004\000\000\000ghrk\004\000\000\000cjsj\004\000\000\000uwkm"),
                          { {}, { 0, 1, 2, 3 }, 4, {}, is_enforce_byteswap(true) });
        std::cout << "OneHotEncoder: two transactions" << std::endl;
        std::cout << ad.get_categorical_features() << " ⮕ ";
        snapml::OneHotEncoder::Params p;
        p.categories = categories_1;
        snapml::OneHotEncoder t(p);
        t.transform(ad);
        std::cout << ad.get_enc_features() << std::endl;
        expected = "[[0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "
                   "[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]]";
        if (ad.get_enc_features() != expected)
            throw std::runtime_error(ad.get_enc_features() + " != " + expected);
        if (ad.get_num_ex() != 2)
            throw std::runtime_error(std::to_string(ad.get_num_ex()) + " != 2");
        compare_sklearn_ohe("[['ffph','ezee','wqrd','lszm'],['taga','ghrk','cjsj','uwkm']]",
                            categories_to_json(categories_1), expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        AnyDatasetTest ad(
            VCR("\004\000\000\000ffph\004\000\000\000ezee\004\000\000\000xxxx"
                "\004\000\000\000lszm\004\000\000\000taga\004\000\000\000yyyy\004\000\000\000cjsj\004\000\000\000uwkm"),
            { {}, { 0, 1, 2, 3 }, 4, {}, is_enforce_byteswap(true) });
        std::cout << "OneHotEncoder: two transactions with input that cannot be categorized" << std::endl;
        std::cout << ad.get_categorical_features() << " ⮕ ";
        snapml::OneHotEncoder::Params p;
        p.categories = categories_1;
        snapml::OneHotEncoder t(p);
        t.transform(ad);
        std::cout << ad.get_enc_features() << std::endl;
        expected = "[[0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]]";
        if (ad.get_enc_features() != expected)
            throw std::runtime_error(ad.get_enc_features() + " != " + expected);
        compare_sklearn_ohe("[['ffph','ezee','xxxx','lszm'],['taga','yyyy','cjsj','uwkm']]",
                            categories_to_json(categories_1), expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    std::vector<std::map<std::string, int>> categories_2
        = { { { "abrm", 0 },  { "ceut", 1 },  { "eemq", 2 },  { "efzn", 3 },  { "ffph", 4 },  { "flou", 5 },
              { "fxwy", 6 },  { "geqh", 7 },  { "gjgr", 8 },  { "guxq", 9 },  { "ibxq", 10 }, { "ickf", 11 },
              { "mvlr", 12 }, { "oahc", 13 }, { "plnb", 14 }, { "pndb", 15 }, { "poef", 16 }, { "sncr", 17 },
              { "sote", 18 }, { "svwn", 19 }, { "taga", 20 }, { "tmcs", 21 }, { "uipy", 22 }, { "vebx", 23 },
              { "vgcv", 24 }, { "vqwf", 25 }, { "vymq", 26 }, { "xdyf", 27 }, { "zhqv", 28 }, { "zwnz", 29 } },
            { { "afvm", 0 },  { "astw", 1 },  { "bjyi", 2 },  { "cmbe", 3 },  { "cwxh", 4 },
              { "ezee", 5 },  { "fwji", 6 },  { "ghrk", 7 },  { "hwle", 8 },  { "icph", 9 },
              { "igec", 10 }, { "kllj", 11 }, { "kugl", 12 }, { "lznv", 13 }, { "obfr", 14 },
              { "piud", 15 }, { "pogc", 16 }, { "qbwd", 17 }, { "qedx", 18 }, { "qfak", 19 },
              { "qhgd", 20 }, { "tali", 21 }, { "ukod", 22 }, { "vaej", 23 }, { "vrpu", 24 } },
            { { "bcqe", 0 },  { "cjsj", 1 },  { "cwpp", 2 },  { "dvxp", 3 },  { "dzkn", 4 },  { "fpof", 5 },
              { "furq", 6 },  { "iyqw", 7 },  { "kgmz", 8 },  { "khzy", 9 },  { "nash", 10 }, { "ncoe", 11 },
              { "nkgc", 12 }, { "nrmo", 13 }, { "nwef", 14 }, { "rals", 15 }, { "ripd", 16 }, { "undn", 17 },
              { "uoyw", 18 }, { "vjqi", 19 }, { "vupr", 20 }, { "wmzh", 21 }, { "wqrd", 22 }, { "yrkm", 23 },
              { "ysgi", 24 }, { "yxix", 25 }, { "zawo", 26 }, { "zgaf", 27 } },
            { { "absk", 0 },  { "aocd", 1 },  { "benn", 2 },  { "dkzu", 3 },  { "dpff", 4 },  { "dtst", 5 },
              { "dxsw", 6 },  { "fbmn", 7 },  { "fewv", 8 },  { "ffjb", 9 },  { "gimg", 10 }, { "huke", 11 },
              { "jurz", 12 }, { "lszm", 13 }, { "miqj", 14 }, { "mjez", 15 }, { "oftf", 16 }, { "qjim", 17 },
              { "qmxv", 18 }, { "rbkg", 19 }, { "rrcq", 20 }, { "rwuz", 21 }, { "ssvg", 22 }, { "uarc", 23 },
              { "uskn", 24 }, { "uwkm", 25 } } };

    try {
        AnyDatasetTest ad(VCR("\004\000\000\000ffph\004\000\000\000ezee\004\000\000\000wqrd\004\000\000\000lszm"
                              "\004\000\000\000taga\004\000\000\000ghrk\004\000\000\000cjsj\004\000\000\000uwkm"),
                          { {}, { 0, 1, 2, 3 }, 4, {}, is_enforce_byteswap(true) });
        std::cout << "OneHotEncoder: two transactions, different number of categories" << std::endl;
        std::cout << ad.get_categorical_features() << " ⮕ ";
        snapml::OneHotEncoder::Params p;
        p.categories = categories_2;
        snapml::OneHotEncoder t(p);
        t.transform(ad);
        std::cout << ad.get_enc_features() << std::endl;
        // manually removed content from the expected output
        expected = "[[0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "
                   "[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]]";
        if (ad.get_enc_features() != expected)
            throw std::runtime_error(ad.get_enc_features() + " != " + expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    std::cout << std::endl;

    try {
        AnyDatasetTest ad(VCR("\004\000\000\000ffph\004\000\000\000ezee\004\000\000\000wqrd"
                              "\004\000\000\000taga\004\000\000\000ghrk\004\000\000\000cjsj"),
                          { {}, { 0, 1, 2 }, 3, {}, is_enforce_byteswap(true) });
        std::cout << "OneHotEncoder: two transactions, testing with a wrong number of features as input" << std::endl;
        std::cout << ad.get_categorical_features() << " ⮕ ";
        snapml::OneHotEncoder::Params p;
        p.categories = categories_1;
        snapml::OneHotEncoder t(p);
        t.transform(ad);
        std::cout << "Test was expected to generate an error.";
        assert(0);
    } catch (const std::exception& e) {
        if (std::string(e.what()).compare(
                "Input has 3 features, but OneHotEncoder is expecting 4 features as input.")) {
            std::cout << "Test failed with message '" << e.what()
                      << "', but was expected to fail with message: 'Input has 3 features, but OneHotEncoder is "
                         "expecting 4 features as input.'"
                      << std::endl;
            assert(0);
        } else {
            std::cout << "Test succeeded with message '" << e.what() << "'" << std::endl << std::endl;
        }
    }

    try {
        AnyDatasetTest ad(VCR("\004\000\000\000ffph\004\000\000\000ezee\004\000\000\000wqrd\004\000\000\000lszm"
                              "\004\000\000\000taga\004\000\000\000ghrk\004\000\000\000cjsj\004\000\000\000uwkm"),
                          { {}, { 0, 1, 2, 3 }, 4, {}, is_enforce_byteswap(true) });
        std::cout << "OneHotEncoder: two transactions and an index list: { 1, 3 }" << std::endl;
        std::cout << ad.get_categorical_features() << " ⮕ ";
        snapml::OneHotEncoder::Params p;
        p.categories = categories_1_1;
        p.index_list = { 1, 3 };
        snapml::OneHotEncoder t(p);
        t.transform(ad);
        std::cout << ad.get_enc_features() << std::endl;
        expected = "[[0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "
                   "[0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]]";
        if (ad.get_enc_features() != expected)
            throw std::runtime_error(ad.get_enc_features() + " != " + expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    std::cout << std::endl;

    try {
        AnyDatasetTest ad(VCR("\004\000\000\000ffph\004\000\000\000ezee\004\000\000\000wqrd\004\000\000\000lszm"
                              "\004\000\000\000taga\004\000\000\000ghrk\004\000\000\000cjsj\004\000\000\000uwkm"),
                          { {}, { 0, 1, 2, 3 }, 4, {}, is_enforce_byteswap(true) });
        std::cout << "OneHotEncoder: two transactions and an index list: { 0, 2 }" << std::endl;
        std::cout << ad.get_categorical_features() << " ⮕ ";
        snapml::OneHotEncoder::Params p;
        p.categories = categories_1_2;
        p.index_list = { 0, 2 };
        snapml::OneHotEncoder t(p);
        t.transform(ad);
        std::cout << ad.get_enc_features() << std::endl;
        expected = "[[0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0], "
                   "[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                   "0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]";
        if (ad.get_enc_features() != expected)
            throw std::runtime_error(ad.get_enc_features() + " != " + expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    std::cout << std::endl;

    std::vector<std::map<std::string, float>> categories_3
        = { { { "ased", 0.0075 }, { "bigk", 0.0240 }, { "buea", 0.0367 }, { "dasd", 0.0109 }, { "ddxm", 0.0220 },
              { "dexy", 0.0207 }, { "fyhg", 0.0348 }, { "goyb", 0.0268 }, { "iair", 0.0146 }, { "ihzt", 0.0075 },
              { "jeye", 0.0265 }, { "kxmg", 0.0382 }, { "lmng", 0.0 },    { "nmyz", 0.0296 }, { "ntov", 0.0092 },
              { "pndb", 0.0307 }, { "poef", 0.0300 }, { "sncr", 0.0332 }, { "sote", 0.0122 }, { "svwn", 0.0263 },
              { "taga", 0.0201 }, { "tmcs", 0.0265 }, { "uipy", 0.0227 }, { "vebx", 0.0258 }, { "vgcv", 0.0183 },
              { "vqwf", 0.0213 }, { "vymq", 0.0228 }, { "xdyf", 0.0453 }, { "zhqv", 0.0222 }, { "zwnz", 0.0139 } },
            { { "afvm", 0.0249 }, { "astw", 0.0182 }, { "bjyi", 0.0150 }, { "cmbe", 0.0277 }, { "cwxh", 0.0151 },
              { "ezee", 0.0119 }, { "fwji", 0.0145 }, { "ghrk", 0.0257 }, { "hwle", 0.0110 }, { "icph", 0.0201 },
              { "igec", 0.0277 }, { "kllj", 0.0377 }, { "kugl", 0.0161 }, { "lznv", 0.0416 }, { "obfr", 0.0176 },
              { "piud", 0.0152 }, { "pogc", 0.0160 }, { "qbwd", 0.0403 }, { "qedx", 0.0307 }, { "qfak", 0.0117 },
              { "qhgd", 0.0292 }, { "tali", 0.0187 }, { "ukod", 0.0282 }, { "vaej", 0.0186 }, { "vrpu", 0.0141 },
              { "wbkx", 0.0331 }, { "wxit", 0.0222 }, { "xtmq", 0.0143 }, { "ycvz", 0.0231 }, { "yyib", 0.0386 } },
            { { "bcqe", 0.0203 }, { "cjsj", 0.0226 }, { "cwpp", 0.0109 }, { "dvxp", 0.0123 }, { "dzkn", 0.0165 },
              { "fpof", 0.0171 }, { "furq", 0.0202 }, { "iyqw", 0.0234 }, { "kgmz", 0.0113 }, { "khzy", 0.0277 },
              { "nash", 0.0138 }, { "ncoe", 0.0169 }, { "nkgc", 0.0264 }, { "nrmo", 0.0276 }, { "nwef", 0.0223 },
              { "rals", 0.0324 }, { "ripd", 0.0209 }, { "undn", 0.0247 }, { "uoyw", 0.0301 }, { "vjqi", 0.0142 },
              { "vupr", 0.0118 }, { "wmzh", 0.0117 }, { "wqrd", 0.0373 }, { "yrkm", 0.0218 }, { "ysgi", 0.0070 },
              { "yxix", 0.0239 }, { "zawo", 0.0356 }, { "zgaf", 0.0436 }, { "zqyg", 0.0367 }, { "zuni", 0.0434 } },
            { { "absk", 0.0100 }, { "aocd", 0.0255 }, { "benn", 0.0336 }, { "dkzu", 0.0148 }, { "dpff", 0.0085 },
              { "dtst", 0.0215 }, { "dxsw", 0.0337 }, { "fbmn", 0.0281 }, { "fewv", 0.0253 }, { "ffjb", 0.0331 },
              { "gimg", 0.0146 }, { "huke", 0.0523 }, { "jurz", 0.0349 }, { "lszm", 0.0167 }, { "miqj", 0.0073 },
              { "mjez", 0.0319 }, { "oftf", 0.0297 }, { "qjim", 0.0287 }, { "qmxv", 0.0117 }, { "rbkg", 0.0249 },
              { "rrcq", 0.0268 }, { "rwuz", 0.0086 }, { "ssvg", 0.0115 }, { "uarc", 0.0283 }, { "uskn", 0.0151 },
              { "uwkm", 0.0361 }, { "vbsh", 0.0176 }, { "wdjn", 0.0122 }, { "xqbc", 0.0207 }, { "xwmq", 0.0146 } } };

    try {
        AnyDatasetTest ad(VCR("\004\000\000\000vymq\004\000\000\000kugl\004\000\000\000dvxp\004\000\000\000qjim"),
                          { {}, { 0, 1, 2, 3 }, 4, {}, is_enforce_byteswap(true) });
        std::cout << "TargetEncoder: one transaction" << std::endl;
        std::cout << ad.get_categorical_features() << " ⮕ ";
        snapml::TargetEncoder::Params p;
        p.categories  = categories_3;
        p.target_mean = 0.02275;
        snapml::TargetEncoder t(p);
        t.transform(ad);
        std::cout << ad.get_enc_features() << std::endl;
        expected = "[[0.0228, 0.0161, 0.0123, 0.0287]]";
        if (ad.get_enc_features() != expected)
            throw std::runtime_error(ad.get_enc_features() + " != " + expected);
        if (ad.get_num_ex() != 1)
            throw std::runtime_error(std::to_string(ad.get_num_ex()) + " != 1");
        compare_sklearn_target("[['vymq','kugl','dvxp','qjim']]", categories_to_json(categories_3),
                               encodings_to_json(categories_3), 0.02275, expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        AnyDatasetTest ad(VCR("\004\000\000\000vymq\004\000\000\000kugl\004\000\000\000dvxp\004\000\000\000qjim"
                              "\004\000\000\000sncr\004\000\000\000obfr\004\000\000\000uoyw\004\000\000\000mjez"),
                          { {}, { 0, 1, 2, 3 }, 4, {}, is_enforce_byteswap(true) });
        std::cout << "TargetEncoder: two transactions" << std::endl;
        std::cout << ad.get_categorical_features() << " ⮕ ";
        snapml::TargetEncoder::Params p;
        p.categories  = categories_3;
        p.target_mean = 0.02275;
        snapml::TargetEncoder t(p);
        t.transform(ad);
        std::cout << ad.get_enc_features() << std::endl;
        expected = "[[0.0228, 0.0161, 0.0123, 0.0287], [0.0332, 0.0176, 0.0301, 0.0319]]";
        if (ad.get_enc_features() != expected)
            throw std::runtime_error(ad.get_enc_features() + " != " + expected);
        if (ad.get_num_ex() != 2)
            throw std::runtime_error(std::to_string(ad.get_num_ex()) + " != 2");
        compare_sklearn_target("[['vymq','kugl','dvxp','qjim'],['sncr','obfr','uoyw','mjez']]",
                               categories_to_json(categories_3), encodings_to_json(categories_3), 0.02275, expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        AnyDatasetTest ad(VCR("\004\000\000\000vymq\004\000\000\000kugl\004\000\000\000xxxx\004\000\000\000qjim"
                              "\004\000\000\000sncr\004\000\000\000yyyy\004\000\000\000uoyw\004\000\000\000mjez"),
                          { {}, { 0, 1, 2, 3 }, 4, {}, is_enforce_byteswap(true) });
        std::cout << "TargetEncoder: two transactions with input that cannot be categorized" << std::endl;
        std::cout << ad.get_categorical_features() << " ⮕ ";
        snapml::TargetEncoder::Params p;
        p.categories  = categories_3;
        p.target_mean = 0.02275;
        snapml::TargetEncoder t(p);
        t.transform(ad);
        std::cout << ad.get_enc_features() << std::endl;
        expected = "[[0.0228, 0.0161, 0.02275, 0.0287], [0.0332, 0.02275, 0.0301, 0.0319]]";
        if (ad.get_enc_features() != expected)
            throw std::runtime_error(ad.get_enc_features() + " != " + expected);
        compare_sklearn_target("[['vymq','kugl','xxxx','qjim'],['sncr','yyyy','uoyw','mjez']]",
                               categories_to_json(categories_3), encodings_to_json(categories_3), 0.02275, expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    try {
        AnyDatasetTest ad(VCR("\004\000\000\000vymq\004\000\000\000kugl\004\000\000\000dvxp\004\000\000\000sncr"
                              "\004\000\000\000obfr\004\000\000\000uoyw"),
                          { {}, { 0, 1, 2 }, 3, {}, is_enforce_byteswap(true) });
        std::cout << "TargetEncoder: two transactions, testing with a wrong number of features as input" << std::endl;
        std::cout << ad.get_categorical_features() << " ⮕ ";
        snapml::TargetEncoder::Params p;
        p.categories  = categories_3;
        p.target_mean = 0.02275;
        snapml::TargetEncoder t(p);
        t.transform(ad);
        std::cout << "Test was expected to generate an error.";
        assert(0);
    } catch (const std::exception& e) {
        if (std::string(e.what()).compare(
                "Input has 3 features, but TargetEncoder is expecting 4 features as input.")) {
            std::cout << "Test failed with message '" << e.what()
                      << "', but was expected to fail with message: 'Input has 3 features, but TargetEncoder is "
                         "expecting 4 features as input.'"
                      << std::endl;
            assert(0);
        } else {
            std::cout << "Test succeeded with message '" << e.what() << "'" << std::endl << std::endl;
        }
    }

    std::vector<std::map<std::string, float>> categories_3_1
        = { { { "afvm", 0.0249 }, { "astw", 0.0182 }, { "bjyi", 0.0150 }, { "cmbe", 0.0277 }, { "cwxh", 0.0151 },
              { "ezee", 0.0119 }, { "fwji", 0.0145 }, { "ghrk", 0.0257 }, { "hwle", 0.0110 }, { "icph", 0.0201 },
              { "igec", 0.0277 }, { "kllj", 0.0377 }, { "kugl", 0.0161 }, { "lznv", 0.0416 }, { "obfr", 0.0176 },
              { "piud", 0.0152 }, { "pogc", 0.0160 }, { "qbwd", 0.0403 }, { "qedx", 0.0307 }, { "qfak", 0.0117 },
              { "qhgd", 0.0292 }, { "tali", 0.0187 }, { "ukod", 0.0282 }, { "vaej", 0.0186 }, { "vrpu", 0.0141 },
              { "wbkx", 0.0331 }, { "wxit", 0.0222 }, { "xtmq", 0.0143 }, { "ycvz", 0.0231 }, { "yyib", 0.0386 } },
            { { "absk", 0.0100 }, { "aocd", 0.0255 }, { "benn", 0.0336 }, { "dkzu", 0.0148 }, { "dpff", 0.0085 },
              { "dtst", 0.0215 }, { "dxsw", 0.0337 }, { "fbmn", 0.0281 }, { "fewv", 0.0253 }, { "ffjb", 0.0331 },
              { "gimg", 0.0146 }, { "huke", 0.0523 }, { "jurz", 0.0349 }, { "lszm", 0.0167 }, { "miqj", 0.0073 },
              { "mjez", 0.0319 }, { "oftf", 0.0297 }, { "qjim", 0.0287 }, { "qmxv", 0.0117 }, { "rbkg", 0.0249 },
              { "rrcq", 0.0268 }, { "rwuz", 0.0086 }, { "ssvg", 0.0115 }, { "uarc", 0.0283 }, { "uskn", 0.0151 },
              { "uwkm", 0.0361 }, { "vbsh", 0.0176 }, { "wdjn", 0.0122 }, { "xqbc", 0.0207 }, { "xwmq", 0.0146 } } };

    try {
        AnyDatasetTest ad(
            VCR("\004\000\000\000vymq\004\000\000\000kugl\004\000\000\000dvxp\004\000\000\000qjim\004\000\000\000sncr"
                "\004\000\000\000obfr\004\000\000\000uoyw\004\000\000\000mjez"),
            { {}, { 0, 1, 2, 3 }, 4, {}, is_enforce_byteswap(true) });
        std::cout << "TargetEncoder: two transactions and an index list: { 1, 3 }" << std::endl;
        std::cout << ad.get_categorical_features() << " ⮕ ";
        snapml::TargetEncoder::Params p;
        p.categories  = categories_3_1;
        p.target_mean = 0.02275;
        p.index_list  = { 1, 3 };
        snapml::TargetEncoder t(p);
        t.transform(ad);
        std::cout << ad.get_enc_features() << std::endl;
        expected = "[[0.0161, 0.0287], [0.0176, 0.0319]]";
        if (ad.get_enc_features() != expected)
            throw std::runtime_error(ad.get_enc_features() + " != " + expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    std::cout << std::endl;

    std::vector<std::map<std::string, float>> categories_3_2
        = { { { "ased", 0.0075 }, { "bigk", 0.0240 }, { "buea", 0.0367 }, { "dasd", 0.0109 }, { "ddxm", 0.0220 },
              { "dexy", 0.0207 }, { "fyhg", 0.0348 }, { "goyb", 0.0268 }, { "iair", 0.0146 }, { "ihzt", 0.0075 },
              { "jeye", 0.0265 }, { "kxmg", 0.0382 }, { "lmng", 0.0 },    { "nmyz", 0.0296 }, { "ntov", 0.0092 },
              { "pndb", 0.0307 }, { "poef", 0.0300 }, { "sncr", 0.0332 }, { "sote", 0.0122 }, { "svwn", 0.0263 },
              { "taga", 0.0201 }, { "tmcs", 0.0265 }, { "uipy", 0.0227 }, { "vebx", 0.0258 }, { "vgcv", 0.0183 },
              { "vqwf", 0.0213 }, { "vymq", 0.0228 }, { "xdyf", 0.0453 }, { "zhqv", 0.0222 }, { "zwnz", 0.0139 } },
            { { "bcqe", 0.0203 }, { "cjsj", 0.0226 }, { "cwpp", 0.0109 }, { "dvxp", 0.0123 }, { "dzkn", 0.0165 },
              { "fpof", 0.0171 }, { "furq", 0.0202 }, { "iyqw", 0.0234 }, { "kgmz", 0.0113 }, { "khzy", 0.0277 },
              { "nash", 0.0138 }, { "ncoe", 0.0169 }, { "nkgc", 0.0264 }, { "nrmo", 0.0276 }, { "nwef", 0.0223 },
              { "rals", 0.0324 }, { "ripd", 0.0209 }, { "undn", 0.0247 }, { "uoyw", 0.0301 }, { "vjqi", 0.0142 },
              { "vupr", 0.0118 }, { "wmzh", 0.0117 }, { "wqrd", 0.0373 }, { "yrkm", 0.0218 }, { "ysgi", 0.0070 },
              { "yxix", 0.0239 }, { "zawo", 0.0356 }, { "zgaf", 0.0436 }, { "zqyg", 0.0367 }, { "zuni", 0.0434 } } };

    try {
        AnyDatasetTest ad(
            VCR("\004\000\000\000vymq\004\000\000\000kugl\004\000\000\000dvxp\004\000\000\000qjim\004\000\000\000sncr"
                "\004\000\000\000obfr\004\000\000\000uoyw\004\000\000\000mjez"),
            { {}, { 0, 1, 2, 3 }, 4, {}, is_enforce_byteswap(true) });
        std::cout << "TargetEncoder: two transactions and an index list: { 0, 2 }" << std::endl;
        std::cout << ad.get_categorical_features() << " ⮕ ";
        snapml::TargetEncoder::Params p;
        p.categories  = categories_3_2;
        p.target_mean = 0.02275;
        p.index_list  = { 0, 2 };
        snapml::TargetEncoder t(p);
        t.transform(ad);
        std::cout << ad.get_enc_features() << std::endl;
        expected = "[[0.0228, 0.0123], [0.0332, 0.0301]]";
        if (ad.get_enc_features() != expected)
            throw std::runtime_error(ad.get_enc_features() + " != " + expected);
    } catch (const std::exception& e) {
        std::cout << "Test failed: " << e.what() << std::endl;
        assert(0);
    }

    std::cout << std::endl;
}

void test_pipeline_orig()

{
    snapml::Pipeline p;
    std::string      expected;

    std::cout << "Testing whole pipeline based on a JSON file ==> Func, Norm, KBins, OHE" << std::endl;

    try {
        p.import("../test/data/pipeline_1.json");
    } catch (const std::exception& e) {
        std::cout << "Error importing pipeline information: " << e.what() << std::endl;
        assert(0);
    }

    snapml::DataSchema data_schema = p.get_schema();
    data_schema.enforce_byteswap   = is_enforce_byteswap(true);

    AnyDatasetTest ad(
        VCR("\003\000\000\000320\005\000\000\00030000\005\000\000\00060000\005\000\000\00090000"
            "\006\000\000\000120000\011\000\000\000999999840\002\000\000\00050\005\000\000\00030000"
            "\005\000\000\00060000\005\000\000\00090010\006\000\000\000120000\006\000\000\000515750"
            "\002\000\000\00080"
            "\022\000\000\00022025.465794806718\021\000\000\000485165194.4097903"
            "\004\000\000\000aiku\004\000\000\000brqu\004\000\000\000gtyi\004\000\000\000doax"
            "\004\000\000\000fvjq\004\000\000\000dwtx\004\000\000\000eloh\004\000\000\000gkji\004\000\000\000ixdy"
            "\004\000\000\000inid\004\000\000\000yydc\004\000\000\000wuqz\004\000\000\000wjdo\004\000\000\000zieg"
            "\004\000\000\000vylf\004\000\000\000wuih\004\000\000\000rvjm\004\000\000\000uwun\004\000\000\000tawk"
            "\004\000\000\000sydq"),
        data_schema);

    try {
        p.transform(ad);
    } catch (const std::exception& e) {
        std::cout << "Error running transformers: " << e.what() << std::endl;
        assert(0);
    }

    expected = "[[0, 1, 2, 3, 4, 4, 0, 1, 2, 3, 4, 4, 0, 0, 0]]";
    if (ad.get_numerical_features() != expected) {
        std::cout << "check for numerical features failed: " << ad.get_numerical_features() << " != " + expected
                  << std::endl;
        assert(0);
    }

    // no change
    expected = "[[aiku, brqu, gtyi, doax, fvjq, dwtx, eloh, gkji, ixdy, inid, yydc, wuqz, wjdo, zieg, vylf, wuih, "
               "rvjm, uwun, tawk, sydq]]";
    if (ad.get_categorical_features() != expected) {
        std::cout << "check for categorical features failed: " << ad.get_categorical_features() + " != " << expected
                  << std::endl;
        assert(0);
    }

    expected = "[[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,"
               " 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,"
               " 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,"
               " 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,"
               " 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,"
               " 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,"
               " 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,"
               " 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,"
               " 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,"
               " 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,"
               " 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,"
               " 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0,"
               " 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0,"
               " 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0,"
               " 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0,"
               " 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0,"
               " 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,"
               " 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0,"
               " 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,"
               " 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]]";

    if (ad.get_enc_features() != expected) {
        std::cout << "check for OHE features failed: " << ad.get_enc_features() << " != " << expected << std::endl;
        assert(0);
    }

    std::cout << "Test passed." << std::endl;

    snapml::DenseDataset dense_dataset = ad.convertToDenseDataset();

    const std::shared_ptr<glm::DenseDataset> dd = dense_dataset.get();
}

void test_pipeline_orig_ord()

{
    snapml::Pipeline p;
    std::string      expected;

    std::cout << "Testing whole pipeline based on a JSON file ==> Func, Norm, KBins, Ordinal" << std::endl;

    try {
        p.import("../test/data/pipeline_2.json");
    } catch (const std::exception& e) {
        std::cout << "Error importing pipeline information: " << e.what() << std::endl;
        assert(0);
    }

    snapml::DataSchema data_schema = p.get_schema();
    data_schema.enforce_byteswap   = is_enforce_byteswap(true);

    AnyDatasetTest ad(
        VCR("\003\000\000\000320\005\000\000\00030000\005\000\000\00060000\005\000\000\00090000"
            "\006\000\000\000120000\011\000\000\000999999840\002\000\000\00050\005\000\000\00030000"
            "\005\000\000\00060000\005\000\000\00090010\006\000\000\000120000\006\000\000\000515750"
            "\002\000\000\00080"
            "\022\000\000\00022025.465794806718\021\000\000\000485165194.4097903"
            "\004\000\000\000aiku\004\000\000\000brqu\004\000\000\000gtyi\004\000\000\000doax"
            "\004\000\000\000fvjq\004\000\000\000dwtx\004\000\000\000eloh\004\000\000\000gkji\004\000\000\000ixdy"
            "\004\000\000\000inid\004\000\000\000yydc\004\000\000\000wuqz\004\000\000\000wjdo\004\000\000\000zieg"
            "\004\000\000\000vylf\004\000\000\000wuih\004\000\000\000rvjm\004\000\000\000uwun\004\000\000\000tawk"
            "\004\000\000\000sydq"),
        data_schema);

    try {
        p.transform(ad);
    } catch (const std::exception& e) {
        std::cout << "Error running transformers: " << e.what() << std::endl;
        assert(0);
    }

    expected = "[[0, 1, 2, 3, 4, 4, 0, 1, 2, 3, 4, 4, 0, 0, 0]]";
    if (ad.get_numerical_features() != expected) {
        std::cout << "check for numerical features failed: " << ad.get_numerical_features() << " != " + expected
                  << std::endl;
        assert(0);
    }

    // no change
    expected = "[[aiku, brqu, gtyi, doax, fvjq, dwtx, eloh, gkji, ixdy, inid, yydc, wuqz, wjdo, zieg, vylf, wuih, "
               "rvjm, uwun, tawk, sydq]]";
    if (ad.get_categorical_features() != expected) {
        std::cout << "check for categorical features failed: " << ad.get_categorical_features() + " != " << expected
                  << std::endl;
        assert(0);
    }

    expected = "[[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 29, 28, 27, 26, 25, 24, "
               "23, 22, 21, 20]]";

    if (ad.get_enc_features() != expected) {
        std::cout << "check for ORDINAL features failed: " << ad.get_enc_features() << " != " << expected << std::endl;
        assert(0);
    }

    std::cout << "Test passed." << std::endl;

    snapml::DenseDataset dense_dataset = ad.convertToDenseDataset();

    const std::shared_ptr<glm::DenseDataset> dd = dense_dataset.get();
}

void test_pipeline_orig_target()

{
    snapml::Pipeline p;
    std::string      expected;

    std::cout << "Testing whole pipeline based on a JSON file ==> Func, Norm, KBins, Target" << std::endl;

    try {
        p.import("../test/data/pipeline_3.json");
    } catch (const std::exception& e) {
        std::cout << "Error importing pipeline information: " << e.what() << std::endl;
        assert(0);
    }

    snapml::DataSchema data_schema = p.get_schema();
    data_schema.enforce_byteswap   = is_enforce_byteswap(true);

    AnyDatasetTest ad(
        VCR("\003\000\000\000320\005\000\000\00030000\005\000\000\00060000\005\000\000\00090000"
            "\006\000\000\000120000\011\000\000\000999999840\002\000\000\00050\005\000\000\00030000"
            "\005\000\000\00060000\005\000\000\00090010\006\000\000\000120000\006\000\000\000515750"
            "\002\000\000\00080"
            "\022\000\000\00022025.465794806718\021\000\000\000485165194.4097903"
            "\004\000\000\000ased\004\000\000\000axpe\004\000\000\000bkoo\004\000\000\000ddnd"
            "\004\000\000\000dsej\004\000\000\000cqwz\004\000\000\000hfyy\004\000\000\000eefu\004\000\000\000frcq"
            "\004\000\000\000nlnj\004\000\000\000ogdv\004\000\000\000sglf\004\000\000\000twqm\004\000\000\000ttwq"
            "\004\000\000\000tusf\004\000\000\000xtzn\004\000\000\000vibs\004\000\000\000xphm\004\000\000\000wkqs"
            "\004\000\000\000yvfm"),
        data_schema);

    try {
        p.transform(ad);
    } catch (const std::exception& e) {
        std::cout << "Error running transformers: " << e.what() << std::endl;
        assert(0);
    }

    expected = "[[0, 1, 2, 3, 4, 4, 0, 1, 2, 3, 4, 4, 0, 0, 0]]";
    if (ad.get_numerical_features() != expected) {
        std::cout << "check for numerical features failed: " << ad.get_numerical_features() << " != " + expected
                  << std::endl;
        assert(0);
    }

    // no change
    expected = "[[ased, axpe, bkoo, ddnd, dsej, cqwz, hfyy, eefu, frcq, nlnj,"
               " ogdv, sglf, twqm, ttwq, tusf, xtzn, vibs, xphm, wkqs, yvfm]]";
    if (ad.get_categorical_features() != expected) {
        std::cout << "check for categorical features failed: " << ad.get_categorical_features() + " != " << expected
                  << std::endl;
        assert(0);
    }

    expected = "[[0.00748167, 0.0145646, 0.0281456, 0.0152864, 0.0193163,"
               " 0.0143048, 0.0200898, 0.00708461, 0.0238996, 0.0112575,"
               " 0.0223064, 0.0200898, 0.0144596, 0.0154633, 0.0102935,"
               " 0.0249027, 0.0116052, 0.0211321, 0.0263004, 0.0297062]]";

    if (ad.get_enc_features() != expected) {
        std::cout << "check for TARGET features failed: " << ad.get_enc_features() << " != " << expected << std::endl;
        assert(0);
    }

    std::cout << "Test passed." << std::endl;

    snapml::DenseDataset dense_dataset = ad.convertToDenseDataset();

    const std::shared_ptr<glm::DenseDataset> dd = dense_dataset.get();
}

void test_pipeline_orig_all()

{
    snapml::Pipeline p;
    std::string      expected;

    std::cout << "Testing whole pipeline based on a JSON file ==> Func, Norm, KBins, Ord, Target, OHE " << std::endl;

    try {
        p.import("../test/data/pipeline_all.json");
    } catch (const std::exception& e) {
        std::cout << "Error importing pipeline information: " << e.what() << std::endl;
        assert(0);
    }

    snapml::DataSchema data_schema = p.get_schema();
    data_schema.enforce_byteswap   = is_enforce_byteswap(true);

    AnyDatasetTest ad(VCR("\003\000\000\000320\005\000\000\00030000\005\000\000\00060000\005\000\000\00090000"
                          "\006\000\000\000120000\011\000\000\000999999840\002\000\000\00050\005\000\000\00030000\005"
                          "\000\000\00060000"
                          "\005\000\000\00090010\006\000\000\000120000\006\000\000\000515750\002\000\000\00080"
                          "\022\000\000\00022025.465794806718\021\000\000\000485165194.4097903"
                          "\004\000\000\000ajyz\004\000\000\000dmam\004\000\000\000fimx\004\000\000\000bkju"
                          "\004\000\000\000elol\004\000\000\000zksx\004\000\000\000xvvp\004\000\000\000yzsx"
                          "\004\000\000\000xfae\004\000\000\000ueca\004\000\000\000aeym\004\000\000\000cmnc"
                          "\004\000\000\000awzl\004\000\000\000bvdt\004\000\000\000cxgi\004\000\000\000gjju"
                          "\004\000\000\000zact\004\000\000\000ymih\004\000\000\000yoja\004\000\000\000wdxg"),
                      data_schema);

    try {
        p.transform(ad);
    } catch (const std::exception& e) {
        std::cout << "Error running transformers: " << e.what() << std::endl;
        assert(0);
    }

    expected = "[[0, 1, 2, 3, 4, 4, 0, 1, 2, 3, 4, 4, 0, 0, 0]]";
    if (ad.get_numerical_features() != expected) {
        std::cout << "check for numerical features failed: " << ad.get_numerical_features() << " != " + expected
                  << std::endl;
        assert(0);
    }

    // no change
    expected = "[[ajyz, dmam, fimx, bkju, elol, zksx, xvvp, yzsx, xfae, ueca,"
               " aeym, cmnc, awzl, bvdt, cxgi, gjju, zact, ymih, yoja, wdxg]]";
    if (ad.get_categorical_features() != expected) {
        std::cout << "check for categorical features failed: " << ad.get_categorical_features() + " != " << expected
                  << std::endl;
        assert(0);
    }

    expected = "[[0, 1, 2, 3, 4,"
               " 0.0207629, 0.0290524, 0.0210094, 0.0156412, 0.0329016,"
               " 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,"
               " 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,"
               " 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,"
               " 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,"
               " 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,"
               " 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,"
               " 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,"
               " 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0,"
               " 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0,"
               " 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]]";

    if (ad.get_enc_features() != expected) {
        std::cout << "check for Categorical features failed: " << ad.get_enc_features() << " != " << expected
                  << std::endl;
        assert(0);
    }

    std::cout << "Test passed." << std::endl;

    snapml::DenseDataset dense_dataset = ad.convertToDenseDataset();

    const std::shared_ptr<glm::DenseDataset> dd = dense_dataset.get();
}

// to compare with a Python pipline
void compare_pipeline(const std::string num_features, const std::string cat_features, const std::string result)
{
    std::stringstream sstr;
    sstr << R"(
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import Normalizer, OneHotEncoder, KBinsDiscretizer
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import FunctionTransformer
import warnings
warnings.filterwarnings('ignore')

# create an empty data frame with given column types
def df_empty(columns, dtypes, index=None):
    assert len(columns)==len(dtypes)
    df = pd.DataFrame(index=index)
    for c,d in zip(columns, dtypes):
        df[c] = pd.Series(dtype=d)
    return df

if __name__ == '__main__':
    # first element: just because of the AnyDatasetTest::get_final_features()
    # function that produces a 2d vector for AnyDatasetTest::to_string()
    result = np.array()"
         << result << R"().astype(float)[0]
    # number of samples in the dataset
    n_samples = 4

    # number of unique categories per feature 
    cat_per_feat = 20

    xnum_train = np.array()"
         << num_features << R"()
    xcat_train = np.array()"
         << cat_features << R"()
    n_num_feats = len(xnum_train[0])
    n_cat_feats = len(xcat_train[0])

    # ---------- Pipeline (preprocessing) generation step ---------- #

    colnames  = []
    num_feats = []
    coltypes  = []
    cat_feats = []

    for i in range(n_num_feats):
        colnames.append('num'+str(i))
        num_feats.append('num'+str(i))
        coltypes.append(np.float32)

    for i in range(n_cat_feats):
        colnames.append('cat'+str(i))
        cat_feats.append('cat'+str(i))
        coltypes.append(str)

    # aggregate all the numerical and categorical data into a single dataframe 
    df_train = df_empty(colnames, dtypes=coltypes)
    df_train.iloc[:,0:n_num_feats] = pd.DataFrame(xnum_train)
    df_train.iloc[:,n_num_feats:]  = pd.DataFrame(xcat_train)

    # Create the preprocessing steps as Pipelines
    num_transformer = Pipeline(steps=[('normalizer', Normalizer()), ('discretizer', KBinsDiscretizer(encode="ordinal"))])
    cat_transformer = Pipeline(steps=[('onehot', OneHotEncoder(categories='auto', sparse_output=False, handle_unknown='ignore'))])

    # Create the ColumnTransformer based on the transfomers above
    preprocessor = ColumnTransformer(transformers=[('num_trans', num_transformer, num_feats), ('encoding_trans', cat_transformer, cat_feats)])

    # Create the pipeline
    pipeline = Pipeline(steps=[ ('preprocessor', preprocessor)])
    pipeline.fit(df_train)

    # Transform the data
    expected = pipeline['preprocessor'].transform(df_train).flatten()
	
    if np.allclose(result, expected) == False:
        raise Exception('result ' + str(result) + ' does not match the expected ' + str(expected))
)";

    if (PyRun_SimpleString(sstr.str().c_str())) {
        std::cout << "comparison to scikit-learn failed for Pipeline" << std::endl;
        assert(0);
    } else {
        std::cout << "comparison to scikit-learn succeeded for Pipeline" << std::endl << std::endl;
    }
}

// compare with a Python pipeline - Ordinal Encoder for categorical data
void compare_pipeline_o(const std::string num_features, const std::string cat_features, const std::string result)
{
    std::stringstream sstr;
    sstr << R"(
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import Normalizer, OrdinalEncoder, KBinsDiscretizer
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import FunctionTransformer
import warnings
warnings.filterwarnings('ignore')

# create an empty data frame with given column types
def df_empty(columns, dtypes, index=None):
    assert len(columns)==len(dtypes)
    df = pd.DataFrame(index=index)
    for c,d in zip(columns, dtypes):
        df[c] = pd.Series(dtype=d)
    return df

if __name__ == '__main__':
    # first element: just because of the AnyDatasetTest::get_final_features()
    # function that produces a 2d vector for AnyDatasetTest::to_string()
    result = np.array()"
         << result << R"().astype(float)[0]
    # number of samples in the dataset
    n_samples = 4

    # number of unique categories per feature 
    cat_per_feat = 20

    xnum_train = np.array()"
         << num_features << R"()
    xcat_train = np.array()"
         << cat_features << R"()
    n_num_feats = len(xnum_train[0])
    n_cat_feats = len(xcat_train[0])

    # ---------- Pipeline (preprocessing) generation step ---------- #

    colnames  = []
    num_feats = []
    coltypes  = []
    cat_feats = []

    for i in range(n_num_feats):
        colnames.append('num'+str(i))
        num_feats.append('num'+str(i))
        coltypes.append(np.float32)

    for i in range(n_cat_feats):
        colnames.append('cat'+str(i))
        cat_feats.append('cat'+str(i))
        coltypes.append(str)

    # aggregate all the numerical and categorical data into a single dataframe 
    df_train = df_empty(colnames, dtypes=coltypes)
    df_train.iloc[:,0:n_num_feats] = pd.DataFrame(xnum_train)
    df_train.iloc[:,n_num_feats:]  = pd.DataFrame(xcat_train)

    # Create the preprocessing steps as Pipelines
    num_transformer = Pipeline(steps=[('normalizer', Normalizer()), ('discretizer', KBinsDiscretizer(encode="ordinal"))])
    cat_transformer = Pipeline(steps=[('ordinal', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1))])

    # Create the ColumnTransformer based on the transfomers above
    preprocessor = ColumnTransformer(transformers=[('num_trans', num_transformer, num_feats), ('encoding_trans', cat_transformer, cat_feats)])

    # Create the pipeline
    pipeline = Pipeline(steps=[ ('preprocessor', preprocessor)])
    pipeline.fit(df_train)

    # Transform the data
    expected = pipeline['preprocessor'].transform(df_train).flatten()
	
    if np.allclose(result, expected) == False:
        raise Exception('result ' + str(result) + ' does not match the expected ' + str(expected))
)";

    if (PyRun_SimpleString(sstr.str().c_str())) {
        std::cout << "comparison to scikit-learn failed for Pipeline" << std::endl;
        assert(0);
    } else {
        std::cout << "comparison to scikit-learn succeeded for Pipeline" << std::endl << std::endl;
    }
}

// compare with a Python pipeline - OHE + Ordinal Encoder for categorical data
void compare_pipeline_oo(const std::string num_features, const std::string cat_features, const std::string result)
{
    std::stringstream sstr;
    sstr << R"(
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import Normalizer, OrdinalEncoder, OneHotEncoder, KBinsDiscretizer
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import FunctionTransformer
import warnings
warnings.filterwarnings('ignore')

# create an empty data frame with given column types
def df_empty(columns, dtypes, index=None):
    assert len(columns)==len(dtypes)
    df = pd.DataFrame(index=index)
    for c,d in zip(columns, dtypes):
        df[c] = pd.Series(dtype=d)
    return df

if __name__ == '__main__':
    # first element: just because of the AnyDatasetTest::get_final_features()
    # function that produces a 2d vector for AnyDatasetTest::to_string()
    result = np.array()"
         << result << R"().astype(float)[0]
    # number of samples in the dataset
    n_samples = 4

    # number of unique categories per feature 
    cat_per_feat = 20

    xnum_train = np.array()"
         << num_features << R"()
    xcat_train = np.array()"
         << cat_features << R"()
    n_num_feats = len(xnum_train[0])
    n_cat_feats = len(xcat_train[0])
    n_cat_feats_ohe = int(n_cat_feats/2)
    n_cat_feats_ord = n_cat_feats - n_cat_feats_ohe

    # ---------- Pipeline (preprocessing) generation step ---------- #

    colnames  = []
    num_feats = []
    coltypes  = []
    cat_feats_ohe = []
    cat_feats_ord = []

    for i in range(n_num_feats):
        colnames.append('num'+str(i))
        num_feats.append('num'+str(i))
        coltypes.append(np.float32)

    for i in range(n_cat_feats_ohe):
        colnames.append('cat'+str(i))
        cat_feats_ohe.append('cat'+str(i))
        coltypes.append(str)

    for i in range(n_cat_feats_ord):
        colnames.append('cat'+str(i+n_cat_feats_ohe))
        cat_feats_ord.append('cat'+str(i+n_cat_feats_ohe))
        coltypes.append(str)

    # aggregate all the numerical and categorical data into a single dataframe 
    df_train = df_empty(colnames, dtypes=coltypes)
    df_train.iloc[:,0:n_num_feats] = pd.DataFrame(xnum_train)
    df_train.iloc[:,n_num_feats:]  = pd.DataFrame(xcat_train)

    # Create the preprocessing steps as Pipelines
    num_transformer = Pipeline(steps=[('normalizer', Normalizer()), ('discretizer', KBinsDiscretizer(encode="ordinal"))])
    cat_transformer_ord = Pipeline(steps=[('ordinal', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1))])
    cat_transformer_ohe = Pipeline(steps=[('onehot', OneHotEncoder(categories='auto', sparse_output=False, handle_unknown='ignore'))])

    # Create the ColumnTransformer based on the transfomers above
    preprocessor = ColumnTransformer(transformers=[('num_trans', num_transformer, num_feats), ('ohe_encoding_trans', cat_transformer_ohe, cat_feats_ohe), ('ord_encoding_trans', cat_transformer_ord, cat_feats_ord)])

    # Create the pipeline
    pipeline = Pipeline(steps=[ ('preprocessor', preprocessor)])
    pipeline.fit(df_train)

    # Transform the data
    expected = pipeline['preprocessor'].transform(df_train).flatten()
	
    if np.allclose(result, expected) == False:
        raise Exception('result ' + str(result) + ' does not match the expected ' + str(expected))
)";

    if (PyRun_SimpleString(sstr.str().c_str())) {
        std::cout << "comparison to scikit-learn failed for Pipeline" << std::endl;
        assert(0);
    } else {
        std::cout << "comparison to scikit-learn succeeded for Pipeline" << std::endl << std::endl;
    }
}

// compare with a Python pipeline - Target Encoder for categorical data
void compare_pipeline_t(const std::string num_features, const std::string cat_features, const std::string encodings,
                        float target_mean, const std::string result)
{
    std::stringstream sstr;
    sstr << R"(

import sklearn.preprocessing

if 'TargetEncoder' in sklearn.preprocessing.__dict__:

	from sklearn.model_selection import train_test_split
	from sklearn.preprocessing import Normalizer, TargetEncoder, KBinsDiscretizer
	import numpy as np
	import pandas as pd
	from sklearn.pipeline import Pipeline
	from sklearn.compose import ColumnTransformer
	from sklearn.preprocessing import FunctionTransformer
	import warnings
	warnings.filterwarnings('ignore')
	
	# create an empty data frame with given column types
	def df_empty(columns, dtypes, index=None):
		assert len(columns)==len(dtypes)
		df = pd.DataFrame(index=index)
		for c,d in zip(columns, dtypes):
			df[c] = pd.Series(dtype=d)
		return df
	
	if __name__ == '__main__':
		# first element: just because of the AnyDatasetTest::get_final_features()
		# function that produces a 2d vector for AnyDatasetTest::to_string()
		result = np.array()"
         << result << R"().astype(float)[0]
		encodings = )"
         << encodings << R"(
		target_mean = )"
         << target_mean << R"(
		# number of samples in the dataset
		n_samples = 3
	
		# number of unique categories per feature 
		cat_per_feat = 20
	
		xnum_train = np.array()"
         << num_features << R"()
		xcat_train = np.array()"
         << cat_features << R"()
		n_num_feats = len(xnum_train[0])
		n_cat_feats = len(xcat_train[0])
	
		# ---------- Pipeline (preprocessing) generation step ---------- #
	
		colnames  = []
		num_feats = []
		coltypes  = []
		cat_feats = []
	
		for i in range(n_num_feats):
			colnames.append('num'+str(i))
			num_feats.append('num'+str(i))
			coltypes.append(np.float32)
	
		for i in range(n_cat_feats):
			colnames.append('cat'+str(i))
			cat_feats.append('cat'+str(i))
			coltypes.append(str)
	
		# aggregate all the numerical and categorical data into a single dataframe 
		df_train = df_empty(colnames, dtypes=coltypes)
		df_train.iloc[:,0:n_num_feats] = pd.DataFrame(xnum_train)
		df_train.iloc[:,n_num_feats:]  = pd.DataFrame(xcat_train)
		y_train = np.random.choice(2, n_samples, p=[0.98, 0.02])
	
		# Create the preprocessing steps as Pipelines
		num_transformer = Pipeline(steps=[('normalizer', Normalizer()), ('discretizer', KBinsDiscretizer(encode="ordinal"))])
		cat_transformer = Pipeline(steps=[('target', TargetEncoder(categories='auto', cv=2))])
	
		# Create the ColumnTransformer based on the transfomers above
		preprocessor = ColumnTransformer(transformers=[('num_trans', num_transformer, num_feats), ('encoding_trans', cat_transformer, cat_feats)])
	
		# Create the pipeline
		pipeline = Pipeline(steps=[ ('preprocessor', preprocessor)])
		pipeline.fit(df_train, y_train)
	
		pipeline["preprocessor"].transformers_[1][1].steps[0][1].encodings_ = np.array(encodings)
		pipeline["preprocessor"].transformers_[1][1].steps[0][1].target_mean_ = target_mean
	 
		# Transform the data
		expected = pipeline['preprocessor'].transform(df_train).flatten()
		
		if np.allclose(result, expected) == False:
			raise Exception('result ' + str(result) + ' does not match the expected ' + str(expected))
)";

    if (PyRun_SimpleString(sstr.str().c_str())) {
        std::cout << "comparison to scikit-learn failed for Pipeline" << std::endl;
        assert(0);
    } else {
        std::cout << "Test succeeded for Pipeline" << std::endl << std::endl;
    }
}

// compare with a Python pipeline - OHE + Target Encoder for categorical data
void compare_pipeline_ot(const std::string num_features, const std::string cat_features, const std::string encodings,
                         float target_mean, const std::string result)
{
    std::stringstream sstr;
    sstr << R"(
import sklearn.preprocessing

if 'TargetEncoder' in sklearn.preprocessing.__dict__:

	from sklearn.model_selection import train_test_split
	from sklearn.preprocessing import Normalizer, TargetEncoder, OneHotEncoder, KBinsDiscretizer
	import numpy as np
	import pandas as pd
	from sklearn.pipeline import Pipeline
	from sklearn.compose import ColumnTransformer
	from sklearn.preprocessing import FunctionTransformer
	import warnings
	warnings.filterwarnings('ignore')
	
	# create an empty data frame with given column types
	def df_empty(columns, dtypes, index=None):
		assert len(columns)==len(dtypes)
		df = pd.DataFrame(index=index)
		for c,d in zip(columns, dtypes):
			df[c] = pd.Series(dtype=d)
		return df
	
	if __name__ == '__main__':
		# first element: just because of the AnyDatasetTest::get_final_features()
		# function that produces a 2d vector for AnyDatasetTest::to_string()
		result = np.array()"
         << result << R"().astype(float)[0]
		encodings = )"
         << encodings << R"(
		target_mean = )"
         << target_mean << R"(
		# number of samples in the dataset
		n_samples = 3
	
		# number of unique categories per feature 
		cat_per_feat = 20
	
		xnum_train = np.array()"
         << num_features << R"()
		xcat_train = np.array()"
         << cat_features << R"()
		n_num_feats = len(xnum_train[0])
		n_cat_feats = len(xcat_train[0])
		n_cat_feats_ohe = int(n_cat_feats/2)
		n_cat_feats_trg = n_cat_feats - n_cat_feats_ohe
	
		# ---------- Pipeline (preprocessing) generation step ---------- #
	
		colnames  = []
		num_feats = []
		coltypes  = []
		cat_feats_ohe = []
		cat_feats_trg = []
	
		for i in range(n_num_feats):
			colnames.append('num'+str(i))
			num_feats.append('num'+str(i))
			coltypes.append(np.float32)
	
		for i in range(n_cat_feats_ohe):
			colnames.append('cat'+str(i))
			cat_feats_ohe.append('cat'+str(i))
			coltypes.append(str)
	
		for i in range(n_cat_feats_trg):
			colnames.append('cat'+str(i+n_cat_feats_ohe))
			cat_feats_trg.append('cat'+str(i+n_cat_feats_ohe))
			coltypes.append(str)
	
		# aggregate all the numerical and categorical data into a single dataframe 
		df_train = df_empty(colnames, dtypes=coltypes)
		df_train.iloc[:,0:n_num_feats] = pd.DataFrame(xnum_train)
		df_train.iloc[:,n_num_feats:]  = pd.DataFrame(xcat_train)
		y_train = np.random.choice(2, n_samples, p=[0.98, 0.02])
	
		# Create the preprocessing steps as Pipelines
		num_transformer = Pipeline(steps=[('normalizer', Normalizer()), ('discretizer', KBinsDiscretizer(encode="ordinal"))])
		cat_transformer_trg = Pipeline(steps=[('target', TargetEncoder(categories='auto', cv=2))])
		cat_transformer_ohe = Pipeline(steps=[('onehot', OneHotEncoder(categories='auto', sparse_output=False, handle_unknown='ignore'))])
	
		# Create the ColumnTransformer based on the transfomers above
		preprocessor = ColumnTransformer(transformers=[('num_trans', num_transformer, num_feats), ('ohe_encoding_trans', cat_transformer_ohe, cat_feats_ohe), ('trg_encoding_trans', cat_transformer_trg, cat_feats_trg)])
	
		# Create the pipeline
		pipeline = Pipeline(steps=[ ('preprocessor', preprocessor)])
		pipeline.fit(df_train, y_train)
	
		pipeline["preprocessor"].transformers_[2][1].steps[0][1].encodings_ = np.array(encodings)
		pipeline["preprocessor"].transformers_[2][1].steps[0][1].target_mean_ = target_mean
	
		# Transform the data
		expected = pipeline['preprocessor'].transform(df_train).flatten()
		
		if np.allclose(result, expected) == False:
			raise Exception('result ' + str(result) + ' does not match the expected ' + str(expected))
)";

    if (PyRun_SimpleString(sstr.str().c_str())) {
        std::cout << "comparison to scikit-learn failed for Pipeline" << std::endl;
        assert(0);
    } else {
        std::cout << "Test succeeded for Pipeline" << std::endl << std::endl;
    }
}

const std::string data_schema_1 = snapml::JSON_STRING + R"(
{
    "data_schema": {
        "num_indices": [
            0,
            1,
            2
        ],
        "cat_indices": [
            3,
            4,
            5,
            6
        ]
    },
    "transformers": {
        "transformer1": [
            {
                "type": "Normalizer",
                "params": {
                    "copy": true,
                    "norm": "l2"
                },
                "data": {},
                "columns": [
                    0,
                    1,
                    2
                ]
            },
            {
                "type": "KBinsDiscretizer",
                "params": {
                    "dtype": null,
                    "encode": "ordinal",
                    "n_bins": 5,
                    "random_state": null,
                    "strategy": "quantile",
                    "subsample": "warn"
                },
                "data": {
                    "bin_edges": [
                        [
                            0.47309933875093857,
                            0.5094161343269863,
                            0.5457329299030341,
                            0.5986126693954231,
                            0.6680553528041535,
                            0.7374980362128838
                        ],
                        [
                            0.09922345624712578,
                            0.13210883244984142,
                            0.16499420865255707,
                            0.31635419515571106,
                            0.5861887919593036,
                            0.856023388762896
                        ],
                        [
                            0.2083290031760162,
                            0.38520571816885263,
                            0.5620824331616892,
                            0.6843899567332227,
                            0.7521282888834534,
                            0.8198666210336841
                        ]
                    ]
                },
                "columns": [
                    0,
                    1,
                    2
                ]
            }
        ],
        "transformer2": [
            {
                "type": "OneHotEncoder",
                "params": {
                    "categories": "auto",
                    "drop": null,
                    "dtype": "float64",
                    "feature_name_combiner": "concat",
                    "handle_unknown": "ignore",
                    "max_categories": null,
                    "min_frequency": null,
                    "sparse_output": false
                },
                "data": {
                    "categories": [
                        [
                            "aelg",    
                            "lvci",
                            "ppgt"
                        ],
                        [
                            "bbnd",
                            "ophn",
                            "xate"
                        ],
                        [
                            "uezy",
                            "xhoo",
                            "xswz"
                        ],
                        [
                            "brbm",
                            "dmkj",
                            "nvfv"
                        ]
                    ]
                },
                "columns": [
                    3,
                    4,
                    5,
                    6
                ]
            }
        ]
    },
    "remainder": "passthrough"
}
)";

const std::string data_schema_2 = snapml::JSON_STRING + R"(
{
    "data_schema": {
        "num_indices": [
            0,
            1,
            2
        ],
        "cat_indices": [
            3,
            4,
            5,
            6
        ]
    },
    "transformers": {
        "transformer1": [
            {
                "type": "Normalizer",
                "params": {
                    "copy": true,
                    "norm": "l2"
                },
                "data": {},
                "columns": [
                    0,
                    1,
                    2
                ]
            },
            {
                "type": "KBinsDiscretizer",
                "params": {
                    "dtype": null,
                    "encode": "ordinal",
                    "n_bins": 5,
                    "random_state": null,
                    "strategy": "quantile",
                    "subsample": "warn"
                },
                "data": {
                    "bin_edges": [
                        [
                            0.3246094865261828,
                            0.3898583976830521,
                            0.4551073088399214,
                            0.5057631434141221,
                            0.5418259014056543,
                            0.5778886593971866
                        ],
                        [
                            0.016072176390513435,
                            0.059819899055370454,
                            0.10356762172022747,
                            0.22055948009635104,
                            0.4107954741837413,
                            0.6010314682711314
                        ],
                        [
                            0.5520922671872612,
                            0.6803935933658978,
                            0.8086949195445343,
                            0.8857750650977687,
                            0.9116340300256011,
                            0.9374929949534333
                        ]
                    ]
                },
                "columns": [
                    0,
                    1,
                    2
                ]
            }
        ],
        "transformer2": [
            {
                "type": "OneHotEncoder",
                "params": {
                    "categories": "auto",
                    "drop": null,
                    "dtype": "float64",
                    "feature_name_combiner": "concat",
                    "handle_unknown": "ignore",
                    "max_categories": null,
                    "min_frequency": null,
                    "sparse_output": false
                },
                "data": {
                    "categories": [
                        [
                            "jdbk",
                            "kgfg"
                        ],
                        [
                            "eecw",
                            "hvcs"
                        ],
                        [
                            "aawt",
                            "dcks"
                        ],
                        [
                            "nekw",
                            "rrkh"
                        ]
                    ]
                },
                "columns": [
                    3,
                    4,
                    5,
                    6
                ]
            }
        ]
    },
    "remainder": "passthrough"
}
)";

const std::string data_schema_3 = snapml::JSON_STRING + R"(
{
    "data_schema": {
        "num_indices": [
            0,
            1,
            2
        ],
        "cat_indices": [
            3,
            4,
            5,
            6
        ]
    },
    "transformers": {
        "transformer1": [
            {
                "type": "Normalizer",
                "params": {
                    "copy": true,
                    "norm": "l2"
                },
                "data": {},
                "columns": [
                    0,
                    1,
                    2
                ]
            },
            {
                "type": "KBinsDiscretizer",
                "params": {
                    "dtype": null,
                    "encode": "ordinal",
                    "n_bins": 5,
                    "random_state": null,
                    "strategy": "quantile",
                    "subsample": "warn"
                },
                "data": {
                    "bin_edges": [
                        [
                            0.2837140844168808,
                            0.356849981596399,
                            0.4299858787759172,
                            0.5093957190154785,
                            0.5950795023150829,
                            0.6807632856146872
                        ],
                        [
                            0.6408865038699008,
                            0.6488601260168705,
                            0.6568337481638402,
                            0.6664824153456518,
                            0.6778061275623051,
                            0.6891298397789584
                        ],
                        [
                            0.31603407640374015,
                            0.4114050585083769,
                            0.5067760406130136,
                            0.5862255686838188,
                            0.6497536427207926,
                            0.7132817167577664
                        ]
                    ]
                },
                "columns": [
                    0,
                    1,
                    2
                ]
            }
        ],
        "transformer2": [
            {
                "type": "OneHotEncoder",
                "params": {
                    "categories": "auto",
                    "drop": null,
                    "dtype": "float64",
                    "feature_name_combiner": "concat",
                    "handle_unknown": "ignore",
                    "max_categories": null,
                    "min_frequency": null,
                    "sparse_output": false
                },
                "data": {
                    "categories": [
                        [
                            "vgug",
                            "xcyx"
                        ],
                        [
                            "auhm",
                            "nxsd"
                        ],
                        [
                            "aggj",
                            "vjzs"
                        ],
                        [
                            "hfvc",
                            "tbjh"
                        ]
                    ]
                },
                "columns": [
                    3,
                    4,
                    5,
                    6
                ]
            }
        ]
    },
    "remainder": "passthrough"
}
)";

const std::string data_schema_4 = snapml::JSON_STRING + R"(
{
    "data_schema": {
        "num_indices": [
            0,
            1,
            2
        ],
        "cat_indices": [
            3,
            4,
            5,
            6
        ]
    },
    "transformers": {
        "transformer1": [
            {
                "type": "Normalizer",
                "params": {
                    "copy": true,
                    "norm": "l2"
                },
                "data": {},
                "columns": [
                    0,
                    1,
                    2
                ]
            },
            {
                "type": "KBinsDiscretizer",
                "params": {
                    "dtype": null,
                    "encode": "ordinal",
                    "n_bins": 5,
                    "random_state": null,
                    "strategy": "quantile",
                    "subsample": "warn"
                },
                "data": {
                    "bin_edges": [
                        [
                            0.45601948135128145,
                            0.589716143605117,
                            0.7234128058589525,
                            0.7956956545545705,
                            0.8065646896919709,
                            0.8174337248293714
                        ],
                        [
                            0.011292858968814752,
                            0.2206973582208546,
                            0.4301018574728944,
                            0.5430156124368152,
                            0.5594386231126167,
                            0.5758616337884184
                        ],
                        [
                            0.013619259969364543,
                            0.12781897293655858,
                            0.24201868590375258,
                            0.41727446240307753,
                            0.6535863024345336,
                            0.8898981424659895
                        ]
                    ]
                },
                "columns": [
                    0,
                    1,
                    2
                ]
            }
        ],
        "transformer2": [
            {
                "type": "OneHotEncoder",
                "params": {
                    "categories": "auto",
                    "drop": null,
                    "dtype": "float64",
                    "feature_name_combiner": "concat",
                    "handle_unknown": "ignore",
                    "max_categories": null,
                    "min_frequency": null,
                    "sparse_output": false
                },
                "data": {
                    "categories": [
                        [
                            "aewa",
                            "qdrp"
                        ],
                        [
                            "eppq",
                            "uhge"
                        ],
                        [
                            "ojvu",
                            "wwtz"
                        ],
                        [
                            "ggzh",
                            "jtsr"
                        ]
                    ]
                },
                "columns": [
                    3,
                    4,
                    5,
                    6
                ]
            }
        ]
    },
    "remainder": "passthrough"
}
)";

const std::string data_schema_o = snapml::JSON_STRING + R"(
{
    "data_schema": {
        "num_indices": [
            0,
            1,
            2
        ],
        "cat_indices": [
            3,
            4,
            5,
            6
        ]
    },
    "transformers": {
        "transformer1": [
            {
                "type": "Normalizer",
                "params": {
                    "copy": true,
                    "norm": "l2"
                },
                "data": {},
                "columns": [
                    0,
                    1,
                    2
                ]
            },
            {
                "type": "KBinsDiscretizer",
                "params": {
                    "dtype": null,
                    "encode": "ordinal",
                    "n_bins": 5,
                    "random_state": null,
                    "strategy": "quantile",
                    "subsample": "warn"
                },
                "data": {
                    "bin_edges": [
                        [
                            0.47309933875093857,
                            0.5094161343269863,
                            0.5457329299030341,
                            0.5986126693954231,
                            0.6680553528041535,
                            0.7374980362128838
                        ],
                        [
                            0.09922345624712578,
                            0.13210883244984142,
                            0.16499420865255707,
                            0.31635419515571106,
                            0.5861887919593036,
                            0.856023388762896
                        ],
                        [
                            0.2083290031760162,
                            0.38520571816885263,
                            0.5620824331616892,
                            0.6843899567332227,
                            0.7521282888834534,
                            0.8198666210336841
                        ]
                    ]
                },
                "columns": [
                    0,
                    1,
                    2
                ]
            }
        ],
        "transformer2": [
            {
                "type": "OrdinalEncoder",
                "params": {
                    "categories": "auto",
                    "dtype": "float64",
                    "handle_unknown": "use_encoded_value",
                    "unknown_value": -1        
                },
                "data": {
                    "categories": [
                        [
                            "aelg",    
                            "lvci",
                            "ppgt"
                        ],
                        [
                            "bbnd",
                            "ophn",
                            "xate"
                        ],
                        [
                            "uezy",
                            "xhoo",
                            "xswz"
                        ],
                        [
                            "brbm",
                            "dmkj",
                            "nvfv"
                        ]
                    ]
                },
                "columns": [
                    3,
                    4,
                    5,
                    6
                ]
            }
        ]
    },
    "remainder": "passthrough"
}
)";

const std::string data_schema_oo = snapml::JSON_STRING + R"(
{
    "data_schema": {
        "num_indices": [
            0,
            1,
            2
        ],
        "cat_indices": [
            3,
            4,
            5,
            6
        ]
    },
    "transformers": {
        "transformer1": [
            {
                "type": "Normalizer",
                "params": {
                    "copy": true,
                    "norm": "l2"
                },
                "data": {},
                "columns": [
                    0,
                    1,
                    2
                ]
            },
            {
                "type": "KBinsDiscretizer",
                "params": {
                    "dtype": null,
                    "encode": "ordinal",
                    "n_bins": 5,
                    "random_state": null,
                    "strategy": "quantile",
                    "subsample": "warn"
                },
                "data": {
                    "bin_edges": [
                        [
                            0.47309933875093857,
                            0.5094161343269863,
                            0.5457329299030341,
                            0.5986126693954231,
                            0.6680553528041535,
                            0.7374980362128838
                        ],
                        [
                            0.09922345624712578,
                            0.13210883244984142,
                            0.16499420865255707,
                            0.31635419515571106,
                            0.5861887919593036,
                            0.856023388762896
                        ],
                        [
                            0.2083290031760162,
                            0.38520571816885263,
                            0.5620824331616892,
                            0.6843899567332227,
                            0.7521282888834534,
                            0.8198666210336841
                        ]
                    ]
                },
                "columns": [
                    0,
                    1,
                    2
                ]
            }
        ],
        "transformer2": [
            {
                "type": "OneHotEncoder",
                "params": {
                    "categories": "auto",
                    "drop": null,
                    "dtype": "float64",
                    "feature_name_combiner": "concat",
                    "handle_unknown": "ignore",
                    "max_categories": null,
                    "min_frequency": null,
                    "sparse_output": false
                },
                "data": {
                    "categories": [
                        [
                            "aelg",    
                            "lvci",
                            "ppgt"
                        ],
                        [
                            "bbnd",
                            "ophn",
                            "xate"
                        ]
                    ]
                },
                "columns": [
                    3,
                    4
                ]
            }
        ],
        "transformer3": [
            {
                "type": "OrdinalEncoder",
                "params": {
                    "categories": "auto",
                    "dtype": "float64",
                    "handle_unknown": "use_encoded_value",
                    "unknown_value": -1        
                },
                "data": {
                    "categories": [
                        [
                            "uezy",
                            "xhoo",
                            "xswz"
                        ],
                        [
                            "brbm",
                            "dmkj",
                            "nvfv"
                        ]
                    ]
                },
                "columns": [
                    5,
                    6
                ]
            }
        ]
    },
    "remainder": "passthrough"
}
)";

const std::string data_schema_t = snapml::JSON_STRING + R"(
{
    "data_schema": {
        "num_indices": [
            0,
            1,
            2
        ],
        "cat_indices": [
            3,
            4,
            5,
            6
        ]
    },
    "transformers": {
        "transformer1": [
            {
                "type": "Normalizer",
                "params": {
                    "copy": true,
                    "norm": "l2"
                },
                "data": {},
                "columns": [
                    0,
                    1,
                    2
                ]
            },
            {
                "type": "KBinsDiscretizer",
                "params": {
                    "dtype": null,
                    "encode": "ordinal",
                    "n_bins": 5,
                    "random_state": null,
                    "strategy": "quantile",
                    "subsample": "warn"
                },
                "data": {
                    "bin_edges": [
                        [
                            0.47309933875093857,
                            0.5094161343269863,
                            0.5457329299030341,
                            0.5986126693954231,
                            0.6680553528041535,
                            0.7374980362128838
                        ],
                        [
                            0.09922345624712578,
                            0.13210883244984142,
                            0.16499420865255707,
                            0.31635419515571106,
                            0.5861887919593036,
                            0.856023388762896
                        ],
                        [
                            0.2083290031760162,
                            0.38520571816885263,
                            0.5620824331616892,
                            0.6843899567332227,
                            0.7521282888834534,
                            0.8198666210336841
                        ]
                    ]
                },
                "columns": [
                    0,
                    1,
                    2
                ]
            }
        ],
        "transformer2": [
            {
                "type": "TargetEncoder",
                "params": {
                    "categories": "auto",
                    "cv": 5,
                    "random_state": null,
                    "shuffle": true,
                    "smooth": "auto",
                    "target_type": "continuous"  
                },
                "data": {
                    "categories": [
                        [
                            "aelg",    
                            "lvci",
                            "ppgt"
                        ],
                        [
                            "bbnd",
                            "ophn",
                            "xate"
                        ],
                        [
                            "uezy",
                            "xhoo",
                            "xswz"
                        ],
                        [
                            "brbm",
                            "dmkj",
                            "nvfv"
                        ]
                    ],
                    "encodings": [
                        [
                            0.007,
                            0.023,
                            0.036
                        ],
                        [
                            0.022,
                            0.014,
                            0.026
                        ],
                        [
                            0.037,
                            0.011,
                            0.021
                        ],
                        [
                            0.035,
                            0.015,
                            0.024
                        ]
                    ],
					"target_mean": 0.02275
                },
                "columns": [
                    3,
                    4,
                    5,
                    6
                ]
            }
        ]
    },
    "remainder": "passthrough"
}
)";

const std::string data_schema_ot = snapml::JSON_STRING + R"(
{
    "data_schema": {
        "num_indices": [
            0,
            1,
            2
        ],
        "cat_indices": [
            3,
            4,
            5,
            6
        ]
    },
    "transformers": {
        "transformer1": [
            {
                "type": "Normalizer",
                "params": {
                    "copy": true,
                    "norm": "l2"
                },
                "data": {},
                "columns": [
                    0,
                    1,
                    2
                ]
            },
            {
                "type": "KBinsDiscretizer",
                "params": {
                    "dtype": null,
                    "encode": "ordinal",
                    "n_bins": 5,
                    "random_state": null,
                    "strategy": "quantile",
                    "subsample": "warn"
                },
                "data": {
                    "bin_edges": [
                        [
                            0.47309933875093857,
                            0.5094161343269863,
                            0.5457329299030341,
                            0.5986126693954231,
                            0.6680553528041535,
                            0.7374980362128838
                        ],
                        [
                            0.09922345624712578,
                            0.13210883244984142,
                            0.16499420865255707,
                            0.31635419515571106,
                            0.5861887919593036,
                            0.856023388762896
                        ],
                        [
                            0.2083290031760162,
                            0.38520571816885263,
                            0.5620824331616892,
                            0.6843899567332227,
                            0.7521282888834534,
                            0.8198666210336841
                        ]
                    ]
                },
                "columns": [
                    0,
                    1,
                    2
                ]
            }
        ],
        "transformer2": [
            {
                "type": "OneHotEncoder",
                "params": {
                    "categories": "auto",
                    "drop": null,
                    "dtype": "float64",
                    "feature_name_combiner": "concat",
                    "handle_unknown": "ignore",
                    "max_categories": null,
                    "min_frequency": null,
                    "sparse_output": false
                },
                "data": {
                    "categories": [
                        [
                            "aelg",    
                            "lvci",
                            "ppgt"
                        ],
                        [
                            "bbnd",
                            "ophn",
                            "xate"
                        ]
                    ]
                },
                "columns": [
                    3,
                    4
                ]
            }
        ],
        "transformer3": [
            {
                "type": "TargetEncoder",
                "params": {
                    "categories": "auto",
                    "cv": 5,
                    "random_state": null,
                    "shuffle": true,
                    "smooth": "auto",
                    "target_type": "continuous"  
                },
                "data": {
                    "categories": [
                        [
                            "uezy",
                            "xhoo",
                            "xswz"
                        ],
                        [
                            "brbm",
                            "dmkj",
                            "nvfv"
                        ]
                    ],
                    "encodings": [
                        [
                            0.037,
                            0.011,
                            0.021
                        ],
                        [
                            0.035,
                            0.015,
                            0.024
                        ]
                    ],
					"target_mean": 0.02275
                },
                "columns": [
                    5,
                    6
                ]
            }
        ]
    },
    "remainder": "passthrough"
}
)";

void test_pipeline_small_1()

{
    snapml::Pipeline p;
    std::string      expected;

    std::cout << "(1) Testing whole pipeline and compare the result of a Python pipeline." << std::endl;

    try {
        p.import(data_schema_1);
    } catch (const std::exception& e) {
        std::cout << "Error importing pipeline information: " << e.what() << std::endl;
        assert(0);
    }

    snapml::DataSchema data_schema = p.get_schema();
    data_schema.enforce_byteswap   = is_enforce_byteswap(true);

    AnyDatasetTest ad(
        VCR("\013\000\000\00048.21914014\013\000\000\00087.24745352\013\000\000\00021.23326809"
            "\004\000\000\000ppgt\004\000\000\000xate\004\000\000\000xswz\004\000\000\000brbm\013\000\000\00084."
            "17407243"
            "\013\000\000\00020.70823444\013\000\000\00074.24695336\004\000\000\000lvci\004\000\000\000bbnd"
            "\004\000\000\000uezy\004\000\000\000nvfv\013\000\000\00065.35895855\013\000\000\00011."
            "50069431\013\000\000\00095."
            "02828643"
            "\004\000\000\000aelg\004\000\000\000ophn\004\000\000\000xhoo\004\000\000\000dmkj"),
        data_schema);

    try {
        p.transform(ad);
    } catch (const std::exception& e) {
        std::cout << "Error running transformers: " << e.what() << std::endl;
        assert(0);
    }

    compare_pipeline(
        "[[48.21914014, 87.24745352, 21.23326809], [84.17407243, 20.70823444, 74.24695336], [65.35895855, 11.50069431, "
        "95.02828643]]",
        "[['ppgt', 'xate', 'xswz', 'brbm'], ['lvci', 'bbnd', 'uezy', 'nvfv'], ['aelg', 'ophn', 'xhoo', 'dmkj']]",
        ad.get_final_features());
}

void test_pipeline_small_2()

{
    snapml::Pipeline p;
    std::string      expected;

    std::cout << "(2) Testing whole pipeline and compare the result of a Python pipeline." << std::endl;

    try {
        p.import(data_schema_2);
    } catch (const std::exception& e) {
        std::cout << "Error importing pipeline information: " << e.what() << std::endl;
        assert(0);
    }
    snapml::DataSchema data_schema = p.get_schema();
    data_schema.enforce_byteswap   = is_enforce_byteswap(true);

    AnyDatasetTest ad(
        VCR("\013\000\000\00018.85322236\012\000\000\0007.28560382\013\000\000\00054.44931401"
            "\004\000\000\000kgfg\004\000\000\000eecw\004\000\000\000dcks\004\000\000\000nekw\013\000\000\00058."
            "18265937"
            "\013\000\000\00060.51271197\013\000\000\00055.58544158\004\000\000\000jdbk\004\000\000\000hvcs"
            "\004\000\000\000aawt\004\000\000\000rrkh\013\000\000\00054.74398796\012\000\000\0001."
            "80397326\013\000\000\00097.96993344"
            "\004\000\000\000kgfg\004\000\000\000hvcs\004\000\000\000aawt\004\000\000\000rrkh"),
        data_schema);

    try {
        p.transform(ad);
    } catch (const std::exception& e) {
        std::cout << "Error running transformers: " << e.what() << std::endl;
        assert(0);
    }

    compare_pipeline(
        "[[18.85322236, 7.28560382, 54.44931401], [58.18265937, 60.51271197, 55.58544158], [54.74398796, 1.80397326, "
        "97.96993344]]",
        "[['kgfg', 'eecw', 'dcks', 'nekw'], ['jdbk', 'hvcs', 'aawt', 'rrkh'], ['kgfg', 'hvcs', 'aawt', 'rrkh']]",
        ad.get_final_features());
}

void test_pipeline_small_3()

{
    snapml::Pipeline p;
    std::string      expected;

    std::cout << "(3) Testing whole pipeline and compare the result of a Python pipeline." << std::endl;

    try {
        p.import(data_schema_3);
    } catch (const std::exception& e) {
        std::cout << "Error importing pipeline information: " << e.what() << std::endl;
        assert(0);
    }
    snapml::DataSchema data_schema = p.get_schema();
    data_schema.enforce_byteswap   = is_enforce_byteswap(true);

    AnyDatasetTest ad(VCR("\013\000\000\00030.52022575\013\000\000\00068.94265084\013\000\000\00076.73048413"
                          "\004\000\000\000vgug\004\000\000\000nxsd\004\000\000\000vjzs\004\000\000\000hfvc"
                          "\013\000\000\00093.35795121\013\000\000\00090.62306481"
                          "\013\000\000\00043."
                          "34001968\004\000\000\000xcyx\004\000\000\000auhm\004\000\000\000aggj\004\000\000\000tbjh\013"
                          "\000\000\00059.37423815"
                          "\013\000\000\00087.69954597\013\000\000\00070."
                          "56148207\004\000\000\000xcyx\004\000\000\000nxsd\004\000\000\000aggj"
                          "\004\000\000\000hfvc"),
                      data_schema);

    try {
        p.transform(ad);
    } catch (const std::exception& e) {
        std::cout << "Error running transformers: " << e.what() << std::endl;
        assert(0);
    }

    compare_pipeline(
        "[[30.52022575, 68.94265084, 76.73048413], [93.35795121, 90.62306481, 43.34001968], [59.37423815, 87.69954597, "
        "70.56148207]]",
        "[['vgug', 'nxsd', 'vjzs', 'hfvc'], ['xcyx', 'auhm', 'aggj', 'tbjh'], ['xcyx', 'nxsd', 'aggj', 'hfvc']]",
        ad.get_final_features());
}

void test_pipeline_small_4()

{
    snapml::Pipeline p;
    std::string      expected;

    std::cout << "(4) Testing whole pipeline and compare the result of a Python pipeline." << std::endl;

    try {
        p.import(data_schema_4);
    } catch (const std::exception& e) {
        std::cout << "Error importing pipeline information: " << e.what() << std::endl;
        assert(0);
    }
    snapml::DataSchema data_schema = p.get_schema();
    data_schema.enforce_byteswap   = is_enforce_byteswap(true);

    AnyDatasetTest ad(VCR("\013\000\000\00095.33620188\013\000\000\00067.16197434\012\000\000\0001.58839603"
                          "\004\000\000\000aewa\004\000\000\000uhge\004\000\000\000ojvu\004\000\000\000ggzh\013\000\000"
                          "\00044.56597276"
                          "\012\000\000\0001.10363101\011\000\000\00086.968163\004\000\000\000qdrp\004\000\000\000uhge"
                          "\004\000\000\000wwtz\004\000\000\000jtsr\013\000\000\00086.62494056\013\000\000\00058."
                          "62286685\013\000\000\00032."
                          "78805586"
                          "\004\000\000\000qdrp\004\000\000\000eppq\004\000\000\000ojvu\004\000\000\000ggzh"),
                      data_schema);

    try {
        p.transform(ad);
    } catch (const std::exception& e) {
        std::cout << "Error running transformers: " << e.what() << std::endl;
        assert(0);
    }

    compare_pipeline(
        "[[95.33620188, 67.16197434, 1.58839603], [44.56597276, 1.10363101, 86.968163], [86.62494056, 58.62286685, "
        "32.78805586]]",
        "[['aewa', 'uhge', 'ojvu', 'ggzh'], ['qdrp', 'uhge', 'wwtz', 'jtsr'], ['qdrp', 'eppq', 'ojvu', 'ggzh']]",
        ad.get_final_features());
}

// small pipeline with Ordinal Encoder
void test_pipeline_small_o()

{
    snapml::Pipeline p;
    std::string      expected;

    std::cout << "Testing whole pipeline including Ordinal Encoder and compare the result of a Python pipeline."
              << std::endl;

    try {
        p.import(data_schema_o);
    } catch (const std::exception& e) {
        std::cout << "Error importing pipeline information: " << e.what() << std::endl;
        assert(0);
    }
    snapml::DataSchema data_schema = p.get_schema();
    data_schema.enforce_byteswap   = is_enforce_byteswap(true);

    AnyDatasetTest ad(
        VCR("\013\000\000\00048.21914014\013\000\000\00087.24745352\013\000\000\00021.23326809"
            "\004\000\000\000ppgt\004\000\000\000xate\004\000\000\000xswz\004\000\000\000brbm\013\000\000\00084."
            "17407243\013\000\000\00020.70823444"
            "\013\000\000\00074."
            "24695336\004\000\000\000lvci\004\000\000\000bbnd\004\000\000\000uezy\004\000\000\000nvfv\013\000\000\00065"
            ".35895855"
            "\013\000\000\00011.50069431\013\000\000\00095."
            "02828643\004\000\000\000aelg\004\000\000\000ophn\004\000\000\000xhoo\004\000\000\000dmkj"),
        data_schema);

    try {
        p.transform(ad);
    } catch (const std::exception& e) {
        std::cout << "Error running transformers: " << e.what() << std::endl;
        assert(0);
    }

    compare_pipeline_o(
        "[[48.21914014, 87.24745352, 21.23326809], [84.17407243, 20.70823444, 74.24695336], [65.35895855, 11.50069431, "
        "95.02828643]]",
        "[['ppgt', 'xate', 'xswz', 'brbm'], ['lvci', 'bbnd', 'uezy', 'nvfv'], ['aelg', 'ophn', 'xhoo', 'dmkj']]",
        ad.get_final_features());
}

// small pipeline with OHE + Ordinal Encoder
void test_pipeline_small_oo()

{
    snapml::Pipeline p;
    std::string      expected;

    std::cout
        << "Testing whole pipeline including One-Hot and Ordinal Encoder and compare the result of a Python pipeline."
        << std::endl;

    try {
        p.import(data_schema_oo);
    } catch (const std::exception& e) {
        std::cout << "Error importing pipeline information: " << e.what() << std::endl;
        assert(0);
    }
    snapml::DataSchema data_schema = p.get_schema();
    data_schema.enforce_byteswap   = is_enforce_byteswap(true);

    AnyDatasetTest ad(
        VCR("\013\000\000\00048.21914014\013\000\000\00087.24745352\013\000\000\00021.23326809\004\000\000\000ppgt"
            "\004\000\000\000xate\004\000\000\000xswz\004\000\000\000brbm\013\000\000\00084.17407243\013\000\000\00020."
            "70823444\013\000\000\00074.24695336"
            "\004\000\000\000lvci\004\000\000\000bbnd\004\000\000\000uezy\004\000\000\000nvfv\013\000\000\00065."
            "35895855\013\000\000\00011.50069431"
            "\013\000\000\00095."
            "02828643\004\000\000\000aelg\004\000\000\000ophn\004\000\000\000xhoo\004\000\000\000dmkj"),
        data_schema);

    try {
        p.transform(ad);
    } catch (const std::exception& e) {
        std::cout << "Error running transformers: " << e.what() << std::endl;
        assert(0);
    }

    compare_pipeline_oo(
        "[[48.21914014, 87.24745352, 21.23326809], [84.17407243, 20.70823444, 74.24695336], [65.35895855, 11.50069431, "
        "95.02828643]]",
        "[['ppgt', 'xate', 'xswz', 'brbm'], ['lvci', 'bbnd', 'uezy', 'nvfv'], ['aelg', 'ophn', 'xhoo', 'dmkj']]",
        ad.get_final_features());
}

// small pipeline with Target Encoder
void test_pipeline_small_t()

{
    snapml::Pipeline p;
    std::string      expected;

    std::cout << "Testing whole pipeline including Target Encoder and compare the result of a Python pipeline."
              << std::endl;

    try {
        p.import(data_schema_t);
    } catch (const std::exception& e) {
        std::cout << "Error importing pipeline information: " << e.what() << std::endl;
        assert(0);
    }
    snapml::DataSchema data_schema = p.get_schema();
    data_schema.enforce_byteswap   = is_enforce_byteswap(true);

    AnyDatasetTest ad(
        VCR("\013\000\000\00048.21914014\013\000\000\00087.24745352\013\000\000\00021.23326809\004\000\000\000ppgt"
            "\004\000\000\000xate\004\000\000\000xswz\004\000\000\000brbm\013\000\000\00084.17407243\013\000\000\00020."
            "70823444\013\000\000\00074.24695336"
            "\004\000\000\000lvci\004\000\000\000bbnd\004\000\000\000uezy\004\000\000\000nvfv\013\000\000\00065."
            "35895855\013\000\000\00011.50069431"
            "\013\000\000\00095."
            "02828643\004\000\000\000aelg\004\000\000\000ophn\004\000\000\000xhoo\004\000\000\000dmkj"),
        data_schema);

    try {
        p.transform(ad);
    } catch (const std::exception& e) {
        std::cout << "Error running transformers: " << e.what() << std::endl;
        assert(0);
    }

    compare_pipeline_t(
        "[[48.21914014, 87.24745352, 21.23326809], [84.17407243, 20.70823444, 74.24695336], [65.35895855, 11.50069431, "
        "95.02828643]]",
        "[['ppgt', 'xate', 'xswz', 'brbm'], ['lvci', 'bbnd', 'uezy', 'nvfv'], ['aelg', 'ophn', 'xhoo', 'dmkj']]",
        "[['0.007', '0.023', '0.036'], ['0.022', '0.014', '0.026'], ['0.037', '0.011', '0.021'], ['0.035', '0.015', "
        "'0.024']]",
        0.02275, ad.get_final_features());
}

// small pipeline with OHE + Target Encoder
void test_pipeline_small_ot()

{
    snapml::Pipeline p;
    std::string      expected;

    std::cout
        << "Testing whole pipeline including One-Hot and Target Encoder and compare the result of a Python pipeline."
        << std::endl;

    try {
        p.import(data_schema_ot);
    } catch (const std::exception& e) {
        std::cout << "Error importing pipeline information: " << e.what() << std::endl;
        assert(0);
    }
    snapml::DataSchema data_schema = p.get_schema();
    data_schema.enforce_byteswap   = is_enforce_byteswap(true);

    AnyDatasetTest ad(
        VCR("\013\000\000\00048.21914014\013\000\000\00087.24745352\013\000\000\00021.23326809"
            "\004\000\000\000ppgt\004\000\000\000xate\004\000\000\000xswz\004\000\000\000brbm\013\000\000\00084."
            "17407243\013\000\000\00020.70823444"
            "\013\000\000\00074."
            "24695336\004\000\000\000lvci\004\000\000\000bbnd\004\000\000\000uezy\004\000\000\000nvfv\013\000\000\00065"
            ".35895855"
            "\013\000\000\00011.50069431\013\000\000\00095."
            "02828643\004\000\000\000aelg\004\000\000\000ophn\004\000\000\000xhoo\004\000\000\000dmkj"),
        data_schema);

    try {
        p.transform(ad);
    } catch (const std::exception& e) {
        std::cout << "Error running transformers: " << e.what() << std::endl;
        assert(0);
    }

    compare_pipeline_ot(
        "[[48.21914014, 87.24745352, 21.23326809], [84.17407243, 20.70823444, 74.24695336], [65.35895855, 11.50069431, "
        "95.02828643]]",
        "[['ppgt', 'xate', 'xswz', 'brbm'], ['lvci', 'bbnd', 'uezy', 'nvfv'], ['aelg', 'ophn', 'xhoo', 'dmkj']]",
        "[['0.037', '0.011', '0.021'], ['0.035', '0.015', '0.024']]", 0.02275, ad.get_final_features());
}

// to compare with a Python pipeline
void fit(uint32_t pipeline_id, const std::string& fit_array)
{
    std::stringstream sstr;
    sstr << R"(
import sklearn
sklearn_version = sklearn.__version__
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
import sklearn.preprocessing
from sklearn.preprocessing import Normalizer, KBinsDiscretizer
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder
if 'TargetEncoder' in sklearn.preprocessing.__dict__:
    from sklearn.preprocessing import TargetEncoder
import random
import string
import re
import os
import joblib
import sys
import numpy as np
import pandas as pd
import ast
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import FunctionTransformer
import warnings
warnings.filterwarnings('ignore')
if "__file__" not in globals():
    __file__ = os.path.abspath(sys.argv[0])
gfp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",".."))
if gfp_dir not in sys.path:
    sys.path.append(gfp_dir)
    
import json
# create an empty data frame with given column types
def df_empty(columns, dtypes, index=None):
    assert len(columns)==len(dtypes)
    df = pd.DataFrame(index=index)
    for c,d in zip(columns, dtypes):
        df[c] = pd.Series(dtype=d)
    return df

if __name__ == '__main__':
    pipeline_id = )"
         << pipeline_id << R"(

    # number of samples in the dataset
    n_samples = 10

    # number of categorical features
    n_cat_feats = 4

    # number of unique categories per feature
    cat_per_feat = 10

    # number of numerical features which will need logarithmic scale transformation
    n_num_feats_log = 2

    # total number of numerical features
    n_num_feats = 3


    # ---------- Data generation step ---------- #
    
    # Generate random categorical feature values
    categories = {}
    for i in range(n_cat_feats):
        categories[str(i)] = []
        for j in range(cat_per_feat) :
            categories[str(i)].append(''.join(random.choice(string.ascii_lowercase) for k in range(4)))
    
    # Create a numpy array containing the categorical features
    cat_matrix = np.empty(shape=(n_samples, n_cat_feats), dtype="<U4")
    for c in range(n_cat_feats):
        cat_matrix[:,c] = random.choices(categories[str(c)], k=n_samples)
    # print("Shape of categorical matrix: ", cat_matrix.shape)
    
    # Create a numpy array containing the numerical features
    #num_matrix = np.random.uniform(low=0, high=100, size=(n_samples, n_num_feats))
    # print("Shape of numerical matrix: ", num_matrix.shape)
    try:
        fit_array = ast.literal_eval(')"
         << fit_array << R"(')
    except ValueError as e:
        print(f"Error: {e}")
    # Create numpy array from fit_array
    num_matrix = np.array(fit_array)
    # Create labels (highly imbalanced binary classification problem)
    # labels = np.random.choice(2, n_samples, p=[0.98, 0.02])
    labels = np.zeros(n_samples)
    indices = np.arange(n_samples)
    
    # Split data into train and test and retrieve their corresponding indices
    xnum_train, xnum_test, y_train, y_test, indices_train, indices_test = train_test_split(num_matrix, labels, indices, test_size=0.2, random_state=42, stratify=labels)
    xcat_train = cat_matrix[indices_train,:]
    xcat_test  = cat_matrix[indices_test,:]
    
    # ---------- Pipeline (preprocessing + training) generation step ---------- #
    
    colnames  = []
    num_feats = []
    coltypes  = []
    cat_feats = []
    
    for i in range(n_num_feats):
        colnames.append('num'+str(i))
        num_feats.append('num'+str(i))
        coltypes.append(np.float32)
    
    for i in range(n_cat_feats):
        colnames.append('cat'+str(i))
        cat_feats.append('cat'+str(i))
        coltypes.append(str)
    
    # aggregate all the numerical and categorical data into a single dataframe 
    df_train = df_empty(colnames, dtypes=coltypes)
    df_train.iloc[:,0:n_num_feats] = pd.DataFrame(xnum_train)
    df_train.iloc[:,n_num_feats:]  = pd.DataFrame(xcat_train)

    # print(df_train.to_csv(header=False, index=False))
    with open("df_train.str", "w") as file: 
        file.write(df_train.to_csv(header=False, index=False))

    # Create the preprocessing steps as Pipelines
    num_transformer = Pipeline(steps=[('logscaler', FunctionTransformer(func=np.log1p)), ('normalizer', Normalizer()), ('discretizer', KBinsDiscretizer(encode="ordinal"))])
    
    if pipeline_id == 0:
        cat_transformer = Pipeline(steps=[('onehot', OneHotEncoder(categories='auto', sparse_output=False, handle_unknown='ignore'))])            
    elif pipeline_id == 1:
        cat_transformer = Pipeline(steps=[('ordinal', OrdinalEncoder(categories='auto', handle_unknown='use_encoded_value', unknown_value=-1))])
    elif pipeline_id == 2:
        cat_transformer = Pipeline(steps=[('target', TargetEncoder(categories='auto'))])

    # Create the ColumnTransformer based on the transformers above
    preprocessor = ColumnTransformer(transformers=[('num_trans', num_transformer, num_feats), ('encoding_trans', cat_transformer, cat_feats)])

    # Create a pipeline
    pipeline = Pipeline(steps=[ ('preprocessor', preprocessor)])
    pipeline.fit(df_train, y_train)

    joblib.dump(df_train, "df_train.pkl")
    joblib.dump(pipeline, "pipeline.pkl")

    import imp
    pipeline_io = imp.load_source('pipeline_io', os.path.realpath("../../pipeline_io.py"))
    pipeline_io.export_preprocessing_pipeline(pipeline['preprocessor'], 'pipeline.json')
)";

    if (PyRun_SimpleString(sstr.str().c_str())) {
        std::cout << "fit failed" << std::endl;
        assert(0);
    }
}

// to compare with a Python pipeline
void fit_1(uint32_t pipeline_id, const std::string& fit_array)
{
    std::stringstream sstr;
    sstr << R"(
import sklearn
sklearn_version = sklearn.__version__
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
import sklearn.preprocessing
from sklearn.preprocessing import Normalizer, KBinsDiscretizer
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder
if 'TargetEncoder' in sklearn.preprocessing.__dict__:
    from sklearn.preprocessing import TargetEncoder
import random
import string
import re
import os
import joblib
import sys
import numpy as np
import pandas as pd
import ast
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import FunctionTransformer
import warnings
warnings.filterwarnings('ignore')
if "__file__" not in globals():
    __file__ = os.path.abspath(sys.argv[0])
gfp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",".."))
if gfp_dir not in sys.path:
    sys.path.append(gfp_dir)
    
import json
# create an empty data frame with given column types
def df_empty(columns, dtypes, index=None):
    assert len(columns)==len(dtypes)
    df = pd.DataFrame(index=index)
    for c,d in zip(columns, dtypes):
        df[c] = pd.Series(dtype=d)
    return df

if __name__ == '__main__':
    pipeline_id = )"
         << pipeline_id << R"(

    # number of samples in the dataset
    n_samples = 10

    # number of categorical features
    n_cat_feats = 4
    n_cat_feats_ohe = 2
    n_cat_feats_other = n_cat_feats - n_cat_feats_ohe

    # number of unique categories per feature
    cat_per_feat = 10

    # number of numerical features which will need logarithmic scale transformation
    n_num_feats_log = 2

    # total number of numerical features
    n_num_feats = 3


    # ---------- Data generation step ---------- #
    
    # Generate random categorical feature values
    categories = {}
    for i in range(n_cat_feats):
        categories[str(i)] = []
        for j in range(cat_per_feat) :
            categories[str(i)].append(''.join(random.choice(string.ascii_lowercase) for k in range(4)))
    
    # Create a numpy array containing the categorical features
    cat_matrix = np.empty(shape=(n_samples, n_cat_feats), dtype="<U4")
    for c in range(n_cat_feats):
        cat_matrix[:,c] = random.choices(categories[str(c)], k=n_samples)
    # print("Shape of categorical matrix: ", cat_matrix.shape)
    
    # Create a numpy array containing the numerical features
    #num_matrix = np.random.uniform(low=0, high=100, size=(n_samples, n_num_feats))
    # print("Shape of numerical matrix: ", num_matrix.shape)
    # Convert the passed fit_array string into a 2D array (list of lists)
    try:
        fit_array = ast.literal_eval(')"
         << fit_array << R"(')
    except ValueError as e:
        print(f"Error: {e}")
    # Create numpy array from fit_array
    num_matrix = np.array(fit_array)
    # Create labels (highly imbalanced binary classification problem)
    # labels = np.random.choice(2, n_samples, p=[0.98, 0.02])
    labels = np.zeros(n_samples)
    indices = np.arange(n_samples)
    
    # Split data into train and test and retrieve their corresponding indices
    xnum_train, xnum_test, y_train, y_test, indices_train, indices_test = train_test_split(num_matrix, labels, indices, test_size=0.2, random_state=42, stratify=labels)
    xcat_train = cat_matrix[indices_train,:]
    xcat_test  = cat_matrix[indices_test,:]
    
    # ---------- Pipeline (preprocessing + training) generation step ---------- #
    
    colnames  = []
    num_feats = []
    coltypes  = []
    cat_feats_ohe = []
    cat_feats_other = []

    for i in range(n_num_feats):
        colnames.append('num'+str(i))
        num_feats.append('num'+str(i))
        coltypes.append(np.float32)

    for i in range(n_cat_feats_ohe):
        colnames.append('cat'+str(i))
        cat_feats_ohe.append('cat'+str(i))
        coltypes.append(str)

    for i in range(n_cat_feats_other):
        colnames.append('cat'+str(i+n_cat_feats_ohe))
        cat_feats_other.append('cat'+str(i+n_cat_feats_ohe))
        coltypes.append(str)

    
    # aggregate all the numerical and categorical data into a single dataframe 
    df_train = df_empty(colnames, dtypes=coltypes)
    df_train.iloc[:,0:n_num_feats] = pd.DataFrame(xnum_train)
    df_train.iloc[:,n_num_feats:]  = pd.DataFrame(xcat_train)

    # print(df_train.to_csv(header=False, index=False))
    with open("df_train.str", "w") as file: 
        file.write(df_train.to_csv(header=False, index=False))  

    # Create the preprocessing steps as Pipelines
    num_transformer = Pipeline(steps=[('logscaler', FunctionTransformer(func=np.log1p)), ('normalizer', Normalizer()), ('discretizer', KBinsDiscretizer(encode="ordinal"))])
    cat_transformer_ohe = Pipeline(steps=[('onehot', OneHotEncoder(categories='auto', sparse_output=False, handle_unknown='ignore'))])    
    if pipeline_id == 3:    
        cat_transformer_other = Pipeline(steps=[('ordinal', OrdinalEncoder(categories='auto', handle_unknown='use_encoded_value', unknown_value=-1))])
    elif pipeline_id == 4:
        cat_transformer_other = Pipeline(steps=[('target', TargetEncoder(categories='auto'))])

    # Create the ColumnTransformer based on the transformers above
    preprocessor = ColumnTransformer(transformers=[('num_trans', num_transformer, num_feats), ('ohe_encoding_trans', cat_transformer_ohe, cat_feats_ohe), ('ord_encoding_trans', cat_transformer_other, cat_feats_other)])

    # Create a pipeline
    pipeline = Pipeline(steps=[ ('preprocessor', preprocessor)])
    pipeline.fit(df_train, y_train)

    joblib.dump(df_train, "df_train.pkl")
    joblib.dump(pipeline, "pipeline.pkl")

    import imp
    pipeline_io = imp.load_source('pipeline_io', os.path.realpath("../../pipeline_io.py"))
    pipeline_io.export_preprocessing_pipeline(pipeline['preprocessor'], 'pipeline.json')
)";
    if (PyRun_SimpleString(sstr.str().c_str())) {
        std::cout << "fit failed" << std::endl;
        assert(0);
    }
}

void compare_transform(const std::string result)

{
    std::stringstream sstr;
    sstr << R"(
import os
import numpy as np
from sklearn.pipeline import Pipeline
import warnings
warnings.filterwarnings('ignore')

if __name__ == '__main__':
    result = np.array()"
         << result << R"().astype(float)[0]
    df_train = joblib.load("df_train.pkl")
    os.remove("df_train.pkl")
    pipeline = joblib.load("pipeline.pkl")
    os.remove("pipeline.pkl")

    # Transform the data
    expected = pipeline['preprocessor'].transform(df_train).flatten()

    if np.allclose(result, expected) == False:
        raise Exception('result ' + str(result) + ' does not match the expected ' + str(expected))
)";

    if (PyRun_SimpleString(sstr.str().c_str())) {
        std::cout << "comparison to scikit-learn failed for Pipeline" << std::endl;
        assert(0);
    } else {
        std::cout << ".";
    }
}

void test_pipeline_complete(uint32_t pipeline_id, const std::string& array)
{

    snapml::Pipeline p;

    if (pipeline_id < 3)
        fit(pipeline_id, array);
    else
        fit_1(pipeline_id, array);

    std::ifstream     istrm("df_train.str");
    std::string       input_str((std::istreambuf_iterator<char>(istrm)), std::istreambuf_iterator<char>());
    std::vector<char> input_vctr
        = replace_delimiter_with_octal_prefix(std::vector<char>(input_str.begin(), input_str.end()));

    // std::cout << "running pipeline_id " << pipeline_id << "input" << input_str
    //           << replace_delimiter_with_octal_prefix(input_str) << std::endl;

    unlink("df_train.str");

    try {
        p.import("pipeline.json");
    } catch (const std::exception& e) {
        std::cout << "Error importing pipeline information: " << e.what() << std::endl;
        assert(0);
    }

    unlink("pipeline.json");

    snapml::DataSchema data_schema = p.get_schema();
    data_schema.enforce_byteswap   = is_enforce_byteswap(true);

    AnyDatasetTest ad(input_vctr, data_schema);

    try {
        p.transform(ad);
    } catch (const std::exception& e) {
        std::cout << "Error running transformers: " << e.what() << std::endl;
        assert(0);
    }

    compare_transform(ad.get_final_features());
}

void test_gen_preprocessing()
{
    snapml::Pipeline     p;
    std::string          expected;
    snapml::DenseDataset dense_dataset;
    std::cout << "Testing whole pipeline based on a JSON file ==> KBins, OHE" << std::endl;
    try {
        p.import("../test/data/gen_preprocessing_label.json");
    } catch (const std::exception& e) {
        std::cout << "Error importing pipeline information: " << e.what() << std::endl;
        assert(0);
    }

    snapml::DataSchema data_schema = p.get_schema();
    data_schema.enforce_byteswap   = is_enforce_byteswap(true);
    AnyDatasetTest ad(VCR("\004\000\000\000Blue\004\000\000\0000100\003\000\000\000Red"
                          "\004\000\000\0000150\005\000\000\000Green\004\000\000\0000120"),
                      data_schema);

    std::cout << std::endl;
    std::cout << ad.get_categorical_features() << " ⮕ ";
    std::cout << std::endl;
    std::cout << ad.get_numerical_features() << " ⮕ ";
    std::cout << std::endl;
    try {
        dense_dataset                      = p.transform(ad);
        std::vector<std::vector<float>> fd = p.get_vec(ad);

    } catch (const std::exception& e) {
        std::cout << "Error running transformers: " << e.what() << std::endl;
        assert(0);
    }
    expected = "[[1, 0, 0, 0, 0, 0, 1, 2, 0, 1, 0, 1]]";
    if (ad.get_final_features() != expected) {
        std::cout << "check for numerical features failed: " << ad.get_final_features() << " != " + expected
                  << std::endl;
        assert(0);
    }

    std::cout << std::endl;
}

// Function to convert JSON array to std::vector<std::vector<float>>
std::vector<std::vector<float>> json_to_vector(const rapidjson::Value& array)
{
    std::vector<std::vector<float>> vec;
    assert(array.IsArray());
    for (rapidjson::SizeType i = 0; i < array.Size(); i++) {
        assert(array[i].IsArray());
        std::vector<float> row;
        for (rapidjson::SizeType j = 0; j < array[i].Size(); j++) {
            assert(array[i][j].IsNumber());
            row.push_back(array[i][j].GetFloat());
        }
        vec.push_back(row);
    }
    return vec;
}

// Function to read JSON file and collect keys
void read_json_and_get_keys(std::vector<std::string>& keys, rapidjson::Document& doc, const std::string& file_path)
{
    // Read JSON file
    FILE* fp = fopen(file_path.c_str(), "r");
    if (!fp) {
        std::cerr << "Could not open file: " << file_path << std::endl;
        exit(EXIT_FAILURE);
    }
    char                      readBuffer[65536];
    rapidjson::FileReadStream is(fp, readBuffer, sizeof(readBuffer));
    doc.ParseStream(is);
    fclose(fp);

    // Collect keys
    for (rapidjson::Value::ConstMemberIterator itr = doc.MemberBegin(); itr != doc.MemberEnd(); ++itr) {
        keys.push_back(itr->name.GetString());
    }
}

// Function to get a random key from the keys vector
std::string get_random_key(const std::vector<std::string>& keys) { return keys[std::rand() % keys.size()]; }

// Function to convert 2D vector to string
std::string convert_vector_to_string(const std::vector<std::vector<float>>& vec)
{
    std::ostringstream num_stream;
    num_stream << "[";
    for (size_t i = 0; i < vec.size(); ++i) {
        num_stream << "[";
        for (size_t j = 0; j < vec[i].size(); ++j) {
            num_stream << vec[i][j];
            if (j < vec[i].size() - 1) {
                num_stream << ", ";
            }
        }
        num_stream << "]";
        if (i < vec.size() - 1) {
            num_stream << ", ";
        }
    }
    num_stream << "]";
    return num_stream.str();
}

int main(int argc, char** argv)

{
    Py_Initialize();
    std::string                     key;
    rapidjson::Document             doc;
    std::string                     array_stream;
    std::vector<std::string>        keys;
    std::vector<std::vector<float>> fit_num;
    // Read JSON file and get keys
    read_json_and_get_keys(keys, doc, "../test/data/fit_matrix_data.json");
    // Seed the random number generator
    std::srand(static_cast<unsigned int>(std::time(nullptr)));
    std::stringstream sstr;
    sstr << R"(
import sklearn.preprocessing
target_encoder_available = 'TargetEncoder' in sklearn.preprocessing.__dict__
)";

    PyRun_SimpleString(sstr.str().c_str());

    PyObject* main_module              = PyImport_AddModule("__main__");
    PyObject* globals                  = PyModule_GetDict(main_module);
    PyObject* target_encoder_available = PyDict_GetItemString(globals, "target_encoder_available");
    int       enable_target_encoder    = PyObject_IsTrue(target_encoder_available);

    Py_XDECREF(main_module);

    test_input();
    test_transformer();
    test_pipeline_orig();
    test_pipeline_orig_ord();
    test_pipeline_orig_target();
    test_pipeline_orig_all();
    test_pipeline_small_1();
    test_pipeline_small_2();
    test_pipeline_small_3();
    test_pipeline_small_4();
    test_pipeline_small_o();
    test_pipeline_small_oo();
    test_pipeline_small_t();
    test_pipeline_small_ot();
    test_gen_preprocessing();
    std::cout
        << "Testing whole pipeline + transform including One-Hot Encoder and compare the result of a Python pipeline."
        << std::endl;
    for (uint32_t trun = 0; trun < 200; trun++) {
        key                           = get_random_key(keys);
        const rapidjson::Value& array = doc[key.c_str()];
        fit_num                       = json_to_vector(array);
        array_stream                  = convert_vector_to_string(fit_num);
        test_pipeline_complete(0, array_stream);
    }
    std::cout
        << "\nTesting whole pipeline + transform including Ordinal Encoder and compare the result of a Python pipeline."
        << std::endl;
    for (uint32_t trun = 0; trun < 200; trun++) {
        key                           = get_random_key(keys);
        const rapidjson::Value& array = doc[key.c_str()];
        fit_num                       = json_to_vector(array);
        array_stream                  = convert_vector_to_string(fit_num);
        test_pipeline_complete(1, array_stream);
    }
    std::cout << "\nTesting whole pipeline"
                 "transform including One-Hot + Ordinal Encoder and compare the result of a Python pipeline."
              << std::endl;
    for (uint32_t trun = 0; trun < 200; trun++) {
        key                           = get_random_key(keys);
        const rapidjson::Value& array = doc[key.c_str()];
        fit_num                       = json_to_vector(array);
        array_stream                  = convert_vector_to_string(fit_num);
        test_pipeline_complete(3, array_stream);
    }
    if (enable_target_encoder) {
        std::cout << "\nTesting whole pipeline + transform including Target Encoder and compare the result of a Python "
                     "pipeline."
                  << std::endl;
        for (uint32_t trun = 0; trun < 200; trun++) {
            key                           = get_random_key(keys);
            const rapidjson::Value& array = doc[key.c_str()];
            fit_num                       = json_to_vector(array);
            array_stream                  = convert_vector_to_string(fit_num);
            test_pipeline_complete(2, array_stream);
        }
        std::cout << "\nTesting whole pipeline + transform including One-Hot + Target Encoder and compare the result "
                     "of a Python pipeline."
                  << std::endl;
        for (uint32_t trun = 0; trun < 200; trun++) {
            key                           = get_random_key(keys);
            const rapidjson::Value& array = doc[key.c_str()];
            fit_num                       = json_to_vector(array);
            array_stream                  = convert_vector_to_string(fit_num);
            test_pipeline_complete(4, array_stream);
        }
    }

    std::cout << std::endl;

    if (Py_FinalizeEx() < 0) {
        exit(120);
    }

    return 0;
}
