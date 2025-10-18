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

#ifndef SIMPLE_TREE_MODEL
#define SIMPLE_TREE_MODEL

#include "Model.hpp"
#include "TreeModel.hpp"

namespace tree {

struct SimpleTreeModel : public Model {

    SimpleTreeModel(const std::shared_ptr<TreeModel> in)
    {
        task        = in->task;
        num_classes = in->num_classes;
        num_nodes   = in->num_nodes;

        node_id.resize(num_nodes);
        node_is_leaf.resize(num_nodes);
        node_leaf_label.resize(num_nodes);
        node_feature.resize(num_nodes);
        node_threshold.resize(num_nodes);
        node_left_child.resize(num_nodes);
        node_right_child.resize(num_nodes);

        for (uint32_t i = 0; i < num_nodes; i++) {
            node_id[i]        = i;
            node_is_leaf[i]   = in->nodes[i].is_leaf;
            node_feature[i]   = in->nodes[i].feature;
            node_threshold[i] = in->nodes[i].threshold;
            if (node_is_leaf[i]) {
                if (num_classes <= 2)
                    node_leaf_label[i].push_back(in->nodes[i].leaf_label);
                else {
                    float sum = 0.0;
                    for (uint32_t k = 0; k < num_classes - 1; k++) {
                        node_leaf_label[i].push_back(in->nodes[i].leaf_proba[k]);
                        sum += in->nodes[i].leaf_proba[k];
                    }
                    node_leaf_label[i].push_back(1.0 - sum); // TO BE REMOVED
                }
                node_left_child[i]  = -1;
                node_right_child[i] = -1;
            } else {
                node_leaf_label[i].push_back(0.0);
                node_left_child[i]  = in->nodes[i].left_child;
                node_right_child[i] = in->nodes[i].right_child;
            }
        }
    }

    void get(tree::Model::Getter& getter) override
    {

        throw std::runtime_error(
            "SimpleTreeModels are just for testing; serialization/de-serialization API not implemented.");
    }

    void put(tree::Model::Setter& setter, const uint64_t len) override
    {

        throw std::runtime_error(
            "SimpleTreeModels are just for testing; serialization/de-serialization API not implemented.");
    }

    snapml::task_t                  task;
    uint32_t                        num_classes;
    uint32_t                        num_nodes;
    std::vector<uint32_t>           node_id;
    std::vector<bool>               node_is_leaf;
    std::vector<std::vector<float>> node_leaf_label;
    std::vector<uint32_t>           node_feature;
    std::vector<float>              node_threshold;
    std::vector<uint32_t>           node_left_child;
    std::vector<uint32_t>           node_right_child;
};

}

#endif
