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
 * Author       : Jan van Lunteren
 *                Thomas Parnell
 *
 * End Copyright
 ********************************************************************/

#ifndef COMPR_TREE_ENSEMBLE_MODEL
#define COMPR_TREE_ENSEMBLE_MODEL

#include "SIMDDefines.hpp"
#include "TreeEnsembleModel.hpp"
#include "SimpleTreeModel.hpp"

namespace tree {

struct ComprTreeEnsembleModel : public Model {

public:
    ComprTreeEnsembleModel()
        : num_classes(2)
        , compr_tree_buf_(nullptr)
        , compr_tree_buf_size_(0)
        , compr_model_type_(0)
        , compr_tree_count_(0)
        , compr_tree_ensemble_type_(0)
    {
    }

    ~ComprTreeEnsembleModel() { }

    void compress(const std::shared_ptr<TreeEnsembleModel> in, const std::shared_ptr<glm::DenseDataset> data)
    {
        task        = in->task;
        num_classes = in->num_classes;

        float*   val    = data->get_data().val;
        uint32_t num_ex = data->get_num_ex();
        uint32_t num_ft = data->get_num_ft();

        std::vector<std::vector<uint32_t>>           node_id;
        std::vector<std::vector<bool>>               node_is_leaf;
        std::vector<std::vector<std::vector<float>>> node_leaf_label;
        std::vector<std::vector<uint32_t>>           node_feature;
        std::vector<std::vector<float>>              node_threshold;
        std::vector<std::vector<uint32_t>>           node_left_child;
        std::vector<std::vector<uint32_t>>           node_right_child;

        for (const auto& tree : in->trees) {
            auto tmp = std::make_shared<SimpleTreeModel>(tree);
            node_id.push_back(tmp->node_id);
            node_is_leaf.push_back(tmp->node_is_leaf);
            node_leaf_label.push_back(tmp->node_leaf_label);
            node_feature.push_back(tmp->node_feature);
            node_threshold.push_back(tmp->node_threshold);
            node_left_child.push_back(tmp->node_left_child);
            node_right_child.push_back(tmp->node_right_child);
        }
        compress_impl(&node_id, &node_is_leaf, &node_leaf_label, &node_feature, &node_threshold, &node_left_child,
                      &node_right_child, val, num_ex, num_ft);
    }

    uint32_t get_num_trees() { return compr_tree_count_; }

    void aggregate(glm::DenseDataset* const data, double* const preds, bool prob, uint32_t num_threads = 1) const
    {
        if (num_classes > 2)
            predict_impl<true>(data->get_data().val, data->get_num_ex(), data->get_num_ft(), preds, num_threads);
        else
            predict_impl<false>(data->get_data().val, data->get_num_ex(), data->get_num_ft(), preds, num_threads);
    }

    void get(tree::Model::Getter& getter) override
    {
        getter.add(*compr_tree_buf_, compr_tree_buf_size_ * sizeof(uint32_t));
        getter.add(task);
        getter.add(num_classes);
    }

    void put(tree::Model::Setter& setter, const uint64_t len) override
    {
        const uint64_t offset_begin = setter.get_offset();

        setter.check_before(len);

        size_t to_read = len - sizeof(snapml::task_t) - sizeof(uint32_t);

        if (0 != (to_read % sizeof(uint32_t)))
            throw std::runtime_error("(de)serialisation error");

        compr_tree_buf_size_ = static_cast<uint32_t>(to_read / sizeof(uint32_t));

        compr_tree_vector_.resize(compr_tree_buf_size_ + CACHE_LINE_SIZE / 4);

        compr_tree_buf_ = compr_tree_vector_.data();
        while (reinterpret_cast<uintptr_t>(compr_tree_buf_) % CACHE_LINE_SIZE)
            compr_tree_buf_++;

        uint8_t* const p = reinterpret_cast<uint8_t*>(compr_tree_buf_);

        setter.get(p, to_read);
        setter.get(&task);
        setter.get(&num_classes);

        setter.check_after(offset_begin, len);

        set_compr_root_params();
    }

    snapml::task_t task;
    uint32_t       num_classes;

private:
    ComprTreeEnsembleModel(const ComprTreeEnsembleModel&) = delete;

    /*=================================================================================================================*/
    /* compressed tree structure definition */
    /*=================================================================================================================*/
    const uint32_t cnode_threshold_offset[3][24] = {
        { 1, 1, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 1, 1, 1, 2, 2, 2, 2 },
        { 1, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 1, 2, 2, 3, 3, 4, 4 },
        { 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 2, 3, 4, 5, 6, 7, 8 }
    };
    const uint32_t cnode_child_ptr_offset[3][24] = {
        { 0, 2, 4, 9, 19, 39, 79, 159, 319, 639, 1279, 2559, 5119, 10239, 20479, 40959, 81919, 2, 3, 4, 6, 7, 8, 9 },
        { 0, 2, 5, 11, 23, 47, 95, 191, 383, 767, 1535, 3071, 6143, 12287, 24575, 49151, 98303, 2, 4, 5, 7, 8, 10, 11 },
        { 0,    3,     7,     15,    31,     63, 127, 255, 511, 1023, 2047, 4095,
          8191, 16383, 32767, 65535, 131071, 3,  5,   7,   9,   11,   13,   15 }
    };
    const uint32_t cnode_size[3][24] = { { 2,    4,     8,     17,    35,     71, 143, 287, 575, 1151, 2303, 4607,
                                           9215, 18431, 36863, 73727, 147455, 4,  6,   8,   11,  13,   15,   17 },
                                         { 2,     4,     9,     19,    39,     79, 159, 319, 639, 1279, 2559, 5119,
                                           10239, 20479, 40959, 81919, 163839, 4,  7,   9,   12,  14,   17,   19 },
                                         { 2,     5,     11,    23,    47,     95, 191, 383, 767, 1535, 3071, 6143,
                                           12287, 24575, 49151, 98303, 196607, 5,  8,   11,  14,  17,   20,   23 } };

#define TPOW(X) (1u << static_cast<uint32_t>(X))

    /*=================================================================================================================*/
    /* functions used for converting binary tree structure into compressed tree structure */
    /*=================================================================================================================*/
    void bin_tree_predict_update_access_counts( // TODO: < or <=
        std::vector<bool>* node_is_leaf, std::vector<uint32_t>* node_feature, std::vector<float>* node_threshold,
        std::vector<uint32_t>* node_left_child, std::vector<uint32_t>* node_right_child, float* in, uint32_t num_ft,
        uint32_t ex, std::vector<uint32_t>* access_count) const
    {
        uint32_t bin_tree_node_index = 0;

        while (!node_is_leaf->at(bin_tree_node_index)) {
            access_count->at(bin_tree_node_index) += 1;
            float val = (reinterpret_cast<float*>(in + num_ft * ex))[node_feature->at(bin_tree_node_index)];
            if (val < node_threshold->at(bin_tree_node_index)) {
                uint32_t left_child = node_left_child->at(bin_tree_node_index);
                bin_tree_node_index = left_child;
            } else {
                uint32_t right_child = node_right_child->at(bin_tree_node_index);
                bin_tree_node_index  = right_child;
            }
        }
        access_count->at(bin_tree_node_index) += 1;
    }

    void rec_analyze_bin_tree(std::vector<bool>* node_is_leaf, std::vector<uint32_t>* node_feature,
                              std::vector<uint32_t>* node_left_child, std::vector<uint32_t>* node_right_child,
                              const uint32_t bin_tree_node_index, uint32_t cur_depth, uint32_t* max_depth,
                              uint32_t* max_ft)
    {
        if (node_is_leaf->at(bin_tree_node_index)) {
            if (cur_depth > *max_depth)
                *max_depth = cur_depth;
        } else {
            if (node_feature->at(bin_tree_node_index) > *max_ft)
                *max_ft = node_feature->at(bin_tree_node_index);
            rec_analyze_bin_tree(node_is_leaf, node_feature, node_left_child, node_right_child,
                                 node_left_child->at(bin_tree_node_index), cur_depth + 1, max_depth, max_ft);
            rec_analyze_bin_tree(node_is_leaf, node_feature, node_left_child, node_right_child,
                                 node_right_child->at(bin_tree_node_index), cur_depth + 1, max_depth, max_ft);
        }
    }

    bool rec_check_bin_tree_depth(std::vector<bool>* node_is_leaf, std::vector<uint32_t>* node_left_child,
                                  std::vector<uint32_t>* node_right_child, const uint32_t bin_tree_node_index,
                                  uint32_t cur_level, uint32_t* tree_depth, uint32_t threshold)
    {
        bool ret_val = true;
        *tree_depth  = cur_level;

        if ((cur_level > threshold) || ((cur_level == threshold) && (!node_is_leaf->at(bin_tree_node_index))))
            ret_val = false;
        else {
            if (!node_is_leaf->at(bin_tree_node_index)) {
                uint32_t left_tree_depth;
                uint32_t right_tree_depth;
                bool     ret_val_left  = rec_check_bin_tree_depth(node_is_leaf, node_left_child, node_right_child,
                                                             node_left_child->at(bin_tree_node_index), cur_level + 1,
                                                             &left_tree_depth, threshold);
                bool     ret_val_right = rec_check_bin_tree_depth(node_is_leaf, node_left_child, node_right_child,
                                                              node_right_child->at(bin_tree_node_index), cur_level + 1,
                                                              &right_tree_depth, threshold);

                ret_val     = ret_val_left && ret_val_right;
                *tree_depth = (left_tree_depth > right_tree_depth ? left_tree_depth : right_tree_depth);
            }
        }
        return ret_val;
    }

