/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2023
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Thomas Parnell
 *
 * End Copyright
 ********************************************************************/
#include <mutex>

#include "GenericTreeEnsembleModel.hpp"
#include "TreeTypes.hpp"
#include "ModelImport.hpp"
#include "BoosterModel.hpp"
#include "BoosterModelInt.hpp"
#include "RandomForestModel.hpp"
#include "ForestModel.hpp"

namespace snapml {

GenericTreeEnsembleModel::GenericTreeEnsembleModel()
    : mtx_(std::shared_ptr<std::mutex>(new std::mutex()))
{
    model_parser_  = nullptr;
    booster_model_ = nullptr;
    rf_model_      = nullptr;
}

snapml::ensemble_t GenericTreeEnsembleModel::get_ensemble_type() const
{
    if (booster_model_ == nullptr) {
        return snapml::ensemble_t::forest;
    } else {
        return snapml::ensemble_t::boosting;
    }
}

std::shared_ptr<snapml::BoosterModel> GenericTreeEnsembleModel::get_booster_model() const { return booster_model_; }

std::shared_ptr<snapml::RandomForestModel> GenericTreeEnsembleModel::get_rf_model() const { return rf_model_; }

void GenericTreeEnsembleModel::import_model(std::string filename, const std::string file_type,
                                            bool remap_feature_indices)
{
    std::unique_lock<std::mutex> lock(*mtx_);
    model_parser_ = std::make_shared<tree::ModelImport>(filename, file_type, snapml::ensemble_t::boosting);

    if (remap_feature_indices) {
        model_parser_->update_to_used_features_only();
    }

    if (model_parser_->get_ensemble_type() == snapml::ensemble_t::boosting) {
        booster_model_ = std::make_shared<tree::BoosterModelInt>(model_parser_);
        rf_model_      = nullptr;
    } else {
        booster_model_ = nullptr;
        rf_model_      = std::make_shared<tree::RandomForestModelInt>(model_parser_);
    }
}

void GenericTreeEnsembleModel::compress(snapml::DenseDataset data)
{
    if (rf_model_ == nullptr) {
        booster_model_->compress(data);
    } else {
        rf_model_->compress(data);
    }
}

void GenericTreeEnsembleModel::convert_mbit(snapml::DenseDataset data)
{
    if (rf_model_ == nullptr) {
        booster_model_->convert_mbit(data);
    } else {
        rf_model_->convert_mbit(data);
    }
}

bool GenericTreeEnsembleModel::compressed_tree()
{
    if (rf_model_ == nullptr) {
        return booster_model_->compressed_tree();
    } else {
        return rf_model_->compressed_tree();
    }
}

bool GenericTreeEnsembleModel::check_if_nnpa_installed()
{
    if (rf_model_ == nullptr) {
        return booster_model_->check_if_nnpa_installed();
    } else {
        return rf_model_->check_if_nnpa_installed();
    }
}

void GenericTreeEnsembleModel::get(std::vector<uint8_t>& vec)
{
    if (rf_model_ == nullptr) {
        booster_model_->get(vec);
    } else {
        rf_model_->get(vec);
    }
}

void GenericTreeEnsembleModel::put(const std::vector<uint8_t>& vec)
{
    if (rf_model_ == nullptr) {
        booster_model_->put(vec);
    } else {
        rf_model_->put(vec);
    }
}

void GenericTreeEnsembleModel::export_model(const std::string filename, const std::string file_type,
                                            const std::vector<double>& classes, const std::string version)
{
    if (rf_model_ == nullptr) {
        booster_model_->export_model(filename, file_type, classes, version);
    } else {
        rf_model_->export_model(filename, file_type, classes, version);
    }
}

snapml::task_t GenericTreeEnsembleModel::get_task_type()
{
    if (rf_model_ == nullptr) {
        return booster_model_->get_task_type();
    } else {
        return rf_model_->get_task_type();
    }
}

uint32_t GenericTreeEnsembleModel::get_num_classes()
{
    if (rf_model_ == nullptr) {
        return booster_model_->get_num_classes();
    } else {
        return rf_model_->get_num_classes();
    }
}

std::vector<float> GenericTreeEnsembleModel::get_class_labels()
{
    if (rf_model_ == nullptr) {
        return booster_model_->get_class_labels();
    } else {
        return rf_model_->get_class_labels();
    }
}

bool GenericTreeEnsembleModel::get_class_labels_valid()
{
    if (rf_model_ == nullptr) {
        return booster_model_->get_class_labels_valid();
    } else {
        return rf_model_->get_class_labels_valid();
    }
}

bool GenericTreeEnsembleModel::mbit_tree()
{
    if (rf_model_ == nullptr) {
        return booster_model_->mbit_tree();
    } else {
        return rf_model_->mbit_tree();
    }
}

std::vector<uint32_t> GenericTreeEnsembleModel::get_used_features() const { return model_parser_->get_used_features(); }

std::vector<std::string> GenericTreeEnsembleModel::get_feature_names() const
{
    return model_parser_->get_feature_names();
}

std::vector<std::string> GenericTreeEnsembleModel::get_feature_datatypes() const
{
    return model_parser_->get_feature_datatypes();
}

std::vector<std::string> GenericTreeEnsembleModel::get_feature_optypes() const
{
    return model_parser_->get_feature_optypes();
}

std::vector<std::string> GenericTreeEnsembleModel::get_target_field_names() const
{
    return model_parser_->get_target_field_names();
}

std::vector<std::string> GenericTreeEnsembleModel::get_target_field_datatypes() const
{
    return model_parser_->get_target_field_datatypes();
}

std::vector<std::string> GenericTreeEnsembleModel::get_target_field_optypes() const
{
    return model_parser_->get_target_field_optypes();
}

std::vector<std::string> GenericTreeEnsembleModel::get_output_field_names() const
{
    return model_parser_->get_output_field_names();
}

std::vector<std::string> GenericTreeEnsembleModel::get_output_field_datatypes() const
{
    return model_parser_->get_output_field_datatypes();
}

std::vector<std::string> GenericTreeEnsembleModel::get_output_field_optypes() const
{
    return model_parser_->get_output_field_optypes();
}

}
