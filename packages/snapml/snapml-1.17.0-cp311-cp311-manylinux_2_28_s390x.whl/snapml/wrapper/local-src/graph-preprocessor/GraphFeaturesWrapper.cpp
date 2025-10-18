/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2022
 * IBM Zurich Research Laboratory - Infrastructure AIOPS Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Kubilay Atasu
 *                Jovan Blanusa
 *
 * End Copyright
 ********************************************************************/

#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>

#define NO_IMPORT_ARRAY
#include <numpy/arrayobject.h>

#include <exception>
#include <unordered_map>
#include <string>
#include <vector>
#include <exception>
#include "GraphFeatures.h"

struct module_state_ {
    PyObject* type_error;
    PyObject* other_error;
};

#define PyInt_FromLong      PyLong_FromLong
#define GET_MODULE_STATE(m) (reinterpret_cast<module_state_*>(PyModule_GetState(m)))
#define INITERROR           return NULL

#include <iostream>
using namespace std;
using namespace GraphFeatures;

void pygraphfeatures_delete(PyObject* gp_ptr)
{
    GraphFeaturePreprocessor* gp = reinterpret_cast<GraphFeaturePreprocessor*>(PyCapsule_GetPointer(gp_ptr, NULL));

    delete gp;
}

PyObject* pygraphfeatures_allocate(PyObject* self)
{
    GraphFeaturePreprocessor* gp = new GraphFeaturePreprocessor;

    if (gp == nullptr) {
        struct module_state_* st = GET_MODULE_STATE(self);
        PyErr_SetString(st->other_error, "Unable to allocate memory for the preprocessor.");
        return NULL;
    }

    PyObject* gp_ptr = PyCapsule_New(gp, NULL, pygraphfeatures_delete);

    return gp_ptr;
}

PyObject* pygraphfeatures_set_params(PyObject* self, PyObject* args)
{
    PyObject* gp_ptr;
    PyObject* gp_dict;

    if (!PyArg_ParseTuple(args, "OO", &gp_ptr, &gp_dict))
        return NULL;

    GraphFeaturePreprocessor* gp = reinterpret_cast<GraphFeaturePreprocessor*>(PyCapsule_GetPointer(gp_ptr, NULL));

    if (gp == nullptr) {
        struct module_state_* st = GET_MODULE_STATE(self);
        PyErr_SetString(st->type_error, "The graph preprocessor is not available.");
        return NULL;
    }

    if (!PyDict_Check(gp_dict)) {
        struct module_state_* st = GET_MODULE_STATE(self);
        PyErr_SetString(st->type_error, "The input argument is not a dictionary.");
        return NULL;
    }

    unordered_map<string, int>         intParams;
    unordered_map<string, vector<int>> vecParams;
    Py_ssize_t                         pos = 0;
    PyObject *                         pykey, *pyvalue;

    string message;
    bool   report_error = false;

    while (PyDict_Next(gp_dict, &pos, &pykey, &pyvalue)) {
        string key;
        if (PyUnicode_Check(pykey)) {
            const char* ckey = PyUnicode_AsUTF8(pykey);
            key.assign(ckey);
        } else {
            message      = "Key of params must be a string.";
            report_error = true;
            break;
        }

        if (PyLong_Check(pyvalue)) {
            int value      = PyLong_AsLong(pyvalue);
            intParams[key] = value;
        } else if (PyList_Check(pyvalue)) {
            vector<int> value {};

            Py_ssize_t size = PyList_Size(pyvalue);
            value.reserve(size);

            for (Py_ssize_t index = 0; index < size; index++) {
                PyObject* pyvalelem = PyList_GetItem(pyvalue, index);

                if (!PyLong_Check(pyvalelem)) {
                    message      = "Value of params must be an integer or a list of integers.";
                    report_error = true;
                    break;
                }
                int valelem = PyLong_AsLong(pyvalelem);

                value.push_back(valelem);
            }
            if (report_error)
                break;

            vecParams[key] = std::move(value);
        } else {
            message      = "Value of params must be an integer or a list of integers.";
            report_error = true;
            break;
        }
    }
    if (report_error) {
        struct module_state_* st = GET_MODULE_STATE(self);
        PyErr_SetString(st->type_error, message.c_str());
        return PyInt_FromLong(-1);
    }

    try {
        gp->setParams(intParams, vecParams);
    } catch (const std::exception& e) {
        struct module_state_* st = GET_MODULE_STATE(self);
        PyErr_SetString(st->other_error, e.what());
        return PyInt_FromLong(-1);
    }

    return PyInt_FromLong(-1);
}

