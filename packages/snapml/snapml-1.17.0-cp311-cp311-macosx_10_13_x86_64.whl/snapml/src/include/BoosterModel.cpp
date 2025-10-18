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

#include "BoosterModel.hpp"
#include "BoosterModelInt.hpp"

namespace snapml {

BoosterModel::BoosterModel()
    : mtx_(std::shared_ptr<std::mutex>(new std::mutex()))
{
    model_        = std::make_shared<tree::BoosterModel>();
    model_parser_ = nullptr;
}

void BoosterModel::compress(snapml::DenseDataset data)
{
    std::unique_lock<std::mutex> lock(*mtx_);
    model_->compress(data.get());
}

void BoosterModel::convert_mbit(snapml::DenseDataset data)
{
#ifdef Z14_SIMD
    std::unique_lock<std::mutex> lock(*mtx_);
    model_->convert_mbit(data.get());
#endif
}

bool BoosterModel::check_if_nnpa_installed()
{
#ifdef Z14_SIMD
    std::unique_lock<std::mutex> lock(*mtx_);
    return model_->check_if_nnpa_installed();
#else
    return false;
#endif
}

void BoosterModel::get(std::vector<uint8_t>& vec)
{
    std::unique_lock<std::mutex> lock(*mtx_);
    tree::Model::Getter          getter(vec);
    model_->get(getter);
}

void BoosterModel::put(const std::vector<uint8_t>& vec)
{
    std::unique_lock<std::mutex> lock(*mtx_);
    tree::Model::Setter          setter(vec);
    model_->put(setter);
}

void BoosterModel::import_model(std::string filename, const std::string file_type)
{
    std::unique_lock<std::mutex> lock(*mtx_);
    model_parser_ = std::make_shared<tree::ModelImport>(filename, file_type, snapml::ensemble_t::boosting);
    model_        = std::make_shared<tree::BoosterModel>(model_parser_);
}

void BoosterModel::export_model(const std::string filename, const std::string file_type,
                                const std::vector<double>& classes, const std::string version)
{
    std::unique_lock<std::mutex> lock(*mtx_);
    model_->export_model(filename, file_type, classes, version);
}

bool BoosterModel::compressed_tree()
{
    std::unique_lock<std::mutex> lock(*mtx_);
    return (model_->compr_tree_ensemble_models.size() != 0);
}

snapml::task_t BoosterModel::get_task_type()
{
    std::unique_lock<std::mutex> lock(*mtx_);
    return model_->task;
}

uint32_t BoosterModel::get_num_classes()
{
    std::unique_lock<std::mutex> lock(*mtx_);
    return model_->num_classes;
}

uint32_t BoosterModel::get_num_trees()
{
    std::unique_lock<std::mutex> lock(*mtx_);
    return model_->tree_ensemble_models[0]->get_num_trees();
}

std::vector<float> BoosterModel::get_class_labels()
{
    std::unique_lock<std::mutex> lock(*mtx_);
    if (model_parser_ == nullptr)
        throw std::runtime_error("get_class_labels() member function is only available for imported models.");
    return model_parser_->get_class_labels();
}

bool BoosterModel::get_class_labels_valid()
{
    std::unique_lock<std::mutex> lock(*mtx_);
    if (model_parser_ == nullptr)
        throw std::runtime_error("get_class_labels_valid() member function is only available for imported models.");
    return model_parser_->get_class_labels_valid();
}

uint32_t BoosterModel::get_n_regressors()
{
    std::unique_lock<std::mutex> lock(*mtx_);
    return model_->get_n_regressors();
}

bool BoosterModel::mbit_tree()
{
#ifdef Z14_SIMD
    std::unique_lock<std::mutex> lock(*mtx_);
    return (model_->mbi_tree_ensemble_models.size() != 0);
#else
    return false;
#endif
}

}
