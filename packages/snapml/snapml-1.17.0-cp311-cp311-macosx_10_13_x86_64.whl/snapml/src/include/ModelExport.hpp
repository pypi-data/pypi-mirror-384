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
 * Authors      : Jan van Lunteren
 *
 * End Copyright
 ********************************************************************/

#ifndef MODELEXPORT
#define MODELEXPORT

#include <fstream>
#include <iomanip>

namespace tree {

class ModelExport {

public:
    ModelExport(std::string filename, std::string file_type, const std::vector<std::shared_ptr<TreeEnsembleModel>> in,
                snapml::ensemble_t ensemble_type, float rescale_constant, float rescale_factor,
                snapml::compare_t comparison_type, const std::vector<double>& classes, snapml::task_t model_type,
                std::string version)
    {
        exp_ensemble_t exp_ensemble_type
            = ((ensemble_type == snapml::ensemble_t::boosting) ? exp_ensemble_t::gradient_boosting
                                                               : exp_ensemble_t::random_forest);
        exp_model_t exp_model_type
            = ((model_type == snapml::task_t::classification) ? exp_model_t::classification : exp_model_t::regression);
        exp_comparison_t exp_comparison_type
            = ((comparison_type == snapml::compare_t::less_than) ? exp_comparison_t::less_than
                                                                 : exp_comparison_t::less_than_or_equal_to);

        output_filename_.assign(filename);
        output_file_.open(filename.c_str(), std::ios::binary);
        if (!output_file_.is_open())
            throw std::runtime_error("could not open file " + output_filename_);

        std::vector<std::vector<uint32_t>>           node_id;
        std::vector<std::vector<bool>>               node_is_leaf;
        std::vector<std::vector<std::vector<float>>> node_leaf_label;
        std::vector<std::vector<uint32_t>>           node_feature;
        std::vector<std::vector<float>>              node_threshold;
        std::vector<std::vector<uint32_t>>           node_left_child;
        std::vector<std::vector<uint32_t>>           node_right_child;

        for (uint32_t i = 0; i < in.size(); i++) {
            for (const auto& tree : in.at(i)->trees) {
                auto tmp = std::make_shared<SimpleTreeModel>(tree);
                node_id.push_back(tmp->node_id);
                node_is_leaf.push_back(tmp->node_is_leaf);
                node_leaf_label.push_back(tmp->node_leaf_label);
                node_feature.push_back(tmp->node_feature);
                node_threshold.push_back(tmp->node_threshold);
                node_left_child.push_back(tmp->node_left_child);
                node_right_child.push_back(tmp->node_right_child);
            }
        }

        if (file_type.compare(0, 4, "pmml") == 0) {
            if (classes.size() <= 2)
                export_pmml(&node_id, &node_is_leaf, &node_leaf_label, &node_feature, &node_threshold, &node_left_child,
                            &node_right_child, exp_ensemble_type, rescale_constant, rescale_factor, exp_comparison_type,
                            classes, exp_model_type, version);
            else
                export_pmml_mc(&node_id, &node_is_leaf, &node_leaf_label, &node_feature, &node_threshold,
                               &node_left_child, &node_right_child, exp_ensemble_type, rescale_constant, rescale_factor,
                               exp_comparison_type, classes, exp_model_type, version);
        }
        // else if (file_type.compare(0, 4, "onnx") == 0) {
        // }
        else
            throw std::runtime_error("non-supported output file type");
        output_file_.close();
    }

    ~ModelExport() { }

private:
    enum class exp_ensemble_t { gradient_boosting, random_forest };
    enum class exp_model_t { classification, regression };
    enum class exp_comparison_t { less_than, less_than_or_equal_to };

    /*=================================================================================================================*/
    /* PMML export */
    /*=================================================================================================================*/
    void determine_used_features(std::vector<uint32_t>* used_features, uint32_t* max_feature_id,
                                 std::vector<bool>* node_is_leaf, std::vector<uint32_t>* node_feature)
    {

        used_features->resize(0);
        *max_feature_id = 0;

        std::vector<uint32_t> feature_map;
        feature_map.resize(1, 0);

        for (uint32_t i = 0; i < node_is_leaf->size(); i++) {
            if (!node_is_leaf->at(i)) {
                if (*max_feature_id < node_feature->at(i)) {
                    *max_feature_id = node_feature->at(i);
                    if (*max_feature_id > (feature_map.size() * 32 - 1))
                        feature_map.resize(*max_feature_id / 32 + 1, 0);
                }
                feature_map.at(node_feature->at(i) / 32U) |= 1U << (node_feature->at(i) % 32U);
            }
        }
        for (uint32_t i = 0; i <= *max_feature_id; i++)
            if (feature_map.at(i / 32U) & (1U << (i % 32U))) {
                used_features->push_back(i);
            }
    }

    void rec_extract_nodes_gb_c(uint32_t cur_node_index, uint32_t cur_tag_depth, std::vector<bool>* node_is_leaf,
                                std::vector<std::vector<float>>* node_leaf_label, std::vector<uint32_t>* node_feature,
                                std::vector<float>* node_threshold, std::vector<uint32_t>* node_left_child,
                                std::vector<uint32_t>* node_right_child, std::vector<float>* node_score,
                                std::vector<uint32_t>* tag_depth, std::vector<uint32_t>* pred_field,
                                std::vector<float>* pred_value, std::vector<uint32_t>* non_mapped_score_indices)
    {
        if (cur_node_index == 0) {
            node_score->push_back(0.0);
            non_mapped_score_indices->push_back(0);
            tag_depth->push_back(cur_tag_depth);
            pred_field->push_back(0);
            pred_value->push_back(0.0);
        }
        if (!node_is_leaf->at(cur_node_index)) {
            tag_depth->push_back(cur_tag_depth);
            pred_field->push_back(node_feature->at(cur_node_index));
            pred_value->push_back(node_threshold->at(cur_node_index));

            if (node_is_leaf->at(node_left_child->at(cur_node_index)))
                node_score->push_back(node_leaf_label->at(node_left_child->at(cur_node_index)).at(0));
            else {
                node_score->push_back(0.0);
                non_mapped_score_indices->push_back(node_score->size() - 1);
                rec_extract_nodes_gb_c(node_left_child->at(cur_node_index), cur_tag_depth + 1, node_is_leaf,
                                       node_leaf_label, node_feature, node_threshold, node_left_child, node_right_child,
                                       node_score, tag_depth, pred_field, pred_value, non_mapped_score_indices);
            }

            if (node_is_leaf->at(node_right_child->at(cur_node_index))) {
                node_score->at(non_mapped_score_indices->back())
                    = node_leaf_label->at(node_right_child->at(cur_node_index)).at(0);
                non_mapped_score_indices->pop_back();
            } else
                rec_extract_nodes_gb_c(node_right_child->at(cur_node_index), cur_tag_depth, node_is_leaf,
                                       node_leaf_label, node_feature, node_threshold, node_left_child, node_right_child,
                                       node_score, tag_depth, pred_field, pred_value, non_mapped_score_indices);
        }
    }

