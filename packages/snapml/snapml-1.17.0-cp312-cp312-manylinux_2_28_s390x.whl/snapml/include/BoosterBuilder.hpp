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

#include "DenseDataset.hpp"
#include "BoosterParams.hpp"
#include "BoosterModel.hpp"

namespace tree {
struct BoosterModel;
template <class> class Builder;
}

namespace snapml {

//! @ingroup c-api
class BoosterBuilder {

public:
    BoosterBuilder(snapml::DenseDataset data, snapml::DenseDataset val_data, snapml::BoosterParams params);

    void                 init();
    double               get_feature_importance(uint32_t ft);
    void                 get_feature_importances(double* const out, uint32_t num_ft_chk);
    size_t               get_full_feature_importances_size();
    void                 get_full_feature_importances(double* const out, uint32_t len);
    void                 build(const float* const sample_weight, const float* const sample_weight_val = nullptr,
                               const double* const labels = nullptr);
    snapml::BoosterModel get_model();

private:
    std::shared_ptr<tree::Builder<tree::BoosterModel>> builder_;
    std::shared_ptr<std::mutex>                        mtx_;
};

}
