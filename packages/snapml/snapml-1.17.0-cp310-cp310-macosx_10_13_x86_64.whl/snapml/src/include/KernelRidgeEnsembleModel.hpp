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
 * Authors      : Andreea Anghel
 *                Celestine Duenner
 *                Thomas Parnell
 *                Nikolas Ioannou
 *                Jan van Lunteren
 *                Milos Stanisavljevic
 *
 * End Copyright
 ********************************************************************/

#ifndef KERNEL_RIDGE_ENSEMBLE_MODEL
#define KERNEL_RIDGE_ENSEMBLE_MODEL

#include "Model.hpp"
#include "RBFSampler.hpp"
#include <cassert>

namespace tree {

struct KernelRidgeEnsembleModel : public Model {

    KernelRidgeEnsembleModel(uint32_t n_components_)
        : task(snapml::task_t::regression)
        , num_classes(2)
        , n_components(n_components_)

    {
        n_models = 0;
    }

    KernelRidgeEnsembleModel()
        : task(snapml::task_t::regression)
        , num_classes(2)
        , n_models(0)
        , n_components(10)
    {
    }

    ~KernelRidgeEnsembleModel() { }

    void insert_linear(const float offset, const std::vector<float> coef)
    {
        assert(coef.size() == n_components);
        n_models++;
        offsets.push_back(offset);
        coefs.push_back(coef);
    }

    void resize(uint32_t size)
    {
        n_models = size;
        offsets.resize(size);
        coefs.resize(size);
    }

    void get(tree::Model::Getter& getter) override
    {
        getter.add(n_models);
        getter.add(n_components);
        getter.add(offsets[0], n_models * sizeof(float));

        for (uint32_t i = 0; i < n_models; i++) {
            getter.add(coefs[i][0], coefs[i].size() * sizeof(float));
        }
    }

    void put(tree::Model::Setter& setter, const uint64_t len) override
    {
        const uint64_t offset_begin = setter.get_offset();

        setter.check_before(len);

        setter.get(&n_models);
        setter.get(&n_components);

        offsets.resize(n_models);
        setter.get(&offsets[0], n_models * sizeof(float));

        coefs.resize(n_models);
        for (uint32_t i = 0; i < n_models; i++) {
            coefs[i].resize(n_components);
            setter.get(&coefs[i][0], n_components * sizeof(float));
        }

        setter.check_after(offset_begin, len);
    }

    void aggregate(const std::vector<float> data, double* preds, uint32_t num_threads = 1) const
    {
        aggregate_impl(data, preds, num_threads);
    }

    const snapml::task_t task;
    const uint32_t       num_classes;

    uint32_t                        n_models;
    uint32_t                        n_components;
    std::vector<float>              offsets;
    std::vector<std::vector<float>> coefs;

private:
    void aggregate_impl(const std::vector<float> data, double* preds, uint32_t num_threads = 1) const
    {

        const uint32_t num_ex = data.size() / n_components;

        omp_set_num_threads(num_threads);
        OMP::parallel_for<int32_t>(0, num_ex, [this, &data, &num_ex, &preds](const int32_t& ex) {
            double tmp = 0.0;
            for (uint32_t j = 0; j < n_models; j++) {
                tmp += offsets[j];
                for (uint32_t k = 0; k < n_components; k++) {
                    uint64_t ind = static_cast<uint64_t>(k) * static_cast<uint64_t>(num_ex) + static_cast<uint64_t>(ex);
                    tmp += data[ind] * coefs[j][k];
                }
            }
            preds[ex] += tmp;
        });
    }
};

}

#endif
