/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2018, 2019, 2020
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
 *                Milos Stanisavljevic
 *
 * End Copyright
 ********************************************************************/

/*! @file
 *  @ingroup wrapper
 */

#define NO_IMPORT_ARRAY
#include "Wrapper.h"

#include "common.hpp"
#include "SparseDataset.hpp"
#include "DenseDatasetInt.hpp"
#include "Predictors.hpp"
#include "PrimalLassoRegression.hpp"
#include "PrimalRidgeRegression.hpp"
#include "DualRidgeRegression.hpp"
#include "DualL1SupportVectorMachine.hpp"
#include "DualL2SupportVectorMachine.hpp"
#include "PrimalLogisticRegression.hpp"
#include "PrimalSparseLogisticRegression.hpp"
#include "DualLogisticRegression.hpp"

#include "Solver.hpp"

#ifdef WITH_NUMA
#include "MultiHostSolver.hpp"
#else
#include "HostSolver.hpp"
#endif

#include "SGDSolver.hpp"
#include "Privacy.hpp"

#include <set>

enum class prediction_t { LinearRegression, LinearClassification, LogisticProbabilities };

// type for accumulating history stats
struct history_t {
    uint32_t epoch;
    double   t_elap_sec;
    double   train_obj;
};

template <class D, class O>
std::vector<double> train_model(D* data, O* obj, uint32_t num_epochs, bool use_gpu, std::vector<uint32_t> device_ids,
                                uint32_t& n_iter, std::vector<uint32_t>& support_vectors,
                                std::vector<history_t>& history, uint32_t return_training_history = 0,
                                size_t gpu_mem_limit = 0, uint32_t num_threads = 32, bool verbose = false,
                                double tol = -1.0, bool add_bias = false, double bias_val = 1.0)
{

    double                       sigma = 1.0;
    std::shared_ptr<glm::Solver> solver;

    if (!use_gpu) {
#ifdef WITH_NUMA
        if (numa_num_configured_nodes() > 1) {
            solver
                = std::make_shared<glm::MultiNumaSolver<D, O>>(data, obj, sigma, tol, num_threads, add_bias, bias_val);
        } else {
            solver = std::make_shared<glm::HostSolver<D, O>>(data, obj, sigma, tol, num_threads, add_bias, bias_val);
        }
#else
        solver = std::make_shared<glm::HostSolver<D, O>>(data, obj, sigma, tol, num_threads, add_bias, bias_val);
#endif
    } else {
#ifdef WITH_CUDA
        solver = make_device_solver(data, obj, sigma, tol, device_ids, num_threads, add_bias, bias_val);
#else
        throw std::runtime_error("Snap ML was not compiled with GPU support");
#endif
    }

    if (verbose) {
        std::cout << "--------------------------------" << std::endl;
        std::cout << "Training objective per iteration" << std::endl;
        std::cout << "--------------------------------" << std::endl;
    }

    CurTime t1, t2;

    double t_elap_sec = 0.0;
    double train_obj;

    std::vector<double> shared(solver->dim());
    double*             shared_ptr = nullptr;

    // initialization
    t1 = Clock::now();
    solver->init(shared_ptr);
    t2       = Clock::now();
    auto dur = t2 - t1;
    t_elap_sec += (double)dur.count() / 1.0e9;

    if (verbose || return_training_history == 2) {
        train_obj = solver->partial_cost();
    }

    if (verbose) {
        printf("epoch: %5d, t_elap_sec: %10.2f, train_obj: %e\n", 0, t_elap_sec, train_obj);
    }

    if (return_training_history == 2) {
        history_t rec;
        rec.epoch      = 0;
        rec.t_elap_sec = t_elap_sec;
        rec.train_obj  = train_obj;
        history.push_back(rec);
    }

    bool     stop  = false;
    uint32_t epoch = 0;
    while (!stop) {

        t1       = Clock::now();
        stop     = solver->get_update(shared_ptr);
        t2       = Clock::now();
        auto dur = t2 - t1;
        t_elap_sec += static_cast<double>(dur.count()) / 1.0e9;

        // increase epoch count
        epoch++;

        if (epoch == num_epochs) {
            stop = true;
        }

        // compute training objective (optional)
        if (verbose || return_training_history == 2 || (return_training_history == 1 && stop)) {
            train_obj = solver->partial_cost();
        }

        // print off progress
        if (verbose) {
            printf("epoch: %5u, t_elap_sec: %10.2f, train_obj: %e\n", epoch, t_elap_sec, train_obj);
        }

        if (return_training_history == 2 || (return_training_history == 1 && stop)) {
            history_t rec;
            rec.epoch      = epoch;
            rec.t_elap_sec = t_elap_sec;
            rec.train_obj  = train_obj;
            history.push_back(rec);
        }
    }
    if (verbose) {
        if (epoch < num_epochs) {
            std::cout << "[Info] Tolerance " << tol << " attained after " << epoch << " epochs." << std::endl;
        } else {
            std::cout << "[Info] Warning: did not converge within tolerance " << tol << std::endl;
        }
    }
    // set n_iter
    n_iter = epoch;

    uint32_t num_ft = data->get_num_ft();
    if (add_bias) {
        num_ft++;
    }
    std::vector<double> model(num_ft);
    solver->get_model(model.data());

    support_vectors.resize(0);
    solver->get_nz_coordinates(support_vectors);

    return model;
}

