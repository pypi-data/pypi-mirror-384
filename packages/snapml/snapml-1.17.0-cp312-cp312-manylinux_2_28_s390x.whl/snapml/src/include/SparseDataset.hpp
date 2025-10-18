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
 *                Andreea Anghel
 *                Milos Stanisavljevic
 *
 * End Copyright
 ********************************************************************/

#ifndef GLM_SPARSE_DATASET
#define GLM_SPARSE_DATASET

#include <cstdint>
#include <cassert>
#include <limits>
#include "Traits.hpp"
#include <vector>
#include <cstdio>
#include <iostream>
#include "Dataset.hpp"
#include <stdexcept>
#include <memory>
#include <thread>

#ifdef WITH_CUDA
#include "Checking.hpp"
#endif

#include "OMP.hpp"

namespace glm {

// New Sparse Dataset
class SparseDataset : public Dataset {

public:
    struct data_t {
        float*    labs;
        uint64_t* start;
        uint32_t* ind;
        float*    val;
        uint64_t  offset;
        float*    labs_orig;
    };

    // ctor (does not transfer ownership)
    SparseDataset(bool transpose, uint32_t num_ex, uint32_t num_ft, uint32_t this_num_pt, uint32_t num_partitions,
                  uint32_t partition_id, uint32_t this_pt_offset, uint64_t num_nz, uint32_t num_pos, uint32_t num_neg,
                  float* labs, uint64_t* start, uint32_t* ind, float* val, uint64_t offset = 0)
        : Dataset(transpose, num_ex, num_ft, this_num_pt, num_partitions, partition_id, this_pt_offset, num_nz, num_pos,
                  num_neg)
    {

        // set pointers in matrix
        data_.labs      = labs;
        data_.start     = start;
        data_.ind       = ind;
        data_.val       = val;
        data_.offset    = offset;
        data_.labs_orig = nullptr;
    }

    // ctor (does transfer ownership)
    SparseDataset(bool transpose, uint32_t num_ex, uint32_t num_ft, uint32_t this_num_pt, uint32_t num_partitions,
                  uint32_t partition_id, uint32_t this_pt_offset, uint64_t num_nz, uint32_t num_pos, uint32_t num_neg,
                  std::vector<float>& labs, std::vector<uint64_t>& start, std::vector<uint32_t>& ind,
                  std::vector<float>& val)
        : Dataset(transpose, num_ex, num_ft, this_num_pt, num_partitions, partition_id, this_pt_offset, num_nz, num_pos,
                  num_neg)
    {

        labs_  = std::move(labs);
        start_ = std::move(start);
        ind_   = std::move(ind);
        val_   = std::move(val);

        // set pointers in matrix
        data_.labs      = labs_.data();
        data_.start     = start_.data();
        data_.ind       = ind_.data();
        data_.val       = val_.data();
        data_.offset    = 0;
        data_.labs_orig = nullptr;
    }

    // copy ctor
    SparseDataset(const SparseDataset& src)
        : Dataset(src.transpose_, src.num_ex_, src.num_ft_, src.this_num_pt_, src.num_partitions_, src.partition_id_,
                  src.this_pt_offset_, src.num_nz_, src.num_pos_, src.num_neg_)
    {

        data_.labs = (float*)malloc(num_labs_ * sizeof(float));
        memcpy(data_.labs, src.data_.labs, num_labs_ * sizeof(float));

        data_.start = (uint64_t*)calloc((1 + src.this_num_pt_), sizeof(uint64_t));
        memcpy(data_.start, src.data_.start, (1 + src.this_num_pt_) * sizeof(uint64_t));

        data_.ind = (uint32_t*)malloc(num_nz_ * sizeof(uint32_t));
        memcpy(data_.ind, src.data_.ind, num_nz_ * sizeof(uint32_t));

        data_.val = (float*)malloc(num_nz_ * sizeof(float));
        memcpy(data_.val, src.data_.val, num_nz_ * sizeof(float));

        data_.offset    = src.data_.offset;
        data_.labs_orig = nullptr;

        cur_chunk_      = 0;
        nxt_chunk_      = 0;
        num_chunks_     = 0;
        dev_data_ind_1_ = nullptr;
        dev_data_ind_2_ = nullptr;
        dev_data_val_1_ = nullptr;
        dev_data_val_2_ = nullptr;

        labs_.resize(0);
        start_.resize(0);
        ind_.resize(0);
        val_.resize(0);

        chunk_start_.resize(0);
        chunk_len_.resize(0);
    }

