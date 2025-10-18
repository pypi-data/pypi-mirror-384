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
 *                Jan van Lunteren
 *                Milos Stanisavljevic
 *
 * End Copyright
 ********************************************************************/

/*! @file
 *  @ingroup wrapper
 */

#define NO_IMPORT_ARRAY
#include "Wrapper.h"

#include "DenseDataset.hpp"
#include "DenseDatasetInt.hpp"
#include "BoosterBuilder.hpp"
#include "BoosterPredictor.hpp"
#include "BoosterModel.hpp"

std::vector<snapml::BoosterModel> boosterManager;

uint64_t remember_booster(snapml::BoosterModel model)
{
    boosterManager.push_back(model);
    return boosterManager.size();
}

wrapperError_t __booster_fit(PyObject* m, snapml::DenseDataset train_data, snapml::DenseDataset val_data,
                             const snapml::BoosterParams& params, PyObject** feature_importances_out,
                             uint32_t& best_num_rounds, float* sample_weight, float* sample_weight_val,
                             bool compress_trees, uint64_t& cache_id, PyObject* model_ptr)
{

    try {

        std::shared_ptr<snapml::BoosterBuilder> builder
            = std::make_shared<snapml::BoosterBuilder>(train_data, val_data, params);

        builder->init();
        builder->build(sample_weight, sample_weight_val);

        uint32_t feature_importances_size = params.aggregate_importances
                                                ? static_cast<glm::DenseDatasetInt*>(&train_data)->get_num_ft()
                                                : builder->get_full_feature_importances_size();
        double* const feature_importances = new double[feature_importances_size];

        if (params.aggregate_importances) {
            builder->get_feature_importances(feature_importances, feature_importances_size);
        } else {
            builder->get_full_feature_importances(feature_importances, feature_importances_size);
        }

        snapml::BoosterModel model = builder->get_model();

        if (compress_trees) {
            model.compress(train_data);
            cache_id = remember_booster(model);
        }

        std::vector<uint8_t>* vec = reinterpret_cast<std::vector<uint8_t>*>(PyCapsule_GetPointer(model_ptr, NULL));
        if (vec == nullptr) {
            struct module_state* st = GET_MODULE_STATE(m);
            PyErr_SetString(st->type_error, "No model_ptr available.");
            return wrapperError_t::Failure;
        }
        model.get(*vec);

        if (params.aggregate_importances) {
            npy_intp ft_dims[] { static_cast<int64_t>(static_cast<glm::DenseDatasetInt*>(&train_data)->get_num_ft()) };
            PyObject* const py_feature_importances = reinterpret_cast<PyObject*>(
                PyArray_SimpleNewFromData(1, ft_dims, NPY_DOUBLE, reinterpret_cast<void*>(feature_importances)));
            *feature_importances_out = py_feature_importances;
        } else {
            uint32_t num_sets
                = feature_importances_size / static_cast<glm::DenseDatasetInt*>(&train_data)->get_num_ft();
            npy_intp        ft_dims[] { static_cast<int64_t>(num_sets),
                                 static_cast<int64_t>(static_cast<glm::DenseDatasetInt*>(&train_data)->get_num_ft()) };
            PyObject* const py_feature_importances = reinterpret_cast<PyObject*>(
                PyArray_SimpleNewFromData(2, ft_dims, NPY_DOUBLE, reinterpret_cast<void*>(feature_importances)));
            *feature_importances_out = py_feature_importances;
        }
        // output number of completed boosting rounds
        best_num_rounds = model.get_n_regressors();

    } catch (const std::exception& e) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->other_error, e.what());
        return wrapperError_t::Failure;
    }

    return wrapperError_t::Success;
}

wrapperError_t __booster_predict(PyObject* m, snapml::DenseDataset data, double* pred, bool proba, uint32_t num_threads,
                                 uint64_t& cache_id, PyObject* model_ptr)
{

    try {

        snapml::BoosterModel model;

        if (cache_id) {
            model = boosterManager[cache_id - 1];
        } else {
            std::vector<uint8_t>* vec = reinterpret_cast<std::vector<uint8_t>*>(PyCapsule_GetPointer(model_ptr, NULL));
            if (vec == nullptr) {
                struct module_state* st = GET_MODULE_STATE(m);
                PyErr_SetString(st->type_error, "No model_ptr available.");
                return wrapperError_t::Failure;
            }
            model.put(*vec);
        }

        snapml::BoosterPredictor predictor(model);

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

wrapperError_t __booster_cache(PyObject* m, std::vector<uint8_t>* vec, uint64_t& cache_id)
{

    try {

        snapml::BoosterModel model;
        model.put(*vec);

        // for compressed trees
        if (model.compressed_tree()) {
            cache_id = remember_booster(model);
        }

#ifdef Z14_SIMD
        // for mbit trees
        if (model.mbit_tree()) {
            cache_id = remember_booster(model);
        }
#endif

    } catch (const std::exception& e) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->other_error, e.what());
        return wrapperError_t::Failure;
    }

    return wrapperError_t::Success;
}

