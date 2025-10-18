/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2018
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

#ifndef GLM_DATASET_GENERATORS
#define GLM_DATASET_GENERATORS

#include <vector>
#include <cstdlib>
#include <iostream>
#include <cassert>
#include <stdexcept>
#include <random>

#include "DenseDataset.hpp"
#include "DenseDatasetInt.hpp"
#include "L2SparseDataset.hpp"
#include "SparseDataset.hpp"

namespace glm {
namespace tests {

    std::shared_ptr<DenseDataset> generate_small_random_dense_dataset(uint32_t seed, bool transpose, uint32_t num_ex,
                                                                      uint32_t num_ft, double sparsity,
                                                                      uint32_t num_classes = 2, bool normalize = false)
    {

        // seed rng
        srand(seed);

        std::vector<float> labs(num_ex);

        uint32_t num_pos = 0;
        uint32_t num_neg = 0;

        // generate random labels
        if (num_classes == 2) {

            for (uint32_t i = 0; i < num_ex; i++) {
                double p = rand() / double(RAND_MAX);
                if (p < 0.5) {
                    labs[i] = +1.0;
                    num_pos++;
                } else {
                    labs[i] = -1.0;
                    num_neg++;
                }
            }
        } else {
            bool     not_all_classes = true;
            uint32_t trials          = 0;

            std::vector<uint32_t> num(num_classes, 0);

            // make sure that we have all num_classes classes in the labels
            while ((not_all_classes) && (trials < 10)) {
                trials++;
                not_all_classes = false;

                for (uint32_t i = 0; i < num_ex; i++) {
                    labs[i] = rand() % num_classes;
                    num[(uint32_t)labs[i]] += 1;
                }
                for (uint32_t i = 0; i < num_classes; i++) {
                    if (num[i] == 0)
                        not_all_classes = true;
                }
            }

            if (not_all_classes == false) {
                num_neg = num[0];
                num_pos = num_ex - num[0];
            } else {
                printf("Could not generate multiclass classification dataset. Increase number of examples. \n");
                exit(1);
            }
        }

        // generate random matrix
        std::vector<float> X(num_ex * num_ft);

        for (uint32_t ex = 0; ex < num_ex; ex++) {
            for (uint32_t ft = 0; ft < num_ft; ft++) {
                double p = rand() / double(RAND_MAX);
                if (p < sparsity) {
                    if (transpose) {
                        X[ft * num_ex + ex] = normalize ? 1.0 : (rand() / double(RAND_MAX));
                    } else {
                        X[ex * num_ft + ft] = normalize ? 1.0 : (rand() / double(RAND_MAX));
                    }
                }
            }
        }

        uint32_t this_num_pt = transpose ? num_ft : num_ex;
        uint32_t pt_len      = transpose ? num_ex : num_ft;

        if (normalize) {
            for (uint32_t pt = 0; pt < this_num_pt; pt++) {
                uint32_t Z = 0;
                for (uint32_t i = 0; i < pt_len; i++) {
                    Z += (X[pt * pt_len + i] > 0);
                }
                if (Z > 0) {
                    for (uint32_t i = 0; i < pt_len; i++) {
                        X[pt * pt_len + i] /= sqrt(double(Z));
                    }
                }
            }
        }

        uint64_t num_nz         = num_ex * num_ft;
        uint32_t num_partitions = 1;
        uint32_t partition_id   = 0;
        uint32_t this_pt_offset = 0;

        return std::make_shared<DenseDataset>(transpose, num_ex, num_ft, this_num_pt, num_partitions, partition_id,
                                              this_pt_offset, num_nz, num_pos, num_neg, labs, X, false);
    }

    snapml::DenseDataset generate_small_random_dense_dataset_api(uint32_t seed, bool transpose, uint32_t num_ex,
                                                                 uint32_t num_ft, double sparsity,
                                                                 uint32_t num_classes = 2, bool normalize = false)

    {
        std::shared_ptr<DenseDataset> data_p
            = generate_small_random_dense_dataset(seed, transpose, num_ex, num_ft, sparsity, num_classes, normalize);
        snapml::DenseDataset data;
        data.set(data_p);
        return data;
    }

