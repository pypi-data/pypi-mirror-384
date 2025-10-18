/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2021
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Author       : Milos Stanisavljevic
 *                Nikolaos Papandreou
 *                Jan van Lunteren
 *
 * End Copyright
 ********************************************************************/

#ifndef MBI_TREE_ENSEMBLE_MODEL
#define MBI_TREE_ENSEMBLE_MODEL

#include <sys/time.h>
#include <iostream>
#include <fstream>
#include <chrono>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <atomic>
#include "MBITUtils.hpp"
#include "TreeEnsembleModel.hpp"
#include "Model.hpp"

//#define TIME_PROFILE // uncomment/comment = enable/disable eigen steps time profile

namespace tree {

struct MBITreeEnsembleModel : public Model {

public:
    MBITreeEnsembleModel()
        : pred_num_threads(1)
        , thread_info_vec(1)
        , exception(false)
        , threads_started(0)
    {
        task      = snapml::task_t::regression; // is checked in BoosterPredictor
        first_run = true;
        dbg_      = false;
    }

    ~MBITreeEnsembleModel()
    {
        try {
            free_matrices();
            clear_threads();
        } catch (std::exception& e) {
            std::cout << "Exception during cleanup of the MBI Tree Ensemble Model: " << e.what() << std::endl;
        }
    }

    uint32_t get_num_trees() { return mbit_tree_struct.size(); }

#define TREE_DEPTH_THRESHOLD 6
#define TREE_DEPTH_ZAIU      6

    void generate_data_structures(std::shared_ptr<TreeEnsembleModel> tree_ensemble_model,
                                  std::shared_ptr<glm::DenseDataset> data)
    {
        node_cmp_type = false;
        for (uint32_t i = 0; i < tree_ensemble_model->trees[0]->nodes.size(); i++) {
            if (tree_ensemble_model->trees[0]->nodes[i].is_leaf) {
                node_cmp_type = (tree_ensemble_model->trees[0]->nodes[i].feature != 0);
                break;
            }
        }

        num_trees = tree_ensemble_model->trees.size();

        // determine maximum tree depth and maximum feature selector in the ensemble
        max_tree_depth = 0;
        max_ft         = 0;

        for (uint32_t i = 0; i < num_trees; i++)
            rec_analyze_tree(tree_ensemble_model, i, 0, 0, &max_tree_depth, &max_ft);

        zaiu_only = (max_tree_depth <= TREE_DEPTH_THRESHOLD);

        if (!zaiu_only)
            max_tree_depth = TREE_DEPTH_ZAIU;

        // generate node vectors
        create_data_structures(tree_ensemble_model, data);

        // extend trees to maximum tree depth (perfect trees)
        for (uint32_t i = 0; i < num_trees; i++) {
            rec_extend_tree(i, 0, 0, 0, max_tree_depth);
            rec_assign_nodeids(i, 0, 0);
            remap_by_nodeids(i);
        }

        // generate single C, D matrix pair for maximum tree depth
        mbit_generate_CD_2D_matrices(max_tree_depth);

        // generate A, B, E matrices for each tree
        mbit_tree_struct.resize(num_trees);
        mbit_res_struct.resize(num_trees);
        for (uint32_t i = 0; i < num_trees; i++) {
            mbit_tree_generate_2D_matrices(i, max_tree_depth);
        }

        // determine pv_offset based on model parameters
        const uint32_t a[10] = { 3, 6, 12, 24, 48, 96, 192, 378, 750, 1500 };
        const uint32_t b[7]  = { 2, 3, 4, 5, 6, 7, 8 };

        pv_offset = 0;
        for (uint32_t i = 0; i < 10; i++) {
            if (num_trees >= a[i])
                pv_offset += 384;
            else
                break;
        }
        for (uint32_t i = 0; i < 7; i++) {
            if (max_tree_depth >= b[i])
                pv_offset += 48;
            else
                break;
        }
    }

    void get(tree::Model::Getter& getter) override
    {
        // num_trees
        getter.add(num_trees);

        // pv_offset
        getter.add(pv_offset);

        // mbit_CD_struct - content
        getter.add(mbit_CD_struct.mdim);
        getter.add(mbit_CD_struct.C_matrix[0], mbit_CD_struct.mdim.C_rows * mbit_CD_struct.mdim.C_cols * sizeof(float));
        getter.add(mbit_CD_struct.D_vector[0], mbit_CD_struct.mdim.D_cols * sizeof(float));

        for (uint32_t i = 0; i < num_trees; i++) {
            // mbit_tree_struct - content
            getter.add(mbit_tree_struct[i].mdim);
            getter.add(mbit_tree_struct[i].A_vector[0], mbit_tree_struct[i].mdim.A_cols * sizeof(uint32_t));
            getter.add(mbit_tree_struct[i].B_vector[0], mbit_tree_struct[i].mdim.B_cols * sizeof(float));
            getter.add(mbit_tree_struct[i].E_vector[0], mbit_tree_struct[i].mdim.E_rows * sizeof(float));
        }

        // zaiu_only
        getter.add(zaiu_only);

        // node_cmp_type
        getter.add(node_cmp_type);

        // compr_tree_buf_size_
        getter.add(compr_tree_buf_size_);

        // compr_tree_buf_ba
        if (compr_tree_buf_size_ > 0) {
            getter.add(*compr_tree_buf_, compr_tree_buf_size_ * sizeof(uint32_t));
        }
    }

    void put(tree::Model::Setter& setter, const uint64_t len) override
    {
        const uint64_t offset_begin = setter.get_offset();
        setter.check_before(len);

        // num_trees
        setter.get(&num_trees);

        mbit_tree_struct.resize(num_trees);
        mbit_res_struct.resize(num_trees);

        // pv_offset
        setter.get(&pv_offset);

        // mbit_CD_struct - content
        setter.get(&mbit_CD_struct.mdim);

        mbit_CD_struct.C_matrix = new float[(uint64_t)mbit_CD_struct.mdim.C_rows * mbit_CD_struct.mdim.C_cols]();
        mbit_CD_struct.D_vector = new float[mbit_CD_struct.mdim.D_cols]();

        setter.get(mbit_CD_struct.C_matrix, mbit_CD_struct.mdim.C_rows * mbit_CD_struct.mdim.C_cols * sizeof(float));
        setter.get(mbit_CD_struct.D_vector, mbit_CD_struct.mdim.D_cols * sizeof(float));

        for (uint32_t i = 0; i < num_trees; i++) {
            // mbit_tree_struct - content
            setter.get(&mbit_tree_struct[i].mdim);

            mbit_tree_struct[i].A_vector = new uint32_t[mbit_tree_struct[i].mdim.A_cols]();
            mbit_tree_struct[i].B_vector = new float[mbit_tree_struct[i].mdim.B_cols]();
            mbit_tree_struct[i].E_vector = new float[mbit_tree_struct[i].mdim.E_rows]();

            setter.get(mbit_tree_struct[i].A_vector, mbit_tree_struct[i].mdim.A_cols * sizeof(uint32_t));
            setter.get(mbit_tree_struct[i].B_vector, mbit_tree_struct[i].mdim.B_cols * sizeof(float));
            setter.get(mbit_tree_struct[i].E_vector, mbit_tree_struct[i].mdim.E_rows * sizeof(float));
        }

        // zaiu_only
        setter.get(&zaiu_only);

        // node_cmp_type
        setter.get(&node_cmp_type);

        // compr_tree_buf_size_
        setter.get(&compr_tree_buf_size_);
        compr_tree_vector_.resize(compr_tree_buf_size_);

        // compr_tree_buf_ba
        if (compr_tree_buf_size_ > 0) {
            compr_tree_buf_ = compr_tree_vector_.data();
            setter.get(compr_tree_buf_, compr_tree_buf_size_ * sizeof(uint32_t));
        }

        setter.check_after(offset_begin, len);
    }

    void aggregate(glm::DenseDataset* const data, double* preds, bool prob, uint32_t num_threads = 1)
    {
        if (node_cmp_type) {
            if (zaiu_only || (compr_tree_buf_[0] == 0))
                aggregate_impl<uint8_t, true>(data, preds, prob, num_threads, 0, data->get_num_ex());
            else if (compr_tree_buf_[0] == 4)
                aggregate_impl<uint16_t, true>(data, preds, prob, num_threads, 0, data->get_num_ex());
            else
                aggregate_impl<uint32_t, true>(data, preds, prob, num_threads, 0, data->get_num_ex());
        } else {
            if (zaiu_only || (compr_tree_buf_[0] == 0))
                aggregate_impl<uint8_t, false>(data, preds, prob, num_threads, 0, data->get_num_ex());
            else if (compr_tree_buf_[0] == 4)
                aggregate_impl<uint16_t, false>(data, preds, prob, num_threads, 0, data->get_num_ex());
            else
                aggregate_impl<uint32_t, false>(data, preds, prob, num_threads, 0, data->get_num_ex());
        }
    }

    void free_matrices() { mbit_free_matrics_impl(); }

    uint32_t       num_ex    = 0;
    uint64_t       num_trees = 0;
    snapml::task_t task;
    uint32_t       pv_offset      = 0;
    uint32_t       max_tree_depth = 0;
    uint32_t       max_ft         = 0;

private:
    /*=================================================================================================================*/
    /* compressed decision tree */
    /*=================================================================================================================*/
    const uint32_t compr_tree_to[3][24] = {
        { 1, 1, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 1, 1, 1, 2, 2, 2, 2 },
        { 1, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 1, 2, 2, 3, 3, 4, 4 },
        { 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 2, 3, 4, 5, 6, 7, 8 }
    };
    const uint32_t compr_tree_co[3][24] = {
        { 0, 2, 4, 9, 19, 39, 79, 159, 319, 639, 1279, 2559, 5119, 10239, 20479, 40959, 81919, 2, 3, 4, 6, 7, 8, 9 },
        { 0, 2, 5, 11, 23, 47, 95, 191, 383, 767, 1535, 3071, 6143, 12287, 24575, 49151, 98303, 2, 4, 5, 7, 8, 10, 11 },
        { 0,    3,     7,     15,    31,     63, 127, 255, 511, 1023, 2047, 4095,
          8191, 16383, 32767, 65535, 131071, 3,  5,   7,   9,   11,   13,   15 }
    };
    const uint32_t compr_tree_cs[3][24] = { { 2,    4,     8,     17,    35,     71, 143, 287, 575, 1151, 2303, 4607,
                                              9215, 18431, 36863, 73727, 147455, 4,  6,   8,   11,  13,   15,   17 },
                                            { 2,     4,     9,     19,    39,     79, 159, 319, 639, 1279, 2559, 5119,
                                              10239, 20479, 40959, 81919, 163839, 4,  7,   9,   12,  14,   17,   19 },
                                            { 2,     5,     11,    23,    47,     95, 191, 383, 767, 1535, 3071, 6143,
                                              12287, 24575, 49151, 98303, 196607, 5,  8,   11,  14,  17,   20,   23 } };

    std::vector<uint32_t> compr_tree_vector_;
    uint32_t*             compr_tree_buf_      = nullptr;
    uint32_t              compr_tree_buf_size_ = 0;

    void compr_tree_upd_access_counts(const std::shared_ptr<TreeEnsembleModel> tree_ensemble_model, uint32_t tree_id,
                                      float* in, uint32_t num_ft, uint32_t ex,
                                      std::vector<uint32_t>* access_count) const
    {
        uint32_t bin_tree_node_index = 0;

        while (!tree_ensemble_model->trees[tree_id]->nodes[bin_tree_node_index].is_leaf) {
            access_count->at(bin_tree_node_index) += 1;
            float val
                = ((float*)(in + num_ft * ex))[tree_ensemble_model->trees[tree_id]->nodes[bin_tree_node_index].feature];
            if (val < tree_ensemble_model->trees[tree_id]->nodes[bin_tree_node_index].threshold) {
                uint32_t left_child = tree_ensemble_model->trees[tree_id]->nodes[bin_tree_node_index].left_child;
                bin_tree_node_index = left_child;
            } else {
                uint32_t right_child = tree_ensemble_model->trees[tree_id]->nodes[bin_tree_node_index].right_child;
                bin_tree_node_index  = right_child;
            }
        }
        access_count->at(bin_tree_node_index) += 1;
    }

