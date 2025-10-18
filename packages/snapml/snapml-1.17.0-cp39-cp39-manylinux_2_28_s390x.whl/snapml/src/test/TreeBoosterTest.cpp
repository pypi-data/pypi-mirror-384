/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2018, 2020, 2021
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Thomas Parnell
 *                Andreea Anghel
 *                Nikolas Ioannou
 *
 * End Copyright
 ********************************************************************/

#include <cstring>

#include "DatasetGenerators.hpp"
#include "Metrics.hpp"
#include "TestUtils.hpp"
#include "BoosterParams.hpp"
#include "BoosterBuilder.hpp"
#include "BoosterModel.hpp"
#include "BoosterPredictor.hpp"

double test_regression(uint32_t num_ex, uint32_t num_ft, uint32_t min_max_depth, uint32_t max_max_depth,
                       bool use_gpu = false, uint32_t n_regressors = 100, uint32_t n_threads = 8, float subsample = 1.0,
                       float colsample_bytree = 1.0)
{

    snapml::DenseDataset data
        = glm::tests::generate_small_random_dense_dataset_regression_api(42, false, num_ex, num_ft, 1.0);

    snapml::BoosterParams params;
    params.base_prediction  = 0.1;
    params.learning_rate    = 1.0;
    params.n_regressors     = n_regressors;
    params.subsample        = subsample;
    params.colsample_bytree = 0.5;
    params.use_gpu          = use_gpu;
    params.use_histograms   = true;
    params.min_max_depth    = min_max_depth;
    params.max_max_depth    = max_max_depth;
    params.n_threads        = n_threads;
    params.verbose          = true;
    params.lambda           = 10.0;

    snapml::BoosterBuilder builder = snapml::BoosterBuilder(data, snapml::DenseDataset(), params);

    typedef std::chrono::high_resolution_clock Clock;
    auto                                       t1 = Clock::now();
    builder.init();
    builder.build(nullptr);
    auto   t2    = Clock::now();
    auto   dur   = t2 - t1;
    double t_fit = (double)dur.count() / 1e9;

    snapml::BoosterModel     model     = builder.get_model();
    snapml::BoosterPredictor predictor = snapml::BoosterPredictor(model);

    std::vector<double> preds(num_ex);
    std::vector<double> new_preds(num_ex);
    predictor.predict(data, preds.data(), n_threads);

    double mse = glm::metrics::jni::mean_squared_error(data.get().get(), preds.data(), preds.size());

    printf("num_ex: %u, num_ft: %u, max_depth: [%u,%u], use_gpu: %d, t_fit: %f, mse: %f\n", num_ex, num_ft,
           min_max_depth, max_max_depth, use_gpu, t_fit, mse);

    // if (1.0 == subsample && 1.0 == colsample_bytree)
    //    assert(mse < 1e-10);

    std::vector<uint8_t> vec;
    model.get(vec);

    snapml::BoosterModel new_model;
    new_model.put(vec);

    snapml::BoosterPredictor new_predictor = snapml::BoosterPredictor(new_model);

    new_predictor.predict(data, new_preds.data(), n_threads);

    for (uint32_t i = 0; i < num_ex; i++)
        assert(glm::tests::are_close(preds[i], new_preds[i], 1e-12));

    return mse;
}

