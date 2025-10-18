/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2018, 2019, 2021
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
 *
 * End Copyright
 ********************************************************************/

#ifndef GLM_TREE_NODE_HH_
#define GLM_TREE_NODE_HH_

#include "TreeTypes.hpp"
#include <vector>
#include <cmath>

#include "OMP.hpp"

namespace tree {

// type for saving weight and node information
struct ex_md_t {
    uint32_t weight;
    uint32_t node;
    ex_md_t()
        : weight(0)
        , node(0)
    {
    }
};

struct ex_lab_t {
    uint32_t idx;
    float    lab;
    float    sample_weight;
};

// Classification
class ClTreeNode {
public:
    // type for saving histograms for binary classification and regression tasks
    struct hist_bin_t {
        uint32_t weight;        // count
        uint32_t num_pos;       // count of positive examples
        double   sample_weight; // sum of sample_weights as defined by the user in fit
        double   lab_sum;       // sum of labels
        hist_bin_t(uint32_t num_classes = 2)
            : weight(0)
            , num_pos(0)
            , sample_weight(0.0)
            , lab_sum(0.0)
        {
        }
    };

private:
    int32_t  left_child;
    int32_t  right_child;
    uint32_t num_pos;
    uint32_t num_neg;
    double   wnum_pos;
    double   wnum_neg;
    uint32_t num_classes;
    int32_t  parent;
    float    best_score;
    float    best_threshold;
    int32_t  best_feature;
    uint32_t num_pos_left;
    uint32_t num_neg_left;
    double   wnum_pos_left;
    double   wnum_neg_left;
    int32_t  prev_ex;
    float    prev_val;
    uint32_t num_pos_left_best;
    uint32_t num_neg_left_best;
    double   wnum_pos_left_best;
    double   wnum_neg_left_best;

public:
    ClTreeNode()
        : left_child(-1)
        , right_child(-1)
        , num_pos(0)
        , num_neg(0)
        , wnum_pos(0)
        , wnum_neg(0)
        , num_classes(2)
        , parent(-1)
        , best_score(-1.0)
        , best_threshold(0.0)
        , best_feature(-1)
        , num_pos_left(0)
        , num_neg_left(0)
        , wnum_pos_left(0)
        , wnum_neg_left(0)
        , prev_ex(-1)
        , prev_val(0.0)
        , num_pos_left_best(0)
        , num_neg_left_best(0)
        , wnum_pos_left_best(0)
        , wnum_neg_left_best(0)
    {
    }

    ClTreeNode(const ClTreeNode& node)
        : left_child(-1)
        , right_child(-1)
        , num_pos(0)
        , num_neg(0)
        , wnum_pos(0)
        , wnum_neg(0)
        , num_classes(2)
        , parent(-1)
        , best_score(-1.0)
        , best_threshold(0.0)
        , best_feature(-1)
        , num_pos_left(0)
        , num_neg_left(0)
        , wnum_pos_left(0)
        , wnum_neg_left(0)
        , prev_ex(-1)
        , prev_val(0.0)
        , num_pos_left_best(0)
        , num_neg_left_best(0)
        , wnum_pos_left_best(0)
        , wnum_neg_left_best(0)
    {
        copy_node(&node);
    }

    __host__ __device__ void GLM_INLINE copy_node(const ClTreeNode* const in)
    {
        this->left_child         = in->left_child;
        this->right_child        = in->right_child;
        this->num_pos            = in->num_pos;
        this->num_neg            = in->num_neg;
        this->wnum_pos           = in->wnum_pos;
        this->wnum_neg           = in->wnum_neg;
        this->num_classes        = in->num_classes;
        this->parent             = in->parent;
        this->best_score         = in->best_score;
        this->best_threshold     = in->best_threshold;
        this->best_feature       = in->best_feature;
        this->num_pos_left       = in->num_pos_left;
        this->num_neg_left       = in->num_neg_left;
        this->wnum_pos_left      = in->wnum_pos_left;
        this->wnum_neg_left      = in->wnum_neg_left;
        this->prev_ex            = in->prev_ex;
        this->prev_val           = in->prev_val;
        this->num_pos_left_best  = in->num_pos_left_best;
        this->num_neg_left_best  = in->num_neg_left_best;
        this->wnum_pos_left_best = in->wnum_pos_left_best;
        this->wnum_neg_left_best = in->wnum_neg_left_best;
    }

    // sample_weight not supported in histogram mode
    void init_with_hist(const std::vector<hist_bin_t>& hist_bin, uint32_t num_classes = 2)
    {
        this->num_classes = num_classes;

        this->num_pos  = 0;
        this->wnum_pos = 0;
        this->num_neg  = 0;
        this->wnum_neg = 0;

        uint32_t num_ex = 0;
        for (auto& bin : hist_bin) {
            this->num_pos += bin.num_pos;
            this->wnum_pos += bin.lab_sum;
            this->wnum_neg += bin.sample_weight - bin.lab_sum;
            num_ex += bin.weight;
        }

        this->num_neg = num_ex - this->num_pos;
    }

