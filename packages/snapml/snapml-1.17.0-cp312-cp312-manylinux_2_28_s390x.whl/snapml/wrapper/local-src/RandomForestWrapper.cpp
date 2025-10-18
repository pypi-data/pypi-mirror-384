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
 *                Milos Stanisavljevic
 *
 * End Copyright
 ********************************************************************/

/*! @file
 *  @ingroup wrapper
 */

#include <vector>

#define NO_IMPORT_ARRAY
#include "Wrapper.h"

#include "DenseDataset.hpp"
#include "DenseDatasetInt.hpp"
#include "common.hpp"
#include "RandomForestBuilder.hpp"
#include "RandomForestPredictor.hpp"
#include "ModelImport.hpp"
#include "RandomForestModel.hpp"

std::vector<snapml::RandomForestModel> forestManager;

uint64_t remember_forest(snapml::RandomForestModel model)
{
    forestManager.push_back(model);
    return forestManager.size();
}

wrapperError_t __rfc_optimize_trees(PyObject* m, snapml::DenseDataset data, uint64_t& cache_id, PyObject* model_ptr,
                                    char* tree_format, bool& is_nnpa_installed)
{
    try {

        snapml::RandomForestModel model;

        std::vector<uint8_t>* vec = reinterpret_cast<std::vector<uint8_t>*>(PyCapsule_GetPointer(model_ptr, NULL));
        if (vec == nullptr) {
            struct module_state* st = GET_MODULE_STATE(m);
            PyErr_SetString(st->type_error, "No model_ptr available.");
            return wrapperError_t::Failure;
        }

        if (cache_id) {
            model = forestManager[cache_id - 1];
        } else {
            model.put(*vec);
            cache_id = remember_forest(model);
        }

        std::string model_tree_format;
        if (tree_format != NULL)
            model_tree_format.assign(tree_format);
        else
            model_tree_format.assign("auto");

        is_nnpa_installed = false;

        if (model_tree_format.compare(0, 4, "auto") == 0) {
#ifdef Z14_SIMD
            if (model.check_if_nnpa_installed()) {
                is_nnpa_installed = true;
                model.convert_mbit(data);
            } else {
                model.compress(data);
            }
#else
            model.compress(data);
#endif
        } else if (model_tree_format.compare(0, 12, "zdnn_tensors") == 0) {
#ifdef Z14_SIMD
            if (model.check_if_nnpa_installed()) {
                is_nnpa_installed = true;
                model.convert_mbit(data);
            } else {
                throw std::runtime_error("Accelerator chip not available in current Z system.");
            }
#else
            throw std::runtime_error("zDNN library supported only in Z systems");
#endif
        } else {
            model.compress(data);
        }

        model.get(*vec);

    } catch (const std::exception& e) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->other_error, e.what());
        return wrapperError_t::Failure;
    }

    return wrapperError_t::Success;
}

