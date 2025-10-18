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

/*! @file
 *  @ingroup wrapper
 */

#define NO_IMPORT_ARRAY
#include "Wrapper.h"

#include <functional>

#include "OMP.hpp"

#include "DecisionTreeBuilder.hpp"
#include "DecisionTreePredictor.hpp"
#include "DenseDataset.hpp"
#include "DecisionTreeModel.hpp"
#include "DenseDatasetInt.hpp"

wrapperError_t _dtc_fit(snapml::DecisionTreeParams params, PyObject* m, snapml::DenseDataset data, float* sample_weight,
                        PyObject** feature_importances_out, PyObject* model_ptr)
{

    try {
        std::shared_ptr<snapml::DecisionTreeBuilder> builder;

        builder = std::static_pointer_cast<snapml::DecisionTreeBuilder>(
            std::make_shared<snapml::DecisionTreeBuilder>(data, &params));

        builder->init();
        builder->build(sample_weight);

        double* const feature_importances
            = new double[static_cast<int64_t>(static_cast<glm::DenseDatasetInt*>(&data)->get_num_ft())];

        builder->get_feature_importances(feature_importances, static_cast<glm::DenseDatasetInt*>(&data)->get_num_ft());

        snapml::DecisionTreeModel model = builder->get_model();

        std::vector<uint8_t>* vec = reinterpret_cast<std::vector<uint8_t>*>(PyCapsule_GetPointer(model_ptr, NULL));
        if (vec == nullptr) {
            struct module_state* st = GET_MODULE_STATE(m);
            PyErr_SetString(st->type_error, "No model_ptr available.");
            return wrapperError_t::Failure;
        }
        model.get(*vec);

        npy_intp        ft_dims[] { static_cast<int64_t>(static_cast<glm::DenseDatasetInt*>(&data)->get_num_ft()) };
        PyObject* const py_feature_importances = reinterpret_cast<PyObject*>(
            PyArray_SimpleNewFromData(1, ft_dims, NPY_DOUBLE, reinterpret_cast<void*>(feature_importances)));

        *feature_importances_out = py_feature_importances;

    } catch (const std::exception& e) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->other_error, e.what());
        return wrapperError_t::Failure;
    }

    return wrapperError_t::Success;
}

wrapperError_t __dtc_predict(PyObject* m, snapml::DenseDataset data, double* pred, uint32_t num_threads, bool proba,
                             PyObject* model_ptr)
{

    try {

        snapml::DecisionTreeModel model;

        std::vector<uint8_t>* vec = reinterpret_cast<std::vector<uint8_t>*>(PyCapsule_GetPointer(model_ptr, NULL));
        if (vec == nullptr) {
            struct module_state* st = GET_MODULE_STATE(m);
            PyErr_SetString(st->type_error, "No model_ptr available.");
            return wrapperError_t::Failure;
        }
        model.put(*vec);

        snapml::DecisionTreePredictor predictor = snapml::DecisionTreePredictor(model);

        if (proba) {
            predictor.predict_proba(data, pred, num_threads);
        } else {
            predictor.predict(data, pred, num_threads);
        }

    } catch (const std::exception& e) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->other_error, e.what());
        return wrapperError_t::Failure;
    }

    return wrapperError_t::Success;
}