    void init(const std::vector<ex_md_t>& ex_weights, const float* const sample_weight, const double* const labs,
              const std::vector<uint32_t>& indices, const uint32_t& num_ex, uint32_t num_classes,
              double sum_weights = 0)
    {

        const bool            use_indices      = 0 != indices.size();
        const uint32_t        num_ex_effective = use_indices ? indices.size() : num_ex;
        const uint32_t        num_threads      = omp_get_max_threads();
        std::vector<uint32_t> lnum_pos(num_threads, 0);
        std::vector<double>   lwnum_pos(num_threads, 0);

        if (sample_weight == nullptr) {
            // no sample weighting during training
            OMP::parallel([&num_ex_effective, &use_indices, &indices, &labs, &lnum_pos](std::exception_ptr& eptr) {
                const int tid = omp_get_thread_num();
                OMP::_for<int32_t>(0, num_ex_effective, eptr, [&](int32_t i) {
                    const uint32_t ex = use_indices ? indices[i] : i;
                    if (labs[ex] > 0)
                        lnum_pos[tid]++;
                });
            });
        } else {
            // sample weighting during training
            OMP::parallel([&num_ex_effective, &use_indices, &indices, &labs, &lnum_pos, &lwnum_pos,
                           &sample_weight](std::exception_ptr& eptr) {
                const int tid = omp_get_thread_num();
                OMP::_for<int32_t>(0, num_ex_effective, eptr, [&](int32_t i) {
                    const uint32_t ex = use_indices ? indices[i] : i;
                    if (labs[ex] > 0) {
                        lnum_pos[tid]++;
                        lwnum_pos[tid] += sample_weight[ex];
                    }
                });
            });
        }

        this->num_pos = 0;
        for (uint32_t i = 0; i < num_threads; ++i) {
            this->num_pos += lnum_pos[i];
        }
        this->num_neg = num_ex_effective - this->num_pos;

        this->wnum_pos = 0;
        if (sample_weight != nullptr) {
            // sample weighting during training
            for (uint32_t i = 0; i < num_threads; ++i) {
                this->wnum_pos += lwnum_pos[i];
            }
            this->wnum_neg = sum_weights - this->wnum_pos;
        } else {
            // no sample weighting during training
            this->wnum_pos = this->num_pos;
            this->wnum_neg = this->num_neg;
        }
    }

    void reset()
    {
        this->num_pos_left  = 0;
        this->num_neg_left  = 0;
        this->wnum_pos_left = 0;
        this->wnum_neg_left = 0;
        this->prev_ex       = -1;
    }

    // for weighted gini score (sample weights given at training time):
    // the counts are actually weighted counts
    __host__ __device__ static double GLM_INLINE compute_gini_score(const double left_pos_cnt,
                                                                    const double right_pos_cnt,
                                                                    const double left_neg_cnt,
                                                                    const double right_neg_cnt)
    {

        const double pos_cnt  = left_pos_cnt + right_pos_cnt;
        const double neg_cnt  = left_neg_cnt + right_neg_cnt;
        const double n_parent = pos_cnt + neg_cnt;

        const double n_left  = left_pos_cnt + left_neg_cnt;
        const double n_right = right_pos_cnt + right_neg_cnt;

        double score = (pos_cnt * pos_cnt + neg_cnt * neg_cnt) / n_parent;

        if (n_left > 0)
            score -= (left_pos_cnt * left_pos_cnt + left_neg_cnt * left_neg_cnt) / n_left;

        if (n_right > 0)
            score -= (right_pos_cnt * right_pos_cnt + right_neg_cnt * right_neg_cnt) / n_right;

        return score;
    }

    __host__ __device__ void init_node(const ClTreeNode* const in) { *this = *in; }

    __host__ __device__ void GLM_INLINE update_best(const ClTreeNode* in)
    {
        if (-1 != in->best_feature && ((in->best_score < this->best_score) || (-1 == this->best_feature))
            && (in->best_score < 0)) {
            this->best_score         = in->best_score;
            this->best_threshold     = in->best_threshold;
            this->best_feature       = in->best_feature;
            this->num_pos_left_best  = in->num_pos_left_best;
            this->num_neg_left_best  = in->num_neg_left_best;
            this->wnum_pos_left_best = in->wnum_pos_left_best;
            this->wnum_neg_left_best = in->wnum_neg_left_best;
        }
    }

    __host__ __device__ void GLM_INLINE update_best(const uint32_t feature, const float val,
                                                    const uint32_t        min_samples_leaf,
                                                    const snapml::split_t split_criterion, const double lambda)
    {

        const uint32_t num_pos_right  = this->num_pos - this->num_pos_left;
        const uint32_t num_neg_right  = this->num_neg - this->num_neg_left;
        const double   wnum_pos_right = this->wnum_pos - this->wnum_pos_left;
        const double   wnum_neg_right = this->wnum_neg - this->wnum_neg_left;

        // stopping criteria
        if (this->num_pos_left + this->num_neg_left < min_samples_leaf)
            return;
        if (num_pos_right + num_neg_right < min_samples_leaf)
            return;

        const float threshold = val;

        // assert(split_criterion == snapml::split_t::gini);
        float score = compute_gini_score(this->wnum_pos_left, wnum_pos_right, this->wnum_neg_left, wnum_neg_right);

        if (((score < this->best_score) || (this->best_feature == -1)) && (score < 0)) {
            this->best_score         = score;
            this->best_threshold     = threshold;
            this->best_feature       = feature;
            this->num_pos_left_best  = this->num_pos_left;
            this->num_neg_left_best  = this->num_neg_left;
            this->wnum_pos_left_best = this->wnum_pos_left;
            this->wnum_neg_left_best = this->wnum_neg_left;
        }
    }

    __host__ __device__ void GLM_INLINE update_best_hist(const uint32_t feature, const float val,
                                                         uint32_t min_samples_leaf, snapml::split_t split_criterion,
                                                         double lambda)
    {
        return update_best(feature, val, min_samples_leaf, split_criterion, lambda);
    }