wrapperError_t __booster_import(PyObject* m, const std::string filename, const std::string file_type,
                                PyObject** classes_out, uint32_t* num_classes_out, PyObject* model_ptr)
{

    try {
        snapml::BoosterModel model;
        uint32_t             num_classes;
        PyObject*            pyclasses = nullptr;

        model.import_model(filename, file_type);
        num_classes = model.get_num_classes();

        if (model.get_task_type() == snapml::task_t::classification) {
            if (!model.get_class_labels_valid()) {
                throw std::runtime_error("Could not extract class labels from model file.");
            }
            std::vector<float> class_labels = model.get_class_labels();
            float* const       labs         = new float[num_classes];
            for (uint32_t i = 0; i < num_classes; i++) {
                labs[i] = class_labels[i];
            }
            int64_t  num_classes_int64t = static_cast<int64_t>(num_classes);
            npy_intp labs_dims[] { num_classes_int64t };

            pyclasses = reinterpret_cast<PyObject*>(
                PyArray_SimpleNewFromData(1, labs_dims, NPY_FLOAT32, reinterpret_cast<void*>(labs)));

        } else {
            pyclasses = Py_None;
        }

        // serialize the model
        std::vector<uint8_t>* vec = reinterpret_cast<std::vector<uint8_t>*>(PyCapsule_GetPointer(model_ptr, NULL));
        // inside the API proxy class a vector should be passed
        model.get(*vec);

        *classes_out     = pyclasses;
        *num_classes_out = num_classes;

    } catch (const std::exception& e) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->other_error, e.what());
        return wrapperError_t::Failure;
    }

    return wrapperError_t::Success;
}

