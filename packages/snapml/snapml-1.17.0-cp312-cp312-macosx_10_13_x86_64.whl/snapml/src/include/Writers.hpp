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
 *
 *
 * End Copyright
 ********************************************************************/

#ifndef GLM_WRITERS
#define GLM_WRITERS

#include "L2SparseDataset.hpp"
#include "SparseDataset.hpp"
#include "DenseDatasetInt.hpp"
#include <stdexcept>

#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

namespace glm {

namespace writers {

    void __write_to_snap(const char* filename, Dataset* data, uint32_t data_type, uint64_t this_nz_offset,
                         uint64_t tot_num_nz, uint32_t* count, uint32_t* ind, float* val)
    {

        int fd = open(filename, O_WRONLY | O_CREAT, 00600);

        // check file is open
        if (fd == -1) {
            throw std::runtime_error("Could not open file");
        }

        uint32_t partition_id   = data->get_partition_id();
        bool     transpose      = data->get_transpose();
        uint32_t num_ex         = data->get_num_ex();
        uint32_t num_ft         = data->get_num_ft();
        uint32_t this_num_pt    = data->get_this_num_pt();
        uint32_t this_pt_offset = data->get_this_pt_offset();
        uint32_t num_pt         = transpose ? num_ft : num_ex;
        float*   labs           = data->get_labs();
        uint64_t this_num_nz    = data->get_num_nz();

        uint64_t pos = 0;

        if (partition_id == 0) {

            pos += pwrite(fd, &data_type, sizeof(uint32_t), pos);
            pos += pwrite(fd, &transpose, sizeof(bool), pos);
            pos += pwrite(fd, &num_ex, sizeof(uint32_t), pos);
            pos += pwrite(fd, &num_ft, sizeof(uint32_t), pos);

        } else {
            pos += 3 * sizeof(uint32_t) + sizeof(bool);
        }

        // write out counts
        if (data_type == 1 || data_type == 2) {
            pos += this_pt_offset * sizeof(uint32_t);
            pos += pwrite(fd, count, this_num_pt * sizeof(uint32_t), pos);
            pos += (num_pt - this_num_pt - this_pt_offset) * sizeof(uint32_t);
        }

        if (transpose) {
            if (partition_id == 0) {
                pos += pwrite(fd, labs, num_ex * sizeof(float), pos);
            } else {
                pos += num_ex * sizeof(float);
            }
        } else {
            pos += this_pt_offset * sizeof(float);
            pos += pwrite(fd, labs, this_num_pt * sizeof(float), pos);
            pos += (num_pt - this_num_pt - this_pt_offset) * sizeof(float);
        }

        if (data_type == 1 || data_type == 2) {
            pos += this_nz_offset * sizeof(uint32_t);
            pos += pwrite(fd, ind, this_num_nz * sizeof(uint32_t), pos);
            pos += (tot_num_nz - this_num_nz - this_nz_offset) * sizeof(uint32_t);
        }

        if (data_type == 0 || data_type == 1) {
            pos += this_nz_offset * sizeof(float);
            pos += pwrite(fd, val, this_num_nz * sizeof(float), pos);
            pos += (tot_num_nz - this_num_nz - this_nz_offset) * sizeof(float);
        }

        close(fd);
    }

    void write_to_snap(const char* filename, DenseDataset* data, uint64_t this_nz_offset, uint64_t tot_num_nz)
    {

        auto                  arr = data->get_data();
        std::vector<uint32_t> count(data->get_this_num_pt());
        for (uint32_t i = 0; i < count.size(); i++) {
            count[i] = data->get_transpose() ? data->get_num_ex() : data->get_num_ft();
        }

        __write_to_snap(filename, data, 0, this_nz_offset, tot_num_nz, count.data(), nullptr, arr.val);
    }

    void write_to_snap(const char* filename, SparseDataset* data, uint64_t this_nz_offset, uint64_t tot_num_nz,
                       bool with_implicit_vals)
    {
        auto arr = data->get_data();

        std::vector<uint32_t> count(data->get_this_num_pt());
        for (uint32_t i = 0; i < count.size(); i++) {
            count[i] = arr.start[1 + i] - arr.start[i];
        }

        uint32_t data_type = with_implicit_vals ? 2 : 1;

        __write_to_snap(filename, data, data_type, this_nz_offset, tot_num_nz, count.data(), arr.ind, arr.val);
    }

    void write_to_snap(const char* filename, L2SparseDataset* data, uint64_t this_nz_offset, uint64_t tot_num_nz)
    {
        auto arr = data->get_data();

        std::vector<uint32_t> count(data->get_this_num_pt());
        for (uint32_t i = 0; i < count.size(); i++) {
            count[i] = arr.start[1 + i] - arr.start[i];
        }

        __write_to_snap(filename, data, 2, this_nz_offset, tot_num_nz, count.data(), arr.ind, nullptr);
    }

}
}

#endif