    // to do for classification
    __host__ __device__ void GLM_INLINE post_update_best_hist(const hist_bin_t& bin, const int32_t prev_ex = -1,
                                                              const float prev_val = 0.0)
    {
        this->num_pos_left += bin.num_pos;
        this->wnum_pos_left += bin.lab_sum;

        this->num_neg_left += bin.weight - bin.num_pos;
        this->wnum_neg_left += bin.sample_weight - bin.lab_sum;

        if (-1 != prev_ex) {
            this->prev_ex  = prev_ex;
            this->prev_val = prev_val;
        }
    }

    void GLM_INLINE post_update_best(const uint32_t weight, const double label, const double sample_weight,
                                     const int32_t prev_ex = -1, const float prev_val = 0.0)
    {

        if (label > 0) {
            this->num_pos_left += weight;
            this->wnum_pos_left += weight * sample_weight;
        } else {
            this->num_neg_left += weight;
            this->wnum_neg_left += weight * sample_weight;
        }

        if (-1 != prev_ex) {
            this->prev_ex  = prev_ex;
            this->prev_val = prev_val;
        }
    }

    void GLM_INLINE update_parent(const uint32_t left, const uint32_t right)
    {
        this->left_child  = left;
        this->right_child = right;
    }

    void GLM_INLINE update_left_child(const ClTreeNode* const parent, const int32_t parent_idx)
    {
        this->parent      = parent_idx;
        this->num_classes = parent->num_classes;
        this->num_pos     = parent->num_pos_left_best;
        this->num_neg     = parent->num_neg_left_best;
        this->wnum_pos    = parent->wnum_pos_left_best;
        this->wnum_neg    = parent->wnum_neg_left_best;
    }

    void GLM_INLINE update_right_child(const ClTreeNode* const parent, const int32_t parent_idx)
    {
        this->parent      = parent_idx;
        this->num_classes = parent->num_classes;
        this->num_pos     = parent->num_pos - parent->num_pos_left_best;
        this->num_neg     = parent->num_neg - parent->num_neg_left_best;
        this->wnum_pos    = parent->wnum_pos - parent->wnum_pos_left_best;
        this->wnum_neg    = parent->wnum_neg - parent->wnum_neg_left_best;
    }

    bool            stopping_criterion() const { return 0 == this->num_pos || 0 == this->num_neg; }
    int32_t         get_prev_ex() const { return prev_ex; }
    float           get_prev_val() const { return prev_val; }
    int32_t         get_best_feature() const { return best_feature; }
    float           get_best_threshold() const { return best_threshold; }
    int32_t         get_left_child() const { return left_child; }
    int32_t         get_right_child() const { return right_child; }
    int32_t         get_parent() const { return parent; }
    uint32_t        get_num() const { return num_pos + num_neg; }
    uint32_t        get_num_pos() const { return num_pos; }
    uint32_t        get_num_classes() const { return num_classes; }
    float           get_pred_val(double lambda, double max_delta_step) const { return 0; }
    float           get_best_score() const { return best_score; }
    double          get_wnum_pos() const { return wnum_pos; }
    double          get_wnum_neg() const { return wnum_neg; }
    __device__ void set_num_pos(const uint32_t _num_pos) { copyData(&num_pos, _num_pos); }
    __device__ void set_num_neg(const uint32_t _num_neg) { copyData(&num_neg, _num_neg); }
    __device__ void set_wnum_pos(const double _wnum_pos) { copyData(&wnum_pos, _wnum_pos); }
    __device__ void set_wnum_neg(const double _wnum_neg) { copyData(&wnum_neg, _wnum_neg); }
    __device__ void set_num_pos_left(const uint32_t _num_pos_left) { copyData(&num_pos_left, _num_pos_left); }
    __device__ void set_num_neg_left(const uint32_t _num_neg_left) { copyData(&num_neg_left, _num_neg_left); }
    __device__ void set_wnum_pos_left(const double _wnum_pos_left) { copyData(&wnum_pos_left, _wnum_pos_left); }
    __device__ void set_wnum_neg_left(const double _wnum_neg_left) { copyData(&wnum_neg_left, _wnum_neg_left); }
    void            pretty_print(uint32_t node_idx) const
    {
        printf("idx=%u num=%u wnum_pos=%lf\n", node_idx, get_num(), this->wnum_pos);
    }
};

// Multiclass Classification
class MultiClTreeNode {
public:
    // type for saving histograms for multiclass classification
    struct hist_bin_t {
        uint32_t  weight;
        double    sample_weight;
        double    lab_sum;
        uint32_t  num_classes;
        uint32_t* num;
        double*   wnum;

        hist_bin_t(uint32_t num_classes_)
            : weight(0)
            , sample_weight(0.0)
            , lab_sum(0.0)
            , num_classes(num_classes_)
        {
            num  = new uint32_t[num_classes_]();
            wnum = new double[num_classes_]();
        }

        hist_bin_t(const hist_bin_t& in_bin)
            : weight(0)
            , sample_weight(0.0)
            , lab_sum(0.0)
            , num(nullptr)
            , wnum(nullptr)
        {
            this->weight        = (&in_bin)->weight;
            this->sample_weight = (&in_bin)->sample_weight;
            this->lab_sum       = (&in_bin)->lab_sum;
            this->num_classes   = (&in_bin)->num_classes;

            // release memory
            if (this->num != nullptr) {
                delete[] this->num;
                this->num = nullptr;
            }
            if (this->wnum != nullptr) {
                delete[] this->wnum;
                this->wnum = nullptr;
            }

            // allocate memory
            if ((&in_bin)->num != nullptr)
                this->num = new uint32_t[this->num_classes]();
            if ((&in_bin)->wnum != nullptr)
                this->wnum = new double[this->num_classes]();

            // actual deep copy
            for (uint32_t cl = 0; cl < this->num_classes; cl++) {
                if ((&in_bin)->num != nullptr)
                    this->num[cl] = (&in_bin)->num[cl];
                if ((&in_bin)->wnum != nullptr)
                    this->wnum[cl] = (&in_bin)->wnum[cl];
            }
        }

