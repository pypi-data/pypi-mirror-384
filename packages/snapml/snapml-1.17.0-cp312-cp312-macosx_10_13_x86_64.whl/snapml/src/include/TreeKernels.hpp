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
 * Authors      : Thomas Parnell
 *                Nikolas Ioannou
 *
 * End Copyright
 ********************************************************************/

#ifndef TREE_KERNELS
#define TREE_KERNELS

#include "GPUUtils.hpp"

namespace tree {

// set training predictions
__global__ void dev_update_train_preds(const uint32_t len, const ex_lab_t* const dev_nex, const double val,
                                       double* const dev_preds)
{

    // index into active examples
    const uint32_t i = blockIdx.x * blockDim.x + threadIdx.x;

    if (i < len) {

        const ex_lab_t ex = dev_nex[i];

        dev_preds[ex.idx] = val;
    }
}

__global__ void dev_init_nex(const uint32_t len, const double* const labs, const float* const sample_weight,
                             const bool is_regression, ex_lab_t* const dev_nex)
{

    // index into active examples
    const uint32_t i = blockIdx.x * blockDim.x + threadIdx.x;

    if (i < len) {
        dev_nex[i].idx           = i;
        dev_nex[i].lab           = is_regression ? labs[i] : (0 < labs[i] ? 1 : 0);
        dev_nex[i].sample_weight = nullptr == sample_weight ? 1.0 : sample_weight[i];
    }
}

__global__ void dev_init_preds(const uint32_t len, const double val, double dev_preds[])
{
    // index into active examples
    const uint32_t i = blockIdx.x * blockDim.x + threadIdx.x;

    if (i < len)
        dev_preds[i] = val;
}

__global__ void dev_init_nex_subsample(const uint32_t len, const uint32_t* const indices, const double* const labs,
                                       const float* const sample_weight, const bool is_regression,
                                       ex_lab_t* const dev_nex)
{

    // index into active examples
    const uint32_t i = blockIdx.x * blockDim.x + threadIdx.x;

    if (i < len) {
        const uint32_t idx       = indices[i];
        dev_nex[i].idx           = idx;
        dev_nex[i].lab           = is_regression ? labs[idx] : (0 < labs[idx] ? 1 : 0);
        dev_nex[i].sample_weight = nullptr == sample_weight ? 1.0 : sample_weight[idx];
    }
}

// split active examples
__global__ void dev_split(const uint32_t num_active_ex, const ex_lab_t* const dev_nex,
                          const uint8_t* const dev_ex_to_bin, const float* const dev_hist_val, const uint64_t num_ft,
                          const uint32_t best_ft, const float best_thd, uint8_t dev_go_left[])
{

    // index into active examples
    const uint32_t i = blockIdx.x * blockDim.x + threadIdx.x;

    if (i < num_active_ex) {

        // lookup into nex
        const ex_lab_t ex = dev_nex[i];

        // get bin_idx for this example
        const uint8_t bin_idx = dev_ex_to_bin[(uint64_t)ex.idx * num_ft + (uint64_t)best_ft];

        // split
        dev_go_left[i] = dev_hist_val[bin_idx] < best_thd;
    }
}

template <class N> __device__ void init_node_stats_from_bin(const typename N::hist_bin_t* const bin, N* const node);

template <>
__device__ void init_node_stats_from_bin<ClTreeNode>(const ClTreeNode::hist_bin_t* const bin, ClTreeNode* const node)
{
    node->set_num_pos(bin->num_pos);
    node->set_wnum_pos(bin->lab_sum);
    node->set_wnum_neg(bin->sample_weight - bin->lab_sum);
    node->set_num_neg(bin->weight - bin->num_pos);
}

template <>
__device__ void init_node_stats_from_bin<MultiClTreeNode>(const MultiClTreeNode::hist_bin_t* const bin,
                                                          MultiClTreeNode* const                   node)
{
}

template <>
__device__ void init_node_stats_from_bin<RegTreeNode>(const RegTreeNode::hist_bin_t* const bin, RegTreeNode* const node)
{
    node->set_num(bin->weight);
    node->set_wnum(bin->sample_weight);
    node->set_sum(bin->lab_sum);
}

template <class N>
__device__ void update_node_stats(const uint32_t weight, const double sample_weight, const double lab_sum,
                                  const uint32_t num_pos, N* const node);

template <>
__device__ void update_node_stats<ClTreeNode>(const uint32_t weight, const double sample_weight, const double lab_sum,
                                              const uint32_t num_pos, ClTreeNode* const node)
{
    node->set_num_pos_left(num_pos);
    node->set_wnum_pos_left(lab_sum);
    node->set_num_neg_left(weight - num_pos);
    node->set_wnum_neg_left(sample_weight - lab_sum);
}

template <>
__device__ void update_node_stats<RegTreeNode>(const uint32_t weight, const double sample_weight, const double lab_sum,
                                               const uint32_t num_pos, RegTreeNode* const node)
{
    node->set_num_left(weight);
    node->set_wnum_left(sample_weight);
    node->set_sum_left(lab_sum);
}

template <class N> __global__ void dev_node_init(const uint32_t dev_fts[], const N* const node_in, N dev_nodes[])
{
    const uint32_t ftp        = blockIdx.x;
    const uint32_t hist_nbins = blockDim.x;
    // feature processed by current thread
    const uint32_t bin_idx = threadIdx.x;
    const uint32_t ft      = dev_fts[ftp];
    N* const       my_node = &dev_nodes[ft * hist_nbins + bin_idx];
    N::init_node(my_node, node_in);
}

template <class N>
__global__ void dev_prep_best_split(const uint32_t dev_fts[], const typename N::hist_bin_t dev_hist[], N dev_nodes[])
{
    const uint32_t ftp        = blockIdx.x;
    const uint32_t hist_nbins = gridDim.y;
    // feature processed by current thread
    const uint32_t bin_idx = blockIdx.y;
    const uint32_t tid     = threadIdx.x;
    const uint32_t ft      = dev_fts[ftp];
    N* const       my_node = &dev_nodes[ft * hist_nbins + bin_idx];
    if (0 < bin_idx && tid < bin_idx) {
        // update from all previous bins, up-to bin_idx - 1
        const typename N::hist_bin_t& bin = dev_hist[ft * hist_nbins + tid];
        if (0 < bin.weight) {
            update_node_stats<N>(bin.weight, bin.sample_weight, bin.lab_sum, bin.num_pos, my_node);
        }
    }
}

template <class N>
__global__ void dev_compute_best_split3(const snapml::split_t split_criterion, const uint32_t min_samples_leaf,
                                        const double lambda, const uint32_t dev_fts[], const float dev_hist_val[],
                                        const typename N::hist_bin_t dev_hist[], N dev_nodes[])
{
    // bin_idx
    const uint32_t ftp        = blockIdx.x;
    const uint32_t hist_nbins = blockDim.x;
    // feature processed by current thread
    const uint32_t bin_idx = threadIdx.x;
    const uint32_t tid     = threadIdx.x;
    // do from 1 to hist_nbins
    if (bin_idx < hist_nbins) {
        const uint32_t                ft      = dev_fts[ftp];
        const float                   val     = dev_hist_val[ft * hist_nbins + bin_idx];
        const typename N::hist_bin_t& bin     = dev_hist[ft * hist_nbins + bin_idx];
        N* const                      my_node = &dev_nodes[ft * hist_nbins + bin_idx];
        if (0 < bin.weight) {
            N::update_best_hist(my_node, ft, val, min_samples_leaf, split_criterion, lambda);
            // assert(-1 != my_node->best_feature);
        }
        uint32_t n = hist_nbins, m = (hist_nbins + 1) / 2;
        // reduce across bins
        __syncthreads();
        while (0 < m) {
            if (tid < m && tid + m < n) {
                N::update_best(my_node, &dev_nodes[ft * hist_nbins + tid + m]);
            }
            __syncthreads();
            n = m;
            m = 1 < m ? (m + 1) / 2 : 0;
        }
        // if not even, add the last one, it wasn't reduced in the loop above
        if (0 == tid) {
            if (0 == tid && 1 < hist_nbins && 0 != ((hist_nbins)&1))
                N::update_best(my_node, &dev_nodes[ft * hist_nbins + hist_nbins - 1]);
        }
    }
}

template <class N>
__global__ void dev_compute_best_split(const uint32_t num_ft_effective, const uint32_t hist_nbins,
                                       const snapml::split_t split_criterion, const uint32_t min_samples_leaf,
                                       const double lambda, const uint32_t dev_fts[], const float dev_hist_val[],
                                       const typename N::hist_bin_t* const dev_hist, const N* const node_in,
                                       N* const dev_nodes)
{
    // bin_idx
    const uint32_t ftp = blockIdx.x;

    // feature processed by current thread
    const uint32_t bin_idx = blockDim.x * blockIdx.y + threadIdx.x;
    const uint32_t tid     = threadIdx.x;

    if (bin_idx < hist_nbins && ftp < num_ft_effective) {
        const uint32_t                ft      = dev_fts[ftp];
        const float                   val     = dev_hist_val[ft * hist_nbins + bin_idx];
        const typename N::hist_bin_t& bin     = dev_hist[ft * hist_nbins + bin_idx];
        N* const                      my_node = &dev_nodes[ft * hist_nbins + bin_idx];
        N::init_node(my_node, node_in);
        N::update_best_hist(my_node, ft, val, min_samples_leaf, split_criterion, lambda);
        N::post_update_best_hist(my_node, bin);

        uint32_t m = hist_nbins / 2;
        // reduce across bins
        __syncthreads();
        while (0 < m) {
            if (tid < m) {
                N::update_best(my_node, &dev_nodes[ft * hist_nbins + tid + m]);
            }
            __syncthreads();
            m /= 2;
        }
        // if not even, add the last one, it wasn't reduced in the loop above
        if (0 == tid && 1 < hist_nbins && 0 != (hist_nbins & 1))
            N::update_best(my_node, &dev_nodes[ft * hist_nbins + hist_nbins - 1]);
    }
}

template <class N>
__global__ void dev_compute_best_split2(const uint32_t num_ft_effective, const uint32_t hist_nbins,
                                        const snapml::split_t split_criterion, const uint32_t min_samples_leaf,
                                        const double lambda, const uint32_t dev_fts[], const float dev_hist_val[],
                                        const typename N::hist_bin_t dev_hist[], const N* const node_in, N dev_nodes[])
{
    const uint32_t ftp = blockIdx.x * blockDim.x + threadIdx.x;
    if (ftp < num_ft_effective) {
        // assert(threadIdx.x == ftp);
        const uint32_t ft      = dev_fts[ftp];
        N* const       my_node = &dev_nodes[ft];
        my_node->init_node(node_in);
        for (uint32_t bin_idx = 0; bin_idx < hist_nbins; ++bin_idx) {
            const typename N::hist_bin_t& bin = dev_hist[ft * hist_nbins + bin_idx];
            if (0 < bin.weight) {
                const float val = dev_hist_val[ft * hist_nbins + bin_idx];
                my_node->update_best_hist(ft, val, min_samples_leaf, split_criterion, lambda);
                my_node->post_update_best_hist(bin);
                // assert(0 == bin_idx || -1 != my_node->best_feature); //((TreeNode *) my_node)->get_best_feature());
            }
        }
    }
}

template <class N>
__global__ void dev_reduce_best_split(const uint32_t num_ft_effective, const uint32_t hist_nbins,
                                      const uint32_t dev_fts[], N dev_nodes[])
{
    // feature processed by current thread
    const uint32_t ftp = blockIdx.x * blockDim.x + threadIdx.x;
    const uint32_t tid = threadIdx.x;
    // assert(ftp < num_ft_effective && tid == ftp);
    // reduce across features
    const uint32_t ft      = dev_fts[ftp];
    N* const       my_node = &dev_nodes[ft];

    uint32_t n = num_ft_effective, m = (num_ft_effective + 1) / 2;
    __syncthreads();
    while (0 < m) {
        if (tid < m && tid + m < n) {
            my_node->update_best(&dev_nodes[dev_fts[ftp + m]]);
        }
        __syncthreads();
        n = m;
        m = 1 < m ? (m + 1) / 2 : 0;
    }
    // if not even, add the last one, it wasn't reduced in the loop above
    if (0 == tid && 1 < num_ft_effective && 0 != (num_ft_effective & 1))
        my_node->update_best(&dev_nodes[dev_fts[num_ft_effective - 1]]);
}

// recompute histogram bin on GPU
template <class N>
__global__ void dev_init_node_with_hist(const uint32_t hist_nbins, const typename N::hist_bin_t dev_hist[], N* node)
{

    const uint32_t bin_idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (bin_idx < hist_nbins) {
        const typename N::hist_bin_t& bin = dev_hist[bin_idx];
        init_node_stats_from_bin(&bin, node);
    }
}

// recompute histogram bin on GPU
template <class N>
__global__ void dev_recompute_hist_bin(const uint64_t num_ft, const uint64_t num_ft_effective,
                                       const uint32_t hist_nbins, const uint32_t dev_fts[], const ex_lab_t dev_nex[],
                                       const uint8_t dev_ex_to_bin[], typename N::hist_bin_t dev_hist[])
{

    // active example processed by thread
    const uint32_t i = blockIdx.x;

    // feature processed by current thread
    const uint32_t ftp = blockDim.x * blockIdx.y + threadIdx.x;

    if (ftp < num_ft_effective) {

        const uint32_t ex            = dev_nex[i].idx;
        const float    lab           = dev_nex[i].lab;
        const float    sample_weight = dev_nex[i].sample_weight;
        const float    tmp1          = sample_weight * lab;
        const uint32_t ft            = dev_fts[ftp];

        const uint8_t bin_idx = dev_ex_to_bin[(uint64_t)ex * num_ft + (uint64_t)ft];

        typename N::hist_bin_t& bin = dev_hist[ft * hist_nbins + bin_idx];

        copyData(&bin.weight, (uint32_t)1);
        copyData(&bin.sample_weight, (double)sample_weight);
        copyData(&bin.lab_sum, (double)tmp1);
        copyData(&bin.num_pos, (uint32_t)lab);
    }
}

template <class N>
__global__ void dev_recompute_hist_bin_sibling(const uint32_t num_ft_effective, const uint32_t hist_nbins,
                                               const uint32_t dev_fts[], typename N::hist_bin_t dev_hist_parent[],
                                               const typename N::hist_bin_t dev_hist_sibling[])
{

    // active bin idx processed by thread
    const uint32_t bin_idx = blockIdx.x;

    // feature processed by current thread
    const uint32_t ftp = blockDim.x * blockIdx.y + threadIdx.x;

    if (ftp < num_ft_effective) {

        const uint32_t ft = dev_fts[ftp];
        // hist_bin_t &parent = dev_hist_parent[ft*hist_nbins + bin_idx];
        const typename N::hist_bin_t& sibling = dev_hist_sibling[ft * hist_nbins + bin_idx];
        typename N::hist_bin_t&       output  = dev_hist_parent[ft * hist_nbins + bin_idx];
        // output.weight = parent.weight - sibling.weight;
        // output.sample_weight = parent.sample_weight - sibling.sample_weight;
        // output.lab_sum = parent.lab_sum - sibling.lab_sum;
        // output.num_pos = parent.num_pos - sibling.num_pos;
        // assert(sibling.weight <= output.weight);
        output.weight -= sibling.weight;
        // assert(sibling.sample_weight <= output.sample_weight);
        output.sample_weight -= sibling.sample_weight;
        // assert(sibling.lab_sum <= output.lab_sum);
        output.lab_sum -= sibling.lab_sum;
        // assert(sibling.num_pos <= output.num_pos);
        output.num_pos -= sibling.num_pos;
    }
}

}

#endif