template <class D, class O>
std::vector<double> train_sgd_model(D* data, O* obj, uint32_t num_epochs, std::vector<history_t>& history,
                                    uint32_t return_training_history = 0, uint32_t num_threads = 32,
                                    bool verbose = false, double tol = -1.0, double eta = 0.3,
                                    uint32_t batch_size = 100, double grad_clip = 1, double privacy_sigma = 0.0)
{

    double                                sigma = 1.0;
    std::shared_ptr<glm::SGDSolver<D, O>> solver;

    solver = std::make_shared<glm::SGDSolver<D, O>>(data, obj, sigma, tol, eta, batch_size, grad_clip, privacy_sigma);

    if (verbose) {
        std::cout << "--------------------------------" << std::endl;
        std::cout << "Training objective per iteration" << std::endl;
        std::cout << "--------------------------------" << std::endl;
    }

    CurTime t1, t2;

    double t_elap_sec = 0.0;
    double train_obj;

    std::vector<double> shared(solver->dim());
    double*             shared_ptr = nullptr;

    // initialization
    t1 = Clock::now();
    solver->init(shared_ptr);
    t2       = Clock::now();
    auto dur = t2 - t1;
    t_elap_sec += (double)dur.count() / 1.0e9;

    if (verbose || return_training_history == 2) {
        train_obj = solver->partial_cost();
    }

    if (verbose) {
        printf("epoch: %5d, t_elap_sec: %10.2f, train_obj: %e\n", 0, t_elap_sec, train_obj);
    }

    if (return_training_history == 2) {
        history_t rec;
        rec.epoch      = 0;
        rec.t_elap_sec = t_elap_sec;
        rec.train_obj  = train_obj;
        history.push_back(rec);
    }

    bool     stop  = false;
    uint32_t epoch = 0;
    while (!stop && epoch < num_epochs) {

        t1       = Clock::now();
        stop     = solver->get_update(shared_ptr);
        t2       = Clock::now();
        auto dur = t2 - t1;
        t_elap_sec += static_cast<double>(dur.count()) / 1.0e9;

        // increase epoch count
        epoch++;

        // compute training objective (optional)
        if (verbose || return_training_history == 2 || (return_training_history == 1 && stop)) {
            train_obj = solver->partial_cost();
        }

        // print off progress
        if (verbose) {
            printf("epoch: %5u, t_elap_sec: %10.2f, train_obj: %e\n", epoch, t_elap_sec, train_obj);
        }

        if (return_training_history == 2 || (return_training_history == 1 && stop)) {
            history_t rec;
            rec.epoch      = epoch;
            rec.t_elap_sec = t_elap_sec;
            rec.train_obj  = train_obj;
            history.push_back(rec);
        }
    }

    uint32_t            num_ft = data->get_num_ft();
    std::vector<double> model(num_ft);
    solver->get_model(model.data());

    return model;
}

template <class O_p, class O_d>
wrapperError_t __train_model(PyObject* m, glm::Dataset* data, uint64_t transpose, bool is_sparse, double lambda,
                             double w_pos, double w_neg, uint32_t num_ex, uint32_t num_epochs, uint64_t use_gpu,
                             std::vector<uint32_t> device_ids, uint32_t& n_iter, std::vector<uint32_t>& support_vectors,
                             std::vector<double>& model, std::vector<history_t>& history,
                             uint32_t return_training_history = 0, size_t gpu_mem_limit = 0, uint32_t num_threads = 32,
                             uint32_t verbose = false, double tol = -1.0, bool fit_intercept = false,
                             double intercept_scaling = 1.0, npy_int64 privacy = 0, double eta = 0.0,
                             npy_int64 batch_size = 0, double grad_clip = 0.0, double privacy_eps = 0.0)
{

    using glm::DenseDataset;
    using glm::SparseDataset;

    try {
        if (!privacy) {
            if (transpose) {
                auto objective = std::make_shared<O_p>(lambda, w_pos, w_neg);
                if (is_sparse) {
                    model = train_model<SparseDataset, O_p>(static_cast<SparseDataset*>(data), objective.get(),
                                                            num_epochs, use_gpu, device_ids, n_iter, support_vectors,
                                                            history, return_training_history, 0, num_threads, verbose,
                                                            tol, fit_intercept, intercept_scaling);
                } else {
                    model = train_model<DenseDataset, O_p>(static_cast<DenseDataset*>(data), objective.get(),
                                                           num_epochs, use_gpu, device_ids, n_iter, support_vectors,
                                                           history, return_training_history, 0, num_threads, verbose,
                                                           tol, fit_intercept, intercept_scaling);
                }
            } else {
                auto objective = std::make_shared<O_d>(lambda, w_pos, w_neg);
                if (is_sparse) {
                    model = train_model<SparseDataset, O_d>(static_cast<SparseDataset*>(data), objective.get(),
                                                            num_epochs, use_gpu, device_ids, n_iter, support_vectors,
                                                            history, return_training_history, 0, num_threads, verbose,
                                                            tol, fit_intercept, intercept_scaling);
                } else {
                    model = train_model<DenseDataset, O_d>(static_cast<DenseDataset*>(data), objective.get(),
                                                           num_epochs, use_gpu, device_ids, n_iter, support_vectors,
                                                           history, return_training_history, 0, num_threads, verbose,
                                                           tol, fit_intercept, intercept_scaling);
                }
            }
        } else { // if(!privacy)
            // get sigma (will throw an exception if it can't)
            double privacy_sigma = glm::privacy::find_sigma_for_privacy((uint32_t)num_epochs, (uint32_t)num_ex,
                                                                        batch_size, privacy_eps, 0.01);

            auto objective = std::make_shared<O_p>(lambda, w_pos, w_neg);
            if (is_sparse) {
                model = train_sgd_model<SparseDataset, O_p>(
                    static_cast<SparseDataset*>(data), objective.get(), static_cast<uint32_t>(num_epochs), history,
                    static_cast<uint32_t>(return_training_history), num_threads, verbose, tol, eta,
                    static_cast<uint32_t>(batch_size), grad_clip, privacy_sigma);
            } else {
                model = train_sgd_model<DenseDataset, O_p>(
                    static_cast<DenseDataset*>(data), objective.get(), static_cast<uint32_t>(num_epochs), history,
                    static_cast<uint32_t>(return_training_history), num_threads, verbose, tol, eta,
                    static_cast<uint32_t>(batch_size), grad_clip, privacy_sigma);
            }
        }
    } catch (const std::exception& e) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->other_error, e.what());
        return wrapperError_t::Failure;
    }
    return wrapperError_t::Success;
}

