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

#include "Wrapper.h"

#ifdef WITH_CUDA
#include <cuda_runtime.h>
#endif

PyObject* get_gpu_count(PyObject* m, PyObject* args)
{

#ifdef WITH_CUDA

    int nDevices;

    cudaError_t err = cudaGetDeviceCount(&nDevices);
    if (err == cudaSuccess && nDevices > 0) {
        return PyLong_FromLong(nDevices);
    } else {
        return PyLong_FromLong(0);
    }
#else
    return PyLong_FromLong(0);
#endif
}

static PyMethodDef mymethods[] = {
    { "load_svmlight_file", reinterpret_cast<PyCFunction>(load_svmlight_file), METH_VARARGS, "Load libsvm" },
    { "load_from_svmlight_format", reinterpret_cast<PyCFunction>(load_from_svmlight_format), METH_VARARGS,
      "Load svm file in snap format" },
    { "load_from_dense_snap_format", reinterpret_cast<PyCFunction>(load_from_dense_snap_format), METH_VARARGS,
      "Load dense snap format" },
    { "load_from_sparse_snap_format", reinterpret_cast<PyCFunction>(load_from_sparse_snap_format), METH_VARARGS,
      "Load sparse snap format" },
    { "load_from_l2sparse_snap_format", reinterpret_cast<PyCFunction>(load_from_l2sparse_snap_format), METH_VARARGS,
      "Load l2sparse snap format" },
    { "lr_fit", reinterpret_cast<PyCFunction>(lr_fit), METH_VARARGS, "Fit model (LogisticRegression)" },
    { "lr_predict_proba", reinterpret_cast<PyCFunction>(lr_predict_proba), METH_VARARGS,
      "Predict probabilities (LogisticRegression)" },
    { "lr_predict", reinterpret_cast<PyCFunction>(lr_predict), METH_VARARGS, "Predict classes (LogisticRegression)" },
    { "svm_fit", reinterpret_cast<PyCFunction>(svm_fit), METH_VARARGS, "Fit model (SupportVectorMachine)" },
    { "svm_predict", reinterpret_cast<PyCFunction>(svm_predict), METH_VARARGS, "Predict (SupportVectorMachine)" },
    { "svm_decision_function", reinterpret_cast<PyCFunction>(svm_decision_function), METH_VARARGS,
      "Decision function (SupportVectorMachine)" },
    { "linear_fit", reinterpret_cast<PyCFunction>(linear_fit), METH_VARARGS, "Fit model (LinearRegression)" },
    { "linear_predict", reinterpret_cast<PyCFunction>(linear_predict), METH_VARARGS, "Predict (LinearRegression)" },
    { "dtc_fit", reinterpret_cast<PyCFunction>(dtc_fit), METH_VARARGS, "Fit model (DecisionTreeClassifier)" },
    { "dtc_predict", reinterpret_cast<PyCFunction>(dtc_predict), METH_VARARGS,
      "Predict classes (DecisionTreeClassifier)" },
    { "rfc_fit", reinterpret_cast<PyCFunction>(rfc_fit), METH_VARARGS, "Fit model (RandomForestClassifier)" },
    { "rfc_predict", reinterpret_cast<PyCFunction>(rfc_predict), METH_VARARGS,
      "Predict classes (RandomForestClassifier)" },
    { "rfc_optimize_trees", reinterpret_cast<PyCFunction>(rfc_optimize_trees), METH_VARARGS,
      "Optimize_trees (Forest)" },
    { "rfc_import", reinterpret_cast<PyCFunction>(rfc_import), METH_VARARGS, "Import trees (Forest)" },
    { "rfc_export", reinterpret_cast<PyCFunction>(rfc_export), METH_VARARGS, "Export trees (Forest)" },
    { "rfc_cache", reinterpret_cast<PyCFunction>(rfc_cache), METH_VARARGS, "Cache forest model" },
    { "rfc_delete", reinterpret_cast<PyCFunction>(rfc_delete), METH_VARARGS, "Remove forest model from cache" },
    { "booster_fit", reinterpret_cast<PyCFunction>(booster_fit), METH_VARARGS, "Fit model (Booster)" },
    { "booster_predict", reinterpret_cast<PyCFunction>(booster_predict), METH_VARARGS, "Predict (Booster)" },
    { "booster_optimize_trees", reinterpret_cast<PyCFunction>(booster_optimize_trees), METH_VARARGS,
      "Optimize trees (Booster)" },
    { "booster_import", reinterpret_cast<PyCFunction>(booster_import), METH_VARARGS, "Import trees (Booster)" },
    { "booster_export", reinterpret_cast<PyCFunction>(booster_export), METH_VARARGS, "Export trees (Booster)" },
    { "booster_cache", reinterpret_cast<PyCFunction>(booster_cache), METH_VARARGS, "Cache booster model" },
    { "booster_delete", reinterpret_cast<PyCFunction>(booster_delete), METH_VARARGS,
      "Remove booster model from cache." },
    { "booster_apply", reinterpret_cast<PyCFunction>(booster_apply), METH_VARARGS,
      "Get leaf indices for batch of examples." },
    { "rbf_fit", reinterpret_cast<PyCFunction>(rbf_fit), METH_VARARGS, "Fit kernel approximator (RBF Sampler)" },
    { "rbf_transform", reinterpret_cast<PyCFunction>(rbf_transform), METH_VARARGS, "Transformer (RBF Sampler)" },
    { "get_gpu_count", reinterpret_cast<PyCFunction>(get_gpu_count), METH_VARARGS, "Get GPU Count if available" },
    { "log_loss", reinterpret_cast<PyCFunction>(log_loss), METH_VARARGS, "Logistic Loss (snap format data)" },
    { "accuracy", reinterpret_cast<PyCFunction>(accuracy), METH_VARARGS, "Accuracy (snap format data)" },
    { "mean_squared_error", reinterpret_cast<PyCFunction>(mean_squared_error), METH_VARARGS,
      "Mean squared error (snap format data)" },
    { "hinge_loss", reinterpret_cast<PyCFunction>(hinge_loss), METH_VARARGS, "Hinge loss (snap format data)" },
    { "model_allocate", reinterpret_cast<PyCFunction>(model_allocate), METH_NOARGS,
      "Allocate memory for the model data" },
    { "model_get", reinterpret_cast<PyCFunction>(model_get), METH_O, "Get model data to store elsewhere" },
    { "model_put", reinterpret_cast<PyCFunction>(model_put), METH_VARARGS, "Create a vector based on a numpy array" },
    { "generic_import", reinterpret_cast<PyCFunction>(generic_import), METH_VARARGS, "Import trees (generic)" },
#if !defined(WIN_BUILD) && !defined(WITH_ZOS)
    { "gf_set_params", reinterpret_cast<PyCFunction>(pygraphfeatures_set_params), METH_VARARGS,
      "Set parameters of the graph preprocessor" },
    { "gf_allocate", reinterpret_cast<PyCFunction>(pygraphfeatures_allocate), METH_NOARGS,
      "Allocate memory for the graph preprocessor" },
    { "gf_transform", reinterpret_cast<PyCFunction>(pygraphfeatures_transform), METH_VARARGS,
      "Engineer topological features to enrich feature representation" },
    { "gf_partial_fit", reinterpret_cast<PyCFunction>(pygraphfeatures_partial_fit), METH_VARARGS, "Update the graph" },
    { "gf_get_num_engineered_features", reinterpret_cast<PyCFunction>(pygraphfeatures_get_num_engineered_features),
      METH_VARARGS, "Retrieve the number of new features engineered" },
    { "gf_get_output_array_dims", reinterpret_cast<PyCFunction>(pygraphfeatures_get_output_array_dims), METH_VARARGS,
      "Retrieve the number dimensions of the output array used by export_graph" },
    { "gf_import_graph", reinterpret_cast<PyCFunction>(pygraphfeatures_import_graph), METH_VARARGS,
      "Import graph from a numpy array" },
    { "gf_export_graph", reinterpret_cast<PyCFunction>(pygraphfeatures_export_graph), METH_VARARGS,
      "Export graph into a numpy array" },
#endif
    { NULL, NULL, 0, NULL }
};

