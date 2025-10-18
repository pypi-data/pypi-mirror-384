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

#include "UnitTests.hpp"
#include "PrimalLassoRegression.hpp"

int main()
{

    using namespace std;
    using namespace glm;

    double lambda = 0.5;

    // weights do not make sense for regression!
    double w_pos = 1.0;
    double w_neg = 1.0;

    auto obj = make_shared<PrimalLassoRegression>(lambda, w_pos, w_neg);

    // without bias
    tests::primal_unit_test<PrimalLassoRegression>(obj, false);
    // with bias
    tests::primal_unit_test<PrimalLassoRegression>(obj, true);

    return 0;
}
