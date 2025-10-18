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

/*! @file
 *  @ingroup wrapper
 */

#define NO_IMPORT_ARRAY
#include "Wrapper.h"

#include "Metrics.hpp"
#include "DenseDatasetInt.hpp"
#include <set>

template <uint32_t sel> PyObject* __simple_metric(PyObject* m, PyObject* args)
{
    char*          ptr_str;
    Py_ssize_t     ptr_len;
    npy_int64      type;
    PyArrayObject* proba;
    npy_int64      num_ex;
    PyArrayObject* py_labs;

    if (!PyArg_ParseTuple(args, "lO!s#lO!", &num_ex, &PyArray_Type, &py_labs, &ptr_str, &ptr_len, &type, &PyArray_Type,
                          &proba)) {
        return NULL;
    }

    glm::Dataset* data = NULL;

    if (ptr_len == 0) {

        /* We may not need this code; as we can get the metrics from sklearn ? */

        /*
        CurTime starttime, finish;
        double elapsed;
        starttime = Clock::now();
        */

        if (PyArray_TYPE(py_labs) != NPY_FLOAT32) {
            char                 message[] = "The elements of data have the wrong type. Expected type: float32.";
            struct module_state* st        = GET_MODULE_STATE(m);
            PyErr_SetString(st->type_error, message);
            return NULL;
        }

        // Only one partition for snap-ml-local
        uint32_t num_partitions = 1;
        uint32_t partition_id   = 0;
        uint32_t this_pt_offset = 0;

        using glm::DenseDataset;

        DenseDataset* data_train_d;
        try {
            // data_train_d = std::shared_ptr < DenseDataset > (new DenseDataset( transpose,
            data_train_d = new DenseDataset(false, static_cast<uint32_t>(num_ex), 1, static_cast<uint32_t>(num_ex),
                                            num_partitions, partition_id, this_pt_offset, static_cast<uint64_t>(num_ex),
                                            0, 0, reinterpret_cast<float*>(PyArray_DATA(py_labs)), NULL, false);
            // data = data_train_d.get();
            type = 1;
            data = data_train_d;
        } catch (const std::exception& e) {
            struct module_state* st = GET_MODULE_STATE(m);
            PyErr_SetString(st->other_error, e.what());
            return NULL;
        }

        /*
        finish = Clock::now();
        auto dur = finish - starttime;
        elapsed = (double)dur.count() / 1.0e9;
        printf("Elapsed Time : %f \n", elapsed);
        */

    } else {
        // check if the pointer length is 8
        assert(ptr_len == 8);

        uint64_t* ptr = reinterpret_cast<uint64_t*>(ptr_str);
        data          = reinterpret_cast<glm::Dataset*>(*ptr);
    }

    double*  proba_cpp = reinterpret_cast<double*>(PyArray_DATA(proba));
    uint32_t proba_len = PyArray_SIZE(proba);
    double   out;

    std::set<float> unique_labs;
    float*          labs = data->get_labs();
    for (uint64_t i = 0; i < data->get_num_labs(); i++) {
        unique_labs.insert(labs[i]);
    }

    if (sel == 0) {
        // what about regression with 2 float labels
        if (unique_labs.size() <= 2) {
            out = glm::metrics::jni::logistic_loss(data, proba_cpp, proba_len);
        } else {
            char message[] = "Only accuracy_score and mean_squared_error metrics support in multi-class classification "
                             "or regression mode. User input: log_loss.";
            struct module_state* st = GET_MODULE_STATE(m);
            PyErr_SetString(st->type_error, message);
            return NULL;
        }
    } else if (sel == 1) {
        out = glm::metrics::jni::mean_squared_error(data, proba_cpp, proba_len);
    } else if (sel == 2) {
        out = glm::metrics::jni::accuracy_mpi(data, proba_cpp, proba_len);
    } else if (sel == 3) {
        // what about regression with 2 float labels
        if (unique_labs.size() <= 2) {
            out = glm::metrics::jni::hinge_loss(data, proba_cpp, proba_len);
        } else {
            char message[] = "Only accuracy_score and mean_squared_error metrics support in multi-class classification "
                             "or regression mode. User input: hinge_loss.";
            struct module_state* st = GET_MODULE_STATE(m);
            PyErr_SetString(st->type_error, message);
            return NULL;
        }
    }

    PyObject* output = Py_BuildValue("d", out);

    return output;
}

PyObject* log_loss(PyObject* dummy, PyObject* args) { return __simple_metric<0>(dummy, args); }

PyObject* mean_squared_error(PyObject* dummy, PyObject* args) { return __simple_metric<1>(dummy, args); }

PyObject* accuracy(PyObject* dummy, PyObject* args) { return __simple_metric<2>(dummy, args); }

PyObject* hinge_loss(PyObject* dummy, PyObject* args) { return __simple_metric<3>(dummy, args); }
