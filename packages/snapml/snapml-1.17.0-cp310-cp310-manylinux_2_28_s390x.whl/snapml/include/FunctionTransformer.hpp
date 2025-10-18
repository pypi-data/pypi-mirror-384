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
class FunctionTransformer : Transformer {
public:
    struct Params {
        // like sklearn.preprocessing.FunctionTransformer: If func is None, then func will be the identity function.
        Params()
            : func([](float x) { return x; })
            , index_list({})
        {
        }
        std::function<float(float&)> func = [](float x) { return x; };
        std::set<uint32_t>           index_list;
    };
    FunctionTransformer(const snapml::FunctionTransformer::Params params);
    void transform(snapml::AnyDataset& dataset);

private:
    Params params;
};
}