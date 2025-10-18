/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2018
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Jan van Lunteren
 *
 * End Copyright
 ********************************************************************/

#ifndef MODELIMPORT
#define MODELIMPORT

#include <fstream>
#include <iomanip>
#include <stack>
#include <cmath>
#include <cassert>
#include <vector>
#include <cstring>
#include <algorithm>
#include <string>

namespace tree {

class ModelImport {

public:
    ModelImport(std::string filename, std::string file_type, snapml::ensemble_t ensemble_type)
    {
        input_filename_.assign(filename);
        input_file_.open(filename.c_str(), std::ios::binary);
        if (!input_file_.is_open())
            throw std::runtime_error("could not open file " + input_filename_);

        parsed_num_trees_ = 0;

        node_id_.resize(0);
        node_is_leaf_.resize(0);
        node_leaf_label_.resize(0);
        node_feature_.resize(0);
        node_threshold_.resize(0);
        node_left_child_.resize(0);
        node_right_child_.resize(0);

        if (file_type.compare(0, 4, "pmml") == 0) {
            parse_pmml();
            if (parsed_used_features_.size() == 0)
                throw std::runtime_error("no features could be parsed (might be due to non-supported format)");
        } else if (file_type.compare(0, 8, "lightgbm") == 0) {
            parse_lightGBM();
        } else if (false) { //(file_type.compare(0,7,"xgboost") == 0) {
            parse_XGBoost();
        } else if (file_type.compare(0, 8, "xgb_json") == 0) {
            parse_XGBoost_json();
        } else if (file_type.compare(0, 8, "cb_json") == 0) {
            parse_CatBoost_json();
        } else if (file_type.compare(0, 4, "onnx") == 0) {
            parse_onnx(ensemble_type);
        } else
            throw std::runtime_error("non-supported input file type");

        input_file_.close();

        // temp.
        new_node_leaf_label_.resize(0);
        for (uint32_t t = 0; t < node_is_leaf_.size(); t++) {
            new_node_leaf_label_.push_back(std::vector<std::vector<float>>());
            for (uint32_t i = 0; i < node_is_leaf_.at(t).size(); i++)
                new_node_leaf_label_.at(t).push_back(std::vector<float> { node_leaf_label_.at(t).at(i) });
        }
    }

    ~ModelImport() { }

    uint32_t const get_num_trees() const { return node_is_leaf_.size(); }

    uint32_t const get_num_nodes(uint32_t tree_id) const { return node_is_leaf_.at(tree_id).size(); }

    std::vector<uint32_t>* get_node_id(uint32_t tree_id) { return &node_id_.at(tree_id); }

    std::vector<bool>* get_node_is_leaf(uint32_t tree_id) { return &node_is_leaf_.at(tree_id); }

    std::vector<std::vector<float>>* get_node_leaf_label(uint32_t tree_id) { return &new_node_leaf_label_.at(tree_id); }

    std::vector<uint32_t>* get_node_feature(uint32_t tree_id) { return &node_feature_.at(tree_id); }

    std::vector<float>* get_node_threshold(uint32_t tree_id) { return &node_threshold_.at(tree_id); }

    std::vector<uint32_t>* get_node_left_child(uint32_t tree_id) { return &node_left_child_.at(tree_id); }

    std::vector<uint32_t>* get_node_right_child(uint32_t tree_id) { return &node_right_child_.at(tree_id); }

    double const get_base_score() const
    {

        if (parsed_base_score_valid_)
            return parsed_base_score_;
        else
            return 0.0; // CHECK: default value or throw error that base_score was not defined in input file
    }

    double const get_learning_rate() const
    {
        if (parsed_learning_rate_valid_)
            return parsed_learning_rate_;
        else
            return 1.0; // CHECK: default value or throw error that learning_rate was not defined in input file
    }

    uint32_t const get_node_comparison_type() const
    {
        if (parsed_node_comparison_type_valid_)
            return parsed_node_comparison_type_; // 0: less than, 1: less than or equal to
        else
            return 0;
    }

    uint32_t get_num_features() const { return parsed_num_features_; }
    bool     get_num_features_valid() const { return parsed_num_features_valid_; }

    std::vector<uint32_t> get_used_features() const { return parsed_used_features_; }

    void update_to_used_features_only() { update_to_used_features_only_impl(); }

    snapml::task_t get_model_type() const
    {
        return (parsed_model_type_ == 0 ? snapml::task_t::classification : snapml::task_t::regression);
    }
    bool get_model_type_valid() const { return parsed_model_type_valid_; }

    snapml::ensemble_t get_ensemble_type() const
    {
        return (parsed_ensemble_type_ == 0 ? snapml::ensemble_t::boosting : snapml::ensemble_t::forest);
    }
    bool get_ensemble_type_valid() const { return parsed_ensemble_type_valid_; }

    uint32_t get_num_classes() const { return parsed_num_classes_; }
    bool     get_num_classes_valid() const { return parsed_num_classes_valid_; }

    std::vector<float> get_class_labels() { return parsed_class_labels_; }
    bool               get_class_labels_valid() const { return parsed_num_classes_valid_; }

    std::vector<std::string> get_feature_names() { return feature_names_; }
    std::vector<std::string> get_feature_datatypes() { return feature_datatypes_; }
    std::vector<std::string> get_feature_optypes() { return feature_optypes_; }

    std::vector<std::string> get_target_field_names() { return target_field_names_; }
    std::vector<std::string> get_target_field_datatypes() { return target_field_datatypes_; }
    std::vector<std::string> get_target_field_optypes() { return target_field_optypes_; }

    std::vector<std::string> get_output_field_names() { return output_field_names_; }
    std::vector<std::string> get_output_field_datatypes() { return output_field_datatypes_; }
    std::vector<std::string> get_output_field_optypes() { return output_field_optypes_; }

private:
    void rec_extend_tree(uint32_t tree_index, uint32_t cur_node_index, uint32_t parent_node_index, uint32_t cur_depth,
                         uint32_t target_depth)
    {
        if (node_is_leaf_.at(tree_index).at(cur_node_index)) {
            if (cur_depth < target_depth) {
                node_id_.at(tree_index).push_back(static_cast<uint32_t>(node_id_.at(tree_index).size()));
                node_is_leaf_.at(tree_index).push_back(true);
                node_leaf_label_.at(tree_index).push_back(node_leaf_label_.at(tree_index).at(cur_node_index));
                node_feature_.at(tree_index).push_back(0);
                node_threshold_.at(tree_index).push_back(0.0);
                node_left_child_.at(tree_index).push_back(0);
                node_right_child_.at(tree_index).push_back(0);

                node_id_.at(tree_index).push_back(static_cast<uint32_t>(node_id_.at(tree_index).size()));
                node_is_leaf_.at(tree_index).push_back(true);
                node_leaf_label_.at(tree_index).push_back(node_leaf_label_.at(tree_index).at(cur_node_index));
                node_feature_.at(tree_index).push_back(0);
                node_threshold_.at(tree_index).push_back(0);
                node_left_child_.at(tree_index).push_back(0);
                node_right_child_.at(tree_index).push_back(0);

                node_is_leaf_.at(tree_index).at(cur_node_index)    = false;
                node_leaf_label_.at(tree_index).at(cur_node_index) = { 0.0 };
                node_feature_.at(tree_index).at(cur_node_index)
                    = ((cur_depth > 0) ? node_feature_.at(tree_index).at(parent_node_index) : 0);
                node_threshold_.at(tree_index).at(cur_node_index)
                    = ((cur_depth > 0) ? node_threshold_.at(tree_index).at(parent_node_index) : 0.0);
                node_left_child_.at(tree_index).at(cur_node_index)  = node_id_.at(tree_index).size() - 2;
                node_right_child_.at(tree_index).at(cur_node_index) = node_id_.at(tree_index).size() - 1;
            }
        }
        if (!node_is_leaf_.at(tree_index).at(cur_node_index)) {
            rec_extend_tree(tree_index, node_left_child_.at(tree_index).at(cur_node_index), cur_node_index,
                            cur_depth + 1, target_depth);
            rec_extend_tree(tree_index, node_right_child_.at(tree_index).at(cur_node_index), cur_node_index,
                            cur_depth + 1, target_depth);
        }
    }

    void rec_assign_nodeids(uint32_t tree_index, uint32_t cur_node_index, uint32_t new_node_id)
    {
        node_id_.at(tree_index).at(cur_node_index) = new_node_id;
        if (!node_is_leaf_.at(tree_index).at(cur_node_index)) {
            rec_assign_nodeids(tree_index, node_left_child_.at(tree_index).at(cur_node_index), 2 * new_node_id + 1);
            rec_assign_nodeids(tree_index, node_right_child_.at(tree_index).at(cur_node_index), 2 * new_node_id + 2);
        }
    }

    void remap_by_nodeids(uint32_t tree_index)
    {
        if (node_id_.at(tree_index).size() > 0) {
            std::vector<uint32_t> new_node_id(node_id_.at(tree_index));
            std::vector<bool>     new_node_is_leaf(node_is_leaf_.at(tree_index));
            std::vector<float>    new_node_leaf_label(node_leaf_label_.at(tree_index));
            std::vector<uint32_t> new_node_feature(node_feature_.at(tree_index));
            std::vector<float>    new_node_threshold(node_threshold_.at(tree_index));
            std::vector<uint32_t> new_node_left_child(node_left_child_.at(tree_index));
            std::vector<uint32_t> new_node_right_child(node_right_child_.at(tree_index));

            for (uint32_t i = 0; i < node_id_.at(tree_index).size(); i++) {
                uint32_t j                             = new_node_id.at(i);
                node_id_.at(tree_index).at(j)          = j;
                node_is_leaf_.at(tree_index).at(j)     = new_node_is_leaf.at(i);
                node_leaf_label_.at(tree_index).at(j)  = new_node_leaf_label.at(i);
                node_feature_.at(tree_index).at(j)     = new_node_feature.at(i);
                node_threshold_.at(tree_index).at(j)   = new_node_threshold.at(i);
                node_left_child_.at(tree_index).at(j)  = new_node_id.at(new_node_left_child.at(i));
                node_right_child_.at(tree_index).at(j) = new_node_id.at(new_node_right_child.at(i));
            }
        }
    }

