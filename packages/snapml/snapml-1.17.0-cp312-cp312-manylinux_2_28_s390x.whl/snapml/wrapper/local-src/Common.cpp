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
 *
 * End Copyright
 ********************************************************************/

/*! @file
 *  @ingroup wrapper
 */

#define NO_IMPORT_ARRAY
#include "Wrapper.h"

#include "DenseDatasetInt.hpp"
#include "DenseDataset.hpp"
#include "SparseDataset.hpp"

// validate data input
wrapperError_t check_numpy_args(PyObject* m, PyArrayObject* py_indptr, PyArrayObject* py_indices,
                                PyArrayObject* py_data, PyArrayObject* py_labs, bool& is_sparse)
{

    is_sparse = PyArray_SIZE(py_indptr) > 0;
    if (is_sparse && PyArray_TYPE(py_indptr) != NPY_UINT64) {
        char                 message[] = "The elements of py_indptr have the wrong type. Expected type: uint64.";
        struct module_state* st        = GET_MODULE_STATE(m);
        PyErr_SetString(st->type_error, message);
        return wrapperError_t::Failure;
    }

    is_sparse = PyArray_SIZE(py_indices) > 0;
    if (is_sparse && PyArray_TYPE(py_indices) != NPY_UINT32) {
        char                 message[] = "The elements of indices have the wrong type. Expected type: uint32.";
        struct module_state* st        = GET_MODULE_STATE(m);
        PyErr_SetString(st->type_error, message);
        return wrapperError_t::Failure;
    }

    if (PyArray_TYPE(py_data) != NPY_FLOAT32) {
        char                 message[] = "The elements of data have the wrong type. Expected type: float32.";
        struct module_state* st        = GET_MODULE_STATE(m);
        PyErr_SetString(st->type_error, message);
        return wrapperError_t::Failure;
    }

    if (py_labs != nullptr && PyArray_TYPE(py_labs) != NPY_FLOAT32) {
        char                 message[] = "The elements of labs (labels) have the wrong type. Expected type: float32.";
        struct module_state* st        = GET_MODULE_STATE(m);
        PyErr_SetString(st->type_error, message);
        return wrapperError_t::Failure;
    }

    return wrapperError_t::Success;
}

// validate fit_sample_weight parameter
wrapperError_t check_numpy_sample_weight(PyObject* m, PyArrayObject* py_sample_weight, uint64_t num_ex)
{
    uint64_t array_size = PyArray_SIZE(py_sample_weight);

    if (array_size > 0 && array_size != num_ex) {
        char message[]
            = "The size of the sample_weight array should be equal to the number of examples in the train set.";
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->type_error, message);
        return wrapperError_t::Failure;
    }

    if (array_size > 0 && PyArray_TYPE(py_sample_weight) != NPY_FLOAT32) {
        char message[] = "The elements of the sample_weight array have the wrong type. Expected type: float32.";
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->type_error, message);
        return wrapperError_t::Failure;
    }

    return wrapperError_t::Success;
}

// count number of positive/negative examples in labels
wrapperError_t count_num_pos_neg(PyObject* m, PyArrayObject* py_labs, uint32_t& num_pos, uint32_t& num_neg)
{

    float**               dataptr;
    PyArray_Descr*        dtype;
    NpyIter*              iter;
    NpyIter_IterNextFunc* iternext;

    dtype = PyArray_DescrFromType(NPY_FLOAT32);
    iter  = NpyIter_New(py_labs, NPY_ITER_READONLY, NPY_KEEPORDER, NPY_NO_CASTING, dtype);
    if (iter == NULL) {
        char                 message[] = "Cannot count number of pos/neg labels.";
        struct module_state* st        = GET_MODULE_STATE(m);
        PyErr_SetString(st->type_error, message);
        return wrapperError_t::Failure;
    }

    iternext = NpyIter_GetIterNext(iter, NULL);
    dataptr  = reinterpret_cast<float**>(NpyIter_GetDataPtrArray(iter));

    do {
        if (**dataptr > 0) {
            num_pos++;
        } else {
            num_neg++;
        }
    } while (iternext(iter));

    NpyIter_Deallocate(iter);

    return wrapperError_t::Success;
}

