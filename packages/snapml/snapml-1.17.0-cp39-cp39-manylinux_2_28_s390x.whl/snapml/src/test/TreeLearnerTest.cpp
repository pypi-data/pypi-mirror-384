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
 * Authors      : Thomas Parnell
 *                Celestine Duenner
 *                Dimitrios Sarigiannis
 *                Andreea Anghel
 *                Nikolas Ioannou
 *
 * End Copyright
 ********************************************************************/

#include "Utils.hpp"
#include "DatasetGenerators.hpp"
#include "Metrics.hpp"
//#include "HistSolver.hpp"
//#include "HistSolverGPUFactory.hpp"
#include "TestUtils.hpp"
#include "DecisionTreePredictor.hpp"
#include "DecisionTreeBuilder.hpp"
#include "DecisionTreeModel.hpp"

bool decision_tree_test(snapml::DecisionTreeParams params, uint32_t num_ex, uint32_t num_ft, double sparsity,
                        bool use_sample_weights, double seed, double& score_pos, double& score_neg)
{

    snapml::DenseDataset                         data;
    std::shared_ptr<snapml::DecisionTreeBuilder> builder;
    snapml::DecisionTreeModel                    model;

    if (params.task == snapml::task_t::classification) {
        data = glm::tests::generate_small_random_dense_dataset_api(seed, false, num_ex, num_ft, sparsity);
    } else {
        data = glm::tests::generate_small_random_dense_dataset_regression_api(seed, false, num_ex, num_ft, sparsity);
    }

    builder = std::static_pointer_cast<snapml::DecisionTreeBuilder>(
        std::make_shared<snapml::DecisionTreeBuilder>(data, &params));

    double thd = (params.task == snapml::task_t::classification) ? 0.0 : 0.5;

    float* const sample_weight = use_sample_weights ? new float[num_ex] : nullptr;
    if (use_sample_weights) {
        assert(nullptr != sample_weight);
        float* labs = data.get()->get_labs();
        for (uint32_t i = 0; i < num_ex; i++) {
            sample_weight[i] = (labs[i] > thd) ? 1.0 : 0.00001;
            // std::cout << labs[i] << " " << thd << " " << sample_weight[i] << std::endl;
        }
    }

    builder->init();
    builder->build(sample_weight);

    std::vector<uint32_t> indices(num_ex);

    // generate indices as in training
    if (params.bootstrap) {
        std::mt19937                            rng_ = std::mt19937(params.random_state);
        std::uniform_int_distribution<uint32_t> uniform_dist(0, num_ex - 1);

        for (uint32_t ex = 0; ex < num_ex; ex++) {
            indices[ex] = uniform_dist(rng_);
        }
    } else {
        for (uint32_t ex = 0; ex < num_ex; ex++) {
            indices[ex] = ex;
        }
    }

    model          = builder->get_model();
    auto predictor = std::make_shared<snapml::DecisionTreePredictor>(model);

    std::vector<double> preds(num_ex);

    score_pos        = 0.0;
    score_neg        = 0.0;
    uint32_t num_pos = 0;
    uint32_t num_neg = 0;

    predictor->predict(data, preds.data());

    std::vector<double> preds_remap(num_ex);
    for (uint32_t i = 0; i < num_ex; i++) {
        preds_remap[i] = preds[indices[i]];
    }

    for (uint32_t ex = 0; ex < num_ex; ex++) {

        double label = data.get()->get_labs()[indices[ex]];

        if (label > thd) {
            num_pos++;
        } else {
            num_neg++;
        }

        if (params.task == snapml::task_t::classification) {
            if (label > 0) {
                score_pos += (preds_remap[ex] == label);
            } else {
                score_neg += (preds_remap[ex] == label);
            }
        } else {
            double diff = preds_remap[ex] - label;
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
            acc_ok = score < 1e-3;
        }
    }

    std::vector<uint8_t> vec;
    model.get(vec); // retrieve

    snapml::DecisionTreeModel new_model;

    new_model.put(vec);

    auto new_predictor = std::make_shared<snapml::DecisionTreePredictor>(new_model);

    std::vector<double> new_pred(num_ex);

    new_predictor->predict(data, new_pred.data());

    for (uint32_t ex = 0; ex < num_ex; ex++) {
        assert(new_pred[ex] == preds[ex]);
    }

    delete[] sample_weight;

    return acc_ok;
}

