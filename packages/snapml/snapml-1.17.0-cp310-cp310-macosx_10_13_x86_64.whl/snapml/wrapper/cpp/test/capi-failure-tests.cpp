#include "BoosterModel.hpp"
#include "RandomForestModel.hpp"
#include <iostream>
#include <cassert>

int main()
{
    snapml::BoosterModel model_boost;
    try {
        model_boost.import_model("../models/rf_model.pmml", "pmml");
    } catch (std::exception& e) {
        std::string expected = "Import expects an ensemble of boosting type.";
        assert(!expected.compare(e.what()));
    }

    snapml::RandomForestModel model_rf;
    try {
        model_rf.import_model("../models/xgb_model.json", "xgb_json", snapml::task_t::classification);
    } catch (std::exception& e) {
        std::string expected = "A random forest model can only be imported from PMML or ONNX format.";
        assert(!expected.compare(e.what()));
    }

    try {
        model_rf.import_model("../models/xgb_model.pmml", "pmml", snapml::task_t::classification);
    } catch (std::exception& e) {
        std::string expected = "Import expects an ensemble of random forest type.";
        assert(!expected.compare(e.what()));
    }

    return 0;
}
