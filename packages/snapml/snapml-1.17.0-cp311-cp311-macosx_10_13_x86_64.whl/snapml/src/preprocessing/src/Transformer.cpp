/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2023
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      :
 *
 * End Copyright
 ********************************************************************/

#include <string>
#include <vector>
#include <map>
#include <set>

#include "DenseDataset.hpp"
#include "DataSchema.hpp"
#include "AnyDataset.hpp"
#include "Features.hpp"
#include "Transformer.hpp"

namespace snapml {

bool Transformer::index_list_valid(std::set<uint32_t>& index_list, uint32_t max)
{
    // check for size
    if (index_list.size() > max) {
        return false;
    }
    // check for content < max
    for (uint32_t i : index_list) {
        if (i >= max) {
            return false;
        }
    }
    return true;
}

}