template <class O_p, class O_d> PyObject* __fit(PyObject* m, PyObject* args)
{
    npy_int64      num_epochs;
    double         lambda;
    double         eps;
    npy_int64      verbose;
    npy_int64      balanced;
    npy_int64      use_gpu;
    npy_int64      num_threads;
    npy_int64      transpose;
    npy_int64      num_ex;
    npy_int64      num_ft;
    npy_int64      num_nz;
    PyArrayObject* py_indptr { nullptr };
    PyArrayObject* py_indices { nullptr };
    PyArrayObject* py_data { nullptr };
    PyArrayObject* py_labs { nullptr };
    PyArrayObject* py_device_ids;
    uint64_t       gpu_data_ptr;
    uint64_t       gpu_lab_ptr;
    npy_int64      gpu_matrix;
    char*          ptr_str;
    Py_ssize_t     ptr_len;
    int            lab_size;
    npy_int64      type;
    const char*    penalty;
    double         tol;
    npy_int64      return_training_history;
    npy_int64      privacy;
    double         eta;
    npy_int64      batch_size;
    double         grad_clip;
    double         privacy_eps;
    npy_int64      fit_intercept;
    double         intercept_scaling;
    npy_int64      is_regression;
    const char*    loss;

    if (!PyArg_ParseTuple(args, "LddLLLLLLLLO!O!O!O!LLLO!s#LsdLLdLddLLds", &num_epochs, &lambda, &eps, &verbose,
                          &balanced, &use_gpu, &num_threads, &transpose, &num_ex, &num_ft, &num_nz, &PyArray_Type,
                          &py_indptr, &PyArray_Type, &py_indices, &PyArray_Type, &py_data, &PyArray_Type, &py_labs,
                          &gpu_data_ptr, &gpu_lab_ptr, &gpu_matrix, &PyArray_Type, &py_device_ids, &ptr_str, &ptr_len,
                          &type, &penalty, &tol, &return_training_history, &privacy, &eta, &batch_size, &grad_clip,
                          &privacy_eps, &is_regression, &fit_intercept, &intercept_scaling, &loss)) {
        return NULL;
    }

    wrapperError_t chk;

    if (PyArray_TYPE(py_device_ids) != NPY_UINT32) {
        char                 message[] = "The elements device_ids have the wrong type. Expected type: uint32.";
        struct module_state* st        = GET_MODULE_STATE(m);
        PyErr_SetString(st->type_error, message);
        return NULL;
    }

    npy_intp device_ids_count = PyArray_SIZE(py_device_ids);

    glm::Dataset* data = NULL;

    if (ptr_len == 0) {
        bool is_sparse {};
        chk = check_numpy_args(m, py_indptr, py_indices, py_data, py_labs, is_sparse);
        if (chk != wrapperError_t::Success)
            return NULL;

        uint32_t num_pos = 0;
        uint32_t num_neg = 0;
        chk              = count_num_pos_neg(m, py_labs, num_pos, num_neg);
        if (chk != wrapperError_t::Success)
            return NULL;

        uint32_t this_num_pt    = transpose ? num_ft : num_ex;
        uint32_t num_partitions = 1;
        uint32_t partition_id   = 0;
        uint32_t this_pt_offset = 0;

        using glm::DenseDataset;
        using glm::SparseDataset;

        SparseDataset* data_train_s;
        DenseDataset*  data_train_d;

        try {
            if (is_sparse) {
                data_train_s = new SparseDataset(
                    transpose, static_cast<uint32_t>(num_ex), static_cast<uint32_t>(num_ft),
                    static_cast<uint32_t>(this_num_pt), num_partitions, partition_id, this_pt_offset,
                    static_cast<uint64_t>(num_nz), num_pos, num_neg, reinterpret_cast<float*>(PyArray_DATA(py_labs)),
                    reinterpret_cast<uint64_t*>(PyArray_DATA(py_indptr)),
                    reinterpret_cast<uint32_t*>(PyArray_DATA(py_indices)),
                    reinterpret_cast<float*>(PyArray_DATA(py_data)));
                type = 1;
                data = data_train_s;
            } else {
                if (!gpu_matrix) {
                    data_train_d
                        = new DenseDataset(transpose, static_cast<uint32_t>(num_ex), static_cast<uint32_t>(num_ft),
                                           static_cast<uint32_t>(this_num_pt), num_partitions, partition_id,
                                           this_pt_offset, static_cast<uint64_t>(num_nz), num_pos, num_neg,
                                           reinterpret_cast<float*>(PyArray_DATA(py_labs)),
                                           reinterpret_cast<float*>(PyArray_DATA(py_data)), false);
                } else {
                    data_train_d = new DenseDataset(
                        transpose, static_cast<uint32_t>(num_ex), static_cast<uint32_t>(num_ft),
                        static_cast<uint32_t>(this_num_pt), num_partitions, partition_id, this_pt_offset,
                        static_cast<uint64_t>(num_nz), num_pos, num_neg, reinterpret_cast<float*>(gpu_lab_ptr),
                        reinterpret_cast<float*>(gpu_data_ptr), true);
                }
                type = 0;
                data = data_train_d;
            }
        } catch (const std::exception& e) {
            struct module_state* st = GET_MODULE_STATE(m);
            PyErr_SetString(st->other_error, e.what());
            return NULL;
        }
    } else { // if (ptr_len == 0 )
        // check if the pointer length is 8
        assert(ptr_len == 8);

        uint64_t* ptr = reinterpret_cast<uint64_t*>(ptr_str);
        data          = reinterpret_cast<glm::Dataset*>(*ptr);
    }

    double w_pos = 1.0;
    double w_neg = 1.0;

    if (balanced) {
        w_pos = data->get_num_ex() / (2.0 * data->get_num_pos());
        w_neg = data->get_num_ex() / (2.0 * data->get_num_neg());
    }

    std::vector<std::vector<double>>    models;
    std::vector<std::vector<history_t>> histories;
    std::vector<uint32_t>               support_vectors;
    uint32_t                            n_iter    = num_epochs;
    bool                                is_sparse = (type == 1);
    std::set<float>                     unique_labs;
    // keep track of labels change from 0,1 to -1,1 if binary classification
    int labels_flag = 0;

    std::vector<uint32_t> device_ids(device_ids_count);
    for (int i = 0; i < device_ids_count; i++) {
        device_ids[i] = *reinterpret_cast<uint32_t*>(PyArray_GETPTR1(py_device_ids, i));
    }

    if (is_regression == 1) {
        std::vector<double>    model;
        std::vector<history_t> history;

        chk = __train_model<O_p, O_d>(
            m, data, transpose, is_sparse, lambda, w_pos, w_neg, (uint32_t)num_ex, (uint32_t)num_epochs, use_gpu,
            device_ids, n_iter, support_vectors, model, history, (uint32_t)return_training_history, 0, num_threads,
            verbose, tol, fit_intercept, intercept_scaling, privacy, eta, batch_size, grad_clip, privacy_eps);
        if (chk != wrapperError_t::Success)
            return NULL;

        models.push_back(model);
        histories.push_back(history);
    } else // classification
    {
        // Identify all distinct classes in the data

        if (!gpu_matrix) {
            float* labs = data->get_labs();
            for (uint64_t i = 0; i < data->get_num_labs(); i++) {
                unique_labs.insert(labs[i]);
            }
            lab_size = unique_labs.size();
        } else {
            // GPU matrix support binary classification
            lab_size = 2;
        }

        // binary classification
        if (lab_size <= 2) {

            std::vector<double>    model;
            std::vector<history_t> history;
            // For GPU matrix, Label transformation is already done
            // by the upper python layer
            if (!gpu_matrix) {

                uint32_t is_zero      = 0;
                uint32_t is_one       = 0;
                uint32_t is_minus_one = 0;

                std::set<float>::iterator it;
                // iterate through the labels in the partition
                for (it = unique_labs.begin(); it != unique_labs.end(); ++it) {
                    if ((*it) == 0)
                        is_zero = 1;
                    if ((*it) == 1)
                        is_one = 1;
                    if ((*it) == -1)
                        is_minus_one = 1;
                }

                if ((is_zero == 1) && (is_one == 1)) {
                    data->set_labs(1);
                    labels_flag = 1;
                } else if ((is_one == 0) || (is_minus_one == 0)) {
                    char                 message[] = "The labels in the train dataset should be {-1, 1} or {0, 1}.";
                    struct module_state* st        = GET_MODULE_STATE(m);
                    PyErr_SetString(st->type_error, message);
                    return NULL;
                }
            }

            chk = __train_model<O_p, O_d>(
                m, data, transpose, is_sparse, lambda, w_pos, w_neg, (uint32_t)num_ex, (uint32_t)num_epochs, use_gpu,
                device_ids, n_iter, support_vectors, model, history, (uint32_t)return_training_history, 0, num_threads,
                verbose, tol, fit_intercept, intercept_scaling, privacy, eta, batch_size, grad_clip, privacy_eps);
            if (chk != wrapperError_t::Success)
                return NULL;

            if (!gpu_matrix)
                data->restore_labs();

            models.push_back(model);
            histories.push_back(history);
        }
        // multi-class classification
        else {
            std::set<float>::iterator it;
            for (it = unique_labs.begin(); it != unique_labs.end(); ++it) {
                std::vector<double>    model;
                std::vector<history_t> history;

                float f = *it;
                data->set_labs(f);

                uint32_t num_pos = data->get_num_pos();
                uint32_t num_neg = data->get_num_neg();

                if (balanced) {
                    w_pos = data->get_num_ex() / (2.0 * num_pos);
                    w_neg = data->get_num_ex() / (2.0 * num_neg);
                }

                chk = __train_model<O_p, O_d>(
                    m, data, transpose, is_sparse, lambda, w_pos, w_neg, static_cast<uint32_t>(num_ex),
                    static_cast<uint32_t>(num_epochs), use_gpu, device_ids, n_iter, support_vectors, model, history,
                    static_cast<uint32_t>(return_training_history), 0, num_threads, verbose, tol, fit_intercept,
                    intercept_scaling, privacy, eta, batch_size, grad_clip, privacy_eps);
                if (chk != wrapperError_t::Success)
                    return NULL;

                models.push_back(model);
                histories.push_back(history);
            }
            // set labels to original values
            data->restore_labs();
        }
    }

    uint32_t  num_models = models.size();
    uint32_t  model_size = models[0].size();
    PyObject* pymodel;

    double* flat_model_ = new double[num_models * model_size];
    for (uint32_t i = 0; i < num_models; i++) {
        for (uint32_t j = 0; j < model_size; j++) {
            flat_model_[(i * model_size) + j] = models[i][j];
        }
    }
    npy_intp model_dims[2] = { num_models, model_size };
    pymodel                = reinterpret_cast<PyObject*>(
        PyArray_SimpleNewFromData(2, model_dims, NPY_FLOAT64, reinterpret_cast<void*>(flat_model_)));
    PyArray_ENABLEFLAGS(reinterpret_cast<PyArrayObject*>(pymodel), NPY_ARRAY_OWNDATA);
    // build a Python object training_metadata with the following information
    PyObject* training_metadata = PyDict_New();

    // number of unique classes in the train dataset: int
    PyDict_SetItemString(training_metadata, "num_uniq_labs", PyLong_FromLong(unique_labs.size()));

    uint32_t i = 0;
    // list of unique classes in the train dataset: list
    PyObject* train_classes = PyList_New(unique_labs.size());
    for (std::set<float>::iterator it = unique_labs.begin(); it != unique_labs.end(); ++it) {
        PyList_SetItem(train_classes, i++, PyFloat_FromDouble(*it));
    }
    PyDict_SetItemString(training_metadata, "uniq_labs", train_classes);

    // train dataset labels conversion flag : int
    PyDict_SetItemString(training_metadata, "labs_converted", PyLong_FromLong(labels_flag));

    // model size : int
    PyDict_SetItemString(training_metadata, "model_size", PyLong_FromLong(model_size));

    // make support vector py object
    PyObject* pysupportvectors = PyList_New(support_vectors.size());
    for (uint32_t i = 0; i < support_vectors.size(); i++) {
        PyList_SetItem(pysupportvectors, i, PyFloat_FromDouble(support_vectors[i]));
    }

    // build Python object for the training history
    PyObject* pyhistories = PyList_New(histories.size());

    // make dictionary with training histor(ies)
    for (uint32_t i = 0; i < histories.size(); i++) {
        if (i < histories.size()) {
            std::vector<history_t> history   = histories[i];
            PyObject*              pyhistory = Py_None;

            if (history.size()) {
                PyObject* pyhistory_epochs;
                if (history.size() > 1) {
                    pyhistory_epochs = PyList_New(history.size());
                    for (uint32_t i = 0; i < history.size(); i++) {
                        PyList_SetItem(pyhistory_epochs, i, PyLong_FromLong(history[i].epoch));
                    }
                } else {
                    pyhistory_epochs = PyLong_FromLong(history[0].epoch);
                }

                PyObject* pyhistory_time;
                if (history.size() > 1) {
                    pyhistory_time = PyList_New(history.size());
                    for (uint32_t i = 0; i < history.size(); i++) {
                        PyList_SetItem(pyhistory_time, i, PyFloat_FromDouble(history[i].t_elap_sec));
                    }
                } else {
                    pyhistory_time = PyFloat_FromDouble(history[0].t_elap_sec);
                }

                PyObject* pyhistory_obj;
                if (history.size() > 1) {
                    pyhistory_obj = PyList_New(history.size());
                    for (uint32_t i = 0; i < history.size(); i++) {
                        PyList_SetItem(pyhistory_obj, i, PyFloat_FromDouble(history[i].train_obj));
                    }
                } else {
                    pyhistory_obj = PyFloat_FromDouble(history[0].train_obj);
                }

                pyhistory = PyDict_New();
                PyDict_SetItemString(pyhistory, "epochs", pyhistory_epochs);
                PyDict_SetItemString(pyhistory, "t_elap_sec", pyhistory_time);
                PyDict_SetItemString(pyhistory, "train_obj", pyhistory_obj);

                PyList_SetItem(pyhistories, i, pyhistory);
            }
        }
    }

    // make output
    PyObject* output
        = Py_BuildValue("OOOOO", pymodel, pyhistories, pysupportvectors, PyLong_FromLong(n_iter), training_metadata);
    Py_DECREF(pymodel);
    Py_DECREF(pyhistories);
    Py_DECREF(pysupportvectors);
    Py_DECREF(training_metadata);

    // TPA -- this is a bit exotic - do we really need to do this?? [very minor]
    std::vector<uint32_t>().swap(device_ids);

    return output;
}

