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
class OrdinalEncoder : Transformer {
public:
    struct Params {
        Params()
            : handle_unkown(use_encoded_value)
            , unknown_value(-1)
        {
        }
        enum HandleUnknown { error, use_encoded_value };
        HandleUnknown                           handle_unkown;
        int32_t                                 unknown_value;
        std::vector<std::map<std::string, int>> categories;
        std::set<uint32_t>                      index_list;
    };
    OrdinalEncoder(const snapml::OrdinalEncoder::Params params);
    void transform(snapml::AnyDataset& dataset);

private:
    Params params;
};

}
