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

#include "TreeTypes.hpp"

namespace snapml {

//! @ingroup c-api
struct RandomForestParams {
    uint32_t              n_threads        = 1;                              // number of threads
    snapml::task_t        task             = snapml::task_t::classification; // define task type
    uint32_t              max_depth        = 0;                              // maximum tree depth
    snapml::split_t       split_criterion  = snapml::split_t::gini;          // define split criterion
    uint32_t              min_samples_leaf = 1;                              // minimum number of samples in a leaf
    uint32_t              random_state     = 0;                              // random state
    bool                  bootstrap        = false;                          // is bootstrapping used?
    uint32_t              max_features     = 0;     // maximum number of features if it is not provided from dataset
    bool                  use_histograms   = false; // use histograms
    uint32_t              hist_nbins       = 64;    // number of bins
    bool                  use_gpu          = false; // use gpu
    uint32_t              verbose          = 0;     // verbose mode
    uint32_t              num_classes      = 2;     // number of classes
    uint32_t              n_trees          = 10;    // number of trees
    std::vector<uint32_t> gpu_ids;
    bool                  enable_profile = false; // enable profiling
};

}
