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
 *                Milos Stanisavljevic
 *
 * End Copyright
 ********************************************************************/

#ifndef GLM_UNIT_TESTS
#define GLM_UNIT_TESTS

#include "DenseDatasetInt.hpp"
#include "L2SparseDataset.hpp"
#include "SparseDataset.hpp"
#include "GLMUtils.hpp"
#include "DatasetGenerators.hpp"
#include "TestUtils.hpp"

#include <cmath>
#include <vector>
#include <cstdlib>
#include <iostream>
#include <cassert>
#include <stdexcept>
#include <random>

namespace glm {
namespace tests {

    template <class L>
    std::vector<std::shared_ptr<L>> load_partitions(std::string filename, uint32_t num_partitions, uint32_t num_chunks)
    {

        std::vector<std::shared_ptr<L>> loaders;
        for (uint32_t p = 0; p < num_partitions; p++) {
            loaders.push_back(std::make_shared<L>(filename, p, num_partitions, num_chunks));
        }

        std::vector<uint32_t>              max_ind(num_partitions);
        std::vector<uint32_t>              this_num_pt(num_partitions);
        std::vector<uint32_t>              num_pos(num_partitions);
        std::vector<uint32_t>              num_neg(num_partitions);
        std::vector<std::vector<uint32_t>> offsets(num_partitions, std::vector<uint32_t>(num_partitions));

        for (uint32_t p = 0; p < num_partitions; p++) {
            loaders[p]->get_consistency(max_ind[p], this_num_pt[p], num_pos[p], num_neg[p], offsets[p].data());
        }

        for (uint32_t p = 1; p < num_partitions; p++) {
            max_ind[0] = std::max(max_ind[0], max_ind[p]);
            this_num_pt[0] += this_num_pt[p];
            num_pos[0] += num_pos[p];
            num_neg[0] += num_neg[p];
            for (uint32_t pp = 0; pp < num_partitions; pp++) {
                offsets[0][pp] += offsets[p][pp];
            }
        }

        for (uint32_t p = 0; p < num_partitions; p++) {
            loaders[p]->set_consistency(max_ind[0], this_num_pt[0], num_pos[0], num_neg[0], offsets[0].data());
        }

        return loaders;
    }

    template <class O_p, class O_d>
    int duality_unit_test(std::shared_ptr<O_p> obj_p, std::shared_ptr<O_d> obj_d, bool add_bias)
    {

        using namespace std;

        uint32_t num_ex   = 10;
        uint32_t num_ft   = 20;
        double   sparsity = 0.1;

        uint32_t seed = 12312321;

        std::shared_ptr<SparseDataset> data_d = generate_small_random_dataset(seed, false, num_ex, num_ft, sparsity);
        std::shared_ptr<SparseDataset> data_p = generate_small_random_dataset(seed, true, num_ex, num_ft, sparsity);

        using namespace glm;

        uint32_t num_epochs = 100;
        double   tol        = 0.00001;

        try {
            std::vector<uint32_t> device_ids;
            double                cost1
                = experiment<SparseDataset, O_p>(data_p, obj_p, num_epochs, tol, std::vector<uint32_t> {}, 1, add_bias);
            double cost2
                = experiment<SparseDataset, O_d>(data_d, obj_d, num_epochs, tol, std::vector<uint32_t> {}, 1, add_bias);
            cout << cost1 << endl;
            cout << cost2 << endl;

#ifdef WITH_CUDA
            double cost3 = experiment<SparseDataset, O_p>(data_p, obj_p, num_epochs, tol, std::vector<uint32_t> { 0 },
                                                          32, add_bias);
            double cost4 = experiment<SparseDataset, O_d>(data_d, obj_d, num_epochs, tol, std::vector<uint32_t> { 0 },
                                                          32, add_bias);
            cout << cost3 << endl;
            cout << cost4 << endl;
            double ttol = 1e-6;
            assert(are_close(cost1, cost3, ttol));
            assert(are_close(cost2, cost4, ttol));
            assert(are_close(cost1, -cost2, ttol));
            assert(are_close(cost3, -cost4, ttol));

#ifdef TWO_GPUS
            double cost5 = experiment<SparseDataset, O_p>(data_p, obj_p, num_epochs, tol,
                                                          std::vector<uint32_t> { 0, 1 }, 32, add_bias);
            double cost6 = experiment<SparseDataset, O_d>(data_d, obj_d, num_epochs, tol,
                                                          std::vector<uint32_t> { 0, 1 }, 32, add_bias);
            cout << cost5 << endl;
            cout << cost6 << endl;
            assert(are_close(cost1, cost5, ttol));
            assert(are_close(cost2, cost6, ttol));
            assert(are_close(cost5, -cost6, ttol));
#endif

#endif

        } catch (exception& e) {
            cout << e.what() << endl;
        }

        return 0;
    }

