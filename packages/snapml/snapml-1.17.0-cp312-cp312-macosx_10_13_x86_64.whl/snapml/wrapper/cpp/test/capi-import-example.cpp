#include "GenericTreeEnsembleModel.hpp"
#include "GenericTreeEnsemblePredictor.hpp"
#include "DenseDataset.hpp"

#include <iostream>
#include <cassert>
#include "Dataset.h"

int main()
{

    std::cout << "  Loading the test dataset " << std::endl;
    Dataset test_data("../data/test_data.csv");
    test_data.validate();

    snapml::DenseDataset snapml_test_data = snapml::DenseDataset(test_data.get_num_ex(), test_data.get_num_ft(),
                                                                 test_data.get_data(), test_data.get_labels());

    std::vector<std::string> filenames;
    filenames.push_back("../models/rf_model.pmml");
    filenames.push_back("../models/xgb_model.pmml");

    for (std::string filename : filenames) {

        std::cout << "  Importing model from file " << std::endl;
        snapml::GenericTreeEnsembleModel model;
        model.import_model(filename, "pmml");

        auto used_features = model.get_used_features();
        std::cout << "Used features: ";
        for (auto ft : used_features) {
            std::cout << ft << ", ";
        }
        std::cout << std::endl;

        auto feature_names     = model.get_feature_names();
        auto feature_datatypes = model.get_feature_datatypes();
        auto feature_optypes   = model.get_feature_optypes();
        std::cout << "Features: " << std::endl;
        for (uint32_t i = 0; i < used_features.size(); i++) {
            printf("ft_ind: %d, name: %s, datatype: %s, optype: %s\n", used_features[i], feature_names[i].c_str(),
                   feature_datatypes[i].c_str(), feature_optypes[i].c_str());
        }

        auto target_field_names     = model.get_target_field_names();
        auto target_field_datatypes = model.get_target_field_datatypes();
        auto target_field_optypes   = model.get_target_field_optypes();
        std::cout << "Target fields:" << std::endl;
        for (uint32_t i = 0; i < target_field_names.size(); i++) {
            printf("ind: %u, name: %s, datatype: %s, optype: %s\n", i, target_field_names[i].c_str(),
                   target_field_datatypes[i].c_str(), target_field_optypes[i].c_str());
        }

        auto output_field_names     = model.get_output_field_names();
        auto output_field_datatypes = model.get_output_field_datatypes();
        auto output_field_optypes   = model.get_output_field_optypes();
        std::cout << "Output fields:" << std::endl;
        for (uint32_t i = 0; i < output_field_names.size(); i++) {
            printf("ind: %u, name: %s, datatype: %s, optype: %s\n", i, output_field_names[i].c_str(),
                   output_field_datatypes[i].c_str(), output_field_optypes[i].c_str());
        }

        snapml::DenseDataset dummy_data(0, 0, nullptr, nullptr);
        if (model.compressed_tree() == false) {
            model.compress(dummy_data); // Optimize model for CPU inference
            if (model.compressed_tree() == false) {
                std::cout << "  SnapML tree model optimization failed" << std::endl;
            }
        }

        std::cout << "  Running inference " << std::endl;
        snapml::GenericTreeEnsemblePredictor predictor = snapml::GenericTreeEnsemblePredictor(model);

        std::vector<double> preds(test_data.get_num_ex());
        uint32_t            inference_threads = 4;

        predictor.predict(snapml_test_data, preds.data(), inference_threads);

        for (uint32_t i = 0; i < preds.size(); i++) {
            if (preds[i] < 0)
                preds[i] = 0;
            else
                preds[i] = 1;
        }

        uint32_t acc_preds = 0;
        for (uint32_t i = 0; i < preds.size(); i++) {
            acc_preds += (preds[i] == test_data.get_label(i));
        }

        double acc = acc_preds * 1.0 / test_data.get_num_ex();
        std::cout << "  Accuracy score " << acc << std::endl;
        assert(acc == 1.0);

        std::cout << std::endl;
    }

    return 0;
}