    std::shared_ptr<DenseDataset> generate_small_random_dense_dataset_regression(uint32_t seed, bool transpose,
                                                                                 uint32_t num_ex, uint32_t num_ft,
                                                                                 double sparsity,
                                                                                 bool   normalize = false)
    {

        // seed rng
        srand(seed);

        std::vector<float> labs(num_ex);

        // generate random labels
        uint32_t num_pos = 0;
        uint32_t num_neg = 0;

        for (uint32_t i = 0; i < num_ex; i++) {
            double p = rand() / double(RAND_MAX);
            labs[i]  = p;
            num_pos++;
        }

        // generate random matrix
        std::vector<float> X(num_ex * num_ft);

        for (uint32_t ex = 0; ex < num_ex; ex++) {
            for (uint32_t ft = 0; ft < num_ft; ft++) {
                double p = rand() / double(RAND_MAX);
                if (p < sparsity) {
                    if (transpose) {
                        X[ft * num_ex + ex] = normalize ? 1.0 : (rand() / double(RAND_MAX));
                    } else {
                        X[ex * num_ft + ft] = normalize ? 1.0 : (rand() / double(RAND_MAX));
                    }
                }
            }
        }

        uint32_t this_num_pt = transpose ? num_ft : num_ex;
        uint32_t pt_len      = transpose ? num_ex : num_ft;

        if (normalize) {
            for (uint32_t pt = 0; pt < this_num_pt; pt++) {
                uint32_t Z = 0;
                for (uint32_t i = 0; i < pt_len; i++) {
                    Z += (X[pt * pt_len + i] > 0);
                }
                if (Z > 0) {
                    for (uint32_t i = 0; i < pt_len; i++) {
                        X[pt * pt_len + i] /= sqrt(double(Z));
                    }
                }
            }
        }

        uint64_t num_nz         = num_ex * num_ft;
        uint32_t num_partitions = 1;
        uint32_t partition_id   = 0;
        uint32_t this_pt_offset = 0;

        return std::make_shared<DenseDataset>(transpose, num_ex, num_ft, this_num_pt, num_partitions, partition_id,
                                              this_pt_offset, num_nz, num_pos, num_neg, labs, X, false);
    }

    snapml::DenseDataset generate_small_random_dense_dataset_regression_api(uint32_t seed, bool transpose,
                                                                            uint32_t num_ex, uint32_t num_ft,
                                                                            double sparsity, bool normalize = false)
    {
        std::shared_ptr<DenseDataset> data_p
            = generate_small_random_dense_dataset_regression(seed, transpose, num_ex, num_ft, sparsity, normalize);
        snapml::DenseDataset data;
        data.set(data_p);
        return data;
    }

