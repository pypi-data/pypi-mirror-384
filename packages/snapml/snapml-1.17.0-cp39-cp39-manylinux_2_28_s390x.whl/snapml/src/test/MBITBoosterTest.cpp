/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2018, 2020
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
#include "BoosterBuilder.hpp"
#include "BoosterPredictor.hpp"
#include "RandomForestBuilder.hpp"
#include "RandomForestPredictor.hpp"

#include "RBFSampler.hpp"
#include "RidgeClosed.hpp"

typedef std::chrono::high_resolution_clock             Clock;
typedef std::chrono::high_resolution_clock::time_point CurTime;

int main(const int argc, const char* argv[])
{
    // dataset-specific properties
    uint32_t num_ex    = 512;
    uint32_t num_ft    = 200;
    uint32_t num_trees = 100;

    uint32_t num_threads = 4;

    if (argc > 1)
        num_ex = atoi(argv[1]);
    if (argc > 2)
        num_threads = atoi(argv[2]);
    if (argc > 3)
        num_trees = atoi(argv[3]);
    if (argc > 4)
        num_ft = atoi(argv[4]);

    bool acc_ok = false;

    // vectors for predictions
    std::vector<double> preds(num_ex, 0);
    std::vector<double> mbit_preds(num_ex, 0);

    ///////////////////////////////////
    // TreeBooster Classification Test
    ///////////////////////////////////
    snapml::BoosterParams params;

    params.objective          = snapml::BoosterParams::objective_t::logloss;
    params.n_regressors       = num_trees;
    params.learning_rate      = 0.1;
    params.select_probability = 1.0;
    params.n_threads          = num_threads;
    params.min_max_depth      = 6;
    params.max_max_depth      = 6;

    {

        std::shared_ptr<glm::DenseDataset> data_p
            = glm::tests::generate_small_random_dense_dataset(42, false, num_ex, num_ft, 1.0);

        snapml::DenseDataset data;
        data.set(data_p);

        snapml::BoosterBuilder builder = snapml::BoosterBuilder(data, snapml::DenseDataset(), params);

        builder.init();
        builder.build(nullptr);

        snapml::BoosterModel model = builder.get_model();

        snapml::BoosterPredictor predictor(model);

        predictor.predict(data, preds.data(), params.n_threads);

        // TEST 1
        // verify training data is over-fit
        double score = glm::metrics::jni::accuracy(data.get().get(), preds.data(), preds.size(), true);
        printf(">> score classification booster: %f\n", score);
        acc_ok = score > 0.985;
        if (!acc_ok)
            printf("Predict classification booster failed.\n");
        assert(acc_ok);

        printf("Booster BinaryDecisionTree Classification Test passed!\n");

        // TEST 2
        // verify that predictions are the same after transform to mbit
        model.convert_mbit(data);

        predictor.predict(data, mbit_preds.data(), params.n_threads);

        score = glm::metrics::jni::accuracy(data.get().get(), mbit_preds.data(), preds.size(), true);
        printf(">> score classification mbit booster: %f\n", score);
        acc_ok = score > 0.985;
        if (!acc_ok)
            printf("Predict classification booster failed.\n");
        assert(acc_ok);

        for (uint32_t i = 0; i < num_ex; i++) {
            if (fabs(preds[i] - mbit_preds[i]) / preds[i] > 0.01) {
                printf("FP32->FP16 > 1%% mismatch %u: %f vs %f\n", i, preds[i], mbit_preds[i]);
                acc_ok = false;
            }
        }

        if (!acc_ok)
            printf("Predict classification booster failed.\n");
        assert(acc_ok);

        printf("Booster MBITree Classification Test passed!\n");
    }

    ///////////////////////////////////
    // TreeBooster Regression Test
    ///////////////////////////////////
    params.objective = snapml::BoosterParams::objective_t::mse;
    {

        std::shared_ptr<glm::DenseDataset> data_p
            = glm::tests::generate_small_random_dense_dataset_regression(42, false, num_ex, num_ft, 1.0);

        snapml::DenseDataset data;
        data.set(data_p);

        snapml::BoosterBuilder builder = snapml::BoosterBuilder(data, snapml::DenseDataset(), params);

        builder.init();
        builder.build(nullptr);

        snapml::BoosterModel model = builder.get_model();

        snapml::BoosterPredictor predictor(model);

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
        // verify that predictions are the same after transform to mbit
        model.convert_mbit(data);

        predictor.predict(data, mbit_preds.data(), params.n_threads);

        for (uint32_t i = 0; i < num_ex; i++) {
            if (fabs(preds[i] - mbit_preds[i]) / preds[i] > 0.01) {
                printf("FP32->FP16 > 1%% mismatch %u: %f vs %f\n", i, preds[i], mbit_preds[i]);
                acc_ok = false;
            }
        }

        if (!acc_ok)
            printf("Predict regression booster failed.\n");
        assert(acc_ok);

        printf("Booster Regression Test 2 passed!\n");
    }

    ///////////////////////////////////
    // TreeForest Regression Test
    ///////////////////////////////////
    snapml::RandomForestParams rf_params;
    rf_params.n_trees         = 16;
    rf_params.n_threads       = num_threads;
    rf_params.hist_nbins      = 256;
    rf_params.use_gpu         = false;
    rf_params.task            = snapml::task_t::regression;
    rf_params.split_criterion = snapml::split_t::mse;

    {

        std::shared_ptr<glm::DenseDataset> data_p
            = glm::tests::generate_small_random_dense_dataset_regression(42, false, num_ex, num_ft, 1.0);

        snapml::DenseDataset data;
        data.set(data_p);

        snapml::RandomForestBuilder rf_builder = snapml::RandomForestBuilder(data, &rf_params);

        rf_builder.init();
        rf_builder.build(nullptr);

        snapml::RandomForestModel rf_model = rf_builder.get_model();

        snapml::RandomForestPredictor rf_predictor(rf_model);

        rf_predictor.predict(data, preds.data(), rf_params.n_threads);

        // TEST 1
        // verify training data is over-fit
        double   score_pos = 0.0;
        double   score_neg = 0.0;
        uint32_t num_pos   = 0;
        uint32_t num_neg   = 0;
        double   thd       = 0.5;

        for (uint32_t ex = 0; ex < num_ex; ex++) {
            double label = data.get()->get_labs()[ex];
            double diff  = preds[ex] - label;

            if (label > thd) {
                num_pos++;
                score_pos += diff * diff;
            } else {
                num_neg++;
                score_neg += diff * diff;
            }
        }
        assert(num_pos + num_neg == num_ex);
        double score = (score_pos + score_neg) / (num_pos + num_neg);
        score_pos    = score;
        score_neg    = score;
        printf(">> score regression forest: %f\n", score);
        acc_ok = score < 2.5e-2;
        if (!acc_ok)
            printf("Predict regression forest failed.\n");
        assert(acc_ok);

        printf("Random Forest Regression Test 1 passed!\n");

        // TEST 2
        // verify that predictions are the same after mbit
        rf_model.convert_mbit(data);

        rf_predictor.predict(data, mbit_preds.data(), rf_params.n_threads);

        for (uint32_t i = 0; i < num_ex; i++) {
            if (fabs(preds[i] - mbit_preds[i]) / preds[i] > 0.01) {
                printf("FP32->FP16 > 1%% mismatch %u: %f vs %f\n", i, preds[i], mbit_preds[i]);
                acc_ok = false;
            }
        }

        if (!acc_ok)
            printf("Predict regression forest failed.\n");
        assert(acc_ok);

        printf("Random Forest Regression Test 2 passed!\n");
    }

    return 0;
}