    // pin memory
    void pin_memory()
    {
#ifdef WITH_CUDA
        cuda_safe(cudaHostRegister(data_.labs, num_labs_ * sizeof(float), cudaHostRegisterMapped),
                  "[SparseDataset::pin_memory] Could not pin host memory");
        cuda_safe(cudaHostRegister(data_.start, (1 + this_num_pt_) * sizeof(uint64_t), cudaHostRegisterMapped),
                  "[SparseDataset::pin_memory] Could not pin host memory");
        cuda_safe(cudaHostRegister(data_.ind, num_nz_ * sizeof(uint32_t), cudaHostRegisterMapped),
                  "[SparseDataset::pin_memory] Could not pin host memory");
        cuda_safe(cudaHostRegister(data_.val, num_nz_ * sizeof(float), cudaHostRegisterMapped),
                  "[SparseDataset::pin_memory] Could not pin host memory");
#endif
    }

    // unpin memory
    void unpin_memory()
    {
#ifdef WITH_CUDA
        cuda_safe(cudaHostUnregister(data_.labs), "[SparseDataset::pin_memory] Could not unpin host memory");
        cuda_safe(cudaHostUnregister(data_.start), "[SparseDataset::pin_memory] Could not unpin host memory");
        cuda_safe(cudaHostUnregister(data_.ind), "[SparseDataset::pin_memory] Could not unpin host memory");
        cuda_safe(cudaHostUnregister(data_.val), "[SparseDataset::pin_memory] Could not unpin host memory");
#endif
    }

    // dtor
    ~SparseDataset()
    {
        free(data_.labs_orig);
        // std::cout << "Destroying SparseDataset" << std::endl;
    }

    // get data
    data_t get_data() { return data_; }

    // get dev_data
    data_t get_dev_data() { return dev_data_; }

    // get current chunk
    uint32_t get_cur_chunk() { return cur_chunk_; }

    // get next chunk
    uint32_t get_nxt_chunk() { return nxt_chunk_; }

    size_t get_total_size_B()
    {
        size_t total_size_B = 0;
        total_size_B += num_nz_ * sizeof(uint32_t);
        total_size_B += num_nz_ * sizeof(float);
        total_size_B += num_labs_ * sizeof(float);
        total_size_B += (1 + this_num_pt_) * sizeof(uint64_t);
        return total_size_B;
    }

    // get total size of the dataset assuming double buffer of given length
    size_t get_chunked_size_B(size_t max_num_nz_per_chunk)
    {
        size_t total_size_B = 0;
        total_size_B += max_num_nz_per_chunk * sizeof(uint32_t);
        total_size_B += max_num_nz_per_chunk * sizeof(uint32_t);
        total_size_B += max_num_nz_per_chunk * sizeof(float);
        total_size_B += max_num_nz_per_chunk * sizeof(float);
        total_size_B += num_labs_ * sizeof(float);
        total_size_B += (1 + this_num_pt_) * sizeof(uint64_t);
        return total_size_B;
    }

    // get the length of a given examples/feature
    __host__ __device__ static uint32_t get_pt_len(data_t x, uint32_t this_pt)
    {
        return x.start[1 + this_pt] - x.start[this_pt];
    }

    // lookup (feature,value) from row
    __host__ __device__ static void lookup(data_t x, uint32_t this_pt, uint32_t k, uint32_t this_len,
                                           uint32_t& this_ind, float& this_val)
    {
        uint64_t pos = x.start[this_pt] + uint64_t(k) - x.offset;
        this_ind     = x.ind[pos];
        this_val     = x.val[pos];
    }

