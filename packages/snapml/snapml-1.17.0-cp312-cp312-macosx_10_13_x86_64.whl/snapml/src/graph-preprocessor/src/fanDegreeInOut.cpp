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

#include <vector>
#include <map>
#include <unordered_map>
#include <unordered_set>
#include <fstream>

#include "featureEngineering.h"
#include "graph.h"
#include "utils.h"

#ifdef USE_TBB
using namespace tbb;
#endif

double computeFanDegBatchAPI(Graph* g, PerThreadDataFrame& nodeDF, runSettings& config, vector<GraphElemID> edgeIDs)
{
    auto fan_start = chrono::high_resolution_clock::now();

    unordered_set<GraphElemID> setEdgeIDs(edgeIDs.size());

    if (config.vertexFeatures == false && config.batchedFeatures == true) {
        for (auto el : edgeIDs)
            setEdgeIDs.insert(el);
    }

#ifndef USE_TBB
#pragma omp parallel default(shared)
#pragma omp single
    {
#pragma omp taskloop
        for (unsigned int it = 0; it < edgeIDs.size(); it++) {
#else
    parallel_for(size_t(0), size_t(edgeIDs.size()), [&](size_t it) {
#endif

            GraphElemID eid    = edgeIDs[it];
            int         eindex = g->edgeIdMap[eid];

            Timestamp ts_fi = g->getEdge(eindex)->getTStamp() - config.timewindows[Pattern::FanIn];
            Timestamp ts_fo = g->getEdge(eindex)->getTStamp() - config.timewindows[Pattern::FanOut];
            Timestamp ts_di = g->getEdge(eindex)->getTStamp() - config.timewindows[Pattern::DegIn];
            Timestamp ts_do = g->getEdge(eindex)->getTStamp() - config.timewindows[Pattern::DegOut];

            Timestamp ts_end = g->getEdge(eindex)->getTStamp();

            int fromV = g->getEdge(eindex)->getSourceVertexIndex();
            int toV   = g->getEdge(eindex)->getTargetVertexIndex();

            /// Compute fan-outs
            {
                // count fan out degree, collect edges involved
                int                     fanOut = 0;
                std::vector<int>        fanOutEdges;
                std::unordered_set<int> fanOutVertices;

                int              outDegree = 0;
                std::vector<int> outDegreeEdges;
                g->foreachOutEdge(fromV, [&](int v, Timestamp tv, GraphElemID eiv) {
                    if ((v != fromV) && (tv <= ts_end)) {
                        if (config.patternExists(Pattern::DegOut) && (tv > ts_do)) {
                            outDegree += 1;
                            if (!config.batchedFeatures || setEdgeIDs.find(eiv) != setEdgeIDs.end()) {
                                outDegreeEdges.push_back(eiv);
                            }
                        }
                        if (config.patternExists(Pattern::FanOut) && (tv > ts_fo)) {
                            if (fanOutVertices.count(v) == 0) {
                                fanOut += 1;
                                fanOutVertices.insert(v);
                            }
                            if (!config.batchedFeatures || setEdgeIDs.find(eiv) != setEdgeIDs.end()) {
                                fanOutEdges.push_back(eiv);
                            }
                        }
                    }
                });

                if (config.patternExists(Pattern::FanOut)) {
                    if (fanOut >= 2) {
                        if (config.vertexFeatures == false) {
                            for (auto it : fanOutEdges) {
                                nodeDF.incrementPatternCount(it, Pattern::FanOut,
                                                             binCounts(config.bins[Pattern::FanOut], fanOut));
                            }
                        } else {
                            nodeDF.incrementPatternCount(fromV, Pattern::FanOut,
                                                         binCounts(config.bins[Pattern::FanOut], fanOut));
                        }
                    }
                }

                if (config.patternExists(Pattern::DegOut)) {
                    if (outDegree >= 2) {
                        if (config.vertexFeatures == false) {
                            for (auto it : outDegreeEdges)
                                nodeDF.incrementPatternCount(it, Pattern::DegOut,
                                                             binCounts(config.bins[Pattern::DegOut], outDegree));
                        } else {
                            nodeDF.incrementPatternCount(fromV, Pattern::DegOut,
                                                         binCounts(config.bins[Pattern::DegOut], outDegree));
                        }
                    }
                }
            }

            /// Compute fan-ins
            {
                // update fan in counts analogously to fan outs but using inEdgeArray
                int                     fanIn = 0;
                std::vector<int>        fanInEdges;
                std::unordered_set<int> fanInVertices;

                int              inDegree = 0;
                std::vector<int> inDegreeEdges;
                g->foreachInEdge(toV, [&](int u, Timestamp tu, GraphElemID eiu) {
                    if ((u != toV) && (tu <= ts_end)) {
                        if (config.patternExists(Pattern::DegIn) && (tu > ts_di)) {
                            inDegree += 1;
                            if (!config.batchedFeatures || setEdgeIDs.find(eiu) != setEdgeIDs.end()) {
                                inDegreeEdges.push_back(eiu);
                            }
                        }
                        if (config.patternExists(Pattern::FanIn) && (tu > ts_fi)) {
                            if (fanInVertices.count(u) == 0) {
                                fanInVertices.insert(u);
                                fanIn += 1;
                            }
                            if (!config.batchedFeatures || setEdgeIDs.find(eiu) != setEdgeIDs.end()) {
                                fanInEdges.push_back(eiu);
                            }
                        }
                    }
                });

                if (config.patternExists(Pattern::FanIn)) {
                    if (fanIn >= 2) {
                        if (config.vertexFeatures == false) {
                            for (auto it : fanInEdges)
                                nodeDF.incrementPatternCount(it, Pattern::FanIn,
                                                             binCounts(config.bins[Pattern::FanIn], fanIn));
                        } else {
                            nodeDF.incrementPatternCount(toV, Pattern::FanIn,
                                                         binCounts(config.bins[Pattern::FanIn], fanIn));
                        }
                    }
                }

                if (config.patternExists(Pattern::DegIn)) {
                    if (inDegree >= 2) {
                        if (config.vertexFeatures == false) {
                            for (auto it : inDegreeEdges)
                                nodeDF.incrementPatternCount(it, Pattern::DegIn,
                                                             binCounts(config.bins[Pattern::DegIn], inDegree));
                        } else {
                            nodeDF.incrementPatternCount(toV, Pattern::DegIn,
                                                         binCounts(config.bins[Pattern::DegIn], inDegree));
                        }
                    }
                }
            }
#ifndef USE_TBB
        }
    }
#else
    });
#endif

    auto   fan_end   = chrono::high_resolution_clock::now();
    double fan_total = chrono::duration_cast<chrono::milliseconds>(fan_end - fan_start).count() / 1000.0;

    return fan_total;
}
