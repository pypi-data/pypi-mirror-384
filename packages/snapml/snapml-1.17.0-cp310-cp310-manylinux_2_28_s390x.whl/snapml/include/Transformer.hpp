/*********************************************************************
 *
 * Licensed Materials - Property of IBM
 *
 * (C) Copyright IBM Corp. 2022, 2023. All Rights Reserved.

 * US Government Users Restricted Rights - Use, duplication or
 * disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
 *
 ********************************************************************/

namespace snapml {

//! @ingroup c-api
class Transformer {
public:
    virtual void transform(snapml::AnyDataset& dataset) = 0;
    virtual void fit_transform(snapml::AnyDataset& dataset) {};
    virtual void fit(snapml::AnyDataset& dataset) {};
    virtual ~Transformer() = default;
    bool index_list_valid(std::set<uint32_t>& index_list, uint32_t max);
};

}