    // lookup (feature, index from data matrix)
    // TODO: binary search
    __host__ __device__ static float lookup2D(data_t data, uint32_t this_ex, uint32_t attribute)
    {

        uint32_t this_len = get_pt_len(data, this_ex);

        float    val = 0.0;
        uint32_t ind;

        for (uint32_t k = 0; k < this_len; k++) {
            lookup(data, this_ex, k, this_len, ind, val);
            if (ind == attribute) {
                break;
            }
            if (ind > attribute) {
                val = 0.0;
                break;
            }
        }

        return val;
    }

    // lookup example pointer
    __host__ __device__ static uint64_t get_ex_pt(data_t x, uint32_t this_ex)
    {
        return uint64_t(this_ex) * uint64_t(get_pt_len(x, this_ex)) - x.offset;
    }

    // lookup with example pointer
    __host__ __device__ static float lookup_w_pos(data_t x, uint32_t this_ex, uint64_t this_pos, uint32_t attribute)
    {
        uint32_t this_len = get_pt_len(x, this_ex);

        float    val = 0.0;
        uint32_t ind;
        for (uint32_t k = 0; k < this_len; k++) {
            ind = x.ind[this_pos + k];
            if (ind == attribute) {
                val = x.val[this_pos + k];
                break;
            }
            if (ind > attribute) {
                break;
            }
        }
        return val;
    }

    // copy data onto GPU
#ifdef WITH_CUDA
    void gpu_init(size_t& pos, uint8_t* const gpuMemory, const std::vector<uint64_t>& chunk_len,
                  const std::vector<uint64_t>& chunk_start)
    {

        // validate input
        assert(chunk_len.size() == chunk_start.size());

        // how many chunks are there
        num_chunks_ = chunk_len.size();

        // length of chunks (in nz)
        chunk_len_ = chunk_len;

        // offsets of chunks (in nz)
        chunk_start_ = chunk_start;

        // find max chunk term (in units of nz)
        uint64_t max_chunk_len = 0;
        for (uint32_t i = 0; i < chunk_len_.size(); i++) {
            max_chunk_len = std::max(max_chunk_len, chunk_len_[i]);
        }

        dev_data_.start = reinterpret_cast<uint64_t*>(&gpuMemory[pos]);
        pos += (1 + this_num_pt_) * sizeof(uint64_t);
        dev_data_.labs = reinterpret_cast<float*>(&gpuMemory[pos]);
        pos += num_labs_ * sizeof(float);

        if (this->num_chunks_ == 1) {
            dev_data_ind_1_ = reinterpret_cast<uint32_t*>(&gpuMemory[pos]);
            pos += max_chunk_len * sizeof(uint32_t);
            dev_data_val_1_ = reinterpret_cast<float*>(&gpuMemory[pos]);
            pos += max_chunk_len * sizeof(float);
        } else {
            dev_data_ind_1_ = reinterpret_cast<uint32_t*>(&gpuMemory[pos]);
            pos += max_chunk_len * sizeof(uint32_t);
            dev_data_ind_2_ = reinterpret_cast<uint32_t*>(&gpuMemory[pos]);
            pos += max_chunk_len * sizeof(uint32_t);
            dev_data_val_1_ = reinterpret_cast<float*>(&gpuMemory[pos]);
            pos += max_chunk_len * sizeof(float);
            dev_data_val_2_ = reinterpret_cast<float*>(&gpuMemory[pos]);
            pos += max_chunk_len * sizeof(float);
        }

        // std::cout << "this->num_labs_ = " << this->num_labs_ << std::endl;

        // copy data on
        cuda_safe(
            cudaMemcpy(dev_data_.start, data_.start, (1 + this_num_pt_) * sizeof(uint64_t), cudaMemcpyHostToDevice),
            "[SparseDataset::gpu_init] Could not copy start onto device");
        cuda_safe(cudaMemcpy(dev_data_.labs, data_.labs, num_labs_ * sizeof(float), cudaMemcpyHostToDevice),
                  "[SparseDataset::gpu_init] Could not copy labs onto device");

        // set offset
        dev_data_.offset = data_.offset + chunk_start[0];

        // pointer to initialize chunk
        dev_data_.ind = dev_data_ind_1_;
        dev_data_.val = dev_data_val_1_;

        // copy in first chunk
        cuda_safe(cudaMemcpy(dev_data_ind_1_, data_.ind, chunk_len_[0] * sizeof(uint32_t), cudaMemcpyHostToDevice),
                  "[SparseDataset::gpu_init] Could not copy ind onto device");
        cuda_safe(cudaMemcpy(dev_data_val_1_, data_.val, chunk_len_[0] * sizeof(float), cudaMemcpyHostToDevice),
                  "[SparseDataset::gpu_init] Could not copy val onto device");

        cur_chunk_ = 0;
        nxt_chunk_ = 1 % num_chunks_;
    }

