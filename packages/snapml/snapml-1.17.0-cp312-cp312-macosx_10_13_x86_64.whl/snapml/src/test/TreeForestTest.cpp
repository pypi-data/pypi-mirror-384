/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2018, 2021
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Andreea Anghel
 *                Celestine Duenner
 *                Thomas Parnell
 *
 *
 * End Copyright
 ********************************************************************/

#include "DatasetGenerators.hpp"
#include "TestUtils.hpp"
#include "RandomForestParams.hpp"
#include "RandomForestBuilder.hpp"
#include "RandomForestModel.hpp"
#include "RandomForestPredictor.hpp"

bool tree_forest_test(uint32_t num_ex, uint32_t num_ft, double sparsity, bool use_sample_weights, double seed,
                      snapml::RandomForestParams params, double& score_pos, double& score_neg)
{

    snapml::DenseDataset data;
    if (params.task == snapml::task_t::classification) {
        data = glm::tests::generate_small_random_dense_dataset_api(seed, false, num_ex, num_ft, sparsity);
    } else {
        data = glm::tests::generate_small_random_dense_dataset_regression_api(seed, false, num_ex, num_ft, sparsity);
    }

    snapml::RandomForestBuilder builder = snapml::RandomForestBuilder(data, &params);

    double thd = (params.task == snapml::task_t::classification) ? 0.0 : 0.5;

    float* const sample_weight = use_sample_weights ? new float[num_ex] : nullptr;
    if (use_sample_weights) {
        assert(nullptr != sample_weight);
        float* labs = data.get()->get_labs();
        for (uint32_t i = 0; i < num_ex; i++) {
            sample_weight[i] = (labs[i] > thd) ? 1.0 : 0.00001;
        }
    }

    builder.init();
    builder.build(sample_weight);

    snapml::RandomForestModel model = builder.get_model();

    snapml::RandomForestPredictor predictor = snapml::RandomForestPredictor(model);

    std::vector<double> preds(num_ex);
    predictor.predict(data, preds.data(), params.n_threads);

    score_pos        = 0.0;
    score_neg        = 0.0;
    uint32_t num_pos = 0;
    uint32_t num_neg = 0;

    for (uint32_t ex = 0; ex < num_ex; ex++) {

        double label = data.get()->get_labs()[ex];

        if (label > thd) {
            num_pos++;
        } else {
            num_neg++;
        }

        if (params.task == snapml::task_t::classification) {
            if (label > 0) {
                score_pos += (preds[ex] == label);
            } else {
                score_neg += (preds[ex] == label);
            }
        } else {
            double diff = preds[ex] - label;
            if (label > thd) {
                score_pos += diff * diff;
            } else {
                score_neg += diff * diff;
            }
        }
    }

    assert(num_pos + num_neg == num_ex);

    bool acc_ok = false;

    if (use_sample_weights) {
        score_pos /= num_pos;
        score_neg /= num_neg;

        printf(">> score_pos: %f, score_neg: %f\n", score_pos, score_neg);

        if (params.task == snapml::task_t::classification) {
            acc_ok = score_pos > score_neg;
        } else {
            acc_ok = score_pos < score_neg;
        }

    } else {

        double score = (score_pos + score_neg) / (num_pos + num_neg);
        score_pos    = score;
        score_neg    = score;
        printf(">> score: %f\n", score);

        if (params.task == snapml::task_t::classification) {
            acc_ok = score > 0.99;
        } else {
            acc_ok = score < 2e-2;
        }
    }

    std::vector<uint8_t> vec;
    model.get(vec); // retrieve

    snapml::RandomForestModel new_model;

    new_model.put(vec);

    snapml::RandomForestPredictor new_predictor = snapml::RandomForestPredictor(new_model);

    std::vector<double> new_preds(num_ex);
    new_predictor.predict(data, new_preds.data(), params.n_threads);

    for (uint32_t i = 0; i < num_ex; i++)
        assert(glm::tests::are_close(preds[i], new_preds[i], 1e-12));

    delete[] sample_weight;

    return acc_ok;
}