    bool select_seq_compressed_node_type(std::vector<bool>* node_is_leaf, std::vector<uint32_t>* node_left_child,
                                         std::vector<uint32_t>* node_right_child, const uint32_t bin_tree_node_index,
                                         std::vector<uint32_t>* bin_tree_access_count, uint32_t par_max_depth,
                                         uint32_t* par_actual_depth, bool* par_leaf_only_cnode,
                                         uint32_t* par_bin_tree_node_indices, const bool seq_skip_leafs,
                                         uint32_t seq_max_length, uint32_t* seq_actual_length,
                                         uint32_t* seq_bin_tree_node_indices, bool* seq_left_right_flags)
    {
        bool select_seq_cnode_type;

        if ((bin_tree_node_index == 0)
            && rec_check_bin_tree_depth(node_is_leaf, node_left_child, node_right_child, 0, 0, par_actual_depth,
                                        par_max_depth)) {

            select_seq_cnode_type = false;
            *par_leaf_only_cnode  = true;

            par_bin_tree_node_indices[0] = bin_tree_node_index;
            for (uint32_t cur_level = 0; cur_level < *par_actual_depth - 1; cur_level++) {
                for (uint32_t k = TPOW(cur_level) - 1; k < TPOW(cur_level + 1) - 1; k++) {
                    uint32_t bnode_index = par_bin_tree_node_indices[k];
                    if (node_is_leaf->at(bnode_index)) {
                        par_bin_tree_node_indices[2 * k + 1] = bnode_index;
                        par_bin_tree_node_indices[2 * k + 2] = bnode_index;
                    } else {
                        par_bin_tree_node_indices[2 * k + 1] = node_left_child->at(bnode_index);
                        par_bin_tree_node_indices[2 * k + 2] = node_right_child->at(bnode_index);
                    }
                }
            }
        } else {
            select_seq_cnode_type = true;

            *seq_actual_length       = 0;
            uint32_t cur_bnode_index = bin_tree_node_index;

            while ((*seq_actual_length < seq_max_length) && (!node_is_leaf->at(cur_bnode_index))) {
                seq_bin_tree_node_indices[*seq_actual_length] = cur_bnode_index;

                uint32_t cur_left_child  = node_left_child->at(cur_bnode_index);
                uint32_t cur_right_child = node_right_child->at(cur_bnode_index);

                if (!seq_skip_leafs || (!node_is_leaf->at(cur_left_child) && !node_is_leaf->at(cur_right_child))) {
                    seq_left_right_flags[*seq_actual_length]
                        = (bin_tree_access_count->at(cur_left_child) < bin_tree_access_count->at(cur_right_child));
                } else {
                    if (!node_is_leaf->at(cur_left_child))
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
        }
        return select_seq_cnode_type;
    }

    template <typename I> uint32_t typename_to_index() const
    {
        return (((std::is_same<I, uint32_t>::value) ? 2 : ((std::is_same<I, uint16_t>::value) ? 1 : 0)));
    }

    template <typename I> uint32_t typename_to_shift() const
    {
        return (((std::is_same<I, uint32_t>::value) ? 0 : (std::is_same<I, uint16_t>::value) ? 16 : 24));
    }

    void set_compr_root_params()
    {
        compr_tree_ensemble_type_ = compr_tree_buf_[0];
        compr_tree_count_         = compr_tree_buf_[1];
        compr_model_type_         = compr_tree_buf_[2];
        num_classes               = compr_tree_buf_[3];
        compr_tree_root_type_.resize(compr_tree_count_);
        compr_tree_root_seq_length_.resize(compr_tree_count_);
        compr_tree_root_feature_vector_.resize(compr_tree_count_);
        compr_tree_root_threshold_vector_.resize(compr_tree_count_);
        compr_tree_root_child_ptr_vector_.resize(compr_tree_count_);
        for (uint32_t t = 0; t < compr_tree_count_; t++) {
            uint32_t to                    = compr_tree_buf_[t + 4];
            uint8_t  cnode_root_type       = (reinterpret_cast<uint8_t*>(&(compr_tree_buf_[to])))[0] & 0x1Fu;
            compr_tree_root_type_[t]       = (cnode_root_type < 17);
            compr_tree_root_seq_length_[t] = (cnode_root_type >= 17) ? (cnode_root_type - (17 - 1)) : cnode_root_type;
            if (compr_tree_ensemble_type_ < 4) {
                compr_tree_root_feature_vector_[t] = &((reinterpret_cast<uint8_t*>(&(compr_tree_buf_[to])))[0]);
                compr_tree_root_threshold_vector_[t]
                    = reinterpret_cast<float*>(&(compr_tree_buf_[to + cnode_threshold_offset[0][cnode_root_type] - 1]));
                compr_tree_root_child_ptr_vector_[t]
                    = &(compr_tree_buf_[to + cnode_child_ptr_offset[0][cnode_root_type] - 1]);
            } else if (compr_tree_ensemble_type_ < 8) {
                compr_tree_root_feature_vector_[t] = &((reinterpret_cast<uint16_t*>(&(compr_tree_buf_[to])))[0]);
                compr_tree_root_threshold_vector_[t]
                    = reinterpret_cast<float*>(&(compr_tree_buf_[to + cnode_threshold_offset[1][cnode_root_type] - 1]));
                compr_tree_root_child_ptr_vector_[t]
                    = &(compr_tree_buf_[to + cnode_child_ptr_offset[1][cnode_root_type] - 1]);
            } else {
                compr_tree_root_feature_vector_[t] = &((reinterpret_cast<uint32_t*>(&(compr_tree_buf_[to])))[0]);
                compr_tree_root_threshold_vector_[t]
                    = reinterpret_cast<float*>(&(compr_tree_buf_[to + cnode_threshold_offset[2][cnode_root_type] - 1]));
                compr_tree_root_child_ptr_vector_[t]
                    = &(compr_tree_buf_[to + cnode_child_ptr_offset[2][cnode_root_type] - 1]);
            }
        }
    }

    template <typename I>
    uint32_t map_on_cnode(std::vector<bool>* node_is_leaf, std::vector<uint32_t>* node_leaf_label_offset,
                          std::vector<uint32_t>* node_feature, std::vector<float>* node_threshold,
                          std::vector<uint32_t>* node_left_child, std::vector<uint32_t>* node_right_child,
                          const uint32_t bin_tree_node_index, std::vector<uint32_t>* bin_tree_access_count,
                          const uint32_t par_max_depth, const uint32_t seq_max_length, const bool seq_skip_leafs,
                          uint32_t* buf_free_offset, const bool align_cnode)
    {
        uint32_t cnode_offset = *buf_free_offset;
        uint8_t  selected_cnode_type;
        if (node_is_leaf->at(bin_tree_node_index)) {
            selected_cnode_type = 0;

            *buf_free_offset = cnode_offset + cnode_size[typename_to_index<I>()][selected_cnode_type];

            (reinterpret_cast<uint8_t*>(&(compr_tree_buf_[cnode_offset])))[0]              = selected_cnode_type;
            *(bool*)(&((reinterpret_cast<uint8_t*>(&(compr_tree_buf_[cnode_offset])))[1])) = true;
            float* cur_threshold_vector                                                    = reinterpret_cast<float*>(
                &(compr_tree_buf_[cnode_offset + cnode_threshold_offset[typename_to_index<I>()][selected_cnode_type]]));

            reinterpret_cast<uint32_t*>(cur_threshold_vector)[0] = node_leaf_label_offset->at(bin_tree_node_index);
        } else {
            uint32_t par_depth;
            bool     par_leaf_only_cnode;
            uint32_t par_bin_tree_node_indices[TPOW(13 - 1) - 1];

            uint32_t seq_length;
            uint32_t seq_bin_tree_node_indices[7];
            bool     seq_left_right_flags[7];

            if (select_seq_compressed_node_type(node_is_leaf, node_left_child, node_right_child, bin_tree_node_index,
                                                bin_tree_access_count, par_max_depth, &par_depth, &par_leaf_only_cnode,
                                                par_bin_tree_node_indices, seq_skip_leafs, seq_max_length, &seq_length,
                                                seq_bin_tree_node_indices, seq_left_right_flags)) {

                selected_cnode_type = (seq_length == 0) ? 0 : (seq_length + 17 - 1);

                if (align_cnode) {
                    while (static_cast<uintptr_t>(compr_tree_buf_[cnode_offset]) % CACHE_LINE_SIZE)
                        cnode_offset++;
                }
                *buf_free_offset = cnode_offset + cnode_size[typename_to_index<I>()][selected_cnode_type];

                *(&((reinterpret_cast<uint8_t*>(&(compr_tree_buf_[cnode_offset])))[0])) = selected_cnode_type;

                I*        cur_feature_vector   = &((reinterpret_cast<I*>(&(compr_tree_buf_[cnode_offset])))[1]);
                float*    cur_threshold_vector = (float*)(&(
                    compr_tree_buf_[cnode_offset
                                    + cnode_threshold_offset[typename_to_index<I>()][selected_cnode_type]]));
                uint32_t* cur_child_ptr_vector
                    = &(compr_tree_buf_[cnode_offset
                                        + cnode_child_ptr_offset[typename_to_index<I>()][selected_cnode_type]]);

                for (uint32_t k = 0; k < seq_length; k++) {
                    cur_feature_vector[k] = node_feature->at(seq_bin_tree_node_indices[k]);
                    if (k < seq_length - 1)
                        cur_feature_vector[k]
                            |= (seq_left_right_flags[k] ? (static_cast<uint32_t>(0x80000000) >> typename_to_shift<I>())
                                                        : 0);
                    cur_threshold_vector[k] = node_threshold->at(seq_bin_tree_node_indices[k]);
                    cur_child_ptr_vector[k]
                        = (seq_left_right_flags[k] ? node_left_child->at(seq_bin_tree_node_indices[k])
                                                   : node_right_child->at(seq_bin_tree_node_indices[k]));
                }
                cur_child_ptr_vector[seq_length]
                    = (!seq_left_right_flags[seq_length - 1]
                           ? node_left_child->at(seq_bin_tree_node_indices[seq_length - 1])
                           : node_right_child->at(seq_bin_tree_node_indices[seq_length - 1]));

                for (uint32_t i = 0; i < seq_length + 1; i++) {
                    uint32_t k = (seq_length - i);
                    if (node_is_leaf->at(cur_child_ptr_vector[k])) {
                        cur_child_ptr_vector[k] = node_leaf_label_offset->at(cur_child_ptr_vector[k]);

                        if (k < seq_length)
                            cur_feature_vector[k] = (cur_feature_vector[k]
                                                     | (static_cast<uint32_t>(0x40000000) >> typename_to_shift<I>()));
                        else
                            cur_feature_vector[seq_length - 1]
                                = (cur_feature_vector[seq_length - 1]
                                   | (static_cast<uint32_t>(0x80000000) >> typename_to_shift<I>()));
                    } else
                        cur_child_ptr_vector[k] = map_on_cnode<I>(
                            node_is_leaf, node_leaf_label_offset, node_feature, node_threshold, node_left_child,
                            node_right_child, cur_child_ptr_vector[k], bin_tree_access_count, par_max_depth,
                            seq_max_length, seq_skip_leafs, buf_free_offset, align_cnode);
                }
            } else {
                selected_cnode_type = par_depth;

                if (align_cnode) {
                    while ((uintptr_t)compr_tree_buf_[cnode_offset] % CACHE_LINE_SIZE)
                        cnode_offset++;
                }
                *buf_free_offset = cnode_offset + cnode_size[typename_to_index<I>()][selected_cnode_type];

                (reinterpret_cast<uint8_t*>(&(compr_tree_buf_[cnode_offset])))[0]              = selected_cnode_type;
                *(bool*)(&((reinterpret_cast<uint8_t*>(&(compr_tree_buf_[cnode_offset])))[1])) = par_leaf_only_cnode;

                I*        cur_feature_vector   = &(((I*)(&(compr_tree_buf_[cnode_offset])))[1]);
                float*    cur_threshold_vector = (float*)(&(
                    compr_tree_buf_[cnode_offset
                                    + cnode_threshold_offset[typename_to_index<I>()][selected_cnode_type]]));
                uint32_t* cur_child_ptr_vector
                    = &(compr_tree_buf_[cnode_offset
                                        + cnode_child_ptr_offset[typename_to_index<I>()][selected_cnode_type]]);

                for (uint32_t k = 0; k < TPOW(par_depth) - 1; k++) {
                    uint32_t bnode_index = par_bin_tree_node_indices[k];
                    if (node_is_leaf->at(bnode_index)) {
                        cur_feature_vector[k]   = cur_feature_vector[(k - 1) / 2];
                        cur_threshold_vector[k] = 0.0;
                    } else {
                        cur_feature_vector[k]   = node_feature->at(bnode_index);
                        cur_threshold_vector[k] = node_threshold->at(bnode_index);
                    }
                }

                if (!par_leaf_only_cnode) {
                    for (uint32_t k = 0; k < TPOW(par_depth - 1); k++) {
                        uint32_t bnode_index = par_bin_tree_node_indices[TPOW(par_depth - 1) - 1 + k];

                        if (node_is_leaf->at(bnode_index)) {
                            if ((k > 0)
                                && (par_bin_tree_node_indices[TPOW(par_depth - 1) - 1 + k]
                                    == par_bin_tree_node_indices[TPOW(par_depth - 1) - 1 + k - 1])) {
                                cur_child_ptr_vector[2 * k]     = cur_child_ptr_vector[k - 1];
                                cur_child_ptr_vector[2 * k + 1] = cur_child_ptr_vector[k - 1];
                            } else {
                                cur_child_ptr_vector[2 * k] = map_on_cnode<I>(
                                    node_is_leaf, node_leaf_label_offset, node_feature, node_threshold, node_left_child,
                                    node_right_child, bnode_index, bin_tree_access_count, par_max_depth, seq_max_length,
                                    seq_skip_leafs, buf_free_offset, align_cnode);
                                cur_child_ptr_vector[2 * k + 1] = cur_child_ptr_vector[2 * k];
                            }
                        } else {
                            uint32_t left_child_index   = node_left_child->at(bnode_index);
                            cur_child_ptr_vector[2 * k] = map_on_cnode<I>(
                                node_is_leaf, node_leaf_label_offset, node_feature, node_threshold, node_left_child,
                                node_right_child, left_child_index, bin_tree_access_count, par_max_depth,
                                seq_max_length, seq_skip_leafs, buf_free_offset, align_cnode);

                            uint32_t right_child_index      = node_right_child->at(bnode_index);
                            cur_child_ptr_vector[2 * k + 1] = map_on_cnode<I>(
                                node_is_leaf, node_leaf_label_offset, node_feature, node_threshold, node_left_child,
                                node_right_child, right_child_index, bin_tree_access_count, par_max_depth,
                                seq_max_length, seq_skip_leafs, buf_free_offset, align_cnode);
                        }
                    }
                } else {
                    for (uint32_t k = 0; k < TPOW(par_depth - 1); k++) {
                        uint32_t bnode_index = par_bin_tree_node_indices[TPOW(par_depth - 1) - 1 + k];

                        if (node_is_leaf->at(bnode_index)) {
                            cur_child_ptr_vector[2 * k]     = node_leaf_label_offset->at(bnode_index);
                            cur_child_ptr_vector[2 * k + 1] = node_leaf_label_offset->at(bnode_index);
                        } else {
                            uint32_t left_child_index = node_left_child->at(bnode_index);
                            // assert(node_is_leaf->at(left_child_index));
                            if (node_is_leaf->at(left_child_index) == false)
                                throw std::runtime_error("compression error");

                            cur_child_ptr_vector[2 * k] = node_leaf_label_offset->at(left_child_index);

                            uint32_t right_child_index = node_right_child->at(bnode_index);
                            // assert(node_is_leaf->at(right_child_index));
                            if (node_is_leaf->at(right_child_index) == false)
                                throw std::runtime_error("compression error");

                            cur_child_ptr_vector[2 * k + 1] = node_leaf_label_offset->at(right_child_index);
                        }
                    }
                }
            }
        }
        return cnode_offset;
    }

    void extend_tree(uint32_t cur_node_index, uint32_t parent_node_index, uint32_t cur_depth, uint32_t target_depth,
                     std::vector<uint32_t>* node_id, std::vector<bool>* node_is_leaf,
                     std::vector<std::vector<float>>* node_leaf_label, std::vector<uint32_t>* node_feature,
                     std::vector<float>* node_threshold, std::vector<uint32_t>* node_left_child,
                     std::vector<uint32_t>* node_right_child)
    {
        if (node_is_leaf->at(cur_node_index)) {
            if (cur_depth < target_depth) {
                node_id->push_back(static_cast<uint32_t>(node_id->size()));
                node_is_leaf->push_back(true);
                node_leaf_label->push_back(node_leaf_label->at(cur_node_index));
                node_feature->push_back(0);
                node_threshold->push_back(0.0);
                node_left_child->push_back(0);
                node_right_child->push_back(0);

                node_id->push_back((uint32_t)(node_id->size()));
                node_is_leaf->push_back(true);
                node_leaf_label->push_back(node_leaf_label->at(cur_node_index));
                node_feature->push_back(0);
                node_threshold->push_back(0);
                node_left_child->push_back(0);
                node_right_child->push_back(0);

                node_is_leaf->at(cur_node_index)     = false;
                node_leaf_label->at(cur_node_index)  = std::vector<float> { 0.0 };
                node_feature->at(cur_node_index)     = ((cur_depth > 0) ? node_feature->at(parent_node_index) : 0);
                node_threshold->at(cur_node_index)   = ((cur_depth > 0) ? node_threshold->at(parent_node_index) : 0.0);
                node_left_child->at(cur_node_index)  = node_id->size() - 2;
                node_right_child->at(cur_node_index) = node_id->size() - 1;
            }
        }
        if (!node_is_leaf->at(cur_node_index)) {
            extend_tree(node_left_child->at(cur_node_index), cur_node_index, cur_depth + 1, target_depth, node_id,
                        node_is_leaf, node_leaf_label, node_feature, node_threshold, node_left_child, node_right_child);
            extend_tree(node_right_child->at(cur_node_index), cur_node_index, cur_depth + 1, target_depth, node_id,
                        node_is_leaf, node_leaf_label, node_feature, node_threshold, node_left_child, node_right_child);
        }
    }

    void compress_impl(std::vector<std::vector<uint32_t>>* node_id, std::vector<std::vector<bool>>* node_is_leaf,
                       std::vector<std::vector<std::vector<float>>>* node_leaf_label,
                       std::vector<std::vector<uint32_t>>*           node_feature,
                       std::vector<std::vector<float>>*              node_threshold,
                       std::vector<std::vector<uint32_t>>*           node_left_child,
                       std::vector<std::vector<uint32_t>>* node_right_child, float* in, uint32_t num_ex,
                       uint32_t num_ft)
    {
        uint32_t node_cmp_type = false;
        for (uint32_t i = 0; i < node_id->at(0).size(); i++) {
            if (node_is_leaf->at(0).at(i)) {
                node_cmp_type = node_feature->at(0).at(i);
                break;
            }
        }
        std::vector<uint32_t> bin_tree_depth;
        uint32_t              max_ft = 0;
        for (uint32_t i = 0; i < node_id->size(); i++) {
            uint32_t max_tree_depth = 0;
            rec_analyze_bin_tree(&(node_is_leaf->at(i)), &(node_feature->at(i)), &(node_left_child->at(i)),
                                 &(node_right_child->at(i)), 0, 0, &max_tree_depth, &max_ft);
            bin_tree_depth.push_back(max_tree_depth);
        }

        for (uint32_t i = 0; i < node_id->size() - 1; i++) {
            for (uint32_t j = i + 1; j < node_id->size(); j++) {
                if (bin_tree_depth.at(i) < bin_tree_depth.at(j)) {
                    node_id->at(i).swap(node_id->at(j));
                    node_is_leaf->at(i).swap(node_is_leaf->at(j));
                    node_leaf_label->at(i).swap(node_leaf_label->at(j));
                    node_feature->at(i).swap(node_feature->at(j));
                    node_threshold->at(i).swap(node_threshold->at(j));
                    node_left_child->at(i).swap(node_left_child->at(j));
                    node_right_child->at(i).swap(node_right_child->at(j));
                    std::swap(bin_tree_depth.at(i), bin_tree_depth.at(j));
                }
            }
        }

        for (uint32_t i = 0; i < node_id->size(); i += PAR_COUNT) {
            uint32_t min_depth = bin_tree_depth.at(i);
            uint32_t max_depth = bin_tree_depth.at(i);
            for (uint32_t j = 1; (j < PAR_COUNT) && ((i + j) < node_id->size()); j++) {
                if (bin_tree_depth.at(i + j) < min_depth)
                    min_depth = bin_tree_depth.at(i + j);
                if (bin_tree_depth.at(i + j) > max_depth)
                    max_depth = bin_tree_depth.at(i + j);
            }
            if ((min_depth != max_depth) && (min_depth < 13)) {
                for (uint32_t j = 0; (j < PAR_COUNT) && ((i + j) < node_id->size()); j++) {
                    if (bin_tree_depth.at(i + j) < max_depth)
                        extend_tree(0, 0, 0, max_depth, &(node_id->at(i + j)), &(node_is_leaf->at(i + j)),
                                    &(node_leaf_label->at(i + j)), &(node_feature->at(i + j)),
                                    &(node_threshold->at(i + j)), &(node_left_child->at(i + j)),
                                    &(node_right_child->at(i + j)));
                }
            }
        }
        std::vector<std::vector<uint32_t>> bin_tree_access_count;
        for (uint32_t i = 0; i < node_id->size(); i++) {
            std::vector<uint32_t> access_vector(node_id->at(i).size(), 0);
            bin_tree_access_count.push_back(access_vector);
        }
        // do not use more than 1000 examples
        const uint32_t num_ex_use = (num_ex > 1000) ? 1000 : num_ex;

        for (uint32_t ex = 0; ex < num_ex_use; ex++)
            for (uint32_t i = 0; i < node_id->size(); i++)
                bin_tree_predict_update_access_counts(
                    &(node_is_leaf->at(i)), &(node_feature->at(i)), &(node_threshold->at(i)), &(node_left_child->at(i)),
                    &(node_right_child->at(i)), in, num_ft, ex, &(bin_tree_access_count[i]));
        uint32_t init_buf_size = 2 * static_cast<uint32_t>(node_id->size()) + 4;
        for (uint32_t i = 0; i < node_id->size(); i++) {
            uint32_t tree_depth;
            if (rec_check_bin_tree_depth(&(node_is_leaf->at(i)), &(node_left_child->at(i)), &(node_right_child->at(i)),
                                         0, 0, &tree_depth, 13 - 1))
                init_buf_size += cnode_size[2][tree_depth]; // overdimensioned, will be reduced later
            else
                init_buf_size += 5 * static_cast<uint32_t>(node_id->at(i).size());

            if (num_classes > 2)
                init_buf_size += static_cast<uint32_t>(node_id->at(i).size())
                                 * num_classes; // overdimensioned, will be reduced later
        }
        compr_tree_vector_.resize(init_buf_size + CACHE_LINE_SIZE / 4);
        compr_tree_buf_ = compr_tree_vector_.data();
        while (reinterpret_cast<uintptr_t>(compr_tree_buf_) % CACHE_LINE_SIZE)
            compr_tree_buf_++;
        compr_tree_buf_[1]       = static_cast<uint32_t>(node_id->size());
        compr_tree_buf_[2]       = 0; // TO BE UPDATED
        compr_tree_buf_[3]       = num_classes;
        uint32_t buf_free_offset = static_cast<uint32_t>(node_id->size()) + 4;
        for (uint32_t i = 0; i < node_id->size(); i++) {
            std::vector<uint32_t> mapped_leaf_node_offset(static_cast<uint32_t>(node_id->at(i).size()));
            for (uint32_t k = 0; k < node_id->at(i).size(); k++) {
                if (node_is_leaf->at(i).at(k)) {
                    if (num_classes > 2) {
                        mapped_leaf_node_offset.at(k) = buf_free_offset;
                        for (uint32_t m = 0; m < num_classes - 1; m++)
                            reinterpret_cast<float*>(compr_tree_buf_)[buf_free_offset + m]
                                = node_leaf_label->at(i).at(k).at(m);
                        buf_free_offset += (num_classes - 1);
                    } else {
                        uint32_t uint_val;
                        memcpy(&uint_val, &(node_leaf_label->at(i).at(k).at(0)), 4);
                        mapped_leaf_node_offset.at(k) = uint_val;
                    }
                }
            }
            compr_tree_buf_[i + 4] = buf_free_offset;
            if (max_ft < 64)
                map_on_cnode<uint8_t>(&(node_is_leaf->at(i)), &(mapped_leaf_node_offset), &(node_feature->at(i)),
                                      &(node_threshold->at(i)), &(node_left_child->at(i)), &(node_right_child->at(i)),
                                      0, &(bin_tree_access_count[i]), 13 - 1, 7, false, &buf_free_offset, false);
            else if (max_ft < 16384)
                map_on_cnode<uint16_t>(&(node_is_leaf->at(i)), &(mapped_leaf_node_offset), &(node_feature->at(i)),
                                       &(node_threshold->at(i)), &(node_left_child->at(i)), &(node_right_child->at(i)),
                                       0, &(bin_tree_access_count[i]), 13 - 1, 7, false, &buf_free_offset, false);
            else
                map_on_cnode<uint32_t>(&(node_is_leaf->at(i)), &(mapped_leaf_node_offset), &(node_feature->at(i)),
                                       &(node_threshold->at(i)), &(node_left_child->at(i)), &(node_right_child->at(i)),
                                       0, &(bin_tree_access_count[i]), 13 - 1, 7, false, &buf_free_offset, false);
        }
        compr_tree_buf_size_ = buf_free_offset;
        compr_tree_buf_[0]
            = 2
                  * static_cast<uint32_t>(
                      ((reinterpret_cast<uint8_t*>(&(compr_tree_buf_[compr_tree_buf_[4]])))[0] & 0x1Fu) < 17)
              + node_cmp_type;
        if (max_ft >= 64)
            compr_tree_buf_[0] = compr_tree_buf_[0] + 4;
        if (max_ft >= 16384)
            compr_tree_buf_[0] = compr_tree_buf_[0] + 4;

        set_compr_root_params();
    }

    /*=================================================================================================================*/
    /* compressed tree predict function */
    /*=================================================================================================================*/
#ifdef Z14_SIMD
    template <typename I, bool eq, bool mc> inline void proc_par_cnode_t(uint32_t t, float* in, double* preds) const
    {
        vector unsigned int ci = { 1, 1, 1, 1 };
        for (uint32_t l = 0; l < compr_tree_root_seq_length_[t]; l++) {
            vector unsigned cmp_res;
            if (!eq)
                cmp_res = vec_cmpge((vector float) { in[((I*)(compr_tree_root_feature_vector_[t]))[ci[0]]],
                                                     in[((I*)(compr_tree_root_feature_vector_[t + 1]))[ci[1]]],
                                                     in[((I*)(compr_tree_root_feature_vector_[t + 2]))[ci[2]]],
                                                     in[((I*)(compr_tree_root_feature_vector_[t + 3]))[ci[3]]] },
                                    (vector float) { compr_tree_root_threshold_vector_[t][ci[0]],
                                                     compr_tree_root_threshold_vector_[t + 1][ci[1]],
                                                     compr_tree_root_threshold_vector_[t + 2][ci[2]],
                                                     compr_tree_root_threshold_vector_[t + 3][ci[3]] })
                          & (vector unsigned int) { 1, 1, 1, 1 };
            else
                cmp_res = vec_cmpgt((vector float) { in[((I*)(compr_tree_root_feature_vector_[t]))[ci[0]]],
                                                     in[((I*)(compr_tree_root_feature_vector_[t + 1]))[ci[1]]],
                                                     in[((I*)(compr_tree_root_feature_vector_[t + 2]))[ci[2]]],
                                                     in[((I*)(compr_tree_root_feature_vector_[t + 3]))[ci[3]]] },
                                    (vector float) { compr_tree_root_threshold_vector_[t][ci[0]],
                                                     compr_tree_root_threshold_vector_[t + 1][ci[1]],
                                                     compr_tree_root_threshold_vector_[t + 2][ci[2]],
                                                     compr_tree_root_threshold_vector_[t + 3][ci[3]] })
                          & (vector unsigned int) { 1, 1, 1, 1 };

            ci = (ci << 1) | cmp_res;
        }
        if (!mc) {
            preds[0] += (compr_tree_root_threshold_vector_[t][ci[0]] + compr_tree_root_threshold_vector_[t + 1][ci[1]]
                         + compr_tree_root_threshold_vector_[t + 2][ci[2]]
                         + compr_tree_root_threshold_vector_[t + 3][ci[3]]);
        } else {
            for (uint32_t k = 0; k < num_classes - 1; k++)
                preds[k]
                    += ((double)((
                            (float*)compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t][ci[0]])) + k])
                        + (double)((
                            (float*)
                                compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t + 1][ci[1]])) + k])
                        + (double)((
                            (float*)
                                compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t + 2][ci[2]])) + k])
                        + (double)((
                            (float*)compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t + 3][ci[3]]))
                                                     + k]));
        }
    }

    template <typename I, bool eq, bool mc>
    inline void proc_par_cnode_i(uint32_t t, float* in, uint32_t row_size, double* preds) const
    {
        vector unsigned int ci = { 1, 1, 1, 1 };

        for (uint32_t l = 0; l < compr_tree_root_seq_length_[t]; l++) {
            vector unsigned cmp_res;
            if (!eq)
                cmp_res
                    = vec_cmpge((vector float) { in[((I*)(compr_tree_root_feature_vector_[t]))[ci[0]]],
                                                 in[((I*)(compr_tree_root_feature_vector_[t]))[ci[1]] + row_size],
                                                 in[((I*)(compr_tree_root_feature_vector_[t]))[ci[2]] + row_size * 2],
                                                 in[((I*)(compr_tree_root_feature_vector_[t]))[ci[3]] + row_size * 3] },
                                (vector float) { compr_tree_root_threshold_vector_[t][ci[0]],
                                                 compr_tree_root_threshold_vector_[t][ci[1]],
                                                 compr_tree_root_threshold_vector_[t][ci[2]],
                                                 compr_tree_root_threshold_vector_[t][ci[3]] })
                      & (vector unsigned int) { 1, 1, 1, 1 };
            else
                cmp_res
                    = vec_cmpgt((vector float) { in[((I*)(compr_tree_root_feature_vector_[t]))[ci[0]]],
                                                 in[((I*)(compr_tree_root_feature_vector_[t]))[ci[1]] + row_size],
                                                 in[((I*)(compr_tree_root_feature_vector_[t]))[ci[2]] + row_size * 2],
                                                 in[((I*)(compr_tree_root_feature_vector_[t]))[ci[3]] + row_size * 3] },
                                (vector float) { compr_tree_root_threshold_vector_[t][ci[0]],
                                                 compr_tree_root_threshold_vector_[t][ci[1]],
                                                 compr_tree_root_threshold_vector_[t][ci[2]],
                                                 compr_tree_root_threshold_vector_[t][ci[3]] })
                      & (vector unsigned int) { 1, 1, 1, 1 };

            ci = (ci << 1) | cmp_res;
        }
        if (!mc) {
            preds[0] += compr_tree_root_threshold_vector_[t][ci[0]];
            preds[1] += compr_tree_root_threshold_vector_[t][ci[1]];
            preds[2] += compr_tree_root_threshold_vector_[t][ci[2]];
            preds[3] += compr_tree_root_threshold_vector_[t][ci[3]];
        } else {
            for (uint32_t k = 0; k < num_classes - 1; k++) {
                preds[0 * (num_classes - 1) + k] += (double)((
                    (float*)compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t][ci[0]])) + k]);
                preds[1 * (num_classes - 1) + k] += (double)((
                    (float*)compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t][ci[1]])) + k]);
                preds[2 * (num_classes - 1) + k] += (double)((
                    (float*)compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t][ci[2]])) + k]);
                preds[3 * (num_classes - 1) + k] += (double)((
                    (float*)compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t][ci[3]])) + k]);
            }
        }
    }
