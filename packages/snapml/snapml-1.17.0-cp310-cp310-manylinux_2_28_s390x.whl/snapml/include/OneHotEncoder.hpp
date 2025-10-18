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
class OneHotEncoder : Transformer {
public:
    struct Params {
        Params()
            : handle_unkown(ignore)
            , sparse_output(false)
        {
        }
        enum HandleUnknown { error, ignore, infrequent_if_exist };
        HandleUnknown                           handle_unkown;
        bool                                    sparse_output;
        std::vector<std::map<std::string, int>> categories;
        std::set<uint32_t>                      index_list;
    };
    OneHotEncoder(const snapml::OneHotEncoder::Params params);
    void transform(snapml::AnyDataset& dataset);

private:
    Params params;
};

}