    void copy_next_chunk(cudaStream_t stream)
    {

        if (num_chunks_ > 1) {

            uint64_t chunk_start = chunk_start_[nxt_chunk_];
            uint64_t chunk_len   = chunk_len_[nxt_chunk_];

            if (dev_data_.ind == dev_data_ind_1_) {
                cuda_safe(cudaMemcpyAsync(dev_data_ind_2_, &data_.ind[chunk_start], chunk_len * sizeof(uint32_t),
                                          cudaMemcpyHostToDevice, stream),
                          "[SparseDataset::copy_next_chunk] Could not copy ind onto device");
                cuda_safe(cudaMemcpyAsync(dev_data_val_2_, &data_.val[chunk_start], chunk_len * sizeof(float),
                                          cudaMemcpyHostToDevice, stream),
                          "[SparseDataset::copy_next_chunk] Could not copy val onto device");
            } else {
                cuda_safe(cudaMemcpyAsync(dev_data_ind_1_, &data_.ind[chunk_start], chunk_len * sizeof(uint32_t),
                                          cudaMemcpyHostToDevice, stream),
                          "[SparseDataset::copy_next_chunk] Could not copy ind onto device");
                cuda_safe(cudaMemcpyAsync(dev_data_val_1_, &data_.val[chunk_start], chunk_len * sizeof(float),
                                          cudaMemcpyHostToDevice, stream),
                          "[SparseDataset::copy_next_chunk] Could not copy val onto device");
            }
        }
    }

    // rotate chunks
    void rotate_chunks()
    {

        if (num_chunks_ > 1) {

            if (dev_data_.ind == dev_data_ind_1_) {
                dev_data_.ind = dev_data_ind_2_;
                dev_data_.val = dev_data_val_2_;
            } else {
                dev_data_.ind = dev_data_ind_1_;
                dev_data_.val = dev_data_val_1_;
            }

            cur_chunk_ = (cur_chunk_ + 1) % num_chunks_;
            nxt_chunk_ = (nxt_chunk_ + 1) % num_chunks_;

            dev_data_.offset = data_.offset + chunk_start_[cur_chunk_];
        }
    }
#endif

#ifdef WITH_NUMA
    void set_numa_affinity(const int numa_node)
    {
        if (numa_node < 0)
            return;
#if 0
        size_t size = num_labs_ * sizeof(*data_.labs);
        void *new_ptr = numa_alloc_cpy(data_.labs, size, numa_node);
        if (new_ptr != (void *) data_.labs) {
            data_.labs = reinterpret_cast<float *>(new_ptr);
            numa_allocated_ptrs_.push_back(std::make_tuple(new_ptr, size));
        }
        size = (this_num_pt_ + 1) * sizeof(*data_.start);
        new_ptr = numa_alloc_cpy(data_.start, size, numa_node);
        if (new_ptr != (void *) data_.start) {
            data_.start = reinterpret_cast<uint64_t *>(new_ptr);
            numa_allocated_ptrs_.push_back(std::make_tuple(new_ptr, size));
        }
#endif
        size_t size    = (num_nz_) * sizeof(*data_.ind);
        void*  new_ptr = numa_alloc_cpy(data_.ind, size, numa_node);
        if (new_ptr != (void*)data_.ind) {
            data_.ind = reinterpret_cast<uint32_t*>(new_ptr);
            numa_allocated_ptrs_.push_back(std::make_tuple(new_ptr, size));
        }
        size    = (num_nz_) * sizeof(*data_.val);
        new_ptr = numa_alloc_cpy(data_.val, size, numa_node);
        if (new_ptr != (void*)data_.val) {
            data_.val = reinterpret_cast<float*>(new_ptr);
            numa_allocated_ptrs_.push_back(std::make_tuple(new_ptr, size));
        }
    }
#endif