wrapperError_t make_sparse_dataset(PyObject* m, uint32_t num_ex, uint32_t num_ft, uint64_t num_nz, uint32_t num_pos,
                                   uint32_t num_neg, PyArrayObject* py_indptr, PyArrayObject* py_indices,
                                   PyArrayObject* py_data, PyArrayObject* py_labs,
                                   std::shared_ptr<glm::SparseDataset>& data_out)
{

    try {

        uint32_t this_num_pt    = num_ex;
        uint32_t num_partitions = 1;
        uint32_t partition_id   = 0;
        uint32_t this_pt_offset = 0;

        float*    labs    = (py_labs != nullptr) ? static_cast<float*>(PyArray_DATA(py_labs)) : nullptr;
        uint64_t* indptr  = (py_indptr != nullptr) ? static_cast<uint64_t*>(PyArray_DATA(py_indptr)) : nullptr;
        uint32_t* indices = (py_indices != nullptr) ? static_cast<uint32_t*>(PyArray_DATA(py_indices)) : nullptr;
        float*    data    = (py_data != nullptr) ? static_cast<float*>(PyArray_DATA(py_data)) : nullptr;

        data_out = std::make_shared<glm::SparseDataset>(false, num_ex, num_ft, this_num_pt, num_partitions,
                                                        partition_id, this_pt_offset, num_nz, num_pos, num_neg, labs,
                                                        indptr, indices, data);

    } catch (const std::exception& e) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->other_error, e.what());
        return wrapperError_t::Failure;
    }

    return wrapperError_t::Success;
}

wrapperError_t make_dense_dataset(PyObject* m, uint32_t num_ex, uint32_t num_ft, uint64_t num_nz, uint32_t num_pos,
                                  uint32_t num_neg, PyArrayObject* py_data, PyArrayObject* py_labs,
                                  std::shared_ptr<glm::DenseDataset>& data_out)
{

    try {

        uint32_t this_num_pt    = num_ex;
        uint32_t num_partitions = 1;
        uint32_t partition_id   = 0;
        uint32_t this_pt_offset = 0;

        float* labs = (py_labs != nullptr) ? static_cast<float*>(PyArray_DATA(py_labs)) : nullptr;
        float* data = (py_data != nullptr) ? static_cast<float*>(PyArray_DATA(py_data)) : nullptr;

        data_out = std::make_shared<glm::DenseDataset>(false, num_ex, num_ft, this_num_pt, num_partitions, partition_id,
                                                       this_pt_offset, num_nz, num_pos, num_neg, labs, data, false);

    } catch (const std::exception& e) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->other_error, e.what());
        return wrapperError_t::Failure;
    }

    return wrapperError_t::Success;
}

wrapperError_t make_dense_dataset_api(PyObject* m, uint32_t num_ex, uint32_t num_ft, PyArrayObject* py_data,
                                      PyArrayObject* py_labs, snapml::DenseDataset& data_out)
{

    try {
        float* labs = (py_labs != nullptr) ? static_cast<float*>(PyArray_DATA(py_labs)) : nullptr;
        float* data = (py_data != nullptr) ? static_cast<float*>(PyArray_DATA(py_data)) : nullptr;

        data_out = snapml::DenseDataset(num_ex, num_ft, data, labs);

    } catch (const std::exception& e) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->other_error, e.what());
        return wrapperError_t::Failure;
    }

    return wrapperError_t::Success;
}

// deallocate memory for the model std::vector
void model_delete(PyObject* model_ptr)
{
    std::vector<uint8_t>* vptr = reinterpret_cast<std::vector<uint8_t>*>(PyCapsule_GetPointer(model_ptr, NULL));

    delete vptr;
}

// allocate memory for the model std::vector
PyObject* model_allocate(PyObject* m)
{
    std::vector<uint8_t>* vptr = new std::vector<uint8_t>;

    if (vptr == nullptr) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->other_error, "Unable to allocate memory for the model.");
        return NULL;
    }

    PyObject* model_ptr = PyCapsule_New(vptr, NULL, model_delete);

    return model_ptr;
}

PyObject* model_get(PyObject* m, PyObject* model_ptr)
{
    std::vector<uint8_t>* vptr = reinterpret_cast<std::vector<uint8_t>*>(PyCapsule_GetPointer(model_ptr, NULL));

    npy_intp        dims[] { static_cast<int64_t>(vptr->size()) };
    PyObject* const pymodel = reinterpret_cast<PyObject*>(
        PyArray_SimpleNewFromData(1, dims, NPY_UINT8, reinterpret_cast<void*>(vptr->data())));

    PyObject* output = Py_BuildValue("OK", pymodel, vptr->size());
    Py_DECREF(pymodel);

    return output;
}

PyObject* model_put(PyObject* m, PyObject* args)
{

    PyArrayObject* model;
    npy_int64      model_len;
    PyObject*      model_ptr;

    if (!PyArg_ParseTuple(args, "O!LO", &PyArray_Type, &model, &model_len, &model_ptr)) {
        return NULL;
    }

    const uint64_t ba_size = static_cast<uint64_t>(model_len);
    assert(0 < ba_size);
    uint8_t* const ba = reinterpret_cast<uint8_t*>(PyArray_DATA(model));

    std::vector<uint8_t>* vec = reinterpret_cast<std::vector<uint8_t>*>(PyCapsule_GetPointer(model_ptr, NULL));

    if (vec == nullptr) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->type_error, "No model_ptr available.");
        return NULL;
    }

    vec->assign(&ba[0], &ba[0] + ba_size);

    Py_INCREF(Py_None);
    return Py_None;
}
