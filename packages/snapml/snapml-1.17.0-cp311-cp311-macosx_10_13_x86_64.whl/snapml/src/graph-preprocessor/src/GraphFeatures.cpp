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

#include "GraphFeatures.h"

#include <cstring>
#include <exception>

#include "featureEngineering.h"
#include "utils.h"
#include "graph.h"

namespace GraphFeatures {

#define SUCCESSFUL_OP   (0)
#define UNSUCCESSFUL_OP (-1)

namespace {

}

int GraphFeaturePreprocessor::loadConfigFile(string path)
{
    config->clear();
    parseConfigFile(path, *config);

    if (g)
        delete g;

#if USE_DYNAMIC_GRAPH == True
    g = new DynamicGraph;
#else
    g = new StaticGraph;
#endif

#ifndef USE_TBB
    omp_set_num_threads(config->numthreads);
#else
    task_scheduler_init init(config->numthreads);
#endif

#if USE_DYNAMIC_GRAPH == True
    if (g != nullptr) {
        if (DynamicGraph* dg = dynamic_cast<DynamicGraph*>(g)) {
            initDynamicGraph(dg, *config);
        }
    }
#endif

    if (cycleFinder) {
        delete cycleFinder;
        cycleFinder = NULL;
    }
    cycleFinder = new DynamicCycleFinder(g, *config);

    return SUCCESSFUL_OP;
}

int GraphFeaturePreprocessor::setParams(unordered_map<string, int>         intParams,
                                        unordered_map<string, vector<int>> vecParams)
{
    config->clear();

    if (g)
        delete g;

#if USE_DYNAMIC_GRAPH == True
    g = new DynamicGraph;
#else
    g = new StaticGraph;
#endif

    int ret = loadConfigParams(*config, intParams, vecParams);
    if (ret < 0)
        return UNSUCCESSFUL_OP;

#ifndef USE_TBB
    omp_set_num_threads(config->numthreads);
#else
    task_scheduler_init init(config->numthreads);
#endif

#if USE_DYNAMIC_GRAPH == True
    DynamicGraph* dg = dynamic_cast<DynamicGraph*>(g);
    initDynamicGraph(dg, *config);
#endif

    if (cycleFinder) {
        delete cycleFinder;
        cycleFinder = NULL;
    }
    cycleFinder = new DynamicCycleFinder(g, *config);

    return SUCCESSFUL_OP;
}

int GraphFeaturePreprocessor::enrichFeatureVectors(uint64_t num_samples, double* features_in, uint64_t num_features_in,
                                                   double* features_out, uint64_t num_features_out)
{
#ifndef USE_TBB
    omp_set_num_threads(config->numthreads);
#else
    task_scheduler_init init(config->numthreads);
#endif
    if (!features_in || !features_out)
        throw std::invalid_argument("Invalid array dimensions.");

    if (!g)
        throw std::runtime_error("Graph object does not exist.");

    if (num_features_out - num_features_in != getNumEngineeredFeatures())
        throw std::invalid_argument("Not enough output features allocated.");

    preprocessingStarted = true;

    int nthr = config->numthreads;

    PerThreadDataFrame  ptNodeDF(nthr);
    ShallowFeatureTable ftable;

    set<GraphElemID> localEdgeSet;

#if USE_DYNAMIC_GRAPH == True
    // TODO: find a way to avoid using dynamic_cast
    DynamicGraph* dg = dynamic_cast<DynamicGraph*>(g);

    // Add new edges to the dynamic graph
    multimap<Timestamp, int> sortedEdges;
    for (uint64_t i = 0; i < num_samples; i++) {
        double*     thisFeaturesIn = &(features_in[i * num_features_in]);
        GraphElemID edgeID         = thisFeaturesIn[0];
        Timestamp   tstamp         = thisFeaturesIn[3];

        if (localEdgeSet.find(edgeID) == localEdgeSet.end()) {
            localEdgeSet.insert(edgeID);
            sortedEdges.insert({ tstamp, i });
        }
    }

    for (auto& pair : sortedEdges) {
        int         i              = pair.second;
        double*     thisFeaturesIn = &(features_in[i * num_features_in]);
        GraphElemID edgeID         = thisFeaturesIn[0];
        GraphElemID sourceID       = thisFeaturesIn[1];
        GraphElemID targetID       = thisFeaturesIn[2];
        Timestamp   tstamp         = thisFeaturesIn[3];

        FeatureVector featVector(num_features_in - 4);
        for (uint64_t k = 4; k < num_features_in; k++) {
            featVector[k - 4] = thisFeaturesIn[k];
        }

        dg->addTempEdge(edgeID, tstamp, sourceID, targetID, featVector);
    }
#endif

    set<int> localVertexSet;

    // Update the raw features
    for (uint64_t ind = 0; ind < num_samples; ind++) {
        double* thisFeaturesIn  = &(features_in[ind * num_features_in]);
        double* thisFeaturesOut = &(features_out[ind * num_features_out]);

        // Update the raw features in features_out
        GraphElemID edgeID = thisFeaturesIn[0];

        if (g->edgeIdMap.find(edgeID) == g->edgeIdMap.end()) {
            // This should not happen if the edge was added correctly
            throw std::runtime_error("No edge with the given ID = " + to_string(edgeID) + " exists.");
            return UNSUCCESSFUL_OP;
        }

        if (config->useShallowFeatures) {
            GraphElemID sourceID = thisFeaturesIn[1];
            GraphElemID targetID = thisFeaturesIn[2];
            int         fromV    = g->vertexIdMap[sourceID];
            int         toV      = g->vertexIdMap[targetID];
            localVertexSet.insert(fromV);
            localVertexSet.insert(toV);
        }

        memcpy(&(thisFeaturesOut[0]), &(thisFeaturesIn[0]), sizeof(double) * (num_features_in));

        // Set the out features to 0
        memset(&(thisFeaturesOut[num_features_in]), 0, sizeof(double) * (num_features_out - num_features_in));
    }

    vector<GraphElemID> localEdgeIDs;
    localEdgeIDs.reserve(localEdgeSet.size());
    for (auto el : localEdgeSet)
        localEdgeIDs.push_back(el);

    vector<int> localVertexIDs;
    if (config->useShallowFeatures && (0 != localVertexSet.size())) {
        localVertexIDs.reserve(localVertexSet.size());
        for (auto el : localVertexSet)
            localVertexIDs.push_back(el);
    }

    if (config->patternExists(Pattern::FanIn) || config->patternExists(Pattern::FanOut)
        || config->patternExists(Pattern::DegIn) || config->patternExists(Pattern::DegOut)) {
        computeFanDegBatchAPI(g, ptNodeDF, *config, localEdgeIDs);
    }
    if (config->patternExists(Pattern::ScatGat)) {
        computeScatterGatherBatchAPI(g, ptNodeDF, *config, localEdgeIDs);
    }
    if (config->patternExists(Pattern::TempCycle)) {
        cycleFinder->computeTempCyclesBatchAPI(localEdgeIDs, ptNodeDF, nthr);
    }
    if (config->patternExists(Pattern::LCCycle)) {
        cycleFinder->computeLCCyclesBatchAPI(localEdgeIDs, ptNodeDF, nthr);
    }
    if (config->useShallowFeatures) {
#if USE_DYNAMIC_GRAPH == True
        if (!config->nonincStat)
            computeIncrementalStatisticsFeatures(g, ftable, *config, localVertexIDs);
        else
            computeVertexStatisticsFeatures(g, ftable, *config, localVertexIDs);
#else
        computeVertexStatisticsFeatures(g, ftable, *config, localVertexIDs);
#endif
    }

    DataFrame tempNodeDF;
    ptNodeDF.combineAPI(tempNodeDF, localEdgeIDs);

    unordered_map<int, int> vidToRowMap;
    for (uint64_t i = 0; i < ftable.size(); i++) {
        int vid          = ftable[i].first;
        vidToRowMap[vid] = i;
    }

    unordered_map<GraphElemID, int> eidToRowMap;
    for (uint64_t i = 0; i < tempNodeDF.size(); i++) {
        GraphElemID eid  = tempNodeDF[i].first;
        eidToRowMap[eid] = i;
    }

    int startIdx = num_features_in;
    for (uint64_t i = 0; i < static_cast<int>(Pattern::SIZE); i++) {
        Pattern pat = static_cast<Pattern>(i);
        if (config->patternExists(pat)) {
            startIdx += config->bins[pat].size();
        }
    }

    // Output engineered features
    for (uint64_t ind = 0; ind < num_samples; ind++) {
        double* thisFeaturesOut = &(features_out[ind * num_features_out]);

        // Update the raw features in features_out
        GraphElemID edgeID = thisFeaturesOut[0];

        if (eidToRowMap.find(edgeID) != eidToRowMap.end()) {
            int   erow  = eidToRowMap[edgeID];
            auto& feats = tempNodeDF[erow].second;

            int j = num_features_in;

            for (int i = 0; i < static_cast<int>(Pattern::SIZE); i++) {
                Pattern pat = static_cast<Pattern>(i);
                if (config->patternExists(pat)) {
                    for (auto feat : feats.patternBins[pat])
                        thisFeaturesOut[j + feat.first] = feat.second;
                    j += config->bins[pat].size();
                }
            }
        }

        int j = startIdx;

        if (config->useShallowFeatures) {
            int numVertStatFeats = getNumStatFeatures(*config);

            GraphElemID sourceID = thisFeaturesOut[1];
            GraphElemID targetID = thisFeaturesOut[2];
            int         fromV    = g->vertexIdMap[sourceID];
            int         toV      = g->vertexIdMap[targetID];

            for (int rep = 0; rep < 2; rep++) {
                int vid = (rep == 0) ? fromV : toV;

                int vrow = vidToRowMap[vid];

                auto& tmptable = ftable[vrow];
                for (int i = 0; i < numVertStatFeats; i++) {
                    auto val               = tmptable.second[i];
                    thisFeaturesOut[j + i] = val;
                }

                j += numVertStatFeats;
            }
        }
    }

#if USE_DYNAMIC_GRAPH == True
    // Removing the old edges
    dg->removeOldEdges();
#endif

    return SUCCESSFUL_OP;
}

int GraphFeaturePreprocessor::updateGraph(double* features_in, uint64_t num_samples, uint64_t num_features)
{
    if (!features_in)
        throw std::invalid_argument("Invalid array dimensions.");

    if (!g)
        throw std::runtime_error("Graph object does not exist.");

    preprocessingStarted = true;

    // This function does not make sense for static graph, so nothing is done.
#if USE_DYNAMIC_GRAPH == True
    DynamicGraph* dg = dynamic_cast<DynamicGraph*>(g);

    // Add new edges to the dynamic graph
    multimap<Timestamp, int> sortedEdges;
    for (uint64_t i = 0; i < num_samples; i++) {
        double*   thisFeaturesIn = &(features_in[i * num_features]);
        Timestamp tstamp         = thisFeaturesIn[3];

        sortedEdges.insert({ tstamp, i });
    }

    for (auto& pair : sortedEdges) {
        int         i              = pair.second;
        double*     thisFeaturesIn = &(features_in[i * num_features]);
        GraphElemID edgeID         = thisFeaturesIn[0];
        GraphElemID sourceID       = thisFeaturesIn[1];
        GraphElemID targetID       = thisFeaturesIn[2];
        Timestamp   tstamp         = thisFeaturesIn[3];

        FeatureVector featVector(num_features - 4);
        for (uint64_t k = 4; k < num_features; k++) {
            featVector[k - 4] = thisFeaturesIn[k];
        }

        dg->addTempEdge(edgeID, tstamp, sourceID, targetID, featVector);
    }

    // Removing the old edges
    dg->removeOldEdges();
#endif

    return SUCCESSFUL_OP;
}

uint64_t GraphFeaturePreprocessor::getNumEngineeredFeatures()
{
    uint64_t result = 0;

    for (uint64_t i = 0; i < static_cast<int>(Pattern::SIZE); i++) {
        Pattern pat = static_cast<Pattern>(i);
        if (config->patternExists(pat)) {
            result += config->bins[pat].size();
        }
    }

    // 2 = source vertex and destination vertex
    if (config->useShallowFeatures) {
        result += (2 * getNumStatFeatures(*config));
    }

    return result;
}

pair<uint64_t, uint64_t> GraphFeaturePreprocessor::getOutputArrayDimensions()
{
    if (g->getEdgeNo() == 0)
        return make_pair(0, 0);
    return make_pair(g->getEdgeNo(), g->getNumFeatures());
}

int GraphFeaturePreprocessor::saveGraph(string path)
{
    g->saveGraph(path);
    return SUCCESSFUL_OP;
}

// TODO: exceptions to catch potential seg faults
int GraphFeaturePreprocessor::exportGraph(double* features, uint64_t num_samples, uint64_t num_features)
{
    if (!features)
        throw std::invalid_argument("Invalid array dimensions.");
    if (!g)
        throw std::runtime_error("Graph object does not exist.");

    int out = g->exportGraph(features, num_samples, num_features);
    if (out < 0)
        return UNSUCCESSFUL_OP;

    return SUCCESSFUL_OP;
}

int GraphFeaturePreprocessor::loadGraph(string path)
{
    if (g)
        delete g;

#if USE_DYNAMIC_GRAPH == True
    DynamicGraph* dg = new DynamicGraph;
    if (nullptr == dg) {
        return UNSUCCESSFUL_OP;
    }
    initDynamicGraph(dg, *config);
    int status = dg->readDynamicGraph(path);

    dg->removeOldEdges();
    g = dg;
#else
    g          = new StaticGraph;
    int status = g->readGraph(path, config->simulator);
#endif

    if (status < 0)
        return UNSUCCESSFUL_OP;

    if (cycleFinder) {
        delete cycleFinder;
        cycleFinder = NULL;
    }
    cycleFinder = new DynamicCycleFinder(g, *config);
    return SUCCESSFUL_OP;
}

int GraphFeaturePreprocessor::loadGraph(double* features, uint64_t num_samples, uint64_t num_features)
{
    if (!features)
        throw std::invalid_argument("Invalid array dimensions.");

    if (g)
        delete g;

    preprocessingStarted = true;

#if USE_DYNAMIC_GRAPH == True
    DynamicGraph* dg = new DynamicGraph;
    if (nullptr == dg)
        return UNSUCCESSFUL_OP;
    initDynamicGraph(dg, *config);
    int status = dg->loadDynamicGraph(features, num_samples, num_features);

    dg->removeOldEdges();
    g = dg;
#else
    g          = new StaticGraph;
    int status = g->loadGraph(features, num_samples, num_features);
#endif

    if (status < 0)
        return UNSUCCESSFUL_OP;

    if (cycleFinder) {
        delete cycleFinder;
        cycleFinder = NULL;
    }
    cycleFinder = new DynamicCycleFinder(g, *config);
    return SUCCESSFUL_OP;
}

GraphFeaturePreprocessor::GraphFeaturePreprocessor()
{
    config = new runSettings;
#if USE_DYNAMIC_GRAPH == True
    g = new DynamicGraph;
#else
    g          = new StaticGraph;
#endif
}

GraphFeaturePreprocessor::~GraphFeaturePreprocessor()
{
    if (g)
        delete g;
    if (config)
        delete config;
    if (cycleFinder)
        delete cycleFinder;
}

void GraphFeaturePreprocessor::enableNonIncVertStatComputation() { config->nonincStat = true; }
void GraphFeaturePreprocessor::disableNonIncVertStatComputation() { config->nonincStat = false; }

}
