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
#include "ForestBuilder.hpp"
#include "RandomForestPredictor.hpp"
#include "ModelData.hpp"

typedef std::chrono::high_resolution_clock             Clock;
typedef std::chrono::high_resolution_clock::time_point CurTime;

inline float t_elapsed(const CurTime& t0)
{
    CurTime t1  = Clock::now();
    auto    dur = t1 - t0;
    return (float)dur.count() / 1.0e6;
}

int main(const int argc, const char* argv[])
{
    // dataset-specific properties
    uint32_t depth  = 6;
    uint32_t num_ex = 512;
    uint32_t num_ft = 200;

    uint32_t num_threads = 4;
    uint32_t num_batches = 10;
    bool     dbg         = false;

    if (argc > 1)
        depth = atoi(argv[1]);
    if (argc > 2)
        num_ex = atoi(argv[2]);
    if (argc > 3)
        num_threads = atoi(argv[3]);
    if (argc > 4)
        num_batches = atoi(argv[4]);
    if (argc > 5)
        dbg = atoi(argv[5]);

    CurTime tstart, tend, t0;
    tstart = Clock::now();

    ///////////////////////////////////
    // TreeBooster Classification Test
    ///////////////////////////////////
    snapml::BoosterParams     params;
    RBFSamplerParams          rbf_params;
    glm::RidgeClosed::param_t ridge_params;

    params.objective                      = snapml::BoosterParams::objective_t::logloss;
    params.n_regressors                   = 100;
    params.learning_rate                  = 0.1;
    params.tree_params.select_probability = 1.0;
    params.n_threads                      = num_threads;

    params.min_max_depth = 6;
    params.max_max_depth = 6;

    uint64_t num_nz         = (uint64_t)num_ex * num_ft;
    uint32_t num_partitions = 1;
    uint32_t partition_id   = 0;
    uint32_t this_pt_offset = 0;

    // Load Model
    uint8_t* ba      = (depth == 6) ? ba6 : (depth == 7) ? ba7 : ba8;
    uint64_t ba_size = (depth == 6) ? ba6_size : (depth == 7) ? ba7_size : ba8_size;

    // Load Dataset
    t0                 = Clock::now();
    int    num_repeats = (num_ex + 1023) / 1024;
    float* X_large     = new float[num_repeats * 1024 * num_ft];
    float* y_large     = new float[num_repeats * 1024];
    for (int i = 0; i < num_repeats; i++) {
        std::copy(X, X + 1024 * num_ft, X_large + i * 1024 * num_ft);
        std::copy(y, y + 1024, y_large + i * 1024);
    }
    std::shared_ptr<glm::DenseDataset> data_p
        = std::make_shared<glm::DenseDataset>(false, num_ex, num_ft, num_ex, num_partitions, partition_id,
                                              this_pt_offset, num_nz, num_pos, num_neg, y_large, X_large, false);
    snapml::DenseDataset data;
    data.get().swap(data_p);

    // Load Model
    auto model = std::make_shared<tree::BoosterModel>();
    model->put(ba, ba_size, 0, ba_size);
    float t_load = t_elapsed(t0);

    // Run default (BDT) prediction
    auto                predictor = std::make_shared<snapml::BoosterPredictor>(model);
    std::vector<double> preds(num_ex, 0);
    t0 = Clock::now();
    predictor->predict(data, preds.data(), params.n_threads);
    float t_bdt_pred = t_elapsed(t0);

    // Run compressed prediction
    model->compress(data);
    std::vector<double> comp_preds(num_ex, 0);
    t0 = Clock::now();
    predictor->predict(data, comp_preds.data(), params.n_threads);
    float t_comp_pred = t_elapsed(t0);

    // Run MBIT prediction
    auto model_mbit     = std::make_shared<tree::BoosterModel>();
    auto predictor_mbit = std::make_shared<snapml::BoosterPredictor>(model_mbit);
    model_mbit->put(ba, ba_size, 0, ba_size);
    t0 = Clock::now();
    model_mbit->convert_mbit(data);
    float               t_gen_tree = t_elapsed(t0);
    std::vector<double> mbit_preds(num_ex, 0);

    float* t_mbit_pred = new float[num_batches];
    for (int bn = 0; bn < num_batches; bn++) {
        t0 = Clock::now();
        predictor_mbit->predict(data, mbit_preds.data(), params.n_threads);
        t_mbit_pred[bn] = t_elapsed(t0);
        printf("t_x_stick: %.2fms, t_step12: %.2fms + t_step34: %.2fms + t_step5: %.2fms = "
               "t_zaiu_pred: %.2fms, t_unstick: %.fus, t_aggr: %.fus\n",
               model_mbit->mbi_tree_ensemble_model->profile_ens.t_x_stick,
               model_mbit->mbi_tree_ensemble_model->profile_ens.t_step12,
               model_mbit->mbi_tree_ensemble_model->profile_ens.t_step34,
               model_mbit->mbi_tree_ensemble_model->profile_ens.t_step5,
               model_mbit->mbi_tree_ensemble_model->profile_ens.t_zaiu_pred,
               1000.0 * model_mbit->mbi_tree_ensemble_model->profile_ens.t_unstick,
               1000.0 * model_mbit->mbi_tree_ensemble_model->profile_ens.t_aggr);
    }

    if (dbg) {
        float score = glm::metrics::jni::accuracy(data.get().get(), mbit_preds.data(), preds.size(), true);
        printf(">> score classification mbit booster: %f\n", score);
    }

    tend        = Clock::now();
    auto  dur   = tend - tstart;
    float t_tot = (float)dur.count() / 1.0e6;

    printf("t_load: %.2fms, t_bdt_pred: %.2fms, t_comp_pred: %.2fms, t_gen_tree: %.2fms, "
           "t_init_tree: %.2fms, t_alloc_res: %.2fms, t_tot: %.2fms\n",
           t_load, t_bdt_pred, t_comp_pred, t_gen_tree, model_mbit->mbi_tree_ensemble_model->profile_ens.t_init_tree,
           model_mbit->mbi_tree_ensemble_model->profile_ens.t_alloc_res, t_tot);
    printf("t_mbit_pred: ");
    for (int bn = 0; bn < num_batches - 1; bn++)
        printf("%.2fms, ", t_mbit_pred[bn]);
    printf("%.2fms\n", t_mbit_pred[num_batches - 1]);

    if (dbg)
        for (uint32_t i = 0; i < std::min((int)num_ex, 1024); i++)
            if (preds[i] != mbit_preds[i])
                printf("%u: %f vs %f\n", i, preds[i], mbit_preds[i]);

    return 0;
}