        hist_bin_t& operator=(const hist_bin_t& in_bin)
        {
            if (this == &in_bin)
                return *this; // handle self-assignment

            // Copy scalar values
            this->weight        = (&in_bin)->weight;
            this->sample_weight = (&in_bin)->sample_weight;
            this->lab_sum       = (&in_bin)->lab_sum;
            this->num_classes   = (&in_bin)->num_classes;

            // Release previously allocated memory
            delete[] this->num;
            delete[] this->wnum;
            this->num  = nullptr;
            this->wnum = nullptr;

            // Allocate and copy arrays if present in source
            if (in_bin.num != nullptr)
                this->num = new uint32_t[this->num_classes]();
            if (in_bin.wnum != nullptr)
                this->wnum = new double[this->num_classes]();

            // Deep copy contents
            for (uint32_t cl = 0; cl < this->num_classes; ++cl) {
                if (in_bin.num != nullptr)
                    this->num[cl] = in_bin.num[cl];
                if (in_bin.wnum != nullptr)
                    this->wnum[cl] = in_bin.wnum[cl];
            }

            return *this;
        }

        ~hist_bin_t()
        {
            if (num)
                delete[] num;
            if (wnum)
                delete[] wnum;
        }
    };

private:
    int32_t   left_child;
    int32_t   right_child;
    int32_t   parent;
    float     best_score;
    float     best_threshold;
    int32_t   best_feature;
    int32_t   prev_ex;
    float     prev_val;
    uint32_t  num_classes;
    uint32_t* num;
    uint32_t* num_left;
    uint32_t* num_left_best;
    double*   wnum;
    double*   wnum_left;
    double*   wnum_left_best;

public:
    MultiClTreeNode()
        : left_child(-1)
        , right_child(-1)
        , parent(-1)
        , best_score(-1.0)
        , best_threshold(0.0)
        , best_feature(-1)
        , prev_ex(-1)
        , prev_val(0.0)
        , num_classes(2)
        , num(nullptr)
        , num_left(nullptr)
        , num_left_best(nullptr)
        , wnum(nullptr)
        , wnum_left(nullptr)
        , wnum_left_best(nullptr)
    {
    }

    ~MultiClTreeNode() { release_memory(); }

    MultiClTreeNode(const MultiClTreeNode& node)
        : left_child(-1)
        , right_child(-1)
        , parent(-1)
        , best_score(-1.0)
        , best_threshold(0.0)
        , best_feature(-1)
        , prev_ex(-1)
        , prev_val(0.0)
        , num_classes(2)
        , num(nullptr)
        , num_left(nullptr)
        , num_left_best(nullptr)
        , wnum(nullptr)
        , wnum_left(nullptr)
        , wnum_left_best(nullptr)
    {
        copy_node(&node);
    }

    void release_memory()
    {
        if (num != nullptr) {
            delete[] num;
            num = nullptr;
        }
        if (num_left != nullptr) {
            delete[] num_left;
            num_left = nullptr;
        }
        if (num_left_best != nullptr) {
            delete[] num_left_best;
            num_left_best = nullptr;
        }
        if (wnum != nullptr) {
            delete[] wnum;
            wnum = nullptr;
        }
        if (wnum_left != nullptr) {
            delete[] wnum_left;
            wnum_left = nullptr;
        }
        if (wnum_left_best != nullptr) {
            delete[] wnum_left_best;
            wnum_left_best = nullptr;
        }
    }

    void allocate_memory()
    {
        release_memory();
        num            = new uint32_t[this->num_classes]();
        num_left       = new uint32_t[this->num_classes]();
        num_left_best  = new uint32_t[this->num_classes]();
        wnum           = new double[this->num_classes]();
        wnum_left      = new double[this->num_classes]();
        wnum_left_best = new double[this->num_classes]();
    }

    // sample_weight not supported in histogram mode
    void init_with_hist(const std::vector<MultiClTreeNode::hist_bin_t>& hist_bin, uint32_t num_classes)
    {
        this->num_classes = num_classes;
        allocate_memory();

        for (auto& bin : hist_bin) {
            for (uint32_t cl = 0; cl < num_classes; cl++) {
                this->num[cl] += bin.num[cl];
                this->wnum[cl] += bin.wnum[cl];
            }
        }
    }

    void init(const std::vector<ex_md_t>& ex_weights, const float* const sample_weight, const double* const labs,
              const std::vector<uint32_t>& indices, const uint32_t& num_ex, uint32_t num_classes,
              double sum_weights = 0)
    {

        const bool     use_indices      = 0 != indices.size();
        const uint32_t num_ex_effective = use_indices ? indices.size() : num_ex;

        this->num_classes = num_classes;
        allocate_memory();

        // TODO: parallelize across multiple threads
        if (sample_weight == nullptr) {
            // no sample weighting during training
            for (int32_t i = 0; i < num_ex_effective; i++) {
                const uint32_t ex = use_indices ? indices[i] : i;
                this->num[(uint32_t)labs[ex]]++;
            }
            for (int32_t cl = 0; cl < num_classes; cl++) {
                this->wnum[cl] = this->num[cl];
            }
        } else {
            // sample weighting during training
            for (int32_t i = 0; i < num_ex_effective; i++) {
                const uint32_t ex = use_indices ? indices[i] : i;
                this->num[(uint32_t)labs[ex]]++;
                this->wnum[(uint32_t)labs[ex]] += sample_weight[ex];
            }
        }

        // std::cout << "num_pos = " << this->num_pos << " num_neg = " << this->num_neg << " wnum_pos = " <<
        // this->wnum_pos << " wnum_neg = " << this->wnum_neg <<  std::endl;
    }

