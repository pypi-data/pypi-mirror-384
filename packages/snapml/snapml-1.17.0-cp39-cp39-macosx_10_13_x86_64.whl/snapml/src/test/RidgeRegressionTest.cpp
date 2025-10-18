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
#include "DualRidgeRegression.hpp"
#include "PrimalRidgeRegression.hpp"

int main()
{

    using namespace std;
    using namespace glm;

    double lambda = 1.0;
    double w_pos  = 1.0;
    double w_neg  = 1.0;

    auto obj_p = make_shared<PrimalRidgeRegression>(lambda, w_pos, w_neg);
    auto obj_d = make_shared<DualRidgeRegression>(lambda, w_pos, w_neg);

    // without bias
    glm::tests::duality_unit_test<PrimalRidgeRegression, DualRidgeRegression>(obj_p, obj_d, false);

    // with bias
    glm::tests::duality_unit_test<PrimalRidgeRegression, DualRidgeRegression>(obj_p, obj_d, true);

    return 0;
}