    /*=================================================================================================================*/
    /* PMML import */
    /*=================================================================================================================*/
    void connect_nodes()
    {
        if (cur_tree_node_is_leaf_.size() == 2) {
            assert(cur_tree_node_is_leaf_.at(0) && cur_tree_node_is_leaf_.at(1));

            cur_tree_node_tag_level_.erase(cur_tree_node_tag_level_.begin());
            cur_tree_node_id_.erase(cur_tree_node_id_.begin());
            cur_tree_node_is_leaf_.erase(cur_tree_node_is_leaf_.begin());
            cur_tree_node_leaf_label_.erase(cur_tree_node_leaf_label_.begin());
            cur_tree_node_feature_.erase(cur_tree_node_feature_.begin());
            cur_tree_node_threshold_.erase(cur_tree_node_threshold_.begin());
            cur_tree_node_left_child_.erase(cur_tree_node_left_child_.begin());
            cur_tree_node_right_child_.erase(cur_tree_node_right_child_.begin());
        } else {

            // determine split (non-leaf) nodes
            std::vector<uint32_t> split_node_indices;
            std::vector<bool>     leaf_node_linked_to_parent;
            for (uint32_t i = 0; i < cur_tree_node_is_leaf_.size(); i++) {
                if (!cur_tree_node_is_leaf_.at(i)) {
                    split_node_indices.push_back(i);
                    leaf_node_linked_to_parent.push_back(false);
                } else
                    leaf_node_linked_to_parent.push_back(false);
            }

            // search for and update parent node of each split node
            for (uint32_t i = 1; i < split_node_indices.size(); i++) {
                if (cur_tree_node_tag_level_[split_node_indices.at(i)]
                    == (cur_tree_node_tag_level_[split_node_indices.at(i - 1)] + 1))
                    cur_tree_node_left_child_[split_node_indices.at(i - 1)] = split_node_indices.at(i);
                else {
                    uint32_t j = i - 1;
                    while (cur_tree_node_tag_level_[split_node_indices.at(i)]
                           != cur_tree_node_tag_level_[split_node_indices.at(j)])
                        j--;
                    cur_tree_node_right_child_[split_node_indices.at(j)] = split_node_indices.at(i);
                }
            }

            // update left child pointers in split nodes that have not been assigned
            for (uint32_t i = 0; i < split_node_indices.size(); i++) {
                if (cur_tree_node_left_child_[split_node_indices.at(i)] == 0xFFFFFFFF) {
                    //                assert(cur_tree_node_is_leaf_.at(split_node_indices.at(i) - 1));
                    //                assert((cur_tree_node_tag_level_.at(split_node_indices.at(i) - 1) + 1)
                    if ((!cur_tree_node_is_leaf_.at(split_node_indices.at(i) - 1))
                        || ((cur_tree_node_tag_level_.at(split_node_indices.at(i) - 1) + 1)
                            != (cur_tree_node_tag_level_.at(split_node_indices.at(i)))))
                        throw std::runtime_error("error occurred when trying to interconnect tree nodes imported from "
                                                 + input_filename_);

                    cur_tree_node_left_child_[split_node_indices.at(i)]         = split_node_indices.at(i) - 1;
                    leaf_node_linked_to_parent.at(split_node_indices.at(i) - 1) = true;
                }
            }

            // update right child pointers in split nodes that have not been assigned
            for (uint32_t i = 0; i < split_node_indices.size(); i++) {
                if (cur_tree_node_right_child_[split_node_indices.at(i)] == 0xFFFFFFFF) {
                    uint32_t j = split_node_indices.at(i) + 1;
                    if ((j < cur_tree_node_is_leaf_.size()) && cur_tree_node_is_leaf_.at(j)
                        && (((j + 1) == cur_tree_node_is_leaf_.size()) || (cur_tree_node_is_leaf_.at(j + 1)))) {
                        //                    assert((cur_tree_node_tag_level_.at(j) + 1) ==
                        //                    cur_tree_node_tag_level_.at(split_node_indices.at(i)));
                        if ((cur_tree_node_tag_level_.at(j) + 1)
                            != cur_tree_node_tag_level_.at(split_node_indices.at(i)))
                            throw std::runtime_error(
                                "error occurred when trying to interconnect tree nodes imported from "
                                + input_filename_);
                        cur_tree_node_right_child_[split_node_indices.at(i)] = j;
                        leaf_node_linked_to_parent.at(j)                     = true;
                    } else {
                        uint32_t j = split_node_indices.at(i) - 1;
                        while (!(cur_tree_node_is_leaf_.at(j)
                                 && ((cur_tree_node_tag_level_.at(j) + 2)
                                     == cur_tree_node_tag_level_.at(split_node_indices.at(i)))))
                            j--;
                        //                    assert(cur_tree_node_is_leaf_.at(j) && ((cur_tree_node_tag_level_.at(j) +
                        //                    2)
                        //                    == cur_tree_node_tag_level_.at(split_node_indices.at(i))));
                        //                    assert(!leaf_node_linked_to_parent.at(j));
                        if ((cur_tree_node_is_leaf_.at(j)
                             && ((cur_tree_node_tag_level_.at(j) + 2)
                                 != cur_tree_node_tag_level_.at(split_node_indices.at(i))))
                            || leaf_node_linked_to_parent.at(j))
                            throw std::runtime_error(
                                "error occurred when trying to interconnect tree nodes imported from "
                                + input_filename_);
                        cur_tree_node_right_child_[split_node_indices.at(i)] = j;
                        leaf_node_linked_to_parent.at(j)                     = true;
                    }
                }
            }

            // swap left and right child pointer in split nodes that involve greaterThan or greaterOrEqual comparisons
            for (uint32_t i = 0; i < split_node_indices.size(); i++) {
                if (!cur_tree_node_less_than_[split_node_indices.at(i)]) {
                    uint32_t swap_val = cur_tree_node_left_child_[split_node_indices.at(i)];
                    cur_tree_node_left_child_[split_node_indices.at(i)]
                        = cur_tree_node_right_child_[split_node_indices.at(i)];
                    cur_tree_node_right_child_[split_node_indices.at(i)] = swap_val;
                }
            }
            std::vector<uint32_t> new_cur_tree_node_tag_level_;
            std::vector<uint32_t> new_cur_tree_node_id_;
            std::vector<bool>     new_cur_tree_node_is_leaf_;
            std::vector<float>    new_cur_tree_node_leaf_label_;
            std::vector<uint32_t> new_cur_tree_node_feature_;
            std::vector<float>    new_cur_tree_node_threshold_;
            std::vector<uint32_t> new_cur_tree_node_left_child_;
            std::vector<uint32_t> new_cur_tree_node_right_child_;

            std::vector<uint32_t> mapping(cur_tree_node_is_leaf_.size());

            for (uint32_t i = 0; i < split_node_indices.size(); i++) {
                new_cur_tree_node_tag_level_.push_back(cur_tree_node_tag_level_.at(split_node_indices.at(i)));
                new_cur_tree_node_id_.push_back(cur_tree_node_id_.at(split_node_indices.at(i)));
                new_cur_tree_node_is_leaf_.push_back(cur_tree_node_is_leaf_.at(split_node_indices.at(i)));
                new_cur_tree_node_leaf_label_.push_back(cur_tree_node_leaf_label_.at(split_node_indices.at(i)));
                new_cur_tree_node_feature_.push_back(cur_tree_node_feature_.at(split_node_indices.at(i)));
                new_cur_tree_node_threshold_.push_back(cur_tree_node_threshold_.at(split_node_indices.at(i)));
                new_cur_tree_node_left_child_.push_back(cur_tree_node_left_child_.at(split_node_indices.at(i)));
                new_cur_tree_node_right_child_.push_back(cur_tree_node_right_child_.at(split_node_indices.at(i)));

                mapping.at(split_node_indices.at(i)) = i;
            }

            uint32_t j = split_node_indices.size();
            for (uint32_t i = 0; i < cur_tree_node_is_leaf_.size(); i++) {
                if ((cur_tree_node_is_leaf_.at(i)) && leaf_node_linked_to_parent.at(i)) {
                    new_cur_tree_node_tag_level_.push_back(cur_tree_node_tag_level_.at(i));
                    new_cur_tree_node_id_.push_back(cur_tree_node_id_.at(i));
                    new_cur_tree_node_is_leaf_.push_back(cur_tree_node_is_leaf_.at(i));
                    new_cur_tree_node_leaf_label_.push_back(cur_tree_node_leaf_label_.at(i));
                    new_cur_tree_node_feature_.push_back(cur_tree_node_feature_.at(i));
                    new_cur_tree_node_threshold_.push_back(cur_tree_node_threshold_.at(i));
                    new_cur_tree_node_left_child_.push_back(cur_tree_node_left_child_.at(i));
                    new_cur_tree_node_right_child_.push_back(cur_tree_node_right_child_.at(i));

                    mapping.at(i) = j;
                    j++;
                }
            }

            for (uint32_t i = 0; i < new_cur_tree_node_is_leaf_.size(); i++) {
                if (!new_cur_tree_node_is_leaf_.at(i)) {
                    new_cur_tree_node_left_child_.at(i)  = mapping.at(new_cur_tree_node_left_child_.at(i));
                    new_cur_tree_node_right_child_.at(i) = mapping.at(new_cur_tree_node_right_child_.at(i));
                }
            }

            cur_tree_node_tag_level_.swap(new_cur_tree_node_tag_level_);
            cur_tree_node_id_.swap(new_cur_tree_node_id_);
            cur_tree_node_is_leaf_.swap(new_cur_tree_node_is_leaf_);
            cur_tree_node_leaf_label_.swap(new_cur_tree_node_leaf_label_);
            cur_tree_node_feature_.swap(new_cur_tree_node_feature_);
            cur_tree_node_threshold_.swap(new_cur_tree_node_threshold_);
            cur_tree_node_left_child_.swap(new_cur_tree_node_left_child_);
            cur_tree_node_right_child_.swap(new_cur_tree_node_right_child_);
        }
    }

    int32_t find_attribute(std::vector<std::string> attribute_names, std::string attrib)
    {
        int32_t ret_val = -1;

        std::vector<std::string>::iterator it = std::find(attribute_names.begin(), attribute_names.end(), attrib);
        if (it != attribute_names.end())
            ret_val = std::distance(attribute_names.begin(), it);

        return ret_val;
    }

    const std::vector<std::string> algorithm_names_GB
        = { "XGBoost", "XGBoost (GBTree)", "LightGBM", "Snap ML Boosting" };
    const std::vector<std::string> algorithm_names_RF = { "sklearn.ensemble.forest.RandomForestClassifier",
                                                          "sklearn.ensemble.forest.RandomForestRegressor",
                                                          "sklearn.ensemble.forest.ExtraTreesClassifier",
                                                          "sklearn.ensemble.forest.ExtraTreesRegressor",
                                                          "sklearn.ensemble._forest.RandomForestClassifier",
                                                          "sklearn.ensemble._forest.RandomForestRegressor",
                                                          "sklearn.ensemble._forest.ExtraTreesClassifier",
                                                          "sklearn.ensemble._forest.ExtraTreesRegressor",
                                                          "Snap ML Forest" };

