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

#include <mutex>
#include "DecisionTreeModel.hpp"
#include "DenseDataset.hpp"

namespace tree {
class TreePredictor;
}

namespace snapml {

//! @ingroup c-api
class DecisionTreePredictor {
public:
    DecisionTreePredictor(const snapml::DecisionTreeModel model);
    void apply(snapml::DenseDataset data, const uint32_t ex, uint32_t& leaf_idx, float& leaf_label) const;
    void predict(snapml::DenseDataset data, double* const preds, uint32_t num_threads = 1) const;
    void predict_proba(snapml::DenseDataset data, double* const preds, uint32_t num_threads = 1) const;

private:
    const std::shared_ptr<tree::TreePredictor> predictor_;
    std::shared_ptr<std::mutex>                mtx_;
};

}