double test_classification(uint32_t num_ex, uint32_t num_ft, uint32_t min_max_depth, uint32_t max_max_depth,
                           bool use_gpu = false, uint32_t n_regressors = 100, uint32_t n_threads = 8,
                           float subsample = 1.0, float colsample_bytree = 1.0)
{

    snapml::DenseDataset data = glm::tests::generate_small_random_dense_dataset_api(42, false, num_ex, num_ft, 1.0);

    snapml::BoosterParams params;
    params.objective        = snapml::BoosterParams::objective_t::logloss;
    params.learning_rate    = 1.0;
    params.n_regressors     = n_regressors;
    params.subsample        = subsample;
    params.colsample_bytree = colsample_bytree;
    params.use_gpu          = use_gpu;
    params.use_histograms   = true;
    params.min_max_depth    = min_max_depth;
    params.max_max_depth    = max_max_depth;
    params.n_threads        = n_threads;
    params.verbose          = true;
    params.lambda           = 10.0;

    snapml::BoosterBuilder builder = snapml::BoosterBuilder(data, snapml::DenseDataset(), params);

    typedef std::chrono::high_resolution_clock Clock;
    auto                                       t1 = Clock::now();
    builder.init();
    builder.build(nullptr);
    auto   t2    = Clock::now();
    auto   dur   = t2 - t1;
    double t_fit = (double)dur.count() / 1e9;

    snapml::BoosterModel model     = builder.get_model();
    auto                 predictor = std::make_shared<snapml::BoosterPredictor>(model);

    std::vector<double> preds(num_ex);
    std::vector<double> new_preds(num_ex);
    predictor->predict(data, preds.data(), n_threads);

    double acc = glm::metrics::jni::accuracy(data.get().get(), preds.data(), preds.size(), true);

    printf("num_ex: %u, num_ft: %u, max_depth: [%u,%u], use_gpu: %d, t_fit: %f, accuracy: %f\n", num_ex, num_ft,
           min_max_depth, max_max_depth, use_gpu, t_fit, acc);

    std::vector<uint8_t> vec;
    model.get(vec);

    snapml::BoosterModel new_model;
    new_model.put(vec);

    auto new_predictor = std::make_shared<snapml::BoosterPredictor>(new_model);

    new_predictor->predict(data, new_preds.data(), n_threads);

    for (uint32_t i = 0; i < num_ex; i++) {
        assert(glm::tests::are_close(preds[i], new_preds[i], 1e-12));
    }

    return acc;
}

int main(const int argc, const char* argv[])
{

    int num_ex        = 100;
    int num_ft        = 10;
    int min_max_depth = 4;
    int max_max_depth = 6;
    int n_regressors  = 1000;
    int n_threads     = 4;
    if (1 < argc)
        num_ex = atoi(argv[1]);
    if (2 < argc)
        num_ft = atoi(argv[2]);
    if (3 < argc)
        min_max_depth = atoi(argv[3]);
    if (4 < argc)
        max_max_depth = atoi(argv[4]);
    if (5 < argc)
        n_regressors = atoi(argv[5]);
    if (6 < argc)
        n_threads = atoi(argv[6]);

    // REGRESSION
    std::cout << "MSE CPU:" << std::endl;
    double mse_cpu = test_regression(num_ex, num_ft, min_max_depth, max_max_depth, false, n_regressors, n_threads);
#ifdef WITH_CUDA
    double mse_gpu = test_regression(num_ex, num_ft, min_max_depth, max_max_depth, true, n_regressors, n_threads);

    assert(glm::tests::are_close(mse_cpu, mse_gpu, 0.001));
#endif

    // test colsample_bytree
    double mse_cpu2
        = test_regression(num_ex, num_ft, min_max_depth, max_max_depth, false, n_regressors, n_threads, 1.0, 0.8);
#ifdef WITH_CUDA
    double mse_gpu2
        = test_regression(num_ex, num_ft, min_max_depth, max_max_depth, true, n_regressors, n_threads, 1.0, 0.8);
    assert(glm::tests::are_close(mse_cpu2, mse_gpu2, 0.001));
#endif
    assert(glm::tests::are_close(mse_cpu2, mse_cpu, 0.001));

    // test_classification(100, 4);
    // test subsample
    // test_regression(100, 4, 0.67);
    // test_classification(100, 4, 0.67);
    // test colsample_bytree
    // test_regression(100, 4, 0.33, 0.2);
    // test_classification(100, 4, 0.33, 0.2);

    return 0;
}
