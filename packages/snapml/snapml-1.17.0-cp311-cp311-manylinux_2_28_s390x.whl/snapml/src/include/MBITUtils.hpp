/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2022
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Thomas Parnell
 *                Nikolaos Papandreou
 *                Milos Stanisavljevic
 *
 * End Copyright
 ********************************************************************/

#ifndef MBIT_UTILS
#define MBIT_UTILS

#include "SIMDDefines.hpp"

extern "C" {
#include "zdnn.h"
}

typedef vector unsigned int   vec_float32;
typedef vector unsigned short vec_float16;
typedef vector unsigned short vec_int16;
typedef vector unsigned char  vec_byte;

namespace glm {

/*=================================================================================================================*/
/* Zdnn helper functions */
/*=================================================================================================================*/

static const char* zdnnGetErrorString(zdnn_status status)
{
    switch (status) {
    case ZDNN_INVALID_SHAPE:
        return "ZDNN_INVALID_SHAPE";
    case ZDNN_INVALID_LAYOUT:
        return "ZDNN_INVALID_LAYOUT";
    case ZDNN_INVALID_TYPE:
        return "ZDNN_INVALID_TYPE";
    case ZDNN_INVALID_FORMAT:
        return "ZDNN_INVALID_FORMAT";
    case ZDNN_INVALID_DIRECTION:
        return "ZDNN_INVALID_DIRECTION";
    case ZDNN_ALLOCATION_FAILURE:
        return "ZDNN_ALLOCATION_FAILURE";
    case ZDNN_INVALID_BUFFER:
        return "ZDNN_INVALID_BUFFER";
    case ZDNN_CONVERT_FAILURE:
        return "ZDNN_CONVERT_FAILURE";
    case ZDNN_INVALID_STATE:
        return "ZDNN_INVALID_STATE";
    default:
        return "unknown error";
    }
}

static void zdnn_safe(zdnn_status chk, const char* msg)
{
    if (chk != ZDNN_OK) {
        std::cout << zdnnGetErrorString(chk) << std::endl;
        throw std::runtime_error(msg);
    }
}

static zdnn_ztensor* alloc_ztensor(uint32_t* shape, zdnn_data_layouts pre_tfrmd_layout, zdnn_data_types type)
{
    // Create the pretransformed description
    zdnn_tensor_desc* pre_tfrmd_desc = (zdnn_tensor_desc*)malloc(sizeof(zdnn_tensor_desc));
    switch (pre_tfrmd_layout) {
    case (ZDNN_1D):
        zdnn_init_pre_transformed_desc(pre_tfrmd_layout, type, pre_tfrmd_desc, shape[0]);
        break;
    case (ZDNN_2D):
    case (ZDNN_2DS):
        zdnn_init_pre_transformed_desc(pre_tfrmd_layout, type, pre_tfrmd_desc, shape[0], shape[1]);
        break;
    case (ZDNN_3D):
    case (ZDNN_3DS):
        zdnn_init_pre_transformed_desc(pre_tfrmd_layout, type, pre_tfrmd_desc, shape[0], shape[1], shape[2]);
        break;
    case (ZDNN_4D):
    case (ZDNN_NHWC):
    case (ZDNN_NCHW):
    case (ZDNN_HWCK):
        zdnn_init_pre_transformed_desc(pre_tfrmd_layout, type, pre_tfrmd_desc, shape[0], shape[1], shape[2], shape[3]);
        break;
    default:
        throw std::runtime_error("Wrong tensor format, allocation failed");
        break;
    }

    // Create the transformed description
    zdnn_tensor_desc* tfrmd_desc = (zdnn_tensor_desc*)malloc(sizeof(zdnn_tensor_desc));
    zdnn_safe(zdnn_generate_transformed_desc(pre_tfrmd_desc, tfrmd_desc),
              "[ZDNN_MBIT] coudldn't transform descriptor.");

    // Create ztensor
    zdnn_ztensor* ztensor = (zdnn_ztensor*)malloc(sizeof(zdnn_ztensor));
    zdnn_safe(zdnn_init_ztensor_with_malloc(pre_tfrmd_desc, tfrmd_desc, ztensor),
              "[ZDNN_MBIT] coudldn't allocate ztensor.");

    return ztensor;
}

static void inline aiu_vec_lengthen_to_fp32_inline(vec_int16 a, vec_float32* out1, vec_float32* out2)
{
    vec_float32 work_float_1;
    vec_float32 work_float_2;

    // clang-format off
    __asm volatile(".insn vrr,0xe60000000056,%[out1],%[in_vec],0,2,0,0    \n\t"
                  ".insn vrr,0xe6000000005E,%[out2],%[in_vec],0,2,0,0     \n\t"
                  : [ out1 ] "=&v"(work_float_1), [ out2 ] "=v"(work_float_2)
                  : [ in_vec ] "v"(a));
    // clang-format on

    *out1 = work_float_1;
    *out2 = work_float_2;

    return;
}

/*
static zdnn_status custom_transform_origtensor(void* in_buffer, float* out_buffer, uint32_t num_el)
{
#if defined Z14_SIMD && !defined ZDNN_CONFIG_SIMULATION
    uint16_t*    in_data = (uint16_t*)in_buffer;
    vec_float16  input_data;
    vec_float32* output_data = (vec_float32*)out_buffer;

    vector unsigned int idx;
    vector unsigned int idx_left;
    vector unsigned int idx_right;
    vector unsigned int idx_left_incr  = (vector unsigned int) { 0, 1, 2, 3 } << 6;
    vector unsigned int idx_right_incr = (vector unsigned int) { 4, 5, 6, 7 } << 6;
    for (uint32_t i = 0; i < num_el / 8; i++) {
        idx        = (vector unsigned int) { i, i, i, i } << 9;
        idx_left   = idx + idx_left_incr;
        idx_right  = idx + idx_right_incr;
        input_data = (vec_float16) { in_data[idx_left[0]],  in_data[idx_left[1]],  in_data[idx_left[2]],
                                     in_data[idx_left[3]],  in_data[idx_right[0]], in_data[idx_right[1]],
                                     in_data[idx_right[2]], in_data[idx_right[3]] };
        aiu_vec_lengthen_to_fp32_inline(input_data, (vec_float32*)output_data, (vec_float32*)(output_data + 1));
        output_data += 2;
    }

    int remaining_el = num_el % 8;
    if (!remaining_el)
        return ZDNN_OK;

    vec_float32 tmp_out_left;
    vec_float32 tmp_out_right;
    uint32_t    i = num_el / 8;
    idx           = (vector unsigned int) { i, i, i, i } << 9;
    idx_left      = idx + idx_left_incr;
    idx_right     = idx + idx_right_incr;
    input_data
        = (vec_float16) { in_data[idx_left[0]],  in_data[idx_left[1]],  in_data[idx_left[2]],  in_data[idx_left[3]],
                          in_data[idx_right[0]], in_data[idx_right[1]], in_data[idx_right[2]], in_data[idx_right[3]] };

    int remaining_bytes_to_set = remaining_el * sizeof(uint32_t);

    aiu_vec_lengthen_to_fp32_inline(input_data, (vec_float32*)&tmp_out_left, (vec_float32*)&tmp_out_right);
    vec_store_len(tmp_out_left, (uint32_t*)output_data, remaining_bytes_to_set - 1);

    if (remaining_el > 4) {
        remaining_bytes_to_set -= 4 * sizeof(uint32_t);
        vec_store_len(tmp_out_right, (uint32_t*)(output_data + 1), remaining_bytes_to_set - 1);
    }

#else
    memcpy((void*)out_buffer, in_buffer, num_el * sizeof(float));
#endif

    return ZDNN_OK;
}
*/

/// Sets a zdnn_ztensor struct as transformed
///
/// Typical usage:
/// \code
///   zdnn_set_ztensor(&ztensor);
/// \endcode
///
/// \param ztensor the zdnn_ztensor struct being set.
///
/// \returns None
///

/*
static void zdnn_set_ztensor(zdnn_ztensor* ztensor) { ztensor->is_transformed = true; }
*/
}

#endif