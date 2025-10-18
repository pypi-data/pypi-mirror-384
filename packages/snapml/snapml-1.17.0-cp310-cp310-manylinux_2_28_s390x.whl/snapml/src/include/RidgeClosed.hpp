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

#ifndef RIDGE_CLOSED
#define RIDGE_CLOSED

#include "OMP.hpp"

#include "RBFSampler.hpp"

#define EIGEN_DONT_PARALLELIZE
#define EIGEN_MPL2_ONLY

#ifndef WITH_ZOS
#include <Eigen/Dense>
#endif

namespace glm {

class RidgeClosed {

public:
    struct param_t {
        double   regularizer   = 1.0;
        bool     fit_intercept = false;
        uint32_t n_threads     = 1;
    };

    struct profile_t {
        double t_means     = 0.0;
        double t_subtract  = 0.0;
        double t_gramm     = 0.0;
        double t_uvec      = 0.0;
        double t_reg       = 0.0;
        double t_solve     = 0.0;
        double t_intercept = 0.0;

        void report()
        {
            double t_tot = t_means + t_subtract + t_gramm + t_uvec + t_reg + t_solve + t_intercept;
            printf("RidgeClosed::profile\n");
            printf("t_means:     %e (%4.1f%%)\n", t_means, 100 * t_means / t_tot);
            printf("t_subtract:  %e (%4.1f%%)\n", t_subtract, 100 * t_subtract / t_tot);
            printf("t_gramm:     %e (%4.1f%%)\n", t_gramm, 100 * t_gramm / t_tot);
            printf("t_uvec:      %e (%4.1f%%)\n", t_uvec, 100 * t_uvec / t_tot);
            printf("t_reg:       %e (%4.1f%%)\n", t_reg, 100 * t_reg / t_tot);
            printf("t_solve:     %e (%4.1f%%)\n", t_solve, 100 * t_solve / t_tot);
            printf("t_intercept: %e (%4.1f%%)\n", t_intercept, 100 * t_intercept / t_tot);
        }
    };

    using reduction_t = RBFSampler::reduction_t;

#ifndef WITH_ZOS
    using rmatrix_t = Eigen::Matrix<float, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>;
    using cmatrix_t = Eigen::Matrix<float, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor>;
    using vector_t  = Eigen::Vector<float, Eigen::Dynamic>;
#endif

    typedef std::chrono::high_resolution_clock             Clock;
    typedef std::chrono::high_resolution_clock::time_point CurTime;

#ifdef WITH_ZOS
    RidgeClosed(param_t params, std::shared_ptr<profile_t> profile)
        : params_(params)
        , profile_(profile)
        , num_ex_(0)
        , n_components_(0)
        , intercept_(0.0)
    {
        throw std::runtime_error("Closed form of ridge regression is not supported on z/OS.");
    }
#else
    RidgeClosed(param_t params, std::shared_ptr<profile_t> profile)
        : params_(params)
        , profile_(profile)
        , num_ex_(0)
        , n_components_(0)
        , intercept_(0.0)
    {
        // ctor
    }
#endif

