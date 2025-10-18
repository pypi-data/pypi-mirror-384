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
#include <cstring>
#include <ctime>
#include <chrono>

#include "compressedGraph.h"

using namespace std;

#if USE_DYNAMIC_GRAPH == True

/******************* Compressed Dynamic Graph *******************/

#else

/******************* Compressed Sparse Graph *******************/

namespace {
bool sortfirst(const pair<Timestamp, int>& a, const pair<Timestamp, int>& b) { return (a.first < b.first); }
}

void CompressedGraph::compressEdgeList(EdgeList& edgeList)
{
    tstampNo = edgeList.size();

    typedef vector<pair<Timestamp, GraphElemID>> edgeInfoSet;

    int                                       maxNode = 0;
    unordered_map<int, map<int, edgeInfoSet>> adjacencyList;
    unordered_map<int, map<int, edgeInfoSet>> inEdgeList;

    for (int i = 0; i < edgeList.size(); i++) {
        Edge*       edge   = edgeList[i];
        int         fromV  = edge->getSource()->getIndex();
        int         toV    = edge->getTarget()->getIndex();
        Timestamp   tst    = edge->getTStamp();
        GraphElemID edgeId = edge->getID();

        adjacencyList[fromV][toV].push_back({ tst, edgeId });
        inEdgeList[toV][fromV].push_back({ tst, edgeId });
        maxNode = max(maxNode, max(fromV, toV));
    }

    vertexNo = maxNode + 1;

    for (auto pair : adjacencyList)
        edgeNo += pair.second.size();

    outDegrees      = new int[vertexNo];
    offsArray       = new int[vertexNo + 2];
    edgeArray       = new ColElem[edgeNo + 1];
    int currentOffs = 0;
    offsArray[0]    = 0;
    for (int i = 0; i < vertexNo; i++) {
        outDegrees[i] = 0;
        if (adjacencyList.find(i) != adjacencyList.end()) {
            for (auto& pair : adjacencyList[i]) {
                sort(pair.second.begin(), pair.second.end(), sortfirst);
                edgeArray[currentOffs].vertex = pair.first;
                outDegrees[i] += pair.second.size();
                for (auto epair : pair.second) {
                    edgeArray[currentOffs].tstamps.push_back(epair.first);
                    edgeArray[currentOffs].eids.push_back(epair.second);
                    // Hash the columns with raw features
                    Edge*         edge = edgeList[epair.second];
                    FeatureVector tmp;
                    tmp.reserve(compressedColumnIDs.size());
                    for (auto colid : compressedColumnIDs) {
                        tmp.push_back(edge->getRawFeat(colid));
                    }
                    edgeArray[currentOffs].feats.push_back(move(tmp));
                }
                currentOffs++;
            }
        }
        offsArray[i + 1] = currentOffs;
    }

    inDegrees      = new int[vertexNo];
    inOffsArray    = new int[vertexNo + 1];
    inEdgeArray    = new ColElem[edgeNo];
    currentOffs    = 0;
    inOffsArray[0] = 0;
    for (int i = 0; i < vertexNo; i++) {
        inDegrees[i] = 0;
        if (inEdgeList.find(i) != inEdgeList.end()) {
            for (auto& pair : inEdgeList[i]) {
                sort(pair.second.begin(), pair.second.end(), sortfirst);
                inEdgeArray[currentOffs].vertex = pair.first;
                inDegrees[i] += pair.second.size();
                for (auto epair : pair.second) {
                    inEdgeArray[currentOffs].tstamps.push_back(epair.first);
                    inEdgeArray[currentOffs].eids.push_back(epair.second);
                    // Hash the columns with raw features
                    Edge*         edge = edgeList[epair.second];
                    FeatureVector tmp;
                    tmp.reserve(compressedColumnIDs.size());
                    for (auto colid : compressedColumnIDs) {
                        tmp.push_back(edge->getRawFeat(colid));
                    }
                    inEdgeArray[currentOffs].feats.push_back(move(tmp));
                }
                currentOffs++;
            }
        }
        inOffsArray[i + 1] = currentOffs;
    }
}

void CompressedGraph::compressEdgeList(vector<CompressedEdge>& edgeList)
{
    tstampNo = edgeList.size();

    typedef vector<pair<Timestamp, int>> edgeInfoSet;

    int                                       maxNode = 0;
    unordered_map<int, map<int, edgeInfoSet>> adjacencyList;
    unordered_map<int, map<int, edgeInfoSet>> inEdgeList;

    for (int i = 0; i < edgeList.size(); i++) {
        CompressedEdge* edge   = &(edgeList[i]);
        int             fromV  = edge->fromV;
        int             toV    = edge->toV;
        Timestamp       tst    = edge->tstamp;
        int             edgeId = edge->eid;

        adjacencyList[fromV][toV].push_back({ tst, edgeId });
        inEdgeList[toV][fromV].push_back({ tst, edgeId });
        maxNode = max(maxNode, max(fromV, toV));
    }

    vertexNo = maxNode + 1;

    for (auto pair : adjacencyList)
        edgeNo += pair.second.size();

    outDegrees      = new int[vertexNo];
    offsArray       = new int[vertexNo + 2];
    edgeArray       = new ColElem[edgeNo + 1];
    int currentOffs = 0;
    offsArray[0]    = 0;
    for (int i = 0; i < vertexNo; i++) {
        outDegrees[i] = 0;
        if (adjacencyList.find(i) != adjacencyList.end()) {
            for (auto& pair : adjacencyList[i]) {
                sort(pair.second.begin(), pair.second.end(), sortfirst);
                edgeArray[currentOffs].vertex = pair.first;
                outDegrees[i] += pair.second.size();
                for (auto epair : pair.second) {
                    edgeArray[currentOffs].tstamps.push_back(epair.first);
                    edgeArray[currentOffs].eids.push_back(epair.second);
                }
                currentOffs++;
            }
        }
        offsArray[i + 1] = currentOffs;
    }

    inDegrees      = new int[vertexNo];
    inOffsArray    = new int[vertexNo + 1];
    inEdgeArray    = new ColElem[edgeNo];
    currentOffs    = 0;
    inOffsArray[0] = 0;
    for (int i = 0; i < vertexNo; i++) {
        inDegrees[i] = 0;
        if (inEdgeList.find(i) != inEdgeList.end()) {
            for (auto& pair : inEdgeList[i]) {
                sort(pair.second.begin(), pair.second.end(), sortfirst);
                inEdgeArray[currentOffs].vertex = pair.first;
                inDegrees[i] += pair.second.size();
                for (auto epair : pair.second) {
                    inEdgeArray[currentOffs].tstamps.push_back(epair.first);
                    inEdgeArray[currentOffs].eids.push_back(epair.second);
                }
                currentOffs++;
            }
        }
        inOffsArray[i + 1] = currentOffs;
    }
}

#endif