PyObject* lr_fit(PyObject* dummy, PyObject* args)
{
    npy_int64      num_epochs;
    double         lambda;
    double         eps;
    npy_int64      verbose;
    npy_int64      balanced;
    npy_int64      use_gpu;
    npy_int64      num_threads;
    npy_int64      transpose;
    npy_int64      num_ex;
    npy_int64      num_ft;
    npy_int64      num_nz;
    PyArrayObject* py_indptr;
    PyArrayObject* py_indices;
    PyArrayObject* py_data;
    PyArrayObject* py_labs;
    uint64_t       gpu_data_ptr;
    uint64_t       gpu_lab_ptr;
    npy_int64      gpu_matrix;
    char*          ptr_str;
    Py_ssize_t     ptr_len;
    npy_int64      type;
    PyArrayObject* py_device_ids;
    npy_int64      fit_intercept;
    double         intercept_scaling;

    const char* penalty;
    char        l1string[] = "l1";
    double      tol;
    npy_int64   return_training_history;
    npy_int64   privacy;
    double      eta;
    npy_int64   batch_size;
    double      grad_clip;
    double      privacy_eps;
    npy_int64   is_regression;
    const char* loss;

    using glm::DualLogisticRegression;
    using glm::PrimalLogisticRegression;
    using glm::PrimalSparseLogisticRegression;

    if (!PyArg_ParseTuple(args, "LddLLLLLLLLO!O!O!O!LLLO!s#LsdLLdLddLLds",

                          &num_epochs, &lambda, &eps, &verbose, &balanced, &use_gpu, &num_threads, &transpose, &num_ex,
                          &num_ft, &num_nz, &PyArray_Type, &py_indptr, &PyArray_Type, &py_indices, &PyArray_Type,
                          &py_data, &PyArray_Type, &py_labs, &gpu_data_ptr, &gpu_lab_ptr, &gpu_matrix, &PyArray_Type,
                          &py_device_ids, &ptr_str, &ptr_len, &type, &penalty, &tol, &return_training_history, &privacy,
                          &eta, &batch_size, &grad_clip, &privacy_eps, &is_regression, &fit_intercept,
                          &intercept_scaling, &loss)) {
        return NULL;
    }

    // If L1 regularization use the Sparse Primal Logisitc Regression Objective
    if (!strcmp(penalty, l1string))
        return __fit<PrimalSparseLogisticRegression, PrimalSparseLogisticRegression>(dummy, args);

    return __fit<PrimalLogisticRegression, DualLogisticRegression>(dummy, args);
}