#elif defined(POWER_VMX)
    template <typename I, bool eq, bool mc> inline void proc_par_cnode_t(uint32_t t, float* in, double* preds) const
    {
        vector unsigned short int ci = { 1, 1, 1, 1, 1, 1, 1, 1 };
        for (uint32_t l = 0; l < compr_tree_root_seq_length_[t]; l++) {
            vector bool int cmp_res_A, cmp_res_B;
            if (!eq) {
                cmp_res_A = vec_cmpge((vector float) { in[((I*)(compr_tree_root_feature_vector_[t]))[ci[0]]],
                                                       in[((I*)(compr_tree_root_feature_vector_[t + 2]))[ci[2]]],
                                                       in[((I*)(compr_tree_root_feature_vector_[t + 4]))[ci[4]]],
                                                       in[((I*)(compr_tree_root_feature_vector_[t + 6]))[ci[6]]] },
                                      (vector float) { compr_tree_root_threshold_vector_[t][ci[0]],
                                                       compr_tree_root_threshold_vector_[t + 2][ci[2]],
                                                       compr_tree_root_threshold_vector_[t + 4][ci[4]],
                                                       compr_tree_root_threshold_vector_[t + 6][ci[6]] })
                            & (vector bool int) { 1, 1, 1, 1 };

                cmp_res_B = vec_cmpge((vector float) { in[((I*)(compr_tree_root_feature_vector_[t + 1]))[ci[1]]],
                                                       in[((I*)(compr_tree_root_feature_vector_[t + 3]))[ci[3]]],
                                                       in[((I*)(compr_tree_root_feature_vector_[t + 5]))[ci[5]]],
                                                       in[((I*)(compr_tree_root_feature_vector_[t + 7]))[ci[7]]] },
                                      (vector float) { compr_tree_root_threshold_vector_[t + 1][ci[1]],
                                                       compr_tree_root_threshold_vector_[t + 3][ci[3]],
                                                       compr_tree_root_threshold_vector_[t + 5][ci[5]],
                                                       compr_tree_root_threshold_vector_[t + 7][ci[7]] })
                            & (vector bool int) { 65536, 65536, 65536, 65536 };
            } else {
                cmp_res_A = vec_cmpgt((vector float) { in[((I*)(compr_tree_root_feature_vector_[t]))[ci[0]]],
                                                       in[((I*)(compr_tree_root_feature_vector_[t + 2]))[ci[2]]],
                                                       in[((I*)(compr_tree_root_feature_vector_[t + 4]))[ci[4]]],
                                                       in[((I*)(compr_tree_root_feature_vector_[t + 6]))[ci[6]]] },
                                      (vector float) { compr_tree_root_threshold_vector_[t][ci[0]],
                                                       compr_tree_root_threshold_vector_[t + 2][ci[2]],
                                                       compr_tree_root_threshold_vector_[t + 4][ci[4]],
                                                       compr_tree_root_threshold_vector_[t + 6][ci[6]] })
                            & (vector bool int) { 1, 1, 1, 1 };

                cmp_res_B = vec_cmpgt((vector float) { in[((I*)(compr_tree_root_feature_vector_[t + 1]))[ci[1]]],
                                                       in[((I*)(compr_tree_root_feature_vector_[t + 3]))[ci[3]]],
                                                       in[((I*)(compr_tree_root_feature_vector_[t + 5]))[ci[5]]],
                                                       in[((I*)(compr_tree_root_feature_vector_[t + 7]))[ci[7]]] },
                                      (vector float) { compr_tree_root_threshold_vector_[t + 1][ci[1]],
                                                       compr_tree_root_threshold_vector_[t + 3][ci[3]],
                                                       compr_tree_root_threshold_vector_[t + 5][ci[5]],
                                                       compr_tree_root_threshold_vector_[t + 7][ci[7]] })
                            & (vector bool int) { 65536, 65536, 65536, 65536 };
            }

            vector bool short int cmp_res_short_A = (vector bool short int)cmp_res_A;
            vector bool short int cmp_res_short_B = (vector bool short int)cmp_res_B;
            vector bool short int cmp_res_short   = cmp_res_short_A | cmp_res_short_B;
            ci                                    = (ci << 1) | cmp_res_short;
        }
        if (!mc) {
            preds[0]
                += (compr_tree_root_threshold_vector_[t][ci[0]] + compr_tree_root_threshold_vector_[t + 1][ci[1]]
                    + compr_tree_root_threshold_vector_[t + 2][ci[2]] + compr_tree_root_threshold_vector_[t + 3][ci[3]]
                    + compr_tree_root_threshold_vector_[t + 4][ci[4]] + compr_tree_root_threshold_vector_[t + 5][ci[5]]
                    + compr_tree_root_threshold_vector_[t + 6][ci[6]]
                    + compr_tree_root_threshold_vector_[t + 7][ci[7]]);
        } else {
            for (uint32_t k = 0; k < num_classes - 1; k++)
                preds[k]
                    += ((double)((
                            (float*)compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t][ci[0]])) + k])
                        + (double)((
                            (float*)
                                compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t + 1][ci[1]])) + k])
                        + (double)((
                            (float*)
                                compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t + 2][ci[2]])) + k])
                        + (double)((
                            (float*)
                                compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t + 3][ci[3]])) + k])
                        + (double)((
                            (float*)
                                compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t + 4][ci[4]])) + k])
                        + (double)((
                            (float*)
                                compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t + 5][ci[5]])) + k])
                        + (double)((
                            (float*)
                                compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t + 6][ci[6]])) + k])
                        + (double)((
                            (float*)compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t + 7][ci[7]]))
                                                     + k]));
        }
    }

    template <typename I, bool eq, bool mc>
    inline void proc_par_cnode_i(uint32_t t, float* in, uint32_t row_size, double* preds) const
    {
        vector unsigned short int ci = { 1, 1, 1, 1, 1, 1, 1, 1 };
        for (uint32_t l = 0; l < compr_tree_root_seq_length_[t]; l++) {
            vector bool int cmp_res_A, cmp_res_B;
            if (!eq) {
                cmp_res_A
                    = vec_cmpge((vector float) { in[((I*)(compr_tree_root_feature_vector_[t]))[ci[0]]],
                                                 in[((I*)(compr_tree_root_feature_vector_[t]))[ci[2]] + row_size * 2],
                                                 in[((I*)(compr_tree_root_feature_vector_[t]))[ci[4]] + row_size * 4],
                                                 in[((I*)(compr_tree_root_feature_vector_[t]))[ci[6]] + row_size * 6] },
                                (vector float) { compr_tree_root_threshold_vector_[t][ci[0]],
                                                 compr_tree_root_threshold_vector_[t][ci[2]],
                                                 compr_tree_root_threshold_vector_[t][ci[4]],
                                                 compr_tree_root_threshold_vector_[t][ci[6]] })
                      & (vector unsigned int) { 1, 1, 1, 1 };

                cmp_res_B
                    = vec_cmpge((vector float) { in[((I*)(compr_tree_root_feature_vector_[t]))[ci[1]] + row_size],
                                                 in[((I*)(compr_tree_root_feature_vector_[t]))[ci[3]] + row_size * 3],
                                                 in[((I*)(compr_tree_root_feature_vector_[t]))[ci[5]] + row_size * 5],
                                                 in[((I*)(compr_tree_root_feature_vector_[t]))[ci[7]] + row_size * 7] },
                                (vector float) { compr_tree_root_threshold_vector_[t][ci[1]],
                                                 compr_tree_root_threshold_vector_[t][ci[3]],
                                                 compr_tree_root_threshold_vector_[t][ci[5]],
                                                 compr_tree_root_threshold_vector_[t][ci[7]] })
                      & (vector unsigned int) { 65536, 65536, 65536, 65536 };
            } else {
                cmp_res_A
                    = vec_cmpgt((vector float) { in[((I*)(compr_tree_root_feature_vector_[t]))[ci[0]]],
                                                 in[((I*)(compr_tree_root_feature_vector_[t]))[ci[2]] + row_size * 2],
                                                 in[((I*)(compr_tree_root_feature_vector_[t]))[ci[4]] + row_size * 4],
                                                 in[((I*)(compr_tree_root_feature_vector_[t]))[ci[6]] + row_size * 6] },
                                (vector float) { compr_tree_root_threshold_vector_[t][ci[0]],
                                                 compr_tree_root_threshold_vector_[t][ci[2]],
                                                 compr_tree_root_threshold_vector_[t][ci[4]],
                                                 compr_tree_root_threshold_vector_[t][ci[6]] })
                      & (vector unsigned int) { 1, 1, 1, 1 };

                cmp_res_B
                    = vec_cmpgt((vector float) { in[((I*)(compr_tree_root_feature_vector_[t]))[ci[1]] + row_size],
                                                 in[((I*)(compr_tree_root_feature_vector_[t]))[ci[3]] + row_size * 3],
                                                 in[((I*)(compr_tree_root_feature_vector_[t]))[ci[5]] + row_size * 5],
                                                 in[((I*)(compr_tree_root_feature_vector_[t]))[ci[7]] + row_size * 7] },
                                (vector float) { compr_tree_root_threshold_vector_[t][ci[1]],
                                                 compr_tree_root_threshold_vector_[t][ci[3]],
                                                 compr_tree_root_threshold_vector_[t][ci[5]],
                                                 compr_tree_root_threshold_vector_[t][ci[7]] })
                      & (vector unsigned int) { 65536, 65536, 65536, 65536 };
            }
            vector bool short int cmp_res_short_A = (vector bool short int)cmp_res_A;
            vector bool short int cmp_res_short_B = (vector bool short int)cmp_res_B;
            vector bool short int cmp_res_short   = cmp_res_short_A | cmp_res_short_B;
            ci                                    = (ci << 1) | cmp_res_short;
        }
        if (!mc) {
            preds[0] += compr_tree_root_threshold_vector_[t][ci[0]];
            preds[1] += compr_tree_root_threshold_vector_[t][ci[1]];
            preds[2] += compr_tree_root_threshold_vector_[t][ci[2]];
            preds[3] += compr_tree_root_threshold_vector_[t][ci[3]];
            preds[4] += compr_tree_root_threshold_vector_[t][ci[4]];
            preds[5] += compr_tree_root_threshold_vector_[t][ci[5]];
            preds[6] += compr_tree_root_threshold_vector_[t][ci[6]];
            preds[7] += compr_tree_root_threshold_vector_[t][ci[7]];
        } else {
            for (uint32_t k = 0; k < num_classes - 1; k++) {
                preds[0 * (num_classes - 1) + k] += (double)((
                    (float*)compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t][ci[0]])) + k]);
                preds[1 * (num_classes - 1) + k] += (double)((
                    (float*)compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t][ci[1]])) + k]);
                preds[2 * (num_classes - 1) + k] += (double)((
                    (float*)compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t][ci[2]])) + k]);
                preds[3 * (num_classes - 1) + k] += (double)((
                    (float*)compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t][ci[3]])) + k]);
                preds[4 * (num_classes - 1) + k] += (double)((
                    (float*)compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t][ci[4]])) + k]);
                preds[5 * (num_classes - 1) + k] += (double)((
                    (float*)compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t][ci[5]])) + k]);
                preds[6 * (num_classes - 1) + k] += (double)((
                    (float*)compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t][ci[6]])) + k]);
                preds[7 * (num_classes - 1) + k] += (double)((
                    (float*)compr_tree_buf_)[*(uint32_t*)(&(compr_tree_root_threshold_vector_[t][ci[7]])) + k]);
            }
        }
    }
