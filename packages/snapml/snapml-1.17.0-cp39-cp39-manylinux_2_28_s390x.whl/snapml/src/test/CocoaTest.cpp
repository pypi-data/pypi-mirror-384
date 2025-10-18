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

void cocoa_test(bool add_bias)
{

    using namespace glm;
    using namespace std;

    uint32_t num_epochs = 1000;

    double cost1 = tests::cocoa_sim<SvmLightLoader, SparseDataset, DualRidgeRegression>("../test/data/small.libsvm", 1,
                                                                                        1, num_epochs, false, add_bias);
    double cost2 = tests::cocoa_sim<SvmLightLoader, SparseDataset, DualRidgeRegression>("../test/data/small.libsvm", 2,
                                                                                        2, num_epochs, false, add_bias);
    double cost3 = tests::cocoa_sim<SvmLightLoader, SparseDataset, DualRidgeRegression>("../test/data/small.libsvm", 4,
                                                                                        4, num_epochs, false, add_bias);
    double cost4 = tests::cocoa_sim<SvmLightLoader, SparseDataset, DualRidgeRegression>("../test/data/small.libsvm", 8,
                                                                                        8, num_epochs, false, add_bias);
    double cost5 = tests::cocoa_sim<SvmLightLoader, SparseDataset, DualRidgeRegression>("../test/data/small.libsvm", 1,
                                                                                        1, num_epochs, true, add_bias);
    double cost6 = tests::cocoa_sim<SvmLightLoader, SparseDataset, DualRidgeRegression>("../test/data/small.libsvm", 2,
                                                                                        2, num_epochs, true, add_bias);
    double cost7 = tests::cocoa_sim<SvmLightLoader, SparseDataset, DualRidgeRegression>("../test/data/small.libsvm", 4,
                                                                                        4, num_epochs, true, add_bias);
    double cost8 = tests::cocoa_sim<SvmLightLoader, SparseDataset, DualRidgeRegression>("../test/data/small.libsvm", 8,
                                                                                        8, num_epochs, true, add_bias);

    double tol = 1e-3;

    cout << "cost1 = " << cost1 << endl;
    cout << "cost2 = " << cost2 << endl;
    cout << "cost3 = " << cost3 << endl;
    cout << "cost4 = " << cost4 << endl;
    cout << "cost5 = " << cost5 << endl;
    cout << "cost6 = " << cost6 << endl;
    cout << "cost7 = " << cost7 << endl;
    cout << "cost8 = " << cost8 << endl;

    assert(tests::are_close(cost1, cost2, tol));
    assert(tests::are_close(cost1, cost3, tol));
    assert(tests::are_close(cost1, cost4, tol));
    assert(tests::are_close(cost1, cost5, tol));
    assert(tests::are_close(cost1, cost6, tol));
    assert(tests::are_close(cost1, cost7, tol));
    assert(tests::are_close(cost1, cost8, tol));
}

int main()
{

    // without bias
    cocoa_test(false);

    // with bias
    cocoa_test(true);

    return 0;
}
