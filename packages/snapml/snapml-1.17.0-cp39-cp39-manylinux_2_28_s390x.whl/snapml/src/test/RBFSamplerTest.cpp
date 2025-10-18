/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2020
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Thomas Parnell
 *                Celestine Duenner
 *                Dimitrios Sarigiannis
 *
 * End Copyright
 ********************************************************************/

#include "DatasetGenerators.hpp"
#include "RBFSampler.hpp"
#include "DenseDatasetInt.hpp"

int main()
{

    using namespace std;
    using namespace glm;

    uint32_t num_ex = 1000;
    uint32_t num_ft = 100;

    // bool transpose = is_primal<O>::value ? true : false;
    bool   transpose = false;
    double sparsity  = 1.0;

    uint32_t                 seed = 12312321;
    shared_ptr<DenseDataset> data
        = tests::generate_small_random_dense_dataset(seed, transpose, num_ex, num_ft, sparsity, true);

    RBFSamplerParams rbf_params;
    rbf_params.gamma        = 0.2;
    rbf_params.n_components = 20;
    rbf_params.n_threads    = 1;

    RBFSampler* rbf_obj = new RBFSampler(rbf_params);
    rbf_obj->fit(num_ft);

    // transform API (used during training)
    auto new_data = rbf_obj->transform(data.get());
    assert(new_data.size() == num_ex * rbf_params.n_components);

    // transform API (used during inference)
    auto new_data_ = rbf_obj->transform(data.get(), 8);
    assert(new_data_.size() == num_ex * rbf_params.n_components);

    std::cout << "RBFSampler test finalized" << std::endl;

    return 0;
}