bool multiclass_decision_tree_test(uint32_t num_ex, uint32_t num_ft, double sparsity, bool use_sample_weights,
                                   double seed, snapml::DecisionTreeParams params, double& score_pos, double& score_neg)
{

    snapml::DenseDataset                         data;
    std::shared_ptr<snapml::DecisionTreeBuilder> builder;
    snapml::DecisionTreeModel                    model;

    data = glm::tests::generate_small_random_dense_dataset_api(seed, false, num_ex, num_ft, sparsity,
                                                               params.num_classes);

    builder = std::static_pointer_cast<snapml::DecisionTreeBuilder>(
        std::make_shared<snapml::DecisionTreeBuilder>(data, &params));

    double       thd           = 0.0;
    float* const sample_weight = use_sample_weights ? new float[num_ex] : nullptr;

    float* labs = data.get()->get_labs();
    for (uint32_t i = 0; i < num_ex; i++) {
        labs[i] = (labs[i] < 0) ? 0 : labs[i];
    }

    if (use_sample_weights) {
        assert(nullptr != sample_weight);
        for (uint32_t i = 0; i < num_ex; i++) {
            sample_weight[i] = (labs[i] > thd) ? 1.0 : 0.00001;
        }
    }

    builder->init();
    builder->build(sample_weight);

    std::vector<uint32_t> indices(num_ex);

    // generate indices as in training
    if (params.bootstrap) {
        std::mt19937                            rng_ = std::mt19937(params.random_state);
        std::uniform_int_distribution<uint32_t> uniform_dist(0, num_ex - 1);

        for (uint32_t ex = 0; ex < num_ex; ex++) {
            indices[ex] = uniform_dist(rng_);
        }
    } else {
        for (uint32_t ex = 0; ex < num_ex; ex++) {
            indices[ex] = ex;
        }
    }

    model          = builder->get_model();
    auto predictor = std::make_shared<snapml::DecisionTreePredictor>(model);

    std::vector<uint32_t> num(params.num_classes, 0);
    std::vector<double>   score(params.num_classes, 0);

    std::vector<double> preds(num_ex);
    std::vector<double> preds_remap(num_ex);
    predictor->predict(data, preds.data());
    for (uint32_t i = 0; i < num_ex; i++) {
        preds_remap[i] = preds[indices[i]];
    }

    for (uint32_t ex = 0; ex < num_ex; ex++) {
        double label = labs[indices[ex]];

        num[(uint32_t)label]++;
        score[(uint32_t)label] += (preds_remap[ex] == label);
    }

    std::vector<double> proba(num_ex * (params.num_classes - 1));
    predictor->predict_proba(data, proba.data());

    // test predict_proba only for classification
    for (uint32_t i = 0; i < proba.size(); i++) {
        assert((proba[i] >= 0) && (proba[i] <= 1));
    }

    uint32_t total_ex    = 0;
    double   score_total = 0;

    for (uint32_t cl = 0; cl < params.num_classes; cl++) {
        total_ex += num[cl];
        score_total += score[cl];
    }
    assert(total_ex == num_ex);

    bool acc_ok = false;

    if (use_sample_weights) {
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

    snapml::DecisionTreeModel new_model;

    new_model.put(vec);

    auto new_predictor = std::make_shared<snapml::DecisionTreePredictor>(new_model);

    std::vector<double> new_pred(num_ex);
    new_predictor->predict(data, new_pred.data());

    for (uint32_t ex = 0; ex < num_ex; ex++) {
        assert(new_pred[ex] == preds[ex]);
    }

    delete[] sample_weight;

    return acc_ok;
}

int main()
{

    uint32_t num_ex   = 100;
    uint32_t num_ft   = 4;
    double   sparsity = 1.0;
    uint32_t seed     = 12312321;

    snapml::DecisionTreeParams params;

    params.max_features = 0; // remains to be tested
    params.hist_nbins   = 256;

    int num_failed_tests = 0;
    int num_ok_tests     = 0;

    // binary tests

    for (int task = 0; task < 2; task++) {

        params.task            = task ? snapml::task_t::classification : snapml::task_t::regression;
        params.split_criterion = task ? snapml::split_t::gini : snapml::split_t::mse;

        for (int bootstrap = 0; bootstrap < 2; bootstrap++) {

            params.bootstrap = bootstrap;

            for (int use_sample_weights = 0; use_sample_weights < 2; use_sample_weights++) {

                for (int use_histograms = 0; use_histograms < 2; use_histograms++) {

                    // in order to verify the behaviour of sample weights, we need to use bounded depth
                    // since for unbounded depth all samples will belong in separate nodes, masking the
                    // effect of sample weighting.
                    // GPU max_depth is currently capped at 20, so in order to verify against CPU
                    // we use depth 20, without histograms we test unbounded depth
                    params.max_depth      = use_sample_weights ? 3 : (use_histograms ? 20 : 0);
                    params.use_histograms = use_histograms;

                    bool ok        = false;
                    params.use_gpu = false;
                    printf(">> task: %c, bootstrap: %d, use_sample_weights: %d, use_histograms: %d, max_depth: %d, "
                           "use_gpu: %d\n",
                           task ? 'c' : 'r', bootstrap, use_sample_weights, use_histograms, params.max_depth,
                           params.use_gpu);

                    double score_pos_cpu, score_neg_cpu;
                    ok = decision_tree_test(params, num_ex, num_ft, sparsity, use_sample_weights, seed, score_pos_cpu,
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
                    printf(">> task: %c, bootstrap: %d, use_sample_weights: %d, use_histograms: %d, max_depth: %d, "
                           "use_gpu: %d\n",
                           task ? 'c' : 'r', bootstrap, use_sample_weights, use_histograms, params.max_depth,
                           params.use_gpu);

                    double score_pos_gpu, score_neg_gpu;
                    ok = decision_tree_test(params, num_ex, num_ft, sparsity, use_sample_weights, seed, score_pos_gpu,
                                            score_neg_gpu);

                    ok &= glm::tests::are_close(score_pos_cpu, score_pos_gpu, 1e-3);
                    ok &= glm::tests::are_close(score_neg_cpu, score_neg_gpu, 1e-3);

                    if (!ok) {
                        printf(">> GPU test FAIL.\n\n");
                        num_failed_tests++;
                    } else {
                        printf(">> GPU test passed.\n\n");
                        num_ok_tests++;
                    }
#endif
                }
            }
        }
    }

    // multiclass tests
    params.task            = snapml::task_t::classification;
    params.split_criterion = snapml::split_t::gini;

    for (int num_cl = 3; num_cl < 5; num_cl++) {
        params.num_classes = num_cl;

        for (int bootstrap = 0; bootstrap < 2; bootstrap++) {
            params.bootstrap = bootstrap;

            for (int use_sample_weights = 0; use_sample_weights < 2; use_sample_weights++) {

                for (int use_histograms = 0; use_histograms < 2; use_histograms++) {
                    // in order to verify the behaviour of sample weights, we need to use bounded depth
                    // since for unbounded depth all samples will belong in separate nodes, masking the
                    // effect of sample weighting.
                    params.max_depth      = use_sample_weights ? 3 : 0;
                    params.use_histograms = use_histograms;

                    bool ok        = false;
                    params.use_gpu = false;
                    printf(">> task: mc-%dclasses, bootstrap: %d, use_sample_weights: %d, use_histograms: %d, "
                           "max_depth: %d\n",
                           num_cl, bootstrap, use_sample_weights, use_histograms, params.max_depth);

                    double score_pos_cpu, score_neg_cpu;
                    ok = multiclass_decision_tree_test(num_ex, num_ft, sparsity, use_sample_weights, seed, params,
                                                       score_pos_cpu, score_neg_cpu);

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
