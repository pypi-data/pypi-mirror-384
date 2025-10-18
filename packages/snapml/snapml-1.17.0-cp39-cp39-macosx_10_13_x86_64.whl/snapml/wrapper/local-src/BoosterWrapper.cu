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
 * Authors      : Thomas Parnell
 *                Celestine Duenner
 *                Dimitrios Sarigiannis
 *                Andreea Anghel
 *                Nikolas Ioannou
 *                Nikolaos Papandreou
 *                Gummadi Ravi
 *                Josiah Sathiadass
 *                Sangeeth Keeriyadath
 *                Pradipta Ghosh
 *
 * End Copyright
 ********************************************************************/

#define NO_IMPORT_ARRAY
#include "Wrapper.h"

#include "DenseDatasetInt.hpp"

#include "DeviceSolverWrapper.hpp"
#include "DeviceSolver.hpp"
#include "MultiDeviceSolver.hpp"
#include "DualRidgeRegression.hpp"
#include "PrimalRidgeRegression.hpp"

template <>
std::shared_ptr<glm::Solver>
make_device_solver_<glm::DualRidgeRegression>(glm::DenseDataset* data, glm::DualRidgeRegression* obj, double sigma,
                                              double tol, const std::vector<unsigned int>& device_ids,
                                              uint32_t num_threads, bool add_bias, double bias_val)
{

    if (device_ids.size() == 0) {
        return std::make_shared<glm::DeviceSolver<glm::DenseDataset, glm::DualRidgeRegression>>(
            data, obj, sigma, tol, 0, 0, num_threads, add_bias, bias_val);
    } else if (device_ids.size() == 1) {
        return std::make_shared<glm::DeviceSolver<glm::DenseDataset, glm::DualRidgeRegression>>(
            data, obj, sigma, tol, device_ids[0], 0, num_threads, add_bias, bias_val);
    } else {
        return std::make_shared<glm::MultiDeviceSolver<glm::DenseDataset, glm::DualRidgeRegression>>(
            data, obj, sigma, tol, device_ids, num_threads, add_bias, bias_val);
    }
};

template <>
std::shared_ptr<glm::Solver>
make_device_solver_<glm::PrimalRidgeRegression>(glm::DenseDataset* data, glm::PrimalRidgeRegression* obj, double sigma,
                                                double tol, const std::vector<unsigned int>& device_ids,
                                                uint32_t num_threads, bool add_bias, double bias_val)
{

    if (device_ids.size() == 0) {
        return std::make_shared<glm::DeviceSolver<glm::DenseDataset, glm::PrimalRidgeRegression>>(
            data, obj, sigma, tol, 0, 0, num_threads, add_bias, bias_val);
    } else if (device_ids.size() == 1) {
        return std::make_shared<glm::DeviceSolver<glm::DenseDataset, glm::PrimalRidgeRegression>>(
            data, obj, sigma, tol, device_ids[0], 0, num_threads, add_bias, bias_val);
    } else {
        return std::make_shared<glm::MultiDeviceSolver<glm::DenseDataset, glm::PrimalRidgeRegression>>(
            data, obj, sigma, tol, device_ids, num_threads, add_bias, bias_val);
    }
};
