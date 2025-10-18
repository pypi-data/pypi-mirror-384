/******************************************************************
 *
 * Licensed Materials - Property of IBM
 *
 * (C) Copyright IBM Corp. 2017, 2019. All Rights Reserved.
 *
 * US Government Users Restricted Rights - Use, duplication or
 * disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
 *
 *******************************************************************/

#include <Python.h>
#include <iostream>
#include "common.hpp"

struct module_state {
    PyObject* type_error;
    PyObject* other_error;
};

#define GET_MODULE_STATE(m) ((struct module_state*)PyModule_GetState(m))

/* Fn to check the license file existence.
 * Returns  0 : If it exists
 *         -1 : license file missing
 */
int enterprise_license_exist()
{
    struct stat        buffer;
    int                rc                   = 0;
    static const char* COMMON_PATH          = "/kernel/conf/platform.entitlement";
    static const char* DEFAULT_LICENSE_PATH = "/opt/ibm/spectrumcomputing/kernel/conf/platform.entitlement";
    std::string        LICENSE_PATH         = std::string(DEFAULT_LICENSE_PATH);
    char const*        EGO_TOP_VAL          = std::getenv("EGO_TOP");

    if (EGO_TOP_VAL != NULL) {
        LICENSE_PATH = std::string(EGO_TOP_VAL) + std::string(COMMON_PATH);
    }

    if (stat(LICENSE_PATH.c_str(), &buffer) != 0) {
        rc = -1;
    }

    return rc;
}

/* Expose this license check to python
 *   Returns  0 : If it exists
 *           -1 : license file missing
 */
static PyObject* check_enterprise_license(PyObject* m) { return Py_BuildValue("i", enterprise_license_exist()); }

static PyMethodDef mymethods[]
    = { { "check_enterprise_license", reinterpret_cast<PyCFunction>(check_enterprise_license), METH_NOARGS,
          "Check for WML accelerator license" },
        { NULL } };

static int mytraverse(PyObject* m, visitproc visit, void* arg)
{
    Py_VISIT(GET_MODULE_STATE(m)->type_error);
    Py_VISIT(GET_MODULE_STATE(m)->other_error);
    return 0;
}

static int myclear(PyObject* m)
{
    Py_CLEAR(GET_MODULE_STATE(m)->type_error);
    Py_CLEAR(GET_MODULE_STATE(m)->other_error);
    return 0;
}

static struct PyModuleDef moduledef = { PyModuleDef_HEAD_INIT,
#ifdef X86_AVX2
                                        "libsnapmlutils_avx2",
#else
                                        "libsnapmlutils",
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
PyMODINIT_FUNC PyInit_libsnapmlutils_avx2(void)
#else
PyMODINIT_FUNC PyInit_libsnapmlutils(void)
#endif
{
    PyObject* module = PyModule_Create(&moduledef);

    if (module == NULL)
        INITERROR;

    struct module_state* st = GET_MODULE_STATE(module);

    /* Adding module globals */
    if (PyModule_AddIntConstant(module, "max_gpus_base", MAX_GPUS_FOR_BASE)) {
        Py_DECREF(module);
        INITERROR;
    }

    if (PyModule_AddIntConstant(module, "max_nodes_base", MAX_NODES_FOR_BASE)) {
        Py_DECREF(module);
        INITERROR;
    }

    if (PyModule_AddStringConstant(module, "nodes_errmsg", NODES_ERRMSG)) {
        Py_DECREF(module);
        INITERROR;
    }

    if (PyModule_AddStringConstant(module, "gpus_errmsg", GPUS_ERRMSG)) {
        Py_DECREF(module);
        INITERROR;
    }

    if (PyModule_AddStringConstant(module, "processes_errmsg", PROCESSES_ERRMSG)) {
        Py_DECREF(module);
        INITERROR;
    }

    if (PyModule_AddStringConstant(module, "nodes_infomsg", NODES_INFOMSG)) {
        Py_DECREF(module);
        INITERROR;
    }

    if (PyModule_AddStringConstant(module, "gpus_infomsg", GPUS_INFOMSG)) {
        Py_DECREF(module);
        INITERROR;
    }

    if (PyModule_AddStringConstant(module, "processes_infomsg", PROCS_INFOMSG)) {
        Py_DECREF(module);
        INITERROR;
    }

    // Setting up the errors
    char error[]    = "SnapMlUtilsLibrary.Error";
    st->other_error = PyErr_NewException(error, NULL, NULL);

    if (st->other_error == NULL) {
        Py_DECREF(module);
        INITERROR;
    }

    char error_[]  = "SnapMlUtilsLibrary.TypeError";
    st->type_error = PyErr_NewException(error_, NULL, NULL);

    if (st->type_error == NULL) {
        Py_DECREF(module);
        INITERROR;
    }

    return module;
}
