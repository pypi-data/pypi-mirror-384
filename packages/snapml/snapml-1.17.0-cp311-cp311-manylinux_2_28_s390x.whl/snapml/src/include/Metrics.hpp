/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2018
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

#ifndef GLM_METRICS
#define GLM_METRICS

#include "Dataset.hpp"
#include <cmath>

namespace glm {
namespace metrics {

    namespace jni {

        double logistic_loss(Dataset* data, const double* proba, uint32_t proba_len)
        {

            if (data->get_transpose()) {
                throw std::runtime_error("Cannot perform inference on transposed data.");
            }

            uint32_t num_ex      = data->get_num_ex();
            uint32_t this_num_ex = data->get_this_num_pt();
            float*   labs        = data->get_labs();

            if (this_num_ex != proba_len) {
                throw std::runtime_error(
                    "Number of examples in the partition is not aligned with the length of the probabilities");
            }

            double loss = 0.0;
            for (uint32_t i = 0; i < this_num_ex; i++) {
                double this_lab = (labs[i] > 0) ? 1.0 : 0.0;
                double p1       = proba[i];
                double p0       = 1 - p1;
                p1              = std::max(1e-15, p1);
                p0              = std::max(1e-15, p0);
                loss -= this_lab * std::log(p1) + (1.0 - this_lab) * std::log(p0);
            }
            loss /= static_cast<double>(num_ex);

            return loss;
        }

        double accuracy(Dataset* data, const double* pred, uint32_t pred_len, bool binary)
        {

            if (data->get_transpose()) {
                throw std::runtime_error("Cannot perform inference on transposed data.");
            }

            uint32_t num_ex      = data->get_num_ex();
            uint32_t this_num_ex = data->get_this_num_pt();
            float*   labs        = data->get_labs();

            if (this_num_ex != pred_len) {
                throw std::runtime_error(
                    "Number of examples in the partition is not aligned with the length of the predictions");
            }

            uint32_t num_same = 0;
            for (uint32_t i = 0; i < this_num_ex; i++) {
                if ((labs[i] > 0) == (pred[i] > 0)) {
                    num_same++;
                }
            }

            return static_cast<double>(num_same) / static_cast<double>(num_ex);
        }

        double accuracy_mpi(Dataset* data, const double* pred, uint32_t pred_len)
        {

            if (data->get_transpose()) {
                throw std::runtime_error("Cannot perform inference on transposed data.");
            }

            uint32_t num_ex      = data->get_num_ex();
            uint32_t this_num_ex = data->get_this_num_pt();
            float*   labs        = data->get_labs();

            if (this_num_ex != pred_len) {
                throw std::runtime_error(
                    "Number of examples in the partition is not aligned with the length of the predictions");
            }

            uint32_t num_same = 0;
            for (uint32_t i = 0; i < this_num_ex; i++) {
                if (labs[i] == pred[i]) {
                    num_same++;
                }
            }

            return static_cast<double>(num_same) / static_cast<double>(num_ex);
        }

        double hinge_loss(Dataset* data, const double* pred, uint32_t pred_len)
        {

            if (data->get_transpose()) {
                throw std::runtime_error("Cannot perform inference on transposed data.");
            }

            uint32_t num_ex      = data->get_num_ex();
            uint32_t this_num_ex = data->get_this_num_pt();
            float*   labs        = data->get_labs();

            if (this_num_ex != pred_len) {
                throw std::runtime_error(
                    "Number of examples in the partition is not aligned with the length of the predictions");
            }

            double sum = 0;
            for (uint32_t i = 0; i < this_num_ex; i++) {
                double this_lab = (labs[i] > 0) ? +1.0 : -1.0;
                sum += std::max(static_cast<double>(0), 1 - this_lab * pred[i]);
            }

            return static_cast<double>(sum) / static_cast<double>(num_ex);
        }

        double mean_squared_error(Dataset* data, const double* pred, uint32_t pred_len)
        {

            if (data->get_transpose()) {
                throw std::runtime_error("Cannot perform inference on transposed data.");
            }

            uint32_t num_ex      = data->get_num_ex();
            uint32_t this_num_ex = data->get_this_num_pt();
            float*   labs        = data->get_labs();

            if (this_num_ex != pred_len) {
                throw std::runtime_error(
                    "Number of examples in the partition is not aligned with the length of the predictions");
            }

            double mse = 0.0;
            for (size_t i = 0; i < this_num_ex; i++) {
                double tmp = static_cast<double>(labs[i]) - pred[i];
                mse += tmp * tmp;
            }

            mse /= static_cast<double>(num_ex);

            return mse;
        }

        void classification_statistics(Dataset* data, const double* pred, uint32_t pred_len, uint32_t& num_tp,
                                       uint32_t& num_fp, uint32_t& num_tn, uint32_t& num_fn)
        {

            if (data->get_transpose()) {
                throw std::runtime_error("Cannot perform inference on transposed data.");
            }

            uint32_t this_num_ex = data->get_this_num_pt();
            float*   labs        = data->get_labs();

            if (this_num_ex != pred_len) {
                throw std::runtime_error(
                    "Number of examples in the partition is not aligned with the length of the predictions");
            }

            num_tp = 0;
            num_fp = 0;
            num_tn = 0;
            num_fn = 0;

            for (size_t i = 0; i < this_num_ex; i++) {

                if (pred[i] > 0) {
                    if (labs[i] > 0) {
                        num_tp++;
                    } else {
                        num_fp++;
                    }
                } else {
                    if (labs[i] <= 0) {
                        num_tn++;
                    } else {
                        num_fn++;
                    }
                }
            }
        }

    }

    template <class D> double logistic_loss(std::shared_ptr<D> data, const std::vector<double>& proba)
    {
        return jni::logistic_loss(data.get(), proba.data(), static_cast<uint32_t>(proba.size()));
    }

}
}

#endif
