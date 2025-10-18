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
 *                Kubilay Atasu
 *                Gummadi Ravi
 *
 *
 * End Copyright
 ********************************************************************/

#ifndef GLM_LOADERS
#define GLM_LOADERS

#include "L2SparseDataset.hpp"
#include "SparseDataset.hpp"
#include "DenseDatasetInt.hpp"
#include <fstream>
#include <stdexcept>
#include <string>

namespace glm {

inline std::vector<std::pair<uint32_t, uint32_t>> load_balancing(const uint32_t num_ex, const uint32_t* const count,
                                                                 const uint32_t numPartitions)
{

    // check
    if (numPartitions > num_ex) {
        throw std::runtime_error(
            "Number of partitions cannot be bigger than number of examples (in the dual) or features (in the primal).");
    }

    // first  -> min example
    // second -> max_example
    std::vector<std::pair<uint32_t, uint32_t>> out;

    out.resize(numPartitions);

    uint64_t tot_nz = 0;
    for (uint32_t i = 0; i < num_ex; i++)
        tot_nz += count[i];

    uint64_t cap_size = tot_nz / uint64_t(numPartitions);

    uint64_t tot_nz_allocated = 0;

    uint32_t i = 0;
    uint32_t p = 0;
    for (p = 0; p < (numPartitions - 1); p++) {
        uint32_t remaining_partitions = numPartitions - (p + 1);
        out[p].first                  = i;
        uint64_t cur_size             = 0;
        while ((cur_size < cap_size) && (i < (num_ex - remaining_partitions))) {
            cur_size += count[i];
            tot_nz_allocated += count[i];
            i++;
        }
        if ((double(tot_nz_allocated) > double(p + 1) / double(numPartitions) * double(tot_nz))
            && (i > (out[p].first + 1))) {
            i--;
            cur_size -= count[i];
            tot_nz_allocated -= count[i];
        }
        out[p].second = i;
    }

    out[p].first  = i;
    out[p].second = num_ex;

    return out;
}

template <class D> class Loader {

public:
    // ctor
    Loader<D>(uint32_t partition_id, uint32_t num_partitions)
    {
        consistent_     = false;
        partition_id_   = partition_id;
        num_partitions_ = num_partitions;
        max_ind_        = 0;
        this_num_pt_    = 0;
        num_pos_        = 0;
        num_neg_        = 0;
        this_pt_offset_ = 0;
        transpose_      = false;
    }

    // virtal dtor
    virtual ~Loader<D>() { }

    void get_consistency(uint32_t& max_ind, uint32_t& this_num_pt, uint32_t& num_pos, uint32_t& num_neg,
                         uint32_t* const offsets)
    {
        max_ind                = max_ind_;
        this_num_pt            = this_num_pt_;
        num_pos                = num_pos_;
        num_neg                = num_neg_;
        offsets[partition_id_] = this_num_pt;
    }

    void set_consistency(const uint32_t& max_ind, const uint32_t& this_num_pt, const uint32_t& num_pos,
                         const uint32_t& num_neg, const uint32_t* const offsets)
    {
        if (transpose_) {
            num_ex_  = max_ind + 1;
            num_ft_  = this_num_pt;
            num_pos_ = num_pos / num_partitions_;
            num_neg_ = num_neg / num_partitions_;
        } else {
            num_ex_  = this_num_pt;
            num_ft_  = max_ind + 1;
            num_pos_ = num_pos;
            num_neg_ = num_neg;
        }
        this_pt_offset_ = 0;
        for (uint32_t i = 0; i < partition_id_; i++) {
            this_pt_offset_ += offsets[i];
        }
        consistent_ = true;

        /*
        std::cout << "partition_id = " << partition_id_ << std::endl;
        std::cout << "num_ex       = " << num_ex_ << std::endl;
        std::cout << "num_ft       = " << num_ft_ << std::endl;
        std::cout << "num_pos      = " << num_pos_ << std::endl;
        std::cout << "num_neg      = " << num_neg_ << std::endl;
        std::cout << "this_num_pt  = " << this_num_pt_ << std::endl;
        std::cout << "num_pos_     = " << num_pos_ << std::endl;
        std::cout << "num_neg_     = " << num_neg_ << std::endl;
    */
    }

    // function to get dataset
    virtual std::shared_ptr<D> get_data() = 0;
    uint32_t                   get_num_partitions() { return num_partitions_; }

protected:
    bool consistent_;
    bool transpose_;

    uint32_t partition_id_;
    uint32_t num_partitions_;
    uint32_t num_ex_;
    uint32_t num_ft_;
    uint32_t this_num_pt_;
    uint32_t num_pos_;
    uint32_t num_neg_;
    uint32_t this_pt_offset_;
    uint32_t max_ind_;
};

class CsvLoader : public Loader<DenseDataset> {

public:
    CsvLoader(const CsvLoader&) = delete;

