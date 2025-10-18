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

#ifndef GLM_KERNELS
#define GLM_KERNELS

#include "GPUUtils.hpp"

namespace glm {

// initialize bias in primal case
// note -- could be optimized further
template <class D, class O>
__global__ void dev_init_bias_primal(uint32_t num_threads, typename D::data_t x, typename O::params_t p, double* bias,
                                     double* shared, uint32_t shared_len, double bias_val)
{

    int tid = threadIdx.x;

    __shared__ uint32_t this_len;
    __shared__ double   delta;

    if (tid == 0) {
        this_len = shared_len;
        delta    = O::init_model(p, 0.0);
        bias[0]  = delta;
    }

    __syncthreads();

    uint32_t k = tid;
    while (k < this_len) {
        shared[k] += bias_val * delta;
        k += num_threads;
    }
}

template <class D, class O, bool add_bias>
__global__ void dev_init(uint32_t num_threads, typename D::data_t x, typename O::params_t p, double* model,
                         double* shared, uint32_t* perm, uint32_t perm_len, uint32_t shared_len, double bias_val)
{

    int idx = blockIdx.x * gridDim.y + blockIdx.y;
    int tid = threadIdx.x;

    __shared__ uint32_t this_pt;
    __shared__ uint32_t this_len;
    __shared__ double   this_lab;
    __shared__ double   delta;

    if (idx < perm_len) {
        if (tid == 0) {
            this_pt        = perm[idx];
            this_len       = D::get_pt_len(x, this_pt);
            this_lab       = is_primal<O>::value ? 0.0 : O::lab_transform(x.labs[this_pt]);
            delta          = O::init_model(p, this_lab);
            model[this_pt] = delta;
        }

        __syncthreads();

        uint32_t k = tid;
        uint32_t ind;
        float    val;
        while (k < this_len) {
            D::lookup(x, this_pt, k, this_len, ind, val);
            copyData(&shared[ind], val * delta);
            k += num_threads;
        }

        __syncthreads();

        // add bias term to shared vector (dual case)
        if (add_bias && !is_primal<O>::value) {
            if (tid == 0) {
                atomicAdd(&shared[shared_len - 1], bias_val * delta);
            }
        }
    }
}

template <class D, class O>
__global__ void dev_epoch_bias_primal(uint32_t num_threads, typename D::data_t x, typename O::params_t p, double* bias,
                                      double* shared, double* c2, double eps, double sigma, double* bias_diff,
                                      double* bias_rdiff, uint32_t shared_len, double bias_val)
{

    int tid = threadIdx.x;

    __shared__ uint32_t      this_len;
    __shared__ double        old_model;
    __shared__ double        delta;
    extern __shared__ double cache[];

    if (tid == 0) {
        old_model = bias[0];
        this_len  = shared_len;
    }

    __syncthreads();

    double   num = 0.0;
    double   den = 0.0;
    uint32_t k   = tid;
    while (k < this_len) {
        num += c2[k] * shared[k] * bias_val;
        den += c2[k] * bias_val * bias_val;
        k += num_threads;
    }
    cache[tid]               = num;
    cache[num_threads + tid] = den;

    __syncthreads();

    uint32_t m = num_threads / 2;
    while (m != 0) {
        if (tid < m) {
            cache[tid] += cache[tid + m];
            cache[num_threads + tid] += cache[num_threads + tid + m];
        }
        __syncthreads();
        m /= 2;
    }

    if (tid == 0) {
        double num       = cache[0] + O::dg1(p, old_model, 0.0);
        double den       = sigma * cache[num_threads] + O::dg2(p, old_model, 0.0);
        double new_model = old_model - eps * num / den;
        O::apply_constraints(p, new_model, 0.0, den / eps);
        delta         = new_model - old_model;
        bias_diff[0]  = O::g_cost(p, old_model, 0.0) - O::g_cost(p, old_model + delta, 0.0);
        bias_rdiff[0] = fabs(delta);
        bias_rdiff[1] = fabs(new_model);
        bias[0] += delta;
    }

    __syncthreads();

    k = tid;
    while (k < shared_len) {
        shared[k] += bias_val * delta * sigma;
        k += num_threads;
    }
}

template <class D, class O, bool add_bias>
__global__ void dev_epoch(uint32_t num_threads, typename D::data_t x, typename O::params_t p, double* model,
                          double* shared, double* c2, double eps, double sigma, uint32_t* perm, uint32_t perm_len,
                          double* diff, double* rdiff, uint32_t shared_len, double bias_val)
{

    int idx = blockIdx.x * gridDim.y + blockIdx.y;
    int tid = threadIdx.x;

    __shared__ uint32_t      this_pt;
    __shared__ uint32_t      this_len;
    __shared__ double        this_lab;
    __shared__ double        old_model;
    __shared__ double        delta;
    extern __shared__ double cache[];

    if (idx < perm_len) {

        if (tid == 0) {
            this_pt   = perm[idx];
            old_model = model[this_pt];
            this_len  = D::get_pt_len(x, this_pt);
            this_lab  = is_primal<O>::value ? 0.0 : O::lab_transform(x.labs[this_pt]);
        }

        __syncthreads();

        double   num = 0.0;
        double   den = 0.0;
        uint32_t k   = tid;
        uint32_t ind;
        float    val;
        while (k < this_len) {
            D::lookup(x, this_pt, k, this_len, ind, val);
            num += c2[ind] * shared[ind] * val;
            den += c2[ind] * val * val;
            k += num_threads;
        }

        // add bias term to shared vector (dual case)
        if (add_bias && !is_primal<O>::value) {
            if (tid == 0) {
                num += c2[shared_len - 1] * shared[shared_len - 1] * bias_val;
                den += c2[shared_len - 1] * bias_val * bias_val;
            }
        }

        cache[tid]               = num;
        cache[num_threads + tid] = den;

        __syncthreads();

        uint32_t m = num_threads / 2;
        while (m != 0) {
            if (tid < m) {
                cache[tid] += cache[tid + m];
                cache[num_threads + tid] += cache[num_threads + tid + m];
            }
            __syncthreads();
            m /= 2;
        }

        if (tid == 0) {
            double num       = cache[0] + O::dg1(p, old_model, this_lab);
            double den       = sigma * cache[num_threads] + O::dg2(p, old_model, this_lab);
            double new_model = old_model - eps * num / den;
            O::apply_constraints(p, new_model, this_lab, den / eps);
            delta                 = new_model - old_model;
            diff[idx]             = O::g_cost(p, old_model, this_lab) - O::g_cost(p, old_model + delta, this_lab);
            rdiff[idx]            = fabs(delta);
            rdiff[perm_len + idx] = fabs(new_model);
            model[this_pt] += delta;
        }

        __syncthreads();

        k = tid;
        while (k < this_len) {
            D::lookup(x, this_pt, k, this_len, ind, val);
            atomicAdd(&shared[ind], val * delta * sigma);
            k += num_threads;
        }

        __syncthreads();

        // add bias term to shared vector (dual case)
        if (add_bias && !is_primal<O>::value) {
            if (tid == 0) {
                atomicAdd(&shared[shared_len - 1], bias_val * delta * sigma);
            }
        }
    }
}

template <class D, class O>
__global__ void dev_transform(uint32_t num_threads, uint32_t shared_len, typename D::data_t x, typename O::params_t p,
                              double* shared, double* shared_cached, double* c1, double* c2)
{

    int idx = blockIdx.x * gridDim.y + blockIdx.y;
    int tid = threadIdx.x;

    uint32_t this_pt = idx * num_threads + tid;

    if (this_pt < shared_len) {
        double this_lab = is_primal<O>::value ? O::lab_transform(x.labs[this_pt]) : 0.0;
        c1[this_pt]     = O::df1(p, shared_cached[this_pt], this_lab);
        c2[this_pt]     = O::df2(p, shared_cached[this_pt], this_lab);
        shared[this_pt] = c1[this_pt] / c2[this_pt];
    }
}

template <class D, class O>
__global__ void dev_subtract(uint32_t num_threads, uint32_t shared_len, uint32_t num_partitions, typename D::data_t x,
                             typename O::params_t p, double* shared, double* shared_cached, double* c1, double* c2,
                             double sigma, double* diff)
{

    int idx = blockIdx.x * gridDim.y + blockIdx.y;
    int tid = threadIdx.x;

    uint32_t this_pt = idx * num_threads + tid;

    if (this_pt < shared_len) {
        shared_cached[this_pt] /= double(num_partitions);
    }
    __syncthreads();

    if (this_pt < shared_len) {
        double this_c1  = c1[this_pt];
        double this_c2  = c2[this_pt];
        double delta    = (shared[this_pt] - this_c1 / this_c2) / sigma;
        shared[this_pt] = shared_cached[this_pt] + delta;
        diff[this_pt]   = -delta * (this_c1 + 0.5 * sigma * this_c2 * delta);
    }
    __syncthreads();
}

template <class D, class O>
__global__ void dev_model_init(uint32_t num_threads, uint32_t model_len, typename D::data_t x, double* model,
                               typename O::params_t p)
{
    int      idx     = blockIdx.x * gridDim.y + blockIdx.y;
    int      tid     = threadIdx.x;
    uint32_t this_pt = idx * num_threads + tid;

    __shared__ double this_lab;
    __shared__ double init_m;

    if (this_pt < model_len) {
        this_lab       = is_primal<O>::value ? 0.0 : O::lab_transform(x.labs[this_pt]);
        init_m         = O::init_model(p, this_lab);
        model[this_pt] = init_m;
    }
}

}

#endif
