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
class Normalizer : Transformer {
public:
    struct Params {
        enum Norm { l1, l2, max };
        Params()
            : norm(l2)
            , index_list({})
        {
        }
        Norm               norm       = l2;
        std::set<uint32_t> index_list = {};
    };
    Normalizer(const snapml::Normalizer::Params params);
    void transform(snapml::AnyDataset& dataset);

private:
    Params params;
};

}