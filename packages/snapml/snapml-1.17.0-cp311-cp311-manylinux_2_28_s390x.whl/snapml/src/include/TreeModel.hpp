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
 * Authors      : Celestine Duenner
 *                Andreea Anghel
 *                Thomas Parnell
 *                Nikolas Ioannou
 *                Nikolaos Papandreou
 *                Milos Stanisavljevic
 *
 * End Copyright
 ********************************************************************/

#ifndef TREE_MODEL
#define TREE_MODEL

#include "Model.hpp"
#include "TreeTypes.hpp"
#include "DecisionTreeModel.hpp"
#include <cassert>

namespace tree {

struct TreeModel : public Model {

    PACK(struct node_t {
        float    threshold;
        uint32_t feature : 31;
        uint32_t is_leaf : 1;
        union {
            struct {
                uint32_t left_child;
                uint32_t right_child;
                // int32_t node_index;
            };
            // leaf information
            // bool is_leaf;
            struct {
                float leaf_label;
                float unused;
            };
        };
        float* leaf_proba;
    });

    TreeModel(snapml::task_t task_, uint32_t num_classes_, uint32_t num_nodes_)
        : task(task_)
        , num_classes(num_classes_)
        , num_nodes(num_nodes_)
    {
        nodes.resize(num_nodes);
        num_leaves = 0;
    }

    TreeModel()
        : task(snapml::task_t::classification)
        , num_classes(0)
        , num_nodes(0)
        , num_leaves(0)
        , nodes({})
    {
    }

    ~TreeModel()
    {

        if (num_classes <= 2)
            return;

        for (uint32_t i = 0; i < num_nodes; i++) {
            if (nodes[i].is_leaf) {
                assert(nodes[i].leaf_proba != nullptr);
                delete[] nodes[i].leaf_proba;
            }
        }
    }

    void get(tree::Model::Getter& getter) override
    {
        getter.add(task);
        getter.add(num_classes);
        getter.add(num_nodes);
        getter.add(num_leaves);

        for (uint32_t i = 0; i < num_nodes; i++) {
            getter.add(nodes[i]);
            if (nodes[i].is_leaf && num_classes > 2) {
                getter.add(nodes[i].leaf_proba[0], (num_classes - 1) * sizeof(float));
            }
        }
    }

    void put(tree::Model::Setter& setter, const uint64_t len) override
    {
        const uint64_t offset_begin = setter.get_offset();

        setter.check_before(len);

        setter.get(&task);
        setter.get(&num_classes);
        setter.get(&num_nodes);
        setter.get(&num_leaves);

        nodes.resize(num_nodes);
        for (uint32_t i = 0; i < num_nodes; i++) {
            setter.get(&nodes[i]);
            if (nodes[i].is_leaf && num_classes > 2) {
                nodes[i].leaf_proba = new float[num_classes - 1];
                setter.get(&nodes[i].leaf_proba[0], (num_classes - 1) * sizeof(float));
            }
        }

        setter.check_after(offset_begin, len);
    }

    snapml::task_t      task;
    uint32_t            num_classes;
    uint32_t            num_nodes;
    uint32_t            num_leaves;
    std::vector<node_t> nodes;
};

class DecisionTreeModelInt : public snapml::DecisionTreeModel {
public:
    DecisionTreeModelInt()
        : snapml::DecisionTreeModel()
    {
    }
    DecisionTreeModelInt(std::shared_ptr<tree::TreeModel> model) { model_ = model; }
    const std::shared_ptr<tree::TreeModel> get_internal() const { return model_; };
};

}

#endif