    bool compr_tree_select_node_type(const std::shared_ptr<TreeEnsembleModel> tree_ensemble_model, uint32_t tree_id,
                                     uint32_t bin_tree_node_index, std::vector<uint32_t>* bin_tree_access_count,
                                     const bool seq_skip_leafs, uint32_t seq_max_length, uint32_t* seq_actual_length,
                                     uint32_t* seq_bin_tree_node_indices, bool* seq_left_right_flags)
    {
        bool select_seq_cnode_type = true;

        *seq_actual_length       = 0;
        uint32_t cur_bnode_index = bin_tree_node_index;

        while ((*seq_actual_length < seq_max_length)
               && (!tree_ensemble_model->trees[tree_id]->nodes[cur_bnode_index].is_leaf)) {
            seq_bin_tree_node_indices[*seq_actual_length] = cur_bnode_index;

            uint32_t cur_left_child  = tree_ensemble_model->trees[tree_id]->nodes[cur_bnode_index].left_child;
            uint32_t cur_right_child = tree_ensemble_model->trees[tree_id]->nodes[cur_bnode_index].right_child;

            if (!seq_skip_leafs
                || (!tree_ensemble_model->trees[tree_id]->nodes[cur_left_child].is_leaf
                    && !tree_ensemble_model->trees[tree_id]->nodes[cur_right_child].is_leaf)) {
                seq_left_right_flags[*seq_actual_length]
                    = (bin_tree_access_count->at(cur_left_child) < bin_tree_access_count->at(cur_right_child));
            } else {
                if (!tree_ensemble_model->trees[tree_id]->nodes[cur_left_child].is_leaf)
                    seq_left_right_flags[*seq_actual_length] = false;
                else
                    seq_left_right_flags[*seq_actual_length] = true;
            }

            if (seq_left_right_flags[*seq_actual_length])
                cur_bnode_index = cur_right_child;
            else
                cur_bnode_index = cur_left_child;
            *seq_actual_length = *seq_actual_length + 1;
        }
        if (*seq_actual_length > 0)
            seq_left_right_flags[*seq_actual_length - 1] = true;

        return select_seq_cnode_type;
    }

    template <typename I> uint32_t compr_tree_typename_to_index() const
    {
        return (((std::is_same<I, uint32_t>::value) ? 2 : ((std::is_same<I, uint16_t>::value) ? 1 : 0)));
    }

    template <typename I> uint32_t compr_tree_typename_to_shift() const
    {
        return (((std::is_same<I, uint32_t>::value) ? 0 : (std::is_same<I, uint16_t>::value) ? 16 : 24));
    }

    template <typename I>
    uint32_t compr_tree_map_node(const std::shared_ptr<TreeEnsembleModel> tree_ensemble_model, uint32_t tree_id,
                                 const uint32_t bin_tree_node_index, std::vector<uint32_t>* bin_tree_access_count,
                                 const uint32_t seq_max_length, const bool seq_skip_leafs, uint32_t* buf_free_offset)
    {
        uint32_t cnode_offset = *buf_free_offset;
        uint8_t  selected_cnode_type;
        if (tree_ensemble_model->trees[tree_id]->nodes[bin_tree_node_index].is_leaf) {
            selected_cnode_type = 0;

            *buf_free_offset = cnode_offset + compr_tree_cs[compr_tree_typename_to_index<I>()][selected_cnode_type];

            ((uint8_t*)(&(compr_tree_buf_[cnode_offset])))[0]              = selected_cnode_type;
            *(bool*)(&(((uint8_t*)(&(compr_tree_buf_[cnode_offset])))[1])) = true;
            float* cur_threshold_vector                                    = (float*)(&(
                compr_tree_buf_[cnode_offset + compr_tree_to[compr_tree_typename_to_index<I>()][selected_cnode_type]]));

            cur_threshold_vector[0] = tree_ensemble_model->trees[tree_id]->nodes[bin_tree_node_index].leaf_label;
        } else {
            uint32_t seq_length;
            uint32_t seq_bin_tree_node_indices[7];
            bool     seq_left_right_flags[7];

            if (compr_tree_select_node_type(tree_ensemble_model, tree_id, bin_tree_node_index, bin_tree_access_count,
                                            seq_skip_leafs, seq_max_length, &seq_length, seq_bin_tree_node_indices,
                                            seq_left_right_flags)) {

                selected_cnode_type = (seq_length == 0) ? 0 : (seq_length + 17 - 1);

                *buf_free_offset = cnode_offset + compr_tree_cs[compr_tree_typename_to_index<I>()][selected_cnode_type];

                *(&(((uint8_t*)(&(compr_tree_buf_[cnode_offset])))[0])) = selected_cnode_type;

                I*        cur_feature_vector   = &(((I*)(&(compr_tree_buf_[cnode_offset])))[1]);
                float*    cur_threshold_vector = (float*)(&(
                    compr_tree_buf_[cnode_offset
                                    + compr_tree_to[compr_tree_typename_to_index<I>()][selected_cnode_type]]));
                uint32_t* cur_child_ptr_vector
                    = &(compr_tree_buf_[cnode_offset
                                        + compr_tree_co[compr_tree_typename_to_index<I>()][selected_cnode_type]]);

                for (uint32_t k = 0; k < seq_length; k++) {
                    cur_feature_vector[k]
                        = tree_ensemble_model->trees[tree_id]->nodes[seq_bin_tree_node_indices[k]].feature;
                    if (k < seq_length - 1)
                        cur_feature_vector[k]
                            |= (seq_left_right_flags[k] ? ((uint32_t)0x80000000 >> compr_tree_typename_to_shift<I>())
                                                        : 0);
                    cur_threshold_vector[k]
                        = tree_ensemble_model->trees[tree_id]->nodes[seq_bin_tree_node_indices[k]].threshold;
                    cur_child_ptr_vector[k]
                        = (seq_left_right_flags[k]
                               ? tree_ensemble_model->trees[tree_id]->nodes[seq_bin_tree_node_indices[k]].left_child
                               : tree_ensemble_model->trees[tree_id]->nodes[seq_bin_tree_node_indices[k]].right_child);
                }
                cur_child_ptr_vector[seq_length]
                    = (!seq_left_right_flags[seq_length - 1] ? tree_ensemble_model->trees[tree_id]
                                                                   ->nodes[seq_bin_tree_node_indices[seq_length - 1]]
                                                                   .left_child
                                                             : tree_ensemble_model->trees[tree_id]
                                                                   ->nodes[seq_bin_tree_node_indices[seq_length - 1]]
                                                                   .right_child);

                for (uint32_t i = 0; i < seq_length + 1; i++) {
                    uint32_t k = (seq_length - i);
                    if (tree_ensemble_model->trees[tree_id]->nodes[cur_child_ptr_vector[k]].is_leaf) {
                        float leaf_label
                            = tree_ensemble_model->trees[tree_id]->nodes[cur_child_ptr_vector[k]].leaf_label;
                        memcpy(&(cur_child_ptr_vector[k]), &leaf_label, 4);
                        if (k < seq_length)
                            cur_feature_vector[k]
                                = (cur_feature_vector[k] | ((uint32_t)0x40000000 >> compr_tree_typename_to_shift<I>()));
                        else
                            cur_feature_vector[seq_length - 1]
                                = (cur_feature_vector[seq_length - 1]
                                   | ((uint32_t)0x80000000 >> compr_tree_typename_to_shift<I>()));
                    } else
                        cur_child_ptr_vector[k] = compr_tree_map_node<I>(
                            tree_ensemble_model, tree_id, cur_child_ptr_vector[k], bin_tree_access_count,
                            seq_max_length, seq_skip_leafs, buf_free_offset);
                }
            }
        }
        return cnode_offset;
    }

    template <typename I, bool eq>
    bool compr_tree_proc_node(uint32_t* cur_cnode_offset, uint32_t iteration_count, I* cur_feature_vector,
                              float* cur_threshold_vector, uint32_t* cur_child_ptr_vector, float* i,
                              float* pred_result) const
    {
        bool not_ready   = true;
        bool match_found = false;
        for (uint8_t k = 0; k < iteration_count; k++) {
            I    cur_feature    = (cur_feature_vector[k] & ((uint32_t)0x3FFFFFFF >> compr_tree_typename_to_shift<I>()));
            bool cur_left_right = (cur_feature_vector[k] & ((uint32_t)0x80000000 >> compr_tree_typename_to_shift<I>()));
            bool cur_child_is_leaf
                = (cur_feature_vector[k] & ((uint32_t)0x40000000 >> compr_tree_typename_to_shift<I>()));
            float    cur_threshold  = cur_threshold_vector[k];
            uint32_t cur_child_node = cur_child_ptr_vector[k];

            if ((!eq && ((i[cur_feature] < cur_threshold) == cur_left_right))
                || (eq && ((i[cur_feature] <= cur_threshold) == cur_left_right))) {
                if (cur_child_is_leaf) {
                    float float_val;
                    memcpy(&float_val, &cur_child_node, 4);
                    *pred_result = float_val;
                    not_ready    = false;
                } else {
                    *cur_cnode_offset = cur_child_node;
                }
                match_found = true;
                break;
            }
        }
        if (!match_found) {
            uint8_t k           = iteration_count;
            I       cur_feature = (cur_feature_vector[k] & ((uint32_t)0x3FFFFFFF >> compr_tree_typename_to_shift<I>()));
            bool    cur_left_child_is_leaf
                = (cur_feature_vector[k] & ((uint32_t)0x40000000 >> compr_tree_typename_to_shift<I>()));
            bool cur_right_child_is_leaf
                = (cur_feature_vector[k] & ((uint32_t)0x80000000 >> compr_tree_typename_to_shift<I>()));
            float    cur_threshold        = cur_threshold_vector[k];
            uint32_t cur_left_child_node  = cur_child_ptr_vector[k];
            uint32_t cur_right_child_node = cur_child_ptr_vector[k + 1];

            if ((!eq && (i[cur_feature] < cur_threshold)) || (eq && (i[cur_feature] <= cur_threshold))) {
                if (cur_left_child_is_leaf) {
                    float float_val;
                    memcpy(&float_val, &cur_left_child_node, 4);
                    *pred_result = float_val;
                    not_ready    = false;
                } else {
                    *cur_cnode_offset = cur_left_child_node;
                }
                match_found = true;
            } else {
                if (cur_right_child_is_leaf) {
                    float float_val;
                    memcpy(&float_val, &cur_right_child_node, 4);
                    *pred_result = float_val;
                    not_ready    = false;
                } else {
                    *cur_cnode_offset = cur_right_child_node;
                }
                match_found = true;
            }
        }
        return not_ready;
    }

    template <typename I, bool eq> float compr_tree_predict(uint32_t node_offset, float* i) const
    {
        float ret_val = 0.0;
        if (((uint8_t*)(&(compr_tree_buf_[node_offset])))[0]) {

            uint32_t cur_cnode_offset = node_offset;
            bool     not_ready        = true;
            while (not_ready) {
                uint8_t  cur_cnode_type     = ((uint8_t*)(&(compr_tree_buf_[cur_cnode_offset])))[0] & 0x1F;
                uint32_t iteration_count    = (cur_cnode_type >= 17) ? (cur_cnode_type - 17) : (cur_cnode_type - 1);
                I*       cur_feature_vector = &(((I*)(&(compr_tree_buf_[cur_cnode_offset])))[1]);
                float*   cur_threshold_vector
                    = (float*)(&(compr_tree_buf_[cur_cnode_offset
                                                 + compr_tree_to[compr_tree_typename_to_index<I>()][cur_cnode_type]]));
                uint32_t* cur_child_ptr_vector
                    = &(compr_tree_buf_[cur_cnode_offset
                                        + compr_tree_co[compr_tree_typename_to_index<I>()][cur_cnode_type]]);

                not_ready = compr_tree_proc_node<I, eq>(&cur_cnode_offset, iteration_count, cur_feature_vector,
                                                        cur_threshold_vector, cur_child_ptr_vector, i, &ret_val);
            }
        } else
            ret_val = ((float*)compr_tree_buf_)[node_offset + 1];

        return ret_val;
    }