    std::vector<std::shared_ptr<SparseDataset>> partition(uint32_t targ_n_part)
    {

        std::vector<std::shared_ptr<SparseDataset>> out;

        // partition the local data points (implemented in parent class)
        std::vector<std::tuple<uint32_t, uint32_t, uint64_t>> part_pt = partition_pt(targ_n_part);
        uint32_t                                              n_part  = part_pt.size();

        uint64_t nz_offset = 0;
        for (uint32_t i = 0; i < n_part; i++) {

            uint32_t local_num_pt    = std::get<1>(part_pt[i]) - std::get<0>(part_pt[i]);
            uint32_t local_id        = partition_id_ * n_part + i;
            uint32_t local_pt_offset = this_pt_offset_ + std::get<0>(part_pt[i]);
            uint64_t local_num_nz    = std::get<2>(part_pt[i]);
            uint64_t local_nz_offset = nz_offset;

            float*    local_labs  = transpose_ ? &data_.labs[0] : &data_.labs[std::get<0>(part_pt[i])];
            uint64_t* local_start = &data_.start[std::get<0>(part_pt[i])];
            uint32_t* local_ind   = &data_.ind[nz_offset];
            float*    local_val   = &data_.val[nz_offset];

            // create the partition
            out.push_back(std::make_shared<SparseDataset>(
                transpose_, num_ex_, num_ft_, local_num_pt, num_partitions_ * n_part, local_id, local_pt_offset,
                local_num_nz, num_pos_, num_neg_, local_labs, local_start, local_ind, local_val, local_nz_offset));

            nz_offset += local_num_nz;
        }

        // check
        assert(nz_offset == num_nz_);

        return out;
    }

    void change_labs(float* x)
    {
        for (uint32_t i = 0; i < num_labs_; i++) {
            data_.labs[i] = x[i];
        }
    }

    // used for multi-class classification to set labels to specific class
    void set_labs(float label_val)
    {
        if (data_.labs_orig == nullptr) {
            uint64_t size   = sizeof(data_.labs[0]) * num_labs_;
            data_.labs_orig = (float*)malloc(size);
            memcpy(data_.labs_orig, data_.labs, size);
        }

        uint32_t pos = 0;
        OMP::parallel_for_reduction<int64_t>(0, num_labs_, pos, [this, &label_val](int64_t index, uint32_t& pos) {
            if (data_.labs_orig[index] == label_val) {
                data_.labs[index] = 1;
                pos++;
            } else {
                data_.labs[index] = -1;
            }
        });

        num_pos_ = pos;
        num_neg_ = num_labs_ - pos;
    }

    // used for multi-class classification to restore original labels after training
    void restore_labs()
    {
        if (data_.labs_orig != nullptr) {
            uint64_t size = sizeof(data_.labs[0]) * num_labs_;
            memcpy(data_.labs, data_.labs_orig, size);
        }
    }

    float* get_labs() { return data_.labs; }

private:
    data_t data_;
    data_t dev_data_;

    uint32_t  cur_chunk_;
    uint32_t  nxt_chunk_;
    uint32_t  num_chunks_;
    uint32_t* dev_data_ind_1_;
    uint32_t* dev_data_ind_2_;
    float*    dev_data_val_1_;
    float*    dev_data_val_2_;

    // these contain the big data if the data is constructed with std::move
    std::vector<float>    labs_;
    std::vector<uint64_t> start_;
    std::vector<uint32_t> ind_;
    std::vector<float>    val_;

    std::vector<uint64_t> chunk_start_;
    std::vector<uint64_t> chunk_len_;

    // This function is needed to expose the static function to parent class
    uint32_t get_pt_len(uint32_t pt) { return get_pt_len(data_, pt); }

    // This function is needed to expose static function to parent class
    uint32_t get_pt_len_B(uint32_t pt) { return get_pt_len(data_, pt) * (sizeof(float) + sizeof(uint32_t)); }
};

}

#endif
