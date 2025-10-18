/*********************************************************************
 *
 * Licensed Materials - Property of IBM
 *
 * (C) Copyright IBM Corp. 2022, 2023. All Rights Reserved.
 * US Government Users Restricted Rights - Use, duplication or
 * disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
 *
 ********************************************************************/
#include "GraphFeatures.h"
#pragma once

namespace snapml {

//! @ingroup c-api
class GfpEncoder : Transformer {
public:
    struct Params {
        Params()
            : num_threads(0)
            , time_window(0)
            , max_no_edges(-1)
            , vertex_stats(false)
            , vertex_stats_tw(0)
            , fan(false)
            , fan_tw(0)
            , degree(false)
            , degree_tw(0)
            , scatter_gather(false)
            , scatter_gather_tw(0)
            , temp_cycle(false)
            , temp_cycle_tw(0)
            , lc_cycle(false)
            , lc_cycle_tw(0)
            , lc_cycle_len(0)
        {
        }

        int                                     num_threads;
        int                                     time_window;
        int                                     max_no_edges;
        bool                                    vertex_stats;
        int                                     vertex_stats_tw;
        std::vector<int>                        vertex_stats_cols;
        std::vector<int>                        vertex_stats_feats;
        bool                                    fan;
        int                                     fan_tw;
        std::vector<int>                        fan_bins;
        bool                                    degree;
        int                                     degree_tw;
        std::vector<int>                        degree_bins;
        bool                                    scatter_gather;
        int                                     scatter_gather_tw;
        std::vector<int>                        scatter_gather_bins;
        bool                                    temp_cycle;
        int                                     temp_cycle_tw;
        std::vector<int>                        temp_cycle_bins;
        bool                                    lc_cycle;
        int                                     lc_cycle_tw;
        int                                     lc_cycle_len;
        std::vector<int>                        lc_cycle_bins;
        std::vector<std::map<std::string, int>> categories;
        std::set<uint32_t>                      index_list;
        // Variables to store parameters
        std::unordered_map<std::string, int>              intParams;
        std::unordered_map<std::string, std::vector<int>> vecParams;
    };

    GfpEncoder(const snapml::GfpEncoder::Params& params);
    ~GfpEncoder();
    void transform(snapml::AnyDataset& dataset);
    void fit_transform(snapml::AnyDataset& dataset);
    void fit(snapml::AnyDataset& dataset);
    void initialize(snapml::AnyDataset& dataset);

private:
    uint64_t                                                 num_rows;
    uint64_t                                                 num_cols_in;
    uint64_t                                                 num_cols_out;
    std::unique_ptr<double[]>                                features_in;
    std::unique_ptr<double[]>                                features_out;
    Params                                                   params;
    std::unique_ptr<GraphFeatures::GraphFeaturePreprocessor> gp;
    std::vector<std::vector<double>>&                        X_G;
};

} // namespace snapml
