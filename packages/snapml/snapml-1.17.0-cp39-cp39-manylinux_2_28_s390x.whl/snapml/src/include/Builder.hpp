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

#ifndef BUILDER
#define BUILDER

#include "Utils.hpp"
#include "Dataset.hpp"
#include "Model.hpp"
#include <cassert>
namespace tree {

template <typename M> class Builder {

public:
    Builder(glm::Dataset* data, const uint32_t num_classes)
        : data_(data)
        , num_ex_(data->get_num_ex())
        , num_ft_(data->get_num_ft())
        , num_classes_(num_classes)
    {
        feature_importances_.resize(num_ft_, 0.0);
    }

    // virtual dtor
    virtual ~Builder() { }

    // initialize builder
    virtual void init() = 0;

    // do the builder
    virtual void build(const float* const sample_weight, const float* const sample_weight_val = nullptr,
                       const double* const labels = nullptr)
        = 0;

    // pull out feature importances
    void get_feature_importances(double* const out, uint32_t num_ft_chk)
    {
        assert(num_ft_chk == feature_importances_.size());
        double Z = 0.0;
        for (uint32_t i = 0; i < num_ft_chk; i++) {
            out[i] = feature_importances_[i];
            Z += out[i];
        }
        if (Z > 0) {
            for (uint32_t i = 0; i < num_ft_chk; i++) {
                out[i] /= Z;
            }
        }
    }

    virtual size_t get_full_feature_importances_size() { return 0; }
    virtual void   get_full_feature_importances(double* const out, uint32_t len) { }

    double get_feature_importance(uint32_t ft) { return feature_importances_[ft]; }

    std::shared_ptr<M> get_model() { return model_; }

protected:
    glm::Dataset*       data_;
    const uint32_t      num_ex_;
    const uint32_t      num_ft_;
    const uint32_t      num_classes_;
    std::vector<double> feature_importances_;
    std::shared_ptr<M>  model_;
};

}

#endif