PyObject* pygraphfeatures_get_output_array_dims(PyObject* self, PyObject* args)
{
    PyObject* gp_ptr;
    if (!PyArg_ParseTuple(args, "O", &gp_ptr))
        return NULL;

    GraphFeaturePreprocessor* gp = reinterpret_cast<GraphFeaturePreprocessor*>(PyCapsule_GetPointer(gp_ptr, NULL));
    if (gp == nullptr) {
        struct module_state_* st = GET_MODULE_STATE(self);
        PyErr_SetString(st->type_error, "The graph preprocessor is not available.");
        return NULL;
    }

    pair<uint64_t, uint64_t> out_dims;

    try {
        out_dims = gp->getOutputArrayDimensions();
    } catch (const std::exception& e) {
        struct module_state_* st = GET_MODULE_STATE(self);
        PyErr_SetString(st->other_error, e.what());
        return PyInt_FromLong(-1);
    }

    return Py_BuildValue("[kk]", out_dims.first, out_dims.second);
}

PyObject* pygraphfeatures_import_graph(PyObject* self, PyObject* args)
{
    PyObject*      gp_ptr;
    PyArrayObject* features_py_arr;

    string message;
    bool   report_error = false;

    if (!PyArg_ParseTuple(args, "OO", &gp_ptr, &features_py_arr))
        return NULL;

    GraphFeaturePreprocessor* gp = reinterpret_cast<GraphFeaturePreprocessor*>(PyCapsule_GetPointer(gp_ptr, NULL));
    if (gp == nullptr) {
        struct module_state_* st = GET_MODULE_STATE(self);
        PyErr_SetString(st->type_error, "The graph preprocessor is not available.");
        return NULL;
    }
    if (PyArray_NDIM(features_py_arr) != 2) {
        message      = "Input features must be a two-dimensional numpy array.";
        report_error = true;
    } else {
        if (PyArray_TYPE(features_py_arr) != NPY_FLOAT64) {
            message      = "The input features array uses the wrong data type. Expected data type: float64.";
            report_error = true;
        }
    }
    if (report_error) {
        struct module_state_* st = GET_MODULE_STATE(self);
        PyErr_SetString(st->type_error, message.c_str());
        return PyInt_FromLong(-1);
    }

    npy_intp* features_shape = PyArray_DIMS(features_py_arr);
    uint64_t  num_rows       = features_shape[0];
    uint64_t  num_cols       = features_shape[1];

    double* features = reinterpret_cast<double*>(PyArray_DATA(features_py_arr));

    try {
        gp->loadGraph(features, num_rows, num_cols);
    } catch (const std::exception& e) {
        struct module_state_* st = GET_MODULE_STATE(self);
        PyErr_SetString(st->other_error, e.what());
        return PyInt_FromLong(-1);
    }

    return PyInt_FromLong(-1);
}

PyObject* pygraphfeatures_export_graph(PyObject* self, PyObject* args)
{
    PyObject*      gp_ptr;
    PyArrayObject* features_py_arr;

    string message;
    bool   report_error = false;

    if (!PyArg_ParseTuple(args, "OO", &gp_ptr, &features_py_arr))
        return NULL;

    GraphFeaturePreprocessor* gp = reinterpret_cast<GraphFeaturePreprocessor*>(PyCapsule_GetPointer(gp_ptr, NULL));
    if (gp == nullptr) {
        struct module_state_* st = GET_MODULE_STATE(self);
        PyErr_SetString(st->type_error, "The graph preprocessor is not available.");
        return NULL;
    }

    if (PyArray_NDIM(features_py_arr) != 2) {
        message      = "Input features must be a two-dimensional numpy array.";
        report_error = true;
    } else {
        if (PyArray_TYPE(features_py_arr) != NPY_FLOAT64) {
            message      = "The input features array uses the wrong data type. Expected data type: float64.";
            report_error = true;
        }
    }
    if (report_error) {
        struct module_state_* st = GET_MODULE_STATE(self);
        PyErr_SetString(st->type_error, message.c_str());
        return PyInt_FromLong(-1);
    }

    npy_intp* features_shape = PyArray_DIMS(features_py_arr);
    uint64_t  num_rows       = features_shape[0];
    uint64_t  num_cols       = features_shape[1];

    double* features = reinterpret_cast<double*>(PyArray_DATA(features_py_arr));

    try {
        gp->exportGraph(features, num_rows, num_cols);
    } catch (const std::exception& e) {
        struct module_state_* st = GET_MODULE_STATE(self);
        PyErr_SetString(st->other_error, e.what());
        return PyInt_FromLong(-1);
    }

    return PyInt_FromLong(-1);
}

PyObject* pygraphfeatures_get_num_engineered_features(PyObject* self, PyObject* args)
{
    PyObject* gp_ptr;
    if (!PyArg_ParseTuple(args, "O", &gp_ptr))
        return NULL;

    GraphFeaturePreprocessor* gp = reinterpret_cast<GraphFeaturePreprocessor*>(PyCapsule_GetPointer(gp_ptr, NULL));
    if (gp == nullptr) {
        struct module_state_* st = GET_MODULE_STATE(self);
        PyErr_SetString(st->type_error, "The graph preprocessor is not available.");
        return NULL;
    }

    return PyInt_FromLong(gp->getNumEngineeredFeatures());
}

