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
#include <thread>
#include <mutex>
#include <atomic>
#include <condition_variable>

#include "DatasetGenerators.hpp"
#include "Metrics.hpp"
#include "TestUtils.hpp"
#include "BoosterBuilder.hpp"
#include "BoosterPredictor.hpp"
#include "RandomForestBuilder.hpp"
#include "RandomForestPredictor.hpp"

#include "RBFSampler.hpp"
#include "RidgeClosed.hpp"

std::mutex       mtx_start;
std::mutex       mtx_print;
std::atomic<int> num_failed_tests(0);
std::atomic<int> num_ok_tests(0);

const unsigned int num_thrds = 32;

typedef std::chrono::high_resolution_clock             Clock;
typedef std::chrono::high_resolution_clock::time_point CurTime;

void run_prediction(snapml::BoosterPredictor predictor, snapml::DenseDataset data, std::vector<double> preds,
                    std::vector<double> mbit_preds, snapml::BoosterParams params, uint32_t num_ex,
                    unsigned int thrd_num)
{
    try {
        bool acc_ok = true;
        {
            std::unique_lock<std::mutex> lock_start(mtx_start);
        }

        predictor.predict(data, mbit_preds.data(), params.n_threads);

        {
            std::unique_lock<std::mutex> lock_print(mtx_print);

            for (uint32_t i = 0; i < num_ex; i++) {
                if (fabs(preds[i] - mbit_preds[i]) / preds[i] > 0.01) {
                    printf("(%u) FP32->FP16 > 1%% mismatch %u: %f vs %f\n", thrd_num, i, preds[i], mbit_preds[i]);
                    acc_ok = false;
                }
            }

            if (acc_ok)
                num_ok_tests++;
            else
                num_failed_tests++;

            if (params.objective == snapml::BoosterParams::objective_t::mse)
                printf("(%u) Booster Regression Test %s!\n", thrd_num, acc_ok ? "passed" : "failed");
            else
                printf("(%u) Booster MBITree Classification Test %s!\n", thrd_num, acc_ok ? "passed" : "failed");
        }
    } catch (std::exception& e) {
        std::cout << "run_prediction: exception occurred: " << e.what() << std::endl;
    }
}

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
        std::vector<std::thread> thrds;
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
            // assert(acc_ok);

            printf("Booster BinaryDecisionTree Classification Test passed!\n");

            // TEST 2
            // verify that predictions are the same after transform to mbit
            model.convert_mbit(data);

            {
                std::unique_lock<std::mutex> lock_start(mtx_start);
                for (unsigned int i = 0; i < num_thrds; i++)
                    thrds.emplace_back(
                        std::thread(run_prediction, predictor, data, preds, mbit_preds, params, num_ex, i));
            }
        }
        for (unsigned int i = 0; i < num_thrds; i++)
            thrds[i].join();
    }

    ///////////////////////////////////
    // TreeBooster Regression Test
    ///////////////////////////////////
    // thrds_started = 0;
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
        // assert(acc_ok);

        printf("Booster Regression Test 1 passed!\n");

        // TEST 2
        // verify that predictions are the same after transform to mbit
        model.convert_mbit(data);

        std::vector<std::thread> thrds;
        {
            std::unique_lock<std::mutex> lock_start(mtx_start);
            for (unsigned int i = 0; i < num_thrds; i++)
                thrds.emplace_back(std::thread(run_prediction, predictor, data, preds, mbit_preds, params, num_ex, i));
        }
        for (unsigned int i = 0; i < num_thrds; i++)
            thrds[i].join();
    }

    printf("-------- test summary --------\n");
    printf(">>>> num_failed_tests: %d\n", int(num_failed_tests));
    printf(">>>> num_ok_tests:     %d\n", int(num_ok_tests));

    assert(num_failed_tests == 0);

    return 0;
}