wrapperError_t __rfc_fit(snapml::RandomForestParams params, PyObject* m, snapml::DenseDataset data,
                         float* sample_weight, PyObject** feature_importances_out, bool compress_trees,
                         uint64_t& cache_id, PyObject* model_ptr)
{

    try {
        std::shared_ptr<snapml::RandomForestBuilder> builder
            = std::make_shared<snapml::RandomForestBuilder>(data, &params);

        builder->init();
        builder->build(sample_weight);

        double* const feature_importances = new double[static_cast<glm::DenseDatasetInt*>(&data)->get_num_ft()];
        builder->get_feature_importances(feature_importances, static_cast<glm::DenseDatasetInt*>(&data)->get_num_ft());

        snapml::RandomForestModel model = builder->get_model();

        if (compress_trees) {
            model.compress(data);
            cache_id = remember_forest(model);
        }

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

wrapperError_t __rfc_predict(PyObject* m, snapml::DenseDataset data, double* pred, uint32_t num_threads, bool proba,
                             uint64_t& cache_id, PyObject* model_ptr)
{

    try {

        snapml::RandomForestModel model;

        if (cache_id) {
            model = forestManager[cache_id - 1];
        } else {
            std::vector<uint8_t>* vec = reinterpret_cast<std::vector<uint8_t>*>(PyCapsule_GetPointer(model_ptr, NULL));
            if (vec == nullptr) {
                struct module_state* st = GET_MODULE_STATE(m);
                PyErr_SetString(st->type_error, "No model_ptr available.");
                return wrapperError_t::Failure;
            }
            model.put(*vec);
        }

        snapml::RandomForestPredictor predictor = snapml::RandomForestPredictor(model);

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

wrapperError_t __rfc_cache(PyObject* m, std::vector<uint8_t>* vec, uint64_t& cache_id)
{

    try {

        snapml::RandomForestModel model;
        model.put(*vec);

        // for compressed trees
        if (model.compressed_tree()) {
            cache_id = remember_forest(model);
        }

#ifdef Z14_SIMD
        // for mbit trees
        if (model.mbit_tree()) {
            cache_id = remember_forest(model);
        }
#endif

    } catch (const std::exception& e) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->other_error, e.what());
        return wrapperError_t::Failure;
    }

    return wrapperError_t::Success;
}

PyObject* rfc_fit(PyObject* m, PyObject* args)
{
    const char*    task;
    npy_int64      n_estimators;
    const char*    split_criterion;
    npy_int64      max_depth;
    npy_int64      min_samples_leaf;
    npy_int64      max_features;
    npy_int64      bootstrap;
    npy_int64      n_cpu;
    npy_int64      random_state;
    npy_int64      verbose;
    npy_int64      use_histograms;
    npy_int64      hist_nbins;
    npy_int64      use_gpu;
    PyArrayObject* py_gpu_ids;
    npy_int64      compress_trees;
    npy_int64      num_ex;
    npy_int64      num_ft;
    npy_int64      num_classes;
    PyArrayObject* py_indptr { nullptr };
    PyArrayObject* py_indices { nullptr };
    PyArrayObject* py_data { nullptr };
    PyArrayObject* py_labs { nullptr };
    PyArrayObject* py_sample_weight;
    PyObject*      model_ptr;

    if (!PyArg_ParseTuple(args, "sLsLLLLLLLLLLO!LLLLO!O!O!O!O!O", &task, &n_estimators, &split_criterion, &max_depth,
                          &min_samples_leaf, &max_features, &bootstrap, &n_cpu, &random_state, &verbose,
                          &use_histograms, &hist_nbins, &use_gpu, &PyArray_Type, &py_gpu_ids, &compress_trees, &num_ex,
                          &num_ft, &num_classes, &PyArray_Type, &py_indptr, &PyArray_Type, &py_indices, &PyArray_Type,
                          &py_data, &PyArray_Type, &py_labs, &PyArray_Type, &py_sample_weight, &model_ptr)) {
        return NULL;
    }

    wrapperError_t chk;

    if (PyArray_TYPE(py_gpu_ids) != NPY_UINT32) {
        char                 message[] = "The elements gpu_ids have the wrong type. Expected type: uint32.";
        struct module_state* st        = GET_MODULE_STATE(m);
        PyErr_SetString(st->type_error, message);
        return NULL;
    }

    bool is_sparse {};
    chk = check_numpy_args(m, py_indptr, py_indices, py_data, py_labs, is_sparse);
    if (chk != wrapperError_t::Success)
        return NULL;

    assert(!is_sparse);

    snapml::RandomForestParams params;
    if (!strcmp(task, "classification")) {
        params.task = snapml::task_t::classification;
    }
    if (!strcmp(task, "regression")) {
        params.task = snapml::task_t::regression;
    }
    params.n_trees = n_estimators;
    if (!strcmp(split_criterion, "gini")) {
        params.split_criterion = snapml::split_t::gini;
    }
    if (!strcmp(split_criterion, "mse")) {
        params.split_criterion = snapml::split_t::mse;
    }
    params.max_depth        = max_depth;
    params.min_samples_leaf = min_samples_leaf;
    params.max_features     = max_features;
    params.bootstrap        = bootstrap;
    params.random_state     = random_state;
    params.verbose          = verbose;
    params.use_histograms   = use_histograms;
    params.hist_nbins       = hist_nbins;
    params.num_classes      = num_classes;

    if (!strcmp(task, "regression")) {
        params.num_classes = 2;
    }

    params.n_threads = n_cpu;

    if (use_gpu) {
        uint32_t num_gpus = PyArray_SIZE(py_gpu_ids);
        params.use_gpu    = true;
        params.gpu_ids.resize(num_gpus);
        for (uint32_t i = 0; i < num_gpus; i++) {
            params.gpu_ids[i] = *reinterpret_cast<uint32_t*>(PyArray_GETPTR1(py_gpu_ids, i));
        }
    } else {
        params.use_gpu = false;
    }

    chk = check_numpy_sample_weight(m, py_sample_weight, num_ex);
    if (chk != wrapperError_t::Success)
        return NULL;

    float* sample_weight
        = (PyArray_SIZE(py_sample_weight) > 0) ? static_cast<float*>(PyArray_DATA(py_sample_weight)) : nullptr;

    PyObject* py_feature_importances = nullptr;

    snapml::DenseDataset data;

    chk = make_dense_dataset_api(m, num_ex, num_ft, py_data, py_labs, data);
    if (chk != wrapperError_t::Success)
        return NULL;

    uint64_t cache_id = 0;
    chk = __rfc_fit(params, m, data, sample_weight, &py_feature_importances, compress_trees, cache_id, model_ptr);

    if (chk != wrapperError_t::Success)
        return NULL;

    // build a Python object training_metadata with the following information

    PyArray_ENABLEFLAGS(reinterpret_cast<PyArrayObject*>(py_feature_importances), NPY_ARRAY_OWNDATA);
    PyObject* output = Py_BuildValue("OK", py_feature_importances, cache_id);
    Py_DECREF(py_feature_importances);

    return output;
}

PyObject* rfc_predict(PyObject* m, PyObject* args)
{

    npy_int64      num_ex {};
    npy_int64      num_ft {};
    npy_int64      num_threads {};
    PyArrayObject* py_indptr { nullptr };
    PyArrayObject* py_indices { nullptr };
    PyArrayObject* py_data { nullptr };
    npy_int64      proba {};
    npy_int64      num_classes {};
    uint64_t       cache_id {};
    PyObject*      model_ptr { nullptr };

    if (!PyArg_ParseTuple(args, "LLLO!O!O!LLKO", &num_ex, &num_ft, &num_threads, &PyArray_Type, &py_indptr,
                          &PyArray_Type, &py_indices, &PyArray_Type, &py_data, &proba, &num_classes, &cache_id,
                          &model_ptr)) {
        return NULL;
    }

    wrapperError_t chk;

    bool is_sparse {};
    chk = check_numpy_args(m, py_indptr, py_indices, py_data, nullptr, is_sparse);
    if (chk != wrapperError_t::Success)
        return NULL;

    assert(!is_sparse);

    // store the model predictions
    double* pred;
    if (proba == 1) {
        if (num_classes == 2) {
            pred = new double[num_ex * num_classes]();
        } else {
            pred = new double[num_ex * (num_classes - 1)]();
        }
    } else {
        pred = new double[num_ex]();
    }

    snapml::DenseDataset data;

    chk = make_dense_dataset_api(m, num_ex, num_ft, py_data, nullptr, data);

    if (chk != wrapperError_t::Success) {
        delete[] pred;
        return NULL;
    }

    chk = __rfc_predict(m, data, pred, num_threads, proba, cache_id, model_ptr);
    if (chk != wrapperError_t::Success) {
        delete[] pred;
        return NULL;
    }

    PyArrayObject* np_pred;
    npy_intp       dims[1];

    if (proba == 1) {
        if (num_classes == 2) {
            dims[0] = num_ex * num_classes;
        } else {
            dims[0] = num_ex * (num_classes - 1);
        }
    } else {
        dims[0] = num_ex;
    }

    np_pred = reinterpret_cast<PyArrayObject*>(
        PyArray_SimpleNewFromData(1, dims, NPY_DOUBLE, reinterpret_cast<void*>(pred)));
    PyArray_ENABLEFLAGS(np_pred, NPY_ARRAY_OWNDATA);

    PyObject* output = Py_BuildValue("OK", np_pred, cache_id);
    Py_DECREF(np_pred);

    return output;
}

wrapperError_t __rfc_import(PyObject* m, const std::string filename, const std::string file_type, snapml::task_t task,
                            PyObject** classes_out, uint32_t* num_classes_out, PyObject* model_ptr)
{

    try {
        snapml::RandomForestModel model;
        uint32_t                  num_classes;
        PyObject*                 pyclasses = nullptr;

        model.import_model(filename, file_type, task);
        num_classes = model.get_num_classes();

        if (task == snapml::task_t::classification) {
            if (!model.get_class_labels_valid()) {
                throw std::runtime_error("Could not extract class labels from model file.");
            }
            std::vector<float> class_labels = model.get_class_labels();
            float* const       labs         = new float[num_classes];
            for (uint32_t i = 0; i < num_classes; i++) {
                labs[i] = class_labels[i];
            }
            int64_t  num_classes_int64 = static_cast<int64_t>(num_classes);
            npy_intp labs_dims[] { num_classes_int64 };

            pyclasses = reinterpret_cast<PyObject*>(
                PyArray_SimpleNewFromData(1, labs_dims, NPY_FLOAT32, reinterpret_cast<void*>(labs)));

        } else {
            pyclasses = Py_None;
        }

        // serialize the model
        std::vector<uint8_t>* vec = reinterpret_cast<std::vector<uint8_t>*>(PyCapsule_GetPointer(model_ptr, NULL));
        // inside the API proxy class a vector should be passed
        model.get(*vec);

        // prepare output
        *classes_out     = pyclasses;
        *num_classes_out = num_classes;

    } catch (const std::exception& e) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->other_error, e.what());
        return wrapperError_t::Failure;
    }

    return wrapperError_t::Success;
}