#if PY_MAJOR_VERSION >= 3

// required for 3
static int mytraverse(PyObject* m, visitproc visit, void* arg)
{
    Py_VISIT(GET_MODULE_STATE(m)->type_error);
    Py_VISIT(GET_MODULE_STATE(m)->other_error);
    return 0;
}

// required for 3
static int myclear(PyObject* m)
{
    Py_CLEAR(GET_MODULE_STATE(m)->type_error);
    Py_CLEAR(GET_MODULE_STATE(m)->other_error);
    return 0;
}

// required for 3
static struct PyModuleDef moduledef = { PyModuleDef_HEAD_INIT,
#ifdef X86_AVX2
                                        "libsnapmllocal3_avx2",
#else
                                        "libsnapmllocal3",
#endif
                                        NULL,
                                        sizeof(struct module_state),
                                        mymethods,
                                        NULL,
                                        mytraverse,
                                        myclear,
                                        NULL };

#define INITERROR return NULL

#ifdef X86_AVX2
PyMODINIT_FUNC PyInit_libsnapmllocal3_avx2(void)
#else
PyMODINIT_FUNC PyInit_libsnapmllocal3(void)
#endif

#else
// global py2 module state
struct module_state _state;
#define INITERROR return

PyMODINIT_FUNC initlibsnapmllocal2(void)
#endif

{
#if PY_MAJOR_VERSION >= 3
    PyObject* module = PyModule_Create(&moduledef);
#else
    PyObject* module = Py_InitModule("libsnapmllocal2", mymethods);
#endif

    import_array();

    if (module == NULL)
        INITERROR;

    struct module_state* st = GET_MODULE_STATE(module);

    // Setting up the errors
    char error[]    = "SnapMlLibrary.Error";
    st->other_error = PyErr_NewException(error, NULL, NULL);

    if (st->other_error == NULL) {
        Py_DECREF(module);
        INITERROR;
    }

    char error_[]  = "SnapMlLibrary.TypeError";
    st->type_error = PyErr_NewException(error_, NULL, NULL);

    if (st->type_error == NULL) {
        Py_DECREF(module);
        INITERROR;
    }

#if PY_MAJOR_VERSION >= 3
    return module;
#endif
}
