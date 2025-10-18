/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2019
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Nikolas Ioannou
 *                Thomas Parnell
 *
 * End Copyright
 ********************************************************************/

#ifndef TREE_UTILS_HH_
#define TREE_UTILS_HH_

#include <random>
#include <cmath>
#include <limits>

namespace tree {

static void fisher_yates(std::vector<uint32_t>& x, std::mt19937& rng)
{

    if (x.size() == 0)
        return;

    for (uint32_t i = x.size() - 1; i > 0; --i) {
        std::uniform_int_distribution<uint32_t> uniform_dist(0, i);
        const uint32_t                          j   = uniform_dist(rng);
        const uint32_t                          tmp = x[i];
        x[i]                                        = x[j];
        x[j]                                        = tmp;
    }
}

static inline bool are_different(float a, float b)
{
    float max1pn = std::max({ 1.0f, std::fabs(a), std::fabs(b) });
    return (std::fabs(b - a) > std::numeric_limits<float>::epsilon() * max1pn);
}

}

#endif
