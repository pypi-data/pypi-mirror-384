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
 * Authors      : Andreea Anghel
 *                Celestine Duenner
 *                Thomas Parnell
 *                Nikolas Ioannou
 *                Milos Stanisavljevic
 *                Nikolaos Papandreou
 *
 * End Copyright
 ********************************************************************/

#ifndef FOREST_MODEL
#define FOREST_MODEL

#include "Model.hpp"
#include "TreeEnsembleModel.hpp"
#include "ComprTreeEnsembleModel.hpp"
#include "ModelExport.hpp"

#ifdef Z14_SIMD
#include "MBITreeEnsembleModel.hpp"
#endif

namespace tree {

struct ForestModel : public Model {

    ForestModel(std::shared_ptr<tree::TreeEnsembleModel> tree_ensemble_model)
        : tree_ensemble_model(tree_ensemble_model)
        , compr_tree_ensemble_model(nullptr)
#ifdef Z14_SIMD
        , mbi_tree_ensemble_model(nullptr)
#endif
    {
        task        = tree_ensemble_model->task;
        num_classes = tree_ensemble_model->num_classes;
    }

    ForestModel(std::shared_ptr<ModelImport> model_parser, snapml::task_t task_)
        : task(task_)
        , compr_tree_ensemble_model(nullptr)
#ifdef Z14_SIMD
        , mbi_tree_ensemble_model(nullptr)
#endif
    {

        // check if model is indeed a random forest (check only works for pmml)
        if (model_parser->get_ensemble_type_valid()) {
            snapml::ensemble_t imported_ensemble_type = model_parser->get_ensemble_type();
            if (imported_ensemble_type != snapml::ensemble_t::forest) {
                throw std::runtime_error("Import expects an ensemble of random forest type.");
            }
        }

        if (model_parser->get_model_type_valid()) {

            snapml::task_t model_type = model_parser->get_model_type();

            if (task == snapml::task_t::classification && model_type == snapml::task_t::regression) {
                throw std::runtime_error(
                    "Model file represents a regression model, but requested task is classification.");
            }

            if (task == snapml::task_t::regression && model_type == snapml::task_t::classification) {
                throw std::runtime_error(
                    "Model file represents a classification model, but requested task is regression.");
            }

        } else {
            throw std::runtime_error("Could not detect model type (classification or regression) from file.");
        }

        if (task == snapml::task_t::classification) {

            if (!model_parser->get_num_classes_valid()) {
                throw std::runtime_error("Cannot detect number of classes from the model file.");
            }

            num_classes = model_parser->get_num_classes();

            if (num_classes > 2) {
                throw std::runtime_error("ModelImport does not currently support multiclass classification.");
            }

        } else {
            num_classes = 2;
        }

        tree_ensemble_model = std::make_shared<TreeEnsembleModel>(task, num_classes);

        tree_ensemble_model->import(model_parser, 1, 0);
    }

    ForestModel() { }

    ~ForestModel() { }

    void compress(const std::shared_ptr<glm::DenseDataset> data)
    {

        if (compr_tree_ensemble_model != nullptr) {
            assert(tree_ensemble_model == nullptr);
            return;
        }

        assert(tree_ensemble_model != nullptr);
        compr_tree_ensemble_model = std::make_shared<ComprTreeEnsembleModel>();
        compr_tree_ensemble_model->compress(tree_ensemble_model, data);
        tree_ensemble_model = nullptr;
    }

    void export_model(const std::string filename, const std::string file_type, const std::vector<double>& classes,
                      const std::string version)
    {

        if (compr_tree_ensemble_model != nullptr) {
            throw std::runtime_error("Export is not supported for compressed trees.");
        }

#ifdef Z14_SIMD
        if (mbi_tree_ensemble_model != nullptr) {
            throw std::runtime_error("Export is not supported for tensor-based trees.");
        }
#endif

        if (num_classes > 2) {
            throw std::runtime_error("Export is not supported for multi-class random forest classification.");
        }

        ModelExport(filename, file_type, std::vector<std::shared_ptr<TreeEnsembleModel>>(1, tree_ensemble_model),
                    snapml::ensemble_t::forest, 0.0, 1.0, snapml::compare_t::less_than, classes, task, version);
    }

#ifdef Z14_SIMD
    bool check_if_nnpa_installed() { return zdnn_is_nnpa_installed(); }