    void write_node_structure_gb_c(std::vector<bool>* node_is_leaf, std::vector<std::vector<float>>* node_leaf_label,
                                   std::vector<uint32_t>* node_feature, std::vector<float>* node_threshold,
                                   std::vector<uint32_t>* node_left_child, std::vector<uint32_t>* node_right_child,
                                   float rescale_constant, float rescale_factor, exp_comparison_t comparison_type)
    {

        std::vector<float>    node_score;
        std::vector<uint32_t> tag_depth;
        std::vector<uint32_t> predicate_field;
        std::vector<float>    predicate_value;

        std::vector<uint32_t> non_mapped_score_indices;

        node_score.resize(0);
        tag_depth.resize(0);
        predicate_field.resize(0);
        predicate_value.resize(0);
        non_mapped_score_indices.resize(0);

        rec_extract_nodes_gb_c(0, 0, node_is_leaf, node_leaf_label, node_feature, node_threshold, node_left_child,
                               node_right_child, &node_score, &tag_depth, &predicate_field, &predicate_value,
                               &non_mapped_score_indices);

        output_file_ << "\t\t\t\t\t\t\t\t<Node score=\"" << rescale_factor * node_score.at(0) + rescale_constant
                     << "\">" << std::endl;
        output_file_ << "\t\t\t\t\t\t\t\t\t<True/>" << std::endl;

        for (uint32_t i = 1; i < node_score.size(); i++) {
            output_file_ << std::string(9 + tag_depth.at(i), '\t');
            output_file_ << "<Node score=\"" << std::setprecision(std::numeric_limits<float>::max_digits10 - 1)
                         << rescale_factor * node_score.at(i) + rescale_constant << "\">" << std::endl;

            output_file_ << std::string(10 + tag_depth.at(i), '\t');
            output_file_ << "<SimplePredicate field=\"x" << predicate_field.at(i) + 1 << "\" operator=\""
                         << (comparison_type == exp_comparison_t::less_than ? "lessThan" : "lessOrEqual")
                         << "\" value=\"" << std::setprecision(std::numeric_limits<float>::max_digits10 - 1)
                         << predicate_value.at(i) << "\"/>" << std::endl;

            if (i + 1 < node_score.size()) {
                if (tag_depth.at(i + 1) <= tag_depth.at(i)) {
                    for (uint32_t j = 0; j < tag_depth.at(i) - tag_depth.at(i + 1) + 1; j++) {
                        output_file_ << std::string(9 + tag_depth.at(i) - j, '\t');
                        output_file_ << "</Node>" << std::endl;
                    }
                }
            } else {
                for (uint32_t j = 0; j < tag_depth.at(i) + 1; j++) {
                    output_file_ << std::string(9 + tag_depth.at(i) - j, '\t');
                    output_file_ << "</Node>" << std::endl;
                }
            }
        }
        output_file_ << std::string(8, '\t');
        output_file_ << "</Node>" << std::endl;
    }

    void rec_extract_nodes_gb_r(uint32_t cur_node_index, uint32_t cur_tag_depth, std::vector<bool>* node_is_leaf,
                                std::vector<std::vector<float>>* node_leaf_label, std::vector<uint32_t>* node_feature,
                                std::vector<float>* node_threshold, std::vector<uint32_t>* node_left_child,
                                std::vector<uint32_t>* node_right_child, std::vector<float>* node_score,
                                std::vector<uint32_t>* tag_depth, std::vector<uint32_t>* pred_field,
                                std::vector<float>* pred_value, std::vector<uint32_t>* non_mapped_score_indices)
    {
        if (cur_node_index == 0) {
            node_score->push_back(0.0);
            non_mapped_score_indices->push_back(0);
            tag_depth->push_back(cur_tag_depth);
            pred_field->push_back(0);
            pred_value->push_back(0.0);
        }
        if (!node_is_leaf->at(cur_node_index)) {
            tag_depth->push_back(cur_tag_depth);
            pred_field->push_back(node_feature->at(cur_node_index));
            pred_value->push_back(node_threshold->at(cur_node_index));

            if (node_is_leaf->at(node_left_child->at(cur_node_index)))
                node_score->push_back(node_leaf_label->at(node_left_child->at(cur_node_index)).at(0));
            else {
                node_score->push_back(0.0);
                non_mapped_score_indices->push_back(node_score->size() - 1);
                rec_extract_nodes_gb_r(node_left_child->at(cur_node_index), cur_tag_depth + 1, node_is_leaf,
                                       node_leaf_label, node_feature, node_threshold, node_left_child, node_right_child,
                                       node_score, tag_depth, pred_field, pred_value, non_mapped_score_indices);
            }

            if (node_is_leaf->at(node_right_child->at(cur_node_index))) {
                node_score->at(non_mapped_score_indices->back())
                    = node_leaf_label->at(node_right_child->at(cur_node_index)).at(0);
                non_mapped_score_indices->pop_back();
            } else
                rec_extract_nodes_gb_r(node_right_child->at(cur_node_index), cur_tag_depth, node_is_leaf,
                                       node_leaf_label, node_feature, node_threshold, node_left_child, node_right_child,
                                       node_score, tag_depth, pred_field, pred_value, non_mapped_score_indices);
        }
    }

    void write_node_structure_gb_r(std::vector<bool>* node_is_leaf, std::vector<std::vector<float>>* node_leaf_label,
                                   std::vector<uint32_t>* node_feature, std::vector<float>* node_threshold,
                                   std::vector<uint32_t>* node_left_child, std::vector<uint32_t>* node_right_child,
                                   float rescale_constant, float rescale_factor, exp_comparison_t comparison_type)
    {

        std::vector<float>    node_score;
        std::vector<uint32_t> tag_depth;
        std::vector<uint32_t> predicate_field;
        std::vector<float>    predicate_value;

        std::vector<uint32_t> non_mapped_score_indices;

        node_score.resize(0);
        tag_depth.resize(0);
        predicate_field.resize(0);
        predicate_value.resize(0);
        non_mapped_score_indices.resize(0);

        rec_extract_nodes_gb_r(0, 0, node_is_leaf, node_leaf_label, node_feature, node_threshold, node_left_child,
                               node_right_child, &node_score, &tag_depth, &predicate_field, &predicate_value,
                               &non_mapped_score_indices);

        output_file_ << "\t\t\t\t\t<Node score=\"" << rescale_factor * node_score.at(0) + rescale_constant << "\">"
                     << std::endl;
        output_file_ << "\t\t\t\t\t\t<True/>" << std::endl;

        for (uint32_t i = 1; i < node_score.size(); i++) {
            output_file_ << std::string(6 + tag_depth.at(i), '\t');
            output_file_ << "<Node score=\"" << std::setprecision(std::numeric_limits<float>::max_digits10 - 1)
                         << rescale_factor * node_score.at(i) + rescale_constant << "\">" << std::endl;

            output_file_ << std::string(7 + tag_depth.at(i), '\t');
            output_file_ << "<SimplePredicate field=\"x" << predicate_field.at(i) + 1 << "\" operator=\""
                         << (comparison_type == exp_comparison_t::less_than ? "lessThan" : "lessOrEqual")
                         << "\" value=\"" << std::setprecision(std::numeric_limits<float>::max_digits10 - 1)
                         << predicate_value.at(i) << "\"/>" << std::endl;

            if (i + 1 < node_score.size()) {
                if (tag_depth.at(i + 1) <= tag_depth.at(i)) {
                    for (uint32_t j = 0; j < tag_depth.at(i) - tag_depth.at(i + 1) + 1; j++) {
                        output_file_ << std::string(6 + tag_depth.at(i) - j, '\t');
                        output_file_ << "</Node>" << std::endl;
                    }
                }
            } else {
                for (uint32_t j = 0; j < tag_depth.at(i) + 1; j++) {
                    output_file_ << std::string(6 + tag_depth.at(i) - j, '\t');
                    output_file_ << "</Node>" << std::endl;
                }
            }
        }
        output_file_ << std::string(5, '\t');
        output_file_ << "</Node>" << std::endl;
    }

