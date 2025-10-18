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
#include <unordered_set>
#include <unordered_map>
#include <fstream>

#include "featureEngineering.h"
#include "graph.h"
#include "utils.h"
#include "outputDataStructures.h"

#ifdef USE_TBB
using namespace tbb;
#endif

double computeScatterGatherBatchAPI(Graph* g, PerThreadDataFrame& nodeDF, runSettings& config,
                                    vector<GraphElemID> edgeIDs)
{
    auto sg_start = chrono::high_resolution_clock::now();

    unordered_set<int>         setVertexIndices(edgeIDs.size());
    unordered_set<GraphElemID> setEdgeIDs(edgeIDs.size());

    if (config.vertexFeatures == true) {
        if (config.vertexFeatures == true && config.batchedFeatures == true) {
            for (auto eid : edgeIDs) {
                int eindex = g->edgeIdMap[eid];
                int fromV  = g->getEdge(eindex)->getSourceVertexIndex();
                int toV    = g->getEdge(eindex)->getTargetVertexIndex();
                setVertexIndices.insert(fromV);
                setVertexIndices.insert(toV);
            }
        }
    } else {
        if (config.vertexFeatures == false && config.batchedFeatures == true) {
            for (auto eid : edgeIDs)
                setEdgeIDs.insert(eid);
        }
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
            Timestamp   ts     = g->getEdge(eindex)->getTStamp() - config.timewindows[Pattern::ScatGat];
            Timestamp   ts_end = g->getEdge(eindex)->getTStamp();

            int fromV = g->getEdge(eindex)->getSourceVertexIndex();
            int toV   = g->getEdge(eindex)->getTargetVertexIndex();

            //#pragma omp taskloop
            /// Forward
            {
                // One-hop neighborhood: vertex and the edges that lead to it
                std::vector<ColElem*> oneHopNbhd;
                oneHopNbhd.reserve(g->numOutVertices(fromV));
                g->foreachOutVertex(fromV, [&](int v, ColElem& colelem) {
                    if ((colelem.tstamps.back() >= ts) && (v != fromV)) {
                        oneHopNbhd.push_back(&colelem);
                    }
                });

                if (oneHopNbhd.size() >= 1) {
                    vector<int> twoHopNbhd;
                    twoHopNbhd.reserve(g->numOutVertices(toV));
                    g->foreachOutVertex(toV, [&](int v, ColElem& colelem) {
                        if ((colelem.tstamps.back() >= ts) && (v != toV) && (v != fromV)) {
                            twoHopNbhd.push_back(v);
                        }
                    });

#ifndef USE_TBB
                    for (unsigned int wi = 0; wi < twoHopNbhd.size(); wi++) {
#pragma omp task firstprivate(wi)
                        {
#else
                parallel_for(size_t(0), size_t(twoHopNbhd.size()), [&](size_t wi) {
#endif
                            int w = twoHopNbhd[wi];

                            auto inWverties = g->getAdjList(w, false);

                            int              intVertCnt = 0;
                            std::vector<int> edgeSGVec;
                            std::vector<int> intermediateVertices;
                            for (auto colelem : oneHopNbhd) {
                                auto& colelem1 = *colelem;
                                int   vert     = colelem1.vertex;
                                auto  it       = inWverties.find(vert);

                                if (it != inWverties.end()) {
                                    auto& colelem2 = it->second;

                                    // Prevent duplicate SG patterns
                                    if (colelem1.tstamps.back() > ts_end || colelem2.tstamps.back() > ts_end) {
                                        intVertCnt = 0;
                                        break;
                                    }

                                    if (colelem2.tstamps.back() >= ts) {
                                        intVertCnt++;
                                        intermediateVertices.push_back(vert);
                                        if (config.vertexFeatures == true) {
                                            // Collect vertices
                                        } else {
                                            // Collect edges
                                            for (int j = colelem2.tstamps.size() - 1; j >= 0; j--) {
                                                if (colelem2.tstamps[j] < ts)
                                                    break;
                                                edgeSGVec.push_back(colelem2.eids[j]);
                                            }
                                            for (int j = colelem1.tstamps.size() - 1; j >= 0; j--) {
                                                if (colelem1.tstamps[j] < ts)
                                                    break;
                                                edgeSGVec.push_back(colelem1.eids[j]);
                                            }
                                        }
                                    }
                                }
                            }

                            if (intVertCnt >= 2) {
                                if (config.vertexFeatures == false) {
                                    for (auto e : edgeSGVec) {
                                        if (!config.batchedFeatures || setEdgeIDs.find(e) != setEdgeIDs.end()) {
                                            nodeDF.incrementPatternCount(
                                                e, Pattern::ScatGat,
                                                binCounts(config.bins[Pattern::ScatGat], intVertCnt));
                                        }
                                    }
                                } else {
                                    // Intermediary vertices
                                    for (auto v : intermediateVertices) {
                                        if (!config.batchedFeatures
                                            || setVertexIndices.find(v) != setVertexIndices.end()) {
                                            nodeDF.incrementPatternCount(
                                                v, Pattern::ScatGat,
                                                binCounts(config.bins[Pattern::ScatGat], intVertCnt));
                                        }
                                    }
                                    // Source vertex
                                    nodeDF.incrementPatternCount(fromV, Pattern::ScatGat,
                                                                 binCounts(config.bins[Pattern::ScatGat], intVertCnt));
                                    // Destination vertex
                                    if (!config.batchedFeatures || setVertexIndices.find(w) != setVertexIndices.end()) {
                                        nodeDF.incrementPatternCount(
                                            w, Pattern::ScatGat, binCounts(config.bins[Pattern::ScatGat], intVertCnt));
                                    }
                                }
                            }
#ifndef USE_TBB
                        }
                    }
#else
                });
#endif
                }
            }

            /// Backwards
            {
                // One-hop neighborhood: vertex and the edges that lead to it
                std::vector<ColElem*> oneHopNbhd;
                oneHopNbhd.reserve(g->numOutVertices(toV));
                g->foreachInVertex(toV, [&](int v, ColElem& colelem) {
                    if ((colelem.tstamps.back() >= ts) && (v != toV)) {
                        oneHopNbhd.push_back(&colelem);
                    }
                });

                if (oneHopNbhd.size() >= 1) {
                    vector<int> twoHopNbhd;
                    twoHopNbhd.reserve(g->numInVertices(fromV));
                    g->foreachInVertex(fromV, [&](int v, ColElem& colelem) {
                        if ((colelem.tstamps.back() >= ts) && (v != toV) && (v != fromV)) {
                            twoHopNbhd.push_back(v);
                        }
                    });

#ifndef USE_TBB
                    for (unsigned int wi = 0; wi < twoHopNbhd.size(); wi++) {
#pragma omp task firstprivate(wi)
                        {
#else
                parallel_for(size_t(0), size_t(twoHopNbhd.size()), [&](size_t wi) {
#endif
                            int w = twoHopNbhd[wi];

                            auto outWverties = g->getAdjList(w, true);

                            int              intVertCnt = 0;
                            std::vector<int> edgeSGVec;
                            std::vector<int> intermediateVertices;
                            for (auto colelem : oneHopNbhd) {
                                auto& colelem1 = *colelem;
                                int   vert     = colelem1.vertex;

                                auto it = outWverties.find(vert);
                                if (it != outWverties.end()) {
                                    auto& colelem2 = it->second;

                                    // Prevent duplicate SG patterns
                                    if (colelem1.tstamps.back() > ts_end || colelem2.tstamps.back() > ts_end) {
                                        intVertCnt = 0;
                                        break;
                                    }

                                    // Prevent duplicate SG patterns
                                    if (colelem1.tstamps.back() > ts_end || colelem2.tstamps.back() > ts_end) {
                                        intVertCnt = 0;
                                        break;
                                    }

                                    if (colelem2.tstamps.back() >= ts) {
                                        intVertCnt++;
                                        intermediateVertices.push_back(vert);
                                        if (config.vertexFeatures == true) {
                                            // Collect vertices
                                        } else {
                                            // Collect edges
                                            for (int j = colelem2.tstamps.size() - 1; j >= 0; j--) {
                                                if (colelem2.tstamps[j] < ts)
                                                    break;
                                                edgeSGVec.push_back(colelem2.eids[j]);
                                            }
                                            for (int j = colelem1.tstamps.size() - 1; j >= 0; j--) {
                                                if (colelem1.tstamps[j] < ts)
                                                    break;
                                                edgeSGVec.push_back(colelem1.eids[j]);
                                            }
                                        }
                                    }
                                }
                            }

                            if (intVertCnt >= 2) {

                                if (config.vertexFeatures == false) {
                                    for (auto e : edgeSGVec) {
                                        if (!config.batchedFeatures || setEdgeIDs.find(e) != setEdgeIDs.end()) {
                                            nodeDF.incrementPatternCount(
                                                e, Pattern::ScatGat,
                                                binCounts(config.bins[Pattern::ScatGat], intVertCnt));
                                        }
                                    }
                                } else {
                                    // Intermediary vertices
                                    for (auto v : intermediateVertices) {
                                        if (!config.batchedFeatures
                                            || setVertexIndices.find(v) != setVertexIndices.end()) {
                                            nodeDF.incrementPatternCount(
                                                v, Pattern::ScatGat,
                                                binCounts(config.bins[Pattern::ScatGat], intVertCnt));
                                        }
                                    }
                                    // Source vertex
                                    if (!config.batchedFeatures || setVertexIndices.find(w) != setVertexIndices.end()) {
                                        nodeDF.incrementPatternCount(
                                            w, Pattern::ScatGat, binCounts(config.bins[Pattern::ScatGat], intVertCnt));
                                    }
                                    // Destination vertex
                                    nodeDF.incrementPatternCount(toV, Pattern::ScatGat,
                                                                 binCounts(config.bins[Pattern::ScatGat], intVertCnt));
                                }
                            }
#ifndef USE_TBB
                        }
                    }
#else
                });
#endif
                }
            }
#ifndef USE_TBB
        }
    }
#else
    });
#endif

    auto   sg_end   = chrono::high_resolution_clock::now();
    double sg_total = chrono::duration_cast<chrono::milliseconds>(sg_end - sg_start).count() / 1000.0;
    return sg_total;
}