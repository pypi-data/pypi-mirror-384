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
#include "DualLogisticRegression.hpp"
#include "PrimalLogisticRegression.hpp"

int main()
{

    using namespace std;
    using namespace glm;

    double lambda = 1.0;
    double w_pos  = 2.0;
    double w_neg  = 1.0;

    auto obj_p = std::make_shared<PrimalLogisticRegression>(lambda, w_pos, w_neg);
    auto obj_d = std::make_shared<DualLogisticRegression>(lambda, w_pos, w_neg);

    // without bias
    glm::tests::duality_unit_test<PrimalLogisticRegression, DualLogisticRegression>(obj_p, obj_d, false);
    // with bias
    glm::tests::duality_unit_test<PrimalLogisticRegression, DualLogisticRegression>(obj_p, obj_d, true);

    return 0;
}