    void rec_extract_nodes_rf_c(uint32_t cur_node_index, uint32_t cur_tag_depth, std::vector<bool>* node_is_leaf,
                                std::vector<std::vector<float>>* node_leaf_label, std::vector<uint32_t>* node_feature,
                                std::vector<float>* node_threshold, std::vector<uint32_t>* node_left_child,
                                std::vector<uint32_t>* node_right_child, std::vector<bool>* node_score_valid,
                                std::vector<float>* node_score, std::vector<uint32_t>* tag_depth,
                                std::vector<bool>* pred_true, std::vector<uint32_t>* pred_field,
                                std::vector<float>* pred_value)
    {

        tag_depth->push_back(cur_tag_depth);
        if (node_is_leaf->at(cur_node_index)) {
            pred_true->push_back(true);
            pred_field->push_back(0);
            pred_value->push_back(0.0);
            node_score_valid->push_back(true);
            node_score->push_back(node_leaf_label->at(cur_node_index).at(0));
        } else {
            pred_true->push_back(false);
            pred_field->push_back(node_feature->at(cur_node_index));
            pred_value->push_back(node_threshold->at(cur_node_index));
            if (node_is_leaf->at(node_left_child->at(cur_node_index))) {
                node_score_valid->push_back(true);
                node_score->push_back(node_leaf_label->at(node_left_child->at(cur_node_index)).at(0));
            } else {
                node_score_valid->push_back(false);
                node_score->push_back(0.0);
                rec_extract_nodes_rf_c(node_left_child->at(cur_node_index), cur_tag_depth + 1, node_is_leaf,
                                       node_leaf_label, node_feature, node_threshold, node_left_child, node_right_child,
                                       node_score_valid, node_score, tag_depth, pred_true, pred_field, pred_value);
            }

            rec_extract_nodes_rf_c(node_right_child->at(cur_node_index), cur_tag_depth, node_is_leaf, node_leaf_label,
                                   node_feature, node_threshold, node_left_child, node_right_child, node_score_valid,
                                   node_score, tag_depth, pred_true, pred_field, pred_value);
        }
    }

    void write_node_structure_rf_c(std::vector<bool>* node_is_leaf, std::vector<std::vector<float>>* node_leaf_label,
                                   std::vector<uint32_t>* node_feature, std::vector<float>* node_threshold,
                                   std::vector<uint32_t>* node_left_child, std::vector<uint32_t>* node_right_child,
                                   float rescale_constant, float rescale_factor, exp_comparison_t comparison_type,
                                   const std::vector<double>& classes)
    {
        std::vector<bool>     node_score_valid;
        std::vector<float>    node_score;
        std::vector<uint32_t> tag_depth;
        std::vector<bool>     predicate_true;
        std::vector<uint32_t> predicate_field;
        std::vector<float>    predicate_value;

        tag_depth.resize(0);
        predicate_true.resize(0);
        predicate_field.resize(0);
        predicate_value.resize(0);
        node_score_valid.resize(0);
        node_score.resize(0);

        rec_extract_nodes_rf_c(0, 0, node_is_leaf, node_leaf_label, node_feature, node_threshold, node_left_child,
                               node_right_child, &node_score_valid, &node_score, &tag_depth, &predicate_true,
                               &predicate_field, &predicate_value);

        output_file_ << "\t\t\t\t\t<Node>" << std::endl;
        output_file_ << "\t\t\t\t\t\t<True/>" << std::endl;

        for (uint32_t i = 0; i < node_score.size(); i++) {

            output_file_ << std::string(6 + tag_depth.at(i), '\t');
            if (node_score_valid.at(i))
                output_file_ << "<Node score=\"" << std::setprecision(std::numeric_limits<float>::max_digits10 - 1)
                             << ((node_score.at(i) > 0.5) ? classes.at(1) : classes.at(0)) << "\" recordCount=\"1.0\">"
                             << std::endl;
            else
                output_file_ << "<Node>" << std::endl;

            output_file_ << std::string(7 + tag_depth.at(i), '\t');
            if (predicate_true.at(i))
                output_file_ << "<True/>" << std::endl;
            else
                output_file_ << "<SimplePredicate field=\"double(x" << predicate_field.at(i) + 1 << ")\" operator=\""
                             << (comparison_type == exp_comparison_t::less_than ? "lessThan" : "lessOrEqual")
                             << "\" value=\"" << std::setprecision(std::numeric_limits<float>::max_digits10 - 1)
                             << predicate_value.at(i) << "\"/>" << std::endl;

            if (node_score_valid.at(i)) {
                output_file_ << std::string(7 + tag_depth.at(i), '\t') << "<ScoreDistribution value=\"" << classes.at(0)
                             << "\" recordCount=\"" << (1 - node_score.at(i)) << "\"/>" << std::endl;
                output_file_ << std::string(7 + tag_depth.at(i), '\t') << "<ScoreDistribution value=\"" << classes.at(1)
                             << "\" recordCount=\"" << node_score.at(i) << "\"/>" << std::endl;
            }

            if (i + 1 < node_score.size()) {
                if (tag_depth.at(i + 1) <= tag_depth.at(i)) {
                    for (uint32_t j = 0; j < tag_depth.at(i) - tag_depth.at(i + 1) + 1; j++) {
                        output_file_ << std::string(6 + tag_depth.at(i) - j, '\t');
                        output_file_ << "</Node>" << std::endl;
                    }
                }
            } else {
                for (uint32_t j = 0; j < tag_depth.at(i) + 1; j++) {
                    output_file_ << std::string(6 + tag_depth.at(i) - j, '\t');
                    output_file_ << "</Node>" << std::endl;
                }
            }
        }
        output_file_ << std::string(5, '\t');
        output_file_ << "</Node>" << std::endl;
    }