    CsvLoader(std::string filename, uint32_t partition_id, uint32_t num_partitions, uint32_t num_chunks,
              uint32_t label_col_ind = 0)
        : Loader<DenseDataset>(partition_id, num_partitions)
    {
        // number of chunks needs to be a multiple of the number of partitions
        assert(num_chunks % num_partitions == 0);

        // open the file (at the end)
        std::ifstream fin(filename.c_str(), std::ifstream::ate | std::ifstream::binary);

        // check we could open file
        if (!fin.is_open()) {
            throw std::runtime_error("Could not open file");
        }

        // get length of file in bytes
        size_t len = fin.tellg();

        // split into partitions
        size_t chunk_len = len / num_chunks;

        // initialize
        val_.resize(0);
        labs_.resize(0);

        // number of pts in this partition
        this_num_pt_ = 0;

        // number of nz in this partition
        this_num_nz_ = 0;

        // maximum feature index
        max_ind_ = 0;

        // number of positive examples
        num_pos_ = 0;

        // number of negative examples
        num_neg_ = 0;

        for (uint32_t chunk_idx = partition_id; chunk_idx < num_chunks; chunk_idx += num_partitions) {
            // get starting position
            size_t start_pos = chunk_idx * chunk_len;

            // ending position
            size_t end_pos = start_pos + chunk_len;

            // buffer for reading
            std::string line;

            // if we are starting to read from the middle of a line, let's skip it
            if (chunk_idx > 0) {
                fin.seekg(start_pos - 1);
                char chk;
                fin.read(&chk, 1);
                if (chk != '\n') {
                    // std::cout << "skipping line..." << std::endl;
                    std::getline(fin, line);
                    start_pos += line.size() + 1;
                }
            }

            // seek to starting position
            fin.seekg(start_pos);

            // current position
            size_t pos = start_pos;

            // iterate through partition
            while (pos < end_pos && pos < len) {
                // get a line of text
                std::getline(fin, line);

                if (line.size() > 0) {
                    const char* line_c_str = line.c_str();

                    // number of nz in this example
                    uint32_t col = 0;

                    // iterate through tokens
                    while (line_c_str != nullptr) {
                        // skip any whitespace
                        while (static_cast<uint8_t>(line_c_str[0]) == 32 || static_cast<uint8_t>(line_c_str[0]) == 44) {
                            line_c_str++;
                        }

                        // if reach end-of-line stop
                        if (static_cast<uint8_t>(line_c_str[0]) == 0) {
                            break;
                        }

                        float val = atof(line_c_str);

                        if (col == label_col_ind) {
                            labs_.push_back(val);

                            if (val > 0) {
                                num_pos_++;
                            } else {
                                num_neg_++;
                            }
                        } else {
                            // push back feature value
                            val_.push_back(val);
                        }

                        // increment col
                        col++;

                        line_c_str = strchr(line_c_str, ',');
                    }

                    // max ind
                    max_ind_ = col - 2;

                    // increment offset
                    this_num_nz_ += (col - 1);

                    // increment number of pt
                    this_num_pt_++;
                }

                // increment position in file (add one char for newline)
                pos += line.size() + 1;
            }
        }

        fin.close();
    }

