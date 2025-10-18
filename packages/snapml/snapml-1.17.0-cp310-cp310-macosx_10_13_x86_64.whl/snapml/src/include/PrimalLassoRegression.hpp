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

#ifndef GLM_PRIMAL_LASSO_REGRESSION
#define GLM_PRIMAL_LASSO_REGRESSION

#include <cmath>
#include "Traits.hpp"
#include "Objective.hpp"

namespace glm {

// Primal Lasso Regresion
class PrimalLassoRegression : public Objective {

public:
    struct params_t {
        double lambda;
        double w_pos;
        double w_neg;
    };

    PrimalLassoRegression(double lambda, double w_pos, double w_neg)
    {
        params_.lambda = lambda;
        params_.w_pos  = w_pos;
        params_.w_neg  = w_neg;
    }

    __host__ __device__ static double lab_transform(double lab) { return lab; }

    __host__ __device__ static double f_cost(params_t p, double shared, double label)
    {
        double tmp    = shared - label;
        double weight = (label == +1) ? p.w_pos : p.w_neg;
        return 0.5 * weight * tmp * tmp;
    }

    __host__ __device__ static double g_cost(params_t p, double model, double label) { return p.lambda * fabs(model); }

    __host__ __device__ static double df1(params_t p, double shared, double label)
    {
        double weight = (label == +1) ? p.w_pos : p.w_neg;
        return weight * (shared - label);
    }

    __host__ __device__ static double df2(params_t p, double shared, double label)
    {
        double weight = (label == +1) ? p.w_pos : p.w_neg;
        return weight;
    }

    __host__ __device__ static double dg1(params_t p, double model, double label) { return 0.0; }

    __host__ __device__ static double dg2(params_t p, double model, double label)
    {
        return 0.000001; // avoid den=0 in solver
    }

    __host__ __device__ static void apply_constraints(params_t p, double& model, double label, double denom)
    {
        // soft-thresholding for Lasso
        double tau  = p.lambda / denom;
        double sign = (model < 0) ? -1.0 : 1.0;
        model       = sign * fmax(0.0, fabs(model) - tau);
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

template <> struct is_primal<PrimalLassoRegression> {
    static const bool value = true;
};

template <> struct is_sparse<PrimalLassoRegression> {
    static const bool value = true;
};

}

#endif
