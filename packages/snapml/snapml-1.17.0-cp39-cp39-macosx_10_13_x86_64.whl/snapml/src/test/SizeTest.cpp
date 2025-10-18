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
#include "Loaders.hpp"
#include "DualLogisticRegression.hpp"
#include "PrimalLogisticRegression.hpp"
#include "DualSupportVectorMachine.hpp"

int main()
{

    using namespace std;
    using namespace glm;

    auto loader = tests::load_partitions<CsvLoader>("../test/data/test.csv", 1);
}