    // CsvLoader ctr used when data is loaded by Spark Dataframe and passed onto SnapML APIs.
    CsvLoader(uint32_t num_pt, uint64_t num_nz, uint32_t max_ind, std::vector<float>& val, std::vector<float>& labs,
              uint32_t num_pos, uint32_t num_neg, uint32_t partition_id, uint32_t num_partitions)
        : Loader<DenseDataset>(partition_id, num_partitions)
    {
        // this_num_nz_ = this_num_nz_;
        labs_        = std::move(labs);
        val_         = std::move(val);
        this_num_pt_ = num_pt;
        this_num_nz_ = num_nz;
        max_ind_     = max_ind;
        num_pos_     = num_pos;
        num_neg_     = num_neg;
    }

    virtual ~CsvLoader() { }

    virtual std::shared_ptr<DenseDataset> get_data()
    {

        if (!consistent_) {
            throw std::runtime_error("Must make the loading is consistent before the dataset is returned");
        }

        return std::make_shared<DenseDataset>(transpose_, num_ex_, num_ft_, this_num_pt_, num_partitions_,
                                              partition_id_, this_pt_offset_, this_num_nz_, num_pos_, num_neg_, labs_,
                                              val_, false);
    }

    std::vector<float>& get_val() { return val_; }
    std::vector<float>& get_labs() { return labs_; }
    uint64_t            get_num_nz() { return this_num_nz_; }

private:
    uint64_t this_num_nz_;

    std::vector<float> val_;
    std::vector<float> labs_;
};

class SvmLightLoader : public Loader<SparseDataset> {

public:
    SvmLightLoader(const SvmLightLoader&) = delete;

    SvmLightLoader(std::string filename, uint32_t partition_id, uint32_t num_partitions, uint32_t num_chunks,
                   uint32_t expected_num_ft = 1)
        : Loader<SparseDataset>(partition_id, num_partitions)
    {
        // number of chunks needs to be a multiple of the number of partitions
        assert(num_chunks % num_partitions == 0);

        // open the file (at the end)
        std::ifstream fin(filename.c_str(), std::ifstream::ate | std::ifstream::binary);

        // check we could open file
        if (!fin.is_open()) {
            throw std::runtime_error("Could not open file");
        }

        // get length of file in bytes
        size_t len = fin.tellg();

        // compute rounded-down length of each chunk in bytes
        size_t chunk_len = len / size_t(num_chunks);

        // initialize
        start_.resize(0);
        ind_.resize(0);
        val_.resize(0);
        labs_.resize(0);

        // number of pts in this partition
        this_num_pt_ = 0;

        // number of nz in this partition
        this_num_nz_ = 0;

        // maximum feature index
        max_ind_ = expected_num_ft - 1;

        // number of positive examples
        num_pos_ = 0;

        // number of negative examples
        num_neg_ = 0;

        // buffer for reading
        std::string line;

        for (uint32_t chunk_idx = partition_id; chunk_idx < num_chunks; chunk_idx += num_partitions) {
            // get starting position
            size_t start_pos = chunk_idx * chunk_len;

            // ending position
            size_t end_pos = start_pos + chunk_len;

            // reset string (keeps memory allocated)
            line.clear();

            // if we are starting to read from the middle of a line, let's skip it
            if (chunk_idx > 0) {
                fin.seekg(start_pos - 1);
                char chk;
                fin.read(&chk, 1);
                if (chk != '\n') {
                    // std::cout << "skipping line..." << std::endl;
                    std::getline(fin, line);
                    start_pos += line.size() + 1;
                }
            }

            // seek to starting position
            fin.seekg(start_pos);

            // current position
            size_t pos = start_pos;

            // iterate through chunk
            while (pos < end_pos && pos < len) {
                // get a line of text
                std::getline(fin, line);

                if (line.size() > 0) {
                    const char* line_c_str = line.c_str();

                    /*
                  for(int i = 0; i <= line.size(); i++) {
                  printf("%u ", line_c_str[i]);
                  }
                  printf("\n");
                */

                    float lab;
                    sscanf(line_c_str, "%f", &lab);

                    labs_.push_back(lab);

                    if (lab > 0) {
                        num_pos_++;
                    } else {
                        num_neg_++;
                    }

                    // number of nz in this example
                    uint32_t cur_nz = 0;

                    // find first space after label
                    line_c_str = strchr(line_c_str, ' ');

                    // iterate through tokens
                    while (line_c_str != nullptr) {

                        // skip any whitespace
                        while (static_cast<uint8_t>(line_c_str[0]) == 32) {
                            line_c_str++;
                        }

                        // if reach end-of-line stop
                        if (static_cast<uint8_t>(line_c_str[0]) == 0) {
                            break;
                        }

                        // get feature index (-1 since SVM Light has indexing from 1+)
                        uint32_t ind = atoi(line_c_str) - 1;
                        // keep track of max feature index observed
                        max_ind_ = std::max(max_ind_, ind);
                        // push back feature index
                        ind_.push_back(ind);

                        // move past feature index
                        line_c_str = strchr(line_c_str, ':') + 1;

                        // push back feature value
                        float val = atof(line_c_str);
                        // push back value
                        val_.push_back(val);

                        // increment nz counter
                        cur_nz++;

                        // first first space after val
                        line_c_str = strchr(line_c_str, ' ');
                    }

                    // push back offset
                    start_.push_back(this_num_nz_);

                    // increment offset
                    this_num_nz_ += cur_nz;

                    // increment number of pt
                    this_num_pt_++;
                }

                // increment position in file (add one char for newline)
                pos += line.size() + 1;
            }
        }

        // finalize start
        start_.push_back(this_num_nz_);

        fin.close();

        // gettimeofday(&t2, NULL);
        // double t_load = double(t2.tv_usec-t1.tv_usec)/1000.0/1000.0 + double(t2.tv_sec - t1.tv_sec);
        // std::cout << "t_load = " << t_load << std::endl;
    }