    void process_pmml(std::string tag_name, std::vector<std::string> attribute_names,
                      std::vector<std::string> attribute_values, uint32_t tag_level, uint8_t tag_type, uint32_t lineNr)
    {
        if (tag_level == 0) {
            if (tag_type == 0) {
                if (tag_name.compare("PMML") != 0)
                    throw std::runtime_error("root element does not equal PMML in line " + std::to_string(lineNr)
                                             + " in " + input_filename_);
                int32_t attrib_index = find_attribute(attribute_names, "version");
                if (attrib_index == -1)
                    throw std::runtime_error("no PMML version defined for PMML  element in line "
                                             + std::to_string(lineNr) + " in " + input_filename_);
                parsed_pmml_version_ = std::stof(attribute_values.at(attrib_index));
            } else {
                if ((tag_type != 2) || (tag_name.compare("PMML") != 0))
                    throw std::runtime_error("no end tag for root element PMML in line " + std::to_string(lineNr)
                                             + " in " + input_filename_);

                /*
                if (leaf_label_based_on_rcount_) {
                    for (uint32_t t = 0; t < node_is_leaf_.size(); t++) {
                        for (uint32_t i = 0; i < node_is_leaf_.at(t).size(); i++) {
                            if (node_is_leaf_.at(t).at(i))
                                node_leaf_label_.at(t).at(i) = node_leaf_label_.at(t).at(i) / node_is_leaf_.size();
                        }
                    }
                }
                */
            }
        }
        if (tag_name.compare("DataField") == 0) {
            if (tag_type == 2)
                counting_num_classes_ = false;
            else {
                int32_t attrib_index = find_attribute(attribute_names, "name");
                if (attrib_index == -1)
                    throw std::runtime_error("no name attribute defined for DataField element in line "
                                             + std::to_string(lineNr) + " in " + input_filename_);
                feature_names_.push_back(attribute_values.at(attrib_index));

                attrib_index = find_attribute(attribute_names, "optype");
                if (attrib_index == -1)
                    throw std::runtime_error("no optype attribute defined for DataField element in line "
                                             + std::to_string(lineNr) + " in " + input_filename_);
                feature_optypes_.push_back(attribute_values.at(attrib_index));

                attrib_index = find_attribute(attribute_names, "dataType");
                if (attrib_index == -1)
                    throw std::runtime_error("no dataType attribute defined for DataField element in line "
                                             + std::to_string(lineNr) + " in " + input_filename_);
                feature_datatypes_.push_back(attribute_values.at(attrib_index));

                if (tag_type == 0) {
                    if (feature_names_.back().compare("y") == 0) {
                        if (feature_optypes_.back().compare("categorical") == 0) {
                            counting_num_classes_     = true;
                            parsed_num_classes_       = 0;
                            parsed_num_classes_valid_ = true;
                            parsed_class_labels_.resize(0);
                        }
                    }
                    if ((feature_datatypes_.back().compare("integer") != 0)
                        && (feature_datatypes_.back().compare("float") != 0)
                        && (feature_datatypes_.back().compare("double") != 0))
                        throw std::runtime_error("non-supported value for dataType attribute in line "
                                                 + std::to_string(lineNr) + " in " + input_filename_);
                }
            }
        } else if (counting_num_classes_ && (tag_name.compare("Value") == 0)) {
            int32_t attrib_index = find_attribute(attribute_names, "value");
            if (attrib_index == -1)
                throw std::runtime_error("no value attribute defined for Value element in line "
                                         + std::to_string(lineNr) + " in " + input_filename_);
            parsed_class_labels_.push_back(std::stof(attribute_values.at(attrib_index)));
            parsed_num_classes_++;
        } else if ((tag_type == 2) && (tag_name.compare("DataDictionary") == 0)) {
            if (feature_names_.size() == 0)
                throw std::runtime_error("no features defined in " + input_filename_);

            target_field_names_.push_back(feature_names_.at(0));
            target_field_optypes_.push_back(feature_optypes_.at(0));
            target_field_datatypes_.push_back(feature_datatypes_.at(0));

            feature_names_.erase(feature_names_.begin()); // remove first entry ('target')
            feature_optypes_.erase(feature_optypes_.begin());
            feature_datatypes_.erase(feature_datatypes_.begin());

            // determine feature specification type: indices or names
            feature_index_format_ = true;
            for (uint32_t i = 0; i < feature_names_.size(); i++) {
                if ((feature_names_.at(i).size() < 2) || (feature_names_.at(i).at(0) != 'x')) {
                    feature_index_format_ = false;
                    break;
                } else {
                    bool onlyDigits = true;
                    for (uint32_t j = 1; j < feature_names_.at(i).size(); j++) {
                        if ((feature_names_.at(i).at(j) < '0') || (feature_names_.at(i).at(j) > '9')) {
                            onlyDigits = false;
                            break;
                        }
                    }
                    if (!onlyDigits) {
                        feature_index_format_ = false;
                        break;
                    }
                }
            }
            if (feature_index_format_) {
                for (uint32_t i = 0; i < feature_names_.size(); i++) {
                    uint32_t name_length = feature_names_.at(i).size();
                    if ((name_length > 7) && (feature_names_.at(i).substr(0, 7).compare("double(") == 0))
                        parsed_used_features_.push_back(std::stoi(feature_names_.at(i).substr(8, name_length - 1)) - 1);
                    else
                        parsed_used_features_.push_back(std::stoi(feature_names_.at(i).substr(1)) - 1);
                }
            }
        } else if ((tag_type == 0) && (tag_name.compare("Segment") == 0)) {
            int32_t attrib_index = find_attribute(attribute_names, "id");
            if (attrib_index == -1)
                throw std::runtime_error("no id attribute defined for Segment element in line " + std::to_string(lineNr)
                                         + " in " + input_filename_);
            cur_tree_id_ = std::stoi(attribute_values.at(attrib_index));
        } else if (tag_name.compare("TreeModel") == 0) {
            if (tag_type == 0) {
                if (cur_tree_id_ > parsed_num_trees_)
                    parsed_num_trees_ = cur_tree_id_; // cur_tree_id_ starts with 1
                int32_t attrib_index = find_attribute(attribute_names, "functionName");
                if (attrib_index == -1)
                    throw std::runtime_error("no functionName attribute defined for TreeModel element in line "
                                             + std::to_string(lineNr) + " in " + input_filename_);
                if (attribute_values.at(attrib_index).compare("regression") == 0) {
                    if (cur_tree_id_ == 1)
                        parsed_tree_type_ = 1;
                    else {
                        if (parsed_tree_type_ != 1)
                            throw std::runtime_error("tree model has different type than previous tree models in line "
                                                     + std::to_string(lineNr) + " in " + input_filename_);
                    }
                } else if (attribute_values.at(attrib_index).compare("classification") == 0) {
                    if (cur_tree_id_ == 1)
                        parsed_tree_type_ = 0;
                    else {
                        if (parsed_tree_type_ != 0)
                            throw std::runtime_error("tree model has different type than previous tree models in line "
                                                     + std::to_string(lineNr) + " in " + input_filename_);
                    }
                } else
                    throw std::runtime_error("unknown value for functionName attribute in line "
                                             + std::to_string(lineNr) + " in " + input_filename_);

                attrib_index = find_attribute(attribute_names, "missingValueStrategy");
                if (attrib_index == -1)
                    parsed_missing_value_strategy_ = none;
                else {
                    if (attribute_values.at(attrib_index).compare("lastPrediction") == 0)
                        parsed_missing_value_strategy_ = lastPrediction;
                    else if (attribute_values.at(attrib_index).compare("nullPrediction") == 0)
                        parsed_missing_value_strategy_ = nullPrediction;
                    else if (attribute_values.at(attrib_index).compare("defaultChild") == 0)
                        parsed_missing_value_strategy_ = defaultChild;
                    else if (attribute_values.at(attrib_index).compare("weightedConfidence") == 0)
                        parsed_missing_value_strategy_ = weightedConfidence;
                    else if (attribute_values.at(attrib_index).compare("aggregateNodes") == 0)
                        parsed_missing_value_strategy_ = aggregateNodes;
                    else if (attribute_values.at(attrib_index).compare("none") == 0)
                        parsed_missing_value_strategy_ = none;
                }
                // if ((parsed_missing_value_strategy_ != none) && (parsed_missing_value_strategy_ != defaultChild))
                //    throw std::runtime_error("non-supported value for missingValueStrategy attribute in line " +
                //    std::to_string(lineNr) + " in " + input_filename_);

                // new tree
                cur_tree_node_count_ = 0;

                cur_tree_node_tag_level_.resize(0);
                cur_tree_node_id_.resize(0);
                cur_tree_node_is_leaf_.resize(0);
                cur_tree_node_leaf_label_.resize(0);
                cur_tree_node_feature_.resize(0);
                cur_tree_node_threshold_.resize(0);
                cur_tree_node_less_than_.resize(0);
                cur_tree_node_left_child_.resize(0);
                cur_tree_node_right_child_.resize(0);

            } else if (tag_type == 2) {
                connect_nodes();

                // replace original node id's by consecutive numbers
                cur_tree_node_id_.resize(0);
                for (uint32_t i = 0; i < cur_tree_node_is_leaf_.size(); i++)
                    cur_tree_node_id_.push_back(i);

                node_id_.push_back(cur_tree_node_id_);
                node_is_leaf_.push_back(cur_tree_node_is_leaf_);
                node_leaf_label_.push_back(cur_tree_node_leaf_label_);
                node_feature_.push_back(cur_tree_node_feature_);
                node_threshold_.push_back(cur_tree_node_threshold_);
                node_left_child_.push_back(cur_tree_node_left_child_);
                node_right_child_.push_back(cur_tree_node_right_child_);
            }
        } else if ((tag_type == 0) && (tag_name.compare("Node") == 0)) {

            int32_t attrib_index = find_attribute(attribute_names, "id");
            if (attrib_index != -1)
                cur_tree_node_id_.push_back(std::stoi(attribute_values.at(attrib_index)));
            else
                cur_tree_node_id_.push_back(0);

            attrib_index = find_attribute(attribute_names, "score");
            if (attrib_index != -1)
                cur_tree_node_leaf_label_.push_back(std::stof(attribute_values.at(attrib_index)));
            else {
                last_parsed_empty_node_index_.push_back(cur_tree_node_count_);
                cur_tree_node_leaf_label_.push_back(NAN);
            }

            attrib_index = find_attribute(attribute_names, "recordCount");
            if (attrib_index != -1) {
                cur_parsed_node_index_ = cur_tree_node_count_;
                cur_parsed_tot_rcount_ = std::stod(attribute_values.at(attrib_index));
                cur_parsed_rcount_.resize(0);
            }

            cur_tree_node_tag_level_.push_back(tag_level);
            cur_tree_node_is_leaf_.push_back(true);
            cur_tree_node_feature_.push_back(0);
            cur_tree_node_threshold_.push_back(0.0);
            cur_tree_node_less_than_.push_back(true);
            cur_tree_node_left_child_.push_back(0);
            cur_tree_node_right_child_.push_back(0);

            cur_tree_node_count_++;
        } else if ((tag_type == 1) && (tag_name.compare("SimplePredicate") == 0)) {
            cur_parsed_predicate_is_true_ = false;
            cur_tree_node_id_.push_back(0);
            int32_t attrib_index_field = find_attribute(attribute_names, "field");
            if (attrib_index_field == -1)
                throw std::runtime_error("no field attribute defined for SimplePredicate element in line "
                                         + std::to_string(lineNr) + " in " + input_filename_);

            int32_t attrib_index_operator = find_attribute(attribute_names, "operator");
            if (attrib_index_operator == -1)
                throw std::runtime_error("no operator attribute defined for SimplePredicate element in line "
                                         + std::to_string(lineNr) + " in " + input_filename_);

            int32_t attrib_index_value = find_attribute(attribute_names, "value");
            if (attrib_index_value == -1)
                throw std::runtime_error("no value attribute defined for SimplePredicate element in line "
                                         + std::to_string(lineNr) + " in " + input_filename_);

            if ((attribute_values.at(attrib_index_operator).compare("lessThan") == 0)
                || (attribute_values.at(attrib_index_operator).compare("lessOrEqual") == 0)) {
                cur_tree_node_less_than_.push_back(true);
                if (!parsed_node_comparison_type_valid_) {
                    if (attribute_values.at(attrib_index_operator).compare("lessThan") == 0)
                        parsed_node_comparison_type_ = 0;
                    else
                        parsed_node_comparison_type_ = 1;
                    parsed_node_comparison_type_valid_ = true;
                } else {
                    if (((attribute_values.at(attrib_index_operator).compare("lessThan") == 0)
                         && (parsed_node_comparison_type_ != 0))
                        || ((attribute_values.at(attrib_index_operator).compare("lessOrEqual") == 0)
                            && (parsed_node_comparison_type_ != 1)))
                        throw std::runtime_error("mixed less-than and less-than-or-equal-to node comparisons in "
                                                 + input_filename_);
                }
            } else {
                if ((attribute_values.at(attrib_index_operator).compare("greaterThan") != 0)
                    && (attribute_values.at(attrib_index_operator).compare("greaterOrEqual") != 0))
                    throw std::runtime_error("non-supported operator value in line " + std::to_string(lineNr) + " in "
                                             + input_filename_);
                cur_tree_node_less_than_.push_back(false);
                if (!parsed_node_comparison_type_valid_) {
                    if (attribute_values.at(attrib_index_operator).compare("greaterThan") == 0)
                        parsed_node_comparison_type_ = 1;
                    else
                        parsed_node_comparison_type_ = 0;
                    parsed_node_comparison_type_valid_ = true;
                } else {
                    if (((attribute_values.at(attrib_index_operator).compare("greaterThan") == 0)
                         && (parsed_node_comparison_type_ != 1))
                        || ((attribute_values.at(attrib_index_operator).compare("greaterOrEqual") == 0)
                            && (parsed_node_comparison_type_ != 0)))
                        throw std::runtime_error("mixed greater-than and greater-than-or-equal-to node comparisons in "
                                                 + input_filename_);
                }
            }

            cur_tree_node_tag_level_.push_back(tag_level);
            cur_tree_node_is_leaf_.push_back(false);

            if (feature_index_format_) {
                uint32_t attrib_length = attribute_values.at(attrib_index_field).size();
                if ((attrib_length > 13)
                    && (attribute_values.at(attrib_index_field).substr(0, 13).compare("double(float(") == 0))
                    cur_tree_node_feature_.push_back(
                        std::stoi(attribute_values.at(attrib_index_field).substr(14, attrib_length - 1)) - 1);
                else {
                    if ((attrib_length > 7)
                        && (attribute_values.at(attrib_index_field).substr(0, 7).compare("double(") == 0))
                        cur_tree_node_feature_.push_back(
                            std::stoi(attribute_values.at(attrib_index_field).substr(8, attrib_length - 1)) - 1);
                    else
                        cur_tree_node_feature_.push_back(std::stoi(attribute_values.at(attrib_index_field).substr(1))
                                                         - 1);
                }
            } else {
                bool feature_found = false;
                for (uint32_t i = 0; i < feature_names_.size(); i++) {
                    if (feature_names_.at(i).compare(attribute_values.at(attrib_index_field)) == 0) {
                        cur_tree_node_feature_.push_back(i);
                        feature_found = true;
                        break;
                    }
                }
                if (!feature_found)
                    throw std::runtime_error("undefined feature used at line " + std::to_string(lineNr) + " in "
                                             + input_filename_);
            }
            cur_tree_node_threshold_.push_back(std::stof(attribute_values.at(attrib_index_value)));
            cur_tree_node_left_child_.push_back(0xFFFFFFFF);
            cur_tree_node_right_child_.push_back(0xFFFFFFFF);
            cur_tree_node_leaf_label_.push_back(static_cast<float>(parsed_node_comparison_type_));

            cur_tree_node_count_++;
        } else if ((tag_type == 1) && (tag_name.compare("ScoreDistribution") == 0)) {
            if (parsed_model_type_ != 0)
                throw std::runtime_error("ScoreDistribution element found in non-classification model in line "
                                         + std::to_string(lineNr) + " in " + input_filename_);

            int32_t attrib_index_value = find_attribute(attribute_names, "value");
            if (attrib_index_value == -1)
                throw std::runtime_error("no value attribute defined for ScoreDistribution element in line "
                                         + std::to_string(lineNr) + " in " + input_filename_);

            /*
            if ((std::stoi(attribute_values.at(attrib_index_value)) != cur_parsed_rcount_.size())
                || (std::stoi(attribute_values.at(attrib_index_value)) >= parsed_num_classes_))
                throw std::runtime_error(
                    "unexpected value or number of value attributes defined for ScoreDistribution element in line "
                    + std::to_string(lineNr) + " in " + input_filename_);
            */

            int32_t attrib_index_record_count = find_attribute(attribute_names, "recordCount");
            if (attrib_index_record_count == -1)
                throw std::runtime_error("no recordCount attribute defined for ScoreDistribution element in line "
                                         + std::to_string(lineNr) + " in " + input_filename_);
            cur_parsed_rcount_.push_back(std::stod(attribute_values.at(attrib_index_record_count)));

            if (cur_parsed_rcount_.size() == parsed_num_classes_) {
                double rcount_sum = 0;
                for (uint32_t i = 0; i < cur_parsed_rcount_.size(); i++)
                    rcount_sum += cur_parsed_rcount_.at(i);
                if (std::fabs(rcount_sum - cur_parsed_tot_rcount_)
                    > cur_parsed_tot_rcount_ / static_cast<double>(1000.0))
                    throw std::runtime_error(
                        "sum of recordCount attribute values defined for ScoreDistribution elements in line "
                        + std::to_string(lineNr) + " does not match recordCount of corresponding Node element in "
                        + input_filename_);
                cur_tree_node_leaf_label_[cur_parsed_node_index_]
                    = static_cast<float>(cur_parsed_rcount_.at(cur_parsed_rcount_.size() - 1) / cur_parsed_tot_rcount_);
                leaf_label_based_on_rcount_ = true;

                if (cur_parsed_predicate_is_true_ && (last_parsed_empty_node_index_.size() > 0)) {
                    uint32_t last_empty_node_index = last_parsed_empty_node_index_.back();
                    last_parsed_empty_node_index_.pop_back();
                    if (!cur_tree_node_is_leaf_[last_empty_node_index])
                        throw std::runtime_error("derived class probability in line " + std::to_string(lineNr)
                                                 + " cannot be assigned to corresponding tree node in "
                                                 + input_filename_);
                    cur_tree_node_leaf_label_[last_empty_node_index]
                        = cur_tree_node_leaf_label_[cur_parsed_node_index_];
                }
            }
        } else if ((tag_type == 1) && (tag_name.compare("True") == 0)) {
            cur_parsed_predicate_is_true_ = true;
        } else if (((tag_type == 0) || (tag_type == 1)) && (tag_name.compare("Target") == 0)) {

            int32_t attrib_index = find_attribute(attribute_names, "rescaleConstant");
            if (attrib_index != -1) {
                parsed_rescale_constant_       = std::stof(attribute_values.at(attrib_index));
                parsed_rescale_constant_valid_ = true;
            }
        } else if (tag_name.compare("MiningModel") == 0) {
            if (tag_type == 0) {
                int32_t attrib_index = find_attribute(attribute_names, "functionName");
                if (attrib_index == -1)
                    throw std::runtime_error("no functionName attribute defined for MiningModel element in line "
                                             + std::to_string(lineNr) + " in " + input_filename_);

                // only parse the first MiningModel tag
                if (!parsed_model_type_valid_) {
                    if (attribute_values.at(attrib_index).compare("regression") == 0) {
                        parsed_model_type_       = 1;
                        parsed_model_type_valid_ = true;
                    } else if (attribute_values.at(attrib_index).compare("classification") == 0) {
                        parsed_model_type_       = 0;
                        parsed_model_type_valid_ = true;
                    } else
                        throw std::runtime_error("non-supported value defined for functionName attribute in line "
                                                 + std::to_string(lineNr) + " in " + input_filename_);

                    attrib_index = find_attribute(attribute_names, "algorithmName");
                    if (attrib_index == -1)
                        throw std::runtime_error("no algorithmName attribute defined for MiningModel element in line "
                                                 + std::to_string(lineNr) + " in " + input_filename_);

                    bool algorithm_found = false;
                    for (uint32_t i = 0; !algorithm_found && (i < algorithm_names_GB.size()); i++) {
                        if (attribute_values.at(attrib_index).compare(algorithm_names_GB.at(i)) == 0) {
                            parsed_ensemble_type_       = 0;
                            parsed_ensemble_type_valid_ = true;
                            algorithm_found             = true;
                        }
                    }
                    for (uint32_t i = 0; !algorithm_found && (i < algorithm_names_RF.size()); i++) {
                        if (attribute_values.at(attrib_index).compare(algorithm_names_RF.at(i)) == 0) {
                            parsed_ensemble_type_       = 1;
                            parsed_ensemble_type_valid_ = true;
                            algorithm_found             = true;
                        }
                    }
                    if (!algorithm_found)
                        throw std::runtime_error("non-supported value defined for algorithmName attribute in line "
                                                 + std::to_string(lineNr) + " in " + input_filename_);
                }
            }
        } else if (tag_name.compare("LocalTransformations") == 0) {
            if (tag_type == 0)
                parsing_local_transformations_ = true;
            else if (tag_type == 2)
                parsing_local_transformations_ = false;
        } else if (tag_name.compare("Apply") == 0) {
            if ((tag_type == 0) || (tag_type == 1)) {
                if (!parsing_local_transformations_)
                    throw std::runtime_error(
                        "non-supported Apply attribute outside LocalTransformations section in line "
                        + std::to_string(lineNr) + " in " + input_filename_);

                throw std::runtime_error("non-supported Apply attribute inside LocalTransformations section in line "
                                         + std::to_string(lineNr) + " in " + input_filename_);
            }
        } else if ((tag_type == 1) && (tag_name.compare("OutputField") == 0)) {
            int32_t attrib_index = find_attribute(attribute_names, "name");
            if (attrib_index == -1)
                throw std::runtime_error("no name attribute defined for OutputField element in line "
                                         + std::to_string(lineNr) + " in " + input_filename_);

            if (attribute_values.at(attrib_index).compare("xgbValue") != 0) {
                output_field_names_.push_back(attribute_values.at(attrib_index));

                attrib_index = find_attribute(attribute_names, "optype");
                if (attrib_index == -1)
                    throw std::runtime_error("no optype attribute defined for OutputField element in line "
                                             + std::to_string(lineNr) + " in " + input_filename_);
                output_field_optypes_.push_back(attribute_values.at(attrib_index));

                attrib_index = find_attribute(attribute_names, "dataType");
                if (attrib_index == -1)
                    throw std::runtime_error("no dataType attribute defined for OutputField element in line "
                                             + std::to_string(lineNr) + " in " + input_filename_);
                output_field_datatypes_.push_back(attribute_values.at(attrib_index));
            }
        }
    }

