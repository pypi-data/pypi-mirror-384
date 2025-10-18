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
#include "RandomForestParams.hpp"
#include "RandomForestModel.hpp"

namespace tree {
struct ForestModel;
template <class> class Builder;
}

namespace snapml {

//! @ingroup c-api
class RandomForestBuilder {

public:
    RandomForestBuilder(snapml::DenseDataset data, const snapml::RandomForestParams* params);

    void                      init();
    double                    get_feature_importance(uint32_t ft);
    void                      get_feature_importances(double* const out, uint32_t num_ft_chk);
    void                      build(const float* const sample_weight, const float* const sample_weight_val = nullptr,
                                    const double* const labels = nullptr);
    snapml::RandomForestModel get_model();

private:
    std::shared_ptr<tree::Builder<tree::ForestModel>> builder_;
    std::shared_ptr<std::mutex>                       mtx_;
};

}