    // SvmLightLoader ctr used when data is loaded by Spark Dataframe and passed onto SnapML APIs.
    SvmLightLoader(uint32_t num_pt, uint64_t num_nz, std::vector<uint64_t>& start, std::vector<uint32_t>& ind,
                   uint32_t max_ind, std::vector<float>& val, std::vector<float>& labs, uint32_t num_pos,
                   uint32_t num_neg, uint32_t partition_id, uint32_t num_partitions)
        : Loader<SparseDataset>(partition_id, num_partitions)
    {
        // this_num_nz_ = this_num_nz_;
        labs_        = std::move(labs);
        start_       = std::move(start);
        ind_         = std::move(ind);
        val_         = std::move(val);
        this_num_pt_ = num_pt;
        this_num_nz_ = num_nz;
        max_ind_     = max_ind;
        num_pos_     = num_pos;
        num_neg_     = num_neg;
    }

    virtual ~SvmLightLoader() { }

    virtual std::shared_ptr<SparseDataset> get_data()
    {

        if (!consistent_) {
            throw std::runtime_error("Must make the loading is consistent before the dataset is returned");
        }

        return std::make_shared<SparseDataset>(transpose_, num_ex_, num_ft_, this_num_pt_, num_partitions_,
                                               partition_id_, this_pt_offset_, this_num_nz_, num_pos_, num_neg_, labs_,
                                               start_, ind_, val_);
    }

    std::vector<float>&    get_val() { return val_; }
    std::vector<float>&    get_labs() { return labs_; }
    std::vector<uint64_t>& get_start() { return start_; }
    std::vector<uint32_t>& get_ind() { return ind_; }
    uint64_t               get_num_nz() { return this_num_nz_; }

private:
    uint64_t this_num_nz_;