    void parse_pmml()
    {

        std::stack<std::string> tag_stack;
        std::string             inputLine;
        uint32_t                lineNr    = 0;
        uint32_t                cur_level = 0;

        leaf_label_based_on_rcount_ = false;

        while (std::getline(input_file_, inputLine)) {
            lineNr++;
            while (inputLine.size() > 0) {
                while ((inputLine.at(0) == '\t') || (inputLine.at(0) == ' ')) // remove whitespace
                    inputLine.erase(0, 1);

                if (inputLine.at(0) == '<') {
                    inputLine.erase(0, 1);

                    if (inputLine.at(0) == '?') { // XML declaration
                        // ignore XML declaration for now
                    } else if (inputLine.at(0) == '/') { // end tag
                        inputLine.erase(0, 1);
                        std::size_t match_pos = inputLine.find_first_of(" />\t");
                        if (match_pos == std::string::npos)
                            throw std::runtime_error("malformed end tag at line " + std::to_string(lineNr) + " in "
                                                     + input_filename_);

                        std::string tag_name = inputLine.substr(0, match_pos);
                        inputLine.erase(0, match_pos);
                        if (tag_name.compare(tag_stack.top()) != 0)
                            throw std::runtime_error("mismatched end tag at line " + std::to_string(lineNr) + " in "
                                                     + input_filename_);
                        tag_stack.pop();
                        cur_level--;
                        std::vector<std::string> empty_vector;
                        process_pmml(tag_name, empty_vector, empty_vector, cur_level, 2, lineNr);
                    } else { // start tag or empty element
                        std::size_t match_pos = inputLine.find_first_of(" />\t");
                        if (match_pos == std::string::npos)
                            throw std::runtime_error("malformed tag at line " + std::to_string(lineNr) + " in "
                                                     + input_filename_);

                        std::string tag_name = inputLine.substr(0, match_pos);
                        inputLine.erase(0, match_pos);

                        // parse attributes if available
                        std::vector<std::string> attribute_names;
                        std::vector<std::string> attribute_values;
                        bool                     tag_completed = false;
                        while (!tag_completed) {
                            while ((inputLine.at(0) == '\t') || (inputLine.at(0) == ' ')) // remove whitespace
                                inputLine.erase(0, 1);

                            if (inputLine.at(0) == '/') { // end of empty element
                                process_pmml(tag_name, attribute_names, attribute_values, cur_level, 1, lineNr);
                                inputLine.erase(0, 1);
                                if (inputLine.at(0) != '>')
                                    throw std::runtime_error("malformed empty element tag at line "
                                                             + std::to_string(lineNr) + " in " + input_filename_);

                                tag_completed = true;
                            } else if (inputLine.at(0) == '>') { // end of start tag
                                process_pmml(tag_name, attribute_names, attribute_values, cur_level, 0, lineNr);

                                inputLine.erase(0, 1);
                                tag_stack.push(tag_name);
                                cur_level++;
                                tag_completed = true;
                            } else { // attribute
                                std::size_t match_pos = inputLine.find_first_of("=");
                                if (match_pos == std::string::npos)
                                    throw std::runtime_error("no value assigned to attribute at line "
                                                             + std::to_string(lineNr) + " in " + input_filename_);

                                std::string attribute_name = inputLine.substr(0, match_pos);
                                attribute_names.push_back(attribute_name);
                                inputLine.erase(0, match_pos);
                                // assert(inputLine.at(0) == '=');
                                if (inputLine.at(0) != '=')
                                    throw std::runtime_error("= symbol expected at line " + std::to_string(lineNr)
                                                             + " in " + input_filename_);
                                inputLine.erase(0, 1);
                                if (inputLine.at(0) != '"')
                                    throw std::runtime_error(
                                        "attribute value expected to be between double quotes at line "
                                        + std::to_string(lineNr) + " in " + input_filename_);
                                inputLine.erase(0, 1);
                                match_pos = inputLine.find_first_of("\"");
                                if (match_pos == std::string::npos)
                                    throw std::runtime_error(
                                        "attribute value does not have ending double quote at line "
                                        + std::to_string(lineNr) + " in " + input_filename_);

                                std::string attribute_value = inputLine.substr(0, match_pos);
                                attribute_values.push_back(attribute_value);
                                inputLine.erase(0, match_pos);
                                // assert(inputLine.at(0) == '"');
                                inputLine.erase(0, 1);
                            }
                        }
                    }
                } else { // element data
                         // ignore for now
                    while ((inputLine.size() > 0) && (inputLine.at(0) != '<'))
                        inputLine.erase(0, 1);
                }
            }
        }

        if (parsed_num_trees_ == 0) {
            throw std::runtime_error("Could not parse any trees from PMML");
        }

        if (parsed_rescale_constant_valid_)
            parsed_base_score_ = parsed_rescale_constant_;
        else
            parsed_base_score_ = 0.0;
        parsed_base_score_valid_    = true;
        parsed_learning_rate_       = 1.0;
        parsed_learning_rate_valid_ = true;
    }