PyObject* svm_fit(PyObject* dummy, PyObject* args)
{

    npy_int64      num_epochs;
    double         lambda;
    double         eps;
    npy_int64      verbose;
    npy_int64      balanced;
    npy_int64      use_gpu;
    npy_int64      num_threads;
    npy_int64      transpose;
    npy_int64      num_ex;
    npy_int64      num_ft;
    npy_int64      num_nz;
    PyArrayObject* py_indptr;
    PyArrayObject* py_indices;
    PyArrayObject* py_data;
    PyArrayObject* py_labs;
    uint64_t       gpu_data_ptr;
    uint64_t       gpu_lab_ptr;
    npy_int64      gpu_matrix;
    char*          ptr_str;
    Py_ssize_t     ptr_len;
    npy_int64      type;
    PyArrayObject* py_device_ids;
    npy_int64      fit_intercept;
    double         intercept_scaling;

    const char* penalty;
    // char        l1string[] = "l1";
    double    tol;
    npy_int64 return_training_history;
    npy_int64 privacy;
    double    eta;
    npy_int64 batch_size;
    double    grad_clip;
    double    privacy_eps;
    npy_int64 is_regression;

    const char* loss;
    char        hingestring[] = "hinge";

    if (!PyArg_ParseTuple(args, "LddLLLLLLLLO!O!O!O!LLLO!s#LsdLLdLddLLds",

                          &num_epochs, &lambda, &eps, &verbose, &balanced, &use_gpu, &num_threads, &transpose, &num_ex,
                          &num_ft, &num_nz, &PyArray_Type, &py_indptr, &PyArray_Type, &py_indices, &PyArray_Type,
                          &py_data, &PyArray_Type, &py_labs, &gpu_data_ptr, &gpu_lab_ptr, &gpu_matrix, &PyArray_Type,
                          &py_device_ids, &ptr_str, &ptr_len, &type, &penalty, &tol, &return_training_history, &privacy,
                          &eta, &batch_size, &grad_clip, &privacy_eps, &is_regression, &fit_intercept,
                          &intercept_scaling, &loss)) {
        return NULL;
    }

    using glm::DualL1SupportVectorMachine;
    using glm::DualL2SupportVectorMachine;

    if (!strcmp(loss, hingestring))
        return __fit<glm::DualL1SupportVectorMachine, glm::DualL1SupportVectorMachine>(dummy, args);

    return __fit<DualL2SupportVectorMachine, DualL2SupportVectorMachine>(dummy, args);
}

