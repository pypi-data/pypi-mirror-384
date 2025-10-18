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

#ifndef GLM_DUAL_LOGISTIC_REGRESSION
#define GLM_DUAL_LOGISTIC_REGRESSION

#include "Objective.hpp"

namespace glm {

// Dual Logistic Regresion
class DualLogisticRegression : public Objective {

public:
    struct params_t {
        double lambda;
        double w_pos;
        double w_neg;
    };

    DualLogisticRegression(double lambda, double w_pos, double w_neg)
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
        return shared * shared / 2.0 / p.lambda;
    }

    __host__ __device__ static double g_cost(params_t p, double model, double label)
    {
        double weight = (label == +1) ? p.w_pos : p.w_neg;
        double p1     = model * label / weight;
        double p0     = 1.0 - p1;
        p1            = fmax(p1, 1e-15);
        p0            = fmax(p0, 1e-15);
        return weight * (p0 * log(p0) + p1 * log(p1));
    }

    __host__ __device__ static double df1(params_t p, double shared, double label) { return shared / p.lambda; }

    __host__ __device__ static double df2(params_t p, double shared, double label) { return 1.0 / p.lambda; }

    __host__ __device__ static double dg1(params_t p, double model, double label)
    {
        double weight = (label == +1) ? p.w_pos : p.w_neg;
        double p1     = model * label / weight;
        double p0     = 1.0 - p1;
        return label * log(p1) - label * log(p0);
    }

    __host__ __device__ static double dg2(params_t p, double model, double label)
    {
        double weight = (label == +1) ? p.w_pos : p.w_neg;
        double tmp    = model * label;
        return 1.0 / tmp + 1.0 / (weight - tmp);
    }

    __host__ __device__ static void apply_constraints(params_t p, double& model, double label, double denom)
    {
        const double SMALL  = 0.0001;
        double       weight = (label == +1) ? p.w_pos : p.w_neg;
        double       ulim   = (label == +1) ? (weight - SMALL) : (-SMALL);
        double       llim   = (label == +1) ? (SMALL) : (-weight + SMALL);
        model               = fmin(model, ulim);
        model               = fmax(model, llim);
    }

    __host__ __device__ static double shared_to_primal(params_t p, double shared) { return shared / p.lambda; }

    __host__ __device__ static double init_model(params_t p, double label) { return label * 0.001; }

    __host__ __device__ static bool shrinkage(params_t p, double model, double label, double num_min, double num_max,
                                              double& num)
    {
        return false;
    }

    params_t get_params() { return params_; }

private:
    params_t params_;
};

}

#endif