    void fit(uint32_t num_ex, const std::vector<float>& X, const double* const y,
             const float* const sample_weights = nullptr)
    {

        CurTime t0, t1;

        omp_set_num_threads(params_.n_threads);

        num_ex_       = num_ex;
        n_components_ = X.size() / num_ex_;

        std::vector<float> mu_X(n_components_, 0.0);
        float              mu_y  = 0.0;
        float              w_sum = 0.0;

        if (params_.fit_intercept) {

            // compute means
            t0 = Clock::now();
            if (sample_weights == nullptr) {
                compute_means(X, y, &mu_X, &mu_y, &w_sum);
            } else {
                compute_weighted_means(X, y, sample_weights, &mu_X, &mu_y, &w_sum);
            }
            t1 = Clock::now();
            profile_->t_means += t_elapsed(t0, t1);
        }

        // compute gramm matrix
        t0 = Clock::now();
        std::vector<float> Z(n_components_ * n_components_);

        if (sample_weights == nullptr) {
            compute_gramm_matrix(X, &Z);
        } else {
            compute_weighted_gramm_matrix(X, sample_weights, &Z);
        }

        t1 = Clock::now();
        profile_->t_gramm += t_elapsed(t0, t1);

        // compute u-vector
        t0 = Clock::now();
        std::vector<float> u(n_components_);
        if (sample_weights == nullptr) {
            OMP::parallel_for<int32_t>(0, n_components_, [this, &X, &y, &u](const int32_t& i) {
                reduction_t tmp = 0.0;
                for (uint32_t j = 0; j < num_ex_; j++) {
                    uint64_t ind = static_cast<uint64_t>(i) * static_cast<uint64_t>(num_ex_) + static_cast<uint64_t>(j);
                    tmp += X[ind] * y[j];
                }

                u[i] = tmp;
            });
        } else {
            OMP::parallel_for<int32_t>(0, n_components_, [this, &sample_weights, &X, &y, &u](const int32_t& i) {
                reduction_t tmp = 0.0;
                for (uint32_t j = 0; j < num_ex_; j++) {
                    uint64_t ind = static_cast<uint64_t>(i) * static_cast<uint64_t>(num_ex_) + static_cast<uint64_t>(j);
                    tmp += sample_weights[j] * X[ind] * y[j];
                }
                u[i] = tmp;
            });
        }
        t1 = Clock::now();
        profile_->t_uvec += t_elapsed(t0, t1);

        if (params_.fit_intercept) {

            t0 = Clock::now();
            OMP::parallel_for_collapse_2<int32_t, uint32_t>(0, n_components_, 0, n_components_,
                                                            [this, &Z, &mu_X, &w_sum](int32_t i, uint32_t j) {
                                                                Z[i * n_components_ + j] -= mu_X[i] * mu_X[j] * w_sum;
                                                            });

            OMP::parallel_for<int32_t>(
                0, n_components_, [&u, &mu_X, &mu_y, &w_sum](const int32_t& i) { u[i] -= mu_X[i] * mu_y * w_sum; });

            t1 = Clock::now();
            profile_->t_subtract += t_elapsed(t0, t1);
        }

        // add regularizer
        t0 = Clock::now();
        OMP::parallel_for<int32_t>(0, n_components_,
                                   [this, &Z](const int32_t& i) { Z[i * n_components_ + i] += params_.regularizer; });
        t1 = Clock::now();
        profile_->t_reg += t_elapsed(t0, t1);

        // solve LSQ
        coef_.resize(n_components_);
        t0 = Clock::now();

#ifndef WITH_ZOS
        Eigen::Map<rmatrix_t> Z_map(Z.data(), n_components_, n_components_);
        Eigen::Map<vector_t>  coef_map(coef_.data(), n_components_);
        Eigen::Map<vector_t>  u_map(u.data(), n_components_);

        coef_map = Z_map.ldlt().solve(u_map);
#endif
        t1 = Clock::now();
        profile_->t_solve += t_elapsed(t0, t1);

        // compute intercept
        t0         = Clock::now();
        intercept_ = 0.0;
        if (params_.fit_intercept) {
            intercept_ = mu_y;
            for (uint32_t i = 0; i < n_components_; i++) {
                intercept_ -= mu_X[i] * coef_[i];
            }
        }
        t1 = Clock::now();
        profile_->t_intercept += t_elapsed(t0, t1);
    }

    void predict(const std::vector<float>& data, double* const pred)
    {
        omp_set_num_threads(params_.n_threads);

        // infer number of examples
        const uint32_t num_ex = data.size() / n_components_;
        OMP::parallel_for<int32_t>(0, num_ex, [this, &pred, &data, &num_ex](const int32_t& i) {
            pred[i] = intercept_;
            for (uint32_t j = 0; j < n_components_; j++) {
                uint64_t ind = static_cast<uint64_t>(j) * static_cast<uint64_t>(num_ex) + static_cast<uint64_t>(i);
                pred[i] += data[ind] * coef_[j];
            }
        });
    }

    const std::vector<float> get_coef() { return coef_; }

    const float get_intercept() { return intercept_; }

private:
    inline double t_elapsed(const CurTime& t0, const CurTime& t1)
    {
        auto dur = t1 - t0;
        return static_cast<double>(dur.count()) / 1e9;
    }

    // compute means (without sample weights)
    void compute_means(const std::vector<float>& X, const double* const y, std::vector<float>* const mu_X,
                       float* const mu_y, float* const w_sum)
    {

        OMP::parallel_for<int32_t>(0, n_components_, [this, &X, &mu_X](const int32_t& i) {
            reduction_t tmp = 0.0;
            for (uint32_t k = 0; k < num_ex_; k++) {
                uint64_t ind = static_cast<uint64_t>(i) * static_cast<uint64_t>(num_ex_) + static_cast<uint64_t>(k);
                tmp += X[ind];
            }
            tmp /= reduction_t(num_ex_);
            (*mu_X)[i] = tmp;
        });

        reduction_t tmp = 0.0;
        for (uint32_t i = 0; i < num_ex_; i++) {
            tmp += y[i];
        }
        tmp /= reduction_t(num_ex_);

        *mu_y  = tmp;
        *w_sum = num_ex_;
    }