    /*=================================================================================================================*/
    /* mbit */
    /*=================================================================================================================*/
    void mbit_generate_CD_2D_matrices(uint32_t target_tree_depth)
    {
        uint32_t num_nodes          = (2 << target_tree_depth) - 1;
        uint32_t num_nodes_leaf     = 2 << (target_tree_depth - 1);
        uint32_t num_nodes_internal = num_nodes - num_nodes_leaf;

        num_nodes_internal = (num_nodes_internal / (2 * PAR_COUNT) + 1) * 2 * PAR_COUNT; // helps for fast stp12 & stp5

        mbit_CD_struct.mdim.C_rows = num_nodes_internal;
        mbit_CD_struct.mdim.C_cols = num_nodes_leaf;
        mbit_CD_struct.mdim.D_rows = 1;
        mbit_CD_struct.mdim.D_cols = num_nodes_leaf;

        mbit_CD_struct.C_matrix = new float[(uint64_t)mbit_CD_struct.mdim.C_rows * mbit_CD_struct.mdim.C_cols]();
        mbit_CD_struct.D_vector = new float[mbit_CD_struct.mdim.D_cols]();

        uint32_t leaf_id = (2 << (target_tree_depth - 1)) - 1; // starting id of leaf nodes in a perfect tree
        for (uint32_t col = 0; col < mbit_CD_struct.mdim.C_cols; col++) {
            uint32_t node_id = leaf_id + col;
            while (node_id) {
                if (node_id & 0x1) {
                    node_id = (node_id - 1) >> 1; // left_child_id = 2*parent_id +1
                    mbit_CD_struct.C_matrix[(uint64_t)node_id * mbit_CD_struct.mdim.C_cols + col] = +1.0;
                    mbit_CD_struct.D_vector[col]++;
                } else {
                    node_id = (node_id - 2) >> 1; // right_child_id = 2*parent_id +2
                    mbit_CD_struct.C_matrix[(uint64_t)node_id * mbit_CD_struct.mdim.C_cols + col] = -1.0;
                }
            }
        }

        if (dbg_) {
            printf(">>DBG: mbit_generate_CD_2D_matrices()\n");
            // C_perf
            for (uint32_t row = 0; row < mbit_CD_struct.mdim.C_rows; row++) {
                printf("C_perf[%2u,0:%u] =", row, mbit_CD_struct.mdim.C_cols - 1);
                for (uint32_t col = 0; col < mbit_CD_struct.mdim.C_cols; col++)
                    printf(" %2d", (int32_t)mbit_CD_struct.C_matrix[row * mbit_CD_struct.mdim.C_cols + col]);
                printf("\n");
            }
            // D_perf
            printf("D_perf[0:%u] =", mbit_CD_struct.mdim.D_cols - 1);
            for (uint32_t col = 0; col < mbit_CD_struct.mdim.D_cols; col++)
                printf(" %1.0f", mbit_CD_struct.D_vector[col]);
            printf("\n");
        }
    }

    void mbit_init_2D_tensors() { mbit_init_CD_2D_tensors(); }

    void mbit_alloc_2D_res_tensors(const uint32_t new_num_ex, uint32_t new_mbit_par_tree_count)
    {
        for (int32_t i = 0; i < mbit_tree_struct.size(); i++)
            mbit_tree_struct[i].mdim.num_ex = new_num_ex;

        if (!first_run) {
            for (uint32_t i = 0; i < (mbit_tree_struct.size() + (mbit_par_tree_count - 1)) / mbit_par_tree_count; i++) {
                glm::zdnn_safe(zdnn_free_ztensor_buffer(mbit_res_struct[i].Res12_z),
                               "[ZDNN_MBIT] couldn't free memory for Res12.");
                glm::zdnn_safe(zdnn_free_ztensor_buffer(mbit_res_struct[i].Res34_z),
                               "[ZDNN_MBIT] couldn't free memory for Res34.");
            }
        }
        mbit_par_tree_count = new_mbit_par_tree_count;

        for (uint32_t i = 0; i < (mbit_tree_struct.size() + (mbit_par_tree_count - 1)) / mbit_par_tree_count; i++) {
            uint32_t cur_mbit_par_tree_count = ((((mbit_tree_struct.size() % mbit_par_tree_count) > 0)
                                                 && (i == mbit_tree_struct.size() / mbit_par_tree_count))
                                                    ? (mbit_tree_struct.size() % mbit_par_tree_count)
                                                    : mbit_par_tree_count);

            shape = { mbit_tree_struct[i * mbit_par_tree_count].mdim.num_ex * cur_mbit_par_tree_count,
                      mbit_tree_struct[i * mbit_par_tree_count].mdim.B_cols };
            mbit_res_struct[i].Res12_z = glm::alloc_ztensor(shape.data(), ZDNN_2D, FP32);

            shape = { mbit_tree_struct[i * mbit_par_tree_count].mdim.num_ex * cur_mbit_par_tree_count,
                      mbit_CD_struct.mdim.D_cols };
            mbit_res_struct[i].Res34_z = glm::alloc_ztensor(shape.data(), ZDNN_2D, FP32);
        }
    }

    void mbit_free_matrics_impl()
    {
        for (uint32_t i = 0; i < mbit_tree_struct.size(); i++) {
            delete[] mbit_tree_struct[i].A_vector;
            delete[] mbit_tree_struct[i].B_vector;
            delete[] mbit_tree_struct[i].E_vector;
        }

        delete[] mbit_CD_struct.C_matrix;
        delete[] mbit_CD_struct.D_vector;

        if (!first_run) {
            glm::zdnn_safe(zdnn_free_ztensor_buffer(C_z), "[ZDNN_MBIT] couldn't free memory for C.");
            glm::zdnn_safe(zdnn_free_ztensor_buffer(D_z), "[ZDNN_MBIT] couldn't free memory for D.");

            for (uint32_t i = 0; i < (mbit_tree_struct.size() + (mbit_par_tree_count - 1)) / mbit_par_tree_count; i++) {
                glm::zdnn_safe(zdnn_free_ztensor_buffer(mbit_res_struct[i].Res12_z),
                               "[ZDNN_MBIT] couldn't free memory for Res12.");
                glm::zdnn_safe(zdnn_free_ztensor_buffer(mbit_res_struct[i].Res34_z),
                               "[ZDNN_MBIT] couldn't free memory for Res34.");
            }

            delete[] preds_loc;
        }
    }

    uint64_t mbit_get_CD_size() const
    {
        uint64_t out = 0;
        out += sizeof(mbit_CD_dim_t);
        out += mbit_CD_struct.mdim.C_rows * mbit_CD_struct.mdim.C_cols * sizeof(float);
        out += mbit_CD_struct.mdim.D_cols * sizeof(float);

        return out;
    }

    uint64_t mbit_get_tree_size(const uint32_t tree_id) const
    {
        uint64_t out = 0;
        out += sizeof(mbit_dim_t);
        out += mbit_tree_struct[tree_id].mdim.A_cols * sizeof(uint32_t);
        out += mbit_tree_struct[tree_id].mdim.B_cols * sizeof(float);
        out += mbit_tree_struct[tree_id].mdim.E_rows * sizeof(float);

        return out;
    }

    void mbit_tree_generate_2D_matrices(const uint32_t tree_id, const uint32_t target_tree_depth)
    {
        uint32_t num_nodes          = (2 << target_tree_depth) - 1;
        uint32_t num_nodes_leaf     = 2 << (target_tree_depth - 1);
        uint32_t num_nodes_internal = num_nodes - num_nodes_leaf;

        num_nodes_internal = (num_nodes_internal / (2 * PAR_COUNT) + 1) * 2 * PAR_COUNT; // helps for fast stp12 & stp5
        // num_nodes_leaf     = ((num_nodes_leaf + PAR_COUNT - 1) / PAR_COUNT) * PAR_COUNT;

        // allocate matrices
        mbit_tree_struct[tree_id].mdim.A_rows = 1;
        mbit_tree_struct[tree_id].mdim.A_cols = num_nodes_internal;
        mbit_tree_struct[tree_id].mdim.B_rows = 1;
        mbit_tree_struct[tree_id].mdim.B_cols = num_nodes_internal;
        mbit_tree_struct[tree_id].mdim.E_rows = num_nodes_leaf;
        mbit_tree_struct[tree_id].mdim.E_cols = 1;

        mbit_tree_struct[tree_id].A_vector = new uint32_t[mbit_tree_struct[tree_id].mdim.A_cols]();
        mbit_tree_struct[tree_id].B_vector = new float[mbit_tree_struct[tree_id].mdim.B_cols]();
        mbit_tree_struct[tree_id].E_vector = new float[mbit_tree_struct[tree_id].mdim.E_rows]();

        // generate tree matrices A, B, E
        uint32_t node_running_idx = 0;
        uint32_t leaf_running_idx = 0;
        for (uint32_t i = 0; i < num_nodes; i++) {
            if (!mbit_node_is_leaf_.at(tree_id).at(i)) {
                mbit_tree_struct[tree_id].A_vector[node_running_idx] = mbit_node_feature_.at(tree_id).at(i);
                mbit_tree_struct[tree_id].B_vector[node_running_idx] = mbit_node_threshold_.at(tree_id).at(i);
                node_running_idx++;
            } else {
                mbit_tree_struct[tree_id].E_vector[leaf_running_idx] = (float)mbit_node_leaf_label_.at(tree_id).at(i);
                leaf_running_idx++;
            }
        }

        if (dbg_) {
            printf(">>DBG: mbit_tree_generate_2D_matrices\n");
            printf("num_nodes: %u num_nodes_leaf: %u, num_nodes_internal: %u --> %u (PAR_COUNT : %d)\n", num_nodes,
                   num_nodes_leaf, num_nodes - num_nodes_leaf, num_nodes_internal, PAR_COUNT);
            // A
            printf("A[0:%u] =", num_nodes_internal - 1);
            for (uint32_t col = 0; col < num_nodes_internal; col++)
                printf(" %u", mbit_tree_struct[tree_id].A_vector[col]);
            printf("\n");
            // B
            printf("B[0:%u] =", num_nodes_internal - 1);
            for (uint32_t col = 0; col < num_nodes_internal; col++)
                printf(" %.6f", mbit_tree_struct[tree_id].B_vector[col]);
            printf("\n");
            // E
            printf("E[0:%u] =", num_nodes_leaf - 1);
            for (uint32_t col = 0; col < num_nodes_leaf; col++)
                printf(" %+.6f", mbit_tree_struct[tree_id].E_vector[col]);
            printf("\n");
        }
    }

    void mbit_init_CD_2D_tensors()
    {
        // C matrix
        shape = { mbit_CD_struct.mdim.C_rows, mbit_CD_struct.mdim.C_cols };
        C_z   = glm::alloc_ztensor(shape.data(), ZDNN_2D, FP32);
        glm::zdnn_safe(zdnn_transform_ztensor(C_z, mbit_CD_struct.C_matrix), "[ZDNN_MBIT] C stickify failed.");

        // D matrix
        shape = { mbit_CD_struct.mdim.D_cols };
        D_z   = glm::alloc_ztensor(shape.data(), ZDNN_1D, FP32);
        glm::zdnn_safe(zdnn_transform_ztensor(D_z, mbit_CD_struct.D_vector), "[ZDNN_MBIT] D stickify failed.");
        if (dbg_) {
            printf(">>DBG: mbit_init_CD_2D_tensors()\n");
            // C
            float* C_dbg = new float[(uint64_t)mbit_CD_struct.mdim.C_rows * mbit_CD_struct.mdim.C_cols];
            glm::zdnn_safe(zdnn_transform_origtensor(C_z, C_dbg), "[ZDNN_MBIT] C_z unstickify failed.");
            for (uint32_t row = 0; row < mbit_CD_struct.mdim.C_rows; row++) {
                printf("C_dbg[%2u,0:%u] =", row, mbit_CD_struct.mdim.C_cols - 1);
                for (uint32_t col = 0; col < mbit_CD_struct.mdim.C_cols; col++)
                    printf(" %2d", (int32_t)C_dbg[row * mbit_CD_struct.mdim.C_cols + col]);
                printf("\n");
            }
            delete[] C_dbg;
            // D
            float* D_dbg = new float[mbit_CD_struct.mdim.D_cols];
            glm::zdnn_safe(zdnn_transform_origtensor(D_z, D_dbg), "[ZDNN_MBIT] D unstickify failed.");
            printf("D_dbg[0:%u] =", mbit_CD_struct.mdim.D_cols - 1);
            for (uint32_t col = 0; col < mbit_CD_struct.mdim.D_cols; col++)
                printf(" %1.0f", D_dbg[col]);
            printf("\n");
            delete[] D_dbg;
        }
    }