    /*=================================================================================================================*/
    /* XGBoost dump_model() import */
    /*=================================================================================================================*/
    void parse_XGBoost()
    {

        std::string inputLine;
        std::size_t substr_size;

        cur_tree_node_count_ = 0;
        cur_tree_id_         = 0xFFFFFFFF; // unvalid

        // parse trees
        while (std::getline(input_file_, inputLine)) {
            if (inputLine.at(0) == 'b') { // new xgb boost tree
                // assert(inputLine.compare(0, 8, "booster[") == 0);
                if (inputLine.compare(0, 8, "booster[") != 0)
                    throw std::runtime_error("parse error 1 in " + input_filename_);

                inputLine.erase(0, 8);

                if (cur_tree_id_ != 0xFFFFFFFF) { // valid tree data
                    // store most recently parsed tree info
                    node_id_.push_back(cur_tree_node_id_);
                    node_is_leaf_.push_back(cur_tree_node_is_leaf_);
                    node_leaf_label_.push_back(cur_tree_node_leaf_label_);
                    node_feature_.push_back(cur_tree_node_feature_);
                    node_threshold_.push_back(cur_tree_node_threshold_);
                    node_left_child_.push_back(cur_tree_node_left_child_);
                    node_right_child_.push_back(cur_tree_node_right_child_);
                }

                // new tree
                cur_tree_id_ = std::stoi(inputLine, &substr_size);
                inputLine.erase(0, substr_size);

                cur_tree_node_count_ = 0;

                cur_tree_node_id_.resize(0);
                cur_tree_node_is_leaf_.resize(0);
                cur_tree_node_leaf_label_.resize(0);
                cur_tree_node_feature_.resize(0);
                cur_tree_node_threshold_.resize(0);
                cur_tree_node_left_child_.resize(0);
                cur_tree_node_right_child_.resize(0);
            } else {
                while (inputLine.at(0) == '\t') // erase leading tabs
                    inputLine.erase(0, 1);
                cur_tree_node_id_.push_back(std::stoi(inputLine, &substr_size));
                inputLine.erase(0, substr_size);
                // assert(inputLine.at(0) == ':');
                if (inputLine.at(0) != ':')
                    throw std::runtime_error("parse error 2 in " + input_filename_);

                inputLine.erase(0, 1);
                if (inputLine.at(0) == 'l') { // leaf node
                    // assert(inputLine.compare(0, 5, "leaf=") == 0);
                    if (inputLine.compare(0, 5, "leaf=") != 0)
                        throw std::runtime_error("parse error 3 in " + input_filename_);
                    inputLine.erase(0, 5);
                    cur_tree_node_is_leaf_.push_back(true);
                    cur_tree_node_leaf_label_.push_back(std::stof(inputLine, &substr_size));
                    cur_tree_node_feature_.push_back(0);
                    cur_tree_node_threshold_.push_back(0.0);
                    cur_tree_node_left_child_.push_back(0);
                    cur_tree_node_right_child_.push_back(0);
                } else { // split node
                    cur_tree_node_is_leaf_.push_back(false);
                    cur_tree_node_leaf_label_.push_back(0.0);
                    // assert(inputLine.compare(0, 2, "[f") == 0);
                    if (inputLine.compare(0, 2, "[f") != 0)
                        throw std::runtime_error("parse error 4 in " + input_filename_);
                    inputLine.erase(0, 2);
                    cur_tree_node_feature_.push_back(std::stoi(inputLine, &substr_size));
                    inputLine.erase(0, substr_size);
                    // assert(inputLine.at(0) == '<');
                    if (inputLine.at(0) != '<')
                        throw std::runtime_error("parse error 5 in " + input_filename_);
                    inputLine.erase(0, 1);
                    cur_tree_node_threshold_.push_back(std::stof(inputLine, &substr_size));
                    inputLine.erase(0, substr_size);
                    // assert(inputLine.compare(0, 6, "] yes=") == 0);
                    if (inputLine.compare(0, 6, "] yes=") != 0)
                        throw std::runtime_error("parse error 6 in " + input_filename_);
                    inputLine.erase(0, 6);
                    cur_tree_node_left_child_.push_back(std::stoi(inputLine, &substr_size));
                    inputLine.erase(0, substr_size);
                    // assert(inputLine.compare(0, 4, ",no=") == 0);
                    if (inputLine.compare(0, 4, ",no=") != 0)
                        throw std::runtime_error("parse error 7 in " + input_filename_);
                    inputLine.erase(0, 4);
                    cur_tree_node_right_child_.push_back(std::stoi(inputLine, &substr_size));
                }
                cur_tree_node_count_++;
            }
        }

        // store most recently parsed tree info
        node_id_.push_back(cur_tree_node_id_);
        node_is_leaf_.push_back(cur_tree_node_is_leaf_);
        node_leaf_label_.push_back(cur_tree_node_leaf_label_);
        node_feature_.push_back(cur_tree_node_feature_);
        node_threshold_.push_back(cur_tree_node_threshold_);
        node_left_child_.push_back(cur_tree_node_left_child_);
        node_right_child_.push_back(cur_tree_node_right_child_);

        parsed_node_comparison_type_       = 0;
        parsed_node_comparison_type_valid_ = true;
    }

    /*=================================================================================================================*/
    /* lightGBM dump_model() import */
    /*=================================================================================================================*/
    void parse_lightGBM()
    {

        uint32_t cur_tree_leaf_count     = 0;
        uint32_t cur_tree_leaf_id_offset = 0;

        std::string inputLine;
        std::size_t substr_size;

        // parse trees
        while (std::getline(input_file_, inputLine)) {
            if (inputLine.compare(0, 5, "Tree=") == 0) {
                inputLine.erase(0, 5);

                cur_tree_id_ = std::stoi(inputLine, &substr_size);
                inputLine.erase(0, substr_size);

                // new tree
                cur_tree_node_count_ = 0;

                cur_tree_node_id_.resize(0);
                cur_tree_node_is_leaf_.resize(0);
                cur_tree_node_leaf_label_.resize(0);
                cur_tree_node_feature_.resize(0);
                cur_tree_node_threshold_.resize(0);
                cur_tree_node_left_child_.resize(0);
                cur_tree_node_right_child_.resize(0);
            } else if (inputLine.compare(0, 10, "shrinkage=") == 0) {
                inputLine.erase(0, 10);
                cur_tree_node_count_ = cur_tree_node_id_.size();

                node_id_.push_back(cur_tree_node_id_);
                node_is_leaf_.push_back(cur_tree_node_is_leaf_);
                node_leaf_label_.push_back(cur_tree_node_leaf_label_);
                node_feature_.push_back(cur_tree_node_feature_);
                node_threshold_.push_back(cur_tree_node_threshold_);
                node_left_child_.push_back(cur_tree_node_left_child_);
                node_right_child_.push_back(cur_tree_node_right_child_);
            } else if (inputLine.compare(0, 11, "num_leaves=") == 0) {
                inputLine.erase(0, 11);

                cur_tree_leaf_count = std::stoi(inputLine, &substr_size);
                inputLine.erase(0, substr_size);
            } else if (inputLine.compare(0, 14, "split_feature=") == 0) {
                inputLine.erase(0, 14);

                uint32_t cur_node_id = 0;
                while (inputLine.size() > 0) {
                    uint32_t cur_xgb_node_feature = std::stoi(inputLine, &substr_size);
                    inputLine.erase(0, substr_size);

                    cur_tree_node_id_.push_back(cur_node_id);
                    cur_tree_node_is_leaf_.push_back(false);
                    cur_tree_node_leaf_label_.push_back(1.0);
                    cur_tree_node_feature_.push_back(cur_xgb_node_feature);
                    cur_tree_node_threshold_.push_back(0.0);
                    cur_tree_node_left_child_.push_back(0);
                    cur_tree_node_right_child_.push_back(0);

                    cur_node_id++;

                    if (inputLine.size() > 0) {
                        // assert(inputLine.at(0) == ' ');
                        if (inputLine.at(0) != ' ')
                            throw std::runtime_error("parse error 8 in " + input_filename_);
                        inputLine.erase(0, 1);
                    }
                }
                // add leaf nodes
                cur_tree_leaf_id_offset = cur_tree_node_id_.size();

                for (uint32_t i = 0; i < cur_tree_leaf_count; i++) {
                    cur_tree_node_id_.push_back(cur_tree_leaf_id_offset + i);
                    cur_tree_node_is_leaf_.push_back(true);
                    cur_tree_node_leaf_label_.push_back(0.0);
                    cur_tree_node_feature_.push_back(0);     // not used
                    cur_tree_node_threshold_.push_back(0.0); // not used
                    cur_tree_node_left_child_.push_back(0);  // not used
                    cur_tree_node_right_child_.push_back(0); // not used
                }
            } else if (inputLine.compare(0, 10, "threshold=") == 0) {
                inputLine.erase(0, 10);

                uint32_t cur_node_id = 0;
                while (inputLine.size() > 0) {
                    cur_tree_node_threshold_.at(cur_node_id) = std::stof(inputLine, &substr_size);
                    inputLine.erase(0, substr_size);

                    cur_node_id++;

                    if (inputLine.size() > 0) {
                        // assert(inputLine.at(0) == ' ');
                        if (inputLine.at(0) != ' ')
                            throw std::runtime_error("parse error 9 in " + input_filename_);
                        inputLine.erase(0, 1);
                    }
                }
            } else if (inputLine.compare(0, 11, "left_child=") == 0) {
                inputLine.erase(0, 11);

                uint32_t cur_node_id = 0;
                while (inputLine.size() > 0) {
                    int32_t cur_xgb_node_left_child = std::stoi(inputLine, &substr_size);
                    inputLine.erase(0, substr_size);

                    if (cur_xgb_node_left_child < 0)
                        cur_xgb_node_left_child = cur_tree_leaf_id_offset - cur_xgb_node_left_child - 1;

                    cur_tree_node_left_child_.at(cur_node_id) = cur_xgb_node_left_child;

                    cur_node_id++;

                    if (inputLine.size() > 0) {
                        // assert(inputLine.at(0) == ' ');
                        if (inputLine.at(0) != ' ')
                            throw std::runtime_error("parse error 10 in " + input_filename_);
                        inputLine.erase(0, 1);
                    }
                }
            } else if (inputLine.compare(0, 12, "right_child=") == 0) {
                inputLine.erase(0, 12);

                uint32_t cur_node_id = 0;
                while (inputLine.size() > 0) {
                    int32_t cur_xgb_node_right_child = std::stoi(inputLine, &substr_size);
                    inputLine.erase(0, substr_size);

                    if (cur_xgb_node_right_child < 0)
                        cur_xgb_node_right_child = cur_tree_leaf_id_offset - cur_xgb_node_right_child - 1;

                    cur_tree_node_right_child_.at(cur_node_id) = cur_xgb_node_right_child;

                    cur_node_id++;

                    if (inputLine.size() > 0) {
                        // assert(inputLine.at(0) == ' ');
                        if (inputLine.at(0) != ' ')
                            throw std::runtime_error("parse error 11 in " + input_filename_);
                        inputLine.erase(0, 1);
                    }
                }
            } else if (inputLine.compare(0, 11, "leaf_value=") == 0) {
                inputLine.erase(0, 11);

                uint32_t cur_node_id = cur_tree_leaf_id_offset;
                while (inputLine.size() > 0) {
                    cur_tree_node_leaf_label_.at(cur_node_id) = std::stof(inputLine, &substr_size);
                    inputLine.erase(0, substr_size);

                    cur_node_id++;

                    if (inputLine.size() > 0) {
                        // assert(inputLine.at(0) == ' ');
                        if (inputLine.at(0) != ' ')
                            throw std::runtime_error("parse error 12 in " + input_filename_);
                        inputLine.erase(0, 1);
                    }
                }
            }
        }

        parsed_base_score_          = 0.0;
        parsed_base_score_valid_    = true;
        parsed_learning_rate_       = 1.0;
        parsed_learning_rate_valid_ = true;

        parsed_node_comparison_type_       = 1;
        parsed_node_comparison_type_valid_ = true;
    }