    template <class O> int dual_unit_test(std::shared_ptr<O> obj, bool add_bias)
    {

        using namespace std;

        uint32_t num_ex   = 10;
        uint32_t num_ft   = 20;
        double   sparsity = 0.1;

        uint32_t seed = 12312321;

        std::shared_ptr<SparseDataset> data = generate_small_random_dataset(seed, false, num_ex, num_ft, sparsity);

        using namespace glm;

        uint32_t num_epochs = 1000;
        double   tol        = 0.00001;

        double cost1 = experiment<SparseDataset, O>(data, obj, num_epochs, tol, std::vector<uint32_t> {}, 1, add_bias);
        cout << cost1 << endl;

#ifdef WITH_CUDA
        double cost2
            = experiment<SparseDataset, O>(data, obj, num_epochs, tol, std::vector<uint32_t> { 0 }, 32, add_bias);
        cout << cost2 << endl;
        assert(are_close(cost1, cost2, 1e-6));

#ifdef TWO_GPUS
        double cost3
            = experiment<SparseDataset, O>(data, obj, num_epochs, tol, std::vector<uint32_t> { 0, 1 }, 32, add_bias);
        cout << cost3 << endl;
        assert(are_close(cost1, cost3, 1e-6));
#endif

#endif

        return 0;
    }

    template <class O> int primal_unit_test(std::shared_ptr<O> obj, bool add_bias)
    {

        using namespace std;

        uint32_t num_ex   = 10;
        uint32_t num_ft   = 20;
        double   sparsity = 0.1;

        uint32_t seed = 12312321;

        std::shared_ptr<SparseDataset> data = generate_small_random_dataset(seed, true, num_ex, num_ft, sparsity);

        using namespace glm;

        uint32_t num_epochs = 1000;
        double   tol        = 0.00001;

        double cost1 = experiment<SparseDataset, O>(data, obj, num_epochs, tol, std::vector<uint32_t> {}, 1, add_bias);
        cout << cost1 << endl;

#ifdef WITH_CUDA
        double cost2
            = experiment<SparseDataset, O>(data, obj, num_epochs, tol, std::vector<uint32_t> { 0 }, 32, add_bias);
        cout << cost2 << endl;
        assert(are_close(cost1, cost2, 1e-6));

#ifdef TWO_GPUS
        double cost3
            = experiment<SparseDataset, O>(data, obj, num_epochs, tol, std::vector<uint32_t> { 0, 1 }, 32, add_bias);
        cout << cost3 << endl;
        assert(are_close(cost1, cost3, 1e-6));
#endif

#endif

        return 0;
    }

