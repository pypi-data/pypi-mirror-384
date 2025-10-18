/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2018, 2019, 2020, 2021
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      :
 *
 * End Copyright
 ********************************************************************/

#include <mutex>

#include "DecisionTreeBuilder.hpp"
#include "DecisionTreeBuilderInt.hpp"
#include "ExactTreeBuilder.hpp"
#include "GpuHistTreeBuilder.hpp"
#include "CpuHistTreeBuilder.hpp"
#include "TreeNode.hpp"

namespace snapml {

DecisionTreeBuilder::DecisionTreeBuilder(snapml::DenseDataset data, const snapml::DecisionTreeParams* params)
    : mtx_(std::shared_ptr<std::mutex>(new std::mutex()))
{
    glm::DenseDataset* data_p = data.get().get();

    if (params->task == snapml::task_t::classification) {
        if (params->num_classes == 2) {
            if (!params->use_histograms) {
                builder_ = std::make_shared<tree::ExactTreeBuilder<tree::ClTreeNode>>(data_p, *params);
            } else {
                if (params->use_gpu) {
                    builder_ = std::make_shared<tree::GpuHistTreeBuilder<tree::ClTreeNode>>(data_p, *params);
                } else {
                    builder_ = std::make_shared<tree::CpuHistTreeBuilder<tree::ClTreeNode>>(data_p, *params);
                }
            }
        } else {
            if (!params->use_histograms) {
                builder_ = std::make_shared<tree::ExactTreeBuilder<tree::MultiClTreeNode>>(data_p, *params);
            } else {
                if (params->use_gpu) {
                    throw std::runtime_error("Multi-class tree building is not currently supported on GPU.");
                } else {
                    builder_ = std::make_shared<tree::CpuHistTreeBuilder<tree::MultiClTreeNode>>(data_p, *params);
                }
            }
        }
    } else {
        if (!params->use_histograms) {
            builder_ = std::make_shared<tree::ExactTreeBuilder<tree::RegTreeNode>>(data_p, *params);
        } else {
            if (params->use_gpu) {
                builder_ = std::make_shared<tree::GpuHistTreeBuilder<tree::RegTreeNode>>(data_p, *params);
            } else {
                builder_ = std::make_shared<tree::CpuHistTreeBuilder<tree::RegTreeNode>>(data_p, *params);
            }
        }
    }
}

snapml::DecisionTreeModel DecisionTreeBuilder::get_model()
{
    std::unique_lock<std::mutex> lock(*mtx_);
    tree::DecisionTreeModelInt   dtmi = tree::DecisionTreeModelInt(builder_->get_model());
    return *static_cast<snapml::DecisionTreeModel*>(&dtmi);
}

void DecisionTreeBuilder::init()
{
    std::unique_lock<std::mutex> lock(*mtx_);
    builder_->init();
}

double DecisionTreeBuilder::get_feature_importance(uint32_t ft)
{
    std::unique_lock<std::mutex> lock(*mtx_);
    return builder_->get_feature_importance(ft);
}

void DecisionTreeBuilder::get_feature_importances(double* const out, uint32_t num_ft_chk)
{
    std::unique_lock<std::mutex> lock(*mtx_);
    return builder_->get_feature_importances(out, num_ft_chk);
}

void DecisionTreeBuilder::build(const float* const sample_weight, const float* const sample_weight_val,
                                const double* const labels)
{
    std::unique_lock<std::mutex> lock(*mtx_);
    builder_->build(sample_weight, sample_weight_val, labels);
}

}
