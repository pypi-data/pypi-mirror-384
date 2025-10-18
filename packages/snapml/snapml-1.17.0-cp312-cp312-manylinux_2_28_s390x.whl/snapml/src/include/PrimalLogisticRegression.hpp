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

#ifndef GLM_PRIMAL_LOGISTIC_REGRESSION
#define GLM_PRIMAL_LOGISTIC_REGRESSION

#include <cmath>
#include "Traits.hpp"
#include "Objective.hpp"

namespace glm {

// Primal Logistic Regresion
class PrimalLogisticRegression : public Objective {

public:
    struct params_t {
        double lambda;
        double w_pos;
        double w_neg;
    };

    PrimalLogisticRegression(double lambda, double w_pos, double w_neg)
    {
        params_.lambda = lambda;
        params_.w_pos  = w_pos;
        params_.w_neg  = w_neg;
    }

    __host__ __device__ static double lab_transform(double lab)
    {
        double out = (lab > 0) ? +1.0 : -1.0;
        return out;
    }

    __host__ __device__ static double f_cost(params_t p, double shared, double label)
    {
        double tmp    = label * shared;
        double weight = (label == +1) ? p.w_pos : p.w_neg;
        return weight * log(1.0 + exp(-tmp));
    }

    __host__ __device__ static double g_cost(params_t p, double model, double label)
    {
        return p.lambda / 2.0 * model * model;
    }

    __host__ __device__ static double df1(params_t p, double shared, double label)
    {
        double weight = (label == +1) ? p.w_pos : p.w_neg;
        double tmp    = exp(-label * shared);
        return -label * weight * tmp / (1.0 + tmp);
    }

    __host__ __device__ static double df2(params_t p, double shared, double label)
    {
        double weight = (label == +1) ? p.w_pos : p.w_neg;
        double tmp    = exp(-label * shared);
        double tmp1   = 1.0 + tmp;
        return weight * tmp / tmp1 / tmp1;
    }

    __host__ __device__ static double dg1(params_t p, double model, double label) { return p.lambda * model; }

    __host__ __device__ static double dg2(params_t p, double model, double label) { return p.lambda; }

    __host__ __device__ static void apply_constraints(params_t p, double model, double label, double denom)
    {
        // no constraint for primal LR
    }

    params_t get_params() { return params_; }

    __host__ __device__ static double init_model(params_t p, double this_lab) { return 0.0; }

    __host__ __device__ static bool shrinkage(params_t p, double model, double label, double num_min, double num_max,
                                              double& num)
    {
        return false;
    }

private:
    params_t params_;
};

template <> struct is_primal<PrimalLogisticRegression> {
    static const bool value = true;
};

}

#endif
