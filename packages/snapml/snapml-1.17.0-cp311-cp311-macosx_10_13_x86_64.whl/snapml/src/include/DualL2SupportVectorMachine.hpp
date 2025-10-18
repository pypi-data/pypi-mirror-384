/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2021
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

#ifndef GLM_DUAL_L2_SUPPORT_VECTOR_MACHINE
#define GLM_DUAL_L2_SUPPORT_VECTOR_MACHINE

#include "Objective.hpp"

namespace glm {

// Dual L2 Support Vector Machine
class DualL2SupportVectorMachine : public Objective {

public:
    struct params_t {
        double lambda;
        double w_pos;
        double w_neg;
    };

    DualL2SupportVectorMachine(double lambda, double w_pos, double w_neg)
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
        return 0.25 * model * model / weight - model * label;
    }

    __host__ __device__ static double df1(params_t p, double shared, double label) { return shared / p.lambda; }

    __host__ __device__ static double df2(params_t p, double shared, double label) { return 1.0 / p.lambda; }

    __host__ __device__ static double dg1(params_t p, double model, double label)
    {
        double weight = (label == +1) ? p.w_pos : p.w_neg;
        return 0.5 * model / weight - label;
    }

    __host__ __device__ static double dg2(params_t p, double model, double label)
    {
        double weight = (label == +1) ? p.w_pos : p.w_neg;
        return 0.5 / weight;
    }

    __host__ __device__ static void apply_constraints(params_t p, double& model, double label, double denom)
    {
        if (label == +1.0) {
            model = fmax(model, 0.0);
        } else {
            model = fmin(model, 0.0);
        }
    }

    __host__ __device__ static double shared_to_primal(params_t p, double shared) { return shared / p.lambda; }

    __host__ __device__ static double init_model(params_t p, double label) { return 0.0; }

    __host__ __device__ static bool shrinkage(params_t p, double model, double label, double num_min, double num_max,
                                              double& num)
    {

        double tmp1 = model * label;

        bool lbound = (tmp1 == 0);

        bool lshrink = lbound && (num > num_max);

        if (lbound) {
            num = fmin(0.0, num);
        }

        return lshrink;
    }

    params_t get_params() { return params_; }

private:
    params_t params_;
};

template <> struct is_sparse<DualL2SupportVectorMachine> {
    static const bool value = true;
};

}

#endif