wrapperError_t __rfc_export(PyObject* m, const std::string filename, const std::string file_type, uint64_t& cache_id,
                            const std::vector<double>& classes, const std::string version, PyObject* model_ptr)
{
    snapml::RandomForestModel model;

    try {
        if (cache_id) {
            model = forestManager[cache_id - 1];
        } else {
            std::vector<uint8_t>* vec = reinterpret_cast<std::vector<uint8_t>*>(PyCapsule_GetPointer(model_ptr, NULL));
            if (vec == nullptr) {
                struct module_state* st = GET_MODULE_STATE(m);
                PyErr_SetString(st->type_error, "No model_ptr available.");
                return wrapperError_t::Failure;
            }
            model.put(*vec);
        }

        model.export_model(filename, file_type, classes, version);

    } catch (const std::exception& e) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->other_error, e.what());
        return wrapperError_t::Failure;
    }

    return wrapperError_t::Success;
}

PyObject* rfc_optimize_trees(PyObject* m, PyObject* args)
{

    npy_int64      num_ex;
    npy_int64      num_ft;
    PyArrayObject* py_data;
    uint64_t       cache_id;
    PyObject*      model_ptr;
    char*          tree_format;

    if (!PyArg_ParseTuple(args, "LLO!KOz", &num_ex, &num_ft, &PyArray_Type, &py_data, &cache_id, &model_ptr,
                          &tree_format)) {
        return NULL;
    }

    wrapperError_t chk;

    if (PyArray_TYPE(py_data) != NPY_FLOAT32) {
        char                 message[] = "The elements of data have the wrong type. Expected type: float32.";
        struct module_state* st        = GET_MODULE_STATE(m);
        PyErr_SetString(st->type_error, message);
        return NULL;
    }

    snapml::DenseDataset data;

    if (PyArray_SIZE(py_data) > 0) {
        chk = make_dense_dataset_api(m, num_ex, num_ft, py_data, nullptr, data);
    } else {
        chk = make_dense_dataset_api(m, num_ex, num_ft, nullptr, nullptr, data);
    }

    if (chk != wrapperError_t::Success) {
        return NULL;
    }

    bool is_nnpa_installed;
    chk = __rfc_optimize_trees(m, data, cache_id, model_ptr, tree_format, is_nnpa_installed);

    if (chk != wrapperError_t::Success) {
        return NULL;
    }

    std::string optimized_tree_format = (is_nnpa_installed) ? "zdnn_tensors" : "compress_trees";

    // build a Python object training_metadata with the following information
    PyObject* output = Py_BuildValue("Ks", cache_id, optimized_tree_format.c_str());

    return output;
}