    template <bool eq>
    inline void mbit_tree_predict_cpu12(const uint32_t tree_block_id, float* const x, uint32_t cur_mbit_par_tree_count,
                                        const uint32_t num_ft)
    {
#define KMAX (64 / PAR_COUNT)
        uint32_t page_offset
            = ((mbit_tree_struct[tree_block_id * mbit_par_tree_count].mdim.num_ex * cur_mbit_par_tree_count + 31) / 32)
              * 4096;
        uint32_t base_addr     = 0;
        uint32_t output_offset = 0;
        for (uint32_t bi = 0; bi < cur_mbit_par_tree_count; bi++) {
            uint32_t tree_id = tree_block_id * mbit_par_tree_count + bi;
            for (int32_t i = 0; i < mbit_tree_struct[tree_id].mdim.num_ex; i++) {
                uint64_t out_offset_w    = output_offset;
                uint32_t num_column_left = mbit_tree_struct[tree_id].mdim.A_cols / PAR_COUNT;
                for (int32_t j = 0; j < mbit_tree_struct[tree_id].mdim.A_cols; j += 64) {
                    vector unsigned int* a = (vector unsigned int*)&mbit_tree_struct[tree_id].A_vector[j];
                    vector float*        b = (vector float*)&mbit_tree_struct[tree_id].B_vector[j];
                    vec_float16* res12 = (vec_float16*)((unsigned char*)mbit_res_struct[tree_block_id].Res12_z->buffer
                                                        + output_offset);
                    base_addr          = num_ft * i;
                    PREFETCH((void*)a);
                    PREFETCH((void*)b);
                    PREFETCH((void*)res12);

                    uint32_t l = 0;
                    for (int32_t k = 0; k < std::min((int)num_column_left, KMAX); k += 2) {
                        vector unsigned int ft_idx1 = *(a + k);
                        vector unsigned int ft_idx2 = *(a + k + 1);

                        if (!eq) {
                            vec_float32 cmp_res1
                                = vec_cmplt((vector float) { x[base_addr + ft_idx1[0]], x[base_addr + ft_idx1[1]],
                                                             x[base_addr + ft_idx1[2]], x[base_addr + ft_idx1[3]] },
                                            *(b + k))
                                  & (vec_float32) { 0x00003E00, 0x00003E00, 0x00003E00, 0x00003E00 };

                            vec_float32 cmp_res2
                                = vec_cmplt((vector float) { x[base_addr + ft_idx2[0]], x[base_addr + ft_idx2[1]],
                                                             x[base_addr + ft_idx2[2]], x[base_addr + ft_idx2[3]] },
                                            *(b + k + 1))
                                  & (vec_float32) { 0x00003E00, 0x00003E00, 0x00003E00, 0x00003E00 };
                            *(res12 + l++) = vec_pack(cmp_res1, cmp_res2);
                        } else {
                            vec_float32 cmp_res1
                                = vec_cmple((vector float) { x[base_addr + ft_idx1[0]], x[base_addr + ft_idx1[1]],
                                                             x[base_addr + ft_idx1[2]], x[base_addr + ft_idx1[3]] },
                                            *(b + k))
                                  & (vec_float32) { 0x00003E00, 0x00003E00, 0x00003E00, 0x00003E00 };

                            vec_float32 cmp_res2
                                = vec_cmple((vector float) { x[base_addr + ft_idx2[0]], x[base_addr + ft_idx2[1]],
                                                             x[base_addr + ft_idx2[2]], x[base_addr + ft_idx2[3]] },
                                            *(b + k + 1))
                                  & (vec_float32) { 0x00003E00, 0x00003E00, 0x00003E00, 0x00003E00 };
                            *(res12 + l++) = vec_pack(cmp_res1, cmp_res2);
                        }
                    }
                    output_offset += page_offset;
                    num_column_left -= KMAX;
                }
                // base_addr += mbit_tree_struct[tree_id].mdim.num_ft;
                output_offset = out_offset_w + 128;
            }
        }
        mbit_res_struct[tree_block_id].Res12_z->is_transformed = true;
    }

    void mbit_tree_predict_zaiu34(const uint32_t tree_block_id)
    {
        glm::zdnn_safe(zdnn_matmul_op(mbit_res_struct[tree_block_id].Res12_z, C_z, D_z, MATMUL_OP_EQUAL,
                                      mbit_res_struct[tree_block_id].Res34_z),
                       "[ZDNN_MBIT] GEMM2 failed.");
        zdnn_reset_ztensor(mbit_res_struct[tree_block_id].Res12_z);
    }

    inline void mbit_tree_predict_cpu5(const uint32_t tree_block_id, float* res5, uint32_t cur_mbit_par_tree_count)
    {
        uint32_t page_offset
            = ((mbit_tree_struct[tree_block_id * mbit_par_tree_count].mdim.num_ex * cur_mbit_par_tree_count + 31) / 32)
              * 4096;
        uint32_t input_offset = 0;

        for (uint32_t bi = 0; bi < cur_mbit_par_tree_count; bi++) {
            uint32_t tree_id = tree_block_id * mbit_par_tree_count + bi;
            for (int32_t i = 0; i < mbit_tree_struct[tree_id].mdim.num_ex; i++) {
                uint64_t in_offset_w = input_offset;

                [&] {
                    for (int32_t j = 0; j < mbit_CD_struct.mdim.D_cols; j += 64) {
                        vec_float16* res34
                            = (vec_float16*)((unsigned char*)mbit_res_struct[tree_block_id].Res34_z->buffer
                                             + input_offset);
                        float* e = &mbit_tree_struct[tree_id].E_vector[j];
                        PREFETCH((void*)res34);
                        PREFETCH((void*)e);
                        for (int32_t k = 0; k < 8; k++) {
                            vec_float16 res_tmp = *(res34 + k);
                            int         cmpf    = vec_all_eq(res_tmp, (vec_float16) { 0, 0, 0, 0, 0, 0, 0, 0 });
                            if (!cmpf) {
                                if (res_tmp[0] == 0x3E00)
                                    res5[i + bi * mbit_tree_struct[tree_id].mdim.num_ex] = e[k << 3];
                                else if (res_tmp[1] == 0x3E00)
                                    res5[i + bi * mbit_tree_struct[tree_id].mdim.num_ex] = e[(k << 3) + 1];
                                else if (res_tmp[2] == 0x3E00)
                                    res5[i + bi * mbit_tree_struct[tree_id].mdim.num_ex] = e[(k << 3) + 2];
                                else if (res_tmp[3] == 0x3E00)
                                    res5[i + bi * mbit_tree_struct[tree_id].mdim.num_ex] = e[(k << 3) + 3];
                                else if (res_tmp[4] == 0x3E00)
                                    res5[i + bi * mbit_tree_struct[tree_id].mdim.num_ex] = e[(k << 3) + 4];
                                else if (res_tmp[5] == 0x3E00)
                                    res5[i + bi * mbit_tree_struct[tree_id].mdim.num_ex] = e[(k << 3) + 5];
                                else if (res_tmp[6] == 0x3E00)
                                    res5[i + bi * mbit_tree_struct[tree_id].mdim.num_ex] = e[(k << 3) + 6];
                                else
                                    res5[i + bi * mbit_tree_struct[tree_id].mdim.num_ex] = e[(k << 3) + 7];
                                return;
                            }
                        }
                        input_offset += page_offset;
                    }
                }();
                input_offset = in_offset_w + 128;
            }
        }
    }

    void clear_threads()
    {
        std::unique_lock<std::mutex> lock(mtx);

        if (pred_num_threads == 1)
            return;

        for (thread_info_t& p : thread_info_vec)
            p.end = true;

        cond_2.notify_all();

        cond_1.wait(lock, [this] { return threads_started == 0; });

        for (std::thread& thrd : act_thread) {
            if (thrd.joinable()) {
                thrd.join();
            }
        }

        act_thread.clear();
        thread_info_vec.clear();
    }

    // If the number of threads changes all threads will be re-created.
    template <typename I, bool eq> void update_threads(uint32_t num_threads)
    {
        if (pred_num_threads == num_threads)
            return;

        clear_threads();

        std::unique_lock<std::mutex> lock(mtx);

        // set new number of pred_num_threads
        pred_num_threads = num_threads;
        thread_info_vec  = std::vector<thread_info_t>(pred_num_threads);

        for (uint32_t i = 0; i < pred_num_threads - 1; i++)
            act_thread.emplace_back(std::thread(&MBITreeEnsembleModel::act_predict_thread<I, eq>, this, i));

        cond_1.wait(lock, [this] { return (threads_started == (pred_num_threads - 1)); });
    }

    struct mbit_dim_t {
        uint32_t A_rows;
        uint32_t A_cols;
        uint32_t B_rows;
        uint32_t B_cols;
        uint32_t E_rows;
        uint32_t E_cols;
        uint32_t num_ex;
    };

    struct mbit_tree_struct_t {
        mbit_dim_t mdim;
        uint32_t*  A_vector;
        float*     B_vector;
        float*     E_vector;
    };
    std::vector<mbit_tree_struct_t> mbit_tree_struct;

    struct mbit_CD_dim_t {
        uint32_t C_rows;
        uint32_t C_cols;
        uint32_t D_rows;
        uint32_t D_cols;
    };

    struct mbit_CD_struct_t {
        mbit_CD_dim_t mdim;
        float*        C_matrix;
        float*        D_vector;
    };
    mbit_CD_struct_t mbit_CD_struct {};

    zdnn_ztensor* C_z = nullptr;
    zdnn_ztensor* D_z = nullptr;

    struct mbit_res_struct_t {
        zdnn_ztensor* Res12_z;
        zdnn_ztensor* Res34_z;
    };
    std::vector<mbit_res_struct_t> mbit_res_struct {};

    std::vector<uint32_t> shape;

    bool first_run;
    bool dbg_;

    uint32_t mbit_par_tree_count = 0;

    std::vector<std::vector<uint32_t>> mbit_node_id_;
    std::vector<std::vector<bool>>     mbit_node_is_leaf_;
    std::vector<std::vector<float>>    mbit_node_leaf_label_;
    std::vector<std::vector<uint32_t>> mbit_node_feature_;
    std::vector<std::vector<float>>    mbit_node_threshold_;
    std::vector<std::vector<uint32_t>> mbit_node_left_child_;
    std::vector<std::vector<uint32_t>> mbit_node_right_child_;

    uint32_t pred_num_threads;
    uint32_t pred_input_count = 0;
    uint32_t pred_num_ft      = 0;
    float*   pred_x           = nullptr;
    float*   pred_res5        = nullptr;

    struct thread_info_t {
        thread_info_t()
            : start(false)
            , ready(false)
            , end(false)
            , index_start(0)
            , index_end(0)
        {
        }
        std::atomic<bool>     start;       // indicator that thread should start working
        std::atomic<bool>     ready;       // indicator that work is completed
        std::atomic<bool>     end;         // indicator that threads should terminate
        std::atomic<uint32_t> index_start; // division of work: start
        std::atomic<uint32_t> index_end;   // division of work: end
        std::exception_ptr    eptr;        // to capture exception
    };

    std::vector<std::thread>   act_thread;
    std::vector<thread_info_t> thread_info_vec;

    std::mutex              mtx;
    std::condition_variable cond_1;
    std::condition_variable cond_2;
    std::atomic<bool>       exception;
    std::atomic<uint32_t>   threads_started;

