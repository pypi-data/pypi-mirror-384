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
#include <cstdint>
#include <memory>
#include <vector>

namespace glm {
class DenseDataset;
}

namespace snapml {

//! @ingroup c-api
class DenseDataset {
public:
    DenseDataset();
    // needed in the wrapper code since it constructors are not inherited
    DenseDataset(uint32_t num_ex, uint32_t num_ft, float* data, float* labs);
    DenseDataset(std::vector<float>& data, std::vector<float>& labs);
    const std::shared_ptr<glm::DenseDataset>& get() const { return data_; }
    void                                      set(std::shared_ptr<glm::DenseDataset> data) { data_ = data; }

protected:
    std::shared_ptr<glm::DenseDataset> data_;
    std::shared_ptr<std::mutex>        mtx_;
};

}