    void rec_extract_nodes_rf_r(uint32_t cur_node_index, uint32_t cur_tag_depth, std::vector<bool>* node_is_leaf,
                                std::vector<std::vector<float>>* node_leaf_label, std::vector<uint32_t>* node_feature,
                                std::vector<float>* node_threshold, std::vector<uint32_t>* node_left_child,
                                std::vector<uint32_t>* node_right_child, std::vector<float>* node_score,
                                std::vector<uint32_t>* tag_depth, std::vector<uint32_t>* pred_field,
                                std::vector<float>* pred_value, std::vector<uint32_t>* non_mapped_score_indices)
    {
        if (cur_node_index == 0) {
            node_score->push_back(0.0);
            non_mapped_score_indices->push_back(0);
            tag_depth->push_back(cur_tag_depth);
            pred_field->push_back(0);
            pred_value->push_back(0.0);
        }
        if (!node_is_leaf->at(cur_node_index)) {
            tag_depth->push_back(cur_tag_depth);
            pred_field->push_back(node_feature->at(cur_node_index));
            pred_value->push_back(node_threshold->at(cur_node_index));

            if (node_is_leaf->at(node_left_child->at(cur_node_index)))
                node_score->push_back(node_leaf_label->at(node_left_child->at(cur_node_index)).at(0));
            else {
                node_score->push_back(0.0);
                non_mapped_score_indices->push_back(node_score->size() - 1);
                rec_extract_nodes_rf_r(node_left_child->at(cur_node_index), cur_tag_depth + 1, node_is_leaf,
                                       node_leaf_label, node_feature, node_threshold, node_left_child, node_right_child,
                                       node_score, tag_depth, pred_field, pred_value, non_mapped_score_indices);
            }

            if (node_is_leaf->at(node_right_child->at(cur_node_index))) {
                node_score->at(non_mapped_score_indices->back())
                    = node_leaf_label->at(node_right_child->at(cur_node_index)).at(0);
                non_mapped_score_indices->pop_back();
            } else
                rec_extract_nodes_rf_r(node_right_child->at(cur_node_index), cur_tag_depth, node_is_leaf,
                                       node_leaf_label, node_feature, node_threshold, node_left_child, node_right_child,
                                       node_score, tag_depth, pred_field, pred_value, non_mapped_score_indices);
        }
    }

    void write_node_structure_rf_r(std::vector<bool>* node_is_leaf, std::vector<std::vector<float>>* node_leaf_label,
                                   std::vector<uint32_t>* node_feature, std::vector<float>* node_threshold,
                                   std::vector<uint32_t>* node_left_child, std::vector<uint32_t>* node_right_child,
                                   float rescale_constant, float rescale_factor, exp_comparison_t comparison_type)
    {

        std::vector<float>    node_score;
        std::vector<uint32_t> tag_depth;
        std::vector<uint32_t> predicate_field;
        std::vector<float>    predicate_value;

        std::vector<uint32_t> non_mapped_score_indices;

        node_score.resize(0);
        tag_depth.resize(0);
        predicate_field.resize(0);
        predicate_value.resize(0);
        non_mapped_score_indices.resize(0);

        rec_extract_nodes_rf_r(0, 0, node_is_leaf, node_leaf_label, node_feature, node_threshold, node_left_child,
                               node_right_child, &node_score, &tag_depth, &predicate_field, &predicate_value,
                               &non_mapped_score_indices);

        output_file_ << "\t\t\t\t\t<Node score=\"" << rescale_factor * node_score.at(0) + rescale_constant << "\">"
                     << std::endl;
        output_file_ << "\t\t\t\t\t\t<True/>" << std::endl;

        for (uint32_t i = 1; i < node_score.size(); i++) {
            output_file_ << std::string(6 + tag_depth.at(i), '\t');
            output_file_ << "<Node score=\"" << std::setprecision(std::numeric_limits<float>::max_digits10 - 1)
                         << rescale_factor * node_score.at(i) + rescale_constant << "\">" << std::endl;

            output_file_ << std::string(7 + tag_depth.at(i), '\t');
            output_file_ << "<SimplePredicate field=\"double(x" << predicate_field.at(i) + 1 << ")\" operator=\""
                         << (comparison_type == exp_comparison_t::less_than ? "lessThan" : "lessOrEqual")
                         << "\" value=\"" << std::setprecision(std::numeric_limits<float>::max_digits10 - 1)
                         << predicate_value.at(i) << "\"/>" << std::endl;

            if (i + 1 < node_score.size()) {
                if (tag_depth.at(i + 1) <= tag_depth.at(i)) {
                    for (uint32_t j = 0; j < tag_depth.at(i) - tag_depth.at(i + 1) + 1; j++) {
                        output_file_ << std::string(6 + tag_depth.at(i) - j, '\t');
                        output_file_ << "</Node>" << std::endl;
                    }
                }
            } else {
                for (uint32_t j = 0; j < tag_depth.at(i) + 1; j++) {
                    output_file_ << std::string(6 + tag_depth.at(i) - j, '\t');
                    output_file_ << "</Node>" << std::endl;
                }
            }
        }
        output_file_ << std::string(5, '\t');
        output_file_ << "</Node>" << std::endl;
    }