    std::vector<uint64_t> start_;
    std::vector<uint32_t> ind_;
    std::vector<float>    val_;
    std::vector<float>    labs_;
};

template <class D> class GenericSnapLoader : public Loader<D> {

public:
    // ctor
    GenericSnapLoader<D>(std::string filename, uint32_t partition_id, uint32_t num_partitions, uint32_t num_chunks,
                         uint32_t take_from, uint32_t take_to, bool sparse, bool implicit_vals)
        : Loader<D>(partition_id, num_partitions)
    {
        // number of chunks needs to be a multiple of the number of partitions
        assert(num_chunks % num_partitions == 0);

        // beg = begin of the data range
        // pos = position within the data range from which to read
        // len = length of the data range (first), length of the read range (later on)
        size_t count_beg = 0UL;
        size_t count_len = 0UL;

        size_t labs_beg = 0UL;
        size_t labs_pos = 0UL;
        size_t labs_len = 0UL;

        size_t ind_beg = 0UL;
        size_t ind_pos = 0UL;
        size_t ind_len = 0UL;

        size_t val_beg = 0UL;
        size_t val_pos = 0UL;
        size_t val_len = 0UL;

        size_t tot_pt = 0UL;

        // open file
        std::ifstream fin(filename.c_str(), std::ios_base::in | std::ios_base::binary);

        // check file is open
        if (!fin.is_open()) {
            throw std::runtime_error("Could not open file");
        }

        // read in data type
        fin.read(reinterpret_cast<char*>(&data_type_), sizeof(uint32_t));

        if (data_type_ > 2) {
            throw std::runtime_error("Unrecognized data format.");
        }

        if (data_type_ == 0 && sparse) {
            throw std::runtime_error("File is in dense snap format; please use glm::DenseSnapLoader.");
        }

        if (data_type_ > 0 && !sparse) {
            throw std::runtime_error(
                "File is in a sparse snap format; please use glm::SparseSnapLoader or glm::L2SparseSnapLoader");
        }

        if (data_type_ == 1 && implicit_vals) {
            throw std::runtime_error(
                "File is in sparse snap format without implicit values; please use glm::SparseSnapLoader.");
        }

        if (data_type_ == 2 && !implicit_vals) {
            throw std::runtime_error(
                "File is in sparse snap format with implicit values; please use glm::L2SparseSnapLoader.");
        }

        // read in transpose byte
        fin.read(reinterpret_cast<char*>(&this->transpose_), sizeof(bool));

        // read number of examples
        fin.read(reinterpret_cast<char*>(&this->num_ex_), sizeof(uint32_t));

        // read number of features
        fin.read(reinterpret_cast<char*>(&this->num_ft_), sizeof(uint32_t));

        // read non-zero counts
        std::vector<uint32_t> count;
        count.resize(this->transpose_ ? this->num_ft_ : this->num_ex_);
        count_beg = 13;

        if (!sparse) {
            if (this->transpose_) {
                for (uint32_t i = 0; i < this->num_ft_; i++) {
                    count[i] = this->num_ex_;
                }
            } else {
                for (uint32_t i = 0; i < this->num_ex_; i++) {
                    count[i] = this->num_ft_;
                }
            }

            tot_pt = this->num_ex_ * this->num_ft_;
        } else {
            // read counts
            count_len = this->transpose_ ? this->num_ft_ * sizeof(uint32_t) : this->num_ex_ * sizeof(uint32_t);
            fin.read(reinterpret_cast<char*>(&count[0]), count_len);

            // count total number of data points.  This determines the size of the indices and values.
            for (uint32_t i = 0; i < count.size(); i++) {
                tot_pt += count[i];
            }
        }

        labs_beg = count_beg + count_len;
        labs_len = this->num_ex_ * sizeof(float);
        ind_beg  = labs_beg + labs_len;
        ind_len  = sparse ? tot_pt * sizeof(uint32_t) : 0;
        val_beg  = ind_beg + ind_len;
        val_len  = implicit_vals ? 0 : tot_pt * sizeof(float);

        // check arguments
        if (this->transpose_ && (take_from != 0 || take_to != 0)) {
            throw std::runtime_error("take_to/take_from only supported for non-transposed data");
        }

        std::vector<std::pair<uint32_t, uint32_t>> idx;
        if (!this->transpose_) {
            // take_to is only used as upper range if it is strictly greater than take_from
            if (take_to > take_from) {
                idx = load_balancing(take_to - take_from, &count[take_from], num_chunks);
            } else {
                idx = load_balancing(this->num_ex_ - take_from, &count[take_from], num_chunks);
            }
        } else {
            idx = load_balancing(this->transpose_ ? this->num_ft_ : this->num_ex_, &count[0], num_chunks);
        }

        uint64_t skip_num_nz = 0;
        uint32_t skip_num_pt = 0;
        for (uint32_t i = 0; i < take_from; i++) {
            skip_num_nz += uint64_t(count[i]);
            skip_num_pt++;
        }

        start_.resize(1);

        uint32_t pt_pos = 0;
        uint64_t nz_pos = 0;

        this->this_num_pt_ = 0;
        this->this_num_nz_ = 0;

        this->num_pos_ = 0;
        this->num_neg_ = 0;

        uint32_t this_num_lab = 0U;

        if (this->transpose_) {
            this_num_lab = this->num_ex_;
            labs_.resize(this_num_lab);

            labs_pos = labs_beg;
            labs_len = this_num_lab * sizeof(float);

            fin.seekg(labs_pos, std::ios_base::beg);
            fin.read(reinterpret_cast<char*>(&labs_[0]), labs_len);

            for (uint32_t i = 0; i < this_num_lab; i++) {
                if (labs_[i] > 0) {
                    this->num_pos_++;
                } else {
                    this->num_neg_++;
                }
            }
        }

        for (uint32_t chunk_idx = this->partition_id_; chunk_idx < num_chunks; chunk_idx += this->num_partitions_) {
            skip_num_nz = 0;
            skip_num_pt = 0;

            for (uint32_t p = 0; p < chunk_idx; p++) {
                for (uint32_t i = take_from + idx[p].first; i < take_from + idx[p].second; i++) {
                    skip_num_nz += uint64_t(count[i]);
                    skip_num_pt++;
                }
            }

            uint32_t chunk_num_pt_ = 0;
            uint64_t chunk_num_nz_ = 0;
            for (uint32_t i = idx[chunk_idx].first; i < idx[chunk_idx].second; i++) {
                chunk_num_nz_ += uint64_t(count[take_from + i]);
                chunk_num_pt_++;
            }

            // Read labels.  If transposed, each MPI rank needs to read
            // all labels.  Otherwise, only the part of the labels that
            // correspond to the training samples in its partition.

            if (!this->transpose_) {
                // this->this_num_pt_ is number of training samples in this partition
                size_t labs_off = labs_.size();
                this_num_lab    = chunk_num_pt_;
                labs_.resize(labs_.size() + this_num_lab);

                labs_pos = labs_beg + skip_num_pt * sizeof(float);
                labs_len = this_num_lab * sizeof(float);

                fin.seekg(labs_pos, std::ios_base::beg);
                assert(labs_.size() == labs_off + labs_len / sizeof(float));
                fin.read(reinterpret_cast<char*>(&labs_[labs_off]), labs_len);

                for (uint32_t i = labs_off; i < labs_off + this_num_lab; i++) {
                    if (labs_[i] > 0) {
                        this->num_pos_++;
                    } else {
                        this->num_neg_++;
                    }
                }
            }

            ind_pos = ind_beg + skip_num_nz * sizeof(uint32_t);
            ind_len = chunk_num_nz_ * sizeof(uint32_t);
            val_pos = val_beg + skip_num_nz * sizeof(float);
            val_len = chunk_num_nz_ * sizeof(float);

            start_.resize(start_.size() + chunk_num_pt_);

            if (sparse) {
                // Read indices of the sparse vectors
                size_t ind_off = ind_.size();
                ind_.resize(ind_.size() + chunk_num_nz_);

                fin.seekg(ind_pos, std::ios_base::beg);
                assert(ind_.size() == ind_off + ind_len / sizeof(uint32_t));
                fin.read(reinterpret_cast<char*>(&ind_[ind_off]), ind_len);
            }

            if ((sparse && !implicit_vals) || !sparse) {
                // Read values of the (sparse) vectors
                size_t val_off = val_.size();
                val_.resize(val_.size() + chunk_num_nz_);

                fin.seekg(val_pos, std::ios_base::beg);
                assert(val_.size() == val_off + val_len / sizeof(float));
                fin.read(reinterpret_cast<char*>(&val_[val_off]), val_len);
            }

            for (uint32_t i = idx[chunk_idx].first; i < idx[chunk_idx].second; i++) {
                start_[pt_pos] = nz_pos;
                nz_pos += count[take_from + i];
                pt_pos++;
            }
            start_[pt_pos] = nz_pos;

            this->this_num_nz_ += chunk_num_nz_;
            this->this_num_pt_ += chunk_num_pt_;

            assert(nz_pos == this_num_nz_);
            assert(pt_pos == this->this_num_pt_);

            if (this->transpose_) {
                this->max_ind_ = this->num_ex_ - 1;
            } else {
                this->max_ind_ = this->num_ft_ - 1;
            }
        }
        fin.close();
    }

    virtual ~GenericSnapLoader<D>() { }

    virtual std::shared_ptr<D> get_data() = 0;

protected:
    uint32_t data_type_;
    uint64_t this_num_nz_;

    std::vector<uint64_t> start_;
    std::vector<float>    labs_;
    std::vector<uint32_t> ind_;
    std::vector<float>    val_;
};

class DenseSnapLoader : public GenericSnapLoader<DenseDataset> {

public:
    // delete copy ctor
    DenseSnapLoader(const DenseSnapLoader&) = delete;

