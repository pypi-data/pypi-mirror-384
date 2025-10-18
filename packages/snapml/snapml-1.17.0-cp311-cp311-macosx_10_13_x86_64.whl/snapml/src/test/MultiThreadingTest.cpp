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
#include "DualL1SupportVectorMachine.hpp"
#include <chrono>

int main()
{

    typedef std::chrono::high_resolution_clock Clock;

    using namespace std;
    using namespace glm;

    double lambda = 1.0;
    double w_pos  = 1.0;
    double w_neg  = 1.0;

    auto obj = make_shared<DualL1SupportVectorMachine>(lambda, w_pos, w_neg);

    uint32_t num_ex = 100000;
    uint32_t num_ft = 1000;

    auto     data       = tests::generate_small_random_dataset(12312312, false, num_ex, num_ft, 0.001);
    uint32_t num_epochs = 1000;
    double   tol        = 0.0001;

    for (uint32_t num_threads = 1; num_threads <= 16; num_threads *= 2) {
        auto   t1   = Clock::now();
        double cost = experiment<SparseDataset, DualL1SupportVectorMachine>(
            data, obj, num_epochs, tol, std::vector<uint32_t> {}, num_threads, false);
        auto   t2     = Clock::now();
        auto   dur    = t2 - t1;
        double t_elap = (double)dur.count() / 1.0e9;
        std::cout << num_threads << " " << t_elap << " " << cost << std::endl;
    }

    for (uint32_t num_threads = 1; num_threads <= 40; num_threads *= 2) {
        auto   t1   = Clock::now();
        double cost = experiment<SparseDataset, DualL1SupportVectorMachine>(
            data, obj, num_epochs, tol, std::vector<uint32_t> {}, num_threads, true);
        auto   t2     = Clock::now();
        auto   dur    = t2 - t1;
        double t_elap = (double)dur.count() / 1.0e9;
        std::cout << num_threads << " " << t_elap << " " << cost << std::endl;
    }
}
