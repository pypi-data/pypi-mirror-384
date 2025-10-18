/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2022
 * IBM Zurich Research Laboratory - Infrastructure AIOPS Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Jovan Blanusa
 *
 * End Copyright
 ********************************************************************/

#ifndef _MACROS_H_
#define _MACROS_H_

//#define MPI_IMPL

/** Define whether to use the improvements to the (temporal) Read-Tarjan algorithm **/
#define BLK_FORWARD
#define PATH_FORWARD
#define SUCCESSFUL_DFS_BLK

#ifndef BLK_FORWARD
#undef SUCCESSFUL_DFS_BLK
#endif

//#define USE_TBB

#endif //_MACROS_H_
