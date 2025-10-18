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

#ifndef GRAPH_FEATURES_DATA_STRUCTS_H
#define GRAPH_FEATURES_DATA_STRUCTS_H

#include "utils.h"

template <typename T> class ConcurrentContainer {
public:
#ifndef USE_TBB
    ConcurrentContainer(int nt = 256)
        : existVec(nt, 0)
        , vecsize(nt)
    {
        container.resize(nt);
    }
#else
    ConcurrentContainer(int nt = 256) { }
#endif

    T& local()
    {
#ifdef USE_TBB
        return container.local();
#else
        int threadId       = omp_get_thread_num();
        existVec[threadId] = 1;
        return container[threadId];
#endif
    }

    T& local(bool& exists)
    {
#ifdef USE_TBB
        T& ret = container.local(exists);
#else

        int threadId = omp_get_thread_num();

        T& ret = container[threadId];
        exists = existVec[threadId];

        existVec[threadId] = 1;
#endif
        return ret;
    }

    template <typename UnaryFunc> void combine_each(UnaryFunc f)
    {
#ifdef USE_TBB
        container.combine_each(f);
#else
        for (int i = 0; i < vecsize; i++) {
            if (existVec[i]) {
                f(container[i]);
            }
        }
#endif
    }

    void clear() { container.clear(); }

    void setNumThreads(int nthr)
    {
#ifndef USE_TBB
        vecsize = nthr;
        container.resize(nthr);
        existVec.resize(nthr, 0);
#endif
    }

private:
#ifdef USE_TBB
    tbb::combinable<T> container;
#else
    vector<T>   container;
    vector<int> existVec;
    int         vecsize = 1;
#endif
};

#endif