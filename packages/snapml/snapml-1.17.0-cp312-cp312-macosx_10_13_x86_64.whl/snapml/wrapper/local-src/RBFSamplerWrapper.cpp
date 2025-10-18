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
 * Authors      : Andreea Anghel
 *
 * End Copyright
 ********************************************************************/

/*! @file
 *  @ingroup wrapper
 */

#define NO_IMPORT_ARRAY

#include "Wrapper.h"
#include "DenseDatasetInt.hpp"
#include "RBFSampler.hpp"

PyObject* rbf_fit(PyObject* m, PyObject* args)
{

    double    gamma;
    npy_int64 n_components;
    npy_int64 random_state;
    npy_int64 num_ft;

    if (!PyArg_ParseTuple(args, "dlll", &gamma, &n_components, &random_state, &num_ft)) {
        return NULL;
    }

    struct RBFSamplerParams params;
    params.gamma        = gamma;
    params.n_components = n_components;
    params.random_state = random_state;

    auto rbf_sampler = std::make_shared<RBFSampler>(params);

    rbf_sampler->fit(num_ft);

    float* random_weights_ = rbf_sampler->get_feature_map_weights();
    float* random_offsets_ = rbf_sampler->get_feature_map_offsets();

    float* random_weights = new float[num_ft * n_components];
    float* random_offsets = new float[n_components];

    memcpy(random_weights, random_weights_, num_ft * n_components * sizeof(float));
    memcpy(random_offsets, random_offsets_, n_components * sizeof(float));

    /* for(uint32_t i = 0; i < num_ft*n_components; i++) {
        std::cout << "[CPython - fit] weights " << random_weights[i] << std::endl;
    }

    for(uint32_t i = 0; i < n_components; i++) {
        std::cout << "[CPython - fit] offsets " << random_offsets[i] << std::endl;
    }*/

    PyObject* pyweights;
    PyObject* pyoffsets;

    npy_intp dims[] { num_ft * n_components };
    pyweights = reinterpret_cast<PyObject*>(
        PyArray_SimpleNewFromData(1, dims, NPY_FLOAT32, reinterpret_cast<void*>(random_weights)));
    PyArray_ENABLEFLAGS(reinterpret_cast<PyArrayObject*>(pyweights), NPY_ARRAY_OWNDATA);

    dims[0]   = n_components;
    pyoffsets = reinterpret_cast<PyObject*>(
        PyArray_SimpleNewFromData(1, dims, NPY_FLOAT32, reinterpret_cast<void*>(random_offsets)));
    PyArray_ENABLEFLAGS(reinterpret_cast<PyArrayObject*>(pyoffsets), NPY_ARRAY_OWNDATA);

    PyObject* output = Py_BuildValue("OOO", pyweights, pyoffsets, PyLong_FromLong(num_ft * n_components));
    Py_DECREF(pyweights);
    Py_DECREF(pyoffsets);

    return output;
}

PyObject* rbf_transform(PyObject* m, PyObject* args)
{
    npy_int64      num_ex;
    npy_int64      num_ft;
    PyArrayObject* py_data;
    PyArrayObject* py_weights;
    npy_int64      py_weights_len;
    PyArrayObject* py_offsets;
    npy_int64      num_threads;
    double         gamma;
    npy_int64      n_components;
    npy_int64      random_state;

    if (!PyArg_ParseTuple(args, "LLO!O!LO!LdLL", &num_ex, &num_ft, &PyArray_Type, &py_data, &PyArray_Type, &py_weights,
                          &py_weights_len, &PyArray_Type, &py_offsets, &num_threads, &gamma, &n_components,
                          &random_state)) {
        return NULL;
    }

    wrapperError_t chk;

    std::shared_ptr<glm::DenseDataset> data;
    chk = make_dense_dataset(m, num_ex, num_ft, num_ex * num_ft, 0, 0, py_data, nullptr, data);
    if (chk != wrapperError_t::Success)
        return NULL;

    float* weights_cpp = reinterpret_cast<float*>(PyArray_DATA(py_weights));
    float* offsets_cpp = reinterpret_cast<float*>(PyArray_DATA(py_offsets));

    /*
    for(uint32_t i = 0; i < num_ft*n_components; i++) {
        std::cout << "[CPython - transform] weights " << weights_cpp[i] << std::endl;
    }

    for(uint32_t i = 0; i < n_components; i++) {
        std::cout << "[CPython - transform] offsets " << offsets_cpp[i] << std::endl;
    }*/

    struct RBFSamplerParams params;
    params.gamma        = gamma;
    params.n_components = n_components;
    params.random_state = random_state;

    auto rbf_sampler = std::make_shared<RBFSampler>(params, weights_cpp, py_weights_len, offsets_cpp, n_components);

    std::vector<float> new_data = rbf_sampler->transform(data.get(), num_threads);

    float* out = new float[new_data.size()];
    memcpy(out, new_data.data(), new_data.size() * sizeof(float));

    PyObject* py_new_data;

    npy_intp dims[] { num_ex * n_components };
    py_new_data
        = reinterpret_cast<PyObject*>(PyArray_SimpleNewFromData(1, dims, NPY_FLOAT32, reinterpret_cast<void*>(out)));
    PyArray_ENABLEFLAGS(reinterpret_cast<PyArrayObject*>(py_new_data), NPY_ARRAY_OWNDATA);

    PyObject* output = Py_BuildValue("O", py_new_data);
    Py_DECREF(py_new_data);

    return output;
}
