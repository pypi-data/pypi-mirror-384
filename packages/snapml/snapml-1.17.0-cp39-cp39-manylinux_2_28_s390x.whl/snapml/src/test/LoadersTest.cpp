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
#include "UnitTests.hpp"
#include "DualRidgeRegression.hpp"
#include "PrimalRidgeRegression.hpp"

void loaders_test(bool add_bias, bool class_weights, int p, int c)
{

    using namespace glm;
    using namespace std;

    uint32_t num_epochs = 1000;
    double   tol        = 1e-3;

    double cost1 = tests::cocoa_sim<SvmLightLoader, SparseDataset, DualRidgeRegression>(
        "../test/data/small.libsvm", p, c, num_epochs, false, add_bias, class_weights);
    double cost2 = tests::cocoa_sim<DenseSnapLoader, DenseDataset, DualRidgeRegression>(
        "../test/data/small_dense.snap", p, c, num_epochs, false, add_bias, class_weights);
    double cost3 = tests::cocoa_sim<SparseSnapLoader, SparseDataset, DualRidgeRegression>(
        "../test/data/small_sparse.snap", p, c, num_epochs, false, add_bias, class_weights);
    double cost4 = tests::cocoa_sim<L2SparseSnapLoader, L2SparseDataset, DualRidgeRegression>(
        "../test/data/small_l2sparse.snap", p, c, num_epochs, false, add_bias, class_weights);
    double cost5 = tests::cocoa_sim<CsvLoader, DenseDataset, DualRidgeRegression>(
        "../test/data/small.csv", p, c, num_epochs, false, add_bias, class_weights);
    double cost6 = tests::cocoa_sim<DenseSnapLoader, DenseDataset, PrimalRidgeRegression>(
        "../test/data/small_dense.snap.t", p, c, num_epochs, false, add_bias, class_weights);
    double cost7 = tests::cocoa_sim<SparseSnapLoader, SparseDataset, PrimalRidgeRegression>(
        "../test/data/small_sparse.snap.t", p, c, num_epochs, false, add_bias, class_weights);

    cout << add_bias << " " << class_weights << " " << p << " " << c << " " << cost1 << " " << cost2 << " " << cost3
         << " " << cost4 << " " << cost5 << " " << cost6 << " " << cost7 << std::endl;
    assert(tests::are_close(cost1, cost2, tol));
    assert(tests::are_close(cost1, cost3, tol));
    assert(tests::are_close(cost1, cost4, tol));
    assert(tests::are_close(cost1, cost5, tol));
    assert(tests::are_close(cost1, -cost6, tol));
    assert(tests::are_close(cost1, -cost7, tol));
}

int main()
{
    for (int p = 1; p <= 8; p *= 2) {
        for (int c = p; c <= p * 8; c *= 2) {
            loaders_test(false, false, p, c);
            loaders_test(true, false, p, c);
            loaders_test(false, true, p, c);
            loaders_test(true, true, p, c);
        }
    }

    return 0;
}
