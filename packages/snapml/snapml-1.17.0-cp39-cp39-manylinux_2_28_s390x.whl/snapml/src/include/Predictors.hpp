/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2018, 2020
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Thomas Parnell
 *                Celestine Duenner
 *                Dimitrios Sarigiannis
 *                Andreea Anghel
 *
 * End Copyright
 ********************************************************************/

#ifndef GLM_PREDICTORS
#define GLM_PREDICTORS

#include <thread>

#include "OMP.hpp"

namespace glm {
namespace predictors {

    namespace jni {

        template <class D>
        void linear_prediction(D* data, const double* model, uint32_t model_len, double* pred,
                               uint32_t num_threads_ = 0, bool add_bias = false, double bias_val = 1.0)
        {
            if (data->get_transpose()) {
                throw std::runtime_error("Cannot perform inference on transposed data.");
            }

            uint32_t model_len_chk = add_bias ? (1 + data->get_num_ft()) : data->get_num_ft();

            if (model_len_chk != model_len) {
                throw std::runtime_error("Number of features in the data is not aligned with the model dimensions.");
            }

            if (num_threads_ == 0) {
                num_threads_ = std::thread::hardware_concurrency();
            }

            omp_set_num_threads(num_threads_);

            auto     x           = data->get_data();
            uint32_t this_num_ex = data->get_this_num_pt();

            OMP::parallel_for<int32_t>(0, this_num_ex,
                                       [&x, &model, &add_bias, &model_len, &bias_val, &pred](const int32_t& ex) {
                                           uint32_t this_len = D::get_pt_len(x, ex);
                                           double   dp       = 0.0;
                                           for (uint32_t k = 0; k < this_len; k++) {
                                               float    val;
                                               uint32_t ind;
                                               D::lookup(x, ex, k, this_len, ind, val);
                                               dp += model[ind] * val;
                                           }
                                           if (add_bias) {
                                               dp += model[model_len - 1] * bias_val;
                                           }
                                           pred[ex] = dp;
                                       });
        }

        template <class D>
        void linear_classification(D* data, const double* model, uint32_t model_len, double* pred, double thd = 0.0,
                                   uint32_t num_threads_ = 0, bool add_bias = false, double bias_val = 1.0)
        {
            if (data->get_transpose()) {
                throw std::runtime_error("Cannot perform inference on transposed data.");
            }

            uint32_t model_len_chk = add_bias ? (1 + data->get_num_ft()) : data->get_num_ft();

            if (model_len_chk != model_len) {
                throw std::runtime_error("Number of features in the data is not aligned with the model dimensions.");
            }

            if (num_threads_ == 0) {
                num_threads_ = std::thread::hardware_concurrency();
            }

            omp_set_num_threads(num_threads_);

            auto     x           = data->get_data();
            uint32_t this_num_ex = data->get_this_num_pt();

            OMP::parallel_for<int32_t>(0, this_num_ex,
                                       [&x, &model, &add_bias, &model_len, &bias_val, &pred, &thd](const int32_t& ex) {
                                           uint32_t this_len = D::get_pt_len(x, ex);
                                           double   dp       = 0.0;
                                           for (uint32_t k = 0; k < this_len; k++) {
                                               float    val;
                                               uint32_t ind;
                                               D::lookup(x, ex, k, this_len, ind, val);
                                               dp += model[ind] * val;
                                           }
                                           if (add_bias) {
                                               dp += model[model_len - 1] * bias_val;
                                           }
                                           pred[ex] = (dp > thd) ? +1.0 : -1.0;
                                       });
        }

        template <class D>
        void logistic_probabilities(D* data, const double* model, uint32_t model_len, double* proba,
                                    uint32_t num_threads_ = 0, bool add_bias = false, double bias_val = 1.0)
        {
            if (data->get_transpose()) {
                throw std::runtime_error("Cannot perform inference on transposed data.");
            }

            uint32_t model_len_chk = add_bias ? (1 + data->get_num_ft()) : data->get_num_ft();

            if (model_len_chk != model_len) {
                throw std::runtime_error("Number of features in the data is not aligned with the model dimensions.");
            }

            if (num_threads_ == 0) {
                num_threads_ = std::thread::hardware_concurrency();
            }

            omp_set_num_threads(num_threads_);

            auto     x           = data->get_data();
            uint32_t this_num_ex = data->get_this_num_pt();

            OMP::parallel_for<int32_t>(0, this_num_ex,
                                       [&x, &model, &add_bias, &model_len, &bias_val, &proba](const int32_t& ex) {
                                           uint32_t this_len = D::get_pt_len(x, ex);
                                           double   dp       = 0.0;
                                           for (uint32_t k = 0; k < this_len; k++) {
                                               float    val;
                                               uint32_t ind;
                                               D::lookup(x, ex, k, this_len, ind, val);
                                               dp += model[ind] * val;
                                           }
                                           if (add_bias) {
                                               dp += model[model_len - 1] * bias_val;
                                           }
                                           proba[ex] = 1.0 / (1.0 + exp(-dp));
                                       });
        }

        template <class D>
        std::vector<double> logistic_probabilities(std::shared_ptr<D> data, const std::vector<double>& model)
        {
            uint32_t            this_num_ex = data->get_this_num_pt();
            std::vector<double> proba(this_num_ex);
            jni::logistic_probabilities(data.get(), model.data(), static_cast<uint32_t>(model.size()), proba.data());
            return proba;
        }

    }
}
}

#endif
