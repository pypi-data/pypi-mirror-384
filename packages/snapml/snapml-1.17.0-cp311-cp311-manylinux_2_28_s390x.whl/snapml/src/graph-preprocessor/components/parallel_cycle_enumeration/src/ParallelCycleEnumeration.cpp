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

#include "ParallelCycleEnumeration.h"

#include <iostream>
#include <fstream>
#include <unordered_map>
#include <map>
#include <string>

#include <cstdint>
#include <limits.h>
#include <vector>
#include <chrono>

#include "CycleUtils.h"
#include "CycleEnumeration.h"

#ifdef USE_EXT_GRAPH
#include "compressedGraph.h"
#endif

using namespace std;

namespace ParCycEnum {

namespace {
    CycleBundleCallback globalCycleBundleCallback = EMPTY_CYCLE_CALLBACK;
}

// Global variables
Timestamp timeWindow          = 3600;
bool      useCUnion           = true;
bool      disablePathBundling = false;
// ConcurrentCounter          vertexVisits;
// TConcurrentCounter<double> preprocTimer;

bool invertSearch = false;
int  maxTempCycle = -1;

/// Function called every time a cycle is detected
void processCycleBundle(vector<int>& cycle, vector<vector<GraphElemID>>& edgeIDs)
{
    globalCycleBundleCallback(cycle, edgeIDs);
}

/**
 * Constructor.
 */
ParallelCycleEnumerator::ParallelCycleEnumerator(std::string graphpath)
{
    gg = new Graph;

    gg->readTemporalGraph(graphpath);
}

#ifdef USE_EXT_GRAPH
ParallelCycleEnumerator::ParallelCycleEnumerator(CompressedGraph* cgraph) { gg = new ExternalGraph(cgraph); }
#endif

/**
 * Destructor.
 */
ParallelCycleEnumerator::~ParallelCycleEnumerator()
{
    if (gg) {
        delete gg;
        gg = NULL;
    }
}

void ParallelCycleEnumerator::runCycleEnumeration(int tw, int lenc, int nthr, int algo)
{

    globalCycleBundleCallback = this->cycleBundleCallback;

    timeWindow = tw;
    useCUnion  = true;

    switch (algo) {
    case 0:
        allCyclesTempJohnsonFineGrained(gg, cycleHistogram, nthr);
        break;
    case 1:
        allCyclesTempJohnsonCoarseGrained(gg, cycleHistogram, nthr);
        break;
    case 2:
        allLenConstrainedCyclesFineGrained(gg, lenc, cycleHistogram, nthr);
        break;
    case 3:
        allLenConstrainedCyclesCoarseGrained(gg, lenc, cycleHistogram, nthr);
        break;
    }

    globalCycleBundleCallback = EMPTY_CYCLE_CALLBACK;
}

void ParallelCycleEnumerator::setCycleBundleFoundCallback(CycleBundleCallback callback)
{
    cycleBundleCallback = callback;
}

void ParallelCycleEnumerator::runCycleEnumerationBatch(vector<CompressedEdge>& batch, int tw, int lenc, int nthr,
                                                       int algo)
{
    if (!gg)
        return;

    timeWindow = tw;

    useCUnion = true;

    globalCycleBundleCallback = this->cycleBundleCallback;

    ConcurrentContainer<CycleHist> pt_cycleHist;
    pt_cycleHist.setNumThreads(nthr);

    maxTempCycle = lenc;

    switch (algo) {
    case 0:
        allCyclesTempJohnsonFineGrainedBatch(gg, batch, pt_cycleHist, nthr);
        break;
    case 1:
        allCyclesTempJohnsonCoarseGrainedBatch(gg, batch, pt_cycleHist, nthr);
        break;
    case 2:
        allLenConstrainedCyclesFineGrainedBatch(gg, lenc, batch, pt_cycleHist, nthr);
        break;
    case 3:
        allLenConstrainedCyclesCoarseGrainedBatch(gg, lenc, batch, pt_cycleHist, nthr);
        break;
    default:
        break;
    }

    combineCycleHistogram(pt_cycleHist, cycleHistogram);

    globalCycleBundleCallback = EMPTY_CYCLE_CALLBACK;
}

void ParallelCycleEnumerator::printHist()
{
    if (cycleHistogram.size() != 0) {
        cout << "# cycle size, number of cycles\n";
        unsigned long totCycles = 0;
        for (auto hist : cycleHistogram) {
            cout << hist.first << ", " << hist.second << "\n";
            totCycles += hist.second;
        }
        cout << "Total, " << totCycles << endl;
    }
}

}