    void reset()
    {
        for (uint32_t cl = 0; cl < this->num_classes; cl++) {
            this->num_left[cl]  = 0;
            this->wnum_left[cl] = 0;
        }
        this->prev_ex = -1;
    }

    // for weighted gini score (sample weights given at training time):
    // the counts are actually weighted counts
    __host__ __device__ static double GLM_INLINE compute_gini_score(const double left_cnt[], const double parent_cnt[],
                                                                    const uint32_t num_classes)
    {

        double n_parent = 0;
        double n_left   = 0;
        double n_right  = 0;

        for (uint32_t cl = 0; cl < num_classes; cl++) {
            n_left += left_cnt[cl];
            n_parent += parent_cnt[cl];
        }

        n_right = n_parent - n_left;

        // TODO: optimize, same value for all features
        double score = 0.0;
        for (uint32_t cl = 0; cl < num_classes; cl++) {
            score += parent_cnt[cl] * parent_cnt[cl];
        }

        score /= n_parent;

        if (n_left > 0) {
            double tmp = 0;
            for (uint32_t cl = 0; cl < num_classes; cl++) {
                tmp += left_cnt[cl] * left_cnt[cl];
            }
            score -= tmp / n_left;
        }

        if (n_right > 0) {
            double tmp = 0;
            for (uint32_t cl = 0; cl < num_classes; cl++) {
                tmp += (parent_cnt[cl] - left_cnt[cl]) * (parent_cnt[cl] - left_cnt[cl]);
            }
            score -= tmp / n_right;
        }

        return score;
    }

    __host__ __device__ void init_node(const MultiClTreeNode* const in) { *this = *in; }

    __host__ __device__ void GLM_INLINE copy_node(const MultiClTreeNode* const in)
    {

        this->left_child     = in->left_child;
        this->right_child    = in->right_child;
        this->parent         = in->parent;
        this->best_score     = in->best_score;
        this->best_threshold = in->best_threshold;
        this->best_feature   = in->best_feature;
        this->prev_ex        = in->prev_ex;
        this->prev_val       = in->prev_val;
        this->num_classes    = in->num_classes;

        // release memory
        if (this->num != nullptr) {
            delete[] this->num;
            this->num = nullptr;
        }
        if (this->num_left != nullptr) {
            delete[] this->num_left;
            this->num_left = nullptr;
        }
        if (this->num_left_best != nullptr) {
            delete[] this->num_left_best;
            this->num_left_best = nullptr;
        }
        if (this->wnum != nullptr) {
            delete[] this->wnum;
            this->wnum = nullptr;
        }
        if (this->wnum_left != nullptr) {
            delete[] this->wnum_left;
            this->wnum_left = nullptr;
        }
        if (this->wnum_left_best != nullptr) {
            delete[] this->wnum_left_best;
            this->wnum_left_best = nullptr;
        }

        // allocate memory
        if (in->num != nullptr)
            this->num = new uint32_t[this->num_classes]();
        if (in->num_left != nullptr)
            this->num_left = new uint32_t[this->num_classes]();
        if (in->num_left_best != nullptr)
            this->num_left_best = new uint32_t[this->num_classes]();
        if (in->wnum != nullptr)
            this->wnum = new double[this->num_classes]();
        if (in->wnum_left != nullptr)
            this->wnum_left = new double[this->num_classes]();
        if (in->wnum_left_best != nullptr)
            this->wnum_left_best = new double[this->num_classes]();

        // actual deep copy
        for (uint32_t cl = 0; cl < in->num_classes; cl++) {
            if (in->num != nullptr)
                this->num[cl] = in->num[cl];
            if (in->num_left != nullptr)
                this->num_left[cl] = in->num_left[cl];
            if (in->num_left_best != nullptr)
                this->num_left_best[cl] = in->num_left_best[cl];
            if (in->wnum != nullptr)
                this->wnum[cl] = in->wnum[cl];
            if (in->wnum_left != nullptr)
                this->wnum_left[cl] = in->wnum_left[cl];
            if (in->wnum_left_best != nullptr)
                this->wnum_left_best[cl] = in->wnum_left_best[cl];
        }
    }

    __host__ __device__ void GLM_INLINE update_best(const MultiClTreeNode* const in)
    {
        if (-1 != in->best_feature && ((in->best_score < this->best_score) || (-1 == this->best_feature))
            && (in->best_score < 0)) {
            this->best_score     = in->best_score;
            this->best_threshold = in->best_threshold;
            this->best_feature   = in->best_feature;
            for (uint32_t cl = 0; cl < in->num_classes; cl++) {
                this->num_left_best[cl]  = in->num_left_best[cl];
                this->wnum_left_best[cl] = in->wnum_left_best[cl];
            }
        }
    }

    __host__ __device__ void GLM_INLINE update_best(const uint32_t feature, const float val,
                                                    const uint32_t        min_samples_leaf,
                                                    const snapml::split_t split_criterion, const double lambda)
    {

        uint32_t num_left_  = 0;
        uint32_t num_right_ = 0;

        for (uint32_t cl = 0; cl < this->num_classes; cl++) {
            num_left_ += this->num_left[cl];
            num_right_ += this->num[cl] - this->num_left[cl];
        }

        // stopping criteria
        if (num_left_ < min_samples_leaf)
            return;
        if (num_right_ < min_samples_leaf)
            return;

        const float threshold = val;

        float score = compute_gini_score(this->wnum_left, this->wnum, this->num_classes);

        if (((score < this->best_score) || (this->best_feature == -1)) && (score < 0)) {
            this->best_score     = score;
            this->best_threshold = threshold;
            this->best_feature   = feature;

            for (uint32_t cl = 0; cl < this->num_classes; cl++) {
                this->num_left_best[cl]  = this->num_left[cl];
                this->wnum_left_best[cl] = this->wnum_left[cl];
            }
        }
    }

