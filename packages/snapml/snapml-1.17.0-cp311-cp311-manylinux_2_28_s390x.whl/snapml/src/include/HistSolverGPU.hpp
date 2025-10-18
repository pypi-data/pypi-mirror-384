/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2019, 2021
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Nikolas Ioannou
 *                Thomas Parnell
 *
 * End Copyright
 ********************************************************************/

#ifndef _LIBGLM_HIST_SOLVER_GPU_
#define _LIBGLM_HIST_SOLVER_GPU_

#include "HistSolver.hpp"

#include <algorithm>
#include <atomic>
#include <random>
#include <thread>
#include <cub/device/device_radix_sort.cuh>
#include <cub/device/device_partition.cuh>
#include <cuda_profiler_api.h>

#include "Checking.hpp"
#include "Dataset.hpp"

#ifdef WITH_NUMA
#include "NumaUtils.hpp"
#endif

#include "OMP.hpp"

#include "TreeInvariants.hpp"
#include "TreeKernels.hpp"
#include "TreeNode.hpp"
#include "DecisionTreeParams.hpp"
#include "TreeUtils.hpp"

//#define TIME_PROFILE
//#define DEBUG_VERIFY

namespace tree {

template <class D, class N> class HistSolverGPU : public HistSolver<N> {
public:
    typedef typename N::hist_bin_t hist_bin_t;

    HistSolverGPU(const std::shared_ptr<glm::TreeInvariants<D>> tree_invariants, const uint32_t gpu_id)
        : tree_invariants_(tree_invariants)
        , gpu_id_(gpu_id)
        , ex_to_bin_(tree_invariants_->get_ex_to_bin())
        , hist_val_(tree_invariants_->get_hist_val())
        , hist_node_alloc_(0)
    {
    }

    virtual ~HistSolverGPU()
    {
        /* fprintf(stdout, "terminating GPU solver"); */
        // TODO: do not call term if we haven't been initialized
        term();
    }

    void init(glm::Dataset* const data, const snapml::DecisionTreeParams params)
    {
        /* fprintf(stdout, "HistSolverGPU init\n"); */
        num_ex_      = data->get_num_ex();
        num_ft_      = data->get_num_ft();
        tree_params_ = params; //.reset(&params);
        hist_nbins_  = tree_params_.hist_nbins;

        glm::cuda_safe(cudaGetDeviceProperties(&device_prop_, gpu_id_), "failed to get device properties.");

#ifdef WITH_NUMA
        const int numa_node_ = glm::cudadevprop_to_numanode(device_prop_);
        if (0 <= numa_node_) {
            // make sure this thread is running on the correct numa
            // node, this will affect the performance of the cuda host
            // malloc'ed memory
            glm::numa_bind_caller_to_node(numa_node_);
        }
#endif

        num_sm_ = device_prop_.multiProcessorCount;

        // init GPU
        glm::cuda_safe(cudaSetDevice(gpu_id_), "[HistSolverGPU] could not set device");

        std::thread init_th;
        init_th = std::thread([&]() {
            glm::cuda_safe(cudaSetDevice(gpu_id_), "[HistSolverGPU] could not set device");
            std::vector<uint8_t> host_ex_to_bin(num_ex_ * num_ft_);
#ifdef TIME_PROFILE
            struct timeval t1, t2;
            if (omp_get_thread_num() == 0)
                gettimeofday(&t1, NULL);
#endif
            glm::cuda_safe(cudaMalloc(&dev_ex_to_bin_, num_ex_ * num_ft_ * sizeof(uint8_t)),
                           "[HistSolverGPU] cuda call failed");
            OMP::parallel_for<int32_t>(0, num_ex_, [this, &host_ex_to_bin](const int32_t& i) {
                for (uint32_t j = 0; j < num_ft_; j++) {
                    host_ex_to_bin[i * num_ft_ + j] = ex_to_bin_[j][i];
                }
            });
            glm::cuda_safe(cudaMemcpy(dev_ex_to_bin_, host_ex_to_bin.data(), num_ft_ * num_ex_ * sizeof(uint8_t),
                                      cudaMemcpyHostToDevice),
                           "[HistSolverGPU] cuda call failed");

#ifdef TIME_PROFILE
            if (omp_get_thread_num() == 0)
                gettimeofday(&t2, NULL);
            double t_elap = double(t2.tv_sec - t1.tv_sec) + double(t2.tv_usec - t1.tv_usec) / 1000.0 / 1000.0;
            printf("[HistSolverGPU::init] t_transpose_and_copy_ex2bin = %f\n", t_elap);
#endif
        });

#ifdef TIME_PROFILE
        struct timeval t1, t2;
        if (omp_get_thread_num() == 0)
            gettimeofday(&t1, NULL);
#endif
        // allocate on GPU memory
        glm::cuda_safe(cudaMalloc(&dev_hist_val_, num_ft_ * hist_nbins_ * sizeof(float)),
                       "[HistSolverGPU] cuda call failed");
        glm::cuda_safe(cudaMalloc(&dev_fts_, num_ft_ * sizeof(uint32_t)), "[HistSolverGPU] cuda call failed");
        glm::cuda_safe(cudaMalloc(&dev_nex_, num_ex_ * sizeof(ex_lab_t)), "[HistSolverGPU] cuda call failed");
        glm::cuda_safe(cudaMalloc(&dev_nex_out_, num_ex_ * sizeof(ex_lab_t)), "[HistSolverGPU] cuda call failed");
        glm::cuda_safe(cudaMalloc(&dev_go_left_, num_ex_ * sizeof(uint8_t)), "[HistSolverGPU] cuda call failed");
        glm::cuda_safe(cudaMalloc(&dev_go_left_out_, num_ex_ * sizeof(uint8_t)), "[HistSolverGPU] cuda call failed");

        glm::cuda_safe(cudaMalloc(&dev_preds_, num_ex_ * sizeof(double)), "[HistSolverGPU] cuda call failed");
        glm::cuda_safe(cudaMallocHost(&host_hist_[0], MAX_STREAM_NR * 2UL * num_ft_ * hist_nbins_ * sizeof(hist_bin_t)),
                       "[HistSolverGPU] cuda call failed");
        for (uint64_t i = 1; i < MAX_STREAM_NR; ++i) {
            host_hist_[i] = host_hist_[0] + i * 2UL * num_ft_ * hist_nbins_;
        }
        glm::cuda_safe(cudaMallocHost(&host_preds_, num_ex_ * sizeof(double)), "[HistSolverGPU] cuda call failed");

        glm::cuda_safe(cudaMalloc(&dev_nodes_[0], MAX_STREAM_NR * sizeof(N) + MAX_STREAM_NR * num_ft_ * sizeof(N)),
                       "[HistSolverGPU] cuda call failed");
        for (uint32_t i = 1; i < MAX_STREAM_NR; ++i) {
            dev_nodes_[i] = dev_nodes_[0] + i * num_ft_;
        }
        for (uint32_t i = 0; i < MAX_STREAM_NR; ++i) {
            dev_node_in_[i] = dev_nodes_[0] + MAX_STREAM_NR * num_ft_ + i;
        }
        glm::cuda_safe(cudaMallocHost(&host_nodes_[0], MAX_STREAM_NR * sizeof(N)), "[HistSolverGPU] cuda call failed");
        for (uint32_t i = 1; i < MAX_STREAM_NR; ++i) {
            host_nodes_[i] = host_nodes_[0] + i;
        }

        for (uint32_t i = 0; i < num_ft_; i++)
            glm::cuda_safe(cudaMemcpy(&dev_hist_val_[i * hist_nbins_], hist_val_[i].data(),
                                      hist_val_[i].size() * sizeof(float), cudaMemcpyHostToDevice),
                           "[HistSolverGPU] cuda call failed");

        dev_tmp_storage_[0] = nullptr;
        tmp_storage_bytes_  = 0;
        cub::DevicePartition::Flagged(dev_tmp_storage_[0], tmp_storage_bytes_, dev_nex_, dev_go_left_, dev_nex_out_,
                                      dev_go_left_out_, num_ex_);

        glm::cuda_safe(cudaMalloc(&dev_tmp_storage_[0], MAX_STREAM_NR * tmp_storage_bytes_),
                       "[HistSolverGPU] cuda call failed");
        for (uint32_t i = 1; i < MAX_STREAM_NR; ++i) {
            dev_tmp_storage_[i] = (uint8_t*)dev_tmp_storage_[0] + i * tmp_storage_bytes_;
        }
        // create streams
        for (uint32_t i = 0; i < MAX_STREAM_NR; ++i) {
            glm::cuda_safe(cudaStreamCreate(&streams_[i]), "[HistSolverGPU::init] Could not create stream");
        }

        if (init_th.joinable())
            init_th.join();

        {
            uint32_t     max_gpu_depth = 0 == params.max_depth ? 31U : std::min(31U, params.max_depth);
            size_t       gpu_free_B, gpu_tot_B;
            const size_t min_hist_gpu_mem    = MAX_STREAM_NR * num_ft_ * hist_nbins_ * sizeof(hist_bin_t);
            const size_t single_hist_gpu_mem = num_ft_ * hist_nbins_ * sizeof(hist_bin_t);
            assert(max_gpu_depth <= 31);
            max_nodes_gpu_ = (1UL << max_gpu_depth) - 1 + MAX_STREAM_NR;
            glm::cuda_safe(cudaMemGetInfo(&gpu_free_B, &gpu_tot_B),
                           "[HistSolverGPU::init] Could not get GPU memory info");
            gpu_free_B -= num_ex_ * (sizeof(float) + sizeof(uint32_t)); // init_nex_labs in case of sample_weight etc
            gpu_free_B = gpu_free_B / 1024 / 1024 / 1024 * 1024 * 1024 * 1024;
            if (gpu_free_B < min_hist_gpu_mem + single_hist_gpu_mem)
                throw std::runtime_error("not enough GPU memory.");
            gpu_free_B -= min_hist_gpu_mem;
            max_nodes_gpu_
                = std::min(gpu_free_B / (num_ft_ * hist_nbins_ * sizeof(hist_bin_t)), (size_t)max_nodes_gpu_);
#ifdef DEBUG_VERIFY
            printf("[HistSolverGPU::init] gpu_free_B=%lu gpu_mem_b=%lu\n", gpu_free_B, gpu_tot_B);
#endif
            assert(0 < max_nodes_gpu_);
            glm::cuda_safe(cudaMalloc(&dev_hist_, (uint64_t)max_nodes_gpu_ * num_ft_ * hist_nbins_ * sizeof(hist_bin_t)
                                                      + min_hist_gpu_mem),
                           "[HistSolverGPU::init] failed to allocate histograms");
#ifdef DEBUG_VERIFY
            printf("[HistSolverGPU::init] requested depth=%u max_gpu_depth=%u max_nodes_gpu=%u\n", params.max_depth,
                   max_gpu_depth, max_nodes_gpu_);
#endif
        }
#ifdef TIME_PROFILE
        if (omp_get_thread_num() == 0) {
            gettimeofday(&t2, NULL);
            double t_elap = double(t2.tv_sec - t1.tv_sec) + double(t2.tv_usec - t1.tv_usec) / 1000.0 / 1000.0;
            printf("[HistSolverGPU::init] alloc + copying dev_hist_val = %f\n", t_elap);
        }
#endif

#ifdef WITH_NUMA
        if (0 <= numa_node_) {
            // release numa affinity if it was set
            glm::numa_bind_caller_to_node(-1);
        }
#endif
    }

    int get_current_device()
    {
        int device;
        glm::cuda_safe(cudaGetDevice(&device), "[HistSolverGPU] could not get device");
        return device;
    }

    void set_thread_context() { glm::cuda_safe(cudaSetDevice(gpu_id_), "[HistSolverGPU] could not set device"); }

    void init_nex_labs(const std::vector<uint32_t>& indices, const float* sample_weight, const double* labs)
    {
        // using dev__preds_ for labs
        glm::cuda_safe(cudaMemcpy(dev_preds_, labs, num_ex_ * sizeof(double), cudaMemcpyHostToDevice),
                       "[HistSolverGPU] cuda call failed");
        const uint32_t len               = 0 == indices.size() ? num_ex_ : indices.size();
        float*         dev_sample_weight = nullptr;
        uint32_t*      dev_indices       = nullptr;
        if (nullptr != sample_weight) {
            glm::cuda_safe(cudaMalloc(&dev_sample_weight, num_ex_ * sizeof(float)), "[HistSolverGPU] cuda call failed");
            glm::cuda_safe(
                cudaMemcpy(dev_sample_weight, sample_weight, num_ex_ * sizeof(float), cudaMemcpyHostToDevice),
                "[HistSolverGPU] cuda call failed");
        }
        if (0 == indices.size()) {
            dev_init_nex<<<ceil(double(len) / 32.0), 32, 0>>>(
                len, dev_preds_, dev_sample_weight, tree_params_.task == snapml::task_t::regression, dev_nex_);
        } else {
            glm::cuda_safe(cudaMalloc(&dev_indices, len * sizeof(uint32_t)), "[HistSolverGPU] cuda call failed");
            glm::cuda_safe(cudaMemcpy(dev_indices, indices.data(), len * sizeof(uint32_t), cudaMemcpyHostToDevice),
                           "[HistSolverGPU] cuda call failed");
            dev_init_nex_subsample<<<ceil(double(len) / 32.0), 32, 0>>>(len, dev_indices, dev_preds_, dev_sample_weight,
                                                                        tree_params_.task == snapml::task_t::regression,
                                                                        dev_nex_);
        }
        if (nullptr != dev_sample_weight)
            glm::cuda_safe(cudaFree(dev_sample_weight), "[HistSolverGPU] cuda call failed");
        if (nullptr != dev_indices)
            glm::cuda_safe(cudaFree(dev_indices), "[HistSolverGPU] cuda call failed");
    }

    void init_fts(const std::vector<uint32_t>& fts, const uint32_t num_ft_effective, const uint32_t random_state)
    {
        rng_              = std::mt19937(random_state);
        num_ft_effective_ = num_ft_effective;
        fts_              = fts;
        assert(num_ft_effective_ <= fts_.size() && num_ft_effective <= num_ft_);
        glm::cuda_safe(cudaMemcpy(dev_fts_, fts_.data(), fts_.size() * sizeof(uint32_t), cudaMemcpyHostToDevice),
                       "[HistSolverGPU] cuda call failed");
    }

    double* retrieve_preds()
    {
        glm::cuda_safe(cudaDeviceSynchronize(), "[HistSolverGPU] cuda call failed");
        glm::cuda_safe(cudaMemcpy(host_preds_, dev_preds_, num_ex_ * sizeof(double), cudaMemcpyDeviceToHost),
                       "[HistSolverGPU] cuda call failed");
        return host_preds_;
    }

    void retrieve_nex(const N* const node, const uint32_t node_idx, const uint32_t depth,
                      std::unique_ptr<std::vector<ex_lab_t>>& nex)
    {
        const uint32_t tid = omp_get_thread_num();
        assert(tid < MAX_STREAM_NR);
        assert(node_idx < node_dev_md_.size() && GPU_INVAL_NEX != node_dev_md_[node_idx].nex_idx);
        const uint32_t  len            = node->get_num();
        const uint32_t  dev_ex_idx     = node_dev_md_[node_idx].nex_idx;
        ex_lab_t* const dev_nex_to_use = 0 == depth % 2 ? dev_nex_ : dev_nex_out_;
        glm::cuda_safe(cudaMemcpyAsync(nex.get()->data(), &dev_nex_to_use[dev_ex_idx], len * sizeof(ex_lab_t),
                                       cudaMemcpyDeviceToHost, streams_[tid]),
                       "[HistSolverGPU] cuda call failed");
        glm::cuda_safe(cudaStreamSynchronize(streams_[tid]), "[HistSolverGPU::retrieve_nex] Could not retrieve nex");
    }

    void update_training_preds(const N* const node, const uint32_t node_idx, const uint32_t depth)
    {
        const uint32_t tid = omp_get_thread_num();
        assert(tid < MAX_STREAM_NR && 0 < node->get_num());
        assert(node_idx < node_dev_md_.size() && GPU_INVAL_NEX != node_dev_md_[node_idx].nex_idx);
        const uint32_t        dev_nex_idx    = node_dev_md_[node_idx].nex_idx;
        const ex_lab_t* const dev_nex_to_use = 0 == depth % 2 ? dev_nex_ : dev_nex_out_;
        // glm::cuda_safe(cudaStreamSynchronize(streams_[tid]), "[DeviceSolver::init] Could not synchronize device");
        dev_update_train_preds<<<ceil(double(node->get_num()) / 32.0), 32, 0, streams_[tid]>>>(
            node->get_num(), &dev_nex_to_use[dev_nex_idx],
            node->get_pred_val(tree_params_.lambda, tree_params_.max_delta_step), dev_preds_);
    }

    void update_node_size(const uint32_t new_size, const bool shuffle)
    {
        if (node_dev_md_.size() < new_size) {
            node_dev_md_.resize(new_size);
        }
        if (shuffle) {
            fisher_yates(fts_, rng_);
#ifdef DEBUG_VERIFY
            for (uint32_t i = 0; i < num_ft_effective_; ++i)
                assert(fts_[i] < num_ft_);
#endif
            assert(num_ft_effective_ < fts_.size());
            glm::cuda_safe(cudaMemcpy(dev_fts_, fts_.data(), fts_.size() * sizeof(uint32_t), cudaMemcpyHostToDevice),
                           "[HistSolverGPU] cuda call failed");
#ifdef DEBUG_VERIFY
            {
                std::vector<uint32_t> fts_tmp(num_ft_effective_);
                glm::cuda_safe(
                    cudaMemcpy(fts_tmp.data(), dev_fts_, fts_tmp.size() * sizeof(uint32_t), cudaMemcpyDeviceToHost),
                    "[HistSolverGPU] cuda call failed");
                for (uint32_t i = 0; i < num_ft_effective_; ++i)
                    assert(fts_[i] == fts_tmp[i]);
            }
#endif
        }
    }

    void process_initial_node(const uint32_t len, const uint32_t root_idx, N* const root)
    {
        node_dev_md_.clear();
        node_dev_md_.resize(1024);
        assert(GPU_INVAL_NEX == node_dev_md_[root_idx].nex_idx);
        node_dev_md_[root_idx].nex_idx  = root_idx;
        node_dev_md_[root_idx].hist_idx = root_idx;
        hist_node_alloc_                = root_idx + 1;
        // process single node (root)
        const uint32_t tid          = omp_get_thread_num();
        const uint32_t dev_nex_idx  = node_dev_md_[root_idx].nex_idx;
        const uint32_t dev_hist_idx = node_dev_md_[root_idx].hist_idx;
        assert(tid + 1 < MAX_STREAM_NR && 0 < len && 0 == dev_hist_idx);
        assert(root_idx < node_dev_md_.size() && GPU_INVAL_NEX != node_dev_md_[root_idx].nex_idx);
        hist_bin_t* const dev_hist_to_use = &dev_hist_[dev_hist_idx * hist_nbins_ * num_ft_];
        // reset all arrays and data structures that are going to be used
        glm::cuda_safe(cudaMemsetAsync(dev_hist_to_use, 0, num_ft_ * hist_nbins_ * sizeof(hist_bin_t), streams_[tid]),
                       "[HistSolverGPU] cuda call failed");
        // copy node to gpu
        host_nodes_[tid]->init_node(reinterpret_cast<const N*>(root));
        glm::cuda_safe(
            cudaMemcpyAsync(dev_node_in_[tid], host_nodes_[tid], sizeof(N), cudaMemcpyHostToDevice, streams_[tid]),
            "[HistSolverGPU] cuda call failed");
        glm::cuda_safe(cudaStreamSynchronize(streams_[tid]),
                       "[HistSolverGPU::process_initial_node1] Could not synchronize stream");
        // compute histogram directly -- Note that we use fts_.size() and not
        // num_ft_effective, this is to support the max_features and
        // colsample_bytree in the same implementation
        dev_recompute_hist_bin<N><<<dim3(len, ceil(double(fts_.size()) / 32.0)), 32, 0, streams_[tid]>>>(
            num_ft_, fts_.size(), hist_nbins_, dev_fts_, &dev_nex_[dev_nex_idx], dev_ex_to_bin_, dev_hist_to_use);

        glm::cuda_safe(cudaMemsetAsync(&dev_hist_[1 * hist_nbins_ * num_ft_], 0,
                                       (max_nodes_gpu_ - 1ULL) * num_ft_ * hist_nbins_ * sizeof(hist_bin_t),
                                       streams_[tid + 1]),
                       "[HistSolverGPU] cuda call failed");
        dev_init_preds<<<ceil(double(num_ex_) / 32.0), 32, 0, streams_[tid + 1]>>>(
            num_ex_, std::numeric_limits<double>::max(), dev_preds_);

        glm::cuda_safe(cudaStreamSynchronize(streams_[tid]),
                       "[HistSolverGPU::process_initial_node2] Could not synchronize stream");

        // initialize node based on the histogram
        dev_init_node_with_hist<N><<<dim3(ceil((double)hist_nbins_ / 32.0)), 32, 0, streams_[tid]>>>(
            hist_nbins_, &dev_hist_to_use[fts_[0] * hist_nbins_], dev_node_in_[tid]);

#ifdef DEBUG_VERIFY
        {
            glm::cuda_safe(cudaStreamSynchronize(streams_[tid]),
                           "[HistSolverGPU::process_initial_nodeDBG1] Could not synchronize stream");
            glm::cuda_safe(cudaMemcpyAsync(host_hist_[tid], dev_hist_to_use, num_ft_ * hist_nbins_ * sizeof(hist_bin_t),
                                           cudaMemcpyDeviceToHost, streams_[tid]),
                           "[HistSolverGPU] cuda call failed");
            glm::cuda_safe(
                cudaMemcpyAsync(host_nodes_[tid], dev_node_in_[tid], sizeof(N), cudaMemcpyDeviceToHost, streams_[tid]),
                "[HistSolverGPU] cuda call failed");
            glm::cuda_safe(cudaStreamSynchronize(streams_[tid]),
                           "[HistSolverGPU::process_initial_nodeDBG2] Could not synchronize stream");
            N test;
            N::init_node(&test, reinterpret_cast<const N*>(root));
            std::vector<hist_bin_t> hist_test(hist_nbins_);
            for (uint32_t bidx = 0; bidx < hist_nbins_; ++bidx)
                hist_test[bidx] = host_hist_[tid][fts_[0] * hist_nbins_ + bidx];
            test.init_with_hist(hist_test);
            assert(test.best_feature == host_nodes_[tid]->best_feature
                   && test.best_threshold == host_nodes_[tid]->best_threshold);
            N::init_node(reinterpret_cast<N*>(root), (const N*)host_nodes_[tid]);
        }
#endif
        // dev_node_init<N> <<<dim3(num_ft_effective_), hist_nbins_, 0, streams_[tid] >>> (dev_fts_, dev_node_in_[tid],
        // dev_nodes_[tid]); dev_prep_best_split<N> <<<dim3(num_ft_effective_, hist_nbins_), hist_nbins_, 0,
        // streams_[tid] >>> (dev_fts_, dev_hist_to_use, dev_nodes_[tid]); dev_prep_best_split3<N>
        // <<<dim3(num_ft_effective_, hist_nbins_ - 1), 32, 0, streams_[tid] >>> (hist_nbins_, dev_fts_,
        // dev_hist_to_use, dev_nodes_[tid]); dev_compute_best_split3<N> <<<dim3(num_ft_effective_), hist_nbins_, 0,
        // streams_[tid] >>> (tree_params_.split_criterion, tree_params_.min_samples_leaf, tree_params_.lambda,
        // dev_fts_, dev_hist_val_, dev_hist_to_use, dev_nodes_[tid]);
        dev_compute_best_split2<N><<<ceil((double)num_ft_effective_ / 32), 32, 0, streams_[tid]>>>(
            num_ft_effective_, hist_nbins_, tree_params_.split_criterion, tree_params_.min_samples_leaf,
            tree_params_.lambda, dev_fts_, dev_hist_val_, dev_hist_to_use, dev_node_in_[tid], dev_nodes_[tid]);

        if (num_ft_effective_ <= (uint32_t)device_prop_.maxThreadsPerBlock) {
            dev_reduce_best_split<N>
                <<<1, num_ft_effective_, 0, streams_[tid]>>>(num_ft_effective_, hist_nbins_, dev_fts_, dev_nodes_[tid]);
        } else {
            uint32_t ft_rem = num_ft_effective_;
            while (ft_rem) {
                uint32_t len    = std::min(ft_rem, (uint32_t)device_prop_.maxThreadsPerBlock);
                uint32_t ft_off = ft_rem - len;
                dev_reduce_best_split<N>
                    <<<1, len, 0, streams_[tid]>>>(len, hist_nbins_, &dev_fts_[ft_off], dev_nodes_[tid]);
                if (0 == ft_off)
                    break;
                ft_rem -= len - 1; // +1 for the previous reduced item
            }
        }
#ifdef DEBUG_VERIFY
        {
            std::vector<N> nodes(num_ft_effective_);
            for (uint32_t ft = 0; ft < num_ft_effective_; ++ft) {
                glm::cuda_safe(
                    cudaMemcpy(host_nodes_[tid], &dev_nodes_[tid][fts_[ft]], sizeof(N), cudaMemcpyDeviceToHost),
                    "[HistSolverGPU] cuda call failed");
                N::init_node(&nodes[ft], (const N*)host_nodes_[tid]);
            }
            {
                // verify node best split computation
                N test;
                N::init_node(&test, reinterpret_cast<const N*>(root));
                for (uint32_t ft = 0; ft < num_ft_effective_; ++ft) {
                    test.reset();
                    for (uint32_t bin_idx = 0; bin_idx < hist_nbins_; ++bin_idx) {
                        const auto& bin = host_hist_[tid][fts_[ft] * hist_nbins_ + bin_idx];
                        if (0 == bin.weight)
                            continue;
                        const float val = hist_val_[fts_[ft]][bin_idx]; // bin.val
                        test.update_best_hist(fts_[ft], val, tree_params_.min_samples_leaf,
                                              tree_params_.split_criterion, tree_params_.lambda);
                        test.post_update_best_hist(bin.weight, bin.sample_weight, bin.lab_sum, bin.num_pos);
                    }
                }
                assert(test.get_best_feature() == nodes[0].get_best_feature());
            }
            glm::cuda_safe(cudaStreamSynchronize(streams_[tid]),
                           "[HistSolverGPU::process_initial_nodeDBG3] Could not synchronize stream");
        }
        {
            std::vector<uint32_t> fts_tmp(num_ft_effective_);
            glm::cuda_safe(
                cudaMemcpy(fts_tmp.data(), dev_fts_, fts_tmp.size() * sizeof(uint32_t), cudaMemcpyDeviceToHost),
                "[HistSolverGPU] cuda call failed");
            for (uint32_t i = 0; i < num_ft_effective_; ++i)
                assert(fts_[i] == fts_tmp[i]);
        }
#endif
        // copy node out
        glm::cuda_safe(cudaMemcpyAsync(host_nodes_[tid], &dev_nodes_[tid][fts_[0]], sizeof(N), cudaMemcpyDeviceToHost,
                                       streams_[tid]),
                       "[HistSolverGPU] cuda call failed");
        glm::cuda_safe(cudaStreamSynchronize(streams_[tid]),
                       "[HistSolverGPU::process_initial_node3] Could not synchronize stream");
        glm::cuda_safe(cudaStreamSynchronize(streams_[tid + 1]),
                       "[HistSolverGPU::process_initial_node4] Could not synchronize stream");
        reinterpret_cast<N*>(root)->init_node((const N*)host_nodes_[tid]);
    }

    int process_node_pair(const uint32_t depth, const uint32_t parent_idx, const uint32_t left_idx,
                          const uint32_t right_idx, N* const left, N* const right)
    {
        const uint32_t left_num  = left->get_num();
        const uint32_t right_num = right->get_num();
        const bool     left_gt   = right_num < left_num;
        int            rc        = 0;
        // small computed directly (sibling = false)
        // large computed as sibling (sibling = true)
        if (left_gt) {
            rc = process_single_node(right_num, depth, right_idx, right, false);
            if (0 != rc)
                return rc;
            rc = process_single_node(left_num, depth, left_idx, left, true, parent_idx, right_idx);
        } else {
            rc = process_single_node(left_num, depth, left_idx, left, false);
            if (0 != rc)
                return rc;
            rc = process_single_node(right_num, depth, right_idx, right, true, parent_idx, left_idx);
        }
        assert(0 == rc);
        return rc;
    }

    int process_single_node(const uint32_t len, const uint32_t depth, const uint32_t node_idx, N* const node,
                            bool is_sibling = false, const int32_t parent_idx = -1, const int32_t sibling_idx = -1)
    {
        if (len < 2 * hist_nbins_)
            is_sibling = false; // faster to compute directly
        const uint32_t tid = omp_get_thread_num();
        if (!is_sibling)
            node_dev_md_[node_idx].hist_idx = hist_node_alloc_.fetch_add(1U);
        else
            node_dev_md_[node_idx].hist_idx = node_dev_md_[parent_idx].hist_idx;
        const uint32_t dev_nex_idx  = node_dev_md_[node_idx].nex_idx;
        uint32_t       dev_hist_idx = node_dev_md_[node_idx].hist_idx;
        if (max_nodes_gpu_ <= node_dev_md_[node_idx].hist_idx || max_nodes_gpu_ <= hist_node_alloc_) {
#ifdef DEBUG_VERIFY
            printf("[HistSolverGPU]: no enough GPU memory to hold the histograms max_nodes=%u hist_idx=%u\n",
                   max_nodes_gpu_, node_dev_md_[node_idx].hist_idx);
            node->pretty_print(node_idx);
#endif
            dev_hist_idx                      = max_nodes_gpu_ + tid;
            hist_bin_t* const dev_hist_to_use = &dev_hist_[dev_hist_idx * hist_nbins_ * num_ft_];
            node_dev_md_[node_idx].hist_idx   = dev_hist_idx;
            glm::cuda_safe(
                cudaMemsetAsync(dev_hist_to_use, 0, num_ft_ * hist_nbins_ * sizeof(hist_bin_t), streams_[tid]),
                "[HistSolverGPU] cuda call failed");
            is_sibling = false;
        }
        assert(tid < MAX_STREAM_NR && 0 < len && dev_hist_idx < (max_nodes_gpu_ + MAX_STREAM_NR));
        assert(node_idx < node_dev_md_.size() && GPU_INVAL_NEX != node_dev_md_[node_idx].nex_idx);
        hist_bin_t* const     dev_hist_to_use = &dev_hist_[dev_hist_idx * hist_nbins_ * num_ft_];
        const ex_lab_t* const dev_nex_to_use  = 0 == depth % 2 ? dev_nex_ : dev_nex_out_;

        // copy node to gpu
        host_nodes_[tid]->init_node(reinterpret_cast<const N*>(node));
        glm::cuda_safe(
            cudaMemcpyAsync(dev_node_in_[tid], host_nodes_[tid], sizeof(N), cudaMemcpyHostToDevice, streams_[tid]),
            "[HistSolverGPU] cuda call failed");

        glm::cuda_safe(cudaStreamSynchronize(streams_[tid]),
                       "[HistSolverGPU::process_single_node] Could not synchronize stream"); // memset
        if (is_sibling) {
            // compute histogram based on sibling's histogram
            const uint32_t          dev_hist_sibling_idx = node_dev_md_[sibling_idx].hist_idx;
            const hist_bin_t* const dev_hist_sibling     = &dev_hist_[dev_hist_sibling_idx * hist_nbins_ * num_ft_];
            assert(dev_hist_sibling != dev_hist_to_use);
            // Note that we use fts_.size() and not
            // num_ft_effective, this is to support the max_features and
            // colsample_bytree in the same implementation
            dev_recompute_hist_bin_sibling<N><<<dim3(hist_nbins_, ceil(fts_.size() / 32.0)), 32, 0, streams_[tid]>>>(
                fts_.size(), hist_nbins_, dev_fts_, dev_hist_to_use /*in/out*/, dev_hist_sibling /*in*/);
        } else {
            // compute histogram directly
            dev_recompute_hist_bin<N><<<dim3(len, ceil(double(fts_.size()) / 32.0)), 32, 0, streams_[tid]>>>(
                num_ft_, fts_.size(), hist_nbins_, dev_fts_, &dev_nex_to_use[dev_nex_idx], dev_ex_to_bin_,
                dev_hist_to_use);
        }
#ifdef DEBUG_VERIFY
        glm::cuda_safe(cudaMemcpyAsync(host_hist_[tid], dev_hist_to_use, num_ft_ * hist_nbins_ * sizeof(hist_bin_t),
                                       cudaMemcpyDeviceToHost, streams_[tid]),
                       "[HistSolverGPU] cuda call failed");
        glm::cuda_safe(cudaStreamSynchronize(streams_[tid]),
                       "[HistSolverGPU::process_single_node] Could not synchronize stream");
#endif
        // dev_node_init<N> <<<dim3(num_ft_effective_), hist_nbins_, 0, streams_[tid] >>> (dev_fts_, dev_node_in_[tid],
        // dev_nodes_[tid]);
        // dev_prep_best_split<N> <<<dim3(num_ft_effective_, hist_nbins_), hist_nbins_, 0, streams_[tid] >>> (dev_fts_,
        // dev_hist_to_use, dev_nodes_[tid]);
        // dev_prep_best_split3<N> <<<dim3(num_ft_effective_, ceil(hist_nbins_/32.0)), 32, 0, streams_[tid] >>>
        // (hist_nbins_, dev_fts_, dev_hist_to_use, dev_nodes_[tid]);
        // dev_prep_best_split3<N> <<<dim3(num_ft_effective_, hist_nbins_), 32, 0, streams_[tid] >>> (hist_nbins_,
        // dev_fts_, dev_hist_to_use, dev_nodes_[tid]);
        // dev_prep_best_split2<N> <<<dim3(len, ceil(num_ft_effective_/32.0)), 32, 0, streams_[tid] >>>
        // (num_ft_effective_, num_ft_, hist_nbins_, dev_fts_, dev_hist_to_use, dev_nex_to_use, dev_ex_to_bin_,
        // dev_nodes_[tid]);
        // dev_compute_best_split3<N> <<<dim3(num_ft_effective_), hist_nbins_, 0, streams_[tid] >>>
        // (tree_params_.split_criterion, tree_params_.min_samples_leaf, tree_params_.lambda, dev_fts_, dev_hist_val_,
        // dev_hist_to_use, dev_nodes_[tid]); dev_compute_best_split<N> <<<dim3(num_ft_effective_,
        // ceil(double(hist_nbins_)/256.0)), 256, 0, streams_[tid] >>> (num_ft_effective_, hist_nbins_,
        // snapml::split_t::mse, 1U, 1.0, dev_fts_, dev_hist_val_, dev_hist_to_use, dev_node_in_[tid], dev_nodes_[tid]);
        dev_compute_best_split2<N><<<ceil(num_ft_effective_ / 32.0), 32, 0, streams_[tid]>>>(
            num_ft_effective_, hist_nbins_, tree_params_.split_criterion, tree_params_.min_samples_leaf,
            tree_params_.lambda, dev_fts_, dev_hist_val_, dev_hist_to_use, dev_node_in_[tid], dev_nodes_[tid]);
#ifdef DEBUG_VERIFY
        {
            glm::cuda_safe(cudaStreamSynchronize(streams_[tid]),
                           "[HistSolverGPU::process_single_node] Could not synchronize stream");
            std::vector<N> nodes(num_ft_effective_);
            for (uint32_t ft = 0; ft < num_ft_effective_; ++ft) {
                glm::cuda_safe(
                    cudaMemcpy(host_nodes_[tid], &dev_nodes_[tid][fts_[ft]], sizeof(N), cudaMemcpyDeviceToHost),
                    "[HistSolverGPU] cuda call failed");
                N::init_node(&nodes[ft], (const N*)host_nodes_[tid]);
            }
            glm::cuda_safe(cudaStreamSynchronize(streams_[tid]),
                           "[HistSolverGPU::process_single_node] Could not synchronize stream");
        }
#endif
        if (num_ft_effective_ <= (uint32_t)device_prop_.maxThreadsPerBlock) {
            dev_reduce_best_split<N>
                <<<1, num_ft_effective_, 0, streams_[tid]>>>(num_ft_effective_, hist_nbins_, dev_fts_, dev_nodes_[tid]);
        } else {
            uint32_t ft_rem = num_ft_effective_;
            while (ft_rem) {
                uint32_t len    = std::min(ft_rem, (uint32_t)device_prop_.maxThreadsPerBlock);
                uint32_t ft_off = ft_rem - len;
                dev_reduce_best_split<N>
                    <<<1, len, 0, streams_[tid]>>>(len, hist_nbins_, &dev_fts_[ft_off], dev_nodes_[tid]);
                if (0 == ft_off)
                    break;
                ft_rem -= len - 1;
            }
        }
        // copy node out
        glm::cuda_safe(cudaMemcpyAsync(host_nodes_[tid], &dev_nodes_[tid][fts_[0]], sizeof(N), cudaMemcpyDeviceToHost,
                                       streams_[tid]),
                       "[HistSolverGPU] cuda call failed");
        glm::cuda_safe(cudaStreamSynchronize(streams_[tid]),
                       "[HistSolverGPU::process_single_node] Could not synchronize stream");
        reinterpret_cast<N*>(node)->init_node((const N*)host_nodes_[tid]);
#ifdef DEBUG_VERIFY
        {
            std::vector<N> nodes(num_ft_effective_);
            for (uint32_t ft = 0; ft < num_ft_effective_; ++ft) {
                glm::cuda_safe(
                    cudaMemcpy(host_nodes_[tid], &dev_nodes_[tid][fts_[ft]], sizeof(N), cudaMemcpyDeviceToHost),
                    "[HistSolverGPU] cuda call failed");
                N::init_node(&nodes[ft], (const N*)host_nodes_[tid]);
            }
            {
                // verify node best split computation
                N test;
                N::init_node(&test, reinterpret_cast<const N*>(node));
                for (uint32_t ft = 0; ft < num_ft_effective_; ++ft) {
                    test.reset();
                    for (uint32_t bin_idx = 0; bin_idx < hist_nbins_; ++bin_idx) {
                        const auto& bin = host_hist_[tid][fts_[ft] * hist_nbins_ + bin_idx];
                        if (0 == bin.weight)
                            continue;
                        const float val = hist_val_[fts_[ft]][bin_idx]; // bin.val
                        test.update_best_hist(fts_[ft], val, tree_params_.min_samples_leaf,
                                              tree_params_.split_criterion, tree_params_.lambda);
                        test.post_update_best_hist(bin.weight, bin.sample_weight, bin.lab_sum, bin.num_pos);
                    }
                }
                assert(test.get_best_feature() == nodes[0].get_best_feature());
            }
            glm::cuda_safe(cudaStreamSynchronize(streams_[tid]),
                           "[HistSolverGPU::process_single_node] Could not synchronize stream");
        }
        {
            std::vector<uint32_t> fts_tmp(num_ft_effective_);
            glm::cuda_safe(
                cudaMemcpy(fts_tmp.data(), dev_fts_, fts_tmp.size() * sizeof(uint32_t), cudaMemcpyDeviceToHost),
                "[HistSolverGPU] cuda call failed");
            for (uint32_t i = 0; i < num_ft_effective_; ++i)
                assert(fts_[i] == fts_tmp[i]);
        }
#endif
        assert(node->get_num() < num_ex_);
        return 0;
    }

    void split_single_node(const uint32_t best_ft, const float best_thr, const uint32_t depth, const N* const left,
                           const N* const right, const uint32_t parent_idx, const uint32_t left_idx,
                           const uint32_t right_idx)
    {
        const uint32_t tid = omp_get_thread_num();
        assert(tid < MAX_STREAM_NR);
        assert(parent_idx < node_dev_md_.size() && GPU_INVAL_NEX != node_dev_md_[parent_idx].nex_idx);
        const uint32_t  left_num           = left->get_num();
        const uint32_t  right_num          = right->get_num();
        const uint32_t  len                = left_num + right_num;
        const uint32_t  dev_nex_idx        = node_dev_md_[parent_idx].nex_idx;
        ex_lab_t* const dev_nex_to_use     = 0 == depth % 2 ? dev_nex_ : dev_nex_out_;
        ex_lab_t* const dev_nex_out_to_use = 0 == depth % 2 ? dev_nex_out_ : dev_nex_;
        assert(1 < len && 1 <= left_num && 1 <= right_num && len <= num_ex_);
        // perform split
        dev_split<<<ceil(double(len) / 32.0), 32, 0, streams_[tid]>>>(len, &dev_nex_to_use[dev_nex_idx], dev_ex_to_bin_,
                                                                      &dev_hist_val_[best_ft * hist_nbins_], num_ft_,
                                                                      best_ft, best_thr, &dev_go_left_[dev_nex_idx]);
        glm::cuda_safe(cudaStreamSynchronize(streams_[tid]),
                       "[HistSolverGPU::split_single_node] Could not synchronize stream");
        // generate permutation
        cub::DevicePartition::Flagged(dev_tmp_storage_[tid], tmp_storage_bytes_, &dev_nex_to_use[dev_nex_idx],
                                      &dev_go_left_[dev_nex_idx], &dev_nex_out_to_use[dev_nex_idx],
                                      &dev_go_left_out_[tid], len, streams_[tid]);
        assert(GPU_INVAL_NEX == node_dev_md_[left_idx].nex_idx && GPU_INVAL_NEX == node_dev_md_[right_idx].nex_idx);

        // paritioning
        node_dev_md_[left_idx].nex_idx  = dev_nex_idx;
        node_dev_md_[right_idx].nex_idx = dev_nex_idx + left_num;

        glm::cuda_safe(cudaStreamSynchronize(streams_[tid]),
                       "[HistSolverGPU::split_single_node] Could not synchronize stream");

#ifdef DEBUG_VERIFY
        int selected_out = -1;
        glm::cuda_safe(cudaMemcpyAsync(&selected_out, &dev_go_left_out_[tid], sizeof(selected_out),
                                       cudaMemcpyDeviceToHost, streams_[tid]),
                       "[HistSolverGPU] cuda call failed");
        std::vector<ex_lab_t> host_nex(len);
        glm::cuda_safe(cudaMemcpyAsync(host_nex.data(), &dev_nex_to_use[dev_nex_idx], len * sizeof(ex_lab_t),
                                       cudaMemcpyDeviceToHost, streams_[tid]),
                       "[HistSolverGPU] cuda call failed");
        std::vector<uint8_t> host_go_left(len);
        glm::cuda_safe(cudaMemcpyAsync(host_go_left.data(), &dev_go_left_[dev_nex_idx], len * sizeof(uint8_t),
                                       cudaMemcpyDeviceToHost, streams_[tid]),
                       "[HistSolverGPU] cuda call failed");
        glm::cuda_safe(cudaStreamSynchronize(streams_[tid]),
                       "[HistSolverGPU::split_single_node] Could not synchronize stream");
        uint32_t count = 0;
        for (uint32_t i = 0; i < len; ++i)
            if (host_go_left[i])
                count++;
        assert(left_num == count);
        // assert(selected_out == left_num);
#endif
    }

private:
    static constexpr uint32_t GPU_INVAL_NEX = (uint32_t)-1;
    struct node_dev_md {
        uint32_t nex_idx  = GPU_INVAL_NEX;
        uint32_t hist_idx = GPU_INVAL_NEX;
    };

    void term()
    {
        glm::cuda_safe(cudaSetDevice(gpu_id_), "[HistSolverGPU] could not set device");
        glm::cuda_safe(cudaDeviceSynchronize(), "[HistSolverGPU] cudaDeviceSynchronize call failed");
        // free GPU memory
        glm::cuda_safe(cudaFree(dev_fts_), "[HistSolverGPU] cudaFree failed [dev_fts_]");
        glm::cuda_safe(cudaFree(dev_nex_), "[HistSolverGPU] cudaFree failed [dev_nex_]");
        glm::cuda_safe(cudaFree(dev_nex_out_), "[HistSolverGPU] cudaFree failed [dev_nex_out_]");
        glm::cuda_safe(cudaFree(dev_go_left_), "[HistSolverGPU] cudaFree failed [dev_go_left_]");
        glm::cuda_safe(cudaFree(dev_go_left_out_), "[HistSolverGPU] cudaFree failed [dev_go_left_out_]");
        glm::cuda_safe(cudaFree(dev_ex_to_bin_), "[HistSolverGPU] cudaFree failed [dev_ex_to_bin_]");
        glm::cuda_safe(cudaFree(dev_hist_val_), "[HistSolverGPU] cudaFree failed [dev_hist_val_]");
        glm::cuda_safe(cudaFree(dev_hist_), "[HistSolverGPU] cudaFree failed [dev_hist_]");
        glm::cuda_safe(cudaFree(dev_tmp_storage_[0]), "[HistSolverGPU] cudaFree failed [dev_tmp_storage_]");
        glm::cuda_safe(cudaFree(dev_preds_), "[HistSolverGPU] cudaFree failed [dev_preds_]");
        glm::cuda_safe(cudaFree(dev_nodes_[0]), "[HistSolverGPU] cudaFree failed [dev_nodes_]");
        glm::cuda_safe(cudaFreeHost(host_hist_[0]), "[HistSolverGPU] cudaFreHost failed [host_hist_]");
        glm::cuda_safe(cudaFreeHost(host_preds_), "[HistSolverGPU] cudaFreeHost failed [host_preds_]");
        glm::cuda_safe(cudaFreeHost(host_nodes_[0]), "[HistSolverGPU] cudaFreeHost failed [host_nodes_]");
        for (uint32_t i = 0; i < MAX_STREAM_NR; ++i) {
            glm::cuda_safe(cudaStreamDestroy(streams_[i]), "[DeviceSolver::~DeviceSolver] Could not destroy stream");
        }
        cudaProfilerStop();
    }

    std::shared_ptr<glm::TreeInvariants<D>>  tree_invariants_;
    const uint32_t                           gpu_id_;
    const std::vector<std::vector<uint8_t>>& ex_to_bin_;
    const std::vector<std::vector<float>>&   hist_val_;
    snapml::DecisionTreeParams               tree_params_;
    cudaDeviceProp                           device_prop_;
    uint64_t                                 num_ex_;
    uint64_t                                 num_ft_;
    uint64_t                                 num_ft_effective_;
    uint32_t                                 hist_nbins_;
    uint32_t                                 num_sm_;
    uint32_t                                 max_nodes_gpu_; // maximum nr of nodes supported based on GPU mem (init)
    // gpu memory
    ex_lab_t*    dev_nex_;
    ex_lab_t*    dev_nex_out_;
    uint8_t*     dev_go_left_;
    uint8_t*     dev_go_left_out_;
    uint8_t*     dev_ex_to_bin_;
    float*       dev_hist_val_;
    size_t       tmp_storage_bytes_;
    size_t       tmp_storage_per_ex_;
    void*        dev_tmp_storage_[MAX_STREAM_NR];
    hist_bin_t*  dev_hist_;
    hist_bin_t*  host_hist_[MAX_STREAM_NR];
    cudaStream_t streams_[MAX_STREAM_NR];
    N*           dev_nodes_[MAX_STREAM_NR];   // one per stream per ft per bin
    N*           dev_node_in_[MAX_STREAM_NR]; // only one node per stream
    N*           host_nodes_[MAX_STREAM_NR];  // only one node per stream
    double*      dev_preds_;
    double*      host_preds_;
    uint32_t*    dev_fts_;

    std::vector<node_dev_md> node_dev_md_;
    std::vector<uint32_t>    fts_;
    std::atomic<uint32_t>    hist_node_alloc_;
    std::mt19937             rng_;

    HistSolverGPU(const HistSolverGPU&&) = delete;
    HistSolverGPU& operator=(const HistSolverGPU&) = delete;
}; // class HistSolverGPU

};     // namespace tree
#endif // _LIBGLM_HIST_SOLVER_GPU_