bool tree_forest_mc_test(uint32_t num_ex, uint32_t num_ft, double sparsity, bool use_sample_weights, double seed,
                         snapml::RandomForestParams params, double& score_pos, double& score_neg)
{

    snapml::DenseDataset data;
    data = glm::tests::generate_small_random_dense_dataset_api(seed, false, num_ex, num_ft, sparsity,
                                                               params.num_classes);

    snapml::RandomForestBuilder builder = snapml::RandomForestBuilder(data, &params);

    double thd  = 0.0;
    float* labs = data.get()->get_labs();

    float* const sample_weight = use_sample_weights ? new float[num_ex] : nullptr;
    if (use_sample_weights) {
        assert(nullptr != sample_weight);

        for (uint32_t i = 0; i < num_ex; i++) {
            sample_weight[i] = (labs[i] > thd) ? 1.0 : 0.00001;
        }
    }

    for (uint32_t i = 0; i < num_ex; i++) {
        if (labs[i] < 0)
            labs[i] = 0;
    }

    builder.init();
    builder.build(sample_weight);

    snapml::RandomForestModel model = builder.get_model();

    snapml::RandomForestPredictor predictor = snapml::RandomForestPredictor(model);

    std::vector<double> preds(num_ex);
    predictor.predict(data, preds.data(), params.n_threads);

    for (uint32_t i = 0; i < num_ex; i++) {
        if (preds[i] < 0)
            preds[i] = 0;
    }

    uint32_t num_classes = params.num_classes;

    std::vector<uint32_t> num(num_classes, 0);
    std::vector<double>   score(num_classes, 0);

    for (uint32_t ex = 0; ex < num_ex; ex++) {
        double label = labs[ex];
        num[(uint32_t)label]++;
        score[(uint32_t)label] += (preds[ex] == label);
    }

    // test predict_proba only for classification
    std::vector<double> preds_;
    if (params.task == snapml::task_t::classification) {
        preds_.resize(num_ex * (params.num_classes - 1));
        predictor.predict_proba(data, preds_.data(), params.n_threads);

        for (uint32_t ex = 0; ex < num_ex; ex++) {
            double proba_sum = 0.0;
            for (uint32_t cl = 0; cl < num_classes - 1; cl++) {
                // std::cout << preds_[cl+ex*(params.num_classes-1)] << std::endl;
                proba_sum += preds_[cl + ex * (params.num_classes - 1)];
                assert((preds_[cl + ex * (params.num_classes - 1)] >= 0)
                       && (preds_[cl + ex * (params.num_classes - 1)] <= 1));
            }
            assert((proba_sum >= 0) && (proba_sum <= 1));
        }
    }

    uint32_t total_ex    = 0;
    double   score_total = 0;

    for (uint32_t cl = 0; cl < num_classes; cl++) {
        total_ex += num[cl];
        score_total += score[cl];
    }

    assert(total_ex == num_ex);

    bool acc_ok = false;

    if (use_sample_weights) {
        // score_pos /= num[1];
        // score_neg /= num[0];
        score_pos = (score_total - score[0]) / (num_ex - num[0]);
        score_neg = score[0] / num[0];
        printf(">> score_pos: %f, score_neg: %f\n", score_pos, score_neg);
        acc_ok = score_pos > score_neg;
    } else {
        double score = score_total / num_ex;
        score_pos    = score;
        score_neg    = score;
        printf(">> score: %f\n", score);
        acc_ok = score > 0.99;
    }
    std::vector<uint8_t> vec;
    model.get(vec); // retrieve

    snapml::RandomForestModel new_model;
    new_model.put(vec);

    snapml::RandomForestPredictor new_predictor = snapml::RandomForestPredictor(new_model);

    std::vector<double> new_preds(num_ex);
    new_predictor.predict(data, new_preds.data(), params.n_threads);
    for (uint32_t ex = 0; ex < num_ex; ex++) {
        if (new_preds[ex] < 0)
            new_preds[ex] = 0;
        assert(glm::tests::are_close(preds[ex], new_preds[ex], 1e-12));
    }

    delete[] sample_weight;

    return acc_ok;
}

