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
class AnyDataset {
public:
    AnyDataset();
    ~AnyDataset();
    AnyDataset(const std::vector<char> input_vector, const snapml::DataSchema schema);
    snapml::DenseDataset            convertToDenseDataset();
    uint32_t                        get_num_ex();
    std::vector<std::vector<float>> get_vec_data();
};

}
