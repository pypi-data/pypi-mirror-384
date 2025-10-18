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

#ifndef GLM_HOST_SOLVER
#define GLM_HOST_SOLVER

#include "Solver.hpp"

#include <algorithm>
#include <atomic>
#include <cassert>
#include <cstring>
#include <map>
#include <random>
#include <thread>
#include <time.h>

#include "OMP.hpp"

#include "HostSolverUtil.hpp"

namespace glm {

// Solve an Objective on a single CPU numa node
template <class D, class O> class HostSolver : public Solver {
#define max_thread_nr_ 64U

public:
    // delete copy ctor
    HostSolver<D, O>(const HostSolver<D, O>&) = delete;

    // ctor
    HostSolver<D, O>(D* data, O* obj, double sigma, double tol, uint32_t num_threads = 1, bool add_bias = false,
                     double bias_val = 1.0, int numa_node = 0)
        : Solver(static_cast<Dataset*>(data), static_cast<Objective*>(obj), num_threads * sigma, tol, add_bias,
                 bias_val)
        , L1_CACHE_LINE_SIZE(cpu_l1d_cache_line_size())
        , bkt_size_(model_len_ < 500000UL ? 1 : L1_CACHE_LINE_SIZE / sizeof(*model_))
        ,
    // bkt_size_(1),

// On z/OS multiple threads are only used for MBITreeEnsembleModel.
#ifdef WITH_ZOS
        num_threads_(1)
#else
        num_threads_(std::min(std::min(num_threads, std::max(model_len_ / bkt_size_, 1U)), max_thread_nr_))
#endif
        , numa_node_(numa_node)
        ,
        // even 1 thread then there is no local shuffle
        CPUMode_(num_threads_ == 1 ? GLOBAL_SHUFFLE : GLOBAL_SHUFFLE)
    {

// On z/OS multiple threads are only used for MBITreeEnsembleModel.
#ifdef WITH_ZOS
        num_threads = 1;
#endif

#ifdef WITH_NUMA
        // make sure this thread is running on the correct numa
        // node, this will affect the performance of malloc'ed memory
        numa_bind_caller_to_node(numa_node_);
#endif
        bool transpose = data_->get_transpose();

        if (is_primal<O>::value) {
            if (!transpose) {
                throw std::runtime_error("Primal Objective can only be solved with a transposed dataset.");
            }
        } else {
            if (transpose) {
                throw std::runtime_error("Dual Objective can only be solved with a non-transposed dataset.");
            }
        }
        uint64_t tot_b = align_up(model_len_ * sizeof(*model_), L1_CACHE_LINE_SIZE)
                         + 4ULL * align_up(shared_len_ * sizeof(double), L1_CACHE_LINE_SIZE);
        if (CPUMode_ == GLOBAL_SHUFFLE)
            tot_b += align_up(udiv_round_up(model_len_, bkt_size_) * sizeof(*perm_), L1_CACHE_LINE_SIZE);
        if (1 < num_threads_)
            tot_b += (uint64_t)num_threads_ * (uint64_t)align_up(shared_len_ * sizeof(double), L1_CACHE_LINE_SIZE);
        uint8_t* ptr   = cpu_malloc(tot_b, L1_CACHE_LINE_SIZE, uint8_t);
        uint64_t bytes = 0;
        assert(nullptr != ptr);
        model_ = reinterpret_cast<double*>(ptr);
        ptr += align_up(model_len_ * sizeof(*model_), L1_CACHE_LINE_SIZE);
        bytes += align_up(model_len_ * sizeof(*model_), L1_CACHE_LINE_SIZE);
        shared_ = reinterpret_cast<double*>(ptr);
        ptr += align_up(shared_len_ * sizeof(double), L1_CACHE_LINE_SIZE);
        bytes += align_up(shared_len_ * sizeof(double), L1_CACHE_LINE_SIZE);
        shared_cached_ = reinterpret_cast<double*>(ptr);
        ptr += align_up(shared_len_ * sizeof(double), L1_CACHE_LINE_SIZE);
        bytes += align_up(shared_len_ * sizeof(double), L1_CACHE_LINE_SIZE);
        c1_ = reinterpret_cast<double*>(ptr);
        ptr += align_up(shared_len_ * sizeof(double), L1_CACHE_LINE_SIZE);
        bytes += align_up(shared_len_ * sizeof(double), L1_CACHE_LINE_SIZE);
        c2_ = reinterpret_cast<double*>(ptr);
        ptr += align_up(shared_len_ * sizeof(double), L1_CACHE_LINE_SIZE);
        bytes += align_up(shared_len_ * sizeof(double), L1_CACHE_LINE_SIZE);
        if (CPUMode_ == GLOBAL_SHUFFLE) {
            perm_ = reinterpret_cast<uint32_t*>(ptr);
            ptr += align_up(udiv_round_up(model_len_, bkt_size_) * sizeof(*perm_), L1_CACHE_LINE_SIZE);
            bytes += align_up(udiv_round_up(model_len_, bkt_size_) * sizeof(*perm_), L1_CACHE_LINE_SIZE);
            for (uint32_t i = 0; i < udiv_round_up(model_len_, bkt_size_); i++)
                perm_[i] = i;
        }

        // printf("shared len=%u model len=%u.\n", shared_len_, model_len_);
        if (1 == num_threads_)
            return;
        int rc = INIT_BARRIER(&gbarrier_, num_threads_ + 1);
        assert(0 == rc);
        exit_ = false;
        for (uint32_t i = 0; i < num_threads_; ++i) {
            thread_vars_[i].shared = reinterpret_cast<double*>(ptr);
            ptr += align_up(shared_len_ * sizeof(double), L1_CACHE_LINE_SIZE);
            bytes += align_up(shared_len_ * sizeof(double), L1_CACHE_LINE_SIZE);
            thread_vars_[i].thr = std::thread(&HostSolver<D, O>::trainer_thread_uepoch_rnd_bkt, this, i);
        }
        assert(bytes == tot_b);
    }

    // dtor
    virtual ~HostSolver<D, O>()
    {
        if (1 != num_threads_) {
            // stop threads wait for them to finish
            exit_ = true;
            WAIT_BARRIER(&gbarrier_); // signal exit
            for (uint32_t i = 0; i < num_threads_; ++i) {
                if (thread_vars_[i].thr.joinable())
                    thread_vars_[i].thr.join();
            }
        }
        // std::cout << "Destroying HostSolver: " << typeid(O).name() << std::endl;
        cpu_free(model_);

#ifdef WITH_NUMA
        // release numa node affinity
        numa_release_binding();
#endif
    }

    // initialize
    virtual void init(double* const shared_out)
    {
#ifdef WITH_NUMA
        numa_bind_caller_to_node(numa_node_);
#endif
        if (1 == num_threads_)
            init_impl(shared_out);
        else
            init_impl_par(shared_out);
    }

    // set new value of shared vector
    virtual void set_shared(const double* const shared_new)
    {
#ifdef WITH_NUMA
        numa_bind_caller_to_node(numa_node_);
#endif
        memcpy(shared_cached_, shared_new, sizeof(*shared_cached_) * shared_len_);
    }

    virtual bool get_update(double* const shared_delta)
    {
        bool stop = false;
#ifdef WITH_NUMA
        numa_bind_caller_to_node(numa_node_);
#endif
        if (1 == num_threads_)
            stop = get_update_impl_seq(shared_delta);
        else
            stop = reduction(shared_delta);

        epoch_nr_++;

        return stop;
    }

    // compute cost function
    virtual double partial_cost() { return Solver::partial_cost_impl<D, O>(); }

    // get final model vector
    virtual void get_model(double* const x)
    {
#ifdef WITH_NUMA
        numa_bind_caller_to_node(numa_node_);
#endif
        Solver::get_model_impl<O>(x);
    }

    // get non-zero coordinates
    virtual void get_nz_coordinates(std::vector<uint32_t>& x)
    {
#ifdef WITH_NUMA
        numa_bind_caller_to_node(numa_node_);
#endif
        Solver::get_nz_coordinates_impl<O>(x);
    }

private:
    inline void omp_shared_len_cost_threads(const uint64_t iter_nr)
    {
        if (1 < num_threads_ && 50000UL < iter_nr / num_threads_)
            omp_set_num_threads(num_threads_);
        else
            omp_set_num_threads(1);
    }

    inline void compute_derivatives()
    {
        auto x = static_cast<D*>(data_)->get_data();
        auto p = static_cast<O*>(obj_)->get_params();
        omp_shared_len_cost_threads(shared_len_);
        OMP::parallel_for<int32_t>(0, shared_len_, [this, &x, &p](const int32_t& idx) {
            double this_lab = is_primal<O>::value ? O::lab_transform(x.labs[idx]) : 0.0;
            double c1       = O::df1(p, shared_cached_[idx], this_lab);
            double c2       = O::df2(p, shared_cached_[idx], this_lab);
            shared_[idx]    = c1 / c2;
            c1_[idx]        = c1;
            c2_[idx]        = c2;
        });
    }

    bool get_update_impl_seq(double* const shared_delta)
    {
        auto           x      = static_cast<D*>(data_)->get_data();
        auto           p      = static_cast<O*>(obj_)->get_params();
        const uint32_t bkt_nr = udiv_round_up(model_len_, bkt_size_);

        // shuffle coordinates
        std::mt19937 rng(epoch_nr_);
        for (uint32_t i = 0; i < bkt_nr - 1; ++i) {
            const uint32_t j   = (i + rng()) % (bkt_nr - i);
            const uint32_t tmp = perm_[i];
            perm_[i]           = perm_[j];
            perm_[j]           = tmp;
        }

        /*auto data_tmp = static_cast<D*>(data_)->get_data();
        for(uint32_t l = 0; l < data_->get_num_ex(); l++) {
            std::cout << "[HostSolver - get_update] labs " << data_tmp.labs[l] << " ";
        }
        std::cout << "" << std::endl;*/

        // compute derivatives
        for (uint32_t idx = 0; idx < shared_len_; idx++) {
            double this_lab = is_primal<O>::value ? O::lab_transform(x.labs[idx]) : 0.0;
            double c1       = O::df1(p, shared_cached_[idx], this_lab);
            double c2       = O::df2(p, shared_cached_[idx], this_lab);
            shared_[idx]    = c1 / c2;
            c1_[idx]        = c1;
            c2_[idx]        = c2;
            // std::cout << "[HostSolver - get_update] HostSolver this_lab " << this_lab << " c1 " << c1 << " c2 " << c2
            // << " shared_ " << shared_[idx] << std::endl;
        }

        double norm_diff  = 0.0;
        double norm_model = 0.0;

        // update bias term (primal only)
        if (is_primal<O>::value && add_bias_) {
            // bias term in first partition only
            if (data_->get_partition_id() == 0) {
                update_bias_term_primal(shared_, norm_diff, norm_model);
            }
        }

        double num_max_new = -std::numeric_limits<double>::max();
        double num_min_new = +std::numeric_limits<double>::max();

        uint32_t num_active_pt = 0;

        // perform an epoch
        for (uint32_t bkt = 0; bkt < bkt_nr; bkt++) {
            const uint32_t b_idx = perm_[bkt];
            // assert(b_idx < bkt_nr);
            const uint32_t min_idx = b_idx * bkt_size_;
            const uint32_t max_idx = std::min((b_idx + 1) * bkt_size_, model_len_);
            // assert(min_idx < max_idx && (max_idx - min_idx) <= bkt_size_);
            for (uint32_t this_pt = min_idx; this_pt < max_idx; this_pt++) {

                // old value of model
                double old_model = model_[this_pt];

                if (shrinkage_[this_pt]) {
                    norm_model_stopped_ += fabs(old_model);
                    continue;
                }

                num_active_pt++;

                uint32_t this_len = D::get_pt_len(x, this_pt);
                double   num      = 0.0;
                double   den      = 0.0;

                for (uint32_t k = 0; k < this_len; k++) {
                    float    val;
                    uint32_t ind;
                    D::lookup(x, this_pt, k, this_len, ind, val);
                    num += c2_[ind] * shared_[ind] * val;
                    den += c2_[ind] * val * val;
                }

                if (!is_primal<O>::value && add_bias_) {
                    num += c2_[shared_len_ - 1] * shared_[shared_len_ - 1] * bias_val_;
                    den += c2_[shared_len_ - 1] * bias_val_ * bias_val_;
                }

                double this_lab = is_primal<O>::value ? 0.0 : O::lab_transform(x.labs[this_pt]);
                // std::cout << "[HostSolver - get_update] this_lab " << this_lab << std::endl;

                den *= sigma_;
                num += O::dg1(p, old_model, this_lab);
                den += O::dg2(p, old_model, this_lab);

                // std::cout << "[HostSolver - get_update] den " << den << " sigma_ " << sigma_ << " num " << num << "
                // den " << den << std::endl;

                double num_p = this_lab * num;

                shrinkage_[this_pt] = O::shrinkage(p, old_model, this_lab, num_min_, num_max_, num_p);

                num_max_new = std::max(num_max_new, num_p);
                num_min_new = std::min(num_min_new, num_p);

                // update model
                double new_model = old_model - num / den;

                // apply constraints
                O::apply_constraints(p, new_model, this_lab, den);

                // compute delta
                double delta = new_model - old_model;

                // std::cout << "[HostSolver - get_update] new_model " << new_model << " old_model " << old_model << "
                // delta " << delta << std::endl;

                // update model
                model_[this_pt] += delta;

                norm_diff += fabs(delta);
                norm_model += fabs(new_model);

                // update shared vector
                for (uint32_t k = 0; k < this_len; k++) {
                    float    val;
                    uint32_t ind;
                    D::lookup(x, this_pt, k, this_len, ind, val);
                    // std::cout << "[HostSolver - get_update] val " << val << " delta " << delta << std::endl;
                    shared_[ind] += val * delta * sigma_;
                }

                if (!is_primal<O>::value && add_bias_) {
                    shared_[shared_len_ - 1] += bias_val_ * delta * sigma_;
                }
            }
        }

        uint32_t num_partitions = data_->get_num_partitions();

        if (num_partitions > 1) {
            assert(shared_delta != nullptr);
        }
        double* const shared_to_upd = shared_delta != nullptr ? shared_delta : shared_cached_;
        assert(nullptr != shared_to_upd);

        for (uint32_t idx = 0; idx < shared_len_; idx++)
            shared_to_upd[idx]
                = shared_cached_[idx] / double(num_partitions) + (shared_[idx] - c1_[idx] / c2_[idx]) / sigma_;

        bool stop = (norm_diff / (norm_model + norm_model_stopped_) < tol_) || (num_active_pt == 0);

        num_max_ = (num_max_new > 0) ? num_max_new : +std::numeric_limits<double>::max();
        num_min_ = (num_min_new < 0) ? num_min_new : -std::numeric_limits<double>::max();

        return stop;
    }

    bool reduction(double* const shared_delta)
    {

        const uint32_t num_partitions = data_->get_num_partitions();
        double* const  shared_to_upd  = shared_delta != nullptr ? shared_delta : shared_cached_;
        assert(nullptr != shared_to_upd);

        WAIT_BARRIER(&gbarrier_); // start epoch
        compute_derivatives();
        if (GLOBAL_SHUFFLE == CPUMode_) {
            std::mt19937   rng(epoch_nr_);
            const uint32_t len = udiv_round_up(model_len_, bkt_size_);
            for (uint32_t i = 0; i < len - 1; ++i) {
                const uint32_t j   = (i + rng()) % (len - i);
                const uint32_t tmp = perm_[i];
                perm_[i]           = perm_[j];
                perm_[j]           = tmp;
            }
        }

        WAIT_BARRIER(&gbarrier_); // send derivatives
        WAIT_BARRIER(&gbarrier_); // small epoch finished

        omp_shared_len_cost_threads(num_threads_ * shared_len_);
        OMP::parallel_for<int32_t>(0, shared_len_, [this, &shared_to_upd, &num_partitions](const int32_t& idx) {
            shared_to_upd[idx] = shared_cached_[idx] / double(num_partitions);
            for (uint32_t thr = 0; thr < num_threads_; ++thr) {
                shared_to_upd[idx] += (thread_vars_[thr].shared[idx] - c1_[idx] / c2_[idx]) / sigma_;
            }
        });

        double   norm_diff     = 0.0;
        double   norm_model    = 0.0;
        double   num_max_new   = -std::numeric_limits<double>::max();
        double   num_min_new   = +std::numeric_limits<double>::max();
        uint32_t num_active_pt = 0;

        for (uint32_t t = 0; t < num_threads_; t++) {
            norm_diff += thread_vars_[t].norm_diff;
            norm_model += thread_vars_[t].norm_model;
            num_max_new = std::max(num_max_new, thread_vars_[t].num_max);
            num_min_new = std::min(num_min_new, thread_vars_[t].num_min);
            norm_model_stopped_ += thread_vars_[t].norm_model_stopped;
            num_active_pt += thread_vars_[t].num_active_pt;
        }

        num_max_ = (num_max_new > 0) ? num_max_new : +std::numeric_limits<double>::max();
        num_min_ = (num_min_new < 0) ? num_min_new : -std::numeric_limits<double>::max();

        // printf("num_active_pt: %d, num_max: %e, num_min: %e\n", num_active_pt, num_max_, num_min_);
        // printf("diff: %10.8f %10.8f\n", norm_diff/norm_model, tol_);
        bool stop = (norm_diff / (norm_model + norm_model_stopped_) < tol_) || (num_active_pt == 0);
        return stop;
    }

    void trainer_thread_init_bkts(const uint32_t tid, const uint32_t min_per_thr_bkt, const uint32_t bkt_nr,
                                  uint32_t& per_thr_bkt, uint32_t& min_bkt_base)
    {
        uint32_t bkt_idx = 0, rem = bkt_nr - num_threads_ * min_per_thr_bkt;
        for (uint32_t i = 0; i < num_threads_; ++i) {
            uint32_t thr_bkt = min_per_thr_bkt;
            if (0 < rem) {
                thr_bkt++;
                rem--;
            }
            if (tid == i) {
                min_bkt_base = bkt_idx;
                per_thr_bkt  = thr_bkt;
            }
            bkt_idx += thr_bkt;
        }
        assert(bkt_idx == bkt_nr);
    }

    void trainer_thread_uepoch_rnd_bkt(const uint32_t tid)
    {
#ifdef WITH_NUMA
        numa_bind_caller_to_node(numa_node_);
#endif
        auto           x = static_cast<D*>(data_)->get_data();
        auto           p = static_cast<O*>(obj_)->get_params();
        std::mt19937   rng(tid);
        double* const  shared          = thread_vars_[tid].shared;
        const uint32_t bkt_nr          = udiv_round_up(model_len_, bkt_size_);
        const uint32_t max_per_thr_bkt = udiv_round_up(model_len_, bkt_size_ * num_threads_);
        const uint32_t min_per_thr_bkt = model_len_ / bkt_size_ / num_threads_;
        uint32_t*      idxs            = nullptr;
        if (CPUMode_ != GLOBAL_SHUFFLE)
            idxs = cpu_malloc(max_per_thr_bkt * sizeof(*idxs), L1_CACHE_LINE_SIZE, uint32_t);
        uint32_t min_bkt_base = bkt_nr;
        uint32_t per_thr_bkt  = max_per_thr_bkt + 1;
        trainer_thread_init_bkts(tid, min_per_thr_bkt, bkt_nr, per_thr_bkt, min_bkt_base);
        assert(min_bkt_base < bkt_nr && per_thr_bkt <= max_per_thr_bkt);

        if (exit_)
            return;
        // init
        WAIT_BARRIER(&gbarrier_); // start per thread init
        {
            memcpy(shared, shared_, sizeof(*shared) * shared_len_);

            const uint32_t min_bkt = min_bkt_base;
            const uint32_t min_idx = min_bkt * bkt_size_;
            const uint32_t max_idx = std::min((min_bkt + per_thr_bkt) * bkt_size_, model_len_);
            for (uint32_t pt = min_idx; pt < max_idx; ++pt) {
                double   this_label = is_primal<O>::value ? 0.0 : O::lab_transform(x.labs[pt]);
                uint32_t this_len   = D::get_pt_len(x, pt);
                double   delta      = O::init_model(p, this_label);
                model_[pt]          = delta;

                // update shared vector
                for (uint32_t k = 0; k < this_len; k++) {
                    float    val;
                    uint32_t ind;
                    D::lookup(x, pt, k, this_len, ind, val);
                    shared[ind] += val * delta;
                }
                if (!is_primal<O>::value && add_bias_) {
                    shared[shared_len_ - 1] += bias_val_ * delta;
                }
            }
        }
        WAIT_BARRIER(&gbarrier_); // threads finished

        // main loop
        if (CPUMode_ != GLOBAL_SHUFFLE)
            for (uint32_t i = 0; i < per_thr_bkt; ++i)
                idxs[i] = i;
        assert(tid < num_threads_);
        do {
            WAIT_BARRIER(&gbarrier_); // start epoch
            double norm_diff          = 0.0;
            double norm_model         = 0.0;
            double norm_model_stopped = 0.0;
            double num_max            = -std::numeric_limits<double>::max();
            double num_min            = +std::numeric_limits<double>::max();

            uint32_t num_active_pt = 0;

            if (exit_)
                break;
#define GOLDEN_RATIO_32BIT 2654435761UL
            uint32_t min_bkt_off = min_bkt_base;
            switch (CPUMode_) {
            case LOCAL_SHUFFLE_SHIFT:
                min_bkt_off = ((uint64_t)epoch_nr_ * GOLDEN_RATIO_32BIT + min_bkt_base) % bkt_nr;
            case LOCAL_SHUFFLE_NOSHIFT:
                // random shuffle
                for (uint32_t i = 0; i < per_thr_bkt - 1; ++i) {
                    const uint32_t j   = (i + rng()) % (per_thr_bkt - i);
                    const uint32_t tmp = idxs[i];
                    idxs[i]            = idxs[j];
                    idxs[j]            = tmp;
                }
                break;
            case GLOBAL_SHUFFLE:
                break;
            default:
                assert(0);
                break;
            }
            WAIT_BARRIER(&gbarrier_); // wait for derivatives
            memcpy(shared, shared_, sizeof(*shared) * shared_len_);

            // update bias term (primal only)
            if (is_primal<O>::value && add_bias_) {
                // bias term in first partition only
                if (data_->get_partition_id() == 0 && tid == 0) {
                    update_bias_term_primal(shared, norm_diff, norm_model);
                }
            }

            for (uint32_t bkt = 0; bkt < per_thr_bkt; bkt++) {
                uint32_t min_bkt = 0;
                if (CPUMode_ == GLOBAL_SHUFFLE)
                    min_bkt = perm_[min_bkt_off + bkt]; // wrap around if necessary
                else
                    min_bkt = (min_bkt_off + idxs[bkt]) % bkt_nr; // wrap around if necessary
                const uint32_t min_idx = min_bkt * bkt_size_;
                const uint32_t max_idx = std::min((min_bkt + 1) * bkt_size_, model_len_);

                for (uint32_t this_pt = min_idx; this_pt < max_idx; ++this_pt) {

                    // old value of model
                    double old_model = model_[this_pt];

                    if (shrinkage_[this_pt]) {
                        norm_model_stopped += fabs(old_model);
                        continue;
                    }
                    num_active_pt++;

                    const uint32_t this_len = D::get_pt_len(x, this_pt);
                    double         num      = 0.0;
                    double         den      = 0.0;
                    for (uint32_t k = 0; k < this_len; ++k) {
                        float    val;
                        uint32_t ind;
                        D::lookup(x, this_pt, k, this_len, ind, val);
                        num += c2_[ind] * shared[ind] * val;
                        den += c2_[ind] * val * val;
                    }

                    if (!is_primal<O>::value && add_bias_) {
                        num += c2_[shared_len_ - 1] * shared[shared_len_ - 1] * bias_val_;
                        den += c2_[shared_len_ - 1] * bias_val_ * bias_val_;
                    }

                    double this_lab = is_primal<O>::value ? 0.0 : O::lab_transform(x.labs[this_pt]);
                    den *= sigma_;
                    num += O::dg1(p, old_model, this_lab);
                    den += O::dg2(p, old_model, this_lab);

                    double num_p = this_lab * num;

                    shrinkage_[this_pt] = O::shrinkage(p, old_model, this_lab, num_min_, num_max_, num_p);

                    num_max = std::max(num_max, num_p);
                    num_min = std::min(num_min, num_p);

                    // update model
                    double new_model = old_model - num / den;

                    // apply constraints
                    O::apply_constraints(p, new_model, this_lab, den);

                    // compute delta
                    double delta = new_model - old_model;

                    norm_diff += fabs(delta);
                    norm_model += fabs(new_model);

                    // update model
                    model_[this_pt] += delta;
                    for (uint32_t k = 0; k < this_len; k++) {
                        float    val;
                        uint32_t ind;
                        D::lookup(x, this_pt, k, this_len, ind, val);
                        shared[ind] += val * delta * sigma_;
                    }

                    if (!is_primal<O>::value && add_bias_) {
                        shared[shared_len_ - 1] += bias_val_ * delta * sigma_;
                    }
                }
            }
            thread_vars_[tid].norm_diff          = norm_diff;
            thread_vars_[tid].norm_model         = norm_model;
            thread_vars_[tid].norm_model_stopped = norm_model_stopped;
            thread_vars_[tid].num_max            = num_max;
            thread_vars_[tid].num_min            = num_min;
            thread_vars_[tid].num_active_pt      = num_active_pt;

            WAIT_BARRIER(&gbarrier_); // epoch ends
        } while (1);

        if (CPUMode_ != GLOBAL_SHUFFLE)
            cpu_free(idxs);
    }

    inline void init_impl(double* const shared_out)
    {

        auto x = static_cast<D*>(data_)->get_data();
        auto p = static_cast<O*>(obj_)->get_params();

        for (uint32_t i = 0; i < shared_len_; i++)
            shared_[i] = 0.0L;

        num_max_            = +std::numeric_limits<double>::max();
        num_min_            = -std::numeric_limits<double>::max();
        norm_model_stopped_ = 0.0;

        shrinkage_.resize(model_len_, 0);

        // initialize epoch counter
        epoch_nr_ = 0;

        if (is_primal<O>::value && add_bias_) {
            // bias term in first partition only
            if (data_->get_partition_id() == 0) {
                init_bias_term_primal(shared_);
            }
        }

        for (uint32_t pt = 0; pt < model_len_; pt++) {
            double   this_label = is_primal<O>::value ? 0.0 : O::lab_transform(x.labs[pt]);
            uint32_t this_len   = D::get_pt_len(x, pt);
            double   delta      = O::init_model(p, this_label);
            model_[pt]          = delta;

            // std::cout << "init_impl this_label " << this_label << " this_len " << this_len << " delta " << delta <<
            // std::endl; update shared vector
            for (uint32_t k = 0; k < this_len; k++) {
                float    val;
                uint32_t ind;
                D::lookup(x, pt, k, this_len, ind, val);
                // std::cout << "init_impl val " << val << " ind " << ind << std::endl;
                shared_[ind] += val * delta;
            }
            if (!is_primal<O>::value && add_bias_) {
                shared_[shared_len_ - 1] += bias_val_ * delta;
            }
        }

        assert(1 == data_->get_num_partitions() || shared_out != nullptr);

        double* const shared_to_upd = shared_out != nullptr ? shared_out : shared_cached_;
        memcpy(shared_to_upd, shared_, sizeof(*shared_) * shared_len_);
        // for(uint32_t l=0; l < shared_len_; l++)
        //  std::cout << "shared " << shared_to_upd[l] << " real " << shared_[l] << std::endl;
    }

    inline void init_impl_par(double* const shared_out)
    {

        omp_shared_len_cost_threads(shared_len_);
        OMP::parallel_for<int32_t>(0, shared_len_, [this](const int32_t& i) { shared_[i] = 0.0L; });

        num_max_            = +std::numeric_limits<double>::max();
        num_min_            = -std::numeric_limits<double>::max();
        norm_model_stopped_ = 0.0;

        shrinkage_.resize(model_len_, 0);

        // initialize epoch counter
        epoch_nr_ = 0;

        // init bias term (primal only)
        if (is_primal<O>::value && add_bias_) {
            // bias term in first partition only
            if (data_->get_partition_id() == 0) {
                init_bias_term_primal(shared_);
            }
        }

        WAIT_BARRIER(&gbarrier_); // start per thread init
        WAIT_BARRIER(&gbarrier_); // threads finished

        // reduce
        omp_shared_len_cost_threads(num_threads_ * shared_len_);
        OMP::parallel_for<int32_t>(0, shared_len_, [this](const int32_t& idx) {
            for (uint32_t thr = 0; thr < num_threads_; ++thr)
                shared_[idx] += (thread_vars_[thr].shared[idx]);
        });

        double* const shared_to_upd = shared_out != nullptr ? shared_out : shared_cached_;
        memcpy(shared_to_upd, shared_, sizeof(*shared_) * shared_len_);
    }

    void inline init_bias_term_primal(double* const shared_upd)
    {
        auto   p     = static_cast<O*>(obj_)->get_params();
        double delta = O::init_model(p, 0.0);
        bias_        = delta;
        omp_shared_len_cost_threads(shared_len_);
        OMP::parallel_for<int32_t>(
            0, shared_len_, [this, &shared_upd, &delta](const int32_t& k) { shared_upd[k] += bias_val_ * delta; });
    }

    void inline update_bias_term_primal(double* const shared_upd, double& norm_diff, double& norm_model)
    {
        auto   p   = static_cast<O*>(obj_)->get_params();
        double num = 0.0;
        double den = 0.0;
        for (uint32_t k = 0; k < shared_len_; k++) {
            num += c2_[k] * shared_upd[k] * bias_val_;
            den += c2_[k] * bias_val_ * bias_val_;
        }
        double old_model = bias_;
        den *= sigma_;
        num += O::dg1(p, old_model, 0.0);
        den += O::dg2(p, old_model, 0.0);
        double new_model = old_model - num / den;
        O::apply_constraints(p, new_model, 0.0, den);
        double delta = new_model - old_model;
        bias_ += delta;
        norm_diff += fabs(delta);
        norm_model += fabs(new_model);
        for (uint32_t k = 0; k < shared_len_; k++) {
            shared_upd[k] += bias_val_ * delta * sigma_;
        }
    }

    const uint32_t L1_CACHE_LINE_SIZE;
    const uint32_t bkt_size_;
    const uint32_t num_threads_;
    const int      numa_node_;
#define max_thread_nr_ 64U
    // static constexpr uint32_t max_thread_nr_ = 64U;

    enum CPUMode { LOCAL_SHUFFLE_SHIFT, LOCAL_SHUFFLE_NOSHIFT, GLOBAL_SHUFFLE };
    const CPUMode CPUMode_;

    // epoch counter
    uint32_t epoch_nr_;

    double*   c1_;
    double*   c2_;
    uint32_t* perm_;

    double               num_max_;
    double               num_min_;
    double               norm_model_stopped_;
    std::vector<uint8_t> shrinkage_;

    // thread variables
    std::atomic<bool> exit_;
    char              pad0_[_MAX_L1_CACHE_LINE_SIZE];
    BARRIER           gbarrier_; // global
    char              pad1_[_MAX_L1_CACHE_LINE_SIZE];
    struct {
        std::thread thr;
        double      norm_diff;
        double      norm_model;
        double      norm_model_stopped;
        double      num_min;
        double      num_max;
        uint32_t    num_active_pt;
        double*     shared;
    } thread_vars_[max_thread_nr_];
};

}

#endif
