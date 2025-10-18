/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2020, 2021
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
 *                Jan van Lunteren
 *                Milos Stanisavljevic
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
#include "RandomForestParams.hpp"
#include "RandomForestBuilder.hpp"
#include "RandomForestModel.hpp"
#include "RandomForestPredictor.hpp"

int main(const int argc, const char* argv[])
{

    // dataset-specific properties
    uint32_t num_ex = 100;
    uint32_t num_ft = 10;

    uint32_t n_threads = 4;
    bool     use_gpu   = false;
    bool     acc_ok    = false;

    // vectors for predictions
    std::vector<double> preds(num_ex, 0);
    std::vector<double> comp_preds(num_ex, 0);
    std::vector<double> new_preds(num_ex, 0);

    ///////////////////////////////////
    // TreeBooster Classification Test
    ///////////////////////////////////
    snapml::BoosterParams params;

    params.objective          = snapml::BoosterParams::objective_t::logloss;
    params.n_regressors       = 100;
    params.learning_rate      = 0.1;
    params.select_probability = 1.0;
    params.n_threads          = n_threads;
    params.use_gpu            = use_gpu;
    params.min_max_depth      = 4;
    params.max_max_depth      = 4;

    {

        snapml::DenseDataset data = glm::tests::generate_small_random_dense_dataset_api(42, false, num_ex, num_ft, 1.0);

        snapml::BoosterBuilder builder = snapml::BoosterBuilder(data, snapml::DenseDataset(), params);

        builder.init();
        builder.build(nullptr);

        snapml::BoosterModel model = builder.get_model();

        snapml::BoosterPredictor predictor = snapml::BoosterPredictor(model);

        predictor.predict(data, preds.data(), params.n_threads);

        // TEST 1
        // verify training data is over-fit
        double score = glm::metrics::jni::accuracy(data.get().get(), preds.data(), preds.size(), true);
        printf(">> score classification booster: %f\n", score);
        acc_ok = score > 0.99;
        if (!acc_ok)
            printf("Predict classification booster failed.\n");
        assert(acc_ok);

        printf("Booster Classification Test 1 passed!\n");

        // TEST 2
        // verify that predictions are the same after compression

        // (3) test using compressed model/engine

        model.compress(data);

        predictor.predict(data, comp_preds.data(), params.n_threads);

        for (uint32_t i = 0; i < num_ex; i++)
            assert(glm::tests::are_close(preds[i], comp_preds[i], 1e-10));

        printf("Booster Classification Test 2 passed!\n");

        // TEST 3
        // verify serialization + deserialization
        std::vector<uint8_t> vec;
        model.get(vec);

        snapml::BoosterModel chk_model;
        chk_model.put(vec);

        snapml::BoosterPredictor chk_predictor = snapml::BoosterPredictor(chk_model);

        chk_predictor.predict(data, new_preds.data(), params.n_threads);

        for (uint32_t i = 0; i < num_ex; i++)
            assert(glm::tests::are_close(preds[i], new_preds[i], 1e-10));

        printf("Booster Classification Test 3 passed!\n");
    }

    ///////////////////////////////////
    // TreeBooster Regression Test
    ///////////////////////////////////
    params.objective = snapml::BoosterParams::objective_t::mse;

    {

        snapml::DenseDataset data
            = glm::tests::generate_small_random_dense_dataset_regression_api(42, false, num_ex, num_ft, 1.0);

        snapml::BoosterBuilder builder = snapml::BoosterBuilder(data, snapml::DenseDataset(), params);

        builder.init();
        builder.build(nullptr);

        snapml::BoosterModel model = builder.get_model();

        snapml::BoosterPredictor predictor = snapml::BoosterPredictor(model);

        predictor.predict(data, preds.data(), params.n_threads);

        // TEST 1
        // verify training data is over-fit
        double score = glm::metrics::jni::mean_squared_error(data.get().get(), preds.data(), preds.size());
        printf(">> score regression booster: %f\n", score);
        acc_ok = score < 1e-3;

        if (!acc_ok)
            printf("Predict regression booster failed.\n");
        assert(acc_ok);

        printf("Booster Regression Test 1 passed!\n");

        // TEST 2
        // verify that predictions are the same after compression
        model.compress(data);

        predictor.predict(data, comp_preds.data(), params.n_threads);

        printf("Booster Regression Test 2 passed!\n");

        for (uint32_t i = 0; i < num_ex; i++)
            assert(glm::tests::are_close(preds[i], comp_preds[i], 1e-10));
    }

    ///////////////////////////////////
    // TreeForest Classification Test
    ///////////////////////////////////
    snapml::RandomForestParams rf_params;
    rf_params.n_trees         = 16;
    rf_params.n_threads       = n_threads;
    rf_params.hist_nbins      = 256;
    rf_params.use_gpu         = use_gpu;
    rf_params.task            = snapml::task_t::classification;
    rf_params.split_criterion = snapml::split_t::gini;

    {
        snapml::DenseDataset data = glm::tests::generate_small_random_dense_dataset_api(42, false, num_ex, num_ft, 1.0);

        snapml::RandomForestBuilder rf_builder = snapml::RandomForestBuilder(data, &rf_params);

        rf_builder.init();
        rf_builder.build(nullptr);

        snapml::RandomForestModel rf_model = rf_builder.get_model();

        snapml::RandomForestPredictor rf_predictor = snapml::RandomForestPredictor(rf_model);

        rf_predictor.predict(data, preds.data(), rf_params.n_threads);

        // TEST 1
        // verify training data is over-fit
        double score = glm::metrics::jni::accuracy(data.get().get(), preds.data(), preds.size(), true);
        printf(">> score classification forest: %f\n", score);
        acc_ok = score > 0.985;

        if (!acc_ok)
            printf("Predict classification forest failed.\n");
        assert(acc_ok);

        printf("Random Forest Classification Test 1 passed!\n");

        // TEST 2
        // verify that predictions are the same after compression
        rf_model.compress(data);

        rf_predictor.predict(data, comp_preds.data(), rf_params.n_threads);

        for (uint32_t i = 0; i < num_ex; i++) {
            assert(glm::tests::are_close(preds[i], comp_preds[i], 1e-10));
        }

        printf("Random Forest Classification Test 2 passed!\n");
    }

    ///////////////////////////////////
    // TreeForest Regression Test
    ///////////////////////////////////
    rf_params.task            = snapml::task_t::regression;
    rf_params.split_criterion = snapml::split_t::mse;

    {

        snapml::DenseDataset data
            = glm::tests::generate_small_random_dense_dataset_regression_api(42, false, num_ex, num_ft, 1.0);

        snapml::RandomForestBuilder rf_builder = snapml::RandomForestBuilder(data, &rf_params);

        rf_builder.init();
        rf_builder.build(nullptr);

        snapml::RandomForestModel rf_model = rf_builder.get_model();

        snapml::RandomForestPredictor rf_predictor = snapml::RandomForestPredictor(rf_model);

        rf_predictor.predict(data, preds.data(), rf_params.n_threads);

        double score = glm::metrics::jni::mean_squared_error(data.get().get(), preds.data(), preds.size());

        printf(">> score regression forest: %f\n", score);
        acc_ok = score < 2.5e-2;

        if (!acc_ok)
            printf("Predict regression forest failed.\n");
        assert(acc_ok);

        printf("Random Forest Regression Test 1 passed!\n");

        rf_model.compress(data);

        rf_predictor.predict(data, comp_preds.data(), params.n_threads);

        for (uint32_t i = 0; i < num_ex; i++) {
            assert(glm::tests::are_close(preds[i], comp_preds[i], 1e-10));
        }

        printf("Random Forest Regression Test 2 passed!\n");
    }

    return 0;
}