    /*=================================================================================================================*/
    /* XGBoost save_model(*.json) import */
    /*=================================================================================================================*/
    bool find_string(std::string search_string)
    {
        uint32_t match_count = 0;
        char     c {};
        while (input_file_.get(c) && (match_count < search_string.size())) {
            if (c == search_string[match_count]) {
                match_count++;
                if (match_count == search_string.size())
                    break;
            } else
                match_count = 0;
        }
        return (match_count == search_string.size());
    }

    bool parse_string(std::string parse_string)
    {
        uint32_t match_count = 0;
        char     c {};
        while (input_file_.get(c) && (match_count < parse_string.size())) {
            if (c == parse_string[match_count]) {
                match_count++;
                if (match_count == parse_string.size())
                    break;
            } else
                break;
        }
        return (match_count == parse_string.size());
    }

    void parse_XGBoost_json()
    {
        char c {};

        // assert(find_string("\"num_trees\":\""));
        if (!find_string("\"num_trees\":\""))
            throw std::runtime_error("parse error 13 in " + input_filename_);
        input_file_ >> parsed_num_trees_;
        // assert(find_string("\"trees\":"));
        if (!find_string("\"trees\":"))
            throw std::runtime_error("parse error 14 in " + input_filename_);
        for (uint32_t t = 0; t < parsed_num_trees_; t++) {
            // assert(find_string("\"id\":"));
            if (!find_string("\"id\":"))
                throw std::runtime_error("parse error 15 in " + input_filename_);
            input_file_ >> cur_tree_id_;

            cur_tree_node_id_.resize(0);
            cur_tree_node_is_leaf_.resize(0);
            cur_tree_node_leaf_label_.resize(0);
            cur_tree_node_feature_.resize(0);
            cur_tree_node_threshold_.resize(0);
            cur_tree_node_left_child_.resize(0);
            cur_tree_node_right_child_.resize(0);

            uint32_t cur_node_id = 0;
            // assert(find_string("\"left_children\":["));
            if (!find_string("\"left_children\":["))
                throw std::runtime_error("parse error 16 in " + input_filename_);
            do {
                int32_t left_child {};
                input_file_ >> left_child;
                cur_tree_node_id_.push_back(cur_node_id);
                if (left_child == -1) { // leaf node
                    cur_tree_node_is_leaf_.push_back(true);
                    cur_tree_node_left_child_.push_back(0);
                } else { // split node
                    cur_tree_node_is_leaf_.push_back(false);
                    cur_tree_node_left_child_.push_back(left_child);
                }
                cur_node_id++;
                input_file_ >> c;
            } while (c != ']');
            cur_tree_node_count_ = cur_node_id;

            cur_node_id = 0;
            // assert(find_string("\"right_children\":["));
            if (!find_string("\"right_children\":["))
                throw std::runtime_error("parse error 17 in " + input_filename_);
            do {
                int32_t right_child {};
                input_file_ >> right_child;
                if (right_child == -1) // leaf node
                    cur_tree_node_right_child_.push_back(0);
                else // split node
                    cur_tree_node_right_child_.push_back(right_child);
                cur_node_id++;
                input_file_ >> c;
            } while (c != ']');
            // assert(cur_tree_node_count_ == cur_node_id);
            if (cur_tree_node_count_ != cur_node_id)
                throw std::runtime_error("parse error 18 in " + input_filename_);
            cur_node_id = 0;
            // assert(find_string("\"split_conditions\":["));
            if (!find_string("\"split_conditions\":["))
                throw std::runtime_error("parse error 19 in " + input_filename_);
            do {
                float float_val {};
                input_file_ >> float_val;
                if (cur_tree_node_is_leaf_.at(cur_node_id)) { // leaf node
                    cur_tree_node_threshold_.push_back(0.0);
                    cur_tree_node_leaf_label_.push_back(float_val);
                } else { // split node
                    cur_tree_node_threshold_.push_back(float_val);
                    cur_tree_node_leaf_label_.push_back(0.0);
                }
                cur_node_id++;
                input_file_ >> c;
            } while (c != ']');
            // assert(cur_tree_node_count_ == cur_node_id);
            if (cur_tree_node_count_ != cur_node_id)
                throw std::runtime_error("parse error 20 in " + input_filename_);
            cur_node_id = 0;
            // assert(find_string("\"split_indices\":["));
            if (!find_string("\"split_indices\":["))
                throw std::runtime_error("parse error 21 in " + input_filename_);
            do {
                uint32_t int_val {};
                input_file_ >> int_val;
                cur_tree_node_feature_.push_back(int_val);
                cur_node_id++;
                input_file_ >> c;
            } while (c != ']');
            // assert(cur_tree_node_count_ == cur_node_id);
            if (cur_tree_node_count_ != cur_node_id)
                throw std::runtime_error("parse error 22 in " + input_filename_);
            node_id_.push_back(cur_tree_node_id_);
            node_is_leaf_.push_back(cur_tree_node_is_leaf_);
            node_leaf_label_.push_back(cur_tree_node_leaf_label_);
            node_feature_.push_back(cur_tree_node_feature_);
            node_threshold_.push_back(cur_tree_node_threshold_);
            node_left_child_.push_back(cur_tree_node_left_child_);
            node_right_child_.push_back(cur_tree_node_right_child_);
        }
        if (!find_string("\"tree_param\":"))
            throw std::runtime_error("tree parameters not defined in " + input_filename_);

        if (find_string("\"num_feature\":\"")) {
            input_file_ >> parsed_num_features_;
            parsed_num_features_valid_ = true;
        } else
            throw std::runtime_error("number of features not defined in " + input_filename_);

        if (find_string("\"base_score\":\"")) {
            input_file_ >> parsed_base_score_;
            parsed_base_score_valid_ = true;
        } else
            throw std::runtime_error("no base_score parameter defined in " + input_filename_);

        if (find_string("\"objective\":{")) {
            if (find_string("\"name\":\"binary:logistic\""))
                parsed_base_score_ = std::log(parsed_base_score_) - std::log(1.0 - parsed_base_score_);
        } else
            throw std::runtime_error("no objective defined in " + input_filename_);

        parsed_learning_rate_       = 1.0;
        parsed_learning_rate_valid_ = true;

        parsed_node_comparison_type_       = 0;
        parsed_node_comparison_type_valid_ = true;
    }

    /*=================================================================================================================*/
    /* CatBoost save_model(*.json) import */
    /*=================================================================================================================*/
    void remove_white_space(std::string* input_line)
    {
        while ((input_line->size() > 0) && ((input_line->at(0) == '\t') || (input_line->at(0) == ' ')))
            input_line->erase(0, 1);
    }

    void parse_CatBoost_json()
    {
        std::string inputLine;
        uint32_t    lineNr = 0;

        parsed_num_trees_ = 0;
        while (std::getline(input_file_, inputLine)) {
            lineNr++;
            if (inputLine.find("\"oblivious_trees\":") != std::string::npos)
                break;
        }
        if (inputLine.size() == 0)
            throw std::runtime_error("parse error in line " + std::to_string(lineNr) + " in " + input_filename_);

        bool not_ready_parsing_trees = true;
        while (not_ready_parsing_trees) {
            parsed_num_trees_++;

            std::vector<float>    leaf_values;
            std::vector<uint32_t> level_features;
            std::vector<float>    level_thresholds;

            while (inputLine.find("\"leaf_values\":") == std::string::npos) {
                std::getline(input_file_, inputLine);
                lineNr++;
            }
            std::getline(input_file_, inputLine);
            lineNr++;
            remove_white_space(&inputLine);
            if (inputLine[0] != '[')
                throw std::runtime_error("parse error in line " + std::to_string(lineNr) + " in " + input_filename_);

            std::getline(input_file_, inputLine);
            lineNr++;
            remove_white_space(&inputLine);
            while (inputLine[0] != ']') {
                leaf_values.push_back(std::stof(inputLine));

                std::getline(input_file_, inputLine);
                lineNr++;
                remove_white_space(&inputLine);
            }

            while (inputLine.find("\"splits\":") == std::string::npos) {
                std::getline(input_file_, inputLine);
                lineNr++;
            }
            std::getline(input_file_, inputLine);
            lineNr++;
            remove_white_space(&inputLine);
            if (inputLine[0] != '[')
                throw std::runtime_error("parse error in line " + std::to_string(lineNr) + " in " + input_filename_);

            bool not_ready_parsing_tree_levels = true;
            while (not_ready_parsing_tree_levels) {

                std::getline(input_file_, inputLine);
                lineNr++;
                remove_white_space(&inputLine);
                if (inputLine[0] != '{')
                    throw std::runtime_error("parse error in line " + std::to_string(lineNr) + " in "
                                             + input_filename_);

                std::getline(input_file_, inputLine);
                lineNr++;
                remove_white_space(&inputLine);
                if (inputLine.find("\"border\":") != 0)
                    throw std::runtime_error("parse error in line " + std::to_string(lineNr) + " in "
                                             + input_filename_);
                inputLine.erase(0, 9);
                if (inputLine.find(",") == std::string::npos)
                    throw std::runtime_error("parse error in line " + std::to_string(lineNr) + " in "
                                             + input_filename_);
                inputLine.erase(inputLine.find(","));
                level_thresholds.push_back(std::stof(inputLine));

                std::getline(input_file_, inputLine);
                lineNr++;
                remove_white_space(&inputLine);
                if (inputLine.find("\"float_feature_index\":") != 0)
                    throw std::runtime_error("parse error in line " + std::to_string(lineNr) + " in "
                                             + input_filename_);
                inputLine.erase(0, 22);
                if (inputLine.find(",") == std::string::npos)
                    throw std::runtime_error("parse error in line " + std::to_string(lineNr) + " in "
                                             + input_filename_);

                inputLine.erase(inputLine.find(","));
                level_features.push_back(std::stoi(inputLine));

                std::getline(input_file_, inputLine);
                lineNr++;
                if (inputLine.find("\"split_index\":") == std::string::npos)
                    throw std::runtime_error("parse error in line " + std::to_string(lineNr) + " in "
                                             + input_filename_);

                std::getline(input_file_, inputLine);
                lineNr++;
                if (inputLine.find("\"split_type\":") == std::string::npos)
                    throw std::runtime_error("parse error in line " + std::to_string(lineNr) + " in "
                                             + input_filename_);

                std::getline(input_file_, inputLine);
                lineNr++;
                remove_white_space(&inputLine);
                if (inputLine[0] != '}')
                    throw std::runtime_error("parse error in line " + std::to_string(lineNr) + " in "
                                             + input_filename_);
                if ((inputLine.size() == 1) || (inputLine[1] != ','))
                    not_ready_parsing_tree_levels = false;
            }
            std::getline(input_file_, inputLine);
            lineNr++;
            remove_white_space(&inputLine);
            if (inputLine[0] != ']')
                throw std::runtime_error("parse error in line " + std::to_string(lineNr) + " in " + input_filename_);

            cur_tree_node_id_.resize(0);
            cur_tree_node_is_leaf_.resize(0);
            cur_tree_node_leaf_label_.resize(0);
            cur_tree_node_feature_.resize(0);
            cur_tree_node_threshold_.resize(0);
            cur_tree_node_left_child_.resize(0);
            cur_tree_node_right_child_.resize(0);

            for (uint32_t cur_level = 0; cur_level < static_cast<uint32_t>(level_features.size()); cur_level++) {
                for (uint32_t node_index = 0; node_index < (1u << cur_level); node_index++) {
                    cur_tree_node_id_.push_back(cur_tree_node_id_.size());
                    cur_tree_node_is_leaf_.push_back(false);
                    cur_tree_node_leaf_label_.push_back(0.0);
                    cur_tree_node_feature_.push_back(level_features.at(level_features.size() - cur_level - 1));
                    cur_tree_node_threshold_.push_back(level_thresholds.at(level_thresholds.size() - cur_level - 1));
                    cur_tree_node_left_child_.push_back(2 * cur_tree_node_id_.back() + 1);
                    cur_tree_node_right_child_.push_back(2 * cur_tree_node_id_.back() + 2);
                }
            }

            for (uint32_t node_index = 0; node_index < (1u << level_features.size()); node_index++) {
                cur_tree_node_id_.push_back(cur_tree_node_id_.size());
                cur_tree_node_is_leaf_.push_back(true);
                cur_tree_node_leaf_label_.push_back(leaf_values.at(node_index));
                cur_tree_node_feature_.push_back(0);
                cur_tree_node_threshold_.push_back(0.0);
                cur_tree_node_left_child_.push_back(0);
                cur_tree_node_right_child_.push_back(0);
            }

            node_id_.push_back(cur_tree_node_id_);
            node_is_leaf_.push_back(cur_tree_node_is_leaf_);
            node_leaf_label_.push_back(cur_tree_node_leaf_label_);
            node_feature_.push_back(cur_tree_node_feature_);
            node_threshold_.push_back(cur_tree_node_threshold_);
            node_left_child_.push_back(cur_tree_node_left_child_);
            node_right_child_.push_back(cur_tree_node_right_child_);

            std::getline(input_file_, inputLine);
            lineNr++;
            remove_white_space(&inputLine);
            if (inputLine[0] != '}')
                throw std::runtime_error("parse error in line " + std::to_string(lineNr) + " in " + input_filename_);
            if ((inputLine.size() == 1) || (inputLine[1] != ','))
                not_ready_parsing_trees = false;
        }
        std::getline(input_file_, inputLine);
        lineNr++;
        remove_white_space(&inputLine);
        if (inputLine[0] != ']')
            throw std::runtime_error("parse error in line " + std::to_string(lineNr) + " in " + input_filename_);
        if ((inputLine.size() > 1) && (inputLine[1] == ',')) {
            std::getline(input_file_, inputLine);
            lineNr++;
            if (inputLine.find("\"scale_and_bias\":") != std::string::npos) {
                std::getline(input_file_, inputLine);
                lineNr++;
                remove_white_space(&inputLine);
                if (inputLine[0] != '[')
                    throw std::runtime_error("parse error in line " + std::to_string(lineNr) + " in "
                                             + input_filename_);

                std::getline(input_file_, inputLine);
                lineNr++;
                remove_white_space(&inputLine);
                if (inputLine.find(",") == std::string::npos)
                    throw std::runtime_error("parse error in line " + std::to_string(lineNr) + " in "
                                             + input_filename_);
                inputLine.erase(inputLine.find(","));
                float parsed_scale = std::stof(inputLine);

                if (std::abs(parsed_scale - 1.0) > 0.001)
                    throw std::runtime_error("non-supported scaling value in  line " + std::to_string(lineNr) + " in "
                                             + input_filename_);

                std::getline(input_file_, inputLine);
                lineNr++;
                remove_white_space(&inputLine);
                if (inputLine[0] != '[')
                    throw std::runtime_error("parse error in line " + std::to_string(lineNr) + " in "
                                             + input_filename_);

                std::getline(input_file_, inputLine);
                lineNr++;
                remove_white_space(&inputLine);
                float parsed_bias = std::stof(inputLine);

                parsed_base_score_       = parsed_bias;
                parsed_base_score_valid_ = true;
            } else {
                parsed_base_score_valid_ = false;
                parsed_learning_rate_    = false;
            }
        } else {
            parsed_base_score_valid_ = false;
            parsed_learning_rate_    = false;
        }

        if (!parsed_base_score_valid_) {
            parsed_base_score_       = 0.0;
            parsed_base_score_valid_ = true;
        }

        if (!parsed_learning_rate_valid_) {
            parsed_learning_rate_       = 1.0;
            parsed_learning_rate_valid_ = true;
        }

        parsed_node_comparison_type_       = 1;
        parsed_node_comparison_type_valid_ = true;
    }

