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

#include <mutex>
#include <vector>
#include <memory>
#include <stdint.h>

namespace tree {
struct TreeModel;
}

namespace snapml {

//! @ingroup c-api
class DecisionTreeModel {
public:
    DecisionTreeModel();
    void get(std::vector<uint8_t>& vec);
    void put(const std::vector<uint8_t>& vec);

protected:
    std::shared_ptr<tree::TreeModel> model_;
    std::shared_ptr<std::mutex>      mtx_;
};

}
