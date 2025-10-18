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
 *                Andreea Anghel
 *                Milos Stanisavljevic
 *
 * End Copyright
 ********************************************************************/

#ifndef GLM_UTILS
#define GLM_UTILS

#include "Solver.hpp"

#ifdef WITH_NUMA
#include "MultiHostSolver.hpp"
#else
#include "HostSolver.hpp"
#endif

#include "SGDSolver.hpp"
#include <memory>

#ifdef WITH_CUDA
#include "DeviceSolver.hpp"
#include "MultiDeviceSolver.hpp"
#include <cuda_runtime_api.h>

namespace gpu {

int get_gpu_count()
{
    int         nDevices;
    cudaError_t err = cudaGetDeviceCount(&nDevices);
    if (err == cudaSuccess && nDevices > 0) {
        return nDevices;
    }
    return 0;
}

}
#endif

namespace glm {

template <class D, class O>
double experiment(std::shared_ptr<D> data, std::shared_ptr<O> obj, uint32_t num_epochs, double tol,
                  std::vector<uint32_t> device_ids, uint32_t num_threads = 32, bool add_bias = false,
                  size_t gpu_mem_lim_B = 0, size_t chunking_step_B = 512 * 1024 * 1024)
{

    double                  sigma = 1.0;
    std::shared_ptr<Solver> solver;
#ifdef WITH_NUMA
    if (device_ids.size() == 0) {
        solver = std::make_shared<MultiNumaSolver<D, O>>(data.get(), obj.get(), sigma, tol, num_threads, add_bias, 1.0);
    }
#else
    if (device_ids.size() == 0) {
        solver = std::make_shared<HostSolver<D, O>>(data.get(), obj.get(), sigma, tol, num_threads, add_bias, 1.0, 0);
    }
#endif
#ifdef WITH_CUDA
    else if (device_ids.size() == 1) {
        solver = std::make_shared<DeviceSolver<D, O>>(data.get(), obj.get(), sigma, tol, device_ids[0], gpu_mem_lim_B,
                                                      num_threads, add_bias, true, chunking_step_B);
    }
#ifdef TWO_GPUS
    else {
        solver = std::make_shared<MultiDeviceSolver<D, O>>(data.get(), obj.get(), sigma, tol, device_ids, num_threads,
                                                           add_bias, 1.0);
    }
#endif
#endif

    solver->init(nullptr);

    bool     stop = false;
    uint32_t i    = 0;
    while (!stop && i < num_epochs) {
        stop = solver->get_update(nullptr);
        i++;
    }
    std::cout << "num_epochs = " << i << std::endl;
    double cost = solver->partial_cost();

    return cost;
}

#ifdef _DEBUG
#ifdef WITH_CUDA

int is_gpu_adress(const void* addr)
{

    cudaPointerAttributes attr;
    cudaError_t           rc;

    int is_gpu = false;
    rc         = cudaPointerGetAttributes(&attr, addr);
    if (rc == cudaSuccess) {
        if (attr.type == cudaMemoryTypeDevice) {
            is_gpu = true;
        }
    } else {
        // clear error state
        cudaError_t err = cudaGetLastError();
        // normal error if you pass a host ptr above
        assert(err == cudaErrorInvalidValue);
    }

    return is_gpu;
}

void dump_data(void* data_ptr, int len)
{
    float* hostVal;
    bool   gpu_addr = false;

    if (is_gpu_adress(data_ptr) == true) {
        hostVal = (float*)malloc(len * sizeof(float));
        assert(hostVal != NULL);
        gpu_addr = true;
        cuda_safe(cudaMemcpy(hostVal, data_ptr, len * sizeof(float), cudaMemcpyDeviceToHost),
                  "[Debug::dump_data],Could not copy onto device");
    } else {
        hostVal = (float*)data_ptr;
    }
    // Print the data till expected length
    printf(" ====== Start Dump Data ======== \n");
    for (int i = 0; i < len; i++) {
        printf("dump_data[%d] ::  %f \n", i, hostVal[i]);
    }
    printf(" ====== End Dump Data  ======== \n");

    if (gpu_addr)
        free(hostVal);

    return;
}

#endif
#endif
}

#endif
