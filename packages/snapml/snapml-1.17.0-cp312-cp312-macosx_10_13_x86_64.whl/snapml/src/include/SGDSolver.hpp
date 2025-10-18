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
 *                Nikolaos Papandreou
 *
 * End Copyright
 ********************************************************************/

#ifndef GLM_SGD_SOLVER
#define GLM_SGD_SOLVER

#include "Solver.hpp"
#include <algorithm>
#include <math.h>
#include <random>

#include <iostream>
#include <fstream>

namespace glm {

template <class D, class O> class SGDSolver : public Solver {

public:
    struct params_privacy_t {
        double   eta;
        uint32_t batch_size;
        double   grad_clip;
        double   privacy_sigma;
    };

    // delete copy ctor
    SGDSolver<D, O>(const SGDSolver<D, O>&) = delete;

    // ctor
    SGDSolver<D, O>(D* data, O* obj, double sigma, double tol, double eta, uint32_t batch_size, double grad_clip,
                    double privacy_sigma)
        : Solver(static_cast<Dataset*>(data), static_cast<Objective*>(obj), 1.0, 0.0, false, 1.0, true)
    {

        // compile-time check
        // static_assert(is_primal<O>::value, "SGDSolver can only be compiled with a primal objective");

        // runtime check
        if (data_->get_transpose()) {
            throw std::runtime_error("SGDSolver can only be used with a non-transposed dataset.");
        }

        // runtime check
        if (data_->get_num_partitions() > 1) {
            throw std::runtime_error("SGDSolver can only be used with a non-distributed dataset.");
        }

        // runtime check
        assert(model_len_ == data_->get_num_ft());
        assert(shared_len_ == data_->get_num_ex());

        // privacy parameters
        params_privacy_.eta           = eta;
        params_privacy_.batch_size    = batch_size;
        params_privacy_.grad_clip     = grad_clip;
        params_privacy_.privacy_sigma = privacy_sigma;

        model_         = new double[model_len_]();
        shared_cached_ = new double[shared_len_]();

        perm.resize(shared_len_);
        for (uint32_t i = 0; i < shared_len_; i++) {
            perm[i] = i;
        }
    }

    // dtor
    virtual ~SGDSolver<D, O>()
    {
        delete[] model_;
        delete[] shared_cached_;
    }

    // initialize
    virtual void init(double* const shared_out) { init_impl(shared_out); }

    // set new value of shared vector
    virtual void set_shared(const double* const shared_new) { throw std::runtime_error("Should never call this"); }

    virtual bool get_update(double* const shared_delta) { return get_update_impl(shared_delta); }

    // compute cost function
    virtual double partial_cost()
    {
        compute_shared_vector_impl();
        return Solver::partial_cost_impl<D, O>();
    }

    // get final model vector
    virtual void get_model(double* const x) { Solver::get_model_impl<O>(x); }

    // get non-zero coordinates
    virtual void get_nz_coordinates(std::vector<uint32_t>& x) { Solver::get_nz_coordinates_impl<O>(x); }

private:
    // get model update
    bool get_update_impl(double* const shared_delta)
    {

        uint32_t num_ex = data_->get_num_ex();
        uint32_t num_lots;
        uint32_t batch_size = params_privacy_.batch_size;

        // runtime check
        assert(shared_delta == nullptr);

        num_lots = (uint32_t)(floor((double)num_ex / double(batch_size)));

        auto x = static_cast<D*>(data_)->get_data();
        auto p = static_cast<O*>(obj_)->get_params();

        // shuffle example indexes
        std::random_shuffle(perm.begin(), perm.end());

        std::vector<double> grad_vec(model_len_);
        std::vector<double> this_grad_vec(model_len_);
        for (uint32_t pt = 0; pt < model_len_; pt++) {
            grad_vec[pt] = 0;
        }

        // Gaussian noise of zero mean and sigma equal to privacy_sigma
        std::default_random_engine       generator;
        std::normal_distribution<double> distribution(0.0, params_privacy_.grad_clip * params_privacy_.privacy_sigma);

        // perform an epoch (num_lots*batch_size <= num_ex)
        for (uint32_t idx = 0; idx < num_lots * batch_size; idx++) {

            // training example selected
            uint32_t this_ex  = perm[idx];
            uint32_t this_len = D::get_pt_len(x, this_ex);
            double   this_lab = O::lab_transform(x.labs[this_ex]);

            // inner product of X[this_ex,:] * model^T
            double inn_prod = 0.0;
            for (uint32_t k = 0; k < this_len; k++) {
                float    val;
                uint32_t ind;
                D::lookup(x, this_ex, k, this_len, ind, val);
                inn_prod += val * model_[ind];
            }

            // compute local gradient vector
            for (uint32_t pt = 0; pt < model_len_; pt++) {
                this_grad_vec[pt] = 0;
            }

            double c1 = O::df1(p, inn_prod, this_lab);
            for (uint32_t k = 0; k < this_len; k++) {
                float    val;
                uint32_t ind;
                D::lookup(x, this_ex, k, this_len, ind, val);
                this_grad_vec[ind] += c1 * val;
            }

            // clip gradient
            if (params_privacy_.grad_clip > 0) {
                double grad_norm = 0.0;
                for (uint32_t pt = 0; pt < model_len_; pt++) {
                    grad_norm += this_grad_vec[pt] * this_grad_vec[pt];
                }
                grad_norm = sqrt(grad_norm) / params_privacy_.grad_clip;
                if (grad_norm < 1.0) {
                    grad_norm = 1.0;
                }
                for (uint32_t pt = 0; pt < model_len_; pt++) {
                    this_grad_vec[pt] = this_grad_vec[pt] / grad_norm;
                }
            }

            // accumulate local gradient vector
            for (uint32_t pt = 0; pt < model_len_; pt++) {
                grad_vec[pt] += this_grad_vec[pt];
            }

            // lot completed
            if (((idx + 1) % batch_size) == 0) {

                // add noise
                for (uint32_t pt = 0; pt < model_len_; pt++) {
                    double noise = distribution(generator);
                    grad_vec[pt] = (grad_vec[pt] + noise) / (double)batch_size;
                }

                // update model using gradient and learning rate and clear grad_vec
                for (uint32_t pt = 0; pt < model_len_; pt++) {
                    grad_vec[pt] += O::dg1(p, model_[pt], 0.0) / (double)num_ex;
                    model_[pt] -= params_privacy_.eta * grad_vec[pt];
                    grad_vec[pt] = 0;
                }
            }
        }

        return false;
    }

    void compute_shared_vector_impl()
    {

        auto x = static_cast<D*>(data_)->get_data();

        for (uint32_t i = 0; i < shared_len_; i++) {

            // training example
            uint32_t this_ex  = i;
            uint32_t this_len = D::get_pt_len(x, this_ex);

            // inner product of X[this_ex,:] * model^T
            double inn_prod = 0.0;
            for (uint32_t k = 0; k < this_len; k++) {
                float    val;
                uint32_t ind;
                D::lookup(x, this_ex, k, this_len, ind, val);
                inn_prod += val * model_[ind];
            }

            shared_cached_[i] = inn_prod;
        }
    }

    void init_impl(double* const shared_out)
    {

        assert(shared_out == nullptr);

        for (uint32_t pt = 0; pt < model_len_; pt++) {
            model_[pt] = 0.0;
        }
    }

    uint32_t              num_ex_;
    uint32_t              num_ft_;
    std::vector<uint32_t> perm;
    params_privacy_t      params_privacy_;
};

}

#endif
