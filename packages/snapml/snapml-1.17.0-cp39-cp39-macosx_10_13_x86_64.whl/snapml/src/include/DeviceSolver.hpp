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
 * Authors      : Thomas Parnell
 *                Celestine Duenner
 *                Dimitrios Sarigiannis
 *                Nikolas Ioannou
 *
 * End Copyright
 ********************************************************************/

#ifndef GLM_DEVICE_SOLVER
#define GLM_DEVICE_SOLVER

#include "Solver.hpp"

#include <cub/device/device_radix_sort.cuh>
#include <cub/device/device_reduce.cuh>
#include <cub/iterator/transform_input_iterator.cuh>
#include <random>
#include <sys/time.h>

#include <OMP.hpp>

#include "Checking.hpp"
#include "Kernels.hpp"

#ifdef WITH_NUMA
#include "NumaUtils.hpp"
#endif

namespace glm {

// Solve an Objective on the GPU
template <class D, class O> class DeviceSolver : public Solver {

public:
    // delete copy ctor
    DeviceSolver<D, O>(const DeviceSolver<D, O>&) = delete;

    // ctor
    DeviceSolver<D, O>(D* data, O* obj, double sigma, double tol, uint32_t device_id = 0, size_t gpu_mem_B = 0,
                       uint32_t num_threads = 32, bool add_bias = false, double bias_val = 1.0, bool pin = true,
                       size_t chunking_step_B = 512 * 1024 * 1024)
        : Solver(static_cast<Dataset*>(data), static_cast<Objective*>(obj), sigma, tol, add_bias, bias_val)
    {

        device_id_       = device_id;
        pin_             = pin;
        chunking_step_B_ = chunking_step_B;

        cuda_safe(cudaGetDeviceProperties(&device_prop_, device_id_), "failed to get device properties.");

#ifdef WITH_NUMA
        numa_node_ = cudadevprop_to_numanode(device_prop_);
        if (0 <= numa_node_) {
            // make sure this thread is running on the correct numa
            // node, this will affect the performance of the cuda host
            // malloc'ed memory
            numa_bind_caller_to_node(numa_node_);
        }
#endif

        cuda_safe(cudaSetDevice(device_id_), "[DeviceSolver::DeviceSolver] Could not set device");

        bool transpose = data_->get_transpose();

        if (is_primal<O>::value) {
            if (!transpose) {
                throw std::runtime_error(
                    "[DeviceSolver::DeviceSolver] Primal Objective can only be solved with a transposed dataset.");
            }
        } else {
            if (transpose) {
                throw std::runtime_error(
                    "[DeviceSolver::DeviceSolver] Dual Objective can only be solved with a non-transposed dataset.");
            }
        }

        // damping parameter
        eps_ = 1.0;

        // number of GPU threads
        num_threads_ = num_threads;

        // query availiable GPU memory
        size_t gpu_free_B, gpu_tot_B;
        cuda_safe(cudaMemGetInfo(&gpu_free_B, &gpu_tot_B),
                  "[DeviceSolver::DeviceSolver] Could not get GPU memory info");

        // if set to default value, use all available GPU memory (to nearest GB)
        if (gpu_mem_B == 0) {
            gpu_mem_B = gpu_free_B / 1024 / 1024 / 1024 * 1024 * 1024 * 1024;
        }

        // std::cout << "Gpu Memory Total (MB):    " << gpu_tot_B/1024.0/1024.0   << std::endl;
        // std::cout << "Gpu Free Memory Total (MB):    " << gpu_free_B/1024.0/1024.0   << std::endl;
        // std::cout << "Gpu Free Memory Total(MB) converted: "<<gpu_mem_B/1024.0/1024.0   << std::endl;

        size_t   solv_size_B          = 0;
        size_t   data_size_B          = 0;
        uint32_t max_num_pt_per_chunk = 0;
        size_t   max_num_nz_per_chunk = 0;

        // figure out the chunk size
        fit_memory(gpu_mem_B, max_num_pt_per_chunk, max_num_nz_per_chunk, data_size_B, solv_size_B);

        assert(solv_size_B > 0);
        assert(data_size_B > 0);
        assert(max_num_pt_per_chunk > 0);
        assert(max_num_nz_per_chunk > 0);

        // make the chunks
        this->data_->make_chunks(max_num_nz_per_chunk, this->chunks_, this->chunks_start_, this->chunks_len_);

#ifdef WITH_NUMA
        if (chunks_.size() > 1) {
            if (0 <= numa_node_) {
                data_->set_numa_affinity(numa_node_);
                // have to pin here the numa parts, otherwise they won't
                // be covered by the external pinning (e.g., MultiDeviceSolver)
                if (!pin_)
                    data_->pin_numa_mem();
            }
        }
#endif

        // work out how much temporary storage we need
        tmp_storage_size_B_ = count_tmp_storage_bytes(max_num_pt_per_chunk);

        tmp_storage_size_diff_B_ = count_tmp_storage_bytes_reduce(max_num_pt_per_chunk + shared_len_);
        // pinned memory on host
        cuda_safe(cudaMallocHost(&this->model_, this->model_len_ * sizeof(double)),
                  "[DeviceSolver::DeviceSolver] Could not allocate pinned memory for model");
        cuda_safe(cudaMallocHost(&this->shared_, this->shared_len_ * sizeof(double)),
                  "[DeviceSolver::DeviceSolver] Could not allocate pinned memory for shared vector");
        cuda_safe(cudaMallocHost(&this->shared_cached_, this->shared_len_ * sizeof(double)),
                  "[DeviceSolver::DeviceSolver] Could not allocate pinned memory for cached shared vector");
        cuda_safe(cudaMallocHost(&this->keygen_, max_num_pt_per_chunk * sizeof(uint32_t)),
                  "[DeviceSolver::DeviceSolver] Could not alloacte pinned memory for keygen");

        bool data_on_gpu = static_cast<D*>(data_)->is_data_on_gpu();

        // allocate GPU memory
        if (data_on_gpu) {
            // In case data is already on gpu, Then, there is no need to allocate gpu memory for data;
            cuda_safe(cudaMalloc(&gpuMemory, solv_size_B),
                      "[DeviceSolver::DeviceSolver] Could not allocate device memory");
        } else {
            cuda_safe(cudaMalloc(&gpuMemory, data_size_B + solv_size_B),
                      "[DeviceSolver::DeviceSolver] Could not allocate device memory");
        }

        // pin the memory
        if (pin_) {
            static_cast<D*>(data_)->pin_memory();
        }

        // initialize data
        size_t pos       = 0;
        this->dev_model_ = reinterpret_cast<double*>(&gpuMemory[pos]);
        pos += this->model_len_ * sizeof(double);
        this->dev_model_save_ = reinterpret_cast<double*>(&gpuMemory[pos]);
        pos += this->model_len_ * sizeof(double);
        this->dev_shared_ = reinterpret_cast<double*>(&gpuMemory[pos]);
        pos += this->shared_len_ * sizeof(double);
        this->dev_shared_cached_ = reinterpret_cast<double*>(&gpuMemory[pos]);
        pos += this->shared_len_ * sizeof(double);
        this->dev_c1_ = reinterpret_cast<double*>(&gpuMemory[pos]);
        pos += this->shared_len_ * sizeof(double);
        this->dev_c2_ = reinterpret_cast<double*>(&gpuMemory[pos]);
        pos += this->shared_len_ * sizeof(double);
        this->dev_local_cost_ = reinterpret_cast<double*>(&gpuMemory[pos]);
        pos += sizeof(double);
        this->dev_max_rdiff_ = reinterpret_cast<double*>(&gpuMemory[pos]);
        pos += sizeof(double);
        this->dev_diff_ = reinterpret_cast<double*>(&gpuMemory[pos]);
        pos += (max_num_pt_per_chunk + shared_len_) * sizeof(double);
        this->dev_rdiff_ = reinterpret_cast<double*>(&gpuMemory[pos]);
        pos += (2 * max_num_pt_per_chunk) * sizeof(double);

        if (is_primal<O>::value && add_bias_) {
            this->dev_bias_ = reinterpret_cast<double*>(&gpuMemory[pos]);
            pos += sizeof(double);
            this->dev_bias_diff_ = reinterpret_cast<double*>(&gpuMemory[pos]);
            pos += sizeof(double);
            this->dev_bias_rdiff_ = reinterpret_cast<double*>(&gpuMemory[pos]);
            pos += 2 * sizeof(double);
        }

        static_cast<D*>(data_)->gpu_init(pos, gpuMemory, this->chunks_len_, this->chunks_start_);

        this->dev_keygen_ = reinterpret_cast<uint32_t*>(&gpuMemory[pos]);
        pos += max_num_pt_per_chunk * sizeof(uint32_t);
        this->dev_keygen_out_ = reinterpret_cast<uint32_t*>(&gpuMemory[pos]);
        pos += max_num_pt_per_chunk * sizeof(uint32_t);
        this->dev_perm_out_ = reinterpret_cast<uint32_t*>(&gpuMemory[pos]);
        pos += max_num_pt_per_chunk * sizeof(uint32_t);

        this->dev_perms_.resize(this->chunks_.size());
        for (size_t c = 0; c < this->chunks_.size(); c++) {
            this->dev_perms_[c] = reinterpret_cast<uint32_t*>(&gpuMemory[pos]);
            pos += this->chunks_[c].size() * sizeof(uint32_t);
        }

        this->dev_tmp_ = reinterpret_cast<uint8_t*>(&gpuMemory[pos]);
        pos += tmp_storage_size_B_;
        this->dev_tmp_diff_ = reinterpret_cast<uint8_t*>(&gpuMemory[pos]);
        pos += tmp_storage_size_diff_B_;

        if (data_on_gpu)
            assert(pos == solv_size_B);
        else
            assert(pos == data_size_B + solv_size_B);

        // copy chunks in
        for (size_t c = 0; c < this->chunks_.size(); c++) {
            cuda_safe(cudaMemcpy(this->dev_perms_[c], &this->chunks_[c][0], this->chunks_[c].size() * sizeof(uint32_t),
                                 cudaMemcpyHostToDevice),
                      "[DeviceSolver::DeviceSolver] Could not copy perms onto device");
        }

        this->grids_.resize(this->chunks_.size());
        for (uint32_t c = 0; c < this->chunks_.size(); c++) {
            int num_rows    = 8192;
            int num_cols    = (int)ceil(double(this->chunks_[c].size()) / double(num_rows));
            this->grids_[c] = dim3(num_rows, num_cols);
        }

        // std::cout << "model length" << this->model_len_ << std::endl;

        int num_rows        = 8192;
        int num_cols        = (int)ceil(double(this->shared_len_) / double(num_threads_) / double(num_rows));
        int num_cols_mlen   = (int)ceil(double(this->model_len_) / double(num_threads_) / double(num_rows));
        grid_transform      = dim3(num_rows, num_cols);
        grid_transform_mlen = dim3(num_rows, num_cols_mlen);

        num_cpu_threads_ = 4;
        xorseeds_.resize(num_cpu_threads_);

        stop_.resize(this->chunks_.size());

        // generate intial rng
        generate_rng(0);

        // create streams
        cuda_safe(cudaStreamCreate(&this->stream1_), "[DeviceSolver::DeviceSolver] Could not create stream1");
        cuda_safe(cudaStreamCreate(&this->stream2_), "[DeviceSolver::DeviceSolver] Could not create stream2");
    }

    // dtor
    virtual ~DeviceSolver<D, O>()
    {

        cuda_safe(cudaSetDevice(device_id_), "[DeviceSolver::~DeviceSolver] Could not set device");

        // pin the memory
        if (pin_) {
            static_cast<D*>(data_)->unpin_memory();
        }
        // std::cout << "Destroying DeviceSolver: " << typeid(O).name() << std::endl;

        cuda_safe(cudaStreamDestroy(this->stream1_), "[DeviceSolver::~DeviceSolver] Could not destroy stream1");
        cuda_safe(cudaStreamDestroy(this->stream2_), "[DeviceSolver::~DeviceSolver] Could not destroy stream2");

        cuda_safe(cudaFreeHost(this->model_), "[DeviceSolver::~DeviceSolver] Could not free host memory for model");
        cuda_safe(cudaFreeHost(this->shared_),
                  "[DeviceSolver::~DeviceSolver] Could not free host memory for shared vector");
        cuda_safe(cudaFreeHost(this->shared_cached_),
                  "[DeviceSolver::~DeviceSolver] Could not free host memory for cached shared vector");
        cuda_safe(cudaFreeHost(this->keygen_), "[DeviceSolver::~DeviceSolver] Could not free host memory for keygen");

        cuda_safe(cudaFree(gpuMemory), "[DeviceSolver::~DeviceSolver] Could not free device memory");
        // cuda_safe(cudaDeviceReset(), "[DeviceSolver::~DeviceSolver] Could not reset GPU device");
    }

    // set new value of shared vector
    virtual void set_shared(const double* const shared_new)
    {

        cuda_safe(cudaSetDevice(device_id_), "[DeviceSolver::set_shared] Could not set device");

        // load new shared vector into shared_cached
        for (uint32_t i = 0; i < this->shared_len_; i++) {
            this->shared_cached_[i] = shared_new[i];
        }

        // copy onto device
        cuda_safe(cudaMemcpy(this->dev_shared_cached_, this->shared_cached_, this->shared_len_ * sizeof(double),
                             cudaMemcpyHostToDevice),
                  "[DeviceSolver::set_shared] Could not copy shared vector onto device");
    }

    virtual void init(double* const shared_out)
    {
        cuda_safe(cudaSetDevice(device_id_), "[DeviceSolver::init] Could not set device");

        auto x = static_cast<D*>(data_)->get_data();
        auto p = static_cast<O*>(obj_)->get_params();

        bool data_on_gpu = false;
        data_on_gpu      = static_cast<D*>(data_)->is_data_on_gpu();

        if (data_on_gpu == false) {
            for (uint32_t pt = 0; pt < this->model_len_; pt++) {
                double this_lab  = is_primal<O>::value ? 0.0 : O::lab_transform(x.labs[pt]);
                this->model_[pt] = O::init_model(p, this_lab);
            }
            // copy onto GPU
            cuda_safe(
                cudaMemcpy(this->dev_model_, this->model_, this->model_len_ * sizeof(double), cudaMemcpyHostToDevice),
                "[DeviceSolver::init] Could not copy model onto device");
        } else {
            dev_model_init<D, O>
                <<<grid_transform_mlen, num_threads_>>>(num_threads_, this->model_len_, x, this->dev_model_, p);
            cuda_safe(cudaDeviceSynchronize(), "[DeviceSolver::init] Could not synchronize device");
        }

        // initialize shared vector
        for (uint32_t i = 0; i < this->shared_len_; i++) {
            this->shared_[i] = 0.0;
        }

        cuda_safe(
            cudaMemcpy(this->dev_shared_, this->shared_, this->shared_len_ * sizeof(double), cudaMemcpyHostToDevice),
            "[DeviceSolver::init] Could not copy shared vector onto device");

        bool stop = false;

        while (!stop) {

            auto x = static_cast<D*>(data_)->get_dev_data();

            uint32_t cur_chunk = static_cast<D*>(data_)->get_cur_chunk();
            uint32_t nxt_chunk = static_cast<D*>(data_)->get_nxt_chunk();

            stop = (nxt_chunk == 0);

            if (is_primal<O>::value && add_bias_) {
                if (cur_chunk == 0 && data_->get_partition_id() == 0) {
                    dev_init_bias_primal<D, O><<<1, num_threads_, 0, this->stream1_>>>(
                        num_threads_, x, p, dev_bias_, dev_shared_, shared_len_, bias_val_);
                }
            }

            // initialize shared vector on device
            if (add_bias_) {
                dev_init<D, O, true><<<this->grids_[cur_chunk], num_threads_, 0, this->stream1_>>>(
                    num_threads_, x, p, this->dev_model_, this->dev_shared_, this->dev_perms_[cur_chunk],
                    this->chunks_[cur_chunk].size(), shared_len_, bias_val_);
            } else {
                dev_init<D, O, false><<<this->grids_[cur_chunk], num_threads_, 0, this->stream1_>>>(
                    num_threads_, x, p, this->dev_model_, this->dev_shared_, this->dev_perms_[cur_chunk],
                    this->chunks_[cur_chunk].size(), shared_len_, bias_val_);
            }
            static_cast<D*>(data_)->copy_next_chunk(this->stream2_);

            cuda_safe(cudaDeviceSynchronize(), "[DeviceSolver::init] Could not synchronize device");

            static_cast<D*>(data_)->rotate_chunks();
        }

        if (shared_out != nullptr) {

            // copy shared vector back from device to host
            cuda_safe(cudaMemcpy(shared_, dev_shared_, shared_len_ * sizeof(double), cudaMemcpyDeviceToHost),
                      "[DeviceSolver::init] Could not copy shared vector from device to host");

            // copy out for controller to aggregate
            memcpy(shared_out, shared_, sizeof(*shared_out) * shared_len_);

        } else {
            // get the cached shared vector
            cuda_safe(
                cudaMemcpy(dev_shared_cached_, dev_shared_, shared_len_ * sizeof(double), cudaMemcpyDeviceToDevice),
                "[DeviceSolver::get_update] Could not copy shared vector from device to device");
        }
    }

    // compute cost function
    virtual double partial_cost()
    {

        cuda_safe(cudaSetDevice(device_id_), "[DeviceSolver::partial_cost] Could not set device");

        if (is_primal<O>::value && add_bias_) {
            if (data_->get_partition_id() == 0) {
                cuda_safe(cudaMemcpy(&bias_, dev_bias_, sizeof(double), cudaMemcpyDeviceToHost),
                          "[DeviceSolver::partial_cost] Could not copy bias term from device to host");
            }
        }

        // get model
        cuda_safe(cudaMemcpy(model_, dev_model_, model_len_ * sizeof(double), cudaMemcpyDeviceToHost),
                  "[DeviceSolver::partial_cost] Could not copy model from device to host");

        // copy shared vector back from device to host
        cuda_safe(cudaMemcpy(shared_cached_, dev_shared_cached_, shared_len_ * sizeof(double), cudaMemcpyDeviceToHost),
                  "[DeviceSolver::init] Could not copy shared vector from device to host");

        return Solver::partial_cost_impl<D, O>();
    }

    // get final model vector
    virtual void get_model(double* const x)
    {

        cuda_safe(cudaSetDevice(device_id_), "[DeviceSolver::get_model] Could not set device");

        if (is_primal<O>::value && add_bias_) {
            if (data_->get_partition_id() == 0) {
                cuda_safe(cudaMemcpy(&bias_, dev_bias_, sizeof(double), cudaMemcpyDeviceToHost),
                          "[DeviceSolver::partial_cost] Could not copy bias term from device to host");
            }
        }

        // get model
        cuda_safe(cudaMemcpy(this->model_, this->dev_model_, this->model_len_ * sizeof(double), cudaMemcpyDeviceToHost),
                  "[DeviceSolver::get_model] Could not copy model from device to host");

        // copy shared vector back from device to host
        cuda_safe(cudaMemcpy(shared_cached_, dev_shared_cached_, shared_len_ * sizeof(double), cudaMemcpyDeviceToHost),
                  "[DeviceSolver::init] Could not copy shared vector from device to host");

        Solver::get_model_impl<O>(x);
    }

    // get non-zero coordinates
    virtual void get_nz_coordinates(std::vector<uint32_t>& x)
    {

        cuda_safe(cudaSetDevice(device_id_), "[DeviceSolver::get_model] Could not set device");

        // get model
        cuda_safe(cudaMemcpy(this->model_, this->dev_model_, this->model_len_ * sizeof(double), cudaMemcpyDeviceToHost),
                  "[DeviceSolver::get_model] Could not copy model from device to host");

        Solver::get_nz_coordinates_impl<O>(x);
    }

    // perform an epoch
    virtual bool get_update(double* const shared_out)
    {

#ifdef WITH_NUMA
        if (0 <= numa_node_)
            numa_bind_caller_to_node(numa_node_);
#endif

        // struct timeval t1, t2;
        // gettimeofday(&t1, NULL);

        cuda_safe(cudaSetDevice(device_id_), "[DeviceSolver::get_update] Could not set device");

        auto x = static_cast<D*>(data_)->get_dev_data();
        auto p = static_cast<O*>(obj_)->get_params();

        // cache model
        cuda_safe(cudaMemcpy(dev_model_save_, dev_model_, model_len_ * sizeof(double), cudaMemcpyDeviceToDevice),
                  "[DeviceSolver::get_update] Could not cache model");

        // transform shared vector
        dev_transform<D, O><<<grid_transform, num_threads_, 0, stream1_>>>(num_threads_, this->shared_len_, x, p,
                                                                           this->dev_shared_, this->dev_shared_cached_,
                                                                           this->dev_c1_, this->dev_c2_);

        uint32_t cur_chunk = static_cast<D*>(data_)->get_cur_chunk();
        uint32_t nxt_chunk = static_cast<D*>(data_)->get_nxt_chunk();

        // copy on the keygen for the current chunk
        cuda_safe(cudaMemcpyAsync(this->dev_keygen_, this->keygen_, this->chunks_[cur_chunk].size() * sizeof(uint32_t),
                                  cudaMemcpyHostToDevice, this->stream1_),
                  "[DeviceSolver::get_update] Could not copy keygen onto device");

        cuda_safe(cudaStreamSynchronize(this->stream1_), "[DeviceSolver::get_update] Could not synchronize stream1");

        // start copying the data for the next chunk
        static_cast<D*>(data_)->copy_next_chunk(this->stream2_);

        // generate permutation
        cuda_safe(cub::DeviceRadixSort::SortPairs(this->dev_tmp_, tmp_storage_size_B_, this->dev_keygen_,
                                                  this->dev_keygen_out_, this->dev_perms_[cur_chunk],
                                                  this->dev_perm_out_, this->chunks_[cur_chunk].size(), 0,
                                                  sizeof(uint32_t) * 8, this->stream1_),
                  "[DeviceSolver::get_update] Could not generate permutation");

        size_t dynamic_shared_mem_B = 2 * num_threads_ * sizeof(double);

        if (is_primal<O>::value && add_bias_) {
            if (cur_chunk == 0 && data_->get_partition_id() == 0) {
                dev_epoch_bias_primal<D, O><<<1, num_threads_, dynamic_shared_mem_B, this->stream1_>>>(
                    num_threads_, x, p, dev_bias_, dev_shared_, dev_c2_, eps_, sigma_, dev_bias_diff_, dev_bias_rdiff_,
                    shared_len_, bias_val_);
            }
        }

        // Solve on the GPU
        if (add_bias_) {
            dev_epoch<D, O, true><<<this->grids_[cur_chunk], num_threads_, dynamic_shared_mem_B, this->stream1_>>>(
                num_threads_, x, p, this->dev_model_, this->dev_shared_, this->dev_c2_, this->eps_, this->sigma_,
                this->dev_perm_out_, this->chunks_[cur_chunk].size(), dev_diff_, dev_rdiff_, shared_len_, bias_val_);
        } else {
            dev_epoch<D, O, false><<<this->grids_[cur_chunk], num_threads_, dynamic_shared_mem_B, this->stream1_>>>(
                num_threads_, x, p, this->dev_model_, this->dev_shared_, this->dev_c2_, this->eps_, this->sigma_,
                this->dev_perm_out_, this->chunks_[cur_chunk].size(), dev_diff_, dev_rdiff_, shared_len_, bias_val_);
        }
        // generate random numbers
        generate_rng(nxt_chunk);

        cuda_safe(cudaDeviceSynchronize(), "[DeviceSolver::get_update] Could not synchronize device");

        // subtract c1/c2 from shared vector on GPU
        dev_subtract<D, O><<<grid_transform, num_threads_>>>(
            num_threads_, this->shared_len_, data_->get_num_partitions(), x, p, this->dev_shared_,
            this->dev_shared_cached_, this->dev_c1_, this->dev_c2_, sigma_, &dev_diff_[chunks_[cur_chunk].size()]);

        cuda_safe(cub::DeviceReduce::Sum(dev_tmp_diff_, tmp_storage_size_diff_B_, dev_diff_, dev_local_cost_,
                                         chunks_[cur_chunk].size() + shared_len_),
                  "[DeviceSolver::get_update] Could not reduce");
        double local_cost_diff = 0.0;
        cuda_safe(cudaMemcpy(&local_cost_diff, dev_local_cost_, sizeof(double), cudaMemcpyDeviceToHost),
                  "[DeviceSolver::get_update] Could not copy local cost from device to host");

        // norm of diff
        cuda_safe(cub::DeviceReduce::Sum(dev_tmp_diff_, tmp_storage_size_diff_B_, dev_rdiff_, dev_max_rdiff_,
                                         chunks_[cur_chunk].size()),
                  "[DeviceSolver::get_update] Could not reduce");
        double norm_diff = 0.0;
        cuda_safe(cudaMemcpy(&norm_diff, dev_max_rdiff_, sizeof(double), cudaMemcpyDeviceToHost),
                  "[DeviceSolver::get_update] Could not copy max rdiff from device to host");

        // norm of model
        cuda_safe(cub::DeviceReduce::Sum(dev_tmp_diff_, tmp_storage_size_diff_B_,
                                         &dev_rdiff_[chunks_[cur_chunk].size()], dev_max_rdiff_,
                                         chunks_[cur_chunk].size()),
                  "[DeviceSolver::get_update] Could not reduce");
        double norm_model = 0.0;
        cuda_safe(cudaMemcpy(&norm_model, dev_max_rdiff_, sizeof(double), cudaMemcpyDeviceToHost),
                  "[DeviceSolver::get_update] Could not copy max rdiff from device to host");

        if (is_primal<O>::value && add_bias_) {
            if (cur_chunk == 0 && data_->get_partition_id() == 0) {
                double local_cost_bias_diff = 0.0;
                cuda_safe(cudaMemcpy(&local_cost_bias_diff, dev_bias_diff_, sizeof(double), cudaMemcpyDeviceToHost),
                          "[DeviceSolver::get_update] Could not copy local cost (bias) from device to host");
                local_cost_diff += local_cost_bias_diff;
                double norm_bias_diff = 0.0;
                cuda_safe(cudaMemcpy(&norm_bias_diff, &dev_bias_rdiff_[0], sizeof(double), cudaMemcpyDeviceToHost),
                          "[DeviceSolver::get_update] Could not copy max rdiff (bias) from device to host");
                norm_diff += norm_bias_diff;
                double norm_bias_model = 0.0;
                cuda_safe(cudaMemcpy(&norm_bias_model, &dev_bias_rdiff_[1], sizeof(double), cudaMemcpyDeviceToHost),
                          "[DeviceSolver::get_update] Could not copy max rdiff (bias) from device to host");
                norm_model += norm_bias_model;
            }
        }

        /*
        std::cout << "norm_diff = "  << norm_diff << std::endl;
        std::cout << "norm_model = " << norm_model << std::endl;
        std::cout << "norm_ratio = " << norm_diff/norm_model << std::endl;
        */

        if (isnan(local_cost_diff) || local_cost_diff < 0) {

            // revert to saved model in device
            std::swap(dev_model_, dev_model_save_);

            if (shared_out != nullptr) {
                // get the cached shared vector
                cuda_safe(cudaMemcpy(shared_, dev_shared_cached_, shared_len_ * sizeof(double), cudaMemcpyDeviceToHost),
                          "[DeviceSolver::get_update] Could not copy shared delta from device to host");
                // copy out
                memcpy(shared_out, shared_, shared_len_ * sizeof(double));
            }

            // decrease eps_
            eps_ *= 0.5;

            // std::cout << "eps = " << eps_ << std::endl;

        } else {

            if (shared_out != nullptr) {
                // copy shared vector back from device to host
                cuda_safe(cudaMemcpy(shared_, dev_shared_, shared_len_ * sizeof(double), cudaMemcpyDeviceToHost),
                          "[DeviceSolver::get_update] Could not copy shared delta from device to host");

                // copy out
                memcpy(shared_out, shared_, shared_len_ * sizeof(double));

            } else {

                std::swap(dev_shared_cached_, dev_shared_);
            }

            stop_[cur_chunk] = (norm_diff / norm_model < tol_);
            // std::cout << "max_rdiff = " << max_rdiff << std::endl;
        }

        static_cast<D*>(data_)->rotate_chunks();

        // gettimeofday(&t2, NULL);
        // double t_elap = double(t2.tv_usec-t1.tv_usec)/1000.0 + double(t2.tv_sec-t1.tv_sec)*1000.0;
        // std::cout << "t_elap = " << t_elap << std::endl;

        // stop if all chunks are converged
        bool stop = true;
        for (uint32_t i = 0; i < stop_.size(); i++) {
            stop &= stop_[i];
        }

        return stop;
    }

    void update_shared_cached()
    {
        cuda_safe(cudaMemcpy(shared_cached_, dev_shared_cached_, shared_len_ * sizeof(double), cudaMemcpyDeviceToHost),
                  "[DeviceSolver::init] Could not copy shared vector from device to host");
    }

private:
    // get total memory requirements
    size_t get_size_B(uint32_t max_num_pt_per_chunk)
    {

        size_t out = 0;
        out += this->model_len_ * sizeof(double);                     // dev_model
        out += this->model_len_ * sizeof(double);                     // dev_model_save
        out += this->shared_len_ * sizeof(double);                    // dev_shared
        out += this->shared_len_ * sizeof(double);                    // dev_shared_cached
        out += this->shared_len_ * sizeof(double);                    // dev_c1
        out += this->shared_len_ * sizeof(double);                    // dev_c2
        out += (max_num_pt_per_chunk + shared_len_) * sizeof(double); // dev_gdiff;
        out += (2 * max_num_pt_per_chunk) * sizeof(double);           // dev_rdiff;
        out += sizeof(double);                                        // dev_local_cost
        out += sizeof(double);                                        // dev_max_rdiff
        if (is_primal<O>::value && add_bias_) {
            out += sizeof(double);     // dev_bias
            out += sizeof(double);     // dev_bias_diff
            out += 2 * sizeof(double); // dev_bias_rdiff
        }
        out += this->model_len_ * sizeof(uint32_t);                                // dev_perms
        out += max_num_pt_per_chunk * sizeof(uint32_t);                            // dev_keygen
        out += max_num_pt_per_chunk * sizeof(uint32_t);                            // dev_keygen_out
        out += max_num_pt_per_chunk * sizeof(uint32_t);                            // dev_perm_out
        out += count_tmp_storage_bytes(max_num_pt_per_chunk);                      // dev_tmp
        out += count_tmp_storage_bytes_reduce(max_num_pt_per_chunk + shared_len_); // dev_tmp_diff
        return out;
    }

    static size_t count_tmp_storage_bytes(uint32_t x)
    {

        size_t tmp_storage_bytes;

        void*     d_tmp_storage = nullptr;
        uint32_t* dummy         = nullptr;

        cuda_safe(cub::DeviceRadixSort::SortPairs(d_tmp_storage, tmp_storage_bytes, dummy, dummy, dummy, dummy, x),
                  "[DeviceSolver::count_tmp_storage_bytes] Could not count temp storage bytes");

        return tmp_storage_bytes;
    }

    static size_t count_tmp_storage_bytes_reduce(uint32_t x)
    {
        size_t  tmp_storage_bytes = 0;
        void*   d_tmp_storage     = nullptr;
        double* d_in              = nullptr;
        double* d_out             = nullptr;
        cuda_safe(cub::DeviceReduce::Sum(d_tmp_storage, tmp_storage_bytes, d_in, d_out, x),
                  "[DeviceSolver::count_tmp_storage_bytes_reduce] Could not count temp storage bytes");
        return tmp_storage_bytes;
    }

    void fit_memory(size_t gpu_mem_B, uint32_t& max_num_pt_per_chunk, size_t& max_num_nz_per_chunk, size_t& data_size_B,
                    size_t& solv_size_B)
    {

        // get total data size (assuming no chunking)
        size_t mem_usage_B;
        data_size_B = this->data_->get_total_size_B();

        // get solver size (assuming all points are loaded)
        solv_size_B = get_size_B(this->data_->get_this_num_pt());

        // std::cout << "data_size_B = " << data_size_B << std::endl;
        // std::cout << "solv_size_B = " << solv_size_B << std::endl;
        // std::cout << "gpu_mem_B   = " << gpu_mem_B   << std::endl;

        bool data_on_gpu = this->data_->is_data_on_gpu();
        // total memory usage
        if (data_on_gpu) {
            // If data is already on gpu ; then effective memory usage
            // is only for solv_size required on gpu
            mem_usage_B = solv_size_B;
            assert(mem_usage_B <= gpu_mem_B);

        } else {
            mem_usage_B = data_size_B + solv_size_B;
        }

        if (mem_usage_B <= gpu_mem_B) {
            // std::cout << "Data fits without chunking. " << std::endl;
            max_num_pt_per_chunk = this->data_->get_this_num_pt();
            max_num_nz_per_chunk = this->data_->get_num_nz();
        } else {
            // std::cout << "Data does not fit, need to chunk" << std::endl;

            // struct timeval t1, t2;
            // gettimeofday(&t1, NULL);

            uint32_t              num_tries = 8;
            std::vector<uint64_t> res_chunk(num_tries);
            std::vector<uint32_t> res_pt(num_tries);
            std::vector<uint64_t> res_nz(num_tries);
            std::vector<uint64_t> res_data(num_tries);
            std::vector<uint64_t> res_solver(num_tries);

            uint64_t step = gpu_mem_B / uint64_t(2 * num_tries);

            omp_set_num_threads(num_tries);
            OMP::parallel_for<int32_t>(
                0, num_tries, [this, &res_chunk, &step, &res_pt, &res_nz, &res_data, &res_solver](const int32_t& i) {
                    res_chunk[i] = uint64_t(i + 1) * step;
                    this->data_->try_chunk(res_chunk[i], res_pt[i], res_nz[i]);
                    res_data[i]   = this->data_->get_chunked_size_B(res_nz[i]);
                    res_solver[i] = get_size_B(res_pt[i]);
                });

            mem_usage_B = gpu_mem_B;
            uint32_t i  = 0;
            // uint64_t max_chunk_len_B = 0;
            while (i < num_tries && res_data[i] + res_solver[i] < gpu_mem_B) {
                data_size_B = res_data[i];
                solv_size_B = res_solver[i];
                mem_usage_B = data_size_B + solv_size_B;
                // max_chunk_len_B = res_chunk[i];
                max_num_pt_per_chunk = res_pt[i];
                max_num_nz_per_chunk = res_nz[i];
                i++;
            }

            // gettimeofday(&t2, NULL);
            // double t_chunk = double(t2.tv_usec-t1.tv_usec)/1000.0 + double(t2.tv_sec-t1.tv_sec)*1000.0;
            // std::cout << "t_chunk = " << t_chunk << std::endl;

            // did we find a working solution
            if (mem_usage_B == gpu_mem_B) {
                throw std::runtime_error("No valid chunking configuration found.");
            }

            // std::cout << "Selected chunk size (MB): " << max_chunk_len_B/1024.0/1024.0 << std::endl;
        }

        // std::cout << "Data size (MB):           " << data_size_B/1024.0/1024.0 << std::endl;
        // std::cout << "Solver size (MB):         " << solv_size_B/1024.0/1024.0 << std::endl;
        // std::cout << "Memory Usage (MB):        " << mem_usage_B/1024.0/1024.0 << std::endl;
        // std::cout << "Gpu Memory Total (MB):    " << gpu_mem_B/1024.0/1024.0   << std::endl;
    }

    void generate_rng(uint32_t nxt_chunk)
    {

        // genererate seeds for rng
        for (uint32_t thd = 0; thd < num_cpu_threads_; thd++) {
            xorseeds_[thd] = rng();
        }

        // multi-threaded rng
        omp_set_num_threads(num_cpu_threads_);
        OMP::parallel_for<int32_t>(0, num_cpu_threads_, [this, &nxt_chunk](const int32_t& i) {
            size_t   chunk_len = ceil(double(chunks_[nxt_chunk].size()) / double(num_cpu_threads_));
            size_t   pt_start  = i * chunk_len;
            size_t   pt_end    = std::min(chunks_[nxt_chunk].size(), pt_start + chunk_len);
            uint32_t xorvar    = xorseeds_[i];
            for (uint32_t pt = pt_start; pt < pt_end; pt++) {
                keygen_[pt] = xorvar;
                xorvar ^= xorvar << 13;
                xorvar ^= xorvar >> 17;
                xorvar ^= xorvar << 5;
            }
        });
    }

    uint32_t       num_threads_;
    uint32_t       device_id_;
    cudaDeviceProp device_prop_;

#ifdef WITH_NUMA
    int numa_node_;
#endif

    double eps_;

    std::vector<dim3> grids_;
    dim3              grid_transform;
    dim3              grid_transform_mlen;

    double* dev_model_;
    double* dev_model_save_;
    double* dev_shared_cached_;
    double* dev_shared_;
    double* dev_c1_;
    double* dev_c2_;
    double* dev_local_cost_;
    double* dev_diff_;
    double* dev_rdiff_;
    double* dev_max_rdiff_;
    double* dev_bias_;
    double* dev_bias_diff_;
    double* dev_bias_rdiff_;

    std::vector<std::vector<uint32_t>> chunks_;
    std::vector<uint64_t>              chunks_start_;
    std::vector<uint64_t>              chunks_len_;

    cudaStream_t stream1_;
    cudaStream_t stream2_;

    uint8_t* gpuMemory;

    uint32_t*              keygen_;
    uint32_t*              dev_keygen_;
    uint32_t*              dev_keygen_out_;
    uint32_t*              dev_perm_out_;
    std::vector<uint32_t*> dev_perms_;
    uint8_t*               dev_tmp_;
    uint8_t*               dev_tmp_diff_;

    size_t tmp_storage_size_B_;
    size_t tmp_storage_size_diff_B_;

    std::mt19937 rng;

    std::vector<uint32_t> xorseeds_;

    uint32_t num_cpu_threads_;

    bool   pin_;
    size_t chunking_step_B_;

    std::vector<bool> stop_;
};

}

#endif
