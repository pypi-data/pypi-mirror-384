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

#ifndef GRAPH_H
#define GRAPH_H

#include "baseGraph.h"
#include "compressedGraph.h"
#include "vertexStatistics.h"
// #include "utils.h"

const int MIN_EDGE_THRESHOLD = 10000;

using namespace std;

/******************* Graph *******************/

class Graph : public BaseGraph {
public:
    virtual ~Graph() { }
    /// Interface methods
    int  readGraph(string path);
    int  loadGraph(double* features, uint64_t num_edges, uint64_t num_features);
    void saveGraph(string path);
    int  exportGraph(double* features, uint64_t num_edges, uint64_t num_features);

    int numOutEdges(int v) { return csGraph.numOutEdges(v); }
    int numInEdges(int v) { return csGraph.numInEdges(v); }
    int numOutVertices(int v) { return csGraph.numOutVertices(v); }
    int numInVertices(int v) { return csGraph.numInVertices(v); }

    AdjacencyList& getAdjList(int vert, bool out) { return csGraph.getAdjList(vert, out); }

    template <typename TF> void foreachOutEdge(int v, TF&& f);

    template <typename TF> void foreachInEdge(int v, TF&& f);

    template <typename TF> void foreachOutVertex(int v, TF&& f);

    template <typename TF> void foreachInVertex(int v, TF&& f);

    CompressedGraph* getCompressedGraph() { return &csGraph; }

protected:
    Graph()
        : csGraph()
    {
    }
    CompressedGraph csGraph;
};

template <typename TF> inline void Graph::foreachOutEdge(int v, TF&& f) { csGraph.foreachOutEdge(v, f); }

template <typename TF> inline void Graph::foreachInEdge(int v, TF&& f) { csGraph.foreachInEdge(v, f); }

template <typename TF> inline void Graph::foreachOutVertex(int v, TF&& f) { csGraph.foreachOutVertex(v, f); }

template <typename TF> inline void Graph::foreachInVertex(int v, TF&& f) { csGraph.foreachInVertex(v, f); }

// TODO: There is probably a better way to do this
#if USE_DYNAMIC_GRAPH == True

/******************* Dynamic Graph *******************/

class DynamicGraph : public Graph {
public:
    DynamicGraph()
        : Graph()
    {
    }
    virtual ~DynamicGraph() { }

    // TODO: make these two functions virtual
    int readDynamicGraph(string path);
    int loadDynamicGraph(double* features, uint64_t num_edges, uint64_t num_features);

    // Dynamic graph functions
    int       addTempEdge(GraphElemID edgeID, Timestamp tstamp, GraphElemID sourceID, GraphElemID targetID,
                          FeatureVector& rawFeatures);
    void      removeOldEdges();
    void      setTimeWindow(Timestamp tw) { csGraph.setTimeWindow(tw); }
    Timestamp getTimeWindow() { return csGraph.getTimeWindow(); }
    void      setWindowSize(int ws) { csGraph.setWindowSize(ws); }
    int       getWindowSize() { return csGraph.getWindowSize(); }

    void setVertStatTimeWindow(Timestamp tw) { vertStatTimeWindow = tw; }

    VertexStat getStatFeatures(int vertexIndex, int featIndex, bool out)
    {
        if (!collectStatistics)
            return VertexStat();
        return vertStat.getFeatures(vertexIndex, featIndex, out);
    }

    void enableVertexStatistics(bool sum, bool avg, bool var, bool skew, bool kurtosis)
    {
        vertStat.setStatFeatures(sum, avg, var, skew, kurtosis);
        collectStatistics = true;
    }
    void disableVertexStatistics() { collectStatistics = false; }

    // Should be called before "readGraph"
    void collectVertStatForColumns(vector<int> colids) { vertStat.setRawFeatIndices(colids); }

protected:
    bool                        collectStatistics = false;
    IncrementalVertexStatistics vertStat;
    Edge*                       lastExcludedEdge = NULL; // does not exist yet
    Timestamp                   vertStatTimeWindow;
};

/******************* Static Graph *******************/

class StaticGraph : public Graph {
public:
    StaticGraph()
        : Graph()
    {
    }
    virtual ~StaticGraph() { }
};

#endif

#endif