PyObject* rfc_import(PyObject* m, PyObject* args)
{

    char*     ext_model_import_filename;
    char*     ext_model_import_file_type;
    PyObject* model_ptr;

    const char* task_str;
    if (!PyArg_ParseTuple(args, "zzsO", &ext_model_import_filename, &ext_model_import_file_type, &task_str,
                          &model_ptr)) {
        return NULL;
    }

    std::string model_filename;
    if (ext_model_import_filename != NULL)
        model_filename.assign(ext_model_import_filename);

    std::string model_file_type;
    if (ext_model_import_file_type != NULL)
        model_file_type.assign(ext_model_import_file_type);

    PyObject* pyclasses   = nullptr;
    uint32_t  num_classes = 0;

    wrapperError_t chk;

    snapml::task_t task
        = !strcmp(task_str, "classification") ? snapml::task_t::classification : snapml::task_t::regression;

    chk = __rfc_import(m, model_filename, model_file_type, task, &pyclasses, &num_classes, model_ptr);

    if (chk != wrapperError_t::Success) {
        return NULL;
    }

    // build a Python object import_metadata with the following information
    if (pyclasses != Py_None) {
        PyArray_ENABLEFLAGS(reinterpret_cast<PyArrayObject*>(pyclasses), NPY_ARRAY_OWNDATA);
    }
    PyObject* output = Py_BuildValue("OI", pyclasses, num_classes);
    if (pyclasses != Py_None) {
        Py_DECREF(pyclasses);
    }

    return output;
}

