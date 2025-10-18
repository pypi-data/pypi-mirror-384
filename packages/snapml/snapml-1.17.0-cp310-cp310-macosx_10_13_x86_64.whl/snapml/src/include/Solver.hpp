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
 *
 * End Copyright
 ********************************************************************/

#ifndef GLM_SOLVER
#define GLM_SOLVER

#include <stdexcept>
#include <memory>
#include "Traits.hpp"
#include "Dataset.hpp"
#include "Objective.hpp"
#include <cassert>

namespace glm {

// Abstract Solver
class Solver {

public:
    // ctor
    Solver(Dataset* data, Objective* obj, double sigma, double tol, bool add_bias, double bias_val = 1.0,
           bool sgd = false)
        : data_(data)
        , obj_(obj)
        , sigma_(sigma)
        , tol_(tol)
        , add_bias_(add_bias)
        , bias_val_(bias_val)
    {

        bool     transpose   = data_->get_transpose();
        uint32_t num_ex      = data_->get_num_ex();
        uint32_t num_ft      = add_bias_ ? (1 + data_->get_num_ft()) : data_->get_num_ft();
        uint32_t this_num_pt = data_->get_this_num_pt();

        if (!sgd) {
            shared_len_ = transpose ? num_ex : num_ft;
            model_len_  = this_num_pt;
        } else {
            assert(this_num_pt == num_ex);
            shared_len_ = num_ex;
            model_len_  = num_ft;
        }
    }

    // virtual dtor
    virtual ~Solver()
    {
        // std::cout << "Destroying Solver" << std::endl;
    }

    uint32_t dim() const { return shared_len_; }

    double* get_shared_cached(void) const { return shared_cached_; }

    // initialize
    virtual void init(double* const) = 0;

    // set new value of shared vector
    virtual void set_shared(const double* const) = 0;

    // get update to shared vector
    virtual bool get_update(double* const) = 0;

    virtual double partial_cost() = 0;

    virtual void get_model(double* const) = 0;

    virtual void get_nz_coordinates(std::vector<uint32_t>&) = 0;

protected:
    // pointer to dataset
    Dataset* data_;

    // pointer to objective
    Objective* obj_;

    // sigma parameter
    double sigma_;

    // tolerance parameter
    double tol_;

    // add bias term
    bool add_bias_;

    // value to add
    const double bias_val_;

    // local model vector
    double* model_;

    // bias term to add to model (in primal case)
    double bias_;

    // shared vector
    double* shared_;

    // cached shared vector
    double* shared_cached_;

    // length of shared vector
    uint32_t shared_len_;

    // length of local model
    uint32_t model_len_;

protected:
    // partial cost
    template <class D, class O> double partial_cost_impl()
    {

        auto     x              = static_cast<D*>(data_)->get_data();
        auto     p              = static_cast<O*>(obj_)->get_params();
        uint32_t num_partitions = data_->get_num_partitions();
        uint32_t partition_id   = data_->get_partition_id();

        double cost = 0.0;
        for (uint32_t pt = 0; pt < shared_len_; pt++) {
            double this_lab = is_primal<O>::value ? O::lab_transform(x.labs[pt]) : 0.0;
            cost += O::f_cost(p, shared_cached_[pt], this_lab);
        }
        cost /= static_cast<double>(num_partitions);
        for (uint32_t pt = 0; pt < model_len_; pt++) {
            double this_lab = is_primal<O>::value ? 0.0 : O::lab_transform(x.labs[pt]);
            cost += O::g_cost(p, model_[pt], this_lab);
        }
        // add bias term
        if (is_primal<O>::value && add_bias_ && partition_id == 0) {
            cost += O::g_cost(p, bias_, 0.0);
        }
        return cost;
    }

    // Get model (primal)
    template <class O>
    typename std::enable_if<is_primal<O>::value, void>::type get_model_impl(double* const output_model)
    {

        uint32_t num_ft         = data_->get_num_ft();
        uint32_t this_pt_offset = data_->get_this_pt_offset();
        uint32_t partition_id   = data_->get_partition_id();

        if (add_bias_) {
            if (partition_id == 0) {
                output_model[num_ft - 1] = bias_;
            }
        }

        for (uint32_t pt = 0; pt < model_len_; pt++) {
            output_model[this_pt_offset + pt] = model_[pt];
        }
    }

    // Get model (dual)
    template <class O>
    typename std::enable_if<!is_primal<O>::value, void>::type get_model_impl(double* const output_model)
    {

        auto p = static_cast<O*>(obj_)->get_params();

        uint32_t num_partitions = data_->get_num_partitions();

        for (uint32_t ft = 0; ft < shared_len_; ft++) {
            output_model[ft] = O::shared_to_primal(p, shared_cached_[ft]) / static_cast<double>(num_partitions);
        }
    }

    template <class O>
    typename std::enable_if<is_sparse<O>::value, void>::type get_nz_coordinates_impl(std::vector<uint32_t>& nz_inds)
    {
        uint32_t this_pt_offset = data_->get_this_pt_offset();
        double   tol            = 1e-5;
        for (uint32_t i = 0; i < model_len_; i++) {
            if (fabs(model_[i]) > tol) {
                nz_inds.push_back(this_pt_offset + i);
            }
        }
    }

    template <class O>
    typename std::enable_if<!is_sparse<O>::value, void>::type get_nz_coordinates_impl(std::vector<uint32_t>& nz_inds)
    {
    }
};

}

#endif
