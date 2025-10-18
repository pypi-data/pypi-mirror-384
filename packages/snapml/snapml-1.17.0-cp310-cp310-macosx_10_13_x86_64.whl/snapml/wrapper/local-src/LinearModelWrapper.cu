/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2018, 2019
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

// datasets
#include "SparseDataset.hpp"
#include "DenseDatasetInt.hpp"

// objectives
#include "PrimalLassoRegression.hpp"
#include "PrimalRidgeRegression.hpp"
#include "DualRidgeRegression.hpp"
#include "DualL1SupportVectorMachine.hpp"
#include "DualL2SupportVectorMachine.hpp"
#include "PrimalLogisticRegression.hpp"
#include "PrimalSparseLogisticRegression.hpp"
#include "DualLogisticRegression.hpp"

// device solvers
#include "DeviceSolver.hpp"
#include "MultiDeviceSolver.hpp"

template <class D, class O>
std::shared_ptr<glm::Solver> make_device_solver(D* data, O* obj, double sigma, double tol,
                                                std::vector<uint32_t> device_ids, uint32_t num_threads, bool add_bias,
                                                double bias_val)
{

    if (device_ids.size() == 0) {
        return std::make_shared<glm::DeviceSolver<D, O>>(data, obj, sigma, tol, 0, 0, num_threads, add_bias, bias_val);
    } else if (device_ids.size() == 1) {
        return std::make_shared<glm::DeviceSolver<D, O>>(data, obj, sigma, tol, device_ids[0], 0, num_threads, add_bias,
                                                         bias_val);
    } else {
        return std::make_shared<glm::MultiDeviceSolver<D, O>>(data, obj, sigma, tol, device_ids, num_threads, add_bias,
                                                              bias_val);
    }
}

template std::shared_ptr<glm::Solver> make_device_solver(glm::DenseDataset* data, glm::PrimalLassoRegression* obj,
                                                         double sigma, double tol, std::vector<uint32_t> device_ids,
                                                         uint32_t num_threads, bool add_bias, double bias_val);
template std::shared_ptr<glm::Solver> make_device_solver(glm::DenseDataset* data, glm::PrimalLogisticRegression* obj,
                                                         double sigma, double tol, std::vector<uint32_t> device_ids,
                                                         uint32_t num_threads, bool add_bias, double bias_val);
template std::shared_ptr<glm::Solver> make_device_solver(glm::DenseDataset* data, glm::DualLogisticRegression* obj,
                                                         double sigma, double tol, std::vector<uint32_t> device_ids,
                                                         uint32_t num_threads, bool add_bias, double bias_val);
template std::shared_ptr<glm::Solver> make_device_solver(glm::DenseDataset* data, glm::DualL1SupportVectorMachine* obj,
                                                         double sigma, double tol, std::vector<uint32_t> device_ids,
                                                         uint32_t num_threads, bool add_bias, double bias_val);
template std::shared_ptr<glm::Solver> make_device_solver(glm::DenseDataset* data, glm::DualL2SupportVectorMachine* obj,
                                                         double sigma, double tol, std::vector<uint32_t> device_ids,
                                                         uint32_t num_threads, bool add_bias, double bias_val);
template std::shared_ptr<glm::Solver> make_device_solver(glm::DenseDataset*                   data,
                                                         glm::PrimalSparseLogisticRegression* obj, double sigma,
                                                         double tol, std::vector<uint32_t> device_ids,
                                                         uint32_t num_threads, bool add_bias, double bias_val);
template std::shared_ptr<glm::Solver> make_device_solver(glm::DenseDataset* data, glm::PrimalRidgeRegression* obj,
                                                         double sigma, double tol, std::vector<uint32_t> device_ids,
                                                         uint32_t num_threads, bool add_bias, double bias_val);
template std::shared_ptr<glm::Solver> make_device_solver(glm::DenseDataset* data, glm::DualRidgeRegression* obj,
                                                         double sigma, double tol, std::vector<uint32_t> device_ids,
                                                         uint32_t num_threads, bool add_bias, double bias_val);

template std::shared_ptr<glm::Solver> make_device_solver(glm::SparseDataset* data, glm::PrimalLassoRegression* obj,
                                                         double sigma, double tol, std::vector<uint32_t> device_ids,
                                                         uint32_t num_threads, bool add_bias, double bias_val);
template std::shared_ptr<glm::Solver> make_device_solver(glm::SparseDataset* data, glm::PrimalLogisticRegression* obj,
                                                         double sigma, double tol, std::vector<uint32_t> device_ids,
                                                         uint32_t num_threads, bool add_bias, double bias_val);
template std::shared_ptr<glm::Solver> make_device_solver(glm::SparseDataset* data, glm::DualLogisticRegression* obj,
                                                         double sigma, double tol, std::vector<uint32_t> device_ids,
                                                         uint32_t num_threads, bool add_bias, double bias_val);
template std::shared_ptr<glm::Solver> make_device_solver(glm::SparseDataset* data, glm::DualL1SupportVectorMachine* obj,
                                                         double sigma, double tol, std::vector<uint32_t> device_ids,
                                                         uint32_t num_threads, bool add_bias, double bias_val);
template std::shared_ptr<glm::Solver> make_device_solver(glm::SparseDataset* data, glm::DualL2SupportVectorMachine* obj,
                                                         double sigma, double tol, std::vector<uint32_t> device_ids,
                                                         uint32_t num_threads, bool add_bias, double bias_val);
template std::shared_ptr<glm::Solver> make_device_solver(glm::SparseDataset*                  data,
                                                         glm::PrimalSparseLogisticRegression* obj, double sigma,
                                                         double tol, std::vector<uint32_t> device_ids,
                                                         uint32_t num_threads, bool add_bias, double bias_val);
template std::shared_ptr<glm::Solver> make_device_solver(glm::SparseDataset* data, glm::PrimalRidgeRegression* obj,
                                                         double sigma, double tol, std::vector<uint32_t> device_ids,
                                                         uint32_t num_threads, bool add_bias, double bias_val);
template std::shared_ptr<glm::Solver> make_device_solver(glm::SparseDataset* data, glm::DualRidgeRegression* obj,
                                                         double sigma, double tol, std::vector<uint32_t> device_ids,
                                                         uint32_t num_threads, bool add_bias, double bias_val);