    /*=================================================================================================================*/
    /* ONNX import */
    /*=================================================================================================================*/
    uint64_t parse_varint()
    {
        uint64_t ret_val = 0;

        char     parsed_byte;
        uint32_t byte_index = 0;
        do {
            input_file_.read(&parsed_byte, 1);
            ret_val += (static_cast<uint64_t>(static_cast<uint8_t>(parsed_byte) & 0x7F) << (7u * byte_index));
            byte_index++;
        } while (static_cast<uint8_t>(parsed_byte) & 0x80);
        return ret_val;
    }

    void parse_onnx(snapml::ensemble_t ensemble_type)
    {
        std::vector<uint32_t>    class_ids;
        std::vector<uint32_t>    class_node_ids;
        std::vector<uint32_t>    class_tree_ids;
        std::vector<float>       class_weights;
        std::vector<int64_t>     class_labels_int64s;
        std::vector<std::string> class_labels_strings;

        std::vector<uint32_t> nodes_false_node_ids;
        std::vector<uint32_t> nodes_feature_ids;
        std::vector<bool>     nodes_modes; // 0: split node (BRANCH_LT), 1: leaf node (LEAF)
        std::vector<uint32_t> nodes_nodes_ids;
        std::vector<uint32_t> nodes_tree_ids;
        std::vector<uint32_t> nodes_true_node_ids;
        std::vector<float>    nodes_values;

        char parsed_byte;

        parsed_base_score_valid_ = false;
        if (find_string("base_values=")) {
            float    float_val;
            uint32_t parsed_uint32 = 0;
            for (uint32_t b = 0; b < 4; b++) {
                input_file_.read(&parsed_byte, 1);
                parsed_uint32 |= (static_cast<uint8_t>(parsed_byte) << b * 8);
            }
            memcpy(&float_val, &parsed_uint32, 4);
            parsed_base_score_       = float_val;
            parsed_base_score_valid_ = true;
        }
        input_file_.clear();
        input_file_.seekg(0, std::ios::beg);

        if (!find_string("TreeEnsemble"))
            throw std::runtime_error("parse error 23 in " + input_filename_);
        input_file_.read(&parsed_byte, 1);
        if (parsed_byte == 'C') { // Classifier
            if (!parse_string("lassifier"))
                throw std::runtime_error("non-supported model type in " + input_filename_);
            parsed_model_type_       = 0;
            parsed_model_type_valid_ = true;
        } else if (parsed_byte == 'R') { // Regressor
            if (!parse_string("egressor"))
                throw std::runtime_error("non-supported model type in " + input_filename_);
            parsed_model_type_       = 1;
            parsed_model_type_valid_ = true;
        } else
            throw std::runtime_error("non-supported model type in " + input_filename_);

        if (parsed_model_type_ == 0) {
            if (!find_string("class_ids"))
                throw std::runtime_error("parse error 40 in " + input_filename_);
            input_file_.read(&parsed_byte, 1);
            while (parsed_byte == 0x40) {
                uint32_t parsed_class_id = static_cast<uint32_t>(parse_varint());
                class_ids.push_back(parsed_class_id);
                input_file_.read(&parsed_byte, 1);
            }
            if (!find_string("class_nodeids"))
                throw std::runtime_error("parse error 41 in " + input_filename_);
            input_file_.read(&parsed_byte, 1);
            while (parsed_byte == 0x40) {
                uint32_t parsed_class_node_id = static_cast<uint32_t>(parse_varint());
                class_node_ids.push_back(parsed_class_node_id);
                input_file_.read(&parsed_byte, 1);
            }
            if (!find_string("class_treeids"))
                throw std::runtime_error("parse error 42 in " + input_filename_);
            input_file_.read(&parsed_byte, 1);
            while (parsed_byte == 0x40) {
                uint32_t parsed_class_tree_id = static_cast<uint32_t>(parse_varint());
                class_tree_ids.push_back(parsed_class_tree_id);
                input_file_.read(&parsed_byte, 1);
            }
            if (!find_string("class_weights"))
                throw std::runtime_error("parse error 43 in " + input_filename_);
            input_file_.read(&parsed_byte, 1);
            while (parsed_byte == 0x3d) {
                float    float_val;
                uint32_t parsed_uint32 = 0;
                // input_file_.read((char*)&parsed_float, 4);
                for (uint32_t b = 0; b < 4; b++) {
                    input_file_.read(&parsed_byte, 1);
                    parsed_uint32 |= ((uint8_t)parsed_byte << b * 8);
                }
                memcpy(&float_val, &parsed_uint32, 4);
                class_weights.push_back(float_val);
                input_file_.read(&parsed_byte, 1);
            }
            if (!find_string("classlabels_"))
                throw std::runtime_error("parse error 43b in " + input_filename_);
            input_file_.read(&parsed_byte, 1);
            if (parsed_byte == 'i') {
                if (!parse_string("nt64s"))
                    throw std::runtime_error("parse error 43c in " + input_filename_);
                input_file_.read(&parsed_byte, 1);
                while (parsed_byte == 0x40) {
                    uint64_t parsed_label_uint64 = parse_varint();
                    int64_t  parsed_label_int64;
                    memcpy(&parsed_label_int64, &parsed_label_uint64, 8);
                    class_labels_int64s.push_back(parsed_label_int64);
                    input_file_.read(&parsed_byte, 1);
                }
            } else if (parsed_byte == 's') {
                if (!parse_string("trings"))
                    throw std::runtime_error("parse error 43d in " + input_filename_);

            } else
                throw std::runtime_error("parse error 43e in " + input_filename_);
        }

        if (!find_string("nodes_falsenodeids"))
            throw std::runtime_error("parse error 44 in " + input_filename_);

        input_file_.read(&parsed_byte, 1);
        while (parsed_byte == 0x40) {
            uint32_t parsed_false_node_id = static_cast<uint32_t>(parse_varint());
            nodes_false_node_ids.push_back(parsed_false_node_id);
            input_file_.read(&parsed_byte, 1);
        }

        if (!find_string("nodes_featureids"))
            throw std::runtime_error("parse error 45 in " + input_filename_);
        input_file_.read(&parsed_byte, 1);
        while (parsed_byte == 0x40) {
            uint32_t parsed_node_feature_id = static_cast<uint32_t>(parse_varint());
            nodes_feature_ids.push_back(parsed_node_feature_id);
            input_file_.read(&parsed_byte, 1);
        }

        if (!find_string("nodes_modes"))
            throw std::runtime_error("parse error 46 in " + input_filename_);
        input_file_.read(&parsed_byte, 1);
        while (parsed_byte == 0x4a) {
            input_file_.read(&parsed_byte, 1);
            if (parsed_byte == 0x09) { // BRANCH_LT
                if (!parse_string("BRANCH_LT"))
                    throw std::runtime_error("non-supported node mode in " + input_filename_);
                nodes_modes.push_back(false);
                if (!parsed_node_comparison_type_valid_) {
                    parsed_node_comparison_type_       = 0;
                    parsed_node_comparison_type_valid_ = true;
                } else {
                    if (parsed_node_comparison_type_ != 0)
                        throw std::runtime_error("mixed less-than and less-than-or-equal-to node comparisons in "
                                                 + input_filename_);
                }
            } else if (parsed_byte == 0x0a) { // BRANCH_LEQ
                if (!parse_string("BRANCH_LEQ"))
                    throw std::runtime_error("non-supported node mode in " + input_filename_);
                nodes_modes.push_back(false);
                if (!parsed_node_comparison_type_valid_) {
                    parsed_node_comparison_type_       = 1;
                    parsed_node_comparison_type_valid_ = true;
                } else {
                    if (parsed_node_comparison_type_ != 1)
                        throw std::runtime_error("mixed less-than and less-than-or-equal-to node comparisons in "
                                                 + input_filename_);
                }
            } else if (parsed_byte == 0x04) { // LEAF
                if (!parse_string("LEAF"))
                    throw std::runtime_error("non-supported node mode in " + input_filename_);
                nodes_modes.push_back(true);
            } else
                throw std::runtime_error("non-supported node mode in " + input_filename_);
            input_file_.read(&parsed_byte, 1);
        }

        if (!find_string("nodes_nodeids"))
            throw std::runtime_error("parse error 70 in " + input_filename_);

        input_file_.read(&parsed_byte, 1);
        while (parsed_byte == 0x40) {
            uint32_t parsed_node_id = static_cast<uint32_t>(parse_varint());
            nodes_nodes_ids.push_back(parsed_node_id);
            input_file_.read(&parsed_byte, 1);
        }

        if (!find_string("nodes_treeids"))
            throw std::runtime_error("parse error 71 in " + input_filename_);

        input_file_.read(&parsed_byte, 1);
        while (parsed_byte == 0x40) {
            uint32_t parsed_node_tree_id = static_cast<uint32_t>(parse_varint());
            nodes_tree_ids.push_back(parsed_node_tree_id);
            input_file_.read(&parsed_byte, 1);
        }

        if (!find_string("nodes_truenodeids"))
            throw std::runtime_error("parse error 72 in " + input_filename_);

        input_file_.read(&parsed_byte, 1);
        while (parsed_byte == 0x40) {
            uint32_t parsed_true_node_id = static_cast<uint32_t>(parse_varint());
            nodes_true_node_ids.push_back(parsed_true_node_id);
            input_file_.read(&parsed_byte, 1);
        }

        if (!find_string("nodes_values"))
            throw std::runtime_error("parse error 73 in " + input_filename_);

        input_file_.read(&parsed_byte, 1);
        while (parsed_byte == 0x3d) {
            float    float_val;
            uint32_t parsed_uint32 = 0;
            // input_file_.read((char*)&parsed_float, 4);
            for (uint32_t b = 0; b < 4; b++) {
                input_file_.read(&parsed_byte, 1);
                parsed_uint32 |= ((uint8_t)parsed_byte << b * 8);
            }
            memcpy(&float_val, &parsed_uint32, 4);
            nodes_values.push_back(float_val);
            input_file_.read(&parsed_byte, 1);
        }

        if (parsed_model_type_ == 1) {
            if (!find_string("target_nodeids"))
                throw std::runtime_error("parse error 74 in " + input_filename_);

            input_file_.read(&parsed_byte, 1);
            while (parsed_byte == 0x40) {
                uint32_t parsed_class_node_id = static_cast<uint32_t>(parse_varint());
                class_node_ids.push_back(parsed_class_node_id);
                input_file_.read(&parsed_byte, 1);
            }
            if (!find_string("target_treeids"))
                throw std::runtime_error("parse error 75 in " + input_filename_);

            input_file_.read(&parsed_byte, 1);
            while (parsed_byte == 0x40) {
                uint32_t parsed_class_tree_id = static_cast<uint32_t>(parse_varint());
                class_tree_ids.push_back(parsed_class_tree_id);
                input_file_.read(&parsed_byte, 1);
            }
            if (!find_string("target_weights"))
                throw std::runtime_error("parse error 76 in " + input_filename_);

            input_file_.read(&parsed_byte, 1);
            while (parsed_byte == 0x3d) {
                float    float_val;
                uint32_t parsed_uint32 = 0;
                // input_file_.read((char*)&parsed_float, 4);
                for (uint32_t b = 0; b < 4; b++) {
                    input_file_.read(&parsed_byte, 1);
                    parsed_uint32 |= (static_cast<uint8_t>(parsed_byte) << b * 8u);
                }
                memcpy(&float_val, &parsed_uint32, 4);
                class_weights.push_back(float_val);
                input_file_.read(&parsed_byte, 1);
            }
        }

        // assume consecutive tree id and node id. assignements starting at 0
        parsed_num_trees_ = nodes_tree_ids.at(nodes_tree_ids.size() - 1) + 1;

        uint32_t cur_class_index = 0;
        uint32_t cur_node_index  = 0;

        for (uint32_t cur_tree_id = 0; cur_tree_id < parsed_num_trees_; cur_tree_id++) {
            cur_tree_node_id_.resize(0);
            cur_tree_node_is_leaf_.resize(0);
            cur_tree_node_leaf_label_.resize(0);
            cur_tree_node_feature_.resize(0);
            cur_tree_node_threshold_.resize(0);
            cur_tree_node_left_child_.resize(0);
            cur_tree_node_right_child_.resize(0);

            while ((cur_node_index < nodes_tree_ids.size()) && (nodes_tree_ids.at(cur_node_index) == cur_tree_id)) {
                cur_tree_node_id_.push_back(nodes_nodes_ids.at(cur_node_index));
                cur_tree_node_is_leaf_.push_back(nodes_modes.at(cur_node_index));
                if (nodes_modes.at(cur_node_index)) { // leaf
                    uint32_t i = cur_class_index;
                    while (class_node_ids.at(i) != nodes_nodes_ids.at(cur_node_index))
                        i++;
                    if ((class_node_ids.at(i) != nodes_nodes_ids.at(cur_node_index))
                        || (class_tree_ids.at(i) != nodes_tree_ids.at(cur_node_index)))
                        throw std::runtime_error("parse error 77 in " + input_filename_);
                    if (ensemble_type == snapml::ensemble_t::forest)
                        cur_tree_node_leaf_label_.push_back(class_weights.at(i) * parsed_num_trees_);
                    else
                        cur_tree_node_leaf_label_.push_back(class_weights.at(i));
                    cur_tree_node_feature_.push_back(0);
                    cur_tree_node_threshold_.push_back(0.0);
                    cur_tree_node_left_child_.push_back(0);
                    cur_tree_node_right_child_.push_back(0);
                } else { // split node
                    cur_tree_node_leaf_label_.push_back(static_cast<float>(parsed_node_comparison_type_));
                    cur_tree_node_feature_.push_back(nodes_feature_ids.at(cur_node_index));
                    cur_tree_node_threshold_.push_back(nodes_values.at(cur_node_index));
                    cur_tree_node_left_child_.push_back(nodes_true_node_ids.at(cur_node_index));
                    cur_tree_node_right_child_.push_back(nodes_false_node_ids.at(cur_node_index));
                }
                cur_node_index++;
            }

            // advance cur_class_index
            while ((cur_class_index < class_tree_ids.size()) && (class_tree_ids.at(cur_class_index) == cur_tree_id))
                cur_class_index++;

            node_id_.push_back(cur_tree_node_id_);
            node_is_leaf_.push_back(cur_tree_node_is_leaf_);
            node_leaf_label_.push_back(cur_tree_node_leaf_label_);
            node_feature_.push_back(cur_tree_node_feature_);
            node_threshold_.push_back(cur_tree_node_threshold_);
            node_left_child_.push_back(cur_tree_node_left_child_);
            node_right_child_.push_back(cur_tree_node_right_child_);
        }

        parsed_num_classes_       = std::max(class_labels_int64s.size(), class_labels_strings.size());
        parsed_num_classes_valid_ = true;
        for (uint32_t i = 0; i < class_labels_int64s.size(); i++)
            parsed_class_labels_.push_back(static_cast<float>(class_labels_int64s.at(i)));

        if (!parsed_base_score_valid_) {
            parsed_base_score_       = 0.0;
            parsed_base_score_valid_ = true;
        }
        parsed_learning_rate_       = 1.0;
        parsed_learning_rate_valid_ = true;
    }

