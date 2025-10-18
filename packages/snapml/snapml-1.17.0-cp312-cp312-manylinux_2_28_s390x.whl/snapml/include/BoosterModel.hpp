/*********************************************************************
 *
 * Licensed Materials - Property of IBM
 *
 * (C) Copyright IBM Corp. 2022, 2023. All Rights Reserved.

 * US Government Users Restricted Rights - Use, duplication or
 * disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
 *
 ********************************************************************/

#pragma once

#include <mutex>

#include "DenseDataset.hpp"
#include "TreeTypes.hpp"
#include <string>

namespace tree {
struct BoosterModel;
class ModelImport;
}

namespace snapml {

//! @ingroup c-api
class BoosterModel {
public:
    BoosterModel();
    void compress(snapml::DenseDataset data);
    void convert_mbit(snapml::DenseDataset data);
    bool check_if_nnpa_installed();
    void get(std::vector<uint8_t>& vec);
    void put(const std::vector<uint8_t>& vec);
    void import_model(const std::string filename, const std::string file_type);
    void export_model(const std::string filename, const std::string file_type, const std::vector<double>& classes,
                      const std::string version);
    bool compressed_tree();
    snapml::task_t     get_task_type();
    uint32_t           get_num_classes();
    uint32_t           get_num_trees();
    std::vector<float> get_class_labels();
    bool               get_class_labels_valid();
    uint32_t           get_n_regressors();
    bool               mbit_tree();

protected:
    std::shared_ptr<tree::BoosterModel> model_;
    std::shared_ptr<tree::ModelImport>  model_parser_;
    std::shared_ptr<std::mutex>         mtx_;
};

}