wrapperError_t __booster_export(PyObject* m, const std::string filename, const std::string file_type,
                                uint64_t& cache_id, const std::vector<double>& classes, const std::string version,
                                PyObject* model_ptr)
{
    snapml::BoosterModel model;

    try {
        if (cache_id) {
            model = boosterManager[cache_id - 1];
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

wrapperError_t __booster_optimize_trees(PyObject* m, snapml::DenseDataset data, uint64_t& cache_id, PyObject* model_ptr,
                                        char* tree_format, bool& is_nnpa_installed)
{
    try {

        snapml::BoosterModel model;

        std::vector<uint8_t>* vec = reinterpret_cast<std::vector<uint8_t>*>(PyCapsule_GetPointer(model_ptr, NULL));
        if (vec == nullptr) {
            struct module_state* st = GET_MODULE_STATE(m);
            PyErr_SetString(st->type_error, "No model_ptr available.");
            return wrapperError_t::Failure;
        }

        if (cache_id) {
            model = boosterManager[cache_id - 1];
        } else {
            model.put(*vec);
            cache_id = remember_booster(model);
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

PyObject* booster_fit(PyObject* m, PyObject* args)
{
    PyObject* py_boosting_params = nullptr;
    PyObject* py_tree_params     = nullptr;
    PyObject* py_ridge_params    = nullptr;
    PyObject* py_kernel_params   = nullptr;

    npy_int64      train_num_ex {};
    npy_int64      train_num_ft {};
    PyArrayObject* py_train_indptr  = nullptr;
    PyArrayObject* py_train_indices = nullptr;
    PyArrayObject* py_train_data    = nullptr;
    PyArrayObject* py_train_labs    = nullptr;

    npy_int64      val_num_ex {};
    npy_int64      val_num_ft {};
    PyArrayObject* py_val_indptr  = nullptr;
    PyArrayObject* py_val_indices = nullptr;
    PyArrayObject* py_val_data    = nullptr;
    PyArrayObject* py_val_labs    = nullptr;

    PyArrayObject* py_sample_weight     = nullptr;
    PyArrayObject* py_sample_weight_val = nullptr;

    npy_int64 py_num_classes {};

    PyArrayObject* py_gpu_ids = nullptr;
    npy_int64      py_aggregate_importances {};

    PyObject* model_ptr = nullptr;

    if (!PyArg_ParseTuple(args, "O!O!O!O!LLO!O!O!O!LLO!O!O!O!O!O!LO!LO", &PyDict_Type, &py_boosting_params,
                          &PyDict_Type, &py_tree_params, &PyDict_Type, &py_ridge_params, &PyDict_Type,
                          &py_kernel_params, &train_num_ex, &train_num_ft, &PyArray_Type, &py_train_indptr,
                          &PyArray_Type, &py_train_indices, &PyArray_Type, &py_train_data, &PyArray_Type,
                          &py_train_labs, &val_num_ex, &val_num_ft, &PyArray_Type, &py_val_indptr, &PyArray_Type,
                          &py_val_indices, &PyArray_Type, &py_val_data, &PyArray_Type, &py_val_labs, &PyArray_Type,
                          &py_sample_weight, &PyArray_Type, &py_sample_weight_val, &py_num_classes, &PyArray_Type,
                          &py_gpu_ids, &py_aggregate_importances, &model_ptr)) {
        return NULL;
    }

    // was a validation set provided?
    bool with_val = val_num_ex > 0;

    // Tree-specific parameters
    snapml::BoosterParams params {};

    params.num_classes = py_num_classes;

    params.n_threads    = PyLong_AsUnsignedLong(PyDict_GetItemString(py_boosting_params, "num_threads"));
    params.n_regressors = PyLong_AsLong(PyDict_GetItemString(py_boosting_params, "num_round"));
    if (!strcmp(PyBytes_AsString(PyUnicode_AsUTF8String(PyDict_GetItemString(py_boosting_params, "objective"))),
                "logloss")) {
        params.objective = snapml::BoosterParams::objective_t::logloss;
    }

    if (!strcmp(PyBytes_AsString(PyUnicode_AsUTF8String(PyDict_GetItemString(py_boosting_params, "objective"))),
                "mse")) {
        params.objective = snapml::BoosterParams::objective_t::mse;
    }

    if (!strcmp(PyBytes_AsString(PyUnicode_AsUTF8String(PyDict_GetItemString(py_boosting_params, "objective"))),
                "cross_entropy")) {
        params.objective = snapml::BoosterParams::objective_t::cross_entropy;
    }

    if (!strcmp(PyBytes_AsString(PyUnicode_AsUTF8String(PyDict_GetItemString(py_boosting_params, "objective"))),
                "softmax")) {
        params.objective = snapml::BoosterParams::objective_t::softmax;
    }

    if (!strcmp(PyBytes_AsString(PyUnicode_AsUTF8String(PyDict_GetItemString(py_boosting_params, "objective"))),
                "poisson")) {
        params.objective = snapml::BoosterParams::objective_t::poisson;
    }
    if (!strcmp(PyBytes_AsString(PyUnicode_AsUTF8String(PyDict_GetItemString(py_boosting_params, "objective"))),
                "quantile")) {
        params.objective = snapml::BoosterParams::objective_t::quantile;
    }

    params.min_max_depth = PyLong_AsUnsignedLong(PyDict_GetItemString(py_boosting_params, "min_max_depth"));
    params.max_max_depth = PyLong_AsUnsignedLong(PyDict_GetItemString(py_boosting_params, "max_max_depth"));
    params.early_stopping_rounds
        = PyLong_AsUnsignedLong(PyDict_GetItemString(py_boosting_params, "early_stopping_rounds"));
    params.random_state    = PyLong_AsUnsignedLong(PyDict_GetItemString(py_boosting_params, "random_state"));
    params.base_prediction = PyFloat_AsDouble(PyDict_GetItemString(py_boosting_params, "base_score"));
    params.learning_rate   = PyFloat_AsDouble(PyDict_GetItemString(py_boosting_params, "learning_rate"));
    params.verbose         = PyDict_GetItemString(py_boosting_params, "verbose") == Py_True;
    params.enable_profile  = PyDict_GetItemString(py_boosting_params, "enable_profile") == Py_True;

    bool compress_trees = PyDict_GetItemString(py_boosting_params, "compress_trees") == Py_True;

    params.use_histograms = PyDict_GetItemString(py_tree_params, "use_histograms") == Py_True;
    params.hist_nbins     = PyLong_AsUnsignedLong(PyDict_GetItemString(py_tree_params, "hist_nbins"));

    params.colsample_bytree   = PyFloat_AsDouble(PyDict_GetItemString(py_tree_params, "colsample_bytree"));
    params.subsample          = PyFloat_AsDouble(PyDict_GetItemString(py_tree_params, "subsample"));
    params.select_probability = PyFloat_AsDouble(PyDict_GetItemString(py_tree_params, "select_probability"));
    params.lambda             = PyFloat_AsDouble(PyDict_GetItemString(py_tree_params, "lambda_l2"));
    params.max_delta_step     = PyFloat_AsDouble(PyDict_GetItemString(py_tree_params, "max_delta_step"));
    params.alpha              = PyFloat_AsDouble(PyDict_GetItemString(py_tree_params, "alpha"));
    params.min_h_quantile     = PyFloat_AsDouble(PyDict_GetItemString(py_tree_params, "min_h_quantile"));

    // Ridge-specific parameters
    params.regularizer   = PyFloat_AsDouble(PyDict_GetItemString(py_ridge_params, "regularizer"));
    params.fit_intercept = PyDict_GetItemString(py_ridge_params, "fit_intercept") == Py_True;

    // Kernel-specific parameters
    params.gamma        = PyFloat_AsDouble(PyDict_GetItemString(py_kernel_params, "gamma"));
    params.n_components = PyLong_AsUnsignedLong(PyDict_GetItemString(py_kernel_params, "n_components"));

    // std::cout << "[BoosterWrapper] gamma " << kernel_params.gamma  << std::endl;

    params.aggregate_importances = py_aggregate_importances;

    wrapperError_t chk {};

    params.use_gpu = PyDict_GetItemString(py_tree_params, "use_gpu") == Py_True;

    if (params.use_gpu) {

        if (PyArray_TYPE(py_gpu_ids) != NPY_UINT32) {
            char                 message[] = "The elements gpu_ids have the wrong type. Expected type: uint32.";
            struct module_state* st        = GET_MODULE_STATE(m);
            PyErr_SetString(st->type_error, message);
            return NULL;
        }

        uint32_t num_gpus = PyArray_SIZE(py_gpu_ids);
        if (num_gpus == 0) {
            params.gpu_ids = { 0 };
        } else {
            params.gpu_ids.resize(num_gpus);
            for (uint32_t i = 0; i < num_gpus; i++) {
                params.gpu_ids[i] = *reinterpret_cast<uint32_t*>(PyArray_GETPTR1(py_gpu_ids, i));
            }
        }
    }

    chk = check_numpy_sample_weight(m, py_sample_weight, train_num_ex);
    if (chk != wrapperError_t::Success)
        return NULL;

    // TODO: it will not work if X_val is provided and sample_weight_val not
    chk = check_numpy_sample_weight(m, py_sample_weight_val, val_num_ex);
    if (chk != wrapperError_t::Success)
        return NULL;

    float* sample_weight
        = (PyArray_SIZE(py_sample_weight) > 0) ? static_cast<float*>(PyArray_DATA(py_sample_weight)) : nullptr;
    float* sample_weight_val
        = (PyArray_SIZE(py_sample_weight_val) > 0) ? static_cast<float*>(PyArray_DATA(py_sample_weight_val)) : nullptr;

    bool train_is_sparse {};
    chk = check_numpy_args(m, py_train_indptr, py_train_indices, py_train_data, py_train_labs, train_is_sparse);
    if (chk != wrapperError_t::Success)
        return NULL;

    if (with_val) {
        bool val_is_sparse {};
        chk = check_numpy_args(m, py_val_indptr, py_val_indices, py_val_data, py_val_labs, val_is_sparse);
        if (chk != wrapperError_t::Success)
            return NULL;

        if (train_is_sparse != val_is_sparse) {
            return NULL;
        }
    }

    bool is_sparse = train_is_sparse;

    assert(!is_sparse);

    PyObject* py_feature_importances = nullptr;
    uint32_t  best_num_rounds        = 0;

    // make train dataset
    snapml::DenseDataset train_data;
    chk = make_dense_dataset_api(m, train_num_ex, train_num_ft, py_train_data, py_train_labs, train_data);
    if (chk != wrapperError_t::Success)
        return NULL;

    // make val dataset
    snapml::DenseDataset val_data;
    if (with_val) {
        chk = make_dense_dataset_api(m, val_num_ex, val_num_ft, py_val_data, py_val_labs, val_data);
        if (chk != wrapperError_t::Success)
            return NULL;
    }

    uint64_t cache_id = 0;
    chk = __booster_fit(m, train_data, val_data, params, &py_feature_importances, best_num_rounds, sample_weight,
                        sample_weight_val, compress_trees, cache_id, model_ptr);

    if (chk != wrapperError_t::Success)
        return NULL;

    PyArray_ENABLEFLAGS(reinterpret_cast<PyArrayObject*>(py_feature_importances), NPY_ARRAY_OWNDATA);
    PyObject* output = Py_BuildValue("OKK", py_feature_importances, best_num_rounds, cache_id);

    Py_DECREF(py_feature_importances);

    // std::cout << "Ending boosting_fit " << std::endl;

    return output;
}

PyObject* booster_predict(PyObject* m, PyObject* args)
{

    npy_int64      num_ex {};
    npy_int64      num_ft {};
    npy_int64      num_threads {};
    PyArrayObject* py_indptr  = nullptr;
    PyArrayObject* py_indices = nullptr;
    PyArrayObject* py_data    = nullptr;
    npy_int64      proba {};
    npy_int64      num_classes {};
    uint64_t       cache_id {};
    PyObject*      model_ptr = nullptr;

    if (!PyArg_ParseTuple(args, "LLLO!O!O!LLKO", &num_ex, &num_ft, &num_threads, &PyArray_Type, &py_indptr,
                          &PyArray_Type, &py_indices, &PyArray_Type, &py_data, &proba, &num_classes, &cache_id,
                          &model_ptr)) {
        return NULL;
    }

    wrapperError_t chk {};

    bool is_sparse {};
    chk = check_numpy_args(m, py_indptr, py_indices, py_data, nullptr, is_sparse);
    if (chk != wrapperError_t::Success)
        return NULL;

    assert(!is_sparse);

    // store the model predictions
    double* pred;
    if (proba == 1)
        pred = new double[num_ex * num_classes]();
    else {
        pred = new double[num_ex]();
    }

    snapml::DenseDataset data;

    chk = make_dense_dataset_api(m, num_ex, num_ft, py_data, nullptr, data);
    if (chk != wrapperError_t::Success) {
        delete[] pred;
        return NULL;
    }

    chk = __booster_predict(m, data, pred, proba, num_threads, cache_id, model_ptr);

    if (chk != wrapperError_t::Success) {
        delete[] pred;
        return NULL;
    }

    PyArrayObject* np_pred;
    npy_intp       dims[1];

    if (proba == 1)
        dims[0] = num_ex * num_classes;
    else
        dims[0] = num_ex;

    np_pred = reinterpret_cast<PyArrayObject*>(
        PyArray_SimpleNewFromData(1, dims, NPY_DOUBLE, reinterpret_cast<void*>(pred)));
    PyArray_ENABLEFLAGS(np_pred, NPY_ARRAY_OWNDATA);

    PyObject* output = Py_BuildValue("OK", np_pred, cache_id);
    Py_DECREF(np_pred);

    return output;
}

PyObject* booster_cache(PyObject* m, PyObject* args)
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
    chk               = __booster_cache(m, vec, cache_id);

    if (chk != wrapperError_t::Success) {
        return NULL;
    }

    PyObject* output = Py_BuildValue("K", cache_id);

    return output;
}

PyObject* booster_delete(PyObject* m, PyObject* args)
{

    uint64_t cache_id;

    if (!PyArg_ParseTuple(args, "K", &cache_id)) {
        return NULL;
    }

    try {

        if (cache_id == 0) {
            throw std::runtime_error("Trying to remove a model from the cache that has not been cached.");
        } else {
            boosterManager[cache_id - 1] = snapml::BoosterModel();
        }

    } catch (const std::exception& e) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->other_error, e.what());
        return NULL;
    }

    Py_RETURN_NONE;
}

PyObject* booster_import(PyObject* m, PyObject* args)
{

    char*     ext_model_import_filename;
    char*     ext_model_import_file_type;
    PyObject* model_ptr;

    if (!PyArg_ParseTuple(args, "zzO", &ext_model_import_filename, &ext_model_import_file_type, &model_ptr)) {
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

    chk = __booster_import(m, model_filename, model_file_type, &pyclasses, &num_classes, model_ptr);

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

PyObject* booster_export(PyObject* m, PyObject* args)
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

    chk = __booster_export(m, ext_model_export_filename, ext_model_export_file_type, cache_id, classes, version,
                           model_ptr);

    if (chk != wrapperError_t::Success) {
        return NULL;
    }

    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* booster_optimize_trees(PyObject* m, PyObject* args)
{

    npy_int64      num_ex {};
    npy_int64      num_ft {};
    PyArrayObject* py_data = nullptr;
    uint64_t       cache_id {};
    PyObject*      model_ptr   = nullptr;
    char*          tree_format = nullptr;

    if (!PyArg_ParseTuple(args, "LLO!KOz", &num_ex, &num_ft, &PyArray_Type, &py_data, &cache_id, &model_ptr,
                          &tree_format)) {
        return NULL;
    }

    wrapperError_t chk {};

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

    bool is_nnpa_installed {};
    chk = __booster_optimize_trees(m, data, cache_id, model_ptr, tree_format, is_nnpa_installed);

    if (chk != wrapperError_t::Success) {
        return NULL;
    }

    std::string optimized_tree_format = (is_nnpa_installed) ? "zdnn_tensors" : "compress_trees";

    // build a Python object training_metadata with the following information
    PyObject* output = Py_BuildValue("Ks", cache_id, optimized_tree_format.c_str());

    return output;
}

PyObject* booster_apply(PyObject* m, PyObject* args)
{

    npy_int64      num_ex;
    npy_int64      num_ft;
    PyArrayObject* py_data;
    npy_int64      num_threads;
    PyObject*      model_ptr;

    if (!PyArg_ParseTuple(args, "LLO!LO", &num_ex, &num_ft, &PyArray_Type, &py_data, &num_threads, &model_ptr)) {
        return NULL;
    }

    if (PyArray_TYPE(py_data) != NPY_FLOAT32) {
        char                 message[] = "The elements of data have the wrong type. Expected type: float32.";
        struct module_state* st        = GET_MODULE_STATE(m);
        PyErr_SetString(st->type_error, message);
        return NULL;
    }

    snapml::DenseDataset data;

    wrapperError_t chk = make_dense_dataset_api(m, num_ex, num_ft, py_data, nullptr, data);

    if (chk != wrapperError_t::Success) {
        return NULL;
    }

    uint32_t  num_classes;
    uint32_t  num_trees;
    size_t    ind_len;
    uint32_t* leaf_idx = nullptr;
    float*    leaf_lab = nullptr;

    try {

        snapml::BoosterModel  model;
        std::vector<uint8_t>* vec = reinterpret_cast<std::vector<uint8_t>*>(PyCapsule_GetPointer(model_ptr, NULL));
        if (vec == nullptr) {
            throw std::runtime_error("No model_ptr available.");
        }
        model.put(*vec);

        if (model.compressed_tree()) {
            throw std::runtime_error("Apply is only supported for uncompressed ensembles.");
        }

        num_classes = model.get_num_classes();
        num_trees   = model.get_num_trees();

        if (num_classes > 2) {
            ind_len = num_ex * num_trees * num_classes;
        } else {
            ind_len = num_ex * num_trees;
        }

        leaf_idx = new uint32_t[ind_len];
        leaf_lab = new float[ind_len];

        snapml::BoosterPredictor predictor = snapml::BoosterPredictor(model);

        predictor.apply(data, leaf_idx, leaf_lab, num_threads);

    } catch (const std::exception& e) {
        if (leaf_idx != nullptr) {
            delete[] leaf_idx;
        }
        if (leaf_lab != nullptr) {
            delete[] leaf_lab;
        }
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->other_error, e.what());
        return NULL;
    }

    npy_intp dims[3];

    dims[0] = num_ex;
    dims[1] = num_trees;
    dims[2] = num_classes;

    uint32_t dim_use = (num_classes > 2) ? 3 : 2;

    PyArrayObject* np_idx = reinterpret_cast<PyArrayObject*>(
        PyArray_SimpleNewFromData(dim_use, dims, NPY_UINT32, reinterpret_cast<void*>(leaf_idx)));
    PyArray_ENABLEFLAGS(np_idx, NPY_ARRAY_OWNDATA);

    PyArrayObject* np_lab = reinterpret_cast<PyArrayObject*>(
        PyArray_SimpleNewFromData(dim_use, dims, NPY_FLOAT32, reinterpret_cast<void*>(leaf_lab)));
    PyArray_ENABLEFLAGS(np_lab, NPY_ARRAY_OWNDATA);

    PyObject* output = Py_BuildValue("OO", np_idx, np_lab);
    Py_DECREF(np_idx);
    Py_DECREF(np_lab);

    return output;
}