PyObject* rfc_export(PyObject* m, PyObject* args)
{

    char*          ext_model_export_filename;
    char*          ext_model_export_file_type;
    uint64_t       cache_id;
    PyArrayObject* py_classes;
    char*          ext_version;
    PyObject*      model_ptr;

    if (!PyArg_ParseTuple(args, "zzKO!zO", &ext_model_export_filename, &ext_model_export_file_type, &cache_id,
                          &PyArray_Type, &py_classes, &ext_version, &model_ptr)) {
        return NULL;
    }

    std::string model_filename;
    if (ext_model_export_filename != NULL)
        model_filename.assign(ext_model_export_filename);

    std::string model_file_type;
    if (ext_model_export_file_type != NULL)
        model_file_type.assign(ext_model_export_file_type);

    std::string version;
    if (ext_version != NULL)
        version.assign(ext_version);

    wrapperError_t chk;

    std::vector<double> classes;
    for (uint32_t i = 0; i < PyArray_DIM(py_classes, 0); i++) {
        double* ptr = reinterpret_cast<double*>(PyArray_GETPTR1(py_classes, i));
        classes.push_back(*ptr);
    }

    chk = __rfc_export(m, ext_model_export_filename, ext_model_export_file_type, cache_id, classes, version, model_ptr);

    if (chk != wrapperError_t::Success) {
        return NULL;
    }

    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* rfc_cache(PyObject* m, PyObject* args)
{
    PyObject* model_ptr;

    if (!PyArg_ParseTuple(args, "O", &model_ptr)) {
        return NULL;
    }

    wrapperError_t chk;

    std::vector<uint8_t>* vec = reinterpret_cast<std::vector<uint8_t>*>(PyCapsule_GetPointer(model_ptr, NULL));

    if (vec == nullptr) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->type_error, "No model_ptr available.");
        return NULL;
    }
    uint64_t cache_id = 0;
    chk               = __rfc_cache(m, vec, cache_id);

    if (chk != wrapperError_t::Success) {
        return NULL;
    }

    PyObject* output = Py_BuildValue("K", cache_id);

    return output;
}

PyObject* rfc_delete(PyObject* m, PyObject* args)
{

    uint64_t cache_id;

    if (!PyArg_ParseTuple(args, "K", &cache_id)) {
        return NULL;
    }

    try {

        if (cache_id == 0) {
            throw std::runtime_error("Trying to remove a model from the cache that has not been cached.");
        } else {
            // forestManager[cache_id - 1].reset();
            forestManager[cache_id - 1] = snapml::RandomForestModel();
        }

    } catch (const std::exception& e) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->other_error, e.what());
        return NULL;
    }

    Py_RETURN_NONE;
}
