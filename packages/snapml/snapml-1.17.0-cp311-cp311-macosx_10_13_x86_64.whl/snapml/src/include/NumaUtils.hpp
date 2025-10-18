/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2018, 2020
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Nikolas Ioannou
 *
 * End Copyright
 ********************************************************************/

#ifndef GLM_NUMA_UTILS
#define GLM_NUMA_UTILS

#include <numa.h>
#include <numaif.h>
#include <iostream>
#include <cstdio>
#include <cstring>
#include <unistd.h>
#include <mutex>
#include <tuple>
#include <vector>

#define NUMA_AFFINITY_DEBUG_ 0
#if NUMA_AFFINITY_DEBUG_ > 0
#include <pthread.h>
#endif

namespace glm {

const char numa_err_msg[] = "Failed to perform numa affinity optimization. You might get inconsistent performance.";

static int mem_to_numa_node(void* in)
{
    if (nullptr == in)
        return -1;
    const uint64_t page_size = sysconf(_SC_PAGESIZE);
    void*          pages[1]  = { (void*)((uintptr_t)in / page_size * page_size) };
    int            status    = 0;
    long           rc        = move_pages(0 /*pid, 0 for caller*/, 1 /* # pages, just one */, pages,
                         nullptr /*null nodes to retrieve location of pages*/, &status, MPOL_MF_MOVE);
    if (0 != rc) {
#if NUMA_AFFINITY_DEBUG_ > 0
        std::cout << "failed to get numa node of page0x" << pages[0] << " err=" << strerror(errno) << std::endl;
#endif
        return -1;
    }
    return status;
}

static UNUSED void numa_util_free(void* ptr, const size_t size_in)
{
    const uint64_t page_size = sysconf(_SC_PAGESIZE);
    const size_t   size      = (size_in + page_size - 1) / page_size * page_size;
#if NUMA_AFFINITY_DEBUG_ > 0
    std::cout << "calling numa alloc with psize=" << page_size << " size=" << size << std::endl;
#endif
    numa_free(ptr, size);
}

static UNUSED void* numa_util_alloc(const size_t size_in, const int numa_node)
{
    const uint64_t page_size = sysconf(_SC_PAGESIZE);
    const size_t   size      = (size_in + page_size - 1) / page_size * page_size;
#if NUMA_AFFINITY_DEBUG_ > 0
    std::cout << "calling numa alloc with psize=" << page_size << " size=" << size << " node=" << numa_node
              << std::endl;
#endif
    return numa_alloc_onnode(size, numa_node);
}

static UNUSED void* numa_alloc_cpy(void* in, size_t size_in, const int numa_node)
{
    const int mem_numa_node = mem_to_numa_node(in);
#if NUMA_AFFINITY_DEBUG_ > 0
    static std::mutex mtx;
    mtx.lock();
    std::cout << "0x%" << in << " on node=" << mem_numa_node << " desired node=" << numa_node << std::endl;
    mtx.unlock();
#endif
    if (-1 == mem_numa_node) {
        return in;
    } else {
        if (numa_node == mem_numa_node) {
#if NUMA_AFFINITY_DEBUG_ > 0
            std::cout << "0x%" << in << " already on desired numa node" << mem_numa_node << std::endl;
#endif
            return in;
        }
    }
    const uint64_t page_size = sysconf(_SC_PAGESIZE);
    const size_t   size      = (size_in + page_size - 1) / page_size * page_size;
#if NUMA_AFFINITY_DEBUG_ > 0
    std::cout << "calling numa alloc with psize=" << page_size << " size=" << size << " node=" << numa_node
              << std::endl;
#endif
    void* const ptr = numa_alloc_onnode(size, numa_node);
    if (nullptr != ptr) {
        memcpy(ptr, in, size_in);
        return ptr;
    }
    std::cout << numa_err_msg << std::endl;
#if NUMA_AFFINITY_DEBUG_ > 0
    std::cout << "failed to allocate on desired numa node. using original location." << std::endl;
#endif
    return in;
}

#ifdef WITH_CUDA
static UNUSED int cudadevprop_to_numanode(const cudaDeviceProp& prop)
{
    if (numa_available() < 0 || 1 == numa_num_configured_nodes()) {
        // not a numa machine
#if NUMA_AFFINITY_DEBUG_ > 0
        std::cout << "numa not available" << std::endl;
#endif
        return -1;
    }
    char    pcibusid[128] = { 0 };
    char    fname[256]    = { 0 };
    ssize_t n
        = snprintf(pcibusid, sizeof(pcibusid), "%04x:%02x:%02x.0", prop.pciDomainID, prop.pciBusID, prop.pciDeviceID);
    if (12 != n) {
        std::cout << numa_err_msg << std::endl;
        return -1;
    }
    n = snprintf(fname, sizeof(fname), "/sys/bus/pci/devices/%s/numa_node", pcibusid);
    if (43 != n) {
        std::cout << numa_err_msg << std::endl;
        return -1;
    }
    FILE* const f = fopen(fname, "r");
    if (nullptr == f) {
        std::cout << numa_err_msg << std::endl;
        return -1;
    }
    int numa_node = -1;
    n             = fscanf(f, "%d", &numa_node);
    if (numa_node < 0) {
        std::cout << numa_err_msg << std::endl;
        fclose(f);
        return -1;
    }
    fclose(f);
    return numa_node;
}
#endif

static thread_local UNUSED struct bitmask* bm;

static UNUSED void numa_release_binding(void)
{

    if (numa_num_configured_nodes() == 0)
        return;

    const int rc = numa_run_on_node(-1);
    if (0 != rc)
        std::cout << numa_err_msg << std::endl;
}

static UNUSED void numa_bind_caller_to_node(const int numa_node)
{

    if (numa_num_configured_nodes() == 0)
        return;

    const int rc = numa_run_on_node(numa_node);
    if (0 != rc)
        std::cout << numa_err_msg << std::endl;
        // std::cout<<"failed to bind thr to numa node err="<<strerror(errno)<<std::endl;
        // if (nullptr == bm)
        //         bm = numa_allocate_nodemask();
        // numa_bitmask_clearall(bm);
        // numa_bitmask_setbit(bm, (uint32_t) numa_node);
#if NUMA_AFFINITY_DEBUG_ > 0
    static int epoch_nr;
    if (epoch_nr < 4) {
        static std::mutex mtx;
        cpu_set_t         cpuset;
        CPU_ZERO(&cpuset);
        if (0 == sched_getaffinity(0, sizeof(cpu_set_t), &cpuset)) {
            mtx.lock();
            std::cout << "thr " << pthread_self() << " numa_node=" << numa_node << std::endl;
            const long nCores = sysconf(_SC_NPROCESSORS_ONLN);
            for (long cpu = 0; cpu < nCores; cpu++)
                if (CPU_ISSET(cpu, &cpuset))
                    std::cout << cpu << ", ";
            std::cout << std::endl;
            epoch_nr++;
            mtx.unlock();
        } else {
            std::cout << "failed to get affinity" << std::endl;
        }
    }
#endif
}

static void numa_free_allocated_mem(std::vector<std::tuple<void*, size_t>>& ptrs)
{
    for (auto ptr : ptrs) {
        void*  p;
        size_t size;
        std::tie(p, size) = ptr;
#if NUMA_AFFINITY_DEBUG_ > 0
        std::cout << "calling free with ptr=" << p << " psize=" << size << std::endl;
#endif
        numa_free(p, size);
    }
}

static uint32_t logical_cores_per_physical()
{
    uint32_t    input1 = (uint32_t)(-1), input2 = (uint32_t)(-1);
    FILE* const f = fopen("/sys/devices/system/cpu/cpu0/topology/thread_siblings_list", "r");
    if (nullptr == f)
        return 1;
    // either "0" (1), "0,32"(2) or "0-3" (4)
    int n = fscanf(f, "%u-%u", &input1, &input2);
#if NUMA_AFFINITY_DEBUG_ > 0
    fprintf(stdout, "n=%d in1=%u in2=%u where=%ld\n", n, input1, input2, ftell(f));
#endif
    if (2 == n && input1 < input2) {
        fclose(f);
        return input2 - input1 + 1;
    }
    rewind(f);
    n = fscanf(f, "%u,%u", &input1, &input2);
#if NUMA_AFFINITY_DEBUG_ > 0
    fprintf(stdout, "n=%d in1=%u in2=%u where=%ld\n", n, input1, input2, ftell(f));
#endif
    fclose(f);
    if (2 == n && input1 != input2) {
        return 2;
    }
    return 1;
}

// returns numa_cpu_nodes, num_cpus
static UNUSED std::vector<std::tuple<int, int>> numa_get_num_cpu_nodes(void)
{
    std::vector<std::tuple<int, int>> result(0);
    int                               numa_mem_nodes = numa_num_configured_nodes();
    if (numa_available() < 0 || numa_mem_nodes <= 1) {
        // not a numa machine
#if NUMA_AFFINITY_DEBUG_ > 0
        std::cout << "numa not available" << std::endl;
#endif
        return result;
    }
    struct bitmask* const cpubm = numa_allocate_cpumask();
    if (nullptr == cpubm) {
#if NUMA_AFFINITY_DEBUG_ > 0
        std::cout << "failed to allocate cpu bitmask!" << std::endl;
#endif
        return result;
    }
    uint32_t       numa_cpu_nodes = 0, num_cpus = 0;
    const uint32_t max_node      = (uint32_t)numa_max_node();
    const uint32_t logical_cores = logical_cores_per_physical();
#if NUMA_AFFINITY_DEBUG_ > 0
    std::cout << "Each core has " << logical_cores << " logical cpus." << std::endl;
#endif
    for (uint32_t i = 0; i <= max_node; ++i) {
        if (numa_bitmask_isbitset(numa_all_nodes_ptr, i)) {
            const int      rc     = numa_node_to_cpus(i, cpubm);
            const uint32_t weight = numa_bitmask_weight(cpubm);
            if (0 != rc || 0 == weight)
                continue;
#if NUMA_AFFINITY_DEBUG_ > 0
            std::cout << "numa node " << i << " has " << weight << " cpus." << std::endl;
#endif
            numa_cpu_nodes++;
            num_cpus += weight / logical_cores;
            result.push_back(std::make_tuple(i, weight / logical_cores));
            numa_bitmask_clearall(cpubm);
        }
    }
    numa_free_cpumask(cpubm);
    if (0 == numa_cpu_nodes) {
#if NUMA_AFFINITY_DEBUG_ > 0
        std::cout << "no numa node with cpus found!" << std::endl;
#endif
        return result;
    }
#if NUMA_AFFINITY_DEBUG_ > 0
    std::cout << numa_cpu_nodes << " numa nodes with " << num_cpus << " cpus" << std::endl;
#endif
    return result;
}

}; // namespace glm

#endif // GLM_NUMA_UTILS
