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

bool test_booster(uint32_t num_ex, uint32_t num_ft, const snapml::BoosterParams params, uint32_t n_threads)
{

    // generate dataset

    bool                acc_ok;
    std::vector<double> new_preds(num_ex, 0);
    std::vector<double> preds(num_ex, 0);

    snapml::DenseDataset data;
    if (params.objective == snapml::BoosterParams::objective_t::logloss) {
        data = glm::tests::generate_small_random_dense_dataset_api(42, false, num_ex, num_ft, 1.0);
    } else {
        data = glm::tests::generate_small_random_dense_dataset_regression_api(42, false, num_ex, num_ft, 1.0);
    }

    try {

        snapml::BoosterBuilder builder = snapml::BoosterBuilder(data, snapml::DenseDataset(), params);
        builder.init();
        builder.build(nullptr);

        snapml::BoosterModel model     = builder.get_model();
        auto                 predictor = std::make_shared<snapml::BoosterPredictor>(model);

        predictor->predict(data, preds.data(), n_threads);

        if (params.objective == snapml::BoosterParams::objective_t::logloss) {
            double score = glm::metrics::jni::accuracy(data.get().get(), preds.data(), preds.size(), true);
            printf(">> score: %f\n", score);
            acc_ok = score > 0.99;
        } else {
            double score = glm::metrics::jni::mean_squared_error(data.get().get(), preds.data(), preds.size());
            printf(">> score: %f\n", score);
            acc_ok = score < 1e-3;
        }

        std::vector<uint8_t> vec;
        model.get(vec);

        snapml::BoosterModel new_model;
        new_model.put(vec);

        auto new_predictor = std::make_shared<snapml::BoosterPredictor>(new_model);

        new_predictor->predict(data, new_preds.data(), n_threads);
    } catch (std::exception& e) {
        if (e.what() == std::string("Closed form of ridge regression is not supported on z/OS.")) {
            std::cout << e.what() << std::endl;
            acc_ok = true;
        } else {
            std::cout << "test failed: " << e.what() << std::endl;
            acc_ok = false;
        }
    }

    for (uint32_t i = 0; i < num_ex; i++)
        assert(glm::tests::are_close(preds[i], new_preds[i], 1e-12));

    return acc_ok;
}

int main(const int argc, const char* argv[])
{

    // dataset-specific properties
    uint32_t num_ex = 100;
    uint32_t num_ft = 10;

    uint32_t n_threads = 8;

    snapml::BoosterParams params;

    int num_failed_tests = 0;
    int num_ok_tests     = 0;

    params.n_regressors    = 400;
    params.learning_rate   = 1.0;
    params.lambda          = 1.0;
    params.n_components    = 300;
    params.base_prediction = 0.5;

    std::vector<double> proba_range { 0.0, 0.25, 0.5, 0.75, 1.0 };
    std::vector<double> colsample_range { 0.8, 1.0 };
    std::vector<double> subsample_range { 0.8, 1.0 };
    std::vector<bool>   histograms_range { false, true };

    for (int task = 0; task < 4; task++) {
        for (double select_prob : proba_range) {
            for (double subsample : subsample_range) {
                for (double colsample : colsample_range) {
                    for (bool histograms : histograms_range) {

                        std::vector<std::vector<uint32_t>> gpu_ids_range;
                        gpu_ids_range.push_back(std::vector<uint32_t> {});
                        if (histograms) {
#ifdef WITH_CUDA
                            gpu_ids_range.push_back(std::vector<uint32_t> { 0 });
#endif
                        }

                        for (auto& gpu_ids : gpu_ids_range) {

                            params.select_probability = select_prob;
                            params.subsample          = subsample;
                            params.colsample_bytree   = colsample;
                            params.use_histograms     = histograms;
                            params.gpu_ids            = gpu_ids;
                            params.n_threads          = n_threads;

                            if (task == 0) {
                                params.objective = snapml::BoosterParams::objective_t::mse;
                                printf(">> task: 'r', objective: 'm' select_prob: %.3f, colsample: %.2f, subsample: "
                                       "%.2f, histograms: %d, "
                                       "gpus: %d\n",
                                       select_prob, colsample, subsample, histograms, (int)gpu_ids.size());
                            } else if (task == 1) {
                                params.objective = snapml::BoosterParams::objective_t::poisson;
                                printf(">> task: 'r', objective: 'p' select_prob: %.3f, colsample: %.2f, subsample: "
                                       "%.2f, histograms: %d, "
                                       "gpus: %d\n",
                                       select_prob, colsample, subsample, histograms, (int)gpu_ids.size());
                            } else if (task == 2) {
                                params.objective = snapml::BoosterParams::objective_t::quantile;
                                printf(">> task: 'r', objective: 'q' select_prob: %.3f, colsample: %.2f, subsample: "
                                       "%.2f, histograms: %d, "
                                       "gpus: %d\n",
                                       select_prob, colsample, subsample, histograms, (int)gpu_ids.size());
                            } else {
                                params.objective = snapml::BoosterParams::objective_t::logloss;
                                printf(">> task: 'c', objective: 'l' select_prob: %.3f, colsample: %.2f, subsample: "
                                       "%.2f, histograms: %d, "
                                       "gpus: %d\n",
                                       select_prob, colsample, subsample, histograms, (int)gpu_ids.size());
                            }

                            bool ok = test_booster(num_ex, num_ft, params, n_threads);

                            if (!ok) {
                                printf(">> Test FAILED.\n\n");
                                num_failed_tests++;
                            } else {
                                printf(">> Test passed.\n\n");
                                num_ok_tests++;
                            }
                        }
                    }
                }
            }
        }
    }

    printf("-------- test summary --------\n");
    printf(">>>> num_failed_tests: %d\n", num_failed_tests);
    printf(">>>> num_ok_tests:     %d\n", num_ok_tests);

    assert(num_failed_tests == 0);

    return 0;
}
