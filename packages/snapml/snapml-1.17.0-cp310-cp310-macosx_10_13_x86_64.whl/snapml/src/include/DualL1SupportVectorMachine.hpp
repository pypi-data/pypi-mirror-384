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

#ifndef GLM_DUAL_L1_SUPPORT_VECTOR_MACHINE
#define GLM_DUAL_L1_SUPPORT_VECTOR_MACHINE

#include "Objective.hpp"

namespace glm {

// Dual L1 Support Vector Machine
class DualL1SupportVectorMachine : public Objective {

public:
    struct params_t {
        double lambda;
        double w_pos;
        double w_neg;
    };

    DualL1SupportVectorMachine(double lambda, double w_pos, double w_neg)
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

    __host__ __device__ static double g_cost(params_t p, double model, double label) { return -model * label; }

    __host__ __device__ static double df1(params_t p, double shared, double label) { return shared / p.lambda; }

    __host__ __device__ static double df2(params_t p, double shared, double label) { return 1.0 / p.lambda; }

    __host__ __device__ static double dg1(params_t p, double model, double label) { return -label; }

    __host__ __device__ static double dg2(params_t p, double model, double label) { return 0.0; }

    __host__ __device__ static void apply_constraints(params_t p, double& model, double label, double denom)
    {
        double weight = (label == +1) ? p.w_pos : p.w_neg;
        double ulim   = (label == +1) ? (weight) : 0.0;
        double llim   = (label == +1) ? 0.0 : (-weight);
        model         = fmin(model, ulim);
        model         = fmax(model, llim);
    }

    __host__ __device__ static double shared_to_primal(params_t p, double shared) { return shared / p.lambda; }

    __host__ __device__ static double init_model(params_t p, double label) { return 0.0; }

    __host__ __device__ static bool shrinkage(params_t p, double model, double label, double num_min, double num_max,
                                              double& num)
    {

        double weight = (label == +1) ? p.w_pos : p.w_neg;
        double tmp1   = model * label;

        bool lbound = (tmp1 == 0);
        bool ubound = (tmp1 == weight);

        bool lshrink = lbound && (num > num_max);
        bool ushrink = ubound && (num < num_min);

        if (lbound) {
            num = fmin(0.0, num);
        }
        if (ubound) {
            num = fmax(0.0, num);
        }

        return (lshrink || ushrink);
    }

    params_t get_params() { return params_; }

private:
    params_t params_;
};

template <> struct is_sparse<DualL1SupportVectorMachine> {
    static const bool value = true;
};

}

#endif