    /*=================================================================================================================*/
    /* support */
    /*=================================================================================================================*/
    void rec_analyze_tree(const std::shared_ptr<TreeEnsembleModel> tree_ensemble_model, uint32_t cur_tree_index,
                          uint32_t cur_node_index, uint32_t cur_depth, uint32_t* max_depth, uint32_t* max_ft)
    {
        if (tree_ensemble_model->trees[cur_tree_index]->nodes[cur_node_index].is_leaf) {
            if (cur_depth > *max_depth)
                *max_depth = cur_depth;
        } else {
            if (tree_ensemble_model->trees[cur_tree_index]->nodes[cur_node_index].feature > *max_ft)
                *max_ft = tree_ensemble_model->trees[cur_tree_index]->nodes[cur_node_index].feature;
            rec_analyze_tree(tree_ensemble_model, cur_tree_index,
                             tree_ensemble_model->trees[cur_tree_index]->nodes[cur_node_index].left_child,
                             cur_depth + 1, max_depth, max_ft);
            rec_analyze_tree(tree_ensemble_model, cur_tree_index,
                             tree_ensemble_model->trees[cur_tree_index]->nodes[cur_node_index].right_child,
                             cur_depth + 1, max_depth, max_ft);
        }
    }

    void rec_extend_tree(const uint32_t tree_index, uint32_t cur_node_index, uint32_t parent_node_index,
                         uint32_t cur_depth, const uint32_t target_depth)
    {
        if (mbit_node_is_leaf_.at(tree_index).at(cur_node_index)) {
            if (cur_depth < target_depth) {
                mbit_node_id_.at(tree_index).push_back((uint32_t)(mbit_node_id_.at(tree_index).size()));
                mbit_node_is_leaf_.at(tree_index).push_back(true);
                mbit_node_leaf_label_.at(tree_index).push_back(mbit_node_leaf_label_.at(tree_index).at(cur_node_index));
                mbit_node_feature_.at(tree_index).push_back(0);
                mbit_node_threshold_.at(tree_index).push_back(0.0);
                mbit_node_left_child_.at(tree_index).push_back(0);
                mbit_node_right_child_.at(tree_index).push_back(0);

                mbit_node_id_.at(tree_index).push_back((uint32_t)(mbit_node_id_.at(tree_index).size()));
                mbit_node_is_leaf_.at(tree_index).push_back(true);
                mbit_node_leaf_label_.at(tree_index).push_back(mbit_node_leaf_label_.at(tree_index).at(cur_node_index));
                mbit_node_feature_.at(tree_index).push_back(0);
                mbit_node_threshold_.at(tree_index).push_back(0);
                mbit_node_left_child_.at(tree_index).push_back(0);
                mbit_node_right_child_.at(tree_index).push_back(0);

                mbit_node_is_leaf_.at(tree_index).at(cur_node_index)    = false;
                mbit_node_leaf_label_.at(tree_index).at(cur_node_index) = { 0.0 };
                mbit_node_feature_.at(tree_index).at(cur_node_index)
                    = ((cur_depth > 0) ? mbit_node_feature_.at(tree_index).at(parent_node_index) : 0);
                mbit_node_threshold_.at(tree_index).at(cur_node_index)
                    = ((cur_depth > 0) ? mbit_node_threshold_.at(tree_index).at(parent_node_index) : 0.0);
                mbit_node_left_child_.at(tree_index).at(cur_node_index)  = mbit_node_id_.at(tree_index).size() - 2;
                mbit_node_right_child_.at(tree_index).at(cur_node_index) = mbit_node_id_.at(tree_index).size() - 1;
            }
        }
        if (!mbit_node_is_leaf_.at(tree_index).at(cur_node_index)) {
            rec_extend_tree(tree_index, mbit_node_left_child_.at(tree_index).at(cur_node_index), cur_node_index,
                            cur_depth + 1, target_depth);
            rec_extend_tree(tree_index, mbit_node_right_child_.at(tree_index).at(cur_node_index), cur_node_index,
                            cur_depth + 1, target_depth);
        }
    }

    void rec_assign_nodeids(const uint32_t tree_index, uint32_t cur_node_index, uint32_t new_node_id)
    {
        assert(mbit_node_id_.at(tree_index).size() == ((2 << max_tree_depth) - 1));
        mbit_node_id_.at(tree_index).at(cur_node_index) = new_node_id;
        if (!mbit_node_is_leaf_.at(tree_index).at(cur_node_index)) {
            rec_assign_nodeids(tree_index, mbit_node_left_child_.at(tree_index).at(cur_node_index),
                               2 * new_node_id + 1);
            rec_assign_nodeids(tree_index, mbit_node_right_child_.at(tree_index).at(cur_node_index),
                               2 * new_node_id + 2);
        }
    }

    void remap_by_nodeids(const uint32_t tree_index)
    {
        if (mbit_node_id_.at(tree_index).size() > 0) {
            std::vector<uint32_t> new_node_id(mbit_node_id_.at(tree_index));
            std::vector<bool>     new_node_is_leaf(mbit_node_is_leaf_.at(tree_index));
            std::vector<float>    new_node_leaf_label(mbit_node_leaf_label_.at(tree_index));
            std::vector<uint32_t> new_node_feature(mbit_node_feature_.at(tree_index));
            std::vector<float>    new_node_threshold(mbit_node_threshold_.at(tree_index));
            std::vector<uint32_t> new_node_left_child(mbit_node_left_child_.at(tree_index));
            std::vector<uint32_t> new_node_right_child(mbit_node_right_child_.at(tree_index));

            for (uint32_t i = 0; i < mbit_node_id_.at(tree_index).size(); i++) {
                uint32_t j                                  = new_node_id.at(i);
                mbit_node_id_.at(tree_index).at(j)          = j;
                mbit_node_is_leaf_.at(tree_index).at(j)     = new_node_is_leaf.at(i);
                mbit_node_leaf_label_.at(tree_index).at(j)  = new_node_leaf_label.at(i);
                mbit_node_feature_.at(tree_index).at(j)     = new_node_feature.at(i);
                mbit_node_threshold_.at(tree_index).at(j)   = new_node_threshold.at(i);
                mbit_node_left_child_.at(tree_index).at(j)  = new_node_id.at(new_node_left_child.at(i));
                mbit_node_right_child_.at(tree_index).at(j) = new_node_id.at(new_node_right_child.at(i));
            }
        }
    }

    uint32_t rec_add_node(const std::shared_ptr<TreeEnsembleModel> tree_ensemble_model, uint32_t cur_tree_index,
                          uint32_t cur_node_index, uint32_t cur_depth, uint32_t max_depth)
    {

        uint32_t cur_offset = mbit_node_id_.at(cur_tree_index).size();
        assert(cur_depth <= max_depth);
        mbit_node_id_.at(cur_tree_index).push_back(mbit_node_id_.at(cur_tree_index).size());
        if ((cur_depth < max_depth) && (!tree_ensemble_model->trees[cur_tree_index]->nodes[cur_node_index].is_leaf)) {
            mbit_node_feature_.at(cur_tree_index)
                .push_back(tree_ensemble_model->trees[cur_tree_index]->nodes[cur_node_index].feature);
            mbit_node_threshold_.at(cur_tree_index)
                .push_back(tree_ensemble_model->trees[cur_tree_index]->nodes[cur_node_index].threshold);
            mbit_node_is_leaf_.at(cur_tree_index)
                .push_back(tree_ensemble_model->trees[cur_tree_index]->nodes[cur_node_index].is_leaf);
            mbit_node_leaf_label_.at(cur_tree_index)
                .push_back(tree_ensemble_model->trees[cur_tree_index]->nodes[cur_node_index].leaf_label);
            mbit_node_left_child_.at(cur_tree_index).push_back(0);
            mbit_node_right_child_.at(cur_tree_index).push_back(0);
            uint32_t left_child_offset = rec_add_node(
                tree_ensemble_model, cur_tree_index,
                tree_ensemble_model->trees[cur_tree_index]->nodes[cur_node_index].left_child, cur_depth + 1, max_depth);
            uint32_t right_child_offset
                = rec_add_node(tree_ensemble_model, cur_tree_index,
                               tree_ensemble_model->trees[cur_tree_index]->nodes[cur_node_index].right_child,
                               cur_depth + 1, max_depth);
            mbit_node_left_child_.at(cur_tree_index).at(cur_offset)  = left_child_offset;
            mbit_node_right_child_.at(cur_tree_index).at(cur_offset) = right_child_offset;
        } else {
            mbit_node_feature_.at(cur_tree_index).push_back(0);
            mbit_node_threshold_.at(cur_tree_index).push_back(0.0);
            mbit_node_is_leaf_.at(cur_tree_index).push_back(true);
            float float_val;
            memcpy(&float_val, &cur_node_index, 4);
            mbit_node_leaf_label_.at(cur_tree_index).push_back(float_val);
            mbit_node_left_child_.at(cur_tree_index).push_back(0);
            mbit_node_right_child_.at(cur_tree_index).push_back(0);
        }
        return cur_offset;
    }

    /*=================================================================================================================*/
    /* hybrid */
    /*=================================================================================================================*/
    float* preds_loc     = nullptr;
    bool   zaiu_only     = false;
    bool   node_cmp_type = false;

    void create_data_structures(const std::shared_ptr<TreeEnsembleModel> tree_ensemble_model,
                                std::shared_ptr<glm::DenseDataset>       data)
    {
        mbit_node_id_.resize(num_trees);
        mbit_node_is_leaf_.resize(num_trees);
        mbit_node_leaf_label_.resize(num_trees);
        mbit_node_feature_.resize(num_trees);
        mbit_node_threshold_.resize(num_trees);
        mbit_node_left_child_.resize(num_trees);
        mbit_node_right_child_.resize(num_trees);

        if (zaiu_only) {
            for (uint32_t i = 0; i < num_trees; i++) {
                uint32_t num_tree_nodes = tree_ensemble_model->trees[i]->num_nodes;
                for (uint32_t j = 0; j < num_tree_nodes; j++) {
                    mbit_node_id_.at(i).push_back(j);
                    mbit_node_feature_.at(i).push_back(tree_ensemble_model->trees[i]->nodes[j].feature);
                    mbit_node_threshold_.at(i).push_back(tree_ensemble_model->trees[i]->nodes[j].threshold);
                    mbit_node_is_leaf_.at(i).push_back(tree_ensemble_model->trees[i]->nodes[j].is_leaf);
                    if (tree_ensemble_model->trees[i]->nodes[j].is_leaf) {
                        mbit_node_leaf_label_.at(i).push_back(tree_ensemble_model->trees[i]->nodes[j].leaf_label);
                        mbit_node_left_child_.at(i).push_back(0);
                        mbit_node_right_child_.at(i).push_back(0);
                    } else {
                        mbit_node_leaf_label_.at(i).push_back(0.0);
                        mbit_node_left_child_.at(i).push_back(tree_ensemble_model->trees[i]->nodes[j].left_child);
                        mbit_node_right_child_.at(i).push_back(tree_ensemble_model->trees[i]->nodes[j].right_child);
                    }
                }
                assert(mbit_node_id_.at(i).size() == num_tree_nodes);
            }
            compr_tree_buf_size_ = 0;
        } else {
            for (uint32_t i = 0; i < num_trees; i++)
                rec_add_node(tree_ensemble_model, i, 0, 0, TREE_DEPTH_ZAIU);

            // generate access counts
            std::vector<std::vector<uint32_t>> bin_tree_access_count;
            for (uint32_t i = 0; i < num_trees; i++) {
                std::vector<uint32_t> access_vector(tree_ensemble_model->trees[i]->num_nodes, 0);
                bin_tree_access_count.push_back(access_vector);
            }
            const uint32_t num_ex_use
                = (data->get_num_ex() > 1000) ? 1000 : data->get_num_ex(); // limit to first 1000 examples
            for (uint32_t ex = 0; ex < num_ex_use; ex++)
                for (uint32_t i = 0; i < num_trees; i++)
                    compr_tree_upd_access_counts(tree_ensemble_model, i, data->get_data().val, data->get_num_ft(), ex,
                                                 &(bin_tree_access_count[i]));

            uint32_t init_buf_size = 2;
            for (uint32_t i = 0; i < num_trees; i++)
                init_buf_size += 5 * tree_ensemble_model->trees[i]->num_nodes; // overdimensioned - adjusted later

            compr_tree_vector_.resize(init_buf_size);
            compr_tree_buf_ = compr_tree_vector_.data();

            uint32_t buf_free_offset = 2;

            for (uint32_t i = 0; i < num_trees; i++) {
                for (uint32_t j = 0; j < mbit_node_id_.at(i).size(); j++) {
                    if (mbit_node_is_leaf_.at(i).at(j)) {
                        uint32_t node_index;
                        memcpy(&node_index, &(mbit_node_leaf_label_.at(i).at(j)), 4);
                        memcpy(&(mbit_node_leaf_label_.at(i).at(j)), &buf_free_offset, 4);
                        if (max_ft < 64)
                            compr_tree_map_node<uint8_t>(tree_ensemble_model, i, node_index,
                                                         &(bin_tree_access_count[i]), 7, false, &buf_free_offset);
                        else if (max_ft < 16384)
                            compr_tree_map_node<uint16_t>(tree_ensemble_model, i, node_index,
                                                          &(bin_tree_access_count[i]), 7, false, &buf_free_offset);
                        else
                            compr_tree_map_node<uint32_t>(tree_ensemble_model, i, node_index,
                                                          &(bin_tree_access_count[i]), 7, false, &buf_free_offset);
                    }
                }
            }
            compr_tree_buf_size_ = buf_free_offset;
            compr_tree_buf_[0]   = 0;
            if (max_ft >= 64)
                compr_tree_buf_[0] = compr_tree_buf_[0] + 4;
            if (max_ft >= 16384)
                compr_tree_buf_[0] = compr_tree_buf_[0] + 4;
        }
    }

