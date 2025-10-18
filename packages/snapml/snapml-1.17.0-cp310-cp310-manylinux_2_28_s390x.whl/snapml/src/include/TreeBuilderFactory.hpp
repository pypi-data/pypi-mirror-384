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
 *
 * End Copyright
 ********************************************************************/

#ifndef TREE_BUILDER_FACTORY
#define TREE_BUILDER_FACTORY

#include "HistSolver.hpp"
#include <memory>
#include "TreeInvariants.hpp"
#include "DenseDatasetInt.hpp"

#include "ExactTreeBuilder.hpp"
#include "CpuHistTreeBuilder.hpp"
#include "GpuHistTreeBuilder.hpp"

namespace tree {

class TreeBuilderFactory {

public:
    template <class B>
    inline std::shared_ptr<B> make(glm::DenseDataset* data, snapml::DecisionTreeParams params,
                                   std::shared_ptr<glm::TreeInvariants<glm::DenseDataset>> tree_invariants,
                                   std::shared_ptr<HistSolver<typename B::node_type>>      hist_solver_gpu = nullptr)
    {
        return std::make_shared<B>(data, params, tree_invariants);
    }
};

template <>
inline std::shared_ptr<GpuHistTreeBuilder<tree::ClTreeNode>>
TreeBuilderFactory::make<GpuHistTreeBuilder<tree::ClTreeNode>>(
    glm::DenseDataset* data, snapml::DecisionTreeParams params,
    std::shared_ptr<glm::TreeInvariants<glm::DenseDataset>> tree_invariants,
    std::shared_ptr<HistSolver<tree::ClTreeNode>>           hist_solver_gpu)
{
    return std::make_shared<GpuHistTreeBuilder<tree::ClTreeNode>>(data, params, tree_invariants, hist_solver_gpu);
}

template <>
inline std::shared_ptr<GpuHistTreeBuilder<tree::RegTreeNode>>
TreeBuilderFactory::make<GpuHistTreeBuilder<tree::RegTreeNode>>(
    glm::DenseDataset* data, snapml::DecisionTreeParams params,
    std::shared_ptr<glm::TreeInvariants<glm::DenseDataset>> tree_invariants,
    std::shared_ptr<HistSolver<tree::RegTreeNode>>          hist_solver_gpu)
{
    return std::make_shared<GpuHistTreeBuilder<tree::RegTreeNode>>(data, params, tree_invariants, hist_solver_gpu);
}

template <>
inline std::shared_ptr<GpuHistTreeBuilder<tree::MultiClTreeNode>>
TreeBuilderFactory::make<GpuHistTreeBuilder<tree::MultiClTreeNode>>(
    glm::DenseDataset* data, snapml::DecisionTreeParams params,
    std::shared_ptr<glm::TreeInvariants<glm::DenseDataset>> tree_invariants,
    std::shared_ptr<HistSolver<tree::MultiClTreeNode>>      hist_solver_gpu)
{
    return nullptr;
}

}

#endif
