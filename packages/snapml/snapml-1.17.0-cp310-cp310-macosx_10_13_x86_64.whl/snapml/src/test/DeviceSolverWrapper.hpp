/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2020
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
#ifndef _LIBGLM_DEVICE_SOLVER_WRAPPER_
#define _LIBGLM_DEVICE_SOLVER_WRAPPER_

#include "Solver.hpp"
#include "DenseDatasetInt.hpp"
#include <memory>

template <class O>
std::shared_ptr<glm::Solver> make_device_solver_(glm::DenseDataset* data, O* obj, double sigma, double tol,
                                                 const std::vector<unsigned int>& device_ids, uint32_t num_threads,
                                                 bool add_bias, double bias_val);

#endif // _LIBGLM_DEVICE_SOLVER_WRAPPER_
