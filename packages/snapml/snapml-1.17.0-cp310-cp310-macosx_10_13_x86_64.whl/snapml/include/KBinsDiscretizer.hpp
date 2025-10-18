/*********************************************************************
 *
 * Licensed Materials - Property of IBM
 *
 * (C) Copyright IBM Corp. 2022, 2023. All Rights Reserved.

 * US Government Users Restricted Rights - Use, duplication or
 * disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
 *
 ********************************************************************/

#pragma once
namespace snapml {

//! @ingroup c-api
class KBinsDiscretizer : Transformer {
public:
    struct Params {
        enum Encode { onehot, onehot_dense, ordinal };
        Params()
            : n_bins(5)
            , encode(ordinal)
            , bin_edges({})
            , index_list({})
        {
        }
        uint32_t                        n_bins;
        Encode                          encode;
        std::vector<std::vector<float>> bin_edges;
        std::set<uint32_t>              index_list;
    };
    KBinsDiscretizer(const snapml::KBinsDiscretizer::Params params);
    void transform(snapml::AnyDataset& dataset);

private:
    Params params;
};

}