    template <class O> int chunking_test(std::shared_ptr<O> obj, bool add_bias)
    {

        using namespace std;
        using namespace glm;

        uint32_t num_ex   = 10000;
        uint32_t num_ft   = 100;
        double   sparsity = 0.01;

        uint32_t seed = 12312321;

        shared_ptr<SparseDataset> data = generate_small_random_dataset(seed, false, num_ex, num_ft, sparsity);

        double tol = 1e-8;

        double cost_host = experiment<SparseDataset, O>(data, obj, 1000, tol, std::vector<uint32_t> {}, 1, add_bias);
        cout << cost_host << endl;

#ifdef WITH_CUDA
        for (uint32_t i = 1; i <= 4; i++) {

            cout << "Starting test " << i << endl;
            size_t gpu_mem_lim_B   = 1024 * 256 * i;
            size_t chunking_step_B = 1024;

            try {
                double cost_dev = experiment<SparseDataset, O>(data, obj, 1000, tol, std::vector<uint32_t> { 0 }, 1024,
                                                               add_bias, gpu_mem_lim_B, chunking_step_B);
                cout << cost_host << " " << cost_dev << endl;
                assert(are_close(cost_host, cost_dev, 1e-2));
            } catch (exception& e) {
                cout << e.what() << endl;
            }
        }
#endif

        return 0;
    }

    template <class L, class D, class O>
    double cocoa_sim(std::string filename, uint32_t num_partitions, uint32_t num_chunks, uint32_t num_epochs,
                     bool use_gpu, bool add_bias, bool class_weights = false)
    {

        // load the data
        std::vector<std::shared_ptr<L>> loaders = glm::tests::load_partitions<L>(filename, num_partitions, num_chunks);

        std::vector<std::shared_ptr<D>> data;
        for (uint32_t p = 0; p < num_partitions; p++) {
            data.push_back(loaders[p]->get_data());
        }

        double lambda = 1.0;
        double sigma  = num_partitions;
        double w_pos  = class_weights ? data[0]->get_num_ex() / (2.0 * data[0]->get_num_pos()) : 1.0;
        double w_neg  = class_weights ? data[0]->get_num_ex() / (2.0 * data[0]->get_num_neg()) : 1.0;
        double tol    = 0.001;

        std::shared_ptr<O> obj = std::make_shared<O>(lambda, w_pos, w_neg);

        std::vector<std::shared_ptr<glm::Solver>> solvers;
        for (uint32_t p = 0; p < num_partitions; p++) {
#ifdef WITH_CUDA
            size_t   gpu_mem     = 0;
            uint32_t num_threads = 1024;
            if (use_gpu) {
                solvers.push_back(std::make_shared<glm::DeviceSolver<D, O>>(data[p].get(), obj.get(), sigma, tol, 0,
                                                                            gpu_mem, num_threads, add_bias));
            } else
#endif
            {
                solvers.push_back(
                    std::make_shared<glm::HostSolver<D, O>>(data[p].get(), obj.get(), sigma, tol, 1, add_bias));
            }
        }

        uint32_t dim = solvers[0]->dim();

        std::vector<std::vector<double>> shared(num_partitions, std::vector<double>(dim));

        for (uint32_t p = 0; p < num_partitions; p++) {
            solvers[p]->init(shared[p].data());
        }

        for (uint32_t p = 1; p < num_partitions; p++) {
            for (uint32_t i = 0; i < dim; i++) {
                shared[0][i] += shared[p][i];
            }
        }
        for (uint32_t p = 0; p < num_partitions; p++) {
            solvers[p]->set_shared(shared[0].data());
        }

        for (uint32_t i = 0; i < num_epochs; i++) {
            for (uint32_t p = 0; p < num_partitions; p++) {
                solvers[p]->get_update(shared[p].data());
            }
            for (uint32_t p = 1; p < num_partitions; p++) {
                for (uint32_t i = 0; i < dim; i++) {
                    shared[0][i] += shared[p][i];
                }
            }
            for (uint32_t p = 0; p < num_partitions; p++) {
                solvers[p]->set_shared(shared[0].data());
            }
        }

        double cost = 0.0;
        for (uint32_t p = 0; p < num_partitions; p++) {
            cost += solvers[p]->partial_cost();
        }

        return cost;
    }

}
}

#endif
