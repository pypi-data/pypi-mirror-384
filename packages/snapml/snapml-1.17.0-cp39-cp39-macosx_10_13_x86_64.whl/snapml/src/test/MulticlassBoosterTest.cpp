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
    bool acc_ok;

    // generate dataset

    snapml::DenseDataset data
        = glm::tests::generate_small_random_dense_dataset_api(42, false, num_ex, num_ft, 1.0, params.num_classes);

    try {
        snapml::BoosterBuilder builder = snapml::BoosterBuilder(data, snapml::DenseDataset(), params);
        builder.init();
        builder.build(nullptr);

        snapml::BoosterModel model     = builder.get_model();
        auto                 predictor = std::make_shared<snapml::BoosterPredictor>(model);

        std::vector<double> preds(num_ex, 0);
        predictor->predict(data, preds.data(), n_threads);

        double score = glm::metrics::jni::accuracy(data.get().get(), preds.data(), preds.size(), false);
        printf(">> score: %f\n", score);
        acc_ok = score > 0.99;

        std::vector<uint8_t> vec;
        model.get(vec);

        snapml::BoosterModel new_model;
        new_model.put(vec);

        auto new_predictor = std::make_shared<snapml::BoosterPredictor>(new_model);

        std::vector<double> new_preds(num_ex, 0);
        new_predictor->predict(data, new_preds.data(), n_threads);

        for (uint32_t i = 0; i < num_ex; i++)
            assert(glm::tests::are_close(preds[i], new_preds[i], 1e-12));
    } catch (std::exception& e) {
        if (e.what() == std::string("Closed form of ridge regression is not supported on z/OS.")) {
            std::cout << e.what() << std::endl;
            acc_ok = true;
        } else {
            std::cout << "test failed: " << e.what() << std::endl;
            acc_ok = false;
        }
    }

    return acc_ok;
}

int main(const int argc, const char* argv[])
{

    // dataset-specific properties
    uint32_t num_ex = 100;
    uint32_t num_ft = 10;

    uint32_t n_threads = 4;

    snapml::BoosterParams params;

    int num_failed_tests = 0;
    int num_ok_tests     = 0;

    params.objective      = snapml::BoosterParams::objective_t::softmax;
    params.n_regressors   = 100;
    params.learning_rate  = 1.0;
    params.lambda         = 1.0;
    params.n_components   = 300;
    params.verbose        = false;
    params.enable_profile = false;
    params.n_threads      = n_threads;

    params.gpu_ids = std::vector<uint32_t> { 0, 1 };

    std::vector<uint32_t> num_classes_range { 3, 4, 5 };
    std::vector<double>   proba_range { 0.8, 1.0 };
    std::vector<double>   colsample_range { 0.8, 1.0 };
    std::vector<double>   subsample_range { 0.8, 1.0 };
    std::vector<bool>     histograms_range { false, true };

    for (uint32_t num_classes : num_classes_range) {
        for (double select_prob : proba_range) {
            for (double subsample : subsample_range) {
                for (double colsample : colsample_range) {
                    for (bool histograms : histograms_range) {

                        std::vector<std::vector<uint32_t>> gpu_ids_range;
                        gpu_ids_range.push_back(std::vector<uint32_t> {});

                        if (histograms) {
#ifdef WITH_CUDA
                            gpu_ids_range.push_back(std::vector<uint32_t> { 0 });
                            gpu_ids_range.push_back(std::vector<uint32_t> { 0, 1 });
#endif
                        }
                        for (const auto& gpu_ids : gpu_ids_range) {

                            params.num_classes        = num_classes;
                            params.select_probability = select_prob;
                            params.subsample          = subsample;
                            params.colsample_bytree   = colsample;
                            params.use_histograms     = histograms;
                            params.gpu_ids            = gpu_ids;

                            printf(">> num_classes: %u, select_prob: %.3f, colsample: %.2f, subsample: %.2f, "
                                   "histograms: %d, gpus: %d\n",
                                   num_classes, select_prob, colsample, subsample, histograms, (int)gpu_ids.size());

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