    __host__ __device__ void GLM_INLINE update_best_hist(const uint32_t feature, const float val,
                                                         uint32_t min_samples_leaf, snapml::split_t split_criterion,
                                                         double lambda)
    {
        return update_best(feature, val, min_samples_leaf, split_criterion, lambda);
    }

    __host__ __device__ void GLM_INLINE post_update_best_hist(const MultiClTreeNode::hist_bin_t& bin,
                                                              const int32_t prev_ex = -1, const float prev_val = 0.0)
    {

        for (uint32_t cl = 0; cl < this->num_classes; cl++) {
            this->num_left[cl] += bin.num[cl];   // num_pos;
            this->wnum_left[cl] += bin.wnum[cl]; // lab_sum;
        }

        if (-1 != prev_ex) {
            this->prev_ex  = prev_ex;
            this->prev_val = prev_val;
        }
    }

    void GLM_INLINE post_update_best(const uint32_t weight, const double label, const double sample_weight,
                                     const int32_t prev_ex = -1, const float prev_val = 0.0)
    {

        this->num_left[(uint32_t)label] += weight;
        this->wnum_left[(uint32_t)label] += weight * sample_weight;

        if (-1 != prev_ex) {
            this->prev_ex  = prev_ex;
            this->prev_val = prev_val;
        }
    }

    void GLM_INLINE update_parent(const uint32_t left, const uint32_t right)
    {
        this->left_child  = left;
        this->right_child = right;
    }

    void GLM_INLINE update_left_child(const MultiClTreeNode* const parent, const int32_t parent_idx)
    {
        this->parent      = parent_idx;
        this->num_classes = parent->num_classes;
        allocate_memory();

        for (uint32_t cl = 0; cl < parent->num_classes; cl++) {
            this->num[cl]  = parent->num_left_best[cl];
            this->wnum[cl] = parent->wnum_left_best[cl];
        }
    }

    void GLM_INLINE update_right_child(const MultiClTreeNode* const parent, const int32_t parent_idx)
    {
        this->parent      = parent_idx;
        this->num_classes = parent->num_classes;
        allocate_memory();

        for (uint32_t cl = 0; cl < parent->num_classes; cl++) {
            this->num[cl]  = parent->num[cl] - parent->num_left_best[cl];
            this->wnum[cl] = parent->wnum[cl] - parent->wnum_left_best[cl];
        }
    }

    bool stopping_criterion() const
    {
        uint32_t is_pure = 0;
        for (uint32_t cl = 0; cl < this->num_classes; cl++) {
            if (this->num[cl] > 0)
                is_pure++;
        }
        return (1 == is_pure);
    }

    int32_t get_prev_ex() const { return prev_ex; }
    float   get_prev_val() const { return prev_val; }
    int32_t get_best_feature() const { return best_feature; }
    float   get_best_threshold() const { return best_threshold; }
    int32_t get_left_child() const { return left_child; }
    int32_t get_right_child() const { return right_child; }
    int32_t get_parent() const { return parent; }

    uint32_t get_num() const
    {
        uint32_t n = 0;
        for (uint32_t cl = 0; cl < num_classes; cl++)
            n = n + num[cl];
        return n;
    }

    uint32_t get_num_classes() const { return num_classes; }

    float get_pred_val(double lambda, double max_delta_step) const { return 0; }
    float get_best_score() const { return best_score; }
    /* double get_wnum(uint32_t i) const {return wnum[i]; }
    would be more appropriate but it would require error
    handling if i>= num_classes
    */
    double* get_wnum() const { return wnum; }

    void pretty_print(uint32_t node_idx) const
    {
        printf("idx=%u num=%u ", node_idx, get_num());
        for (uint32_t cl = 0; cl < this->num_classes; cl++)
            printf("wnum[%u]=%lf ", cl, this->wnum[cl]);
        printf("best_feature = %d best_threshold=%f", this->best_feature, this->best_threshold);
        printf("\n");
    }
};

// Regression
class RegTreeNode {
public:
    // type for saving histograms for binary classification and regression tasks
    struct hist_bin_t {
        uint32_t weight;        // count
        uint32_t num_pos;       // count of positive examples
        double   sample_weight; // sum of sample_weights as defined by the user in fit
        double   lab_sum;       // sum of labels
        hist_bin_t(uint32_t num_classes = 1)
            : weight(0)
            , num_pos(0)
            , sample_weight(0.0)
            , lab_sum(0.0)
        {
        }
    };

private:
    int32_t  left_child;
    int32_t  right_child;
    int32_t  parent;
    uint32_t num;
    double   wnum;
    double   sum;
    uint32_t num_left;
    double   wnum_left;
    double   sum_left;
    uint32_t num_classes;
    float    best_score;
    float    best_threshold;
    int32_t  best_feature;
    uint32_t num_left_best;
    double   wnum_left_best;
    double   sum_left_best;
    int32_t  prev_ex;
    float    prev_val;

public:
    RegTreeNode()
        : left_child(-1)
        , right_child(-1)
        , parent(-1)
        , num(0)
        , wnum(0)
        , sum(0)
        , num_left(0)
        , wnum_left(0)
        , sum_left(0)
        , num_classes(1)
        , best_score(0.0)
        , best_threshold(0.0)
        , best_feature(-1)
        , num_left_best(0)
        , wnum_left_best(0)
        , sum_left_best(0)
        , prev_ex(-1)
        , prev_val(0.0)
    {
    }

