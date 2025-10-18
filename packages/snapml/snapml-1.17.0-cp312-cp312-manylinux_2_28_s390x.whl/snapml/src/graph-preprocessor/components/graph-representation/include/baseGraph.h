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

#ifndef BASE_GRAPH_H
#define BASE_GRAPH_H

#include <sstream>
#include <fstream>
#include <vector>
#include <deque>
#include <queue>
#include <iostream>
#include <cstdint>
#include <unordered_map>

typedef int     Timestamp;
typedef int64_t GraphElemID;

using namespace std;

/************************* Base Graph **************************/

class BaseGraph;

class Node {
public:
    /**
     * Default constructor
     */
    Node() {};
    Node(int _ind, GraphElemID _id)
        : index(_ind)
        , id(_id)
    {
    }

    /**
     * Copy constructor
     */
    Node(const Node&);

    /**
     * Move constructor
     */
    Node(Node&&) noexcept;

    /**
     * Copy assignment operator
     */
    Node& operator=(const Node&);

    /**
     * Move assignment operator
     */
    Node& operator=(Node&&);

    /**
     * Destructor
     */
    ~Node() noexcept = default;

    // getter & setter methods
    int  getIndex() { return index; }
    void setIndex(int ind) { index = ind; }

    void        setID(GraphElemID i) { id = i; }
    GraphElemID getID() { return id; }

    // TODO: support raw vertex features

    friend class BaseGraph;

protected:
    int         index = -1;
    GraphElemID id    = -1;
};

typedef deque<Node>    VertexList;
typedef vector<double> FeatureVector;

class Edge {
public:
    /**
     * Default constructor
     */
    Edge() {};

    /**
     * Copy constructor
     */
    Edge(const Edge&);

    /**
     * Move constructor
     */
    Edge(Edge&&) noexcept;

    /**
     * Copy assignment operator
     */
    Edge& operator=(const Edge&);

    /**
     * Move assignment operator
     */
    Edge& operator=(Edge&&);

    /**
     * Destructor
     */
    ~Edge() noexcept = default;

    /// Interface methods

    int         getIndex() { return index; }
    GraphElemID getID() { return id; }
    int         getSourceVertexIndex() { return sourceNode->getIndex(); }
    GraphElemID getSourceVertexID() { return sourceNode->getID(); }
    int         getTargetVertexIndex() { return targetNode->getIndex(); }
    GraphElemID getTargetVertexID() { return targetNode->getID(); }
    Timestamp   getTStamp() { return tstamp; }

    /// Other methods

    int getLabel() { return isLaundering; };

    // Replacement for the class FeatureVector
    void setRawFeat(unsigned int key, double val)
    {
        if (featureVector.size() >= key)
            featureVector.resize(key + 1);
        featureVector[key] = val;
    };

    double getRawFeat(unsigned int key)
    {
        if (featureVector.size() <= key)
            throw std::out_of_range("Raw feature column does not exist.");
        return featureVector[key];
    };

    unsigned int getNumRawFeats() { return featureVector.size(); }

    FeatureVector& getFeatureVector() { return featureVector; }

    void setFeatureVector(FeatureVector& featVec) { featureVector = featVec; }

    Node* getSource() { return sourceNode; };
    Node* getTarget() { return targetNode; };

    friend class BaseGraph;
    friend class DynamicGraph;

protected:
    int           index        = -1;
    GraphElemID   id           = -1;
    Timestamp     tstamp       = -1;
    int           isLaundering = 0;
    Node*         sourceNode   = nullptr;
    Node*         targetNode   = nullptr;
    FeatureVector featureVector;
};

typedef deque<Edge*> EdgeList;

class BaseGraph {
public:
    BaseGraph() {};
    virtual ~BaseGraph();

    // Returns -1 if unsuccessful
    int readLabels(string path);

    int getTotalTime() { return totalTime; }

    unsigned int getVertexNo() { return nodeList.size(); };
    unsigned int getEdgeNo() { return edgeList.size(); };
    unsigned int getNumFeatures() { return (getEdgeNo() == 0) ? 0 : (getOldestEdge()->getNumRawFeats() + 4); };

    Edge* getEdge(unsigned int eindex);
    Node* getVertex(unsigned int vid);
    Edge* getNextEdge(Edge* e);

    unordered_map<GraphElemID, int> edgeIdMap;
    unordered_map<GraphElemID, int> vertexIdMap;
    void                            printEdgeList(string path);

    // For testing purposes
    bool isEdgeListSorted();
    int  getNoOutOfOrderEdges();

    vector<string> getRawFeatNames() { return rawEdgeFeatureNames; };

protected:
    int readEdgeList(string path);
    int readCSVEdgeList(string path);
    int loadEdgeList(double* features, uint64_t num_edges, uint64_t num_features);

    void reSortEdges();

    // TODO: some of these methods are specific to dynamic graphs
    Edge*     insertEdge(GraphElemID edgeID, Timestamp tstamp, GraphElemID sourceID, GraphElemID targetID,
                         FeatureVector& featureVec);
    void      popEdge();
    Timestamp getMaxTimestamp() { return maxTs; }
    Edge*     getOldestEdge()
    {
        if (getEdgeNo() == 0)
            return NULL;
        return edgeList.front();
    }

    Timestamp  totalTime;
    EdgeList   edgeList;
    VertexList nodeList;

    vector<string> rawEdgeFeatureNames;

    Timestamp maxTs        = 0;
    Timestamp maxRemovedTs = 0;

    int lastEdgeIndex = 0;

    // Number of out-of-order edges, i.e., edges that have smaller timestam than the max timestamp
    unsigned int oooEdges = 0;
};
#endif