    /*=================================================================================================================*/
    /* general functions */
    /*=================================================================================================================*/
    void update_to_used_features_only_impl()
    {

        // prepare "mapping table" for faster feature (re)mapping based on table indexing
        auto                  it              = parsed_used_features_.end();
        uint32_t              largest_feature = *(--it);
        std::vector<uint32_t> feature_mapper(largest_feature + 1, 0xFFFFFFFF);
        uint32_t              j = 0;
        for (auto i : parsed_used_features_)
            feature_mapper.at(i) = j++;

        // remap features
        for (uint32_t t = 0; t < node_id_.size(); t++) {
            for (uint32_t i = 0; i < node_id_.at(t).size(); i++) {
                if (!node_is_leaf_.at(t).at(i)) {
                    node_feature_.at(t).at(i) = feature_mapper.at(node_feature_.at(t).at(i));
                    if (node_feature_.at(t).at(i) == 0xFFFFFFFF)
                        throw std::runtime_error("internal error in feature (re)mapping for " + input_filename_);
                }
            }
        }
    }

    /*=================================================================================================================*/
    /* ModelImport data structures */
    /*=================================================================================================================*/
    uint32_t rec_determine_tree_depth(uint32_t cur_tree_index, uint32_t cur_node_index, uint32_t cur_depth)
    {
        uint32_t ret_val;

        if (node_is_leaf_.at(cur_tree_index).at(cur_node_index))
            ret_val = cur_depth;
        else {
            uint32_t left_tree_depth = rec_determine_tree_depth(
                cur_tree_index, node_left_child_.at(cur_tree_index).at(cur_node_index), cur_depth + 1);
            uint32_t right_tree_depth = rec_determine_tree_depth(
                cur_tree_index, node_right_child_.at(cur_tree_index).at(cur_node_index), cur_depth + 1);
            ret_val = (left_tree_depth > right_tree_depth ? left_tree_depth : right_tree_depth);
        }
        return ret_val;
    }

    uint32_t determine_tree_depth(uint32_t tree_id) { return rec_determine_tree_depth(tree_id, 0, 0); }

    // delete copy ctor
    ModelImport(const ModelImport&) = delete;

    // files
    std::string   input_filename_; // used for reporting parsing problems/errors
    std::ifstream input_file_;

    // node definitions of tree that is currently being parsed
    uint32_t              cur_tree_id_;
    uint32_t              cur_tree_node_count_;
    std::vector<uint32_t> cur_tree_node_tag_level_;
    std::vector<uint32_t> cur_tree_node_id_;
    std::vector<bool>     cur_tree_node_is_leaf_;
    std::vector<float>    cur_tree_node_leaf_label_;
    std::vector<uint32_t> cur_tree_node_feature_;
    std::vector<float>    cur_tree_node_threshold_;
    std::vector<uint32_t> cur_tree_node_left_child_;
    std::vector<uint32_t> cur_tree_node_right_child_;
    std::vector<bool>
        cur_tree_node_less_than_; // true if split node involves "lessThan" or "lessOrEqual" comparison,
                                  // false if split node involves "greaterThan" or "greaterOrEqual" comparison

    // node definitions of all trees in the ensemble
    std::vector<std::vector<uint32_t>>           node_id_;
    std::vector<std::vector<bool>>               node_is_leaf_;
    std::vector<std::vector<float>>              node_leaf_label_;
    std::vector<std::vector<std::vector<float>>> new_node_leaf_label_;
    std::vector<std::vector<uint32_t>>           node_feature_;
    std::vector<std::vector<float>>              node_threshold_;
    std::vector<std::vector<uint32_t>>           node_left_child_;
    std::vector<std::vector<uint32_t>>           node_right_child_;

    // model parameters
    uint32_t              parsed_num_trees_;
    uint32_t              parsed_num_features_; // xgb_json
    bool                  parsed_num_features_valid_ = false;
    uint32_t              parsed_model_type_; // pmml, onnx: 0 - classification, 1 - regression
    bool                  parsed_model_type_valid_ = false;
    uint32_t              parsed_ensemble_type_; // pmml: 0 - GB, 1 - RF
    bool                  parsed_ensemble_type_valid_ = false;
    uint32_t              parsed_num_classes_;
    bool                  parsed_num_classes_valid_ = false;
    std::vector<float>    parsed_class_labels_;
    std::vector<uint32_t> parsed_used_features_;

    double   parsed_base_score_;
    bool     parsed_base_score_valid_ = false;
    double   parsed_learning_rate_;
    bool     parsed_learning_rate_valid_ = false;
    uint32_t parsed_node_comparison_type_;
    bool     parsed_node_comparison_type_valid_ = false;

    // pmml specific
    enum PMML_MissingValueStrategy {
        lastPrediction,
        nullPrediction,
        defaultChild,
        weightedConfidence,
        aggregateNodes,
        none
    };

    float                     parsed_pmml_version_;
    uint32_t                  parsed_tree_type_;
    PMML_MissingValueStrategy parsed_missing_value_strategy_;
    float                     parsed_rescale_constant_;
    bool                      parsed_rescale_constant_valid_ = false;
    bool feature_index_format_; // true: features specified as indices ("x1", "x2", etc.), false: features specified as
                                // categories/field names

    std::vector<std::string> feature_names_;
    std::vector<std::string> feature_optypes_;
    std::vector<std::string> feature_datatypes_;

    std::vector<std::string> target_field_names_;
    std::vector<std::string> target_field_optypes_;
    std::vector<std::string> target_field_datatypes_;

    std::vector<std::string> output_field_names_;
    std::vector<std::string> output_field_optypes_;
    std::vector<std::string> output_field_datatypes_;

    uint32_t              cur_parsed_node_index_;
    double                cur_parsed_tot_rcount_;
    std::vector<double>   cur_parsed_rcount_;
    bool                  cur_parsed_predicate_is_true_;
    std::vector<uint32_t> last_parsed_empty_node_index_;
    bool                  leaf_label_based_on_rcount_;
    bool                  counting_num_classes_          = false;
    bool                  parsing_local_transformations_ = false;
};

}

#endif
