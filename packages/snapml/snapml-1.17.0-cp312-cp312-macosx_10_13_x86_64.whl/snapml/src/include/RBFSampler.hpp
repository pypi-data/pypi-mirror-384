/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2020, 2021
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Andreea Anghel
 *                Thomas Parnell
 *
 * End Copyright
 ********************************************************************/

#ifndef RBFSAMPLER
#define RBFSAMPLER

#include "Dataset.hpp"
#include <random>
#include <cmath>
#include "OMP.hpp"
#include <cassert>

// RBF kernel + Fourier Transform kernel approximation method
// https://scikit-learn.org/stable/modules/generated/sklearn.kernel_approximation.RBFSampler.html

struct RBFSamplerParams {
    float    gamma        = 1.0; // parameter of RBF kernel: exp(-gamma * x^2)
    uint32_t n_components = 10;  // the dimensionality of the computed feature space
    uint32_t random_state = 0;   // random state used to generate the feature map
    uint32_t n_threads    = 1;   // number of threads
};

class RBFSampler {

public:
    // ctor (when used for fit)
    RBFSampler(RBFSamplerParams params)
        : params_(params)
    {

        if (params_.n_components < 1) {
            throw std::runtime_error("[RBFSampler] invalid n_components parameter value given.");
        }

        random_weights_.resize(0);
        random_offsets_.resize(0);
    }

    // ctor (when used from python, for transform)
    RBFSampler(RBFSamplerParams params, const float* const random_weights, size_t weights_len,
               const float* const random_offsets, size_t offsets_len)
        : params_(params)
    {

        assert(offsets_len == params_.n_components);

        random_weights_.insert(random_weights_.end(), random_weights, random_weights + weights_len);
        random_offsets_.insert(random_offsets_.end(), random_offsets, random_offsets + offsets_len);
    }

    ~RBFSampler() { }

    // Python reference implementation
    // random_weights_ = (np.sqrt(2*self.gamma)*random_state_generator.normal(size=(n_features, self.n_components)))
    // random_offsets_ = random_state_generator.uniform(0, 2*np.pi, size=self.n_components)
    // the rbf fit function is currently not parallelized
    // loop parallelization and random number generation might create an undeterministic behavior
    void fit(uint32_t num_features)
    {

        std::mt19937                          random_generator = std::mt19937(params_.random_state);
        std::normal_distribution<float>       weights_distribution(0.0, 1.0);
        std::uniform_real_distribution<float> offsets_distribution(0.0, 2.0 * M_PI);

        random_weights_.resize(num_features * params_.n_components);
        // TODO: does the combination of loop parallelization and random number generation create undeterministic
        // behavior?
        for (uint32_t i = 0; i < num_features; i++) {
            for (uint32_t j = 0; j < params_.n_components; j++) {
                random_weights_[i * params_.n_components + j]
                    = std::sqrt(2 * params_.gamma) * weights_distribution(random_generator);
            }
        }

        random_offsets_.resize(params_.n_components);
        // TODO: does the combination of loop parallelization and random number generation create undeterministic
        // behavior?
        for (uint32_t i = 0; i < params_.n_components; i++) {
            random_offsets_[i] = offsets_distribution(random_generator);
        }
    }

    float* get_feature_map_weights() { return random_weights_.data(); }

    float* get_feature_map_offsets() { return random_offsets_.data(); }

    // Python reference implementation
    /*  x_ = np.dot(x, random_weights_)
        x_ += random_offsets_
        np.cos(x_, x_)
        x_ *= np.sqrt(2.)/np.sqrt(n_components)
    */

    typedef double reduction_t;

    template <class D> std::vector<float> transform(D* const data)
    {
        // set number of threads from param struct
        omp_set_num_threads(params_.n_threads);
        return transform_impl(data);
    }

    template <class D> std::vector<float> transform(D* const data, const uint32_t num_threads)
    {
        // set number of threads from  argument list
        omp_set_num_threads(num_threads);
        return transform_impl(data);
    }

    template <class D> std::vector<float> transform_impl(D* const data)
    {

        uint32_t num_ex = static_cast<glm::Dataset*>(data)->get_num_ex();
        uint32_t num_ft = static_cast<glm::Dataset*>(data)->get_num_ft();

        // get raw data structure from DenseDataset
        const auto data_ = static_cast<D*>(data)->get_data();

        uint64_t len = static_cast<uint64_t>(num_ex) * static_cast<uint64_t>(params_.n_components);

        std::vector<float> Z(len);

        OMP::parallel_for_collapse_2<int32_t, uint32_t>(
            0, num_ex, 0, params_.n_components, [this, &num_ft, &data_, &Z, &num_ex](int32_t i, uint32_t j) {
                reduction_t        tmp      = 0.0;
                const float* const this_val = &data_.val[static_cast<uint64_t>(i) * static_cast<uint64_t>(num_ft)];
                for (uint32_t k = 0; k < num_ft; k++) {
                    tmp += this_val[k] * random_weights_[k * params_.n_components + j];
                }
                uint64_t ind = static_cast<uint64_t>(j) * static_cast<uint64_t>(num_ex) + static_cast<uint64_t>(i);
                Z[ind]       = tmp;
            });
        // appply remaining operations to matrix
        OMP::parallel_for_collapse_2<int32_t, uint32_t>(
            0, params_.n_components, 0, num_ex, [this, &Z, &num_ex](int32_t j, uint32_t i) {
                uint64_t ind = static_cast<uint64_t>(j) * static_cast<uint64_t>(num_ex) + static_cast<uint64_t>(i);
                Z[ind]       = std::cos(Z[ind] + random_offsets_[j]) * std::sqrt(2.0) / std::sqrt(params_.n_components);
            });
        return Z;
    }

private:
    const RBFSamplerParams params_;

    std::vector<float> random_weights_;
    std::vector<float> random_offsets_;

    // delete copy ctor
    RBFSampler(const RBFSampler&) = delete;
};

#endif