int main()
{

    uint32_t num_ex   = 10000;
    uint32_t num_ft   = 30;
    double   sparsity = 1.0;
    uint32_t seed     = 12312321;

    // configuration to test:
    // task: {0: 'r', 1: 'c'}
    //   max_features: sqrt, 0
    //     sample_weights: {false; true}
    //       use_hist: {false; true}
    //         use_gpu: {false, true} dep[use_hist]
    //           gpu_ids: {[0],[0,1]} dep[: use_gpu, use_hist]

    snapml::RandomForestParams params;
    params.n_trees    = 16;
    params.n_threads  = 4;
    params.hist_nbins = 256;

    int num_failed_tests = 0;
    int num_ok_tests     = 0;

    for (int task = 0; task < 2; task++) {

        params.task            = task ? snapml::task_t::classification : snapml::task_t::regression;
        params.split_criterion = task ? snapml::split_t::gini : snapml::split_t::mse;

        for (int max_features = 0; max_features < 2; max_features++) {

            params.max_features = max_features ? floor(sqrt(num_ft)) : 0;

            for (int use_sample_weights = 0; use_sample_weights < 2; use_sample_weights++) {

                for (int use_histograms = 0; use_histograms < 2; use_histograms++) {

                    // in order to verify the behaviour of sample weights, we need to use bounded depth
                    // since for unbounded depth all samples will belong in separate nodes, masking the
                    // effect of sample weighting.
                    // GPU max_depth is currently capped at 20, so in order to verify against CPU
                    // we use depth 20, without histograms we test unbounded depth
                    params.max_depth      = use_sample_weights ? 3 : 0;
                    params.use_histograms = use_histograms;

                    bool ok        = false;
                    params.use_gpu = false;
                    printf(">> task: %c, max_features %d, use_sample_weights: %d, use_histograms: %d, max_depth: %d, "
                           "num_gpus: %d\n",
                           task ? 'c' : 'r', params.max_features, use_sample_weights, use_histograms, params.max_depth,
                           0);

                    double score_pos_cpu, score_neg_cpu;
                    ok = tree_forest_test(num_ex, num_ft, sparsity, use_sample_weights, seed, params, score_pos_cpu,
                                          score_neg_cpu);

                    if (!ok) {
                        printf(">> CPU test FAIL.\n\n");
                        num_failed_tests++;
                    } else {
                        printf(">> CPU test passed.\n\n");
                        num_ok_tests++;
                    }

                    if (!use_histograms)
                        continue;
#ifdef WITH_CUDA
                    params.use_gpu = true;
                    params.gpu_ids.resize(0);

                    for (int gpu_id = 0; gpu_id < 1; gpu_id++) {

                        params.gpu_ids.push_back(gpu_id);

                        printf(">> task: %c, max_features: %d, use_sample_weights: %d, use_histograms: %d, max_depth: "
                               "%d, num_gpus: %d\n",
                               task ? 'c' : 'r', params.max_features, use_sample_weights, use_histograms,
                               params.max_depth, (int)params.gpu_ids.size());

                        double score_pos_gpu, score_neg_gpu;
                        ok = tree_forest_test(num_ex, num_ft, sparsity, use_sample_weights, seed, params, score_pos_gpu,
                                              score_neg_gpu);

                        // if max_features is on, the features selected by GPU can never exactly match that of CPU
                        double thd = 0.05;

                        ok &= glm::tests::are_close(score_pos_cpu, score_pos_gpu, thd);
                        ok &= glm::tests::are_close(score_neg_cpu, score_neg_gpu, thd);

                        if (!ok) {
                            printf(">> GPU test FAIL.\n\n");
                            num_failed_tests++;
                        } else {
                            printf(">> GPU test passed.\n\n");
                            num_ok_tests++;
                        }
                    }
#endif
                }
            }
        }
    }

    // multiclass tests
    for (int num_cl = 3; num_cl < 4; num_cl++) {
        params.num_classes     = num_cl;
        params.task            = snapml::task_t::classification;
        params.split_criterion = snapml::split_t::gini;

        for (int max_features = 0; max_features < 2; max_features++) {
            params.max_features = max_features ? floor(sqrt(num_ft)) : 0;

            for (int use_sample_weights = 0; use_sample_weights < 2; use_sample_weights++) {

                for (int use_histograms = 0; use_histograms < 2; use_histograms++) {

                    // in order to verify the behaviour of sample weights, we need to use bounded depth
                    // since for unbounded depth all samples will belong in separate nodes, masking the
                    // effect of sample weighting.
                    params.max_depth      = use_sample_weights ? 3 : 0;
                    params.use_histograms = use_histograms;

                    bool ok        = false;
                    params.use_gpu = false;
                    printf(">> task: mc%d, max_features %d, use_sample_weights: %d, use_histograms: %d, max_depth: %d, "
                           "num_gpus: %d\n",
                           num_cl, params.max_features, use_sample_weights, use_histograms, params.max_depth, 0);

                    double score_pos_cpu, score_neg_cpu;
                    ok = tree_forest_mc_test(num_ex, num_ft, sparsity, use_sample_weights, seed, params, score_pos_cpu,
                                             score_neg_cpu);

                    if (!ok) {
                        printf(">> CPU test FAIL.\n\n");
                        num_failed_tests++;
                    } else {
                        printf(">> CPU test passed.\n\n");
                        num_ok_tests++;
                    }

                    if (!use_histograms)
                        continue;
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
