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

#ifndef _FEATURE_ENGINEERING_H_
#define _FEATURE_ENGINEERING_H_

#include <vector>
#include <set>
#include <map>
#include <string>
#include <iostream>
#include <chrono>
#include <unordered_set>
#include <unordered_map>

#include "cycles.h"
#include "graph.h"
#include "utils.h"
#include "outputDataStructures.h"

void writeHeader(std::ofstream& outputData, runSettings& config, vector<string>& rawEdgeFeatureNames,
                 bool printLabels = true);

void computeFeaturesBatched(Graph* g, runSettings& config, int batchSize, int nthr, bool silent = false);
#if USE_DYNAMIC_GRAPH == True
void computeFeaturesDynamic(vector<vector<double>>& edgeList, runSettings& config, int batchSize, int nthr,
                            bool silent = false);
void computeFeaturesDynamicAPI(vector<vector<double>>& edgeList, string config_file, string graph_file, int batchSize,
                               bool silent, string outPath, unordered_map<GraphElemID, int> labels);
#endif

void computeFeatures(Graph* g, runSettings& config, int nthr, bool silent = false);
void computeShallowFeatures(Graph* g, runSettings& config, int nthr, bool silent = false);
void generateType2Net(Graph* g, runSettings& config, int nthr, bool silent = false);

/// VERTEX STATISTICS
void computeVertexStatisticsFeatures(Graph* g, ShallowFeatureTable& featTable, runSettings& config,
                                     vector<int> vertexIDs = vector<int>(), pair<Timestamp, Timestamp> TW = { -1, -1 });

void computeIncrementalStatisticsFeatures(Graph* g, ShallowFeatureTable& featTable, runSettings& config,
                                          vector<int> vertexIDs);

/// FAN IN/OUT, DEGREE IN/OUT
double computeFanDegBatchAPI(Graph* g, PerThreadDataFrame& nodeDF, runSettings& config, vector<GraphElemID> edgeIDs);

/// SCATTER_GATHER
double computeScatterGatherBatchAPI(Graph* gg, PerThreadDataFrame& nodeDF, runSettings& config,
                                    vector<GraphElemID> edgeIDs);

#endif //_FEATURE_ENGINEERING_H_