#elif defined(X86_AVX512)
    template <typename I, bool eq, bool mc> inline void proc_par_cnode_t(uint32_t t, float* in, double* preds) const
    {
        __m512i ci = _mm512_set1_epi32(1);
        __m512i to = _mm512_loadu_si512((__m512i*)(&(compr_tree_buf_[t + 2])));
        __m512i fo = _mm512_add_epi32(_mm512_slli_epi32(to, 2 - typename_to_index<I>()), _mm512_set1_epi32(1));
        __m512i ho = _mm512_add_epi32(
            to, _mm512_set1_epi32(
                    cnode_threshold_offset[typename_to_index<I>()]
                                          [((uint8_t*)(&(compr_tree_buf_[compr_tree_buf_[t + 2]])))[0] & 0x0F]));

        for (uint32_t l = 0; l < compr_tree_root_seq_length_[t]; l++) {
            __m512i fs = _mm512_and_si512(
                _mm512_i32gather_epi32(fo, (int const*)compr_tree_buf_, (1 << typename_to_index<I>())),
                _mm512_set1_epi32((uint32_t)0xFFFFFFFF >> typename_to_shift<I>()));
            __mmask16 cmp_res = _mm512_cmp_ps_mask(_mm512_i32gather_ps(fs, in, 4),
                                                   _mm512_i32gather_ps(ho, (float*)compr_tree_buf_, 4),
                                                   (eq ? _CMP_GT_OQ : _CMP_GE_OQ));

            __m512i incr = _mm512_mask_add_epi32(ci, cmp_res, ci, _mm512_set1_epi32(1));

            fo = _mm512_add_epi32(fo, incr);
            ho = _mm512_add_epi32(ho, incr);
            ci = _mm512_add_epi32(ci, incr);
        }
        preds[0] += (_mm512_reduce_add_ps(_mm512_i32gather_ps(ho, (float*)compr_tree_buf_, 4)));
    }

    template <typename I, bool eq, bool mc>
    inline void proc_par_cnode_i(uint32_t t, float* in, uint32_t row_size, double* preds) const
    {
        const __m512i io = _mm512_set_epi32(15 * row_size, 14 * row_size, 13 * row_size, 12 * row_size, 11 * row_size,
                                            10 * row_size, 9 * row_size, 8 * row_size, 7 * row_size, 6 * row_size,
                                            5 * row_size, 4 * row_size, 3 * row_size, 2 * row_size, 1 * row_size, 0);
        __m512i       ci = _mm512_set1_epi32(1);
        __m512i       fo = _mm512_set1_epi32((compr_tree_buf_[t + 2] << (2 - typename_to_index<I>())) + 1);
        __m512i       ho = _mm512_set1_epi32(
            compr_tree_buf_[t + 2]
            + cnode_threshold_offset[typename_to_index<I>()]
                                    [((uint8_t*)(&(compr_tree_buf_[compr_tree_buf_[t + 2]])))[0] & 0x0F]);
        for (uint32_t l = 0; l < compr_tree_root_seq_length_[t]; l++) {
            __m512i fs = _mm512_and_si512(
                _mm512_i32gather_epi32(fo, (int const*)compr_tree_buf_, (1 << typename_to_index<I>())),
                _mm512_set1_epi32((uint32_t)0xFFFFFFFF >> typename_to_shift<I>()));
            __mmask16 cmp_res = _mm512_cmp_ps_mask(_mm512_i32gather_ps(_mm512_add_epi32(io, fs), in, 4),
                                                   _mm512_i32gather_ps(ho, (float*)compr_tree_buf_, 4),
                                                   (eq ? _CMP_GT_OQ : _CMP_GE_OQ));

            __m512i incr = _mm512_mask_add_epi32(ci, cmp_res, ci, _mm512_set1_epi32(1));

            fo = _mm512_add_epi32(fo, incr);
            ho = _mm512_add_epi32(ho, incr);
            ci = _mm512_add_epi32(ci, incr);
        }
        __m512 res = _mm512_i32gather_ps(ho, (float*)compr_tree_buf_, 4);
        _mm512_storeu_pd(preds, _mm512_add_pd(_mm512_loadu_pd(preds), _mm512_cvtps_pd(_mm512_extractf32x8_ps(res, 0))));
        _mm512_storeu_pd(&(preds[8]),
                         _mm512_add_pd(_mm512_loadu_pd(&(preds[8])), _mm512_cvtps_pd(_mm512_extractf32x8_ps(res, 1))));
    }
