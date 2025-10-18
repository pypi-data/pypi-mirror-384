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
 * End Copyright
 ********************************************************************/

#ifndef UTILS_HH_
#define UTILS_HH_

template <typename T> inline void copyData(T* x, const T& y) { *x = y; }

#endif // UTILS_HH_