    template <typename I, bool eq> void act_predict_thread(uint32_t thr_id)
    {
        bool                         thread_active = true;
        std::unique_lock<std::mutex> llock(mtx); // can also throw exceptions
        threads_started++;
        try {
            cond_1.notify_one();
            while (thread_active) {
                // The thread will start working after thread_info_vec[thr_id].start is set to true.
                cond_2.wait(llock, [this, thr_id] {
                    if (!thread_info_vec[thr_id].start) {
                        if (thread_info_vec[thr_id].end) {
                            return true;
                        }
                        return false;
                    } else {
                        thread_info_vec[thr_id].start = false;
                        return true;
                    }
                });
                llock.unlock();
                if (thread_info_vec[thr_id].end) {
                    thread_active = false;
                }
                if (thread_active) {
                    predict_impl<I, eq>(thread_info_vec[thr_id].index_start, thread_info_vec[thr_id].index_end);
                    llock.lock();
                    // An indication for the main thread that the work is done.
                    thread_info_vec[thr_id].ready = true;
                    cond_1.notify_one();
                }
            }
            llock.lock();
            thread_info_vec[thr_id].ready = true;
            threads_started--;
            llock.unlock();
            cond_1.notify_one();
            // All exceptions should be caught and transferred to the main thread.
        } catch (...) {
            llock.lock();
            exception = true;
            threads_started--;
            thread_info_vec[thr_id].ready = true;
            thread_info_vec[thr_id].eptr  = std::current_exception();
            llock.unlock();
            cond_1.notify_one();
        }
    }

    template <typename I, bool eq> void predict_impl(uint32_t start_val, uint32_t end_val)
    {
        uint32_t tree_count = mbit_tree_struct.size();
        for (int32_t i = start_val; i < end_val; i++) {
            uint32_t cur_par_tree_count
                = ((((tree_count % mbit_par_tree_count) > 0) && (i == tree_count / mbit_par_tree_count))
                       ? (tree_count % mbit_par_tree_count)
                       : mbit_par_tree_count);
            mbit_tree_predict_cpu12<eq>(i, pred_x, cur_par_tree_count, pred_num_ft);
            mbit_tree_predict_zaiu34(i);
            mbit_tree_predict_cpu5(i, &(pred_res5[i * pred_input_count * mbit_par_tree_count]), cur_par_tree_count);

            if (!zaiu_only) {
                for (int32_t ex = 0; ex < pred_input_count; ex++) {
                    float* in = pred_x + pred_num_ft * ex;
                    for (uint32_t t = i * mbit_par_tree_count; t < i * mbit_par_tree_count + cur_par_tree_count; t++) {
                        uint32_t cur_node_index              = ((uint32_t*)pred_res5)[t * pred_input_count + ex];
                        pred_res5[t * pred_input_count + ex] = compr_tree_predict<I, eq>(cur_node_index, in);
                    }
                }
            }
        }
    }