PyObject* linear_fit(PyObject* dummy, PyObject* args)
{
    npy_int64      num_epochs;
    double         lambda;
    double         eps;
    npy_int64      verbose;
    npy_int64      balanced;
    npy_int64      use_gpu;
    npy_int64      num_threads;
    npy_int64      transpose;
    npy_int64      num_ex;
    npy_int64      num_ft;
    npy_int64      num_nz;
    PyArrayObject* py_indptr;
    PyArrayObject* py_indices;
    PyArrayObject* py_data;
    PyArrayObject* py_labs;
    PyArrayObject* py_device_ids;
    uint64_t       gpu_data_ptr;
    uint64_t       gpu_lab_ptr;
    npy_int64      gpu_matrix;
    char*          ptr_str;
    Py_ssize_t     ptr_len;
    npy_int64      type;
    npy_int64      fit_intercept;
    double         intercept_scaling;

    const char* penalty;
    char        l1string[] = "l1";
    double      tol;
    npy_int64   return_training_history;
    npy_int64   privacy;
    double      eta;
    double      batch_size;
    npy_int64   grad_clip;
    double      privacy_eps;
    npy_int64   is_regression;
    const char* loss;

    if (!PyArg_ParseTuple(args, "LddLLLLLLLLO!O!O!O!LLLO!s#LsdLLdLddLLds", &num_epochs, &lambda, &eps, &verbose,
                          &balanced, &use_gpu, &num_threads, &transpose, &num_ex, &num_ft, &num_nz, &PyArray_Type,
                          &py_indptr, &PyArray_Type, &py_indices, &PyArray_Type, &py_data, &PyArray_Type, &py_labs,
                          &gpu_data_ptr, &gpu_lab_ptr, &gpu_matrix, &PyArray_Type, &py_device_ids, &ptr_str, &ptr_len,
                          &type, &penalty, &tol, &return_training_history, &privacy, &eta, &batch_size, &grad_clip,
                          &privacy_eps, &is_regression, &fit_intercept, &intercept_scaling, &loss)) {
        return NULL;
    }

    using glm::DualRidgeRegression;
    using glm::PrimalLassoRegression;
    using glm::PrimalRidgeRegression;

    // If Lasso L1 regularization use the Lasso Primal Regression Objective
    if (!strcmp(penalty, l1string))
        return __fit<PrimalLassoRegression, PrimalLassoRegression>(dummy, args);

    // Otherwise use L2 regularization, deafult Ridge Regression
    return __fit<PrimalRidgeRegression, DualRidgeRegression>(dummy, args);
}