    RegTreeNode(const RegTreeNode& node)
        : left_child(-1)
        , right_child(-1)
        , parent(-1)
        , num(0)
        , wnum(0)
        , sum(0)
        , num_left(0)
        , wnum_left(0)
        , sum_left(0)
        , num_classes(1)
        , best_score(0.0)
        , best_threshold(0.0)
        , best_feature(-1)
        , num_left_best(0)
        , wnum_left_best(0)
        , sum_left_best(0)
        , prev_ex(-1)
        , prev_val(0.0)
    {
        copy_node(&node);
    }

    __host__ __device__ void GLM_INLINE copy_node(const RegTreeNode* const in)
    {
        this->left_child     = in->left_child;
        this->right_child    = in->right_child;
        this->parent         = in->parent;
        this->num            = in->num;
        this->wnum           = in->wnum;
        this->sum            = in->sum;
        this->num_left       = in->num_left;
        this->wnum_left      = in->wnum_left;
        this->sum_left       = in->sum_left;
        this->num_classes    = in->num_classes;
        this->best_score     = in->best_score;
        this->best_threshold = in->best_threshold;
        this->best_feature   = in->best_feature;
        this->num_left_best  = in->num_left_best;
        this->wnum_left_best = in->wnum_left_best;
        this->sum_left_best  = in->sum_left_best;
        this->prev_ex        = in->prev_ex;
        this->prev_val       = in->prev_val;
    }

    void init_with_hist(const std::vector<hist_bin_t>& hist_bin, uint32_t num_classes = 1)
    {
        this->num  = 0;
        this->sum  = 0.0;
        this->wnum = 0.0;

        for (auto& bin : hist_bin) {
            this->num += bin.weight;
            this->wnum += bin.sample_weight;
            this->sum += bin.lab_sum;
        }
    }

    void init(const std::vector<ex_md_t>& ex_weights, const float* const sample_weight, const double* const labs,
              const std::vector<uint32_t>& indices, const uint32_t& num_ex, uint32_t num_classes,
              double sum_weights = 0)
    {
        const bool     use_indices      = 0 != indices.size();
        const uint32_t num_ex_effective = use_indices ? indices.size() : num_ex;
        const uint32_t num_threads      = omp_get_max_threads();

        // TODO: use ex_weights, not indices
        this->num = num_ex_effective;
        std::vector<double> lsum(num_threads, 0.0);
        std::vector<double> lwnum(num_threads, 0.0);

        if (sample_weight == nullptr) {
            OMP::parallel([&num_ex_effective, &use_indices, &indices, &lsum, &labs](std::exception_ptr& eptr) {
                const int tid = omp_get_thread_num();

                OMP::_for<int32_t>(0, num_ex_effective, eptr, [&](int32_t i) {
                    const uint32_t idx = use_indices ? indices[i] : i;
                    lsum[tid] += labs[idx];
                });
            });
            this->sum  = 0.0;
            this->wnum = num_ex_effective;
            for (uint32_t i = 0; i < num_threads; ++i) {
                this->sum += lsum[i];
            }
            return;
        }
        OMP::parallel([&num_ex_effective, &use_indices, &indices, &sample_weight, &labs, &lsum,
                       &lwnum](std::exception_ptr& eptr) {
            const int tid = omp_get_thread_num();

            OMP::_for<int32_t>(0, num_ex_effective, eptr, [&](int32_t i) {
                const uint32_t idx = use_indices ? indices[i] : i;
                const float    sl  = sample_weight[idx] * labs[idx];
                lsum[tid] += sl;
                lwnum[tid] += sample_weight[idx];
            });
        });
        this->sum  = 0.0;
        this->wnum = 0.0;
        for (uint32_t i = 0; i < num_threads; ++i) {
            this->sum += lsum[i];
            this->wnum += lwnum[i];
        }
    }

    void reset()
    {
        this->num_left  = 0;
        this->wnum_left = 0;
        this->sum_left  = 0;
        this->prev_ex   = -1;
    }

    // for weighted MSE (sample weights given at training time):
    // num_* is the sum of the weights, sum_* is the weighted sum of the labels
    __host__ __device__ static double GLM_INLINE compute_mse_score(const double num_left, const double num_right,
                                                                   const double sum_left, const double sum_right,
                                                                   const double lambda)
    {

        const double left   = -sum_left * sum_left / (num_left + lambda);
        const double right  = -sum_right * sum_right / (num_right + lambda);
        const double parent = -(sum_left + sum_right) * (sum_left + sum_right) / (num_left + num_right + lambda);
        return (left + right - parent);
    }

    __host__ __device__ void init_node(const RegTreeNode* const in) { *this = *in; }

    __host__ __device__ void GLM_INLINE update_best(const RegTreeNode* in)
    {
        if (-1 != in->best_feature && ((in->best_score < this->best_score) || (-1 == this->best_feature))
            && (in->best_score < 0)) {
            this->best_score     = in->best_score;
            this->best_threshold = in->best_threshold;
            this->best_feature   = in->best_feature;
            this->num_left_best  = in->num_left_best;
            this->wnum_left_best = in->wnum_left_best;
            this->sum_left_best  = in->sum_left_best;
        }
    }

