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

#include "Loaders.hpp"

std::vector<std::shared_ptr<glm::Dataset>> datasetManager;

PyObject* load_svmlight_file(PyObject* dummy, PyObject* args)
{
    const char* filename;
    npy_int64   expected_num_ft;
    npy_int64   num_chunks = 1;
    if (!PyArg_ParseTuple(args, "sLL", &filename, &expected_num_ft, &num_chunks)) {
        return NULL;
    }

    glm::SvmLightLoader loader(filename, 0, 1, num_chunks, expected_num_ft);

    uint32_t max_ind, this_num_pt, num_pos, num_neg, offsets;

    loader.get_consistency(max_ind, this_num_pt, num_pos, num_neg, &offsets);
    loader.set_consistency(max_ind, this_num_pt, num_pos, num_neg, &offsets);

    using glm::SparseDataset;

    std::shared_ptr<SparseDataset> data = loader.get_data();

    uint32_t              num_ex     = data->get_num_ex();
    int64_t               num_nz     = data->get_num_nz();
    int64_t               start_size = data->get_num_ex() + 1;
    SparseDataset::data_t inner_data = data->get_data();

    float* val_ = new float[num_nz];
    memcpy(val_, inner_data.val, num_nz * sizeof(float));

    uint32_t* ind_ = new uint32_t[num_nz];
    memcpy(ind_, inner_data.ind, num_nz * sizeof(uint32_t));

    uint64_t* start_ = new uint64_t[start_size];
    memcpy(start_, inner_data.start, start_size * sizeof(uint64_t));

    float* labs_ = new float[num_ex];
    memcpy(labs_, inner_data.labs, num_ex * sizeof(float));

    PyObject* val;
    npy_intp  val_dims = num_nz;
    val                = reinterpret_cast<PyObject*>(
        PyArray_SimpleNewFromData(1, &val_dims, NPY_FLOAT32, reinterpret_cast<void*>(val_)));
    // set flag NPY_ARRAY_OWNDATA to free underlying object when Py_DECREF
    PyArray_ENABLEFLAGS(reinterpret_cast<PyArrayObject*>(val), NPY_ARRAY_OWNDATA);

    PyObject* ind;
    npy_intp  ind_dims = num_nz;
    ind                = reinterpret_cast<PyObject*>(
        PyArray_SimpleNewFromData(1, &ind_dims, NPY_UINT32, reinterpret_cast<void*>(ind_)));
    PyArray_ENABLEFLAGS(reinterpret_cast<PyArrayObject*>(ind), NPY_ARRAY_OWNDATA);

    PyObject* start;
    npy_intp  start_dims = start_size;
    start                = reinterpret_cast<PyObject*>(
        PyArray_SimpleNewFromData(1, &start_dims, NPY_UINT64, reinterpret_cast<void*>(start_)));
    PyArray_ENABLEFLAGS(reinterpret_cast<PyArrayObject*>(start), NPY_ARRAY_OWNDATA);

    PyObject* labs;
    npy_intp  lab_dims = num_ex;
    labs               = reinterpret_cast<PyObject*>(
        PyArray_SimpleNewFromData(1, &lab_dims, NPY_FLOAT32, reinterpret_cast<void*>(labs_)));
    PyArray_ENABLEFLAGS(reinterpret_cast<PyArrayObject*>(labs), NPY_ARRAY_OWNDATA);

    PyObject* metadata;
    npy_intp  metadata_dims = 2;
    uint32_t* metadata_     = new uint32_t[2];
    metadata_[0]            = data->get_num_ex();
    metadata_[1]            = data->get_num_ft();
    metadata                = reinterpret_cast<PyObject*>(
        PyArray_SimpleNewFromData(1, &metadata_dims, NPY_UINT32, reinterpret_cast<void*>(metadata_)));
    PyArray_ENABLEFLAGS(reinterpret_cast<PyArrayObject*>(metadata), NPY_ARRAY_OWNDATA);

    PyObject* arrays = PyList_New(5);
    PyList_SetItem(arrays, 0, metadata);
    PyList_SetItem(arrays, 1, val);
    PyList_SetItem(arrays, 2, ind);
    PyList_SetItem(arrays, 3, start);
    PyList_SetItem(arrays, 4, labs);
    PyObject* output = Py_BuildValue("O", arrays);
    Py_DECREF(arrays);

    return output;
}

template <class Loader> Loader* __loader(PyObject* m, PyObject* args)
{
    uint32_t    max_ind, num_pt, num_pos, num_neg, offsets;
    const char* filename;
    npy_int64   num_ft;
    npy_int64   num_chunks = 1;

    if (!PyArg_ParseTuple(args, "sLL", &filename, &num_ft, &num_chunks)) {
        return NULL;
    }

    Loader* loader = new Loader(filename, 0, 1, num_chunks, num_ft);

    try {
        loader->get_consistency(max_ind, num_pt, num_pos, num_neg, &offsets);
    } catch (const std::exception& e) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->other_error, e.what());
        return NULL;
    }

    try {
        loader->set_consistency(max_ind, num_pt, num_pos, num_neg, &offsets);
    } catch (const std::exception& e) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->other_error, e.what());
        return NULL;
    }

    return loader;
}

template <class Loader> PyObject* __loader_snap(PyObject* m, PyObject* args)
{
    Loader* obj  = __loader<Loader>(m, args);
    auto    data = obj->get_data();

    // stop dataset from going out of scope
    datasetManager.push_back(data);

    uint64_t    ptr     = reinterpret_cast<uint64_t>(data.get());
    const char* ptr_str = reinterpret_cast<const char*>(&ptr);

    PyObject* output;

#if PY_MAJOR_VERSION >= 3
    output = Py_BuildValue("y#", ptr_str, sizeof(uint64_t));
#else
    output = Py_BuildValue("s#", ptr_str, sizeof(uint64_t));
#endif

    return output;
}

PyObject* load_from_svmlight_format(PyObject* self, PyObject* args)
{
    return __loader_snap<glm::SvmLightLoader>(self, args);
}

PyObject* load_from_dense_snap_format(PyObject* self, PyObject* args)
{
    return __loader_snap<glm::DenseSnapLoader>(self, args);
}

PyObject* load_from_sparse_snap_format(PyObject* self, PyObject* args)
{
    return __loader_snap<glm::SparseSnapLoader>(self, args);
}

PyObject* load_from_l2sparse_snap_format(PyObject* self, PyObject* args)
{
    return __loader_snap<glm::L2SparseSnapLoader>(self, args);
}
