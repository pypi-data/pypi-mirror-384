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
 * Authors      :
 *
 * End Copyright
 ********************************************************************/

#include <mutex>

#include "RandomForestModel.hpp"
#include "ForestModel.hpp"
#include "DenseDatasetInt.hpp"

namespace snapml {

RandomForestModel::RandomForestModel()
    : mtx_(std::shared_ptr<std::mutex>(new std::mutex()))
{
    model_        = std::make_shared<tree::ForestModel>();
    model_parser_ = nullptr;
}

void RandomForestModel::compress(snapml::DenseDataset data)
{
    std::unique_lock<std::mutex> lock(*mtx_);
    model_->compress(data.get());
}

void RandomForestModel::convert_mbit(snapml::DenseDataset data)
{
#ifdef Z14_SIMD
    std::unique_lock<std::mutex> lock(*mtx_);
    model_->convert_mbit(data.get());
#endif
}

bool RandomForestModel::check_if_nnpa_installed()
{
#ifdef Z14_SIMD
    std::unique_lock<std::mutex> lock(*mtx_);
    return model_->check_if_nnpa_installed();
#else
    return false;
#endif
}

void RandomForestModel::get(std::vector<uint8_t>& vec)
{
    std::unique_lock<std::mutex> lock(*mtx_);
    tree::Model::Getter          getter(vec);
    model_->get(getter);
}

void RandomForestModel::put(const std::vector<uint8_t>& vec)
{
    std::unique_lock<std::mutex> lock(*mtx_);
    tree::Model::Setter          setter(vec);
    model_->put(setter);
}

void RandomForestModel::import_model(std::string filename, const std::string file_type, snapml::task_t task)
{
    if (file_type.compare("pmml") && file_type.compare("onnx")) {
        throw std::runtime_error("A random forest model can only be imported from PMML or ONNX format.");
    }
    std::unique_lock<std::mutex> lock(*mtx_);
    model_parser_ = std::make_shared<tree::ModelImport>(filename, file_type, snapml::ensemble_t::forest);
    model_        = std::make_shared<tree::ForestModel>(model_parser_, task);
}

void RandomForestModel::export_model(const std::string filename, const std::string file_type,
                                     const std::vector<double>& classes, const std::string version)
{
    std::unique_lock<std::mutex> lock(*mtx_);
    model_->export_model(filename, file_type, classes, version);
}

bool RandomForestModel::compressed_tree()
{
    std::unique_lock<std::mutex> lock(*mtx_);
    return (model_->compr_tree_ensemble_model != nullptr);
}

snapml::task_t RandomForestModel::get_task_type()
{
    std::unique_lock<std::mutex> lock(*mtx_);
    return model_->task;
}

uint32_t RandomForestModel::get_num_classes()
{
    std::unique_lock<std::mutex> lock(*mtx_);
    return model_->num_classes;
}

std::vector<float> RandomForestModel::get_class_labels()
{
    std::unique_lock<std::mutex> lock(*mtx_);
    if (model_parser_ == nullptr)
        throw std::runtime_error("get_class_labels() member function is only available for imported models.");
    return model_parser_->get_class_labels();
}

bool RandomForestModel::get_class_labels_valid()
{
    std::unique_lock<std::mutex> lock(*mtx_);
    if (model_parser_ == nullptr)
        throw std::runtime_error("get_class_labels_valid() member function is only available for imported models.");
    return model_parser_->get_class_labels_valid();
}

bool RandomForestModel::mbit_tree()
{
#ifdef Z14_SIMD
    std::unique_lock<std::mutex> lock(*mtx_);
    return (model_->mbi_tree_ensemble_model != nullptr);
#else
    return false;
#endif
}

}