#elif defined(X86_AVX2)
    template <typename I, bool eq, bool mc> inline void proc_par_cnode_t(uint32_t t, float* in, double* preds) const
    {
        __m256i ci = _mm256_set1_epi32(1);
        __m256i to = _mm256_loadu_si256((__m256i*)(&(compr_tree_buf_[t + 4])));
        __m256i fo = _mm256_add_epi32(_mm256_slli_epi32(to, 2 - typename_to_index<I>()), _mm256_set1_epi32(1));
        __m256i ho = _mm256_add_epi32(
            to, _mm256_set1_epi32(
                    cnode_threshold_offset[typename_to_index<I>()]
                                          [((uint8_t*)(&(compr_tree_buf_[compr_tree_buf_[t + 4]])))[0] & 0x1F]));

        for (uint32_t l = 0; l < compr_tree_root_seq_length_[t]; l++) {
            __m256i fs = _mm256_set_epi32(
                ((I*)compr_tree_buf_)[_mm256_extract_epi32(fo, 7)], ((I*)compr_tree_buf_)[_mm256_extract_epi32(fo, 6)],
                ((I*)compr_tree_buf_)[_mm256_extract_epi32(fo, 5)], ((I*)compr_tree_buf_)[_mm256_extract_epi32(fo, 4)],
                ((I*)compr_tree_buf_)[_mm256_extract_epi32(fo, 3)], ((I*)compr_tree_buf_)[_mm256_extract_epi32(fo, 2)],
                ((I*)compr_tree_buf_)[_mm256_extract_epi32(fo, 1)], ((I*)compr_tree_buf_)[_mm256_extract_epi32(fo, 0)]);
            __m256i cmp_res;
            if (!eq)
                cmp_res = _mm256_add_epi32(
                    ci, _mm256_and_si256(_mm256_castps_si256(_mm256_cmp_ps(
                                             _mm256_i32gather_ps(in, fs, 4),
                                             _mm256_i32gather_ps((float*)compr_tree_buf_, ho, 4), _CMP_GE_OQ)),
                                         _mm256_set1_epi32(1)));
            else
                cmp_res = _mm256_add_epi32(
                    ci, _mm256_and_si256(_mm256_castps_si256(_mm256_cmp_ps(
                                             _mm256_i32gather_ps(in, fs, 4),
                                             _mm256_i32gather_ps((float*)compr_tree_buf_, ho, 4), _CMP_GT_OQ)),
                                         _mm256_set1_epi32(1)));
            fo = _mm256_add_epi32(fo, cmp_res);
            ho = _mm256_add_epi32(ho, cmp_res);
            ci = _mm256_add_epi32(ci, cmp_res);
        }
        if (!mc) {
            __m256   res  = _mm256_i32gather_ps((float*)compr_tree_buf_, ho, 4);
            __m256   res2 = _mm256_hadd_ps(res, res);
            __m256   res3 = _mm256_hadd_ps(res2, res2);
            uint32_t int0 = _mm256_extract_epi32(_mm256_castps_si256(res3), 0);
            uint32_t int4 = _mm256_extract_epi32(_mm256_castps_si256(res3), 4);
            float    fl0, fl4;
            memcpy(&fl0, &int0, 4);
            memcpy(&fl4, &int4, 4);
            preds[0] += (fl0 + fl4);
        } else {
            __m256i po = _mm256_i32gather_epi32((int const*)compr_tree_buf_, ho, 4);
            for (uint32_t k = 0; k < num_classes - 1; k++) {
                __m256 res    = _mm256_i32gather_ps((float*)compr_tree_buf_, po, 4);
                po            = _mm256_add_epi32(po, _mm256_set1_epi32(1));
                __m256   res2 = _mm256_hadd_ps(res, res);
                __m256   res3 = _mm256_hadd_ps(res2, res2);
                uint32_t int0 = _mm256_extract_epi32(_mm256_castps_si256(res3), 0);
                uint32_t int4 = _mm256_extract_epi32(_mm256_castps_si256(res3), 4);
                float    fl0, fl4;
                memcpy(&fl0, &int0, 4);
                memcpy(&fl4, &int4, 4);
                preds[k] += (fl0 + fl4);
            }
        }
    }

    template <typename I, bool eq, bool mc>
    inline void proc_par_cnode_i(uint32_t t, float* in, uint32_t row_size, double* preds) const
    {
        const __m256i io = _mm256_set_epi32(7 * row_size, 6 * row_size, 5 * row_size, 4 * row_size, 3 * row_size,
                                            2 * row_size, 1 * row_size, 0);
        __m256i       ci = _mm256_set1_epi32(1);
        __m256i       fo = _mm256_set1_epi32((compr_tree_buf_[t + 4] << (2 - typename_to_index<I>())) + 1);
        __m256i       ho = _mm256_set1_epi32(
            compr_tree_buf_[t + 4]
            + cnode_threshold_offset[typename_to_index<I>()]
                                    [((uint8_t*)(&(compr_tree_buf_[compr_tree_buf_[t + 4]])))[0] & 0x1F]);
        for (uint32_t l = 0; l < compr_tree_root_seq_length_[t]; l++) {
            __m256i fs = _mm256_set_epi32(
                ((I*)compr_tree_buf_)[_mm256_extract_epi32(fo, 7)], ((I*)compr_tree_buf_)[_mm256_extract_epi32(fo, 6)],
                ((I*)compr_tree_buf_)[_mm256_extract_epi32(fo, 5)], ((I*)compr_tree_buf_)[_mm256_extract_epi32(fo, 4)],
                ((I*)compr_tree_buf_)[_mm256_extract_epi32(fo, 3)], ((I*)compr_tree_buf_)[_mm256_extract_epi32(fo, 2)],
                ((I*)compr_tree_buf_)[_mm256_extract_epi32(fo, 1)], ((I*)compr_tree_buf_)[_mm256_extract_epi32(fo, 0)]);
            __m256i cmp_res;
            if (!eq)
                cmp_res = _mm256_add_epi32(
                    ci, _mm256_and_si256(_mm256_castps_si256(_mm256_cmp_ps(
                                             _mm256_i32gather_ps(in, _mm256_add_epi32(io, fs), 4),
                                             _mm256_i32gather_ps((float*)compr_tree_buf_, ho, 4), _CMP_GE_OQ)),
                                         _mm256_set1_epi32(1)));
            else
                cmp_res = _mm256_add_epi32(
                    ci, _mm256_and_si256(_mm256_castps_si256(_mm256_cmp_ps(
                                             _mm256_i32gather_ps(in, _mm256_add_epi32(io, fs), 4),
                                             _mm256_i32gather_ps((float*)compr_tree_buf_, ho, 4), _CMP_GT_OQ)),
                                         _mm256_set1_epi32(1)));
            fo = _mm256_add_epi32(fo, cmp_res);
            ho = _mm256_add_epi32(ho, cmp_res);
            ci = _mm256_add_epi32(ci, cmp_res);
        }
        if (!mc) {
            __m256 res = _mm256_i32gather_ps((float*)compr_tree_buf_, ho, 4);
            _mm256_storeu_pd(preds,
                             _mm256_add_pd(_mm256_loadu_pd(preds), _mm256_cvtps_pd(_mm256_extractf128_ps(res, 0))));
            _mm256_storeu_pd(&(preds[4]), _mm256_add_pd(_mm256_loadu_pd(&(preds[4])),
                                                        _mm256_cvtps_pd(_mm256_extractf128_ps(res, 1))));
        } else {
            __m256i po = _mm256_i32gather_epi32((int const*)compr_tree_buf_, ho, 4);
            for (uint32_t k = 0; k < num_classes - 1; k++) {
                __m256 res    = _mm256_i32gather_ps((float*)compr_tree_buf_, po, 4);
                po            = _mm256_add_epi32(po, _mm256_set1_epi32(1));
                __m256d pred0 = _mm256_set_pd(preds[3 * (num_classes - 1) + k], preds[2 * (num_classes - 1) + k],
                                              preds[1 * (num_classes - 1) + k], preds[0 * (num_classes - 1) + k]);
                __m256d pred4 = _mm256_set_pd(preds[7 * (num_classes - 1) + k], preds[6 * (num_classes - 1) + k],
                                              preds[5 * (num_classes - 1) + k], preds[4 * (num_classes - 1) + k]);
                pred0         = _mm256_add_pd(pred0, _mm256_cvtps_pd(_mm256_extractf128_ps(res, 0)));
                pred4         = _mm256_add_pd(pred4, _mm256_cvtps_pd(_mm256_extractf128_ps(res, 1)));
                ((uint64_t*)preds)[0 * (num_classes - 1) + k] = _mm256_extract_epi64(_mm256_castpd_si256(pred0), 0);
                ((uint64_t*)preds)[1 * (num_classes - 1) + k] = _mm256_extract_epi64(_mm256_castpd_si256(pred0), 1);
                ((uint64_t*)preds)[2 * (num_classes - 1) + k] = _mm256_extract_epi64(_mm256_castpd_si256(pred0), 2);
                ((uint64_t*)preds)[3 * (num_classes - 1) + k] = _mm256_extract_epi64(_mm256_castpd_si256(pred0), 3);
                ((uint64_t*)preds)[4 * (num_classes - 1) + k] = _mm256_extract_epi64(_mm256_castpd_si256(pred4), 0);
                ((uint64_t*)preds)[5 * (num_classes - 1) + k] = _mm256_extract_epi64(_mm256_castpd_si256(pred4), 1);
                ((uint64_t*)preds)[6 * (num_classes - 1) + k] = _mm256_extract_epi64(_mm256_castpd_si256(pred4), 2);
                ((uint64_t*)preds)[7 * (num_classes - 1) + k] = _mm256_extract_epi64(_mm256_castpd_si256(pred4), 3);
            }
        }
    }
