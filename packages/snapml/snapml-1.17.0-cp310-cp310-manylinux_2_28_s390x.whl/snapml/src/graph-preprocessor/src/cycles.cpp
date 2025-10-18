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

#include <map>
#include <vector>
#include <iostream>
#include <chrono>

#include "utils.h"
#include "cycles.h"

using namespace std;

#ifdef USE_TBB
using namespace tbb;
#endif

namespace {
// Variables to be forwarded to callbacks
Graph*              gg       = NULL;
PerThreadDataFrame* ptNodeDf = NULL;
runSettings*        gConfig  = NULL;

bool tempCycles = true;

/// TYPE 1 CALLBACK
void type1CycleCallback(vector<int>& cycle, vector<vector<GraphElemID>>& edgeIDs)
{
    if (!ptNodeDf || !gConfig)
        return;

    // Collect per-vertex features
    for (int node : cycle) {
        if (tempCycles)
            ptNodeDf->incrementPatternCount(node, Pattern::TempCycle,
                                            binCounts(gConfig->bins[Pattern::TempCycle], cycle.size()));
        else
            ptNodeDf->incrementPatternCount(node, Pattern::LCCycle,
                                            binCounts(gConfig->bins[Pattern::LCCycle], cycle.size()));
    }
}

/// TYPE 2 CALLBACK
void type2CycleCallback(vector<int>& cycle, vector<vector<GraphElemID>>& edgeIDs)
{
    if (!ptNodeDf || !gConfig)
        return;

    // Collect per-edge features
    for (auto& evec : edgeIDs) {
        for (auto eid : evec) {
            if (tempCycles)
                ptNodeDf->incrementPatternCount(eid, Pattern::TempCycle,
                                                binCounts(gConfig->bins[Pattern::TempCycle], cycle.size()));
            else
                ptNodeDf->incrementPatternCount(eid, Pattern::LCCycle,
                                                binCounts(gConfig->bins[Pattern::LCCycle], cycle.size()));
        }
    }
}

}

void computeTempCycles(Graph* g, PerThreadDataFrame& edgeDF, runSettings& config, int nthr)
{
    // Forward graphs to callbacks
    gg         = g;
    ptNodeDf   = &edgeDF;
    gConfig    = &config;
    tempCycles = true;

    ParCycEnum::ParallelCycleEnumerator enumerator(g->getCompressedGraph());

    // Register callback
    if (config.networkType == "type1") {
        enumerator.setCycleBundleFoundCallback(type1CycleCallback);
    } else {
        enumerator.setCycleBundleFoundCallback(type2CycleCallback);
    }

    int algo = 0; // Fine-grained Johnson

    // Run cycle enumeration
    auto cyc_start = chrono::steady_clock::now();

    enumerator.runCycleEnumeration(config.timewindows[Pattern::TempCycle], -1, nthr, algo);

    auto   cyc_end   = chrono::steady_clock::now();
    double cyc_total = chrono::duration_cast<chrono::milliseconds>(cyc_end - cyc_start).count() / 1000.0;
    config.processingTime[Pattern::TempCycle] = cyc_total;
}

void computeLCCycles(Graph* g, PerThreadDataFrame& edgeDF, runSettings& config, int nthr)
{
    // Forward graphs to callbacks
    gg         = g;
    ptNodeDf   = &edgeDF;
    gConfig    = &config;
    tempCycles = false;

    ParCycEnum::ParallelCycleEnumerator enumerator(g->getCompressedGraph());

    // Register callback
    if (config.networkType == "type1") {
        enumerator.setCycleBundleFoundCallback(type1CycleCallback);
    } else {
        enumerator.setCycleBundleFoundCallback(type2CycleCallback);
    }

    int algo = 4; // Fine-grained parallel length-constrained cycle enumeration

    // Run cycle enumeration
    auto cyc_start = chrono::steady_clock::now();
    enumerator.runCycleEnumeration(config.timewindows[Pattern::LCCycle], gConfig->maxlengths[Pattern::LCCycle], nthr,
                                   algo);
    auto   cyc_end   = chrono::steady_clock::now();
    double cyc_total = chrono::duration_cast<chrono::milliseconds>(cyc_end - cyc_start).count() / 1000.0;
    config.processingTime[Pattern::LCCycle] = cyc_total;
}

/// DynamicCycleFinder

namespace {

unordered_set<GraphElemID> setEdgeIDs;
unordered_set<int>         setVertexIDs;

void tempCycleCallbackBatch(vector<int>& cycle, vector<vector<GraphElemID>>& edgeIDs)
{
    if (!ptNodeDf || !gConfig)
        return;

    if (gConfig->vertexFeatures == false) {
        // Collect per-edge features
        for (auto& evec : edgeIDs) {
            for (auto eid : evec) {
                if (!gConfig->batchedFeatures || setEdgeIDs.find(eid) != setEdgeIDs.end()) {
                    ptNodeDf->incrementPatternCount(eid, Pattern::TempCycle,
                                                    binCounts(gConfig->bins[Pattern::TempCycle], cycle.size()));
                }
            }
        }
    } else {
        // Collect per-vertex features
        for (int node : cycle) {
            if (!gConfig->batchedFeatures || setVertexIDs.find(node) != setVertexIDs.end()) {
                ptNodeDf->incrementPatternCount(node, Pattern::TempCycle,
                                                binCounts(gConfig->bins[Pattern::TempCycle], cycle.size()));
            }
        }
    }
}

void lcCycleCallbackBatch(vector<int>& cycle, vector<vector<GraphElemID>>& edgeIDs)
{
    if (!ptNodeDf || !gConfig)
        return;

    if (gConfig->vertexFeatures == false) {
        // Collect per-edge features
        for (auto& evec : edgeIDs) {
            for (auto eid : evec) {
                if (!gConfig->batchedFeatures || setEdgeIDs.find(eid) != setEdgeIDs.end()) {
                    ptNodeDf->incrementPatternCount(eid, Pattern::LCCycle,
                                                    binCounts(gConfig->bins[Pattern::LCCycle], cycle.size()));
                }
            }
        }
    } else {
        // Collect per-vertex features
        for (int node : cycle) {
            if (!gConfig->batchedFeatures || setVertexIDs.find(node) != setVertexIDs.end()) {
                ptNodeDf->incrementPatternCount(node, Pattern::LCCycle,
                                                binCounts(gConfig->bins[Pattern::LCCycle], cycle.size()));
            }
        }
    }
}
}

