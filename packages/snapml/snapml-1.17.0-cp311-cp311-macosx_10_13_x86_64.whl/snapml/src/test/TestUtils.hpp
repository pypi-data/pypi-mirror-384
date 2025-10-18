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
 *                Milos Stanisavljvic
 *
 * End Copyright
 ********************************************************************/

#ifndef GLM_TEST_UTILS
#define GLM_TEST_UTILS

namespace glm {
namespace tests {

    template <class T> bool are_close(T a, T b, T eps)
    {
        if ((fabs(a) < eps) || (fabs(b) < eps))
            return fabs(a - b) < eps;
        return (fabs(a - b) / fabs(b)) < eps;
    }

}
}

#endif