    template <typename I, bool eq>
    void aggregate_impl(glm::DenseDataset* const data, double* preds, bool prob, uint32_t num_threads = 1,
                        uint32_t test_data_offset = 0, uint32_t test_data_size = 0)
    {
        uint64_t n_mbi_trees = mbit_tree_struct.size();
        uint32_t cur_num_ex  = test_data_size; // data->get_num_ex();
        uint32_t num_ft      = data->get_num_ft();
        float*   x           = data->get_data().val + test_data_offset * num_ft; // data->get_data().val;

        const uint32_t a[3]    = { 2, 3, 6 };
        const uint32_t b[11]   = { 2, 3, 6, 12, 24, 48, 96, 192, 384, 768, 1536 };
        const uint16_t p[4224] = {
            1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,
            1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,
            1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,
            1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,
            1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,
            1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,
            1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,
            1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,
            1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,
            1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,
            1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,
            1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,
            1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,
            1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,
            1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,
            1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,
            1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,
            1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,
            1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,
            1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,
            1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,    1,
            1,    1,    1,    1,    1,    1,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,
            4,    4,    4,    4,    4,    4,    4,    2,    2,    2,    1,    1,    4,    4,    4,    4,    4,    4,
            4,    2,    2,    1,    1,    1,    4,    4,    4,    4,    4,    4,    4,    2,    2,    1,    1,    1,
            4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,
            4,    2,    2,    2,    1,    1,    4,    4,    4,    4,    4,    4,    4,    2,    2,    1,    1,    1,
            4,    4,    4,    4,    4,    4,    4,    2,    1,    1,    1,    1,    4,    4,    4,    4,    4,    4,
            4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    2,    2,    2,    2,    1,    1,
            4,    4,    4,    4,    4,    4,    2,    2,    2,    1,    1,    1,    4,    4,    4,    4,    4,    4,
            4,    2,    1,    1,    1,    1,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,
            4,    4,    4,    4,    4,    4,    2,    2,    2,    1,    1,    1,    4,    4,    4,    4,    4,    4,
            2,    2,    1,    1,    1,    1,    4,    4,    4,    4,    4,    4,    4,    2,    1,    1,    1,    1,
            4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,
            3,    2,    2,    2,    1,    1,    4,    4,    4,    4,    4,    4,    2,    2,    1,    1,    1,    1,
            4,    4,    4,    4,    4,    4,    3,    2,    1,    1,    1,    1,    4,    4,    4,    4,    4,    4,
            4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    3,    3,    2,    2,    2,    1,    1,
            4,    4,    4,    4,    4,    3,    3,    1,    1,    1,    1,    1,    4,    4,    4,    4,    4,    3,
            3,    1,    1,    1,    1,    1,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    2,    4,
            4,    4,    4,    4,    4,    3,    2,    2,    2,    2,    2,    2,    4,    4,    4,    4,    4,    3,
            2,    1,    1,    1,    1,    1,    4,    4,    4,    4,    4,    3,    3,    1,    1,    1,    1,    1,
            4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    4,    3,    2,
            2,    2,    1,    1,    1,    1,    4,    4,    4,    4,    3,    3,    1,    1,    1,    1,    1,    1,
            4,    4,    4,    4,    3,    3,    1,    1,    1,    1,    1,    1,    8,    8,    8,    8,    8,    8,
            8,    8,    8,    8,    8,    8,    8,    8,    8,    8,    8,    8,    4,    4,    4,    2,    2,    1,
            8,    8,    8,    8,    8,    8,    4,    3,    3,    2,    1,    1,    8,    8,    8,    8,    8,    8,
            4,    4,    2,    2,    1,    1,    8,    8,    8,    8,    8,    8,    8,    8,    8,    8,    8,    8,
            8,    8,    8,    8,    8,    8,    4,    4,    4,    2,    2,    1,    8,    8,    8,    8,    8,    8,
            4,    3,    2,    2,    1,    1,    8,    8,    8,    8,    8,    8,    4,    3,    2,    2,    1,    1,
            8,    8,    8,    8,    8,    8,    8,    8,    8,    8,    8,    7,    8,    8,    8,    8,    8,    8,
            4,    4,    4,    2,    2,    1,    8,    8,    8,    8,    8,    4,    4,    3,    2,    2,    1,    1,
            8,    8,    8,    8,    8,    8,    4,    5,    2,    2,    1,    1,    8,    8,    8,    8,    8,    8,
            8,    8,    8,    8,    8,    8,    8,    8,    8,    8,    8,    4,    4,    4,    4,    2,    2,    1,
            8,    8,    8,    8,    8,    4,    4,    3,    2,    1,    1,    1,    8,    8,    8,    8,    8,    4,
            4,    2,    2,    1,    1,    1,    8,    8,    8,    8,    8,    8,    8,    8,    8,    8,    8,    8,
            8,    8,    8,    8,    8,    4,    4,    4,    4,    2,    1,    1,    8,    8,    8,    8,    8,    5,
            3,    3,    2,    1,    1,    1,    8,    8,    8,    8,    8,    4,    4,    3,    2,    1,    1,    1,
            8,    8,    8,    8,    8,    8,    8,    8,    8,    8,    8,    8,    8,    8,    8,    8,    6,    6,
            5,    4,    4,    2,    1,    1,    8,    8,    8,    8,    6,    6,    3,    2,    1,    1,    1,    1,
            8,    8,    8,    8,    6,    4,    2,    2,    2,    1,    1,    1,    8,    8,    8,    8,    8,    8,
            8,    8,    8,    8,    8,    8,    8,    8,    8,    8,    6,    4,    4,    4,    2,    2,    2,    2,
            8,    8,    8,    7,    6,    5,    3,    2,    1,    1,    1,    1,    8,    8,    8,    7,    6,    5,
            2,    2,    1,    1,    1,    1,    8,    8,    8,    8,    8,    8,    8,    8,    8,    8,    4,    8,
            8,    8,    8,    6,    5,    5,    5,    2,    2,    2,    1,    2,    8,    8,    8,    6,    5,    3,
            3,    1,    1,    1,    1,    1,    8,    8,    8,    6,    5,    3,    2,    1,    1,    1,    1,    1,
            16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   8,
            8,    4,    4,    4,    2,    2,    16,   16,   16,   16,   16,   8,    7,    5,    3,    3,    2,    1,
            16,   16,   16,   16,   16,   8,    8,    7,    3,    3,    3,    1,    16,   16,   16,   16,   16,   16,
            16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   8,    8,    8,    4,    2,    2,    2,
            16,   16,   16,   16,   16,   8,    8,    5,    4,    2,    2,    1,    16,   16,   16,   16,   16,   8,
            8,    4,    3,    3,    3,    1,    16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   8,    16,
            16,   16,   16,   16,   8,    8,    8,    8,    4,    4,    2,    2,    16,   16,   16,   16,   16,   8,
            6,    5,    4,    2,    2,    1,    16,   16,   16,   16,   8,    8,    6,    4,    3,    3,    1,    1,
            16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   8,    8,
            8,    8,    4,    4,    2,    2,    16,   16,   16,   16,   8,    8,    7,    5,    3,    2,    1,    1,
            16,   16,   16,   16,   8,    8,    7,    5,    3,    2,    2,    1,    16,   16,   16,   16,   16,   16,
            16,   16,   16,   16,   11,   16,   16,   16,   16,   16,   8,    8,    8,    4,    4,    4,    2,    2,
            16,   16,   16,   16,   8,    7,    6,    4,    2,    2,    1,    1,    16,   16,   16,   16,   8,    7,
            7,    3,    3,    2,    1,    1,    16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   10,   16,
            16,   16,   16,   11,   11,   10,   8,    8,    4,    4,    2,    1,    16,   16,   16,   12,   11,   7,
            6,    2,    2,    1,    1,    1,    16,   16,   16,   12,   11,   7,    3,    3,    2,    1,    1,    1,
            16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   14,   10,   10,   9,
            9,    9,    4,    2,    2,    2,    16,   16,   13,   12,   7,    5,    4,    2,    2,    2,    2,    1,
            16,   16,   14,   11,   7,    5,    3,    3,    2,    1,    1,    1,    16,   16,   16,   16,   16,   16,
            16,   16,   16,   16,   8,    16,   16,   16,   13,   11,   9,    9,    4,    4,    2,    2,    2,    2,
            16,   16,   13,   11,   6,    6,    2,    2,    1,    1,    1,    1,    16,   16,   13,   11,   5,    3,
            3,    2,    1,    1,    1,    1,    32,   32,   32,   32,   32,   32,   32,   32,   32,   22,   32,   32,
            32,   32,   32,   32,   16,   16,   16,   9,    8,    4,    2,    2,    32,   32,   32,   32,   16,   15,
            10,   6,    5,    4,    2,    2,    32,   32,   32,   32,   16,   16,   11,   6,    6,    6,    2,    2,
            32,   32,   32,   32,   32,   32,   32,   32,   32,   27,   22,   23,   32,   32,   32,   16,   16,   16,
            8,    8,    8,    4,    4,    2,    32,   32,   32,   16,   16,   15,   10,   6,    5,    4,    2,    2,
            32,   32,   32,   16,   16,   12,   14,   6,    6,    4,    2,    2,    32,   32,   32,   32,   32,   32,
            32,   32,   26,   32,   32,   32,   32,   32,   32,   32,   16,   16,   16,   8,    8,    4,    4,    2,
            32,   32,   32,   16,   16,   12,   8,    6,    4,    4,    2,    2,    32,   32,   32,   16,   16,   12,
            8,    6,    6,    4,    2,    2,    32,   32,   32,   32,   32,   32,   32,   32,   32,   32,   17,   22,
            32,   32,   32,   16,   16,   16,   16,   8,    9,    4,    4,    2,    32,   32,   25,   16,   16,   13,
            10,   9,    4,    2,    2,    1,    32,   32,   32,   16,   17,   14,   7,    6,    4,    2,    2,    1,
            32,   32,   32,   32,   32,   32,   32,   32,   32,   32,   32,   32,   32,   32,   32,   16,   16,   16,
            16,   16,   8,    4,    4,    2,    32,   32,   32,   16,   12,   13,   9,    4,    4,    2,    1,    1,
            32,   32,   32,   16,   15,   13,   6,    6,    5,    2,    2,    1,    32,   32,   32,   32,   32,   32,
            28,   32,   32,   32,   24,   17,   32,   32,   29,   23,   20,   19,   16,   8,    8,    4,    4,    2,
            32,   32,   29,   18,   13,   9,    9,    4,    2,    2,    1,    1,    32,   32,   22,   19,   14,   6,
            7,    5,    2,    2,    2,    2,    32,   32,   32,   32,   32,   32,   32,   32,   32,   32,   16,   32,
            32,   28,   21,   20,   19,   18,   18,   8,    4,    4,    4,    4,    32,   28,   23,   13,   9,    9,
            4,    2,    2,    2,    2,    2,    32,   29,   24,   14,   10,   7,    5,    4,    2,    2,    2,    2,
            32,   32,   32,   32,   32,   32,   32,   32,   32,   32,   24,   28,   32,   24,   21,   19,   19,   19,
            4,    4,    2,    2,    2,    1,    32,   24,   21,   13,   9,    4,    4,    2,    2,    2,    2,    1,
            32,   26,   21,   13,   7,    7,    4,    2,    2,    1,    1,    1,    64,   64,   64,   64,   64,   64,
            64,   64,   51,   45,   64,   64,   64,   64,   64,   32,   32,   32,   16,   16,   8,    8,    4,    2,
            64,   64,   64,   32,   30,   20,   15,   10,   10,   4,    4,    2,    64,   64,   64,   32,   29,   20,
            12,   12,   7,    7,    3,    2,    64,   64,   64,   64,   64,   64,   64,   64,   36,   53,   44,   42,
            64,   64,   32,   32,   32,   32,   16,   16,   11,   4,    2,    2,    64,   64,   34,   32,   23,   20,
            19,   8,    8,    4,    4,    2,    64,   64,   32,   32,   32,   20,   12,   12,   8,    4,    4,    3,
            64,   64,   64,   64,   64,   64,   64,   64,   64,   64,   64,   42,   64,   64,   34,   32,   32,   32,
            16,   11,   8,    8,    4,    2,    64,   64,   33,   32,   23,   20,   10,   8,    8,    4,    4,    2,
            64,   64,   33,   32,   23,   17,   12,   12,   7,    4,    4,    2,    64,   64,   64,   64,   64,   64,
            64,   64,   64,   64,   64,   30,   64,   64,   33,   32,   32,   16,   16,   16,   8,    8,    4,    2,
            64,   64,   32,   32,   29,   19,   8,    8,    4,    4,    2,    1,    64,   64,   32,   32,   22,   15,
            12,   9,    5,    4,    3,    2,    64,   64,   64,   64,   64,   64,   64,   64,   64,   57,   34,   19,
            64,   64,   33,   36,   32,   16,   16,   16,   8,    8,    4,    4,    64,   64,   33,   29,   20,   18,
            8,    8,    4,    2,    2,    2,    64,   64,   32,   28,   19,   14,   12,   11,   4,    4,    2,    2,
            64,   64,   64,   64,   64,   64,   64,   64,   35,   64,   33,   19,   64,   47,   33,   39,   38,   35,
            17,   16,   8,    8,    4,    4,    64,   56,   42,   26,   18,   18,   8,    4,    4,    2,    2,    1,
            64,   54,   40,   20,   14,   14,   11,   4,    4,    3,    3,    1,    64,   64,   64,   64,   64,   64,
            64,   64,   64,   64,   64,   64,   56,   46,   40,   37,   36,   35,   16,   8,    8,    4,    8,    34,
            53,   46,   27,   18,   17,   8,    8,    4,    4,    2,    2,    2,    54,   46,   28,   19,   14,   10,
            7,    7,    4,    3,    1,    3,    64,   64,   64,   64,   64,   64,   64,   64,   64,   24,   48,   60,
            48,   42,   39,   38,   37,   8,    8,    4,    4,    2,    2,    36,   48,   42,   25,   18,   10,   8,
            4,    2,    2,    2,    2,    1,    50,   42,   26,   14,   14,   8,    4,    4,    2,    2,    1,    1,
            128,  128,  128,  128,  128,  128,  128,  128,  108,  100,  49,   65,   128,  128,  64,   64,   64,   32,
            32,   16,   11,   11,   5,    4,    128,  128,  64,   52,   41,   39,   20,   20,   11,   8,    4,    2,
            128,  128,  64,   64,   41,   24,   24,   14,   9,    9,    6,    4,    128,  128,  128,  128,  128,  128,
            128,  91,   96,   128,  60,   77,   128,  67,   64,   66,   64,   32,   32,   22,   11,   8,    8,    8,
            128,  65,   76,   49,   40,   38,   20,   11,   11,   8,    4,    3,    128,  64,   65,   59,   41,   30,
            24,   18,   9,    9,    4,    2,    128,  128,  128,  128,  128,  128,  128,  128,  86,   128,  74,   66,
            128,  66,   64,   64,   64,   32,   17,   34,   16,   8,    4,    4,    128,  67,   64,   44,   38,   17,
            17,   11,   8,    8,    4,    2,    128,  64,   64,   44,   34,   24,   18,   9,    9,    6,    4,    2,
            128,  128,  128,  128,  128,  128,  128,  77,   108,  67,   59,   46,   128,  64,   65,   64,   64,   32,
            32,   16,   16,   8,    8,    5,    128,  64,   47,   41,   37,   37,   16,   8,    8,    4,    4,    2,
            128,  70,   68,   47,   31,   24,   18,   9,    9,    6,    3,    2,    128,  128,  128,  128,  128,  94,
            128,  99,   80,   66,   50,   29,   68,   66,   71,   65,   64,   32,   22,   16,   16,   8,    8,    3,
            64,   66,   58,   38,   37,   16,   8,    8,    4,    2,    2,    2,    72,   66,   58,   54,   29,   23,
            13,   8,    6,    4,    4,    2,    128,  128,  128,  128,  128,  128,  128,  111,  117,  65,   33,   17,
            88,   89,   80,   76,   71,   32,   32,   16,   16,   8,    4,    2,    82,   60,   54,   36,   35,   16,
            8,    8,    4,    4,    2,    2,    106,  90,   55,   29,   23,   23,   9,    8,    4,    5,    2,    1,
            128,  128,  128,  128,  128,  128,  128,  128,  64,   128,  128,  128,  87,   81,   76,   72,   71,   32,
            16,   16,   8,    8,    8,    65,   88,   51,   36,   35,   16,   8,    8,    4,    4,    4,    4,    4,
            91,   55,   38,   28,   23,   16,   8,    8,    5,    5,    5,    4,    128,  128,  128,  128,  128,  128,
            128,  128,  76,   111,  120,  125,  84,   78,   76,   74,   16,   16,   8,    8,    8,    4,    69,   69,
            55,   50,   35,   19,   16,   8,    8,    4,    2,    4,    2,    2,    84,   53,   28,   23,   14,   8,
            8,    6,    3,    2,    1,    2,    256,  256,  256,  256,  256,  128,  256,  237,  256,  183,  137,  133,
            256,  128,  131,  128,  65,   44,   46,   26,   16,   8,    10,   22,   256,  128,  112,  80,   60,   40,
            32,   22,   22,   8,    5,    4,    256,  147,  91,   94,   60,   48,   31,   21,   18,   8,    6,    6,
            256,  256,  256,  256,  256,  256,  252,  216,  256,  154,  137,  93,   140,  136,  130,  129,  72,   70,
            45,   26,   22,   22,   13,   26,   140,  128,  101,  78,   48,   34,   22,   22,   13,   8,    4,    5,
            256,  149,  91,   63,   60,   48,   23,   18,   13,   8,    6,    6,    256,  256,  256,  256,  256,  256,
            256,  152,  132,  134,  93,   75,   129,  128,  128,  128,  71,   46,   32,   33,   16,   16,   8,    26,
            132,  128,  123,  80,   40,   32,   22,   22,   16,   8,    4,    2,    147,  140,  90,   62,   59,   47,
            21,   18,   13,   8,    5,    5,    256,  256,  256,  256,  256,  256,  256,  160,  129,  101,  62,   39,
            130,  128,  129,  64,   68,   69,   32,   32,   16,   16,   8,    26,   130,  128,  112,  77,   34,   33,
            16,   13,   8,    4,    4,    2,    146,  91,   91,   59,   47,   31,   21,   18,   11,   8,    4,    2,
            256,  256,  256,  256,  256,  256,  256,  186,  134,  87,   45,   21,   132,  138,  133,  130,  65,   68,
            32,   32,   16,   16,   4,    26,   128,  115,  77,   74,   32,   16,   13,   8,    8,    4,    4,    2,
            132,  90,   61,   58,   46,   31,   19,   12,   8,    8,    4,    2,    256,  256,  256,  256,  256,  256,
            217,  256,  130,  71,   35,   47,   172,  159,  149,  142,  64,   64,   32,   26,   16,   8,    16,   26,
            115,  104,  72,   71,   32,   22,   16,   13,   8,    4,    4,    2,    118,  77,   57,   46,   45,   29,
            16,   16,   4,    4,    4,    2,    256,  256,  256,  256,  256,  256,  256,  192,  256,  256,  256,  256,
            160,  150,  146,  142,  43,   32,   32,   16,   8,    16,   64,   64,   104,  72,   70,   68,   32,   16,
            13,   8,    8,    8,    8,    32,   109,  75,   48,   30,   27,   26,   26,   10,   6,    6,    6,    4,
            256,  256,  256,  256,  256,  256,  256,  144,  234,  250,  254,  256,  156,  152,  150,  43,   26,   16,
            16,   16,   26,   140,  140,  143,  100,  72,   39,   32,   16,   13,   8,    4,    4,    4,    69,   69,
            77,   57,   55,   30,   27,   19,   10,   6,    4,    4,    2,    45,   500,  500,  500,  500,  500,  487,
            257,  500,  253,  187,  155,  87,   250,  251,  253,  127,  138,  89,   50,   32,   43,   14,   51,   42,
            252,  236,  158,  96,   67,   78,   32,   26,   14,   14,   14,   21,   251,  242,  160,  95,   91,   69,
            35,   38,   16,   13,   7,    6,    500,  500,  500,  500,  500,  254,  378,  303,  170,  104,  179,  74,
            255,  256,  139,  134,  137,  88,   64,   32,   23,   28,   43,   28,   255,  227,  157,  94,   64,   56,
            43,   32,   18,   18,   9,    21,   291,  160,  149,  110,  94,   45,   41,   22,   23,   16,   13,   4,
            500,  500,  500,  500,  500,  500,  500,  259,  253,  126,  95,   93,   254,  252,  140,  135,  88,   88,
            52,   51,   32,   21,   51,   42,   252,  214,  120,  79,   65,   64,   32,   26,   14,   7,    5,    25,
            255,  182,  116,  112,  61,   41,   35,   35,   16,   13,   7,    7,    500,  500,  500,  500,  500,  500,
            273,  500,  169,  125,  95,   39,   250,  254,  254,  135,  88,   86,   36,   28,   23,   18,   14,   28,
            253,  218,  151,  66,   66,   32,   21,   14,   9,    6,    7,    21,   194,  209,  116,  92,   60,   38,
            35,   22,   16,   8,    9,    5,    500,  500,  500,  500,  373,  500,  368,  500,  132,  125,  127,  114,
            254,  253,  255,  130,  86,   85,   50,   25,   23,   28,   14,   25,   218,  205,  144,  67,   42,   25,
            21,   21,   9,    5,    7,    3,    224,  211,  113,  90,   53,   37,   28,   22,   9,    8,    4,    4,
            500,  500,  500,  500,  500,  401,  364,  268,  132,  89,   109,  87,   310,  289,  286,  126,  126,  84,
            50,   25,   25,   10,   10,   25,   195,  140,  137,  136,  32,   25,   25,   21,   14,   5,    5,    21,
            152,  112,  109,  58,   52,   28,   27,   20,   19,   19,   3,    3,    500,  500,  500,  500,  426,  256,
            384,  420,  431,  455,  455,  431,  298,  284,  277,  276,  85,   42,   42,   64,   64,   252,  125,  125,
            142,  137,  63,   42,   25,   21,   18,   9,    9,    5,    64,   64,   141,  108,  88,   60,   32,   30,
            30,   15,   9,    16,   8,    28,   500,  500,  500,  500,  500,  257,  384,  499,  489,  492,  499,  499,
            294,  292,  84,   50,   42,   23,   25,   18,   269,  273,  273,  280,  139,  76,   63,   32,   25,   14,
            7,    5,    5,    8,    135,  135,  112,  89,   58,   59,   28,   23,   11,   8,    8,    4,    4,    67,
            1000, 1000, 1000, 1000, 582,  856,  505,  509,  507,  316,  118,  92,   512,  507,  288,  267,  177,  105,
            86,   56,   46,   24,   72,   73,   444,  316,  188,  159,  126,  64,   63,   51,   26,   13,   42,   44,
            444,  321,  192,  187,  108,  70,   70,   32,   30,   27,   12,   34,   1000, 1000, 1000, 1000, 761,  795,
            492,  511,  225,  115,  92,   77,   507,  501,  259,  279,  172,  86,   103,  56,   28,   28,   63,   72,
            460,  314,  189,  131,  87,   64,   86,   28,   28,   14,   42,   42,   472,  248,  191,  184,  108,  70,
            44,   40,   25,   18,   9,    34,   1000, 1000, 1000, 1000, 1000, 515,  508,  507,  214,  114,  92,   92,
            505,  502,  275,  267,  175,  130,  130,  39,   36,   72,   46,   72,   464,  318,  188,  131,  130,  64,
            51,   36,   18,   14,   42,   42,   431,  244,  190,  123,  109,  70,   75,   32,   21,   13,   9,    39,
            1000, 1000, 1000, 1000, 1000, 764,  501,  507,  206,  112,  89,   93,   503,  501,  273,  265,  176,  131,
            64,   56,   28,   72,   63,   56,   440,  302,  128,  126,  63,   51,   36,   25,   10,   10,   42,   42,
            445,  190,  186,  121,  107,  59,   39,   26,   16,   16,   8,    6,    1000, 1000, 1000, 1000, 1000, 1000,
            502,  510,  205,  152,  135,  187,  511,  510,  260,  262,  130,  85,   84,   42,   36,   20,   56,   100,
            405,  285,  128,  85,   64,   50,   28,   18,   10,   10,   5,    50,   233,  225,  181,  151,  70,   64,
            44,   21,   14,   13,   7,    4,    1000, 1000, 1000, 1000, 765,  675,  507,  427,  205,  65,   61,   60,
            576,  570,  557,  257,  100,  126,  84,   56,   20,   20,   50,   50,   280,  273,  125,  84,   63,   28,
            28,   25,   10,   5,    9,    25,   222,  179,  120,  118,  59,   60,   40,   40,   22,   7,    6,    29,
            1000, 1000, 1000, 1000, 511,  768,  885,  963,  910,  963,  963,  963,  572,  563,  554,  128,  102,  72,
            56,   64,   555,  504,  546,  555,  273,  126,  85,   50,   36,   36,   21,   18,   32,   84,   128,  126,
            180,  176,  118,  95,   48,   29,   29,   29,   38,   16,   91,   72,   1000, 1000, 1000, 790,  514,  769,
            963,  946,  984,  997,  993,  997,  580,  168,  100,  72,   84,   42,   24,   546,  546,  546,  546,  546,
            151,  127,  63,   42,   25,   14,   12,   5,    12,   265,  267,  267,  178,  119,  107,  75,   44,   22,
            15,   17,   6,    15,   56,   24,   2000, 2000, 1460, 1462, 1432, 1023, 438,  512,  230,  185,  154,  147,
            1002, 507,  344,  358,  210,  146,  93,   50,   40,   101,  125,  112,  619,  457,  316,  267,  128,  86,
            85,   73,   39,   84,   103,  101,  456,  440,  372,  242,  176,  150,  64,   56,   47,   30,   95,   61,
            2000, 2000, 2000, 1515, 1875, 802,  420,  509,  236,  156,  160,  158,  1003, 502,  356,  346,  210,  145,
            145,  91,   169,  112,  125,  113,  622,  380,  251,  171,  128,  102,  72,   50,   46,   100,  84,   100,
            454,  366,  373,  198,  151,  85,   72,   53,   48,   29,   80,   70,   2000, 2000, 2000, 1991, 1394, 1014,
            424,  510,  238,  168,  156,  161,  1000, 500,  540,  268,  261,  170,  102,  72,   56,   100,  125,  125,
            623,  378,  263,  172,  127,  127,  63,   46,   28,   100,  102,  103,  480,  376,  272,  192,  141,  88,
            65,   42,   38,   28,   66,   72,   2000, 2000, 2000, 2000, 2000, 1007, 353,  1005, 510,  160,  122,  157,
            1000, 506,  533,  543,  262,  148,  100,  100,  170,  100,  100,  125,  606,  581,  263,  130,  72,   63,
            50,   25,   14,   84,   84,   84,   454,  375,  243,  161,  140,  80,   52,   38,   25,   16,   10,   62,
            2000, 2000, 2000, 2000, 2000, 839,  492,  506,  1018, 999,  580,  390,  1080, 511,  342,  262,  129,  113,
            143,  50,   168,  100,  100,  143,  556,  263,  128,  126,  72,   50,   50,   20,   25,   10,   100,  84,
            248,  213,  193,  112,  112,  62,   49,   28,   10,   7,    13,   39,   1235, 2000, 1464, 1242, 1312, 1997,
            417,  1944, 2000, 1750, 1817, 1907, 1090, 1109, 349,  345,  206,  100,  91,   84,   143,  143,  143,  200,
            537,  100,  126,  100,  72,   50,   50,   25,   10,   100,  100,  101,  236,  236,  131,  129,  129,  28,
            42,   21,   31,   47,   105,  47,   2000, 2000, 1511, 1022, 1535, 1820, 1927, 1927, 1927, 1927, 1926, 1819,
            1084, 1103, 256,  169,  169,  127,  128,  1098, 1057, 1092, 1095, 1092, 533,  172,  168,  100,  50,   50,
            20,   64,   260,  250,  250,  250,  296,  229,  205,  112,  80,   105,  57,   102,  32,   167,  151,  266,
            2000, 2000, 2000, 1028, 513,  257,  1891, 1316, 1316, 1316, 1930, 1316, 1142, 200,  168,  92,   92,   257,
            1067, 1057, 1082, 1093, 1078, 1061, 251,  126,  100,  50,   42,   22,   11,   9,    530,  530,  531,  528,
            231,  207,  161,  88,   44,   23,   36,   10,   13,   270,  56,   267
        };

        update_threads<I, eq>(num_threads);

        std::unique_lock<std::mutex> lock(mtx);

        uint32_t index = pv_offset;
        for (uint32_t i = 0; i < 3; i++)
            if (num_threads >= a[i])
                index += 12;
            else
                break;
        for (uint32_t i = 0; i < 11; i++)
            if (cur_num_ex >= b[i])
                index++;
            else
                break;

        uint32_t new_mbit_par_tree_count = p[index];
        if (new_mbit_par_tree_count > num_trees)
            new_mbit_par_tree_count = num_trees;

        uint32_t int_batch_size
            = std::min((uint32_t)32768 / (uint32_t)new_mbit_par_tree_count, cur_num_ex); // #matrix rows < 2^15
        uint32_t num_int_batches = (cur_num_ex + int_batch_size - 1) / int_batch_size;

        for (uint32_t b = 0; b < num_int_batches; b++) {
            float*   b_x     = x + b * int_batch_size * num_ft;
            uint32_t b_count = (((b + 1) == num_int_batches) ? cur_num_ex - (b * int_batch_size) : int_batch_size);
            if (first_run) {
                num_ex = b_count;
                mbit_init_2D_tensors();
                mbit_alloc_2D_res_tensors(num_ex, new_mbit_par_tree_count);
                first_run = false;
                preds_loc = new float[n_mbi_trees * b_count]();
            } else if ((num_ex != b_count) || (mbit_par_tree_count != new_mbit_par_tree_count)) {
                num_ex = b_count;
                mbit_alloc_2D_res_tensors(num_ex, new_mbit_par_tree_count);
                delete[] preds_loc;
                preds_loc = new float[n_mbi_trees * b_count]();
            }

            float* preds_loc_ptr = preds_loc;

            uint32_t end_value = (n_mbi_trees + (mbit_par_tree_count - 1)) / mbit_par_tree_count;

            pred_input_count = b_count;
            pred_num_ft      = num_ft;
            pred_x           = b_x;
            pred_res5        = preds_loc_ptr;

            for (uint32_t i = 0; i < pred_num_threads; i++) {
                thread_info_vec[i].index_start = (i * end_value) / pred_num_threads;
                thread_info_vec[i].index_end   = ((i + 1) * end_value) / pred_num_threads;
                // Tells the other threads to start to work.
                thread_info_vec[i].start = true;
            }

            lock.unlock();
            cond_2.notify_all();

            predict_impl<I, eq>(thread_info_vec[pred_num_threads - 1].index_start,
                                thread_info_vec[pred_num_threads - 1].index_end);
            thread_info_vec[pred_num_threads - 1].ready = true;

            lock.lock();

            // Waiting for the other threads that their work is done.
            cond_1.wait(lock, [this] {
                for (thread_info_t& p : thread_info_vec) {
                    if (p.ready == false) {
                        return false;
                    }
                }
                return true;
            });
            // Resetting the indicator for work completion.
            for (thread_info_t& p : thread_info_vec)
                p.ready = false;

            if (exception) {
                for (thread_info_t& p : thread_info_vec) {
                    if (p.eptr) {
                        std::rethrow_exception(p.eptr);
                    }
                }
            }

            for (int32_t ex = 0; ex < b_count; ex++) {
                for (uint32_t i = 0; i < n_mbi_trees; i++)
                    preds[ex + b * int_batch_size] += preds_loc_ptr[b_count * i + ex];
            }
        }
    }
};

}

#endif
