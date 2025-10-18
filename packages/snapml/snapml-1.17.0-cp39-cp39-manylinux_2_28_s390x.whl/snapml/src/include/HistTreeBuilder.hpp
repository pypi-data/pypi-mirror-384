/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2018, 2020, 2021
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Celestine Duenner
 *                Andreea Anghel
 *                Thomas Parnell
 *                Nikolas Ioannou
 *                Nikolaos Papandreou
 *                Milos Stanisavljevic
 *
 * End Copyright
 ********************************************************************/

#ifndef HIST_TREE_BUILDER
#define HIST_TREE_BUILDER

#include "DecisionTreeBuilderInt.hpp"
#include "TreeInvariants.hpp"
#include "TreeNode.hpp"

#include <stack>
#include <mutex>

namespace tree {

template <class N> class HistTreeBuilder : public DecisionTreeBuilder<N> {

public:
    typedef std::chrono::high_resolution_clock             Clock;
    typedef std::chrono::high_resolution_clock::time_point CurTime;
    typedef typename N::hist_bin_t                         hist_bin_t;

    // ctor without TreeInvariants (for standalone use)
    HistTreeBuilder<N>(glm::DenseDataset* data, snapml::DecisionTreeParams params)
        : DecisionTreeBuilder<N>(static_cast<glm::Dataset*>(data), params)

    {
        validate_hist_tree_parameters();
    }

    // ctor with TreeInvariants (for use within an ensemble)
    HistTreeBuilder<N>(glm::DenseDataset* data, snapml::DecisionTreeParams params,
                       const std::shared_ptr<glm::TreeInvariants<glm::DenseDataset>> tree_invariants)
        : DecisionTreeBuilder<N>(static_cast<glm::Dataset*>(data), params, tree_invariants)

    {
        validate_hist_tree_parameters();
    }

    ~HistTreeBuilder<N>() { }

    const double* get_training_predictions() { return training_predictions_.data(); }

    void clear_training_predictions()
    {
        training_predictions_.clear();
        training_predictions_.shrink_to_fit();
    }

protected:
    virtual void build_tree_impl(const float* const sample_weight) = 0;
    virtual void init_invariants()                                 = 0;

    void validate_hist_tree_parameters() { hist_nbins_ = std::min(this->params_.hist_nbins, 256U); }

    // updates hist bins based on number of examples in this node (nex)
    // returns number of non-empty bins
    template <bool initial>
    uint32_t recompute_hist_bin(const std::vector<ex_lab_t>& nex, const std::vector<std::vector<uint8_t>>& ex_to_bin,
                                std::unique_ptr<std::vector<std::vector<hist_bin_t>>>& hist_bins_p,
                                const uint32_t                                         num_ft_to_compute)
    {

#ifdef TIME_PROFILE
        CurTime t1, t2;
        if (omp_get_thread_num() == 0)
            t1 = Clock::now();
#endif

        auto& hist = *hist_bins_p;

        OMP::parallel_for<int32_t>(0, num_ft_to_compute, [this, &nex, &ex_to_bin, &hist](const int32_t& ftp) {
            const uint32_t ft = this->fts_[ftp];
            for (uint32_t i = 0; i < nex.size(); ++i) {
                const uint32_t ex            = nex[i].idx;
                const float    lab           = nex[i].lab;
                const float    sample_weight = nex[i].sample_weight;
                const float    tmp1          = sample_weight * lab;
                const uint8_t  bin_idx       = ex_to_bin[ft][ex];
                auto&          bin           = hist[ft][bin_idx];
                update_bin<initial>(bin, 1, sample_weight, tmp1, lab);
            }
        });

#ifdef DEBUG_VERIFY
        for (uint32_t ftp = 0; ftp < num_ft_to_compute; ++ftp) {
            const uint32_t ft = this->fts_[ftp];
            for (uint32_t bin = 0; bin < hist[ft].size(); ++bin)
                fprintf(stdout, "ft=%u bin=%u weight=%u lab_sum=%.4f\n", ft, bin, (*hist_bins_p)[ft][bin].weight,
                        (*hist_bins_p)[ft][bin].lab_sum);
        }
#endif

#ifdef TIME_PROFILE
        if (omp_get_thread_num() == 0) {
            t2            = Clock::now();
            auto   dur    = t2 - t1;
            double t_elap = (double)dur.count() / 1.0e9;
            printf("[BinaryDecisionTree::recompute_hist_bin] t_elap = %f\n", t_elap);
        }
#endif
        // return tot_bins;
        return 2 * this->num_ft_;
    }

    template <bool initial>
    inline void update_bin(hist_bin_t& bin, const uint32_t weight, const double sample_weight, const double lab_sum,
                           const uint32_t num_pos)
    {
        if (!initial) {
            bin.weight += weight;
        }
        bin.sample_weight += sample_weight;
        bin.lab_sum += lab_sum;
        bin.num_pos += num_pos;
    }

    void update_training_predictions(N* node, const std::unique_ptr<std::vector<ex_lab_t>>& nex)
    {
        double pred_val = node->get_pred_val(this->params_.lambda, this->params_.max_delta_step);
        OMP::parallel_for<int32_t>(0, node->get_num(), [this, &nex, &pred_val](const int32_t& i) {
            uint32_t ex = (*nex)[i].idx;
            assert(std::numeric_limits<double>::max() == training_predictions_[ex]);
            training_predictions_[ex] = pred_val;
        });
    }

    uint32_t hist_nbins_;

    std::vector<double>  training_predictions_;
    std::vector<uint8_t> go_left_;
};

template <>
template <>
inline void HistTreeBuilder<MultiClTreeNode>::update_bin<true>(MultiClTreeNode::hist_bin_t& bin, const uint32_t weight,
                                                               const double sample_weight, const double lab_sum,
                                                               const uint32_t num_pos)
{

    bin.sample_weight += sample_weight;
    bin.lab_sum += lab_sum;

    bin.num[num_pos] += weight;
    bin.wnum[num_pos] += sample_weight; // lab_sum;
}

template <>
template <>
inline void HistTreeBuilder<MultiClTreeNode>::update_bin<false>(MultiClTreeNode::hist_bin_t& bin, const uint32_t weight,
                                                                const double sample_weight, const double lab_sum,
                                                                const uint32_t num_pos)
{

    bin.weight += weight;
    bin.sample_weight += sample_weight;
    bin.lab_sum += lab_sum;

    bin.num[num_pos] += weight;
    bin.wnum[num_pos] += sample_weight; // lab_sum;
}

}

#endif
