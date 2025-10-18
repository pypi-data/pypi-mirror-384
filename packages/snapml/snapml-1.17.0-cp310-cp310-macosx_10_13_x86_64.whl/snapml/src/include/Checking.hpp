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
 *                Andreea Anghel
 *
 * End Copyright
 ********************************************************************/

#ifndef GLM_CHECKING
#define GLM_CHECKING

#include <stdexcept>
#include <cuda_runtime.h>
#include <iostream>

namespace glm {

static void cuda_safe(cudaError_t chk, const char* msg)
{
    if (chk != cudaSuccess) {
        std::cout << cudaGetErrorString(chk) << std::endl;
        throw std::runtime_error(msg);
    }
}

}

#endif
