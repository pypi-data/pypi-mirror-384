/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2021
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
 * End Copyright
 ********************************************************************/

#ifndef MODEL
#define MODEL

#include "Utils.hpp"
#include "Dataset.hpp"

namespace tree {

class Model {

public:
    // virtual dtor
    virtual ~Model() { }

    class Getter {
    public:
        Getter(std::vector<uint8_t>& _vec)
            : vec(_vec)
        {
            vec.clear();
        }
        template <typename T> void add(const T& val)
        {
            const uint8_t* const arr = reinterpret_cast<const uint8_t*>(&val);
            vec.insert(vec.end(), arr, arr + sizeof(T));
        }
        template <typename T> void add(const T& val, const uint64_t size)
        {
            const uint8_t* const arr = reinterpret_cast<const uint8_t*>(&val);
            vec.insert(vec.end(), arr, arr + size);
        }
        template <typename T> void add_model(const T& model)
        {
            std::vector<uint8_t> vec = {};
            if (model) {
                tree::Model::Getter m_getter(vec);
                model->get(m_getter);
                add(m_getter.size());
                add(vec);
            } else {
                add(static_cast<uint64_t>(0));
            }
        }
        // necessary to be public for tree::TreeEnsembleModel
        void add(std::vector<uint8_t>& other_vec) { vec.insert(vec.end(), other_vec.begin(), other_vec.end()); }
        const uint64_t size() const { return vec.size(); }

    private:
        std::vector<uint8_t>& vec;
    };

    class Setter {
    public:
        Setter(const std::vector<uint8_t>& _vec)
            : vec(_vec)
            , offset(0)
        {
        }
        template <typename T> void get(T* val)
        {
            const uint64_t size = sizeof(*val);
            if (size > vec.size() - offset)
                throw std::runtime_error("Inconsistent model data.");
            memcpy(val, &vec[offset], size);
            offset += size;
        }
        template <typename T> void get(T* val, const uint64_t size)
        {
            if (size > vec.size() - offset)
                throw std::runtime_error("Inconsistent model data.");
            memcpy(val, &vec[offset], size);
            offset += size;
        }
        uint64_t get_offset() { return offset; }
        uint64_t get_size() { return vec.size(); }
        void     check_before(uint64_t len)
        {
            if (vec.size() - offset < len)
                throw std::runtime_error("Inconsistent model data.");
        }
        void check_after(uint64_t offset_begin, uint64_t len)
        {
            if (offset - offset_begin != len)
                throw std::runtime_error("Inconsistent model data.");
        }

    private:
        const std::vector<uint8_t>& vec;
        uint64_t                    offset;
    };

    virtual void get(tree::Model::Getter& getter)                     = 0;
    virtual void put(tree::Model::Setter& setter, const uint64_t len) = 0;
};

}

#endif