    __host__ __device__ void GLM_INLINE update_best(const uint32_t feature, const float val, uint32_t min_samples_leaf,
                                                    snapml::split_t split_criterion, double lambda)
    {
        const float threshold = (this->prev_val + val) / 2;
        update_best_common(feature, threshold, min_samples_leaf, split_criterion, lambda);
    }

    __host__ __device__ void GLM_INLINE update_best_hist(const uint32_t feature, const float val,
                                                         uint32_t min_samples_leaf, snapml::split_t split_criterion,
                                                         double lambda)
    {
        const float threshold = val;
        update_best_common(feature, threshold, min_samples_leaf, split_criterion, lambda);
    }

    __host__ __device__ void GLM_INLINE post_update_best_hist(const hist_bin_t& bin, const int32_t prev_ex = -1,
                                                              const float prev_val = 0.0)
    {
        this->num_left += bin.weight;
        this->wnum_left += bin.sample_weight;
        this->sum_left += bin.lab_sum;

        if (-1 != prev_ex) {
            this->prev_ex  = prev_ex;
            this->prev_val = prev_val;
        }
    }

    void GLM_INLINE post_update_best(const uint32_t weight, const double label, const double sample_weight,
                                     const int32_t prev_ex = -1, const float prev_val = 0.0)
    {

        const uint32_t num_left  = weight;
        const double   wnum_left = weight * sample_weight;
        const double   sum_left  = weight * sample_weight * label;

        this->num_left += num_left;
        this->wnum_left += wnum_left;
        this->sum_left += sum_left;

        if (-1 != prev_ex) {
            this->prev_ex  = prev_ex;
            this->prev_val = prev_val;
        }
    }

    void GLM_INLINE update_parent(const uint32_t left, const uint32_t right)
    {
        this->left_child  = left;
        this->right_child = right;
    }

    void GLM_INLINE update_left_child(const RegTreeNode* const parent, const int32_t parent_idx)
    {
        this->parent = parent_idx;
        this->sum    = parent->sum_left_best;
        this->num    = parent->num_left_best;
        this->wnum   = parent->wnum_left_best;
    }

    void GLM_INLINE update_right_child(const RegTreeNode* const parent, const int32_t parent_idx)
    {
        this->parent = parent_idx;
        this->sum    = parent->sum - parent->sum_left_best;
        this->num    = parent->num - parent->num_left_best;
        this->wnum   = parent->wnum - parent->wnum_left_best;
    }

    bool     stopping_criterion() const { return false; }
    int32_t  get_prev_ex() const { return prev_ex; }
    float    get_prev_val() const { return prev_val; }
    int32_t  get_best_feature() const { return best_feature; }
    float    get_best_threshold() const { return best_threshold; }
    float    get_best_score() const { return best_score; }
    int32_t  get_left_child() const { return left_child; }
    int32_t  get_right_child() const { return right_child; }
    int32_t  get_parent() const { return parent; }
    uint32_t get_num() const { return num; }
    uint32_t get_num_classes() const { return num_classes; }
    float    get_pred_val(double lambda, double max_delta_step) const
    {
        double dw = sum / (wnum + lambda);
        if (max_delta_step > 0) {
            if (std::abs(dw) > max_delta_step)
                dw = std::copysign(max_delta_step, dw);
        }
        return dw;
    }
    double                   get_sum() const { return sum; }
    double                   get_wnum() const { return wnum; }
    __device__ void          set_num(const uint32_t _num) { copyData(&num, _num); }
    __device__ void          set_wnum(const double _wnum) { copyData(&wnum, _wnum); }
    __device__ void          set_sum(const double _sum) { copyData(&sum, _sum); }
    __device__ void          set_num_left(const uint32_t _num_left) { copyData(&num_left, _num_left); }
    __device__ void          set_wnum_left(const double _wnum_left) { copyData(&wnum_left, _wnum_left); }
    __device__ void          set_sum_left(const double _sum_left) { copyData(&sum_left, _sum_left); }
    __host__ __device__ void update_best_common(const uint32_t feature, const float threshold,
                                                uint32_t min_samples_leaf, snapml::split_t split_criterion,
                                                double lambda)
    {
        const uint32_t num_right = this->num - this->num_left;
        const uint32_t num_left  = this->num_left;
        if (num_left < min_samples_leaf || num_right < min_samples_leaf)
            return;
        const double wnum_right = this->wnum - this->wnum_left;
        const double sum_right  = this->sum - this->sum_left;

        // if the remaining weight on the right is very tiny numerical errors in the above subtraction
        // can lead to a zero wnum, which causes non-finte outcomes in the mse computation.
        // we could solve these numerical errors either by using Kahan summation
        // or by increasing MIN_VAL_HESSIAN. for now, let's just avoid these splits.
        if (wnum_right == 0) {
            return;
        }

        double score = compute_mse_score(this->wnum_left, wnum_right, this->sum_left, sum_right, lambda);

        /* update criterion */
        if (((score < this->best_score) || (this->best_feature == -1)) && (score < 0)) {
            this->best_score     = score;
            this->best_threshold = threshold;
            this->best_feature   = feature;
            this->num_left_best  = this->num_left;
            this->wnum_left_best = this->wnum_left;
            this->sum_left_best  = this->sum_left;
        }
    }
    void pretty_print(uint32_t node_idx) const
    {
        printf("idx=%u num=%u wnum=%lf sum=%lf num_left=%u wnum_left=%lf sum_left=%lf best_score=%f best_ft=%d "
               "best_thr=%lf\n",
               node_idx, get_num(), this->wnum, this->sum, this->num_left, this->wnum_left, this->sum_left,
               this->best_score, this->best_feature, this->best_threshold);
    }
};

} // namespace tree
#endif // GLM_TREE_NODE_HH_