DynamicCycleFinder::DynamicCycleFinder(Graph* _g, runSettings& conf)
    : enumerator(_g->getCompressedGraph())
    , g(_g)
    , config(&conf)
{
}

DynamicCycleFinder::~DynamicCycleFinder() { }

double DynamicCycleFinder::computeTempCyclesBatchAPI(vector<GraphElemID> edgeIDs, PerThreadDataFrame& nodeDF, int nthr)
{
    // Forward graphs to callbacks
    ptNodeDf = &nodeDF;
    gConfig  = this->config;

    enumerator.setCycleBundleFoundCallback(tempCycleCallbackBatch);

    int algo = 0; // Fine-grained Johnson

    // Run cycle enumeration
    auto cyc_start = chrono::high_resolution_clock::now();

    vector<CompressedEdge> batchEdges(edgeIDs.size());

    setEdgeIDs.clear();
    setVertexIDs.clear();
    for (unsigned int i = 0; i < edgeIDs.size(); i++) {
        GraphElemID eid    = edgeIDs[i];
        int         eindex = g->edgeIdMap[eid];
        if (gConfig->vertexFeatures == true && gConfig->batchedFeatures == true) {
            setVertexIDs.insert(g->getEdge(eindex)->getSourceVertexIndex());
            setVertexIDs.insert(g->getEdge(eindex)->getTargetVertexIndex());
        }
        if (gConfig->vertexFeatures == false && gConfig->batchedFeatures == true) {
            setEdgeIDs.insert(eid);
        }
        batchEdges[i].fromV  = g->getEdge(eindex)->getSourceVertexIndex();
        batchEdges[i].toV    = g->getEdge(eindex)->getTargetVertexIndex();
        batchEdges[i].tstamp = g->getEdge(eindex)->getTStamp();
        batchEdges[i].eid    = eid;
    }

    enumerator.runCycleEnumerationBatch(batchEdges, gConfig->timewindows[Pattern::TempCycle], -1, nthr, algo);

    auto   cyc_end   = chrono::high_resolution_clock::now();
    double cyc_total = chrono::duration_cast<chrono::milliseconds>(cyc_end - cyc_start).count() / 1000.0;

    enumerator.setCycleBundleFoundCallback(EMPTY_CYCLE_CALLBACK);

    return cyc_total;
}

double DynamicCycleFinder::computeLCCyclesBatchAPI(vector<GraphElemID> edgeIDs, PerThreadDataFrame& nodeDF, int nthr)
{
    // Forward graphs to callbacks
    ptNodeDf = &nodeDF;
    gConfig  = this->config;

    enumerator.setCycleBundleFoundCallback(lcCycleCallbackBatch);

    int algo = 2; // Fine-grained parallel length-constrained cycle enumeration

    // Run cycle enumeration
    auto cyc_start = chrono::high_resolution_clock::now();

    vector<CompressedEdge> batchEdges(edgeIDs.size());

    setEdgeIDs.clear();
    setVertexIDs.clear();
    for (unsigned int i = 0; i < edgeIDs.size(); i++) {
        GraphElemID eid    = edgeIDs[i];
        int         eindex = g->edgeIdMap[eid];
        if (config->vertexFeatures == true && gConfig->batchedFeatures == true) {
            setVertexIDs.insert(g->getEdge(eindex)->getSourceVertexIndex());
            setVertexIDs.insert(g->getEdge(eindex)->getTargetVertexIndex());
        }
        if (gConfig->vertexFeatures == false && gConfig->batchedFeatures == true) {
            setEdgeIDs.insert(eid);
        }

        batchEdges[i].fromV  = g->getEdge(eindex)->getSourceVertexIndex();
        batchEdges[i].toV    = g->getEdge(eindex)->getTargetVertexIndex();
        batchEdges[i].tstamp = g->getEdge(eindex)->getTStamp();
        batchEdges[i].eid    = eid;
    }

    enumerator.runCycleEnumerationBatch(batchEdges, gConfig->timewindows[Pattern::LCCycle],
                                        gConfig->maxlengths[Pattern::LCCycle], nthr, algo);

    auto   cyc_end   = chrono::high_resolution_clock::now();
    double cyc_total = chrono::duration_cast<chrono::milliseconds>(cyc_end - cyc_start).count() / 1000.0;

    enumerator.setCycleBundleFoundCallback(EMPTY_CYCLE_CALLBACK);

    return cyc_total;
}