    std::shared_ptr<SparseDataset> generate_small_random_dataset(uint32_t seed, bool transpose, uint32_t num_ex,
                                                                 uint32_t num_ft, double sparsity,
                                                                 bool normalize = false)
    {

        // seed rng
        srand(seed);

        std::vector<float> labs(num_ex);

        // generate random labels
        uint32_t num_pos = 0;
        uint32_t num_neg = 0;
        for (uint32_t i = 0; i < num_ex; i++) {
            double p = rand() / double(RAND_MAX);
            if (p < 0.5) {
                labs[i] = +1.0;
                num_pos++;
            } else {
                labs[i] = -1.0;
                num_neg++;
            }
        }

        // generate random matrix
        std::vector<std::vector<float>> X;
        X.resize(num_ex);
        for (uint32_t ex = 0; ex < num_ex; ex++) {
            X[ex].resize(num_ft);
            for (uint32_t ft = 0; ft < num_ft; ft++) {
                double p = rand() / double(RAND_MAX);
                if (p < sparsity) {
                    X[ex][ft] = normalize ? 1.0 : (rand() / double(RAND_MAX));
                }
            }
        }

        if (normalize) {
            if (transpose) {
                for (uint32_t ft = 0; ft < num_ft; ft++) {
                    uint32_t Z = 0;
                    for (uint32_t ex = 0; ex < num_ex; ex++) {
                        Z += (X[ex][ft] > 0);
                    }
                    for (uint32_t ex = 0; ex < num_ex; ex++) {
                        X[ex][ft] /= sqrt(double(Z));
                    }
                }
            } else {
                for (uint32_t ex = 0; ex < num_ex; ex++) {
                    uint32_t Z = 0;
                    for (uint32_t ft = 0; ft < num_ft; ft++) {
                        Z += (X[ex][ft] > 0);
                    }
                    for (uint32_t ft = 0; ft < num_ft; ft++) {
                        X[ex][ft] /= sqrt(double(Z));
                    }
                }
            }
        }

        std::vector<uint64_t> start;
        std::vector<uint32_t> ind;
        std::vector<float>    val;

        uint64_t num_nz = 0;

        if (transpose) {

            start.resize(num_ft + 1);
            for (uint32_t ft = 0; ft < num_ft; ft++) {
                start[ft] = num_nz;
                for (uint32_t ex = 0; ex < num_ex; ex++) {
                    if (X[ex][ft] > 0) {
                        ind.push_back(ex);
                        val.push_back(X[ex][ft]);
                        num_nz++;
                    }
                }
            }
            start[num_ft] = num_nz;
        } else {
            start.resize(num_ex + 1);
            for (uint32_t ex = 0; ex < num_ex; ex++) {
                start[ex] = num_nz;
                for (uint32_t ft = 0; ft < num_ft; ft++) {
                    if (X[ex][ft] > 0) {
                        ind.push_back(ft);
                        val.push_back(X[ex][ft]);
                        num_nz++;
                    }
                }
            }
            start[num_ex] = num_nz;
        }

        uint32_t this_num_pt    = transpose ? num_ft : num_ex;
        uint32_t num_partitions = 1;
        uint32_t partition_id   = 0;
        uint32_t this_pt_offset = 0;

        return std::make_shared<SparseDataset>(transpose, num_ex, num_ft, this_num_pt, num_partitions, partition_id,
                                               this_pt_offset, num_nz, num_pos, num_neg, labs, start, ind, val);
    }

    std::shared_ptr<L2SparseDataset> generate_small_random_l2_dataset(uint32_t seed, bool transpose, uint32_t num_ex,
                                                                      uint32_t num_ft, double sparsity)
    {

        // seed rng
        srand(seed);

        std::vector<float> labs(num_ex);

        // generate random labels
        uint32_t num_pos = 0;
        uint32_t num_neg = 0;
        for (uint32_t i = 0; i < num_ex; i++) {
            double p = rand() / double(RAND_MAX);
            if (p < 0.5) {
                labs[i] = +1.0;
                num_pos++;
            } else {
                labs[i] = -1.0;
                num_neg++;
            }
        }

        // generate random matrix
        std::vector<std::vector<float>> X;
        X.resize(num_ex);
        for (uint32_t ex = 0; ex < num_ex; ex++) {
            X[ex].resize(num_ft);
            for (uint32_t ft = 0; ft < num_ft; ft++) {
                double p = rand() / double(RAND_MAX);
                if (p < sparsity) {
                    X[ex][ft] = 1.0;
                }
            }
        }

        std::vector<uint64_t> start;
        std::vector<uint32_t> ind;

        uint64_t num_nz = 0;

        if (transpose) {

            start.resize(num_ft + 1);
            for (uint32_t ft = 0; ft < num_ft; ft++) {
                start[ft] = num_nz;
                for (uint32_t ex = 0; ex < num_ex; ex++) {
                    if (X[ex][ft] > 0) {
                        ind.push_back(ex);
                        num_nz++;
                    }
                }
            }
            start[num_ft] = num_nz;
        } else {
            start.resize(num_ex + 1);
            for (uint32_t ex = 0; ex < num_ex; ex++) {
                start[ex] = num_nz;
                for (uint32_t ft = 0; ft < num_ft; ft++) {
                    if (X[ex][ft] > 0) {
                        ind.push_back(ft);
                        num_nz++;
                    }
                }
            }
            start[num_ex] = num_nz;
        }

        uint32_t this_num_pt    = transpose ? num_ft : num_ex;
        uint32_t num_partitions = 1;
        uint32_t partition_id   = 0;
        uint32_t this_pt_offset = 0;

        return std::make_shared<L2SparseDataset>(transpose, num_ex, num_ft, this_num_pt, num_partitions, partition_id,
                                                 this_pt_offset, num_nz, num_pos, num_neg, labs, start, ind);
    }

}
}

#endif