PyObject* pygraphfeatures_transform(PyObject* self, PyObject* args)
{
    PyObject*      gp_ptr;
    PyArrayObject* features_in_py_arr;
    PyArrayObject* features_out_py_arr;

    string message;
    bool   report_error = false;

    if (!PyArg_ParseTuple(args, "OOO", &gp_ptr, &features_in_py_arr, &features_out_py_arr))
        return NULL;

    GraphFeaturePreprocessor* gp = reinterpret_cast<GraphFeaturePreprocessor*>(PyCapsule_GetPointer(gp_ptr, NULL));
    if (gp == nullptr) {
        struct module_state_* st = GET_MODULE_STATE(self);
        PyErr_SetString(st->type_error, "The graph preprocessor is not available.");
        return NULL;
    }

    if (PyArray_NDIM(features_in_py_arr) != 2) {
        message      = "Input features must be a two-dimensional numpy array.";
        report_error = true;
    } else {
        if (PyArray_TYPE(features_in_py_arr) != NPY_FLOAT64) {
            message      = "The input features array uses the wrong data type. Expected data type: float64.";
            report_error = true;
        }
    }
    if (report_error) {
        struct module_state_* st = GET_MODULE_STATE(self);
        PyErr_SetString(st->type_error, message.c_str());
        return PyInt_FromLong(-1);
    }

    if (PyArray_NDIM(features_out_py_arr) != 2) {
        message      = "Output features must be a two-dimensional numpy array.";
        report_error = true;
    } else {
        if (PyArray_TYPE(features_out_py_arr) != NPY_FLOAT64) {
            message      = "The output features array uses the wrong data type. Expected data type: float64.";
            report_error = true;
        }
    }
    if (report_error) {
        struct module_state_* st = GET_MODULE_STATE(self);
        PyErr_SetString(st->type_error, message.c_str());
        return PyInt_FromLong(-1);
    }

    npy_intp* features_in_shape = PyArray_DIMS(features_in_py_arr);
    uint64_t  num_rows          = features_in_shape[0];
    uint64_t  num_cols_in       = features_in_shape[1];

    npy_intp* features_out_shape = PyArray_DIMS(features_out_py_arr);
    uint64_t  num_cols_out       = features_out_shape[1];

    double* features_in  = reinterpret_cast<double*>(PyArray_DATA(features_in_py_arr));
    double* features_out = reinterpret_cast<double*>(PyArray_DATA(features_out_py_arr));

    try {
        gp->enrichFeatureVectors(num_rows, features_in, num_cols_in, features_out, num_cols_out);
    } catch (const std::exception& e) {
        struct module_state_* st = GET_MODULE_STATE(self);
        PyErr_SetString(st->other_error, e.what());
        return PyInt_FromLong(-1);
    }

    return PyInt_FromLong(-1);
}

PyObject* pygraphfeatures_partial_fit(PyObject* self, PyObject* args)
{
    PyObject*      gp_ptr;
    PyArrayObject* features_py_arr;

    string message;
    bool   report_error = false;

    if (!PyArg_ParseTuple(args, "OO", &gp_ptr, &features_py_arr))
        return NULL;

    GraphFeaturePreprocessor* gp = reinterpret_cast<GraphFeaturePreprocessor*>(PyCapsule_GetPointer(gp_ptr, NULL));
    if (gp == nullptr) {
        struct module_state_* st = GET_MODULE_STATE(self);
        PyErr_SetString(st->type_error, "The graph preprocessor is not available.");
        return NULL;
    }

    if (PyArray_NDIM(features_py_arr) != 2) {
        message      = "Input features must be a two-dimensional numpy array.";
        report_error = true;
    } else {
        if (PyArray_TYPE(features_py_arr) != NPY_FLOAT64) {
            message      = "The input features array uses the wrong data type. Expected data type: float64.";
            report_error = true;
        }
    }
    if (report_error) {
        struct module_state_* st = GET_MODULE_STATE(self);
        PyErr_SetString(st->type_error, message.c_str());
        return PyInt_FromLong(-1);
    }

    npy_intp* features_shape = PyArray_DIMS(features_py_arr);
    uint64_t  num_rows       = features_shape[0];
    uint64_t  num_cols       = features_shape[1];

    double* features_in = reinterpret_cast<double*>(PyArray_DATA(features_py_arr));

    try {
        gp->updateGraph(features_in, num_rows, num_cols);
    } catch (const std::exception& e) {
        struct module_state_* st = GET_MODULE_STATE(self);
        PyErr_SetString(st->other_error, e.what());
        return PyInt_FromLong(-1);
    }

    return PyInt_FromLong(-1);
}

void python_cleanup() { }
