/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2019, 2021
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Nikolas Ioannou
 *                Thomas Parnell
 *
 * End Copyright
 ********************************************************************/

#ifndef _LIBGLM_HIST_SOLVER_
#define _LIBGLM_HIST_SOLVER_

#include <vector>
#include <memory>

#include "DecisionTreeParams.hpp"
#include "Dataset.hpp"
#include "TreeNode.hpp"

//#define TIME_PROFILE

namespace tree {

template <class N> class HistSolver {
#define MAX_STREAM_NR 8U
public:
    virtual ~HistSolver<N>() { }

    virtual void    init(glm::Dataset* const data, const snapml::DecisionTreeParams params) = 0;
    virtual void    set_thread_context()                                                    = 0;
    virtual double* retrieve_preds()                                                        = 0;

    virtual void retrieve_nex(const N* const node, const uint32_t node_idx, const uint32_t depth,
                              std::unique_ptr<std::vector<ex_lab_t>>& nex)
        = 0;
    virtual void update_node_size(const uint32_t new_size, const bool shuffle) = 0;

    virtual void init_fts(const std::vector<uint32_t>& fts, const uint32_t num_ft_effective,
                          const uint32_t random_state)
        = 0;

    virtual void init_nex_labs(const std::vector<uint32_t>& indices, const float* sample_weights, const double* labs)
        = 0;

    virtual void update_training_preds(const N* const node, uint32_t node_idx, const uint32_t depth) = 0;

    // virtual void split_ex_and_recompute_hist_bins(// input variables
    //                                       const uint32_t best_ft, const float best_thr, const bool left_gt,
    //                                       const bool ret_after_split,
    //                                       const N *const left, const N *const right,
    //                                       const uint32_t parent_idx, const uint32_t left_idx, const uint32_t
    //                                       right_idx,
    //                                       // input/output variables
    //                                       std::unique_ptr<std::vector<std::vector<hist_bin_t>> > &hist_bins_p,
    //                                       std::unique_ptr<std::vector<std::vector<hist_bin_t>> > &new_hist_lt,
    //                                       std::unique_ptr<std::vector<std::vector<hist_bin_t>> > &new_hist_gt) = 0;
    virtual void process_initial_node(uint32_t len, uint32_t root_idx, N* root) = 0;
    virtual int  process_node_pair(uint32_t depth, uint32_t parent_idx, uint32_t left_idx, uint32_t right_idx, N* left,
                                   N* right)
        = 0;
    virtual int process_single_node(const uint32_t len, const uint32_t depth, const uint32_t node_idx, N* const node,
                                    const bool is_sibling = false, const int32_t parent_idx = -1,
                                    const int32_t sibling_idx = -1)
        = 0;
    virtual void split_single_node(uint32_t best_ft, float best_thr, uint32_t depth, const N* left, const N* right,
                                   uint32_t parent_idx, uint32_t left_idx, uint32_t right_idx)
        = 0;
}; // class HistSolver

};     // namespace tree
#endif // _LIBGLM_HIST_SOLVER_