#endif

    template <typename I, bool eq, bool mc> inline void proc_par_cnode(uint32_t t, float* in, double* preds) const
    {
        uint32_t ci = 1;
        for (uint32_t l = 0; l < compr_tree_root_seq_length_[t]; l++) {
            if ((!eq
                 && (in[(reinterpret_cast<I*>(compr_tree_root_feature_vector_[t]))[ci]]
                     < compr_tree_root_threshold_vector_[t][ci]))
                || (eq
                    && (in[(reinterpret_cast<I*>(compr_tree_root_feature_vector_[t]))[ci]]
                        <= compr_tree_root_threshold_vector_[t][ci])))
                ci = 2 * ci;
            else
                ci = 2 * ci + 1;
        }
        if (!mc)
            preds[0] += compr_tree_root_threshold_vector_[t][ci];
        else {
            float    pred = compr_tree_root_threshold_vector_[t][ci];
            uint32_t prob_offset;
            memcpy(&prob_offset, &pred, 4);
            for (uint32_t k = 0; k < num_classes - 1; k++)
                preds[k] += static_cast<double>((reinterpret_cast<float*>(compr_tree_buf_))[prob_offset + k]);
        }
    }

    template <typename I, bool eq>
    bool proc_seq_cnode(uint32_t* cur_cnode_offset, uint32_t iteration_count, I* cur_feature_vector,
                        float* cur_threshold_vector, uint32_t* cur_child_ptr_vector, float* i, float* pred_result) const
    {
        bool not_ready   = true;
        bool match_found = false;
        for (uint8_t k = 0; k < iteration_count; k++) {
            I    cur_feature = (cur_feature_vector[k] & (static_cast<uint32_t>(0x3FFFFFFF) >> typename_to_shift<I>()));
            bool cur_left_right
                = (cur_feature_vector[k] & (static_cast<uint32_t>(0x80000000) >> typename_to_shift<I>()));
            bool cur_child_is_leaf
                = (cur_feature_vector[k] & (static_cast<uint32_t>(0x40000000 >> typename_to_shift<I>())));
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
            uint8_t k        = iteration_count;
            I    cur_feature = (cur_feature_vector[k] & (static_cast<uint32_t>(0x3FFFFFFF) >> typename_to_shift<I>()));
            bool cur_left_child_is_leaf
                = (cur_feature_vector[k] & (static_cast<uint32_t>(0x40000000) >> typename_to_shift<I>()));
            bool cur_right_child_is_leaf
                = (cur_feature_vector[k] & (static_cast<uint32_t>(0x80000000) >> typename_to_shift<I>()));
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

    template <typename I, bool eq, bool mc> void tree_predict(uint32_t t, float* i, double* preds) const
    {
        if (compr_tree_root_type_[t])
            proc_par_cnode<I, eq, mc>(t, i, preds);
        else {
            float    pred_result;
            uint32_t cur_cnode_offset = compr_tree_buf_[t + 4];
            bool     not_ready        = proc_seq_cnode<I, eq>(&cur_cnode_offset, compr_tree_root_seq_length_[t] - 1,
                                                   reinterpret_cast<I*>(compr_tree_root_feature_vector_[t]) + 1,
                                                   compr_tree_root_threshold_vector_[t] + 1,
                                                   compr_tree_root_child_ptr_vector_[t] + 1, i, &pred_result);

            while (not_ready) {
                uint8_t  cur_cnode_type = (reinterpret_cast<uint8_t*>(&(compr_tree_buf_[cur_cnode_offset])))[0] & 0x1Fu;
                uint32_t iteration_count      = (cur_cnode_type >= 17) ? (cur_cnode_type - 17) : (cur_cnode_type - 1);
                I*       cur_feature_vector   = &((reinterpret_cast<I*>(&(compr_tree_buf_[cur_cnode_offset])))[1]);
                float*   cur_threshold_vector = reinterpret_cast<float*>(
                    &(compr_tree_buf_[cur_cnode_offset
                                      + cnode_threshold_offset[typename_to_index<I>()][cur_cnode_type]]));
                uint32_t* cur_child_ptr_vector = &(
                    compr_tree_buf_[cur_cnode_offset + cnode_child_ptr_offset[typename_to_index<I>()][cur_cnode_type]]);

                not_ready = proc_seq_cnode<I, eq>(&cur_cnode_offset, iteration_count, cur_feature_vector,
                                                  cur_threshold_vector, cur_child_ptr_vector, i, &pred_result);
            }

            if (!mc)
                preds[0] += static_cast<double>(pred_result);
            else {
                uint32_t prob_offset;
                memcpy(&prob_offset, &pred_result, 4);
                for (uint32_t k = 0; k < num_classes - 1; k++)
                    preds[k] += static_cast<double>(reinterpret_cast<float*>(compr_tree_buf_)[prob_offset + k]);
            }
        }
    }

#if defined(Z14_SIMD) || defined(X86_AVX2) || defined(X86_AVX512) || defined(POWER_VMX)
    template <typename I, bool eq, bool mc> void tree_predict_t(uint32_t tb, float* in, double* preds) const
    {
        if (compr_tree_root_type_[tb]) {
            proc_par_cnode_t<I, eq, mc>(tb, in, preds);
        } else {
            for (uint32_t t = tb; t < tb + PAR_COUNT; t++) {
                float    pred_result;
                uint32_t cur_cnode_offset = compr_tree_buf_[t + 4];
                bool     not_ready        = proc_seq_cnode<I, eq>(&cur_cnode_offset, compr_tree_root_seq_length_[t] - 1,
                                                       (I*)(compr_tree_root_feature_vector_[t]) + 1,
                                                       compr_tree_root_threshold_vector_[t] + 1,
                                                       compr_tree_root_child_ptr_vector_[t] + 1, in, &pred_result);

                while (not_ready) {
                    uint8_t   cur_cnode_type  = ((uint8_t*)(&(compr_tree_buf_[cur_cnode_offset])))[0] & 0x1F;
                    uint32_t  iteration_count = (cur_cnode_type >= 17) ? (cur_cnode_type - 17) : (cur_cnode_type - 1);
                    I*        cur_feature_vector   = &(((I*)(&(compr_tree_buf_[cur_cnode_offset])))[1]);
                    float*    cur_threshold_vector = (float*)(&(
                        compr_tree_buf_[cur_cnode_offset
                                        + cnode_threshold_offset[typename_to_index<I>()][cur_cnode_type]]));
                    uint32_t* cur_child_ptr_vector
                        = &(compr_tree_buf_[cur_cnode_offset
                                            + cnode_child_ptr_offset[typename_to_index<I>()][cur_cnode_type]]);

                    not_ready = proc_seq_cnode<I, eq>(&cur_cnode_offset, iteration_count, cur_feature_vector,
                                                      cur_threshold_vector, cur_child_ptr_vector, in, &pred_result);
                }
                if (!mc)
                    preds[0] += (double)pred_result;
                else {
                    uint32_t prob_offset;
                    memcpy(&prob_offset, &pred_result, 4);
                    for (uint32_t k = 0; k < num_classes - 1; k++)
                        preds[k] += (double)(((float*)compr_tree_buf_)[prob_offset + k]);
                }
            }
        }
    }

    template <typename I, bool eq, bool mc>
    void tree_predict_i(uint32_t t, float* in, uint32_t row_size, double* preds) const
    {
        if (compr_tree_root_type_[t]) {
            proc_par_cnode_i<I, eq, mc>(t, in, row_size, preds);
        } else {
            for (uint32_t i = 0; i < PAR_COUNT; i++) {
                float    pred_result;
                uint32_t cur_cnode_offset = compr_tree_buf_[t + 4];
                bool     not_ready        = proc_seq_cnode<I, eq>(
                    &cur_cnode_offset, compr_tree_root_seq_length_[t] - 1, (I*)(compr_tree_root_feature_vector_[t]) + 1,
                    compr_tree_root_threshold_vector_[t] + 1, compr_tree_root_child_ptr_vector_[t] + 1,
                    in + i * row_size, &pred_result);

                while (not_ready) {
                    uint8_t   cur_cnode_type  = ((uint8_t*)(&(compr_tree_buf_[cur_cnode_offset])))[0] & 0x1F;
                    uint32_t  iteration_count = (cur_cnode_type >= 17) ? (cur_cnode_type - 17) : (cur_cnode_type - 1);
                    I*        cur_feature_vector   = &(((I*)(&(compr_tree_buf_[cur_cnode_offset])))[1]);
                    float*    cur_threshold_vector = (float*)(&(
                        compr_tree_buf_[cur_cnode_offset
                                        + cnode_threshold_offset[typename_to_index<I>()][cur_cnode_type]]));
                    uint32_t* cur_child_ptr_vector
                        = &(compr_tree_buf_[cur_cnode_offset
                                            + cnode_child_ptr_offset[typename_to_index<I>()][cur_cnode_type]]);

                    not_ready = proc_seq_cnode<I, eq>(&cur_cnode_offset, iteration_count, cur_feature_vector,
                                                      cur_threshold_vector, cur_child_ptr_vector, in + i * row_size,
                                                      &pred_result);
                }
                if (!mc)
                    preds[i] += pred_result;
                else {
                    uint32_t prob_offset;
                    memcpy(&prob_offset, &pred_result, 4);
                    for (uint32_t k = 0; k < num_classes - 1; k++)
                        preds[i * (num_classes - 1) + k] += (double)(((float*)compr_tree_buf_)[prob_offset + k]);
                }
            }
        }
    }
#endif

    template <typename I, bool eq, bool mc>
    void ensemble_predict(float* in, uint32_t num_ex, uint32_t num_ft, double* preds, uint32_t num_threads) const
    {
        if (num_threads == 1) {
            for (uint32_t ex = 0; ex < num_ex; ex++)
                for (uint32_t t = 0; t < compr_tree_count_; t++)
                    tree_predict<I, eq, mc>(t, in + num_ft * ex, preds + (mc ? ex * (num_classes - 1) : ex));
        } else {
            if (num_ex < 32) {
                if (!mc) {
                    for (uint32_t ex = 0; ex < num_ex; ex++) {
                        double sum = 0.0;
                        OMP::parallel_for_reduction<int32_t>(0, compr_tree_count_, sum,
                                                             [this, &in, &num_ft, &ex](int32_t t, double& sum) {
                                                                 tree_predict<I, eq, mc>(t, in + num_ft * ex, &sum);
                                                             });
                        preds[ex] += sum;
                    }
                } else {
                    std::vector<double> probs(num_threads * (num_classes - 1));
                    for (uint32_t ex = 0; ex < num_ex; ex++) {
                        std::fill(probs.begin(), probs.end(), 0.0);
                        OMP::parallel_for<int32_t>(0, compr_tree_count_, [this, &in, &num_ft, &ex, &probs](int32_t t) {
                            tree_predict<I, eq, mc>(t, in + num_ft * ex,
                                                    probs.data() + omp_get_thread_num() * (num_classes - 1));
                        });
                        for (uint32_t m = 0; m < num_threads; m++) {
                            for (uint32_t k = 0; k < (num_classes - 1); k++)
                                preds[ex * (num_classes - 1) + k] += probs[m * (num_classes - 1) + k];
                        }
                    }
                }
            } else {
                OMP::parallel_for<int32_t>(0, num_ex, [this, &preds, &in, &num_ft](int32_t ex) {
                    for (uint32_t t = 0; t < compr_tree_count_; t++)
                        tree_predict<I, eq, mc>(t, in + num_ft * ex, preds + (mc ? ex * (num_classes - 1) : ex));
                });
            }
        }
    }

#if defined(Z14_SIMD) || defined(X86_AVX2) || defined(X86_AVX512) || defined(POWER_VMX)
    template <typename I, bool eq, bool mc>
    void ensemble_predict_simd(float* in, uint32_t num_ex, uint32_t num_ft, double* preds, uint32_t num_threads) const
    {
        if (((num_threads == 1) && (num_ex < PAR_COUNT)) || ((num_threads > 1) && (num_ex < 32))) {
            uint32_t par_trees = compr_tree_count_ & ~((uint32_t)PAR_COUNT - 1);
            if (num_threads == 1) {
                for (uint32_t ex = 0; ex < num_ex; ex++)
                    for (uint32_t tb = 0; tb < par_trees; tb += PAR_COUNT)
                        tree_predict_t<I, eq, mc>(tb, in + num_ft * ex, preds + (mc ? ex * (num_classes - 1) : ex));
                for (uint32_t ex = 0; ex < num_ex; ex++)
                    for (uint32_t t = par_trees; t < compr_tree_count_; t++)
                        tree_predict<I, eq, mc>(t, in + num_ft * ex, preds + (mc ? ex * (num_classes - 1) : ex));
            } else {
                if (!mc) {
                    for (uint32_t ex = 0; ex < num_ex; ex++) {
                        double sum = 0.0;
                        OMP::parallel_for_reduction<int32_t>(
                            0, par_trees / PAR_COUNT, sum, [this, &in, &num_ft, &ex](int32_t tb, double& sum) {
                                tree_predict_t<I, eq, mc>(tb * PAR_COUNT, in + num_ft * ex, &sum);
                            });
                        preds[ex] += sum;
                    }
                } else {
                    std::vector<double> probs(num_threads * (num_classes - 1));
                    for (uint32_t ex = 0; ex < num_ex; ex++) {
                        std::fill(probs.begin(), probs.end(), 0.0);
                        OMP::parallel_for<int32_t>(
                            0, par_trees / PAR_COUNT, [this, &ex, &in, &num_ft, &probs](uint32_t tb) {
                                tree_predict_t<I, eq, mc>(tb * PAR_COUNT, in + num_ft * ex,
                                                          probs.data() + omp_get_thread_num() * (num_classes - 1));
                            });
                        for (uint32_t m = 0; m < num_threads; m++) {
                            for (uint32_t k = 0; k < (num_classes - 1); k++)
                                preds[ex * (num_classes - 1) + k] += probs[m * (num_classes - 1) + k];
                        }
                    }
                }
                OMP::parallel_for<int32_t>(0, num_ex, [this, &preds, &in, &num_ft, &par_trees](int32_t ex) {
                    for (uint32_t t = par_trees; t < compr_tree_count_; t++)
                        tree_predict<I, eq, mc>(t, in + num_ft * ex, preds + (mc ? ex * (num_classes - 1) : ex));
                });
            }
        } else {
            uint32_t par_ex = num_ex & ~((uint32_t)PAR_COUNT - 1);
            if (num_threads == 1) {
                for (uint32_t eb = 0; eb < par_ex; eb += PAR_COUNT)
                    for (uint32_t t = 0; t < compr_tree_count_; t++)
                        tree_predict_i<I, eq, mc>(t, in + num_ft * eb, num_ft,
                                                  preds + (mc ? eb * (num_classes - 1) : eb));
                for (uint32_t ex = par_ex; ex < num_ex; ex++)
                    for (uint32_t t = 0; t < compr_tree_count_; t++)
                        tree_predict<I, eq, mc>(t, in + num_ft * ex, preds + (mc ? ex * (num_classes - 1) : ex));
            } else {
                OMP::parallel_for<int32_t>(0, par_ex / PAR_COUNT, [this, &preds, &in, &num_ft](int32_t eb) {
                    for (uint32_t t = 0; t < compr_tree_count_; t++)
                        tree_predict_i<I, eq, mc>(t, in + num_ft * eb * PAR_COUNT, num_ft,
                                                  preds + PAR_COUNT * (mc ? eb * (num_classes - 1) : eb));
                });
                if (!mc) {
                    for (uint32_t ex = par_ex; ex < num_ex; ex++) {
                        double sum = 0.0;
                        OMP::parallel_for_reduction<int32_t>(0, compr_tree_count_, sum,
                                                             [this, &in, &num_ft, &ex](int32_t t, double& sum) {
                                                                 tree_predict<I, eq, mc>(t, in + num_ft * ex, &sum);
                                                             });
                        preds[ex] += sum;
                    }
                } else {
                    std::vector<double> probs(num_threads * (num_classes - 1));
                    for (uint32_t ex = par_ex; ex < num_ex; ex++) {
                        std::fill(probs.begin(), probs.end(), 0.0);
                        OMP::parallel_for<int32_t>(0, compr_tree_count_, [this, &ex, &probs, &in, &num_ft](int32_t t) {
                            tree_predict<I, eq, mc>(t, in + num_ft * ex,
                                                    probs.data() + omp_get_thread_num() * (num_classes - 1));
                        });
                        for (uint32_t m = 0; m < num_threads; m++) {
                            for (uint32_t k = 0; k < (num_classes - 1); k++)
                                preds[ex * (num_classes - 1) + k] += probs[m * (num_classes - 1) + k];
                        }
                    }
                }
            }
        }
    }
#endif

    template <bool mc>
    void predict_impl(float* in, uint32_t num_ex, uint32_t num_ft, double* preds, uint32_t num_threads) const
    {
        switch (compr_tree_ensemble_type_) {
        case 0:
            ensemble_predict<uint8_t, false, mc>(in, num_ex, num_ft, preds, num_threads);
            break;
        case 1:
            ensemble_predict<uint8_t, true, mc>(in, num_ex, num_ft, preds, num_threads);
            break;
#if defined(Z14_SIMD) || defined(X86_AVX2) || defined(X86_AVX512) || defined(POWER_VMX)
        case 2:
            ensemble_predict_simd<uint8_t, false, mc>(in, num_ex, num_ft, preds, num_threads);
            break;
        case 3:
            ensemble_predict_simd<uint8_t, true, mc>(in, num_ex, num_ft, preds, num_threads);
            break;
#else
        case 2:
            ensemble_predict<uint8_t, false, mc>(in, num_ex, num_ft, preds, num_threads);
            break;
        case 3:
            ensemble_predict<uint8_t, true, mc>(in, num_ex, num_ft, preds, num_threads);
            break;
#endif
        case 4:
            ensemble_predict<uint16_t, false, mc>(in, num_ex, num_ft, preds, num_threads);
            break;
        case 5:
            ensemble_predict<uint16_t, true, mc>(in, num_ex, num_ft, preds, num_threads);
            break;
#if defined(Z14_SIMD) || defined(X86_AVX2) || defined(X86_AVX512) || defined(POWER_VMX)
        case 6:
            ensemble_predict_simd<uint16_t, false, mc>(in, num_ex, num_ft, preds, num_threads);
            break;
        case 7:
            ensemble_predict_simd<uint16_t, true, mc>(in, num_ex, num_ft, preds, num_threads);
            break;
#else
        case 6:
            ensemble_predict<uint16_t, false, mc>(in, num_ex, num_ft, preds, num_threads);
            break;
        case 7:
            ensemble_predict<uint16_t, true, mc>(in, num_ex, num_ft, preds, num_threads);
            break;
#endif
        case 8:
            ensemble_predict<uint32_t, false, mc>(in, num_ex, num_ft, preds, num_threads);
            break;
        case 9:
            ensemble_predict<uint32_t, true, mc>(in, num_ex, num_ft, preds, num_threads);
            break;
#if defined(Z14_SIMD) || defined(X86_AVX2) || defined(X86_AVX512) || defined(POWER_VMX)
        case 10:
            ensemble_predict_simd<uint32_t, false, mc>(in, num_ex, num_ft, preds, num_threads);
            break;
        case 11:
            ensemble_predict_simd<uint32_t, true, mc>(in, num_ex, num_ft, preds, num_threads);
            break;
#else
        case 10:
            ensemble_predict<uint32_t, false, mc>(in, num_ex, num_ft, preds, num_threads);
            break;
        case 11:
            ensemble_predict<uint32_t, true, mc>(in, num_ex, num_ft, preds, num_threads);
            break;
#endif
        default:
            // throw error
            break;
        }
    }

    /*=================================================================================================================*/
    /* compressed tree data structure */
    /*=================================================================================================================*/
    std::vector<uint32_t> compr_tree_vector_;

    uint32_t* compr_tree_buf_;
    uint32_t  compr_tree_buf_size_;

    uint32_t compr_model_type_;

    uint32_t               compr_tree_count_;
    uint32_t               compr_tree_ensemble_type_;
    std::vector<bool>      compr_tree_root_type_;
    std::vector<uint8_t>   compr_tree_root_seq_length_;
    std::vector<void*>     compr_tree_root_feature_vector_;
    std::vector<float*>    compr_tree_root_threshold_vector_;
    std::vector<uint32_t*> compr_tree_root_child_ptr_vector_;
};

}

#endif
