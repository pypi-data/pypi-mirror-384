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

#ifndef _CYCLE_UTILS_H_
#define _CYCLE_UTILS_H_

#include <cstdint>
#include <sstream>
#include <fstream>
#include <iostream>
#include <algorithm>
#include <string>
#include <limits>
#include <cstdint>

#include "Macros.h"

#ifdef USE_EXT_GRAPH
#include "compressedGraph.h"
#endif

#ifndef USE_TBB
#include <omp.h>
#else
#include <tbb/task.h>
#include <tbb/combinable.h>
#include <tbb/parallel_for.h>
#include <tbb/tick_count.h>
#include <tbb/task_scheduler_init.h>
#include <tbb/blocked_range.h>
#include <tbb/spin_mutex.h>
#include <tbb/atomic.h>
using namespace tbb;
#endif

#ifndef USE_TBB
/// OpenMP-related macros

#define SPAWN_ROOT_TASK(t)                                                                                             \
    do {                                                                                                               \
        auto* a = new t;                                                                                               \
        a->execute();                                                                                                  \
        delete a;                                                                                                      \
    } while (0)

#define SPAWN_SINGLE_TASK(t)                                                                                           \
    do {                                                                                                               \
        auto* a = new t;                                                                                               \
        a->execute();                                                                                                  \
        delete a;                                                                                                      \
    } while (0)

#else
/// TBB-related macros

#define SPAWN_ROOT_TASK(t)                                                                                             \
    do {                                                                                                               \
        auto* a = new (task::allocate_root()) t;                                                                       \
        task::spawn_root_and_wait(*a);                                                                                 \
    } while (0)

#define SPAWN_SINGLE_TASK(t)                                                                                           \
    do {                                                                                                               \
        increment_ref_count();                                                                                         \
        auto* a = new (allocate_child()) t;                                                                            \
        spawn(*a);                                                                                                     \
    } while (0)

#endif

using namespace std;

namespace ParCycEnum {

#ifndef USE_EXT_GRAPH
typedef int     Timestamp;
typedef int64_t GraphElemID;
#endif
const Timestamp MAX_TS = (std::numeric_limits<Timestamp>::max() >> 1);

inline char* getCmdOption(char** begin, char** end, const std::string& option)
{
    char** itr = std::find(begin, end, option);
    if (itr != end && ++itr != end)
        return *itr;
    return 0;
}

inline bool cmdOptionExists(char** begin, char** end, const std::string& option)
{
    return std::find(begin, end, option) != end;
}

#ifdef USE_TBB
#define TASK_RET tbb::task*
#else
#define TASK_RET void
#endif
}

#endif //_GRAPH_UTILS_H_
