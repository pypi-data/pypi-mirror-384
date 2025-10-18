/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2022
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Thomas Parnell
 *                Jan van Lunteren
 *
 * End Copyright
 ********************************************************************/

/*! @file
 *  @ingroup wrapper
 */

#define NO_IMPORT_ARRAY
#include "Wrapper.h"

#include "DenseDataset.hpp"
#include "BoosterModelInt.hpp"
#include "BoosterModel.hpp"
#include "RandomForestModel.hpp"
#include "ForestModel.hpp"

template <class T> void get_common(T& model, PyObject** classes_out, uint32_t* num_classes_out, PyObject* model_ptr)
{

    PyObject* pyclasses   = nullptr;
    uint32_t  num_classes = model.get_num_classes();

    if (model.get_task_type() == snapml::task_t::classification) {
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

    *classes_out     = pyclasses;
    *num_classes_out = num_classes;

    // serialize the model
    std::vector<uint8_t>* vec = reinterpret_cast<std::vector<uint8_t>*>(PyCapsule_GetPointer(model_ptr, NULL));
    // inside the API proxy class a vector should be passed
    model.get(*vec);
}

void add_to_dict(PyObject* dict, std::string key, const std::vector<std::string>& in)
{

    PyObject* list = PyList_New(in.size());
    for (uint32_t i = 0; i < in.size(); i++) {
        // PyList_SetItem steals reference
        PyList_SetItem(list, i, PyUnicode_FromString(in[i].c_str()));
    }
    // PyDict_SetItemString does not steal reference
    PyDict_SetItemString(dict, key.c_str(), list);
    Py_DECREF(list);
}

wrapperError_t __generic_import(PyObject* m, const std::string filename, const std::string file_type,
                                bool remap_feature_indices, snapml::task_t& task_type,
                                snapml::ensemble_t& ensemble_type, PyObject** classes_out, uint32_t* num_classes_out,
                                PyObject** used_features_out, PyObject** schema_out, PyObject* model_ptr)
{

    try {

        // note last argument needs to be removed
        const std::shared_ptr<tree::ModelImport> parser
            = std::make_shared<tree::ModelImport>(filename, file_type, snapml::ensemble_t::boosting);

        // remap feature indices to those used in the model
        if (remap_feature_indices) {
            parser->update_to_used_features_only();
        }

        std::vector<uint32_t> used_features = parser->get_used_features();

        const size_t n_used_features = used_features.size();

        uint32_t* const used_features_ = new uint32_t[n_used_features];

        for (uint32_t i = 0; i < n_used_features; i++) {
            used_features_[i] = used_features[i];
        }

        int64_t  n_used_features_int64 = static_cast<int64_t>(n_used_features);
        npy_intp features_dims[] { n_used_features_int64 };
        *used_features_out = reinterpret_cast<PyObject*>(
            PyArray_SimpleNewFromData(1, features_dims, NPY_UINT32, reinterpret_cast<void*>(used_features_)));

        ensemble_type = parser->get_ensemble_type();
        task_type     = parser->get_model_type();

        PyObject* schema_features = PyDict_New();
        add_to_dict(schema_features, "name", parser->get_feature_names());
        add_to_dict(schema_features, "data_type", parser->get_feature_datatypes());
        add_to_dict(schema_features, "op_types", parser->get_feature_optypes());

        PyObject* schema_target = PyDict_New();
        add_to_dict(schema_target, "name", parser->get_target_field_names());
        add_to_dict(schema_target, "data_type", parser->get_target_field_datatypes());
        add_to_dict(schema_target, "op_type", parser->get_target_field_optypes());

        PyObject* schema_output = PyDict_New();
        add_to_dict(schema_output, "name", parser->get_output_field_names());
        add_to_dict(schema_output, "data_type", parser->get_output_field_datatypes());
        add_to_dict(schema_output, "op_type", parser->get_output_field_optypes());

        *schema_out = PyDict_New();
        PyDict_SetItemString(*schema_out, "features", schema_features);
        PyDict_SetItemString(*schema_out, "target_field", schema_target);
        PyDict_SetItemString(*schema_out, "output_field", schema_output);
        Py_DECREF(schema_features);
        Py_DECREF(schema_target);
        Py_DECREF(schema_output);

        if (ensemble_type == snapml::ensemble_t::boosting) {
            tree::BoosterModelInt model(parser);
            get_common(static_cast<snapml::BoosterModel&>(model), classes_out, num_classes_out, model_ptr);
        } else {
            tree::RandomForestModelInt model(parser);
            get_common(static_cast<snapml::RandomForestModel&>(model), classes_out, num_classes_out, model_ptr);
        }

    } catch (const std::exception& e) {
        struct module_state* st = GET_MODULE_STATE(m);
        PyErr_SetString(st->other_error, e.what());
        return wrapperError_t::Failure;
    }

    return wrapperError_t::Success;
}

PyObject* generic_import(PyObject* m, PyObject* args)
{

    char*     ext_model_import_filename;
    char*     ext_model_import_file_type;
    npy_int64 remap_feature_indices {};
    PyObject* model_ptr = nullptr;
    if (!PyArg_ParseTuple(args, "zzLO", &ext_model_import_filename, &ext_model_import_file_type, &remap_feature_indices,
                          &model_ptr)) {
        return NULL;
    }

    std::string model_filename {};
    if (ext_model_import_filename != NULL)
        model_filename.assign(ext_model_import_filename);

    std::string model_file_type {};
    if (ext_model_import_file_type != NULL)
        model_file_type.assign(ext_model_import_file_type);

    snapml::task_t     task_type {};
    snapml::ensemble_t ensemble_type {};
    PyObject*          pyclasses   = nullptr;
    PyObject*          pyfeatures  = nullptr;
    PyObject*          pyschema    = nullptr;
    uint32_t           num_classes = 0;

    wrapperError_t chk {};

    chk = __generic_import(m, model_filename, model_file_type, remap_feature_indices, task_type, ensemble_type,
                           &pyclasses, &num_classes, &pyfeatures, &pyschema, model_ptr);

    if (chk != wrapperError_t::Success) {
        return NULL;
    }
    // build a Python object import_metadata with the following information
    if (pyclasses != Py_None) {
        PyArray_ENABLEFLAGS(reinterpret_cast<PyArrayObject*>(pyclasses), NPY_ARRAY_OWNDATA);
    }

    PyArray_ENABLEFLAGS(reinterpret_cast<PyArrayObject*>(pyfeatures), NPY_ARRAY_OWNDATA);

    std::string task_str     = (task_type == snapml::task_t::classification) ? "classification" : "regression";
    std::string ensemble_str = (ensemble_type == snapml::ensemble_t::boosting) ? "boosting" : "forest";

    PyObject* output
        = Py_BuildValue("ssOIOO", task_str.c_str(), ensemble_str.c_str(), pyclasses, num_classes, pyfeatures, pyschema);

    if (pyclasses != Py_None) {
        Py_DECREF(pyclasses);
    }

    Py_DECREF(pyfeatures);
    Py_DECREF(pyschema);

    return output;
}
