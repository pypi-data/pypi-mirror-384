/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2018, 2021
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Thomas Parnell
 *                Nikolas Ioannou
 *
 * End Copyright
 ********************************************************************/

#ifndef HIST_SOLVER_GPU_FACTORY
#define HIST_SOLVER_GPU_FACTORY

#include "HistSolver.hpp"
#include <memory>
#include "TreeInvariants.hpp"
#include "DenseDatasetInt.hpp"

namespace tree {

class HistSolverGPUFactory {

public:
    template <class N>
    std::shared_ptr<tree::HistSolver<N>>
    make(const std::shared_ptr<glm::TreeInvariants<glm::DenseDataset>>& tree_invariants, const uint32_t gpu_id);
};

}

#endif