    // call generic constructor
    DenseSnapLoader(std::string filename, uint32_t partition_id, uint32_t num_partitions, uint32_t num_chunks,
                    uint32_t expected_num_ft = 1, uint32_t take_from = 0, uint32_t take_to = 0)
        : GenericSnapLoader<DenseDataset>(filename, partition_id, num_partitions, num_chunks, take_from, take_to, false,
                                          false)
    {
    }

    // virtual dtor
    virtual ~DenseSnapLoader() { }

    virtual std::shared_ptr<DenseDataset> get_data()
    {

        if (!consistent_) {
            throw std::runtime_error("Must make the loading is consistent before the dataset is returned");
        }

        return std::make_shared<DenseDataset>(transpose_, num_ex_, num_ft_, this_num_pt_, num_partitions_,
                                              partition_id_, this_pt_offset_, this_num_nz_, num_pos_, num_neg_, labs_,
                                              val_, false);
    }
};

class SparseSnapLoader : public GenericSnapLoader<SparseDataset> {

public:
    // delete copy ctor
    SparseSnapLoader(const SparseSnapLoader&) = delete;

    // call generic constructor
    SparseSnapLoader(std::string filename, uint32_t partition_id, uint32_t num_partitions, uint32_t num_chunks,
                     uint32_t expected_num_ft = 1, uint32_t take_from = 0, uint32_t take_to = 0)
        : GenericSnapLoader<SparseDataset>(filename, partition_id, num_partitions, num_chunks, take_from, take_to, true,
                                           false)
    {
    }