    void export_pmml(std::vector<std::vector<uint32_t>>* node_id, std::vector<std::vector<bool>>* node_is_leaf,
                     std::vector<std::vector<std::vector<float>>>* node_leaf_label,
                     std::vector<std::vector<uint32_t>>* node_feature, std::vector<std::vector<float>>* node_threshold,
                     std::vector<std::vector<uint32_t>>* node_left_child,
                     std::vector<std::vector<uint32_t>>* node_right_child, exp_ensemble_t ensemble_type,
                     float rescale_constant, float rescale_factor, exp_comparison_t comparison_type,
                     const std::vector<double>& classes, exp_model_t model_type, std::string version)
    {
        uint32_t                           max_feature_id = 0;
        std::vector<std::vector<uint32_t>> used_features(node_id->size());
        for (uint32_t t = 0; t < node_id->size(); t++) {
            uint32_t tree_max_feature_id = 0;
            determine_used_features(&(used_features.at(t)), &tree_max_feature_id, &(node_is_leaf->at(t)),
                                    &(node_feature->at(t)));
            max_feature_id = (tree_max_feature_id > max_feature_id) ? tree_max_feature_id : max_feature_id;
        }

        output_file_ << "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>" << std::endl;
        output_file_ << "<PMML xmlns=\"http://www.dmg.org/PMML-4_4\" "
                        "xmlns:data=\"http://jpmml.org/jpmml-model/InlineTable\" version=\"4.4\">"
                     << std::endl;
        output_file_ << "\t<Header>" << std::endl;
        output_file_ << "\t\t<Application name=\"Snap ML\" version=\"" << version << "\"/>" << std::endl;

        std::string algorithm_name;
        if (ensemble_type == exp_ensemble_t::gradient_boosting)
            algorithm_name = "Snap ML Boosting";
        else {
            assert(ensemble_type == exp_ensemble_t::random_forest);
            algorithm_name = "Snap ML Forest";
        }

        time_t    cur_time = time(0);
        struct tm time_struct;
        char      time_string[128];
        time_struct = *localtime(&cur_time);
        strftime(time_string, sizeof(time_string), "%Y-%m-%dT%XZ", &time_struct);

        output_file_ << "\t\t<Timestamp>";
        output_file_ << +time_string;
        output_file_ << "</Timestamp>" << std::endl;
        output_file_ << "\t</Header>" << std::endl;
        if (ensemble_type == exp_ensemble_t::gradient_boosting) {
            if (model_type == exp_model_t::classification) {
                output_file_ << "\t<DataDictionary>" << std::endl;
                output_file_ << "\t\t<DataField name=\"y\" optype=\"categorical\" dataType=\"float\">" << std::endl;
                for (uint32_t i = 0; i < classes.size(); i++)
                    output_file_ << "\t\t\t<Value value=\"" << classes.at(i) << "\"/>" << std::endl;
                output_file_ << "\t\t</DataField>" << std::endl;
                for (uint32_t i = 0; i <= max_feature_id; i++)
                    output_file_ << "\t\t<DataField name=\"x" << i + 1
                                 << "\" optype=\"continuous\" dataType=\"float\"/>" << std::endl;
                output_file_ << "\t</DataDictionary>" << std::endl;
                output_file_ << "\t<MiningModel functionName=\"classification\" algorithmName=\"" << algorithm_name
                             << "\" "
                                "x-mathContext=\"float\">"
                             << std::endl;
                output_file_ << "\t\t<MiningSchema>" << std::endl;
                output_file_ << "\t\t\t<MiningField name=\"y\" usageType=\"target\"/>" << std::endl;
                for (uint32_t i = 0; i <= max_feature_id; i++)
                    output_file_ << "\t\t\t<MiningField name=\"x" << i + 1 << "\"/>" << std::endl;
                output_file_ << "\t\t</MiningSchema>" << std::endl;
                output_file_ << "\t\t<Segmentation multipleModelMethod=\"modelChain\" "
                                "x-missingPredictionTreatment=\"returnMissing\">"
                             << std::endl;
                output_file_ << "\t\t\t<Segment id=\"1\">" << std::endl;
                output_file_ << "\t\t\t\t<True/>" << std::endl;
                output_file_ << "\t\t\t\t<MiningModel functionName=\"regression\" x-mathContext=\"float\">"
                             << std::endl;
                output_file_ << "\t\t\t\t\t<MiningSchema>" << std::endl;
                for (uint32_t i = 0; i <= max_feature_id; i++)
                    output_file_ << "\t\t\t\t\t\t<MiningField name=\"x" << i + 1 << "\"/>" << std::endl;
                output_file_ << "\t\t\t\t\t</MiningSchema>" << std::endl;
                output_file_ << "\t\t\t\t\t<Output>" << std::endl;
                output_file_ << "\t\t\t\t\t\t<OutputField name=\"resValue\" optype=\"continuous\" dataType=\"float\" "
                                "isFinalResult=\"false\"/>"
                             << std::endl;
                output_file_ << "\t\t\t\t\t</Output>" << std::endl;
                output_file_ << "\t\t\t\t\t<Segmentation multipleModelMethod=\"sum\">" << std::endl;
                for (uint32_t t = 0; t < node_id->size(); t++) {
                    output_file_ << "\t\t\t\t\t\t<Segment id=\"" << t + 1 << "\">" << std::endl;
                    output_file_ << "\t\t\t\t\t\t\t<True/>" << std::endl;
                    output_file_ << "\t\t\t\t\t\t\t<TreeModel functionName=\"regression\" "
                                    "noTrueChildStrategy=\"returnLastPrediction\" x-mathContext=\"float\">"
                                 << std::endl;
                    output_file_ << "\t\t\t\t\t\t\t\t<MiningSchema>" << std::endl;
                    for (uint32_t i = 0; i < used_features.at(t).size(); i++)
                        output_file_ << "\t\t\t\t\t\t\t\t\t<MiningField name=\"x" << used_features.at(t).at(i) + 1
                                     << "\"/>" << std::endl;
                    output_file_ << "\t\t\t\t\t\t\t\t</MiningSchema>" << std::endl;

                    write_node_structure_gb_c(&(node_is_leaf->at(t)), &(node_leaf_label->at(t)), &(node_feature->at(t)),
                                              &(node_threshold->at(t)), &(node_left_child->at(t)),
                                              &(node_right_child->at(t)), (t == 0) ? rescale_constant : 0,
                                              rescale_factor, comparison_type);

                    output_file_ << "\t\t\t\t\t\t\t</TreeModel>" << std::endl;
                    output_file_ << "\t\t\t\t\t\t</Segment>" << std::endl;
                }
                output_file_ << "\t\t\t\t\t</Segmentation>" << std::endl;
                output_file_ << "\t\t\t\t</MiningModel>" << std::endl;
                output_file_ << "\t\t\t</Segment>" << std::endl;
                output_file_ << "\t\t\t<Segment id=\"2\">" << std::endl;
                output_file_ << "\t\t\t\t<True/>" << std::endl;
                output_file_ << "\t\t\t\t<RegressionModel functionName=\"classification\" "
                                "normalizationMethod=\"logit\" x-mathContext=\"float\">"
                             << std::endl;
                output_file_ << "\t\t\t\t\t<MiningSchema>" << std::endl;
                output_file_ << "\t\t\t\t\t\t<MiningField name=\"y\" usageType=\"target\"/>" << std::endl;
                output_file_ << "\t\t\t\t\t\t<MiningField name=\"resValue\"/>" << std::endl;
                output_file_ << "\t\t\t\t\t</MiningSchema>" << std::endl;
                output_file_ << "\t\t\t\t\t<Output>" << std::endl;
                output_file_ << "\t\t\t\t\t\t<OutputField name=\"probability(" << classes.at(0)
                             << ")\" optype=\"continuous\" "
                                "dataType=\"float\" feature=\"probability\" value=\""
                             << classes.at(0) << "\"/>" << std::endl;
                output_file_ << "\t\t\t\t\t\t<OutputField name=\"probability(" << classes.at(1)
                             << ")\" optype=\"continuous\" "
                                "dataType=\"float\" feature=\"probability\" value=\""
                             << classes.at(1) << "\"/>" << std::endl;
                output_file_ << "\t\t\t\t\t</Output>" << std::endl;
                output_file_ << "\t\t\t\t\t<RegressionTable intercept=\"0.0\" targetCategory=\"" << classes.at(1)
                             << "\">" << std::endl;
                output_file_ << "\t\t\t\t\t\t<NumericPredictor name=\"resValue\" coefficient=\"1.0\"/>" << std::endl;
                output_file_ << "\t\t\t\t\t</RegressionTable>" << std::endl;
                output_file_ << "\t\t\t\t\t<RegressionTable intercept=\"0.0\" targetCategory=\"" << classes.at(0)
                             << "\"/>" << std::endl;
                output_file_ << "\t\t\t\t</RegressionModel>" << std::endl;
                output_file_ << "\t\t\t</Segment>" << std::endl;
                output_file_ << "\t\t</Segmentation>" << std::endl;
                output_file_ << "\t</MiningModel>" << std::endl;
            } else {
                assert(model_type == exp_model_t::regression);
                output_file_ << "\t<DataDictionary>" << std::endl;
                output_file_ << "\t\t<DataField name=\"y\" optype=\"continuous\" dataType=\"double\"/>" << std::endl;
                for (uint32_t i = 0; i <= max_feature_id; i++)
                    output_file_ << "\t\t<DataField name=\"x" << i + 1
                                 << "\" optype=\"continuous\" dataType=\"float\"/>" << std::endl;
                output_file_ << "\t</DataDictionary>" << std::endl;

                output_file_ << "\t<MiningModel functionName=\"regression\" algorithmName=\"" << algorithm_name
                             << "\" x-mathContext=\"float\">" << std::endl;
                output_file_ << "\t\t<MiningSchema>" << std::endl;
                output_file_ << "\t\t\t<MiningField name=\"y\" usageType=\"target\"/>" << std::endl;
                for (uint32_t i = 0; i <= max_feature_id; i++)
                    output_file_ << "\t\t\t<MiningField name=\"x" << i + 1 << "\"/>" << std::endl;
                output_file_ << "\t\t</MiningSchema>" << std::endl;
                output_file_ << "\t\t<Targets>" << std::endl;
                output_file_ << "\t\t\t<Target field=\"y\" rescaleConstant=\"0.0\"/>" << std::endl;
                output_file_ << "\t\t</Targets>" << std::endl;
                output_file_ << "\t\t<Segmentation multipleModelMethod=\"sum\">" << std::endl;
                for (uint32_t t = 0; t < node_id->size(); t++) {
                    output_file_ << "\t\t\t<Segment id=\"" << t + 1 << "\">" << std::endl;
                    output_file_ << "\t\t\t\t<True/>" << std::endl;
                    output_file_ << "\t\t\t\t<TreeModel functionName=\"regression\" "
                                    "noTrueChildStrategy=\"returnLastPrediction\" x-mathContext=\"float\">"
                                 << std::endl;
                    output_file_ << "\t\t\t\t\t<MiningSchema>" << std::endl;
                    for (uint32_t i = 0; i < used_features.at(t).size(); i++)
                        output_file_ << "\t\t\t\t\t\t<MiningField name=\"x" << used_features.at(t).at(i) + 1 << "\"/>"
                                     << std::endl;
                    output_file_ << "\t\t\t\t\t</MiningSchema>" << std::endl;

                    write_node_structure_gb_r(&(node_is_leaf->at(t)), &(node_leaf_label->at(t)), &(node_feature->at(t)),
                                              &(node_threshold->at(t)), &(node_left_child->at(t)),
                                              &(node_right_child->at(t)), (t == 0) ? rescale_constant : 0,
                                              rescale_factor, comparison_type);

                    output_file_ << "\t\t\t\t</TreeModel>" << std::endl;
                    output_file_ << "\t\t\t</Segment>" << std::endl;
                }
                output_file_ << "\t\t</Segmentation>" << std::endl;
                output_file_ << "\t</MiningModel>" << std::endl;
            }
        } else {
            assert(ensemble_type == exp_ensemble_t::random_forest);
            if (model_type == exp_model_t::classification) {
                output_file_ << "\t<DataDictionary>" << std::endl;
                output_file_ << "\t\t<DataField name=\"y\" optype=\"categorical\" dataType=\"float\">" << std::endl;
                for (uint32_t i = 0; i < classes.size(); i++)
                    output_file_ << "\t\t\t<Value value=\"" << classes.at(i) << "\"/>" << std::endl;
                output_file_ << "\t\t</DataField>" << std::endl;
                for (uint32_t i = 0; i <= max_feature_id; i++)
                    output_file_ << "\t\t<DataField name=\"x" << i + 1
                                 << "\" optype=\"continuous\" dataType=\"float\"/>" << std::endl;
                output_file_ << "\t</DataDictionary>" << std::endl;
                output_file_ << "\t<MiningModel functionName=\"classification\" "
                                "algorithmName=\""
                             << algorithm_name << "\">" << std::endl;
                output_file_ << "\t\t<MiningSchema>" << std::endl;
                output_file_ << "\t\t\t<MiningField name=\"y\" usageType=\"target\"/>" << std::endl;
                for (uint32_t i = 0; i <= max_feature_id; i++)
                    output_file_ << "\t\t\t<MiningField name=\"x" << i + 1 << "\"/>" << std::endl;
                output_file_ << "\t\t</MiningSchema>" << std::endl;
                output_file_ << "\t\t<Output>" << std::endl;
                output_file_ << "\t\t\t<OutputField name=\"probability(" << classes.at(0)
                             << ")\" optype=\"continuous\" dataType=\"double\" "
                                "feature=\"probability\" value=\""
                             << classes.at(0) << "\"/>" << std::endl;
                output_file_ << "\t\t\t<OutputField name=\"probability(" << classes.at(1)
                             << ")\" optype=\"continuous\" dataType=\"double\" "
                                "feature=\"probability\" value=\""
                             << classes.at(1) << "\"/>" << std::endl;
                output_file_ << "\t\t</Output>" << std::endl;
                output_file_ << "\t\t<LocalTransformations>" << std::endl;
                for (uint32_t i = 0; i <= max_feature_id; i++) {
                    output_file_ << "\t\t\t<DerivedField name=\"double(x" << i + 1
                                 << ")\" optype=\"continuous\" dataType=\"double\">" << std::endl;
                    output_file_ << "\t\t\t\t<FieldRef field=\"x" << i + 1 << "\"/>" << std::endl;
                    output_file_ << "\t\t\t</DerivedField>" << std::endl;
                }
                output_file_ << "\t\t</LocalTransformations>" << std::endl;
                output_file_ << "\t\t<Segmentation multipleModelMethod=\"average\">" << std::endl;
                for (uint32_t t = 0; t < node_id->size(); t++) {
                    output_file_ << "\t\t\t<Segment id=\"" << t + 1 << "\">" << std::endl;
                    output_file_ << "\t\t\t\t<True/>" << std::endl;
                    output_file_
                        << "\t\t\t\t<TreeModel functionName=\"classification\" missingValueStrategy=\"nullPrediction\">"
                        << std::endl;
                    output_file_ << "\t\t\t\t\t<MiningSchema>" << std::endl;
                    for (uint32_t i = 0; i < used_features.at(t).size(); i++)
                        output_file_ << "\t\t\t\t\t\t<MiningField name=\"double(x" << used_features.at(t).at(i) + 1
                                     << ")\"/>" << std::endl;
                    output_file_ << "\t\t\t\t\t</MiningSchema>" << std::endl;

                    write_node_structure_rf_c(&(node_is_leaf->at(t)), &(node_leaf_label->at(t)), &(node_feature->at(t)),
                                              &(node_threshold->at(t)), &(node_left_child->at(t)),
                                              &(node_right_child->at(t)), (t == 0) ? rescale_constant : 0,
                                              rescale_factor, comparison_type, classes);

                    output_file_ << "\t\t\t\t</TreeModel>" << std::endl;
                    output_file_ << "\t\t\t</Segment>" << std::endl;
                }
                output_file_ << "\t\t</Segmentation>" << std::endl;
                output_file_ << "\t</MiningModel>" << std::endl;
            } else {
                assert(model_type == exp_model_t::regression);
                output_file_ << "\t<DataDictionary>" << std::endl;
                output_file_ << "\t\t<DataField name=\"y\" optype=\"continuous\" dataType=\"double\"/>" << std::endl;
                for (uint32_t i = 0; i <= max_feature_id; i++)
                    output_file_ << "\t\t<DataField name=\"x" << i + 1
                                 << "\" optype=\"continuous\" dataType=\"float\"/>" << std::endl;
                output_file_ << "\t</DataDictionary>" << std::endl;
                output_file_ << "\t<MiningModel functionName=\"regression\" algorithmName=\"" << algorithm_name << "\">"
                             << std::endl;
                output_file_ << "\t\t<MiningSchema>" << std::endl;
                output_file_ << "\t\t\t<MiningField name=\"y\" usageType=\"target\"/>" << std::endl;
                for (uint32_t i = 0; i <= max_feature_id; i++)
                    output_file_ << "\t\t\t<MiningField name=\"x" << i + 1 << "\"/>" << std::endl;
                output_file_ << "\t\t</MiningSchema>" << std::endl;
                output_file_ << "\t\t<LocalTransformations>" << std::endl;
                for (uint32_t i = 0; i <= max_feature_id; i++) {
                    output_file_ << "\t\t\t<DerivedField name=\"double(x" << i + 1
                                 << ")\" optype=\"continuous\" dataType=\"double\">" << std::endl;
                    output_file_ << "\t\t\t\t<FieldRef field=\"x" << i + 1 << "\"/>" << std::endl;
                    output_file_ << "\t\t\t</DerivedField>" << std::endl;
                }
                output_file_ << "\t\t</LocalTransformations>" << std::endl;
                output_file_ << "\t\t<Segmentation multipleModelMethod=\"average\">" << std::endl;
                for (uint32_t t = 0; t < node_id->size(); t++) {
                    output_file_ << "\t\t\t<Segment id=\"" << t + 1 << "\">" << std::endl;
                    output_file_ << "\t\t\t\t<True/>" << std::endl;
                    output_file_
                        << "\t\t\t\t<TreeModel functionName=\"regression\" missingValueStrategy=\"nullPrediction\" "
                           "noTrueChildStrategy=\"returnLastPrediction\">"
                        << std::endl;
                    output_file_ << "\t\t\t\t\t<MiningSchema>" << std::endl;
                    for (uint32_t i = 0; i < used_features.at(t).size(); i++)
                        output_file_ << "\t\t\t\t\t\t<MiningField name=\"double(x" << used_features.at(t).at(i) + 1
                                     << ")\"/>" << std::endl;
                    output_file_ << "\t\t\t\t\t</MiningSchema>" << std::endl;

                    write_node_structure_rf_r(&(node_is_leaf->at(t)), &(node_leaf_label->at(t)), &(node_feature->at(t)),
                                              &(node_threshold->at(t)), &(node_left_child->at(t)),
                                              &(node_right_child->at(t)), (t == 0) ? rescale_constant : 0,
                                              rescale_factor, comparison_type);

                    output_file_ << "\t\t\t\t</TreeModel>" << std::endl;
                    output_file_ << "\t\t\t</Segment>" << std::endl;
                }
                output_file_ << "\t\t</Segmentation>" << std::endl;
                output_file_ << "\t</MiningModel>" << std::endl;
            }
        }
        output_file_ << "</PMML>" << std::endl;
    }

