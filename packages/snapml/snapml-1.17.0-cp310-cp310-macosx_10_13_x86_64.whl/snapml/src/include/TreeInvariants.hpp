/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2019, 2020
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

#ifndef _LIBGLM_SORTED_MATRIX_
#define _LIBGLM_SORTED_MATRIX_

#include <algorithm>
#include <cassert>
#include <chrono>
#include <vector>

#include "OMP.hpp"
#include "Dataset.hpp"
#include "TreeTypes.hpp"
#include "TreeUtils.hpp"

//#define TIME_PROFILE

namespace glm {

template <class D> class TreeInvariants final {
public:
    TreeInvariants<D>() { }

    ~TreeInvariants<D>() { }

    void init(Dataset* const d, snapml::task_t task, const uint32_t num_threads, const uint32_t num_classes)
    {
#ifdef TIME_PROFILE
        typedef std::chrono::high_resolution_clock Clock;
        auto                                       t1 = Clock::now();
#endif

        // trees need to have the labels in double
        float* labs_ptr = d->get_labs();
        labs_.resize(d->get_num_ex());
        for (uint32_t i = 0; i < labs_.size(); i++) {
            labs_[i] = labs_ptr[i];
        }

        sorted_ex_.resize(d->get_num_ft());
        OMP::parallel_for<int32_t>(0, sorted_ex_.size(),
                                   [this, &d](const int32_t& ft) { sorted_ex_[ft].resize(d->get_num_ex()); });
#ifdef TIME_PROFILE
        auto   t2     = Clock::now();
        auto   dur    = t2 - t1;
        double t_elap = (double)dur.count() / 1.0e9;
        std::cout << "[init] elapsed time for allocating sorted matrix " << t_elap << std::endl;
#endif
        sort_matrix(d, task, num_threads, num_classes);
    }

    void init_hist(Dataset* const d, snapml::task_t task, const uint32_t hist_nbins, bool by_example = false)
    {

        if (by_example) {
            ex_to_bin_.resize(d->get_num_ex(), std::vector<uint8_t>(d->get_num_ft()));
        } else {
            // ex_to_bin_.resize(d->get_num_ft(), std::vector<uint8_t> (d->get_num_ex()));
            ex_to_bin_.resize(d->get_num_ft());
            OMP::parallel_for<int32_t>(0, ex_to_bin_.size(),
                                       [this, &d](const int32_t& ft) { ex_to_bin_[ft].resize(d->get_num_ex()); });
        }
        hist_val_.resize(d->get_num_ft(), std::vector<float>(hist_nbins));
        hist_initial_weights_.resize(d->get_num_ft(), std::vector<uint32_t>(hist_nbins, 0));

        bool dbg = false;

        OMP::parallel_for<int32_t>(0, sorted_ex_.size(), [this, &dbg, &hist_nbins, &by_example](int32_t ft) {
            // stage 1 -- create deduplicated sorted vector
            struct dd_t {
                uint32_t count;
                float    val;
                uint32_t rank;
            };

            std::vector<dd_t> dd_sorted;
            dd_t              first;
            first.count = 1;
            first.rank  = 0;
            first.val   = sorted_ex_[ft][0].val;
            dd_sorted.push_back(first);
            for (uint32_t i = 1; i < sorted_ex_[ft].size(); i++) {

                float prev_val = dd_sorted[dd_sorted.size() - 1].val;
                float next_val = sorted_ex_[ft][i].val;

                if (tree::are_different(next_val, prev_val)) {
                    dd_t next;
                    next.count = 1;
                    next.rank  = i;
                    next.val   = sorted_ex_[ft][i].val;
                    dd_sorted.push_back(next);
                } else {
                    dd_sorted[dd_sorted.size() - 1].count++;
                }
            }

            if (dbg) {
                for (uint32_t i = 0; i < dd_sorted.size(); i++) {
                    std::cout << i << " " << dd_sorted[i].val << " " << dd_sorted[i].count << std::endl;
                }
            }

            // stage 2 -- build histograms
            uint32_t              hist_nbins_ft = std::min(dd_sorted.size(), (size_t)hist_nbins);
            std::vector<uint32_t> rank_value;

            // if the number of unique values is  <= the number of bins
            // we can assign one bin per value
            if (hist_nbins_ft == dd_sorted.size()) {

                hist_val_[ft].resize(hist_nbins_ft);
                rank_value.resize(hist_nbins_ft + 1);
                for (uint32_t i = 0; i < hist_nbins_ft; i++) {
                    hist_val_[ft][i] = dd_sorted[i].val;
                    rank_value[i]    = dd_sorted[i].rank;
                }
                rank_value[hist_nbins_ft] = sorted_ex_[ft].size();

                // adjust bin values by 0.5
                for (uint32_t n = 1; n < rank_value.size() - 1; n++) {
                    uint32_t ind_last_bin = rank_value[n] - 1;
                    uint32_t ind_this_bin = rank_value[n];
                    float    min_val      = sorted_ex_[ft][ind_last_bin].val;
                    float    max_val      = sorted_ex_[ft][ind_this_bin].val;
                    hist_val_[ft][n]      = (max_val + min_val) / 2.0;
                }

                // otherwise partition the weighted values in a greedy way
                // this problem maps to something like 'line breaking'
                // and may have a better solution than this
            } else {

                // detect very frequent values
                // i.e., values that occur at least 10% of the time
                std::vector<uint32_t> freqvals;
                for (uint32_t i = 0; i < dd_sorted.size(); i++) {
                    double frac = double(dd_sorted[i].count) / double(sorted_ex_[ft].size());
                    if (frac > 0.1) {
                        freqvals.push_back(i);
                    }
                }

                // adjust target bin size to account for
                // frequent values, which should have their own bin
                uint32_t num = sorted_ex_[ft].size();
                uint32_t den = hist_nbins_ft;
                for (const uint32_t i : freqvals) {
                    num -= dd_sorted[i].count;
                    den--;
                }
                uint32_t targ = floor(static_cast<double>(num) / static_cast<double>(den));

                hist_val_[ft].resize(0);
                uint32_t bin_idx = 0;
                uint32_t pos     = 0;

                while (bin_idx < hist_nbins_ft && pos < dd_sorted.size()) {

                    uint32_t bin_pos  = pos;
                    uint32_t bin_len  = 0;
                    uint32_t bin_rank = dd_sorted[pos].rank;
                    float    bin_val  = dd_sorted[pos].val;

                    while (bin_len < targ && pos < dd_sorted.size()) {
                        bin_len += dd_sorted[pos].count;
                        pos++;
                    }
                    if ((double(bin_len) > 1.2 * double(targ)) && (pos > (bin_pos + 1))) {
                        pos--;
                        bin_len -= dd_sorted[pos].count;
                    }
                    hist_val_[ft].push_back(bin_val);
                    rank_value.push_back(bin_rank);
                    bin_idx++;
                }

                rank_value.push_back(sorted_ex_[ft].size());
                hist_nbins_ft = bin_idx;
            }

            // stage 3 -- compute initial weights and ex_to_bin
            hist_initial_weights_[ft].resize(hist_val_[ft].size());
            uint32_t sum = 0;
            for (uint32_t n = 0; n < rank_value.size() - 1; n++) {
                assert(n < hist_val_[ft].size());
                sum += hist_initial_weights_[ft][n] = rank_value[n + 1] - rank_value[n];
                if (!by_example) {
                    for (uint32_t ex = rank_value[n]; ex < rank_value[n + 1]; ex++) {
                        ex_to_bin_[ft][sorted_ex_[ft][ex].idx] = n;
                    }
                } else {
                    for (uint32_t ex = rank_value[n]; ex < rank_value[n + 1]; ex++) {
                        ex_to_bin_[sorted_ex_[ft][ex].idx][ft] = n;
                        if (ex + 4 < rank_value[n + 1])
                            PREFETCH((void*)&ex_to_bin_[sorted_ex_[ft][ex + 4].idx][ft]);
                    }
                }
            }
            assert(sum == sorted_ex_[ft].size());
        });

        if (dbg) {
            fprintf(stdout, "\n");
            uint32_t avg_size = 0;
            for (uint32_t ft = 0; ft < sorted_ex_.size(); ++ft) {
                fprintf(stdout, "ft=%u bin_nr=%lu", ft, static_cast<unsigned long>(hist_val_[ft].size()));
                avg_size += hist_val_[ft].size();
            }
            fprintf(stdout, " avg-bin-size=%lu\n", avg_size / static_cast<unsigned long>(sorted_ex_.size()));
            for (uint32_t ft = 0; ft < sorted_ex_.size(); ++ft) {
                for (uint32_t n = 0; n < hist_val_[ft].size(); n++) {
                    fprintf(stdout, "ft=%u bin=%u hist-val=%.20f weight=%u \n", ft, n, hist_val_[ft][n],
                            hist_initial_weights_[ft][n]);
                }
            }
        }
    }

    void clear_sorted_matrix()
    {
        sorted_ex_.clear();
        sorted_ex_.shrink_to_fit();
    }

    void clear_ex_to_bin()
    {
        ex_to_bin_.clear();
        ex_to_bin_.shrink_to_fit();
    }

    struct ex_info_t {
        float    val;
        uint32_t idx;   //:31;
        uint32_t label; //:1;
        ex_info_t()
            : val(0.0)
        {
            idx   = 0;
            label = 0;
        }
    };

    const double* get_labs() { return labs_.data(); }

    const std::vector<std::vector<ex_info_t>>& get_sorted_matrix() { return sorted_ex_; }

    const std::vector<std::vector<uint8_t>>& get_ex_to_bin() { return ex_to_bin_; }

    const std::vector<std::vector<float>>& get_hist_val() { return hist_val_; }

    const std::vector<std::vector<uint32_t>>& get_hist_initial_weights() { return hist_initial_weights_; }

private:
    void sort_matrix(Dataset* const d, snapml::task_t task = snapml::task_t::classification,
                     const uint32_t n_threads = 32, const uint32_t num_classes = 2)
    {
        const uint32_t     num_ft = d->get_num_ft();
        const uint32_t     num_ex = d->get_num_ex();
        auto               data   = static_cast<D*>(d)->get_data();
        const float* const labs   = static_cast<D*>(d)->get_labs();
#ifdef TIME_PROFILE
        struct timeval t1, t2;
        gettimeofday(&t1, NULL);
#endif
        struct cmp_ex_info_t {
            inline bool operator()(const ex_info_t& l, const ex_info_t& r) { return (l.val < r.val); }
        };

        omp_set_num_threads(n_threads);
        OMP::parallel_for<int32_t>(0, num_ex, [this, &num_ft, &data, &task, &num_classes, &labs](const int32_t& i) {
            for (uint32_t ft = 0; ft < num_ft; ft++) {
                sorted_ex_[ft][i].val = D::lookup2D(data, i, ft);
                sorted_ex_[ft][i].idx = i;

                if (task == snapml::task_t::classification) {
                    if (num_classes == 2)
                        sorted_ex_[ft][i].label = 0 < labs[i] ? 1 : 0;
                    else
                        sorted_ex_[ft][i].label = labs[i];
                }
            }
        });
        OMP::parallel_for<int32_t>(0, num_ft, [this](const int32_t& ft) {
            std::sort(sorted_ex_[ft].begin(), sorted_ex_[ft].end(), cmp_ex_info_t());
        });

#ifdef TIME_PROFILE
        gettimeofday(&t2, NULL);
        double t_elap = double(t2.tv_sec - t1.tv_sec) + double(t2.tv_usec - t1.tv_usec) / 1000.0 / 1000.0;
        std::cout << "[init] elapsed time for sorting all features " << t_elap << std::endl;
#endif
    }

    std::vector<double>                 labs_;                 // exs
    std::vector<std::vector<ex_info_t>> sorted_ex_;            // fts * exs
    std::vector<std::vector<uint8_t>>   ex_to_bin_;            // fts * exs
    std::vector<std::vector<float>>     hist_val_;             // fts * bins
    std::vector<std::vector<uint32_t>>  hist_initial_weights_; // fts * bins
    TreeInvariants(const TreeInvariants&&) = delete;
    TreeInvariants& operator=(const TreeInvariants&) = delete;
};
#if 0
template<>
inline
void TreeInvariants<DenseDataset>::sort_matrix (Dataset *const d,
                                                 snapml::task_t task = snapml::task_t::classification,
                                                 const uint32_t n_threads = 32)
{

}

template<class D>
inline
void TreeInvariants<SparseDataset>::sort_matrix (Dataset *const d,
                                                 snapml::task_t task = snapml::task_t::classification,
                                                 const uint32_t n_threads = 32)

template<>
inline
void TreeInvariants<SparseDataset>::sort_matrix (Dataset *const d,
                                                 snapml::task_t task = snapml::task_t::classification,
                                                 const uint32_t n_threads = 32)
{

}
#endif
} // glm
#endif // _LIBGLM_SORTED_MATRIX_
