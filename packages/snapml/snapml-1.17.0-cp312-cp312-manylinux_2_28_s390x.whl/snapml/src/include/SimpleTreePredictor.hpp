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

#ifndef SIMPLE_TREE_PREDICTOR
#define SIMPLE_TREE_PREDICTOR

#include "Predictor.hpp"
#include "SimpleTreeModel.hpp"

namespace tree {

class SimpleTreePredictor : public Predictor {

public:
    SimpleTreePredictor(const std::shared_ptr<SimpleTreeModel> model)
        : model_(model)
    {
        if (model_->num_classes > 2) {
            throw std::runtime_error("SimpleTree prediction not supported for multi-class classification tasks.");
        }
    }

    ~SimpleTreePredictor() { }

    void predict(glm::DenseDataset* const data, double* const preds, uint32_t num_threads = 1) const override
    {
        predict_impl(data, preds, false, num_threads);
    }

    void predict_proba(glm::DenseDataset* const data, double* const preds, uint32_t num_threads = 1) const override
    {
        predict_impl(data, preds, true, num_threads);
    }

    template <class T> void predict(glm::DenseDataset* const data, const uint32_t ex, T* const preds) const
    {
        if (model_->task == snapml::task_t::regression) {
            predict_leaf_labels(data, ex, &preds[ex]);
        } else {
            std::vector<T> class_proba(model_->num_classes - 1);
            predict_leaf_labels(data, ex, class_proba.data());
            preds[ex] = class_proba[0] > 0.5 ? +1.0 : -1.0;
        }
    }

    template <class T> void predict_proba(glm::DenseDataset* const data, const uint32_t ex, T* const preds) const
    {
        assert(model_->task == snapml::task_t::classification);
        predict_leaf_labels(data, ex, &preds[ex]);
    }

private:
    const std::shared_ptr<SimpleTreeModel> model_;

    void predict_impl(glm::DenseDataset* const data, double* const preds, bool proba, uint32_t num_threads = 1) const
    {

        uint32_t num_ex  = data->get_num_ex();
        uint32_t num_out = num_ex * (model_->num_classes - 1);

        std::fill_n(preds, num_out, 0.0);

        if (num_threads == 0) {
            num_threads = std::thread::hardware_concurrency();
        }

        omp_set_num_threads(num_threads);

        OMP::parallel_for<int32_t>(0, num_ex, [this, &preds, &data, &proba](const int32_t& ex) {
            if (proba) {
                predict_proba(data, ex, preds);
            } else {
                predict(data, ex, preds);
            }
        });
    }

    template <class T> void predict_leaf_labels(glm::DenseDataset* const data, const uint32_t ex, T* const preds) const
    {

        const uint64_t pos = glm::DenseDataset::get_ex_pt(data->get_data(), ex);

        uint32_t idx = 0;
        while (!model_->node_is_leaf[idx]) {

            const float val = glm::DenseDataset::lookup_w_pos(data->get_data(), ex, pos, model_->node_feature[idx]);

            if (val < model_->node_threshold[idx])
                idx = model_->node_left_child[idx];
            else
                idx = model_->node_right_child[idx];
        }

        preds[0] += static_cast<T>(model_->node_leaf_label[idx]);
    }
};

}

#endif