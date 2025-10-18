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
 *                Kubilay Atasu
 *                Andreea Anghel
 *                Milos Stanisavljevic
 *
 * End Copyright
 ********************************************************************/

#ifndef GLM_DATASET
#define GLM_DATASET

#include <tuple>
#include <vector>
#include <stdexcept>
#include <iostream>
#include <algorithm>
#include <cstring>

#ifdef WITH_VS
#define NOMINMAX
#include "intrin.h"
#define PACK(__DECLARATION__) __pragma(pack(push, 1))(__DECLARATION__) __pragma(pack(pop))
#define PREFETCH              _m_prefetch
#include "windows.h"
#include "synchapi.h"
#define INIT_BARRIER(PNT, VAL) (!InitializeSynchronizationBarrier((PNT), (VAL), -1))
#define WAIT_BARRIER(PNT)      (EnterSynchronizationBarrier((PNT), SYNCHRONIZATION_BARRIER_FLAGS_BLOCK_ONLY))
#define BARRIER                SYNCHRONIZATION_BARRIER
#define COLPS(N)
#else
#define PACK(__Declaration__) __Declaration__ __attribute__((__packed__))
#define PREFETCH              __builtin_prefetch
#include <pthread.h>
#ifdef WITH_MAC
#include "pthread_barrier.h"
#endif
#ifdef WITH_ZOS /* dummy values */
#define INIT_BARRIER(PNT, VAL) ((int)0)
#define WAIT_BARRIER(PNT)      ((void)0)
#define BARRIER                int
#define COLPS(N)               ((void)0)
#else
#define INIT_BARRIER(PNT, VAL) pthread_barrier_init(PNT, NULL, VAL)
#define WAIT_BARRIER(PNT)      pthread_barrier_wait(PNT)
#define BARRIER                pthread_barrier_t
#define COLPS(N)               collapse(N)
#endif
#endif

#ifdef WITH_CUDA
#include <cuda_runtime.h>
#endif

#ifdef WITH_NUMA
#include "NumaUtils.hpp"
#ifdef WITH_CUDA
#include "Checking.hpp"
#endif
#endif

namespace glm {

class Dataset {

public:
    Dataset(bool transpose, uint32_t num_ex, uint32_t num_ft, uint32_t this_num_pt, uint32_t num_partitions,
            uint32_t partition_id, uint32_t this_pt_offset, uint64_t num_nz, uint32_t num_pos, uint32_t num_neg)
    {
        transpose_      = transpose;
        num_ex_         = num_ex;
        num_ft_         = num_ft;
        this_num_pt_    = this_num_pt;
        num_partitions_ = num_partitions;
        partition_id_   = partition_id;
        this_pt_offset_ = this_pt_offset;
        num_nz_         = num_nz;
        num_labs_       = transpose ? num_ex : this_num_pt;
        num_pos_        = num_pos;
        num_neg_        = num_neg;
    }

    // virtual dtor
    virtual ~Dataset()
    {
#ifdef WITH_NUMA
        try {
            unpin_numa_mem();
            numa_free_allocated_mem(numa_allocated_ptrs_);
        } catch (const std::exception& e) {
            std::cerr << "Exception in ~Dataset: " << e.what() << std::endl;
        } catch (...) {
            std::cerr << "An unknown exception in ~Dataset" << std::endl;
        }
#endif
    };

    void try_chunk(size_t max_chunk_len_B, uint32_t& max_num_pt_per_chunk, size_t& max_num_nz_per_chunk)
    {

        // current chunk length in bytes
        size_t chunk_len_B = 0;

        // pt index
        uint32_t pt = 0;

        // number of pts per chunk
        uint32_t num_pt_per_chunk = 0;

        // number of nz per chunk
        size_t num_nz_per_chunk = 0;

        // maximum number of pt per chunk
        max_num_pt_per_chunk = 0;

        // maximum number of nz per chunk
        max_num_nz_per_chunk = 0;

        // iterate through pts
        while (pt < this_num_pt_) {
            // length of this pt in nz
            size_t this_len = get_pt_len(pt);
            // length of this pt in bytes
            size_t this_len_B = get_pt_len_B(pt);
            // does the pt fit in the current chunk?
            if (chunk_len_B + this_len_B < max_chunk_len_B) {
                // add to chunk
                num_pt_per_chunk++;
                num_nz_per_chunk += this_len;
                chunk_len_B += this_len_B;
            } else {
                // take max
                max_num_nz_per_chunk = std::max(max_num_nz_per_chunk, num_nz_per_chunk);
                max_num_pt_per_chunk = std::max(max_num_pt_per_chunk, num_pt_per_chunk);
                // start new chunk
                num_pt_per_chunk = 1;
                num_nz_per_chunk = this_len;
                chunk_len_B      = this_len_B;
            }
            pt++;
        }
        // finish up
        max_num_nz_per_chunk = std::max(max_num_nz_per_chunk, num_nz_per_chunk);
        max_num_pt_per_chunk = std::max(max_num_pt_per_chunk, num_pt_per_chunk);
    }

