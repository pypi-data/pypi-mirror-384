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
 *                Nikolas Ioannou
 *
 * End Copyright
 ********************************************************************/

#ifndef GLM_MULTI_HOST_SOLVER
#define GLM_MULTI_HOST_SOLVER

#include "Solver.hpp"

#include <algorithm>
#include <tuple>
#include <vector>
#include <cmath>
#include <iostream>

#include "OMP.hpp"

#include "HostSolver.hpp"

namespace glm {

// Solve an Objective on the GPU
template <class D, class O> class MultiHostSolver : public Solver {

public:
    // ctor

    MultiHostSolver<D, O>(D* data, O* obj, double sigma, double tol, std::vector<std::tuple<int, int>> numa_nodes_cpus,
                          uint32_t num_threads = 1, bool add_bias = false, double bias_val = 1.0)
        : Solver(static_cast<Dataset*>(data), static_cast<Objective*>(obj), sigma, tol, add_bias, bias_val)
        , num_numa_nodes_(numa_nodes_cpus.size())
        , numa_nodes_cpus_(numa_nodes_cpus)
        , num_threads_(num_threads)
    {

        // partition the data
        sub_data_ = static_cast<D*>(data_)->partition(num_numa_nodes_);

        // in case there isn't enough data for desired number of nodes
        num_numa_nodes_ = std::max(std::min((uint32_t)sub_data_.size(), num_numa_nodes_), 1U);

        // create the sub-solvers
        sub_solv_.resize(num_numa_nodes_);
        omp_set_num_threads(num_numa_nodes_);
        OMP::parallel_for<uint32_t>(0, num_numa_nodes_,
                                    [this, &sigma, &tol, &num_threads, &add_bias, &bias_val](const uint32_t& i) {
                                        auto& n = numa_nodes_cpus_[i];
                                        int   node, cpu;
                                        std::tie(node, cpu) = n;
                                        // std::cout << "Host numa solver on node " << node << " using " << num_threads
                                        // / num_numa_nodes_ << " threads."<< std::endl;
                                        sub_solv_[i] = std::make_shared<HostSolver<D, O>>(
                                            sub_data_[i].get(), static_cast<O*>(obj_), sigma * double(num_numa_nodes_),
                                            tol, num_threads / num_numa_nodes_, add_bias, bias_val, node);
                                    });

        const uint32_t model_len = add_bias_ ? (1 + data_->get_num_ft()) : data_->get_num_ft();

        for (uint32_t i = 0; i < num_numa_nodes_; i++) {
            auto& n = numa_nodes_cpus_[i];
            int   node, cpu;
            std::tie(node, cpu) = n;
            model_tmp_[i]       = (double*)numa_util_alloc(model_len * sizeof(*model_tmp_[i]), node);
            assert(nullptr != model_tmp_[i]);
            shared_tmp_[i] = sub_solv_[i]->get_shared_cached();
        }
        int rc = INIT_BARRIER(&gbarrier_, num_numa_nodes_ + 1);
        assert(0 == rc);
        exit_ = false;
        for (uint32_t i = 0; i < num_numa_nodes_; ++i)
            threads_[i] = std::thread(&MultiHostSolver::update_thread_, this, i);
    }

    virtual ~MultiHostSolver<D, O>()
    {
        exit_ = true;
        WAIT_BARRIER(&gbarrier_); // signal exit
        for (uint32_t i = 0; i < num_numa_nodes_; ++i)
            if (threads_[i].joinable())
                threads_[i].join();

        const uint32_t model_len = add_bias_ ? (1 + data_->get_num_ft()) : data_->get_num_ft();
        for (uint32_t i = 0; i < num_numa_nodes_; i++) {
            numa_util_free(model_tmp_[i], model_len * sizeof(*model_tmp_[i]));
        }
    }

    // set new value of shared vector
    virtual void set_shared(const double* const shared_new)
    {
        omp_set_num_threads(num_numa_nodes_);
        OMP::parallel_for<uint32_t>(0, num_numa_nodes_,
                                    [this, &shared_new](const uint32_t& i) { sub_solv_[i]->set_shared(shared_new); });
    }

    virtual void init(double* const shared_out)
    {
        // get shared vector contribution for all sub-solvers
        omp_set_num_threads(num_numa_nodes_);
        OMP::parallel_for<uint32_t>(0, num_numa_nodes_, [this](const uint32_t& i) { sub_solv_[i]->init(nullptr); });

        double* const shared_to_upd = shared_out == nullptr ? shared_tmp_[0] : shared_out;
        if (nullptr != shared_out)
            memcpy(shared_out, shared_tmp_[0], shared_len_ * sizeof(*shared_out));

        omp_set_num_threads(std::min(num_threads_, 8U));
        OMP::parallel_for<uint32_t>(0, shared_len_, [this, &shared_to_upd](const uint32_t& i) {
            for (uint32_t j = 1; j < num_numa_nodes_; j++)
                shared_to_upd[i] += shared_tmp_[j][i];
        });

        if (nullptr == shared_out) {
            omp_set_num_threads(num_numa_nodes_ - 1);
            OMP::parallel_for<uint32_t>(1, num_numa_nodes_,
                                        [this](const uint32_t& i) { sub_solv_[i]->set_shared(shared_tmp_[0]); });
        }
    }

    // shared_out == null => we do the reduction on node's 0 cached shared vector
    //                       otherwise, we use shared_out as an intermediate caching point
    virtual bool get_update(double* const shared_out)
    {
        WAIT_BARRIER(&gbarrier_); // epoch starts
        // get shared vector contribution for all sub-solvers
        WAIT_BARRIER(&gbarrier_); // epoch ends
        double* const shared_to_upd = shared_out == nullptr ? shared_tmp_[0] : shared_out;

        const int desired_numa_node = std::max(0, mem_to_numa_node(shared_to_upd));
        numa_bind_caller_to_node(desired_numa_node);
        if (nullptr != shared_out)
            memcpy(shared_out, shared_tmp_[0], shared_len_ * sizeof(*shared_out));

        omp_set_num_threads(std::min(num_threads_, 8U));
        OMP::parallel_for<uint32_t>(0, shared_len_, [this, &shared_to_upd](const uint32_t& i) {
            for (uint32_t j = 1; j < num_numa_nodes_; j++) {
                shared_to_upd[i] += shared_tmp_[j][i];
            }
        });

        bool all_stop = true;
        for (uint32_t i = 0; i < num_numa_nodes_; i++) {
            all_stop &= stop[i];
        }

        if (nullptr == shared_out) {
            omp_set_num_threads(num_numa_nodes_ - 1);
            OMP::parallel_for<uint32_t>(1, num_numa_nodes_,
                                        [this](const uint32_t& i) { sub_solv_[i]->set_shared(shared_tmp_[0]); });
        }

        return all_stop;
    }

    // compute cost function
    virtual double partial_cost()
    {

        omp_set_num_threads(num_numa_nodes_);
        for (uint32_t i = 0; i < num_numa_nodes_; i++) {
            cost_tmp_[i] = sub_solv_[i]->partial_cost();
        }
        double cost_out = cost_tmp_[0];
        for (uint32_t i = 1; i < num_numa_nodes_; i++) {
            cost_out += cost_tmp_[i];
        }
        return cost_out;
    }

    // get final model vector
    virtual void get_model(double* const x)
    {

        omp_set_num_threads(num_numa_nodes_);
        OMP::parallel_for<uint32_t>(0, num_numa_nodes_,
                                    [this](const uint32_t& i) { sub_solv_[i]->get_model(model_tmp_[i]); });

        const uint32_t model_len         = add_bias_ ? (1 + data_->get_num_ft()) : data_->get_num_ft();
        const int      desired_numa_node = std::max(0, mem_to_numa_node(x));
        numa_bind_caller_to_node(desired_numa_node);
        omp_set_num_threads(std::min(num_threads_, 8U));
        OMP::parallel_for<uint32_t>(0, model_len, [this, &x](const uint32_t& i) {
            x[i] = model_tmp_[0][i];
            for (uint32_t j = 1; j < num_numa_nodes_; j++) {
                x[i] += model_tmp_[j][i];
            }
        });
    }

    // get non-zero coordinates
    virtual void get_nz_coordinates(std::vector<uint32_t>& x)
    {
        for (uint32_t i = 0; i < num_numa_nodes_; i++) {
            sub_solv_[i]->get_nz_coordinates(x);
        }
    }

private:
    void update_thread_(const uint32_t numa_node)
    {
        if (exit_)
            return;
        do {
            WAIT_BARRIER(&gbarrier_); // start epoch
            if (exit_)
                break;
            stop[numa_node] = sub_solv_[numa_node]->get_update(nullptr);
            WAIT_BARRIER(&gbarrier_); // epoch ends

        } while (1);
    }

    static constexpr uint32_t         max_numa_nodes_ = 64;
    uint32_t                          num_numa_nodes_;
    std::vector<std::tuple<int, int>> numa_nodes_cpus_;
    const uint32_t                    num_threads_;

    std::vector<std::shared_ptr<D>>                sub_data_;
    std::vector<std::shared_ptr<HostSolver<D, O>>> sub_solv_;

    // temporary values need for aggregation
    double* shared_tmp_[max_numa_nodes_];
    double* model_tmp_[max_numa_nodes_];
    double  cost_tmp_[max_numa_nodes_];
    bool    stop[max_numa_nodes_];

    std::atomic<bool> exit_;
    std::thread       threads_[128];
    char              pad0_[_MAX_L1_CACHE_LINE_SIZE];
    BARRIER           gbarrier_; // global

    // delete copy ctor
    MultiHostSolver<D, O>(const MultiHostSolver<D, O>&) = delete;
};

template <class D, class O> class MultiNumaSolver : public Solver {

public:
    MultiNumaSolver<D, O>(D* data, O* obj, double sigma, double tol, uint32_t num_threads = 1, bool add_bias = false,
                          double bias_val = 1.0)
        : Solver(static_cast<Dataset*>(data), static_cast<Objective*>(obj), sigma, tol, add_bias, bias_val)
        , NUMAMode_(NUMA_AFFINITY)
    {

        if (NUMAMode_ == NUMA_NONE) {
            solver_ = std::make_shared<HostSolver<D, O>>(data, obj, sigma, tol, num_threads, add_bias, bias_val,
                                                         -1 /* all nodes */);
            return;
        }

        std::vector<std::tuple<int, int>> numa_nodes_cpus = numa_get_num_cpu_nodes();
        uint32_t                          cpus            = 0;
        for (auto& n : numa_nodes_cpus) {
            int node, cpu;
            std::tie(node, cpu) = n;
            cpus += cpu;
        }

        /*uint32_t exs = data->get_num_ex();
        uint32_t fts = data->get_num_ft();
        for (uint32_t e = 0 ; e < exs; e++) {
            for (uint32_t f = 0 ; f < fts; f++) {
                if (std::isnan(glm::DenseDataset::lookup2D(data->get_data(), e, f))) {
                    std::cout << "Oooops" << std::endl;
                }
            }
        }*/

        const int desired_numa_node = std::max(0, mem_to_numa_node(static_cast<Dataset*>(data)->get_labs()));
        // const int desired_numa_node = std::max(0, mem_to_numa_node(static_cast<D*>(data)->get_data().labs));

        if (numa_nodes_cpus.size() <= 1 || 0 == cpus || num_threads <= (cpus / numa_nodes_cpus.size())) {
            // TODO: make the numa node affinity based on the biggest chunk of data, now it's just labels
            // std::cout<<"Single numa node solver on node " << numa_node<< std::endl;
            solver_ = std::make_shared<HostSolver<D, O>>(data, obj, sigma, tol, num_threads, add_bias, bias_val,
                                                         desired_numa_node);
        } else {
            std::vector<std::tuple<int, int>> numa_nodes_mapped;
            uint32_t                          num_threads_rem = num_threads;
            for (auto it = numa_nodes_cpus.begin(); it != numa_nodes_cpus.end(); ++it) {
                int node, cpu;
                std::tie(node, cpu) = *it;
                if (desired_numa_node == node) {
                    // make desired numa node first
                    std::rotate(numa_nodes_cpus.begin(), it, numa_nodes_cpus.end());
                    break;
                }
            }
            for (auto it = numa_nodes_cpus.begin(); it != numa_nodes_cpus.end(); ++it) {
                int node, cpu;
                std::tie(node, cpu) = *it;
                if (0 == num_threads_rem)
                    break;
                num_threads_rem -= std::min(num_threads_rem, (uint32_t)cpu);
                numa_nodes_mapped.push_back(*it);
            }
            // std::cout<<"Multi numa node solver."<< std::endl;
            solver_ = std::make_shared<MultiHostSolver<D, O>>(data, obj, sigma, tol, numa_nodes_mapped, num_threads,
                                                              add_bias, bias_val);
        }
    }

    virtual ~MultiNumaSolver<D, O>() { }

    virtual void set_shared(const double* const shared_new) { solver_->set_shared(shared_new); }

    virtual void init(double* const shared_out) { solver_->init(shared_out); }

    virtual bool get_update(double* const shared_out) { return solver_->get_update(shared_out); }

    virtual double partial_cost() { return solver_->partial_cost(); }

    virtual void get_model(double* const x) { solver_->get_model(x); }

    // get non-zero coordinates
    virtual void get_nz_coordinates(std::vector<uint32_t>& x) { solver_->get_nz_coordinates(x); }

private:
    std::shared_ptr<Solver> solver_;
    enum NUMAMode { NUMA_AFFINITY, NUMA_NONE };
    const NUMAMode NUMAMode_;
    MultiNumaSolver<D, O>(const MultiNumaSolver<D, O>&) = delete;
};

}

#endif //  GLM_MULTI_HOST_SOLVER
