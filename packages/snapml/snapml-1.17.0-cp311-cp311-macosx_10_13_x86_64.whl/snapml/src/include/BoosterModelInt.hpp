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
 *                Jan van Lunteren
 *                Milos Stanisavljevic
 *                Nikolaos Papandreou
 *
 * End Copyright
 ********************************************************************/

#ifndef BOOSTER_MODEL
#define BOOSTER_MODEL

#include "Model.hpp"
#include "TreeTypes.hpp"
#include "KernelRidgeEnsembleModel.hpp"
#include "TreeEnsembleModel.hpp"
#include "ComprTreeEnsembleModel.hpp"
#include "ModelExport.hpp"
#include "BoosterModel.hpp"

#ifdef Z14_SIMD
#include "MBITreeEnsembleModel.hpp"
#endif

namespace tree {

struct BoosterModel : public Model {

    BoosterModel(const snapml::task_t task_, const snapml::objective_t objective_, const uint32_t num_classes_,
                 const double base_prediction_, const double learning_rate_, const uint32_t random_state_,
                 const uint32_t n_components_, const float gamma_,
                 const std::vector<std::shared_ptr<TreeEnsembleModel>>        tree_ensemble_models_,
                 const std::vector<std::shared_ptr<KernelRidgeEnsembleModel>> kr_ensemble_models_)
        : task(task_)
        , objective(objective_)
        , num_classes(num_classes_)
        , base_prediction(base_prediction_)
        , learning_rate(learning_rate_)
        , random_state(random_state_)
        , n_components(n_components_)
        , gamma(gamma_)
        , tree_ensemble_models(tree_ensemble_models_)
        , kr_ensemble_models(kr_ensemble_models_)
    {
    }

    // currently do not support import for multi-class
    BoosterModel(std::shared_ptr<ModelImport> model_parser)
        : random_state(42)
        , n_components(10)
        , gamma(1.0)
    {

        // check if model is indeed a boosting machine
        if (model_parser->get_ensemble_type_valid()) {
            snapml::ensemble_t imported_ensemble_type = model_parser->get_ensemble_type();
            if (imported_ensemble_type != snapml::ensemble_t::boosting) {
                throw std::runtime_error("Import expects an ensemble of boosting type.");
            }
        }

        if (model_parser->get_model_type_valid()) {
            task = model_parser->get_model_type();
        } else {
            // json format doesn't contain information about the task directly
            task = snapml::task_t::regression;
        }

        if (task == snapml::task_t::classification) {

            if (!model_parser->get_num_classes_valid()) {
                throw std::runtime_error("Cannot detect number of classes from the model file.");
            }

            num_classes = model_parser->get_num_classes();

        } else {
            num_classes = 2;
        }

        if (num_classes > 2) {
            for (uint32_t j = 0; j < num_classes; j++) {
                auto tree_ensemble_model = std::make_shared<TreeEnsembleModel>(task, 2);
                tree_ensemble_model->import(model_parser, num_classes, j);
                tree_ensemble_models.push_back(tree_ensemble_model);
            }
        } else {
            auto tree_ensemble_model = std::make_shared<TreeEnsembleModel>(task, num_classes);
            tree_ensemble_model->import(model_parser, 1, 0);
            tree_ensemble_models.push_back(tree_ensemble_model);
        }

        base_prediction = model_parser->get_base_score();
        learning_rate   = model_parser->get_learning_rate();
        objective       = snapml::objective_t::mse;
    }

    BoosterModel() { }

    ~BoosterModel() { }

    void compress(const std::shared_ptr<glm::DenseDataset> data)
    {

        if (compr_tree_ensemble_models.size()) {
            assert(tree_ensemble_models.size() == 0);
            return;
        }

        assert(tree_ensemble_models.size() > 0);
        for (const auto& tree_ensemble_model : tree_ensemble_models) {
            auto compr_tree_ensemble_model = std::make_shared<ComprTreeEnsembleModel>();
            compr_tree_ensemble_model->compress(tree_ensemble_model, data);
            compr_tree_ensemble_models.push_back(compr_tree_ensemble_model);
        }
        tree_ensemble_models.resize(0);
        tree_ensemble_models.shrink_to_fit();
    }

