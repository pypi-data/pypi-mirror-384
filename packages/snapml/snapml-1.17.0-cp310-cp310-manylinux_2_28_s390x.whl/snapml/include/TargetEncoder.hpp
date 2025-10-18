/*********************************************************************
 *
 * Licensed Materials - Property of IBM
 *
 * (C) Copyright IBM Corp. 2022, 2023, 2024. All Rights Reserved.

 * US Government Users Restricted Rights - Use, duplication or
 * disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
 *
 ********************************************************************/

#pragma once
namespace snapml {

//! @ingroup c-api
class TargetEncoder : Transformer {
public:
    struct Params {
        Params()
            : target_mean(0.0)
        {
        }
        float                                     target_mean;
        std::vector<std::map<std::string, float>> categories;
        std::set<uint32_t>                        index_list;
    };
    TargetEncoder(const snapml::TargetEncoder::Params params);
    void transform(snapml::AnyDataset& dataset);

private:
    Params params;
};

}