PyObject* dtc_fit(PyObject* m, PyObject* args)
{
    const char*    task            = nullptr;
    const char*    split_criterion = nullptr;
    npy_int64      max_depth;
    npy_int64      min_samples_leaf;
    npy_int64      max_features;
    npy_int64      random_state;
    npy_int64      verbose;
    npy_int64      n_threads;
    npy_int64      use_histograms;
    npy_int64      hist_nbins;
    npy_int64      use_gpu;
    npy_int64      gpu_id;
    npy_int64      num_ex;
    npy_int64      num_ft;
    npy_int64      num_classes;
    PyArrayObject* py_indptr        = nullptr;
    PyArrayObject* py_indices       = nullptr;
    PyArrayObject* py_data          = nullptr;
    PyArrayObject* py_labs          = nullptr;
    PyArrayObject* py_sample_weight = nullptr;
    PyObject*      model_ptr        = nullptr;

    if (!PyArg_ParseTuple(args, "ssLLLLLLLLLLLLLO!O!O!O!O!O", &task, &split_criterion, &max_depth, &min_samples_leaf,
                          &max_features, &random_state, &verbose, &n_threads, &use_histograms, &hist_nbins, &use_gpu,
                          &gpu_id, &num_ex, &num_ft, &num_classes, &PyArray_Type, &py_indptr, &PyArray_Type,
                          &py_indices, &PyArray_Type, &py_data, &PyArray_Type, &py_labs, &PyArray_Type,
                          &py_sample_weight, &model_ptr)) {
        return NULL;
    }

    snapml::DecisionTreeParams params;
    if (!strcmp(task, "classification")) {
        params.task = snapml::task_t::classification;
    }
    if (!strcmp(task, "regression")) {
        params.task = snapml::task_t::regression;
    }
    if (!strcmp(split_criterion, "gini")) {
        params.split_criterion = snapml::split_t::gini;
    }
    if (!strcmp(split_criterion, "mse")) {
        params.split_criterion = snapml::split_t::mse;
    }
    params.max_depth        = max_depth;
    params.min_samples_leaf = min_samples_leaf;
    params.max_features     = max_features;
    params.random_state     = random_state;
    params.verbose          = verbose;
    params.n_threads        = n_threads;
    params.use_histograms   = use_histograms;
    params.hist_nbins       = hist_nbins;
    params.use_gpu          = use_gpu;
    params.gpu_id           = gpu_id;
    params.num_classes      = num_classes;

    if (!strcmp(task, "regression")) {
        params.num_classes = 2;
    }

    wrapperError_t chk {};

    chk = check_numpy_sample_weight(m, py_sample_weight, num_ex);
    if (chk != wrapperError_t::Success)
        return NULL;

    float* sample_weight
        = (PyArray_SIZE(py_sample_weight) > 0) ? static_cast<float*>(PyArray_DATA(py_sample_weight)) : nullptr;

    bool is_sparse {};
    chk = check_numpy_args(m, py_indptr, py_indices, py_data, py_labs, is_sparse);
    if (chk != wrapperError_t::Success)
        return NULL;

    PyObject* py_feature_importances = nullptr;

    assert(!is_sparse);

    snapml::DenseDataset data;

    chk = make_dense_dataset_api(m, num_ex, num_ft, py_data, py_labs, data);
    if (chk != wrapperError_t::Success)
        return NULL;

    chk = _dtc_fit(params, m, data, sample_weight, &py_feature_importances, model_ptr);
    if (chk != wrapperError_t::Success)
        return NULL;

    // build a Python object training_metadata with the following information
    PyArray_ENABLEFLAGS(reinterpret_cast<PyArrayObject*>(py_feature_importances), NPY_ARRAY_OWNDATA);
    PyObject* output = Py_BuildValue("O", py_feature_importances);
    Py_DECREF(py_feature_importances);

    return output;
}

PyObject* dtc_predict(PyObject* m, PyObject* args)
{
    npy_int64      num_ex {};
    npy_int64      num_ft {};
    PyArrayObject* py_indptr  = nullptr;
    PyArrayObject* py_indices = nullptr;
    PyArrayObject* py_data    = nullptr;
    npy_int64      num_threads {};
    npy_int64      proba {};
    npy_int64      num_classes {};
    PyObject*      model_ptr = nullptr;

    if (!PyArg_ParseTuple(args, "LLO!O!O!LLLO", &num_ex, &num_ft, &PyArray_Type, &py_indptr, &PyArray_Type, &py_indices,
                          &PyArray_Type, &py_data, &num_threads, &proba, &num_classes, &model_ptr)) {
        return NULL;
    }

    wrapperError_t chk {};

    bool is_sparse {};
    chk = check_numpy_args(m, py_indptr, py_indices, py_data, nullptr, is_sparse);
    if (chk != wrapperError_t::Success)
        return NULL;

    // store the predictions of the decision tree model
    // double* pred = new double[num_ex*(num_classes-1)];
    double* pred;
    if (proba == 1)
        pred = new double[num_ex * (num_classes - 1)];
    else
        pred = new double[num_ex];

    if (nullptr == pred)
        return nullptr;

    assert(!is_sparse);

    snapml::DenseDataset data;

    chk = make_dense_dataset_api(m, num_ex, num_ft, py_data, nullptr, data);
    if (chk != wrapperError_t::Success) {
        delete[] pred;
        return NULL;
    }

    chk = __dtc_predict(m, data, pred, num_threads, proba, model_ptr);
    if (chk != wrapperError_t::Success) {
        delete[] pred;
        return NULL;
    }

    PyArrayObject* np_pred;
    npy_intp       dims[1];

    if (proba == 1)
        dims[0] = num_ex * (num_classes - 1);
    else
        dims[0] = num_ex;

    np_pred = reinterpret_cast<PyArrayObject*>(
        PyArray_SimpleNewFromData(1, dims, NPY_DOUBLE, reinterpret_cast<void*>(pred)));
    PyArray_ENABLEFLAGS(np_pred, NPY_ARRAY_OWNDATA);

    PyObject* output = Py_BuildValue("O", np_pred);
    Py_DECREF(np_pred);

    return output;
}