    void export_model(const std::string filename, const std::string file_type, const std::vector<double>& classes,
                      const std::string version)
    {

        if (kr_ensemble_models.size()) {
            throw std::runtime_error("Export is not supported for ensembles containing kernel ridge regressors.");
        }

        if (compr_tree_ensemble_models.size()) {
            throw std::runtime_error("Export is not supported for compressed trees.");
        }

#ifdef Z14_SIMD
        if (mbi_tree_ensemble_models.size()) {
            throw std::runtime_error("Export is not supported for tensor-based trees.");
        }
#endif

        ModelExport(filename, file_type, tree_ensemble_models, snapml::ensemble_t::boosting, base_prediction,
                    learning_rate, snapml::compare_t::less_than, classes, task, version);
    }

#ifdef Z14_SIMD
    bool check_if_nnpa_installed() { return zdnn_is_nnpa_installed(); }

    void convert_mbit(const std::shared_ptr<glm::DenseDataset> data)
    {

        if (!zdnn_is_nnpa_installed()) {
            throw std::runtime_error("Accelerator chip not available in current Z system.");
        }

        if (mbi_tree_ensemble_models.size()) {
            assert(tree_ensemble_models.size() == 0);
            return;
        }

        assert(tree_ensemble_models.size() > 0);
        for (const auto& tree_ensemble_model : tree_ensemble_models) {
            auto mbit_tree_ensemble_model = std::make_shared<MBITreeEnsembleModel>();
            mbit_tree_ensemble_model->generate_data_structures(tree_ensemble_model, data);
            mbi_tree_ensemble_models.push_back(mbit_tree_ensemble_model);
        }
        tree_ensemble_models.resize(0);
        tree_ensemble_models.shrink_to_fit();
    }
#endif

    uint32_t get_n_regressors()
    {
        uint32_t out = 0;
        if (tree_ensemble_models.size()) {
            out += tree_ensemble_models[0]->get_num_trees();
        }
        if (compr_tree_ensemble_models.size()) {
            out += compr_tree_ensemble_models[0]->get_num_trees();
        }
#ifdef Z14_SIMD
        if (mbi_tree_ensemble_models.size()) {
            out += mbi_tree_ensemble_models[0]->get_num_trees();
        }
#endif
        if (kr_ensemble_models.size()) {
            out += kr_ensemble_models[0]->n_models;
        }
        return out;
    }

    void get(tree::Model::Getter& getter) override
    {
        getter.add(task);
        getter.add(objective);
        getter.add(num_classes);
        getter.add(base_prediction);
        getter.add(learning_rate);
        getter.add(random_state);
        getter.add(n_components);
        getter.add(gamma);

        uint32_t num_tree_ensembles = tree_ensemble_models.size();
        getter.add(num_tree_ensembles);

        for (uint32_t i = 0; i < num_tree_ensembles; i++)
            getter.add_model(tree_ensemble_models[i]);

        uint32_t num_compr_tree_ensembles = compr_tree_ensemble_models.size();
        getter.add(num_compr_tree_ensembles);

        for (uint32_t i = 0; i < num_compr_tree_ensembles; i++)
            getter.add_model(compr_tree_ensemble_models[i]);

#ifdef Z14_SIMD
        uint32_t num_mbi_tree_ensembles = mbi_tree_ensemble_models.size();
        getter.add(num_mbi_tree_ensembles);
        for (uint32_t i = 0; i < num_mbi_tree_ensembles; i++)
            getter.add_model(mbi_tree_ensemble_models[i]);
#else
        getter.add(static_cast<uint32_t>(0));
#endif

        uint32_t num_kr_ensembles = kr_ensemble_models.size();
        getter.add(num_kr_ensembles);

        for (uint32_t i = 0; i < num_kr_ensembles; i++)
            getter.add_model(kr_ensemble_models[i]);
    }