    void make_chunks(size_t max_chunk_len, std::vector<std::vector<uint32_t>>& chunks,
                     std::vector<uint64_t>& chunks_start, std::vector<uint64_t>& chunks_len)
    {

        // pt index
        uint32_t pt = 0;

        // nz index
        uint64_t pos = 0;

        // length of current chunk (in units of nz)
        uint64_t chunk_len = 0;

        // pt indices of current chunk
        std::vector<uint32_t> this_chunk;

        // initiaize
        chunks.resize(0);
        chunks_start.resize(0);
        chunks_len.resize(0);

        // first chunk has offset 0
        chunks_start.push_back(0);

        // iterate through pts
        while (pt < this_num_pt_) {

            // get the length of this example (in nz)
            uint64_t this_len = get_pt_len(pt);

            // does the pt fit in the current chunk?
            if (chunk_len + this_len <= max_chunk_len) {
                // add example to chunk
                this_chunk.push_back(pt);
                chunk_len += this_len;
            } else {
                // add the new chunk
                chunks.push_back(std::move(this_chunk));
                chunks_len.push_back(chunk_len);
                // start a new one
                chunks_start.push_back(pos);
                this_chunk.resize(0);
                this_chunk.push_back(pt);
                chunk_len = this_len;
            }

            pt++;
            pos += this_len;
        }
        // finish up
        chunks.push_back(this_chunk);
        chunks_len.push_back(chunk_len);
    }

#ifdef WITH_NUMA
    void pin_numa_mem()
    {
        for (auto ptr : numa_allocated_ptrs_) {
            void*  p;
            size_t size;
            std::tie(p, size) = ptr;
#ifdef WITH_CUDA
            cuda_safe(cudaHostRegister(p, size, cudaHostRegisterMapped),
                      "[Dataset::pin_memory] Could not pin host memory");
#endif
        }
    }
#endif

#ifdef WITH_NUMA
    void unpin_numa_mem()
    {
        for (auto ptr : numa_allocated_ptrs_) {
            void*  p;
            size_t size;
            std::tie(p, size) = ptr;
#ifdef WITH_CUDA
            cuda_safe(cudaHostUnregister(p), "[Dataset::unpin_memory] Could not unpin host memory");
#endif
        }
    }
#endif

    // Get the total size required to store the dataset (in bytes)
    virtual size_t get_total_size_B() = 0;

    // Get the total size required to store the dataset (in bytes)
    // assuming double-buffering where the maximum number of
    // nz per chunk is given by max_num_nz_per_chunk
    virtual size_t get_chunked_size_B(size_t max_num_nz_per_chunk) = 0;

    bool     get_transpose() { return transpose_; }
    uint32_t get_num_ex() { return num_ex_; }
    uint32_t get_num_ft() { return num_ft_; }
    uint32_t get_this_num_pt() { return this_num_pt_; }
    uint32_t get_num_partitions() { return num_partitions_; }
    uint32_t get_partition_id() { return partition_id_; }
    uint64_t get_num_nz() { return num_nz_; }
    uint32_t get_this_pt_offset() { return this_pt_offset_; }
    uint32_t get_num_pos() { return num_pos_; }
    uint32_t get_num_neg() { return num_neg_; }
    uint32_t get_num_labs() { return num_labs_; }
    void     set_num_pos(uint32_t num_pos) { num_pos_ = num_pos; }
    void     set_num_neg(uint32_t num_neg) { num_neg_ = num_neg; }

    // restore labels to original
    virtual void restore_labs() = 0;

#ifdef WITH_NUMA
    // try to map dataset to desired numa node
    virtual void set_numa_affinity(int numa_node) = 0;
#endif

    // get labels
    virtual float* get_labs() = 0;

    // by default data will be coming from host,
    // Until we have specific support for any dataset
    // to get the gpu_matrix pointer from gpu
    virtual bool is_data_on_gpu() { return false; }

    // set labels
    virtual void set_labs(float label_val) = 0;

protected:
    bool     transpose_;
    uint32_t num_ex_;
    uint32_t num_ft_;
    uint32_t this_num_pt_;
    uint32_t num_partitions_;
    uint32_t partition_id_;
    uint32_t this_pt_offset_;
    uint64_t num_nz_;
    uint32_t num_labs_;
    uint32_t num_pos_;
    uint32_t num_neg_;

#ifdef WITH_NUMA
    std::vector<std::tuple<void*, size_t>> numa_allocated_ptrs_;
#endif

    std::vector<std::tuple<uint32_t, uint32_t, uint64_t>> partition_pt(uint32_t targ_n_part)
    {

        std::vector<std::tuple<uint32_t, uint32_t, uint64_t>> out;

        uint32_t n_part = targ_n_part;
        bool     valid  = false;
        while (!valid && n_part > 0) {

            uint64_t cap_size = num_nz_ / static_cast<uint64_t>(n_part);

            out.resize(0);
            valid           = true;
            uint32_t pt_pos = 0;
            for (uint32_t p = 0; p < n_part; p++) {
                uint64_t cur_size = 0;
                uint32_t pt_start = pt_pos;
                if (p == (n_part - 1)) {
                    while (pt_pos < this_num_pt_) {
                        cur_size += get_pt_len(pt_pos);
                        pt_pos++;
                    }
                } else {
                    while (cur_size < cap_size && pt_pos < this_num_pt_) {
                        cur_size += get_pt_len(pt_pos);
                        pt_pos++;
                    }
                }
                uint32_t pt_end = pt_pos;
                out.push_back(std::make_tuple(pt_start, pt_end, cur_size));
                valid &= pt_end > pt_start;
            }

            if (!valid) {
                n_part--;
            }
        }

        if (n_part == 0) {
            throw std::runtime_error("Could not find valid partitioning");
        }

        if (n_part < targ_n_part) {
            std::cout << "[Warn] Not enough coordinates to form " << targ_n_part << " partitions; Using " << n_part
                      << " instead." << std::endl;
        }

        return out;
    }

private:
    // Get the length of a given pt (in units of nz)
    virtual uint32_t get_pt_len(uint32_t pt) = 0;

    // Get the length of a given pt (in units of bytes)
    virtual uint32_t get_pt_len_B(uint32_t pt) = 0;
};

}

#endif
