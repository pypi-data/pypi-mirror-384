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
 *                Nikolas Ioannou
 *
 * End Copyright
 ********************************************************************/

#ifndef GLM_MULTI_DEVICE_SOLVER
#define GLM_MULTI_DEVICE_SOLVER

#include "OMP.hpp"

#include "Solver.hpp"
#include "DeviceSolver.hpp"

namespace glm {

// Solve an Objective on the GPU
template <class D, class O> class MultiDeviceSolver : public Solver {

public:
    // delete copy ctor
    MultiDeviceSolver<D, O>(const MultiDeviceSolver<D, O>&) = delete;

    // ctor
    MultiDeviceSolver<D, O>(D* data, O* obj, double sigma, double tol, std::vector<uint32_t> device_ids,
                            uint32_t num_threads = 32, bool add_bias = false, double bias_val = 1.0)
        : Solver(static_cast<Dataset*>(data), static_cast<Objective*>(obj), sigma, tol, add_bias, bias_val)
    {

        device_ids_ = device_ids;

        // number of devices
        num_devices_ = device_ids.size();

        static_cast<D*>(data_)->pin_memory();

        // partition the data
        sub_data_ = static_cast<D*>(data_)->partition(num_devices_);

        // in case there isn't enough data to form desired number of partitions
        num_devices_ = sub_data_.size();

        // create the sub-solvers
        sub_solv_.resize(num_devices_);

        omp_set_num_threads(num_devices_);
        OMP::parallel_for<uint32_t>(
            0, num_devices_, [this, &sigma, &tol, &num_threads, &add_bias, &bias_val](const uint32_t& i) {
                sub_solv_[i] = std::make_shared<DeviceSolver<D, O>>(sub_data_[i].get(), static_cast<O*>(obj_),
                                                                    sigma * double(num_devices_), tol, device_ids_[i],
                                                                    size_t(0), num_threads, add_bias, bias_val, false);
            });

        shared_tmp_.resize(num_devices_);
        for (uint32_t i = 0; i < num_devices_; i++) {
            shared_tmp_[i] = sub_solv_[i]->get_shared_cached();
        }

        cost_tmp_.resize(num_devices_);

        uint32_t model_len = add_bias ? (1 + data_->get_num_ft()) : data_->get_num_ft();
        model_tmp_.resize(num_devices_);
        for (uint32_t i = 0; i < num_devices_; i++) {
            model_tmp_[i].resize(model_len);
        }
    }

    virtual ~MultiDeviceSolver<D, O>() { static_cast<D*>(data_)->unpin_memory(); }

    // set new value of shared vector
    virtual void set_shared(const double* const shared_new)
    {
        omp_set_num_threads(num_devices_);
        OMP::parallel_for<uint32_t>(0, num_devices_,
                                    [this, &shared_new](const uint32_t& i) { sub_solv_[i]->set_shared(shared_new); });
    }

    virtual void init(double* const shared_out)
    {
        // get shared vector contribution for all sub-solvers
        omp_set_num_threads(num_devices_);
        OMP::parallel_for<uint32_t>(0, num_devices_, [this](const uint32_t i) {
            sub_solv_[i]->init(nullptr);
            sub_solv_[i]->update_shared_cached();
        });
        double* const shared_to_upd = shared_out == nullptr ? shared_tmp_[0] : shared_out;
        if (nullptr != shared_out)
            memcpy(shared_out, shared_tmp_[0], shared_len_ * sizeof(*shared_out));

        // aggregate
        omp_set_num_threads(8);
        OMP::parallel_for<uint32_t>(0, shared_len_, [this, &shared_to_upd](const uint32_t& i) {
            for (uint32_t j = 1; j < num_devices_; j++)
                shared_to_upd[i] += shared_tmp_[j][i];
        });

        // update rest of devices' solvers
        if (nullptr == shared_out) {
            omp_set_num_threads(num_devices_);
            OMP::parallel_for<uint32_t>(0, num_devices_,
                                        [this](const uint32_t& i) { sub_solv_[i]->set_shared(shared_tmp_[0]); });
        }
    }

    virtual bool get_update(double* const shared_out)
    {

        std::vector<bool> stop(num_devices_);
        double* const     shared_to_upd = shared_out == nullptr ? shared_tmp_[0] : shared_out;

        // get shared vector contribution for all sub-solvers
        omp_set_num_threads(num_devices_);
        OMP::parallel_for<uint32_t>(0, num_devices_, [this, &stop](const uint32_t i) {
            stop[i] = sub_solv_[i]->get_update(nullptr);
            sub_solv_[i]->update_shared_cached();
        });

        if (nullptr != shared_out)
            memcpy(shared_out, shared_tmp_[0], shared_len_ * sizeof(*shared_out));

        // aggregate
        omp_set_num_threads(8);
        OMP::parallel_for<uint32_t>(0, shared_len_, [this, &shared_to_upd](const uint32_t& i) {
            for (uint32_t j = 1; j < num_devices_; j++) {
                shared_to_upd[i] += shared_tmp_[j][i];
            }
        });

        bool all_stop = true;
        for (uint32_t i = 0; i < num_devices_; i++) {
            all_stop &= stop[i];
        }

        if (nullptr == shared_out) {
            omp_set_num_threads(num_devices_);
            OMP::parallel_for<uint32_t>(0, num_devices_,
                                        [this](const uint32_t i) { sub_solv_[i]->set_shared(shared_tmp_[0]); });
        }

        return all_stop;
    }

    // compute cost function
    virtual double partial_cost()
    {

        omp_set_num_threads(num_devices_);
        OMP::parallel_for<uint32_t>(0, num_devices_,
                                    [this](const uint32_t& i) { cost_tmp_[i] = sub_solv_[i]->partial_cost(); });
        double cost_out = cost_tmp_[0];
        for (uint32_t i = 1; i < num_devices_; i++) {
            cost_out += cost_tmp_[i];
        }
        return cost_out;
    }

    // get final model vector
    virtual void get_model(double* const x)
    {

        omp_set_num_threads(num_devices_);
        OMP::parallel_for<uint32_t>(0, num_devices_,
                                    [this](const uint32_t& i) { sub_solv_[i]->get_model(model_tmp_[i].data()); });

        uint32_t model_len = add_bias_ ? (1 + data_->get_num_ft()) : data_->get_num_ft();
        for (uint32_t i = 0; i < model_len; i++) {
            x[i] = model_tmp_[0][i];
            for (uint32_t j = 1; j < num_devices_; j++) {
                x[i] += model_tmp_[j][i];
            }
        }
    }

    // get non-zero coordinates
    virtual void get_nz_coordinates(std::vector<uint32_t>& x)
    {
        for (uint32_t i = 0; i < num_devices_; i++) {
            sub_solv_[i]->get_nz_coordinates(x);
        }
    }

private:
    std::vector<uint32_t> device_ids_;

    uint32_t num_devices_;

    std::vector<std::shared_ptr<D>>                  sub_data_;
    std::vector<std::shared_ptr<DeviceSolver<D, O>>> sub_solv_;

    // temporary values need for aggregation
    std::vector<double*>             shared_tmp_;
    std::vector<std::vector<double>> model_tmp_;
    std::vector<double>              cost_tmp_;
};

}

#endif