    // virtual dtor
    virtual ~SparseSnapLoader() { }

    virtual std::shared_ptr<SparseDataset> get_data()
    {

        if (!consistent_) {
            throw std::runtime_error("Must make the loading is consistent before the dataset is returned");
        }

        return std::make_shared<SparseDataset>(transpose_, num_ex_, num_ft_, this_num_pt_, num_partitions_,
                                               partition_id_, this_pt_offset_, this_num_nz_, num_pos_, num_neg_, labs_,
                                               start_, ind_, val_);
    }
};

class L2SparseSnapLoader : public GenericSnapLoader<L2SparseDataset> {

public:
    // delete copy ctor
    L2SparseSnapLoader(const L2SparseSnapLoader&) = delete;

    // call generic constructor
    L2SparseSnapLoader(std::string filename, uint32_t partition_id, uint32_t num_partitions, uint32_t num_chunks,
                       uint32_t expected_num_ft = 1, uint32_t take_from = 0, uint32_t take_to = 0)
        : GenericSnapLoader<L2SparseDataset>(filename, partition_id, num_partitions, num_chunks, take_from, take_to,
                                             true, true)
    {
    }

    // virtual dtor
    virtual ~L2SparseSnapLoader() { }

    virtual std::shared_ptr<L2SparseDataset> get_data()
    {

        if (!consistent_) {
            throw std::runtime_error("Must make the loading is consistent before the dataset is returned");
        }

        return std::make_shared<L2SparseDataset>(transpose_, num_ex_, num_ft_, this_num_pt_, num_partitions_,
                                                 partition_id_, this_pt_offset_, this_num_nz_, num_pos_, num_neg_,
                                                 labs_, start_, ind_);
    }
};

}

#endif