    void convert_mbit(const std::shared_ptr<glm::DenseDataset> data)
    {

        if (!zdnn_is_nnpa_installed()) {
            throw std::runtime_error("Accelerator chip not available in current Z system.");
        }

        if (num_classes > 2) {
            throw std::runtime_error("Multi-class classification is currently not supported using zdnn_tensors; please "
                                     "try setting tree_format='compress_trees' to run on CPU.");
        }

        if (mbi_tree_ensemble_model != nullptr) {
            assert(tree_ensemble_model == nullptr);
            return;
        }

        assert(tree_ensemble_model != nullptr);
        mbi_tree_ensemble_model = std::make_shared<MBITreeEnsembleModel>();
        mbi_tree_ensemble_model->generate_data_structures(tree_ensemble_model, data);
        tree_ensemble_model = nullptr;
    }
#endif

    void get(tree::Model::Getter& getter) override
    {
        getter.add(task);
        getter.add(num_classes);
        std::vector<uint8_t> vec = {};

        getter.add_model(tree_ensemble_model);
        getter.add_model(compr_tree_ensemble_model);

#ifdef Z14_SIMD
        getter.add_model(mbi_tree_ensemble_model);
#else
        getter.add(static_cast<uint64_t>(0));
#endif
    }

    void put(tree::Model::Setter& setter, const uint64_t len = 0) override
    {
        setter.get(&task);
        setter.get(&num_classes);

        uint64_t tree_ensemble_size;
        setter.get(&tree_ensemble_size);

        if (tree_ensemble_size > 0) {
            tree_ensemble_model = std::make_shared<TreeEnsembleModel>();
            tree_ensemble_model->put(setter, tree_ensemble_size);
            assert(tree_ensemble_model->task == task);
            assert(tree_ensemble_model->num_classes == num_classes);
        }

        uint64_t compr_tree_ensemble_size;
        setter.get(&compr_tree_ensemble_size);

        if (compr_tree_ensemble_size > 0) {
            compr_tree_ensemble_model = std::make_shared<ComprTreeEnsembleModel>();
            compr_tree_ensemble_model->put(setter, compr_tree_ensemble_size);
            assert(compr_tree_ensemble_model->task == task);
            assert(compr_tree_ensemble_model->num_classes == num_classes);
        }

        uint64_t mbi_tree_ensemble_size;
        setter.get(&mbi_tree_ensemble_size);

#ifdef Z14_SIMD
        if (mbi_tree_ensemble_size > 0) {
            mbi_tree_ensemble_model = std::make_shared<MBITreeEnsembleModel>();
            mbi_tree_ensemble_model->put(setter, mbi_tree_ensemble_size);
        }
#endif
        if (setter.get_offset() != setter.get_size())
            throw std::runtime_error("Inconsistent model data.");
    }

    snapml::task_t                          task;
    uint32_t                                num_classes;
    std::shared_ptr<TreeEnsembleModel>      tree_ensemble_model;
    std::shared_ptr<ComprTreeEnsembleModel> compr_tree_ensemble_model;
#ifdef Z14_SIMD
    std::shared_ptr<MBITreeEnsembleModel> mbi_tree_ensemble_model;
#endif
};

class RandomForestModelInt : public snapml::RandomForestModel {
public:
    RandomForestModelInt() { }
    RandomForestModelInt(std::shared_ptr<tree::ForestModel> model) { model_ = model; }
    RandomForestModelInt(std::shared_ptr<tree::ModelImport> model_parser)
    {
        model_parser_ = model_parser;
        model_        = std::make_shared<tree::ForestModel>(model_parser_, model_parser_->get_model_type());
    }
    const std::shared_ptr<tree::ForestModel> get_internal() const { return model_; };
};

}

#endif
