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

#ifndef PAR_OUT_LOOP_H
#define PAR_OUT_LOOP_H

#include <set>
#include <unordered_map>
#include "CycleUtils.h"
#include "Macros.h"
#include "CycleEnumGraph.h"

namespace ParCycEnum {

template <typename TF>
inline void parallelOuterLoop(Graph* g, int numThreads, bool invertSearch, int proc_rank, int cluster_size,
                              TF&& processEdge)
{
    auto& edgeList = g->getEdgeList();

#ifndef USE_TBB
    omp_set_num_threads(numThreads);

#pragma omp parallel default(shared)
#pragma omp single
    {
        if (edgeList.size() != 0) {

#pragma omp taskloop untied
            for (unsigned int i = proc_rank; i < edgeList.size(); i += cluster_size) {

                int         from = !invertSearch ? edgeList[i].fromV : edgeList[i].toV;
                int         to   = !invertSearch ? edgeList[i].toV : edgeList[i].fromV;
                Timestamp   ts   = edgeList[i].tstamp;
                GraphElemID eid  = edgeList[i].eid;

                if (from != to)
                    processEdge(from, to, ts, eid);
            }
        } else {
            for (int from = 0; from < g->getVertexNo(); from++) {
#pragma omp task firstprivate(from)
                {

                    if ((g->numNeighbors(from) != 0) && (g->numInEdges(from) != 0)) {

                        auto beginIt = !invertSearch ? g->beginOut(from) : g->beginIn(from);
                        auto endIt   = !invertSearch ? g->endOut(from) : g->endIn(from);
                        for (auto colelem = beginIt; colelem < endIt; colelem++) {
                            // Prevent visiting loops
                            if (colelem->vertex == from)
                                continue;
#pragma omp task firstprivate(colelem)
                            {
                                int   w    = colelem->vertex;
                                auto& tset = colelem->tstamps;

                                for (int j = 0; j < static_cast<int>(tset.size()); j++) {

                                    if ((from + j) % cluster_size == proc_rank) {

                                        int         to  = w;
                                        Timestamp   ts  = tset[j];
                                        GraphElemID eid = colelem->eids[j];

                                        processEdge(from, to, ts, eid);
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
#else
    if (edgeList.size() != 0) {
        parallel_for(size_t(proc_rank), size_t(edgeList.size()), size_t(cluster_size), [&](size_t i) {
            int         from = !invertSearch ? edgeList[i].fromV : edgeList[i].toV;
            int         to   = !invertSearch ? edgeList[i].toV : edgeList[i].fromV;
            Timestamp   ts   = edgeList[i].tstamp;
            GraphElemID eid  = edgeList[i].eid;

            if (from != to)
                processEdge(from, to, ts, eid);
        });
    } else {
        parallel_for(size_t(0), size_t(g->getVertexNo()), [&](size_t i) {
            if ((g->numNeighbors(i) != 0) && (g->numInEdges(i) != 0)) {

                auto beginIt = !invertSearch ? g->beginOut(i) : g->beginIn(i);
                auto endIt   = !invertSearch ? g->endOut(i) : g->endIn(i);

                int loopLen = endIt - beginIt;
                parallel_for(size_t(0), size_t(loopLen), [&](size_t k) {
                    // Make this for loop parallel
                    auto colelem = beginIt;
                    colelem += (int)k;

                    // Prevent visiting loops
                    if (colelem->vertex != i) {
                        int   w    = colelem->vertex;
                        auto& tset = colelem->tstamps;

                        parallel_for(size_t(0), size_t(tset.size()), [&](size_t j) {
                            if (i % cluster_size == proc_rank) {
                                int         from = i, to = w;
                                Timestamp   ts  = tset[j];
                                GraphElemID eid = colelem->eids[j];

                                processEdge(from, to, ts, eid);
                            }
                        });
                    }
                });
            }
        });
    }
#endif
}

template <typename TF>
inline void parallelColElemIterate(Graph* g, int numThreads, bool invertSearch, int proc_rank, int cluster_size,
                                   TF&& processColElem)
{
#ifndef USE_TBB
    omp_set_num_threads(numThreads);

#pragma omp parallel default(shared)
#pragma omp single
    {
        //#pragma omp taskloop untied
        for (int from = 0; from < g->getVertexNo(); from++) {
#pragma omp task firstprivate(from)
            {

                if ((g->numNeighbors(from) != 0) && (g->numInEdges(from) != 0)) {

                    auto beginIt = !invertSearch ? g->beginOut(from) : g->beginIn(from);
                    auto endIt   = !invertSearch ? g->endOut(from) : g->endIn(from);
                    for (auto colelem = beginIt; colelem < endIt; colelem++) {
                        // Prevent visiting loops
                        if (colelem->vertex == from)
                            continue;
#pragma omp task firstprivate(colelem)
                        {
                            int to = colelem->vertex;

                            if (from % cluster_size == proc_rank) {

                                auto& colElem = *colelem;

                                processColElem(from, to, colElem);
                            }
                        }
                    }
                }
            }
        }
    }
#else
    task_scheduler_init init(numThreads);

    parallel_for(size_t(0), size_t(g->getVertexNo()), [&](size_t i) {
        if ((g->numNeighbors(i) != 0) && (g->numInEdges(i) != 0)) {

            auto beginIt = !invertSearch ? g->beginOut(i) : g->beginIn(i);
            auto endIt   = !invertSearch ? g->endOut(i) : g->endIn(i);

            int loopLen = endIt - beginIt;
            parallel_for(size_t(0), size_t(loopLen), [&](size_t k) {
                // Make this for loop parallel
                auto colelem = beginIt;
                colelem += (int)k;
                // Make this for loop parallel

                // Prevent visiting loops
                if (colelem->vertex != i) {

                    if (i % cluster_size == proc_rank) {
                        int   from    = i;
                        int   to      = colelem->vertex;
                        auto& colElem = *colelem;

                        processColElem(from, to, colElem);
                    }
                }
            });
        }
    });
#endif
}

template <typename TF>
inline void parallelOuterLoopBatch(std::vector<CompressedEdge>* batchOfEdges, int numThreads, bool invertSearch,
                                   int proc_rank, int cluster_size, TF&& processEdge)
{
    unsigned int batchSize = 0;
    if (batchOfEdges)
        batchSize = batchOfEdges->size();

    unsigned int start = proc_rank;
    unsigned int step  = cluster_size;

#ifndef USE_TBB
    omp_set_num_threads(numThreads);

#pragma omp parallel default(shared)
#pragma omp single
    {
#pragma omp taskloop
        for (unsigned int i = start; i < batchSize; i += step) {
#else
    parallel_for(size_t(start), size_t(batchSize), size_t(step), [&](size_t i) {
#endif
            int         fromV, toV;
            GraphElemID eid;
            Timestamp   ts;

            fromV = (*batchOfEdges)[i].fromV;
            toV   = (*batchOfEdges)[i].toV;
            ts    = (*batchOfEdges)[i].tstamp;
            eid   = (*batchOfEdges)[i].eid;

            if (invertSearch)
                swap(fromV, toV);

            if (fromV != toV)
                processEdge(fromV, toV, ts, eid);
#ifndef USE_TBB
        }
    }
#else
    });
#endif
}

}

#endif