    void put(tree::Model::Setter& setter, const uint64_t len = 0) override
    {
        setter.get(&task);
        setter.get(&objective);
        setter.get(&num_classes);
        setter.get(&base_prediction);
        setter.get(&learning_rate);
        setter.get(&random_state);
        setter.get(&n_components);
        setter.get(&gamma);

        uint32_t num_tree_ensembles;
        setter.get(&num_tree_ensembles);

        for (uint32_t i = 0; i < num_tree_ensembles; i++) {
            uint64_t tree_ensemble_size;
            setter.get(&tree_ensemble_size);
            std::shared_ptr<TreeEnsembleModel> tree_ensemble_model = std::make_shared<TreeEnsembleModel>();
            tree_ensemble_model->put(setter, tree_ensemble_size);
            tree_ensemble_models.push_back(tree_ensemble_model);
        }

        uint32_t num_compr_tree_ensembles;
        setter.get(&num_compr_tree_ensembles);

        for (uint32_t i = 0; i < num_compr_tree_ensembles; i++) {
            uint64_t compr_tree_ensemble_size;
            setter.get(&compr_tree_ensemble_size);
            std::shared_ptr<ComprTreeEnsembleModel> compr_tree_ensemble_model
                = std::make_shared<ComprTreeEnsembleModel>();
            compr_tree_ensemble_model->put(setter, compr_tree_ensemble_size);
            compr_tree_ensemble_models.push_back(compr_tree_ensemble_model);
        }

        uint32_t num_mbi_tree_ensembles;
        setter.get(&num_mbi_tree_ensembles);

#ifdef Z14_SIMD

        for (uint32_t i = 0; i < num_mbi_tree_ensembles; i++) {
            uint64_t mbi_tree_ensemble_size;
            setter.get(&mbi_tree_ensemble_size);
            std::shared_ptr<MBITreeEnsembleModel> mbi_tree_ensemble_model = std::make_shared<MBITreeEnsembleModel>();
            mbi_tree_ensemble_model->put(setter, mbi_tree_ensemble_size);
            mbi_tree_ensemble_models.push_back(mbi_tree_ensemble_model);
        }
#endif

        uint32_t num_kr_ensembles;
        setter.get(&num_kr_ensembles);

        for (uint32_t i = 0; i < num_kr_ensembles; i++) {
            uint64_t kr_ensemble_size;
            setter.get(&kr_ensemble_size);
            std::shared_ptr<KernelRidgeEnsembleModel> kr_ensemble_model = std::make_shared<KernelRidgeEnsembleModel>();
            kr_ensemble_model->put(setter, kr_ensemble_size);
            kr_ensemble_models.push_back(kr_ensemble_model);
        }

        if (setter.get_offset() != setter.get_size())
            throw std::runtime_error("Inconsistent model data.");
    }

    snapml::task_t                                       task;
    snapml::objective_t                                  objective;
    uint32_t                                             num_classes;
    double                                               base_prediction;
    double                                               learning_rate;
    uint32_t                                             random_state;
    uint32_t                                             n_components;
    float                                                gamma;
    std::vector<std::shared_ptr<TreeEnsembleModel>>      tree_ensemble_models;
    std::vector<std::shared_ptr<ComprTreeEnsembleModel>> compr_tree_ensemble_models;
#ifdef Z14_SIMD
    std::vector<std::shared_ptr<MBITreeEnsembleModel>> mbi_tree_ensemble_models;
#endif
    std::vector<std::shared_ptr<KernelRidgeEnsembleModel>> kr_ensemble_models;
};

class BoosterModelInt : public snapml::BoosterModel {
public:
    BoosterModelInt(std::shared_ptr<tree::BoosterModel> model) { model_ = model; }
    BoosterModelInt(std::shared_ptr<tree::ModelImport> model_parser)
    {
        model_parser_ = model_parser;
        model_        = std::make_shared<tree::BoosterModel>(model_parser_);
    }
    const std::shared_ptr<tree::BoosterModel> get_internal() const { return model_; }
};

}

#endif
