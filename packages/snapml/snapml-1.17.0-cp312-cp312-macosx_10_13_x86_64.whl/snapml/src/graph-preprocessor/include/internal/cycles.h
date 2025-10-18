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

#ifndef CYCLES_H
#define CYCLES_H

#include <vector>
#include <set>
#include <map>

#include "utils.h"
#include "graph.h"
#include "outputDataStructures.h"

#include "ParallelCycleEnumeration.h"

// TEMPORAL CYCLES
void computeTempCycles(Graph* g, PerThreadDataFrame& edgeDF, runSettings& config, int nthr);

// LENGTH-CONSTRAINED CYCLES
void computeLCCycles(Graph* g, PerThreadDataFrame& edgeDF, runSettings& config, int nthr);

class DynamicCycleFinder {
public:
    DynamicCycleFinder(Graph* g, runSettings& config);
    ~DynamicCycleFinder();

    double computeTempCyclesBatchAPI(vector<GraphElemID> edgeIndices, PerThreadDataFrame& nodeDF, int nthr);
    double computeLCCyclesBatchAPI(vector<GraphElemID> edgeIndices, PerThreadDataFrame& nodeDF, int nthr);

private:
    ParCycEnum::ParallelCycleEnumerator enumerator;

    Graph*       g;
    runSettings* config = NULL;
};

#endif
