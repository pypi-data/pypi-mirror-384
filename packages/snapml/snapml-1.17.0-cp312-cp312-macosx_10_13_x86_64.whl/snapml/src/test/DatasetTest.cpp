/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2018
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
 *
 * End Copyright
 ********************************************************************/

#include "Loaders.hpp"
#include <iostream>
#include "GLMUtils.hpp"
#include "DualLogisticRegression.hpp"
#include "PrimalLogisticRegression.hpp"
#include "UnitTests.hpp"
#include <memory>

template <class O> void data_test(std::shared_ptr<O> obj, bool add_bias)
{

    using namespace glm;
    using namespace std;

    uint32_t num_ex   = 20;
    uint32_t num_ft   = 50;
    double   sparsity = 0.1;

    bool transpose = is_primal<O>::value ? true : false;

    uint32_t                  seed = 12312321;
    shared_ptr<SparseDataset> data1
        = tests::generate_small_random_dataset(seed, transpose, num_ex, num_ft, sparsity, true);
    shared_ptr<L2SparseDataset> data2
        = tests::generate_small_random_l2_dataset(seed, transpose, num_ex, num_ft, sparsity);
    shared_ptr<DenseDataset> data3
        = tests::generate_small_random_dense_dataset(seed, transpose, num_ex, num_ft, sparsity, 2, true);

    uint32_t num_epochs = 1000;
    double   tol        = 0.001;

    double cost1 = experiment<SparseDataset, O>(data1, obj, num_epochs, tol, std::vector<uint32_t> {}, 1, add_bias);
    double cost2 = experiment<L2SparseDataset, O>(data2, obj, num_epochs, tol, std::vector<uint32_t> {}, 1, add_bias);
    double cost3 = experiment<DenseDataset, O>(data3, obj, num_epochs, tol, std::vector<uint32_t> {}, 1, add_bias);
    cout << "cost1 = " << cost1 << endl;
    cout << "cost2 = " << cost2 << endl;
    cout << "cost3 = " << cost3 << endl;
    assert(tests::are_close(cost1, cost2, 1e-3));
    assert(tests::are_close(cost1, cost3, 1e-3));

#ifdef WITH_CUDA
    double cost4 = experiment<SparseDataset, O>(data1, obj, num_epochs, tol, std::vector<uint32_t> { 0 }, 32, add_bias);
    double cost5
        = experiment<L2SparseDataset, O>(data2, obj, num_epochs, tol, std::vector<uint32_t> { 0 }, 32, add_bias);
    double cost6 = experiment<DenseDataset, O>(data3, obj, num_epochs, tol, std::vector<uint32_t> { 0 }, 32, add_bias);
    cout << "cost4 = " << cost4 << endl;
    cout << "cost5 = " << cost5 << endl;
    cout << "cost6 = " << cost6 << endl;
    assert(tests::are_close(cost1, cost4, 1e-3));
    assert(tests::are_close(cost1, cost5, 1e-3));
    assert(tests::are_close(cost1, cost6, 1e-3));

#ifdef TWO_GPUS
    double cost7
        = experiment<SparseDataset, O>(data1, obj, num_epochs, tol, std::vector<uint32_t> { 0, 1 }, 32, add_bias);
    double cost8
        = experiment<L2SparseDataset, O>(data2, obj, num_epochs, tol, std::vector<uint32_t> { 0, 1 }, 32, add_bias);
    double cost9
        = experiment<DenseDataset, O>(data3, obj, num_epochs, tol, std::vector<uint32_t> { 0, 1 }, 32, add_bias);
    cout << "cost7 = " << cost7 << endl;
    cout << "cost8 = " << cost8 << endl;
    cout << "cost9 = " << cost9 << endl;
    assert(tests::are_close(cost1, cost7, 1e-3));
    assert(tests::are_close(cost1, cost8, 1e-3));
    assert(tests::are_close(cost1, cost9, 1e-3));
#endif

#endif
}

int main()
{

    using namespace glm;
    using namespace std;

    double lambda = 1.0;
    double w_pos  = 1.0;
    double w_neg  = 1.0;

    auto obj_d = make_shared<DualLogisticRegression>(lambda, w_pos, w_neg);
    auto obj_p = make_shared<PrimalLogisticRegression>(lambda, w_pos, w_neg);

    data_test<DualLogisticRegression>(obj_d, false);
    data_test<PrimalLogisticRegression>(obj_p, false);
    data_test<DualLogisticRegression>(obj_d, true);
    data_test<PrimalLogisticRegression>(obj_p, true);

    return 0;
}
