
/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2018, 2020, 2021
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
 *                Andreea Anghel
 *                Nikolas Ioannou
 *                Nikolaos Papandreou
 *                Gummadi Ravi
 *                Josiah Sathiadass
 *                Sangeeth Keeriyadath
 *                Pradipta Ghosh
 *
 * End Copyright
 ********************************************************************/

#include "GPUUtils.hpp"
#include "HistSolverGPUFactory.hpp"
#include "DenseDatasetInt.hpp"
#include "HistSolverGPU.hpp"

namespace tree {

template <>
std::shared_ptr<tree::HistSolver<tree::RegTreeNode>> HistSolverGPUFactory::make<tree::RegTreeNode>(
    const std::shared_ptr<glm::TreeInvariants<glm::DenseDataset>>& tree_invariants, const uint32_t gpu_id)
{
    return std::make_shared<tree::HistSolverGPU<glm::DenseDataset, tree::RegTreeNode>>(tree_invariants, gpu_id);
}

template <>
std::shared_ptr<tree::HistSolver<tree::ClTreeNode>> HistSolverGPUFactory::make<tree::ClTreeNode>(
    const std::shared_ptr<glm::TreeInvariants<glm::DenseDataset>>& tree_invariants, const uint32_t gpu_id)
{
    return std::make_shared<tree::HistSolverGPU<glm::DenseDataset, tree::ClTreeNode>>(tree_invariants, gpu_id);
}

template <>
std::shared_ptr<tree::HistSolver<tree::MultiClTreeNode>> HistSolverGPUFactory::make<tree::MultiClTreeNode>(
    const std::shared_ptr<glm::TreeInvariants<glm::DenseDataset>>& tree_invariants, const uint32_t gpu_id)
{
    return nullptr;
}

}
