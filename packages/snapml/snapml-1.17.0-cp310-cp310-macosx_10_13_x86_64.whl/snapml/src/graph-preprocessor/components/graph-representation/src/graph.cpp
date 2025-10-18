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

#include <iostream>
#include <vector>
#include <utility>
#include <set>
#include <map>
#include <chrono>
#include <unordered_set>
#include <unordered_map>
#include <algorithm>
#include <cstring>
#include <ctime>
#include <chrono>

#include "graph.h"

using namespace std;

/******************* Graph *******************/

int Graph::readGraph(string path)
{
    {
        auto start_tstamp = chrono::steady_clock::now();
        int  out          = 0;

        if (path.substr(path.find_last_of(".") + 1) == "csv") {
            readCSVEdgeList(path);
        } else {
            readEdgeList(path);
        }
        if (out < 0)
            return out;
        auto   end_tstamp = chrono::steady_clock::now();
        double total      = chrono::duration_cast<chrono::milliseconds>(end_tstamp - start_tstamp).count() / 1000.0;
        cout << "Transaction list created in: " << total << " s" << endl;
    }

    {
        auto start_tstamp = chrono::steady_clock::now();
        csGraph.compressEdgeList(edgeList);
        auto   end_tstamp = chrono::steady_clock::now();
        double total      = chrono::duration_cast<chrono::milliseconds>(end_tstamp - start_tstamp).count() / 1000.0;
        cout << "Compressed graph representation created in: " << total << " s" << endl;
    }

    return 0;
}

int Graph::loadGraph(double* features, uint64_t num_edges, uint64_t num_features)
{
    int out = loadEdgeList(features, num_edges, num_features);
    if (out < 0)
        return out;

    csGraph.compressEdgeList(edgeList);

    return 0;
}

void Graph::saveGraph(string path)
{
    ofstream outGraph(path);
    outGraph << "# edge ID, timestamp, source vertex ID, target vertex ID" << endl;
    for (auto edge : edgeList) {
        outGraph << edge->getID() << " " << edge->getSource()->getID() << " " << edge->getTarget()->getID() << " "
                 << edge->getTStamp();

        auto& featvec = edge->getFeatureVector();

        for (auto el : featvec) {
            outGraph << " " << el;
        }
        outGraph << endl;
    }
}

int Graph::exportGraph(double* features, uint64_t num_edges, uint64_t num_features)
{

    if (num_edges != getEdgeNo() || getNumFeatures() != num_features)
        throw std::invalid_argument(
            "The dimensions of the array do not match the values required for exporting the graph.");

    for (unsigned int i = 0; i < num_edges; i++) {
        Edge* edge = NULL;

        edge = edgeList[i];

        double* thisFeatureVec = &(features[i * num_features]);

        thisFeatureVec[0] = edge->getID();
        thisFeatureVec[1] = edge->getSource()->getID();
        thisFeatureVec[2] = edge->getTarget()->getID();
        thisFeatureVec[3] = edge->getTStamp();

        int startRawInd = 4;
        for (unsigned int k = startRawInd; k < num_features; k++) {
            thisFeatureVec[k] = edge->getRawFeat(k - startRawInd);
        }
    }

    return 0;
}

int DynamicGraph::readDynamicGraph(string path)
{
    ifstream inFile(path);

    while (true) {
        string line;
        getline(inFile, line);
        if (inFile.eof())
            break;

        if (line[0] == '%' || line[0] == '#')
            continue;

        stringstream ss(line);

        double a, b, c, d;
        ss >> a >> b >> c >> d;

        if (ss.fail()) {
            throw std::invalid_argument("Input file not formatted correctly.");
            return -1;
        }

        GraphElemID edgeID   = a;
        GraphElemID sourceID = b;
        GraphElemID targetID = c;
        Timestamp   tstamp   = d;

        FeatureVector rawFeatures;

        double feat;
        while (ss >> feat) {
            rawFeatures.push_back(feat);
        }

        addTempEdge(edgeID, tstamp, sourceID, targetID, rawFeatures);
    }
    return 0;
}

int DynamicGraph::loadDynamicGraph(double* features, uint64_t num_edges, uint64_t num_features)
{
    for (unsigned int i = 0; i < num_edges; i++) {
        double* thisFeatureVec = &(features[i * num_features]);

        GraphElemID edgeID   = thisFeatureVec[0];
        GraphElemID sourceID = thisFeatureVec[1];
        GraphElemID targetID = thisFeatureVec[2];
        Timestamp   tstamp   = thisFeatureVec[3];

        int startRawInd = 4;

        FeatureVector rawFeatures;
        rawFeatures.reserve(num_features - startRawInd);

        for (unsigned int k = startRawInd; k < num_features; k++) {
            rawFeatures.push_back(thisFeatureVec[k]);
        }

        addTempEdge(edgeID, tstamp, sourceID, targetID, rawFeatures);
    }

    return 0;
}

int DynamicGraph::addTempEdge(GraphElemID edgeID, Timestamp tstamp, GraphElemID sourceID, GraphElemID targetID,
                              FeatureVector& rawFeatures)
{
    Edge* edge = insertEdge(edgeID, tstamp, sourceID, targetID, rawFeatures);

    if (lastExcludedEdge == NULL) {
        lastExcludedEdge = getOldestEdge();
    }

    if (!edge)
        return -1;

    int sourceInd = vertexIdMap[sourceID];
    int targetInd = vertexIdMap[targetID];

    csGraph.addTempEdge(edgeID, tstamp, sourceInd, targetInd);

    if (collectStatistics)
        vertStat.insertEdge(edge);

    return 0;
}

void DynamicGraph::removeOldEdges()
{
    int winsize = csGraph.getWindowSize();
    int thresh  = winsize == -1 ? MIN_EDGE_THRESHOLD : min(winsize / 10, MIN_EDGE_THRESHOLD);

    // Remove old edges
    while (getEdgeNo() != 0) {
        auto& oldestEdge = *(getOldestEdge());

        // Time window constraint and window size constraint

        if ((oldestEdge.getTStamp() >= getMaxTimestamp() - csGraph.getTimeWindow())
            && ((winsize <= -1) || (oldestEdge.getIndex() >= lastEdgeIndex - csGraph.getWindowSize())))
            break;

        if (collectStatistics) {
            if (oldestEdge.getID() == lastExcludedEdge->getID()) {
                vertStat.removeEdge(&oldestEdge);
                lastExcludedEdge = getNextEdge(lastExcludedEdge);
            }
        }

        csGraph.removeEdge(oldestEdge);
        popEdge();
    }

    // If more than 50% of the edges are out-of-order and total number of edges is > const = min(10000,window_size/2)
    if ((oooEdges * 2 > getEdgeNo()) && (getEdgeNo() > thresh)) {
        // Update vertex statistics for all edges that have lower time window but have been omitted
        if (collectStatistics) {
            auto edgeForUpdate = lastExcludedEdge;
            while (edgeForUpdate != NULL) {
                if (edgeForUpdate->getTStamp() < getMaxTimestamp() - vertStatTimeWindow) {
                    vertStat.removeEdge(edgeForUpdate);
                }
                edgeForUpdate = getNextEdge(edgeForUpdate);
            }
        }

        // Reconstruct the graph
        reSortEdges();
    }

    // Update vertex statistics
    if (collectStatistics) {
        while (lastExcludedEdge != NULL) {
            if (lastExcludedEdge->getTStamp() >= getMaxTimestamp() - vertStatTimeWindow)
                break;

            vertStat.removeEdge(lastExcludedEdge);

            lastExcludedEdge = getNextEdge(lastExcludedEdge);
        }
    }
}