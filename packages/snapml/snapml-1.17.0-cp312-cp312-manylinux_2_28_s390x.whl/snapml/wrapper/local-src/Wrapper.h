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

#ifndef WRAPPER_H
#define WRAPPER_H

#define PY_SSIZE_T_CLEAN
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#undef _XOPEN_SOURCE
#undef _POSIX_C_SOURCE
#include <Python.h>

#define PY_ARRAY_UNIQUE_SYMBOL SNAP_ARRAY_API
#include <numpy/arrayobject.h>

#include <memory>
#include <vector>
#include <chrono>

typedef std::chrono::high_resolution_clock             Clock;
typedef std::chrono::high_resolution_clock::time_point CurTime;

// fwd declaration
namespace glm {
class DenseDataset;
class SparseDataset;
class Solver;
template <class D> class TreeInvariants;
}

namespace tree {
template <class N> class HistSolver;
}

namespace snapml {
class DenseDataset;
}

struct module_state {
    PyObject* type_error;
    PyObject* other_error;
};

#if PY_MAJOR_VERSION >= 3
#define GET_MODULE_STATE(m) ((struct module_state*)PyModule_GetState(m))
#else
#define GET_MODULE_STATE(m) (&_state)
extern struct module_state _state;
#endif

enum class wrapperError_t { Success, Failure };

// Booster
PyObject* booster_fit(PyObject* m, PyObject* args);
PyObject* booster_predict(PyObject* m, PyObject* args);
PyObject* booster_optimize_trees(PyObject* m, PyObject* args);
PyObject* booster_import(PyObject* m, PyObject* args);
PyObject* booster_export(PyObject* m, PyObject* args);
PyObject* booster_cache(PyObject* m, PyObject* args);
PyObject* booster_delete(PyObject* m, PyObject* args);
PyObject* booster_apply(PyObject* m, PyObject* args);

// DecisionTreeClassifier
PyObject* dtc_fit(PyObject* m, PyObject* args);
PyObject* dtc_predict(PyObject* m, PyObject* args);

// RandomForestClassifier
PyObject* rfc_fit(PyObject* m, PyObject* args);
PyObject* rfc_predict(PyObject* m, PyObject* args);
PyObject* rfc_optimize_trees(PyObject* m, PyObject* args);
PyObject* rfc_import(PyObject* m, PyObject* args);
PyObject* rfc_export(PyObject* m, PyObject* args);
PyObject* rfc_cache(PyObject* m, PyObject* args);
PyObject* rfc_delete(PyObject* m, PyObject* args);

// Generic import
PyObject* generic_import(PyObject* m, PyObject* args);

// LinearModels
PyObject* lr_fit(PyObject* dummy, PyObject* args);
PyObject* svm_fit(PyObject* dummy, PyObject* args);
PyObject* linear_fit(PyObject* dummy, PyObject* args);
PyObject* lr_predict_proba(PyObject* dummy, PyObject* args);
PyObject* lr_predict(PyObject* dummy, PyObject* args);
PyObject* svm_predict(PyObject* dummy, PyObject* args);
PyObject* svm_decision_function(PyObject* dummy, PyObject* args);
PyObject* linear_predict(PyObject* dummy, PyObject* args);

// RBF Sampler
PyObject* rbf_fit(PyObject* dummy, PyObject* args);
PyObject* rbf_transform(PyObject* dummy, PyObject* args);

// Loaders
PyObject* load_svmlight_file(PyObject* dummy, PyObject* args);
PyObject* load_from_svmlight_format(PyObject* self, PyObject* args);
PyObject* load_from_dense_snap_format(PyObject* self, PyObject* args);
PyObject* load_from_sparse_snap_format(PyObject* self, PyObject* args);
PyObject* load_from_l2sparse_snap_format(PyObject* self, PyObject* args);

// Metrics
PyObject* log_loss(PyObject* dummy, PyObject* args);
PyObject* mean_squared_error(PyObject* dummy, PyObject* args);
PyObject* accuracy(PyObject* dummy, PyObject* args);
PyObject* hinge_loss(PyObject* dummy, PyObject* args);

// Common
wrapperError_t check_numpy_sample_weight(PyObject* m, PyArrayObject* py_sample_weight, uint64_t num_ex);
wrapperError_t check_numpy_args(PyObject* m, PyArrayObject* py_indptr, PyArrayObject* py_indices,
                                PyArrayObject* py_data, PyArrayObject* py_labs, bool& is_sparse);
wrapperError_t count_num_pos_neg(PyObject* m, PyArrayObject* py_labs, uint32_t& num_pos, uint32_t& num_neg);
wrapperError_t make_sparse_dataset(PyObject* m, uint32_t num_ex, uint32_t num_ft, uint64_t num_nz, uint32_t num_pos,
                                   uint32_t num_neg, PyArrayObject* py_indptr, PyArrayObject* py_indices,
                                   PyArrayObject* py_data, PyArrayObject* py_labs,
                                   std::shared_ptr<glm::SparseDataset>& data);
wrapperError_t make_dense_dataset(PyObject* m, uint32_t num_ex, uint32_t num_ft, uint64_t num_nz, uint32_t num_pos,
                                  uint32_t num_neg, PyArrayObject* py_data, PyArrayObject* py_labs,
                                  std::shared_ptr<glm::DenseDataset>& data);
wrapperError_t make_dense_dataset_api(PyObject* m, uint32_t num_ex, uint32_t num_ft, PyArrayObject* py_data,
                                      PyArrayObject* py_labs, snapml::DenseDataset& data_out);

// Model Data
PyObject* model_allocate(PyObject* m);
PyObject* model_get(PyObject* m, PyObject* args);
PyObject* model_put(PyObject* m, PyObject* args);

#if !defined(WIN_BUILD) && !defined(WITH_ZOS)
// GraphFeaturePreprocessor
void      pygraphfeatures_delete(PyObject* gp_ptr);
PyObject* pygraphfeatures_allocate(PyObject* self);
PyObject* pygraphfeatures_set_params(PyObject* self, PyObject* args);
PyObject* pygraphfeatures_get_output_array_dims(PyObject* self, PyObject* args);
PyObject* pygraphfeatures_import_graph(PyObject* self, PyObject* args);
PyObject* pygraphfeatures_export_graph(PyObject* self, PyObject* args);
PyObject* pygraphfeatures_get_num_engineered_features(PyObject* self, PyObject* args);
PyObject* pygraphfeatures_transform(PyObject* self, PyObject* args);
PyObject* pygraphfeatures_partial_fit(PyObject* self, PyObject* args);
void      python_cleanup();
#endif

template <class D, class O>
std::shared_ptr<glm::Solver> make_device_solver(D* data, O* obj, double sigma, double tol,
                                                std::vector<uint32_t> device_ids, uint32_t num_threads, bool add_bias,
                                                double bias_val);

#endif