    // compute means (without sample weights)
    void compute_weighted_means(const std::vector<float>& X, const double* const y, const float* const weights,
                                std::vector<float>* const mu_X, float* const mu_y, float* const w_sum)
    {

        assert(weights != nullptr);

        reduction_t s_sum = 0.0;
        for (uint32_t k = 0; k < num_ex_; k++) {
            s_sum += weights[k];
        }
        *w_sum = s_sum;

        OMP::parallel_for<int32_t>(0, n_components_, [this, &weights, &X, &s_sum, &mu_X](const int32_t& i) {
            reduction_t tmp = 0.0;
            for (uint32_t k = 0; k < num_ex_; k++) {
                uint64_t ind = static_cast<uint64_t>(i) * static_cast<uint64_t>(num_ex_) + static_cast<uint64_t>(k);
                tmp += weights[k] * X[ind];
            }
            tmp /= s_sum;

            (*mu_X)[i] = tmp;
        });

        reduction_t tmp = 0.0;
        for (uint32_t k = 0; k < num_ex_; k++) {
            tmp += weights[k] * y[k];
        }
        tmp /= s_sum;

        *mu_y = tmp;
    }

    void compute_gramm_matrix(const std::vector<float>& X, std::vector<float>* const Z)
    {

        std::vector<std::pair<uint32_t, uint32_t>> pairs;
        for (uint32_t i = 0; i < n_components_; i++) {
            for (uint32_t j = 0; j <= i; j++) {
                pairs.push_back(std::pair<uint32_t, uint32_t>(i, j));
            }
        }

        OMP::parallel_for<int32_t>(0, pairs.size(), [this, &pairs, &X, &Z](const int32_t& p) {
            const uint32_t     i  = pairs[p].first;
            const uint32_t     j  = pairs[p].second;
            const float* const xi = &X[static_cast<uint64_t>(i) * static_cast<uint64_t>(num_ex_)];
            const float* const xj = &X[static_cast<uint64_t>(j) * static_cast<uint64_t>(num_ex_)];

            const uint32_t num_ex4 = (num_ex_ / 4) * 4;

            reduction_t tmp = 0.0;
            uint32_t    k   = 0;
            for (; k < num_ex4; k += 4) {
                float m0 = xi[k] * xj[k];
                float m1 = xi[k + 1] * xj[k + 1];
                float m2 = xi[k + 2] * xj[k + 2];
                float m3 = xi[k + 3] * xj[k + 3];
                tmp += m0 + m1 + m2 + m3;
            }
            for (; k < num_ex_; k++) {
                tmp += xi[k] * xj[k];
            }
            (*Z)[i * n_components_ + j] = tmp;
        });

        OMP::parallel_for<int32_t>(0, n_components_, [this, &Z](const int32_t& i) {
            for (uint32_t j = i + 1; j < n_components_; j++) {
                (*Z)[i * n_components_ + j] = (*Z)[j * n_components_ + i];
            }
        });
    }

    void compute_weighted_gramm_matrix(const std::vector<float>& X, const float* const weights,
                                       std::vector<float>* const Z)
    {

        std::vector<std::pair<uint32_t, uint32_t>> pairs;
        for (uint32_t i = 0; i < n_components_; i++) {
            for (uint32_t j = 0; j <= i; j++) {
                pairs.push_back(std::pair<uint32_t, uint32_t>(i, j));
            }
        }

        OMP::parallel_for<int32_t>(0, pairs.size(), [this, &pairs, &weights, &X, &Z](const int32_t& p) {
            const uint32_t     i  = pairs[p].first;
            const uint32_t     j  = pairs[p].second;
            const float* const xi = &X[static_cast<uint64_t>(i) * static_cast<uint64_t>(num_ex_)];
            const float* const xj = &X[static_cast<uint64_t>(j) * static_cast<uint64_t>(num_ex_)];

            const uint32_t num_ex4 = (num_ex_ / 4) * 4;

            reduction_t tmp = 0.0;
            uint32_t    k   = 0;
            for (; k < num_ex4; k += 4) {
                float m0 = weights[k] * xi[k] * xj[k];
                float m1 = weights[k + 1] * xi[k + 1] * xj[k + 1];
                float m2 = weights[k + 2] * xi[k + 2] * xj[k + 2];
                float m3 = weights[k + 3] * xi[k + 3] * xj[k + 3];
                tmp += m0 + m1 + m2 + m3;
            }
            for (; k < num_ex_; k++) {
                tmp += weights[k] * xi[k] * xj[k];
            }
            (*Z)[i * n_components_ + j] = tmp;
        });

        OMP::parallel_for<int32_t>(0, n_components_, [this, &Z](const int32_t& i) {
            for (uint32_t j = i + 1; j < n_components_; j++) {
                (*Z)[i * n_components_ + j] = (*Z)[j * n_components_ + i];
            }
        });
    }

    // parameters
    const param_t params_;

    // timing profile
    const std::shared_ptr<profile_t> profile_;

    // number of example
    uint32_t num_ex_;

    // number of components
    uint32_t n_components_;

    // coefficients
    std::vector<float> coef_;

    // intercept
    float intercept_;
};

}

#endif