    void export_pmml_mc(std::vector<std::vector<uint32_t>>* node_id, std::vector<std::vector<bool>>* node_is_leaf,
                        std::vector<std::vector<std::vector<float>>>* node_leaf_label,
                        std::vector<std::vector<uint32_t>>*           node_feature,
                        std::vector<std::vector<float>>*              node_threshold,
                        std::vector<std::vector<uint32_t>>*           node_left_child,
                        std::vector<std::vector<uint32_t>>* node_right_child, exp_ensemble_t ensemble_type,
                        float rescale_constant, float rescale_factor, exp_comparison_t comparison_type,
                        const std::vector<double>& classes, exp_model_t model_type, std::string version)
    {
        uint32_t                           max_feature_id = 0;
        std::vector<std::vector<uint32_t>> used_features(node_id->size());
        for (uint32_t t = 0; t < node_id->size(); t++) {
            uint32_t tree_max_feature_id = 0;
            determine_used_features(&(used_features.at(t)), &tree_max_feature_id, &(node_is_leaf->at(t)),
                                    &(node_feature->at(t)));
            max_feature_id = (tree_max_feature_id > max_feature_id) ? tree_max_feature_id : max_feature_id;
        }

        output_file_ << "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>" << std::endl;
        output_file_ << "<PMML xmlns=\"http://www.dmg.org/PMML-4_4\" "
                        "xmlns:data=\"http://jpmml.org/jpmml-model/InlineTable\" version=\"4.4\">"
                     << std::endl;
        output_file_ << "\t<Header>" << std::endl;
        output_file_ << "\t\t<Application name=\"Snap ML\" version=\"" << version << "\"/>" << std::endl;

        assert(ensemble_type == exp_ensemble_t::gradient_boosting);
        assert(model_type == exp_model_t::classification);
        std::string algorithm_name = "Snap ML Boosting";

        time_t    cur_time = time(0);
        struct tm time_struct;
        char      time_string[128];
        time_struct = *localtime(&cur_time);
        strftime(time_string, sizeof(time_string), "%Y-%m-%dT%XZ", &time_struct);

        output_file_ << "\t\t<Timestamp>";
        output_file_ << +time_string;
        output_file_ << "</Timestamp>" << std::endl;
        output_file_ << "\t</Header>" << std::endl;

        output_file_ << "\t<DataDictionary>" << std::endl;
        output_file_ << "\t\t<DataField name=\"y\" optype=\"categorical\" dataType=\"float\">" << std::endl;
        for (uint32_t i = 0; i < classes.size(); i++)
            output_file_ << "\t\t\t<Value value=\"" << classes.at(i) << "\"/>" << std::endl;
        output_file_ << "\t\t</DataField>" << std::endl;
        for (uint32_t i = 0; i <= max_feature_id; i++)
            output_file_ << "\t\t<DataField name=\"x" << i + 1 << "\" optype=\"continuous\" dataType=\"float\"/>"
                         << std::endl;
        output_file_ << "\t</DataDictionary>" << std::endl;
        output_file_ << "\t<MiningModel functionName=\"classification\" algorithmName=\"" << algorithm_name
                     << "\" "
                        "x-mathContext=\"float\">"
                     << std::endl;
        output_file_ << "\t\t<MiningSchema>" << std::endl;
        output_file_ << "\t\t\t<MiningField name=\"y\" usageType=\"target\"/>" << std::endl;
        for (uint32_t i = 0; i <= max_feature_id; i++)
            output_file_ << "\t\t\t<MiningField name=\"x" << i + 1 << "\"/>" << std::endl;
        output_file_ << "\t\t</MiningSchema>" << std::endl;
        output_file_ << "\t\t<Segmentation multipleModelMethod=\"modelChain\" "
                        "x-missingPredictionTreatment=\"returnMissing\">"
                     << std::endl;

        for (uint32_t cur_segment_id = 1; cur_segment_id < classes.size() + 1; cur_segment_id++) {
            output_file_ << "\t\t\t<Segment id=\"" << cur_segment_id << "\">" << std::endl;
            output_file_ << "\t\t\t\t<True/>" << std::endl;
            output_file_ << "\t\t\t\t<MiningModel functionName=\"regression\" x-mathContext=\"float\">" << std::endl;
            output_file_ << "\t\t\t\t\t<MiningSchema>" << std::endl;
            for (uint32_t i = 0; i <= max_feature_id; i++)
                output_file_ << "\t\t\t\t\t\t<MiningField name=\"x" << i + 1 << "\"/>" << std::endl;
            output_file_ << "\t\t\t\t\t</MiningSchema>" << std::endl;
            output_file_ << "\t\t\t\t\t<Output>" << std::endl;
            output_file_ << "\t\t\t\t\t\t<OutputField name=\"resValue(" << classes.at(cur_segment_id - 1)
                         << ")\" optype=\"continuous\" dataType=\"float\" "
                            "isFinalResult=\"false\"/>"
                         << std::endl;
            output_file_ << "\t\t\t\t\t</Output>" << std::endl;
            output_file_ << "\t\t\t\t\t<Segmentation multipleModelMethod=\"sum\">" << std::endl;
            for (uint32_t t = 0; t < node_id->size() / classes.size(); t++) {
                uint32_t k = (cur_segment_id - 1) * (node_id->size() / classes.size()) + t;
                output_file_ << "\t\t\t\t\t\t<Segment id=\"" << t + 1 << "\">" << std::endl;
                output_file_ << "\t\t\t\t\t\t\t<True/>" << std::endl;
                output_file_ << "\t\t\t\t\t\t\t<TreeModel functionName=\"regression\" "
                                "noTrueChildStrategy=\"returnLastPrediction\" x-mathContext=\"float\">"
                             << std::endl;
                output_file_ << "\t\t\t\t\t\t\t\t<MiningSchema>" << std::endl;
                for (uint32_t i = 0; i < used_features.at(k).size(); i++)
                    output_file_ << "\t\t\t\t\t\t\t\t\t<MiningField name=\"x" << used_features.at(k).at(i) + 1 << "\"/>"
                                 << std::endl;
                output_file_ << "\t\t\t\t\t\t\t\t</MiningSchema>" << std::endl;

                write_node_structure_gb_c(&(node_is_leaf->at(k)), &(node_leaf_label->at(k)), &(node_feature->at(k)),
                                          &(node_threshold->at(k)), &(node_left_child->at(k)),
                                          &(node_right_child->at(k)), (t == 0) ? rescale_constant : 0, rescale_factor,
                                          comparison_type);

                output_file_ << "\t\t\t\t\t\t\t</TreeModel>" << std::endl;
                output_file_ << "\t\t\t\t\t\t</Segment>" << std::endl;
            }
            output_file_ << "\t\t\t\t\t</Segmentation>" << std::endl;
            output_file_ << "\t\t\t\t</MiningModel>" << std::endl;
            output_file_ << "\t\t\t</Segment>" << std::endl;
        }
        output_file_ << "\t\t\t<Segment id=\"" << classes.size() + 1 << "\">" << std::endl;
        output_file_ << "\t\t\t\t<True/>" << std::endl;
        output_file_ << "\t\t\t\t<RegressionModel functionName=\"classification\" "
                        "normalizationMethod=\"softmax\" x-mathContext=\"float\">"
                     << std::endl;
        output_file_ << "\t\t\t\t\t<MiningSchema>" << std::endl;
        output_file_ << "\t\t\t\t\t\t<MiningField name=\"y\" usageType=\"target\"/>" << std::endl;
        for (uint32_t i = 0; i < classes.size(); i++)
            output_file_ << "\t\t\t\t\t\t<MiningField name=\"resValue(" << classes.at(i) << ")\"/>" << std::endl;
        output_file_ << "\t\t\t\t\t</MiningSchema>" << std::endl;
        output_file_ << "\t\t\t\t\t<Output>" << std::endl;
        for (uint32_t i = 0; i < classes.size(); i++)
            output_file_ << "\t\t\t\t\t\t<OutputField name=\"probability(" << classes.at(i)
                         << ")\" optype=\"continuous\" "
                            "dataType=\"float\" feature=\"probability\" value=\""
                         << classes.at(i) << "\"/>" << std::endl;
        output_file_ << "\t\t\t\t\t</Output>" << std::endl;
        for (uint32_t i = 0; i < classes.size(); i++) {
            output_file_ << "\t\t\t\t\t<RegressionTable intercept=\"0.0\" targetCategory=\"" << classes.at(i) << "\">"
                         << std::endl;
            output_file_ << "\t\t\t\t\t\t<NumericPredictor name=\"resValue(" << classes.at(i)
                         << ")\" coefficient=\"1.0\"/>" << std::endl;
            output_file_ << "\t\t\t\t\t</RegressionTable>" << std::endl;
        }
        output_file_ << "\t\t\t\t</RegressionModel>" << std::endl;
        output_file_ << "\t\t\t</Segment>" << std::endl;
        output_file_ << "\t\t</Segmentation>" << std::endl;
        output_file_ << "\t</MiningModel>" << std::endl;
        output_file_ << "</PMML>" << std::endl;
    }

    /*=================================================================================================================*/
    /* ONNX export */
    /*=================================================================================================================*/

    // delete copy ctor
    ModelExport(const ModelExport&) = delete;

    // files
    std::string   output_filename_;
    std::ofstream output_file_;
};

}

#endif