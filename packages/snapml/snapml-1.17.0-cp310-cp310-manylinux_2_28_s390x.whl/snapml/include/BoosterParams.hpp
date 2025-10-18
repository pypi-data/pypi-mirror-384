/*********************************************************************
 *
 * Licensed Materials - Property of IBM
 *
 * (C) Copyright IBM Corp. 2022, 2023. All Rights Reserved.

 * US Government Users Restricted Rights - Use, duplication or
 * disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
 *
 ********************************************************************/

#pragma once

#include <vector>

namespace snapml {

//! @ingroup c-api
struct BoosterParams {
    uint32_t n_threads    = 1;                                                          // number of threads
    uint32_t n_regressors = 10;                                                         // number of regressors
    uint32_t num_classes  = 2;                                                          // number of classes
    enum class objective_t { mse, logloss, cross_entropy, softmax, poisson, quantile }; // define different objectives
    objective_t           objective             = objective_t::mse;                     // objective function
    double                max_delta_step        = 0.0;   // regularization term for poisson regression
    double                alpha                 = 0.5;   // quantile
    double                min_h_quantile        = 0.0;   // regularization term for quantile regression
    uint32_t              min_max_depth         = 1;     // minimum max depth
    uint32_t              max_max_depth         = 6;     // maximum max depth
    uint32_t              early_stopping_rounds = 10;    // early stopping rounds
    uint32_t              random_state          = 42;    // random state
    double                base_prediction       = 0.0;   // base prediction
    double                learning_rate         = 0.1;   // learning rate
    bool                  verbose               = false; // verbose mode
    bool                  enable_profile        = false; // enable profiling
    bool                  use_gpu               = false; // use gpu
    std::vector<uint32_t> gpu_ids               = {};    // GPU IDs
    bool                  aggregate_importances = true;  // aggregate feature importances
    bool                  use_histograms        = false; // use histograms
    uint32_t              hist_nbins            = 64;    // number of bins
    float    colsample_bytree   = 1.0; // percentage of features used at each iteration: 1.0 = use all features
    float    subsample          = 1.0; // percentage of examples used at each iteration: 1.0 = use all examples
    float    select_probability = 1.0; // tree selection probability
    double   lambda             = 0.0; // L2-regularization parameter
    float    gamma              = 1.0; // parameter of RBF kernel: exp(-gamma * x^2)
    uint32_t n_components       = 10;  // the dimensionality of the computed feature space
    double   regularizer        = 1.0;
    bool     fit_intercept      = false;
};

}