template <class D>
wrapperError_t __generic_predict(PyObject* m, prediction_t sel, D* data, double* model_cpp, uint32_t model_len,
                                 double* pred, uint32_t num_threads, bool fit_intercept, double intercept_scaling,
                                 uint32_t& num_labs)
{

    try {

        switch (sel) {
        case prediction_t::LinearRegression:
            glm::predictors::jni::linear_prediction<D>(data, model_cpp, model_len, pred, num_threads, fit_intercept,
                                                       intercept_scaling);
            break;
        case prediction_t::LinearClassification:
            glm::predictors::jni::linear_classification<D>(data, model_cpp, model_len, pred, 0.0, num_threads,
                                                           fit_intercept, intercept_scaling);
            break;
        case prediction_t::LogisticProbabilities:
            glm::predictors::jni::logistic_probabilities<D>(data, model_cpp, model_len, pred, num_threads,
                                                            fit_intercept, intercept_scaling);
            break;
        default:
            throw std::runtime_error("Unrecognized prediction_t");
        }

        num_labs = data->get_num_labs();

    } catch (const std::exception& e) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->other_error, e.what());
        return wrapperError_t::Failure;
    }

    return wrapperError_t::Success;
}

PyObject* __predict(PyObject* m, PyObject* args, prediction_t sel)
{
    npy_int64      num_ex;
    npy_int64      num_ft;
    PyArrayObject* py_indptr { nullptr };
    PyArrayObject* py_indices { nullptr };
    PyArrayObject* py_data { nullptr };
    PyArrayObject* model;
    npy_int64      model_len;
    npy_int64      num_train_unique_labs;
    npy_int64      is_regression;
    npy_int64      num_threads;
    npy_int64      fit_intercept;
    double         intercept_scaling;
    char*          ptr_str;
    Py_ssize_t     ptr_len;
    npy_int64      type;
    bool           is_sparse {};

    if (!PyArg_ParseTuple(args, "LLO!O!O!O!s#LLLLLLd", &num_ex, &num_ft, &PyArray_Type, &py_indptr, &PyArray_Type,
                          &py_indices, &PyArray_Type, &py_data, &PyArray_Type, &model, &ptr_str, &ptr_len, &type,
                          &model_len, &num_train_unique_labs, &is_regression, &num_threads, &fit_intercept,
                          &intercept_scaling)) {
        return NULL;
    }

    wrapperError_t chk;

    using glm::DenseDataset;
    using glm::SparseDataset;

    glm::Dataset*                       data_ptr = NULL;
    std::shared_ptr<glm::SparseDataset> sparse_data;
    std::shared_ptr<glm::DenseDataset>  dense_data;

    if (ptr_len == 0) {
        chk = check_numpy_args(m, py_indptr, py_indices, py_data, nullptr, is_sparse);
        if (chk != wrapperError_t::Success)
            return NULL;

        if (is_sparse) {
            chk = make_sparse_dataset(m, num_ex, num_ft, 0, 0, 0, py_indptr, py_indices, py_data, nullptr, sparse_data);
            if (chk != wrapperError_t::Success)
                return NULL;
            data_ptr = sparse_data.get();
        } else {
            chk = make_dense_dataset(m, num_ex, num_ft, num_ex * num_ft, 0, 0, py_data, nullptr, dense_data);
            if (chk != wrapperError_t::Success)
                return NULL;
            data_ptr = dense_data.get();
        }
        num_ex = data_ptr->get_num_labs();
    } else {
        // check if the pointer length is 8
        assert(ptr_len == 8);

        uint64_t* ptr = reinterpret_cast<uint64_t*>(ptr_str);
        data_ptr      = reinterpret_cast<glm::Dataset*>(*ptr);
        num_ex        = data_ptr->get_num_labs();
        is_sparse     = (type == 1);
    }

    double*  model_cpp = reinterpret_cast<double*>(PyArray_DATA(model));
    uint32_t num_labs  = 0;

    uint32_t num_calls
        = (is_regression == 1 || ((is_regression == 0) && (num_train_unique_labs == 2))) ? 1 : num_train_unique_labs;

    if (sel == prediction_t::LinearClassification && (num_train_unique_labs > 2)) {
        sel = prediction_t::LogisticProbabilities;
    }

    double* pred = new double[num_calls * num_ex];

    for (uint32_t i = 0; i < num_calls; i++) {

        if (is_sparse) {
            __generic_predict<glm::SparseDataset>(m, sel, reinterpret_cast<SparseDataset*>(data_ptr),
                                                  &(model_cpp[i * model_len]), model_len, &pred[i * num_ex],
                                                  num_threads, fit_intercept, intercept_scaling, num_labs);
        } else {
            __generic_predict<glm::DenseDataset>(m, sel, reinterpret_cast<DenseDataset*>(data_ptr),
                                                 &(model_cpp[i * model_len]), model_len, &pred[i * num_ex], num_threads,
                                                 fit_intercept, intercept_scaling, num_labs);
        }
    }

    PyArrayObject* np_out;
    if (num_calls > 1) {
        npy_intp dims[2] { num_calls, num_ex };
        np_out = reinterpret_cast<PyArrayObject*>(
            PyArray_SimpleNewFromData(2, dims, NPY_DOUBLE, reinterpret_cast<void*>(pred)));
    } else {
        npy_intp dims[1] { num_ex };
        np_out = reinterpret_cast<PyArrayObject*>(
            PyArray_SimpleNewFromData(1, dims, NPY_DOUBLE, reinterpret_cast<void*>(pred)));
    }
    PyArray_ENABLEFLAGS(np_out, NPY_ARRAY_OWNDATA);

    PyObject* output = Py_BuildValue("O", np_out);
    Py_DECREF(np_out);

    return output;
}

PyObject* lr_predict_proba(PyObject* dummy, PyObject* args)
{
    return __predict(dummy, args, prediction_t::LogisticProbabilities);
}

PyObject* lr_predict(PyObject* dummy, PyObject* args)
{
    return __predict(dummy, args, prediction_t::LinearClassification);
}

PyObject* svm_predict(PyObject* dummy, PyObject* args)
{
    return __predict(dummy, args, prediction_t::LinearClassification);
}

PyObject* svm_decision_function(PyObject* dummy, PyObject* args)
{
    return __predict(dummy, args, prediction_t::LinearRegression);
}

PyObject* linear_predict(PyObject* dummy, PyObject* args)
{
    return __predict(dummy, args, prediction_t::LinearRegression);
}
