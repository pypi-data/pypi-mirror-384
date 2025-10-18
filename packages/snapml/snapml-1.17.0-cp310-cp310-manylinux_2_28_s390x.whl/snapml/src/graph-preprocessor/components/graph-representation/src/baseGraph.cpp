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

#include "baseGraph.h"

using namespace std;

/******************* Node *******************/

Node::Node(const Node& other)
    : index(other.index)
    , id(other.id)
{
}

Node::Node(Node&& other) noexcept
    : index(other.index)
    , id(other.id)
{
}

Node& Node::operator=(const Node& other)
{
    index = other.index;
    id    = other.id;

    return *this;
}

Node& Node::operator=(Node&& other)
{
    index = other.index;
    id    = other.id;

    return *this;
}

/******************* Edge *******************/

Edge::Edge(const Edge& other)
    : index(other.index)
    , id(other.id)
    , tstamp(other.tstamp)
    , isLaundering(other.isLaundering)
    , sourceNode(other.sourceNode)
    , targetNode(other.targetNode)
    , featureVector(other.featureVector)
{
}

Edge::Edge(Edge&& other) noexcept
    : index(other.index)
    , id(other.id)
    , tstamp(other.tstamp)
    , isLaundering(other.isLaundering)
    , sourceNode(other.sourceNode)
    , targetNode(other.targetNode)
    , featureVector(std::move(other.featureVector))
{
}

Edge& Edge::operator=(const Edge& other)
{
    index         = other.index;
    id            = other.id;
    tstamp        = other.tstamp;
    isLaundering  = other.isLaundering;
    sourceNode    = other.sourceNode;
    targetNode    = other.targetNode;
    featureVector = other.featureVector;

    return *this;
}

Edge& Edge::operator=(Edge&& other)
{
    index         = other.index;
    id            = other.id;
    tstamp        = other.tstamp;
    isLaundering  = other.isLaundering;
    sourceNode    = other.sourceNode;
    targetNode    = other.targetNode;
    featureVector = std::move(other.featureVector);

    return *this;
}

/******************* Base Graph *******************/

BaseGraph::~BaseGraph()
{
    for (Edge* e : edgeList) {
        delete e;
    }
}

namespace {
bool compareEdges(Edge* e1, Edge* e2)
{
    if (e1->getTStamp() == e2->getTStamp())
        return e1->getID() < e2->getID();
    return (e1->getTStamp() < e2->getTStamp());
}
}

Edge* BaseGraph::insertEdge(GraphElemID edgeID, Timestamp tstamp, GraphElemID sourceID, GraphElemID targetID,
                            FeatureVector& featureVec)
{
    // Update the vertices
    if (vertexIdMap.find(sourceID) == vertexIdMap.end()) {
        int sourceVertexIndex = nodeList.size();
        vertexIdMap[sourceID] = sourceVertexIndex;
        nodeList.push_back(Node(sourceVertexIndex, sourceID));
    }
    if (vertexIdMap.find(targetID) == vertexIdMap.end()) {
        int targetVertexIndex = nodeList.size();
        vertexIdMap[targetID] = targetVertexIndex;
        nodeList.push_back(Node(targetVertexIndex, targetID));
    }

    // This will not happen because of the check happening outside
    if (edgeIdMap.find(edgeID) != edgeIdMap.end()) {
        return getEdge(edgeIdMap[edgeID]);
    }

    if (edgeList.size() != 0 && (featureVec.size() != edgeList[0]->getNumRawFeats())) {
        throw std::invalid_argument("All edges must have the same number of raw features: "
                                    + to_string(featureVec.size()) + " != " + to_string(edgeList[0]->getNumRawFeats()));
        return NULL;
    }

    int edgeIndex     = lastEdgeIndex++;
    edgeIdMap[edgeID] = edgeIndex;

    int sourceVertexIndex = vertexIdMap[sourceID];
    int targetVertexIndex = vertexIdMap[targetID];

    // Create the edge
    Edge* edge = new Edge();
    if (nullptr != edge) {
        edge->sourceNode = &nodeList[sourceVertexIndex];
        edge->targetNode = &nodeList[targetVertexIndex];

        edge->index  = edgeIdMap[edgeID];
        edge->id     = edgeID;
        edge->tstamp = tstamp;
        edge->setFeatureVector(featureVec);
    } else {
        return nullptr;
    }

    // One out-of-order edge is added
    if (tstamp < maxTs)
        oooEdges++;

    // Update the maximum timestamp
    maxTs = max(maxTs, tstamp);

    edgeList.push_back(edge);

    return edge;
}

void BaseGraph::popEdge()
{
    if (getEdgeNo() == 0)
        throw std::runtime_error("No edges to be removed.");

    Edge* oldestEdge = NULL;

    oldestEdge = edgeList.front();
    edgeList.pop_front();

    edgeIdMap.erase(oldestEdge->getID());

    // One out-of-order edge is removed
    if (maxRemovedTs > oldestEdge->getTStamp())
        oooEdges--;

    maxRemovedTs = max(maxRemovedTs, oldestEdge->getTStamp());

    delete oldestEdge;
}

void BaseGraph::reSortEdges()
{
    sort(edgeList.begin(), edgeList.end(), compareEdges);

    edgeIdMap.clear();
    for (unsigned int eind = 0; eind < edgeList.size(); eind++) {
        GraphElemID edgeID    = edgeList[eind]->id;
        edgeIdMap[edgeID]     = eind;
        edgeList[eind]->index = eind;
    }
    lastEdgeIndex = edgeList.size();
    oooEdges      = 0;
    maxRemovedTs  = edgeList.front()->getTStamp() - 1;
}

int BaseGraph::readEdgeList(string path)
{
    /// First pass - determine number of vertices and edges
    {
        ifstream transFile(path);

        long vertexNo = 0;
        long edgeNo   = 0;
        bool first    = true;
        while (true) {
            string line;
            getline(transFile, line);
            if (transFile.eof())
                break;

            if (line[0] == '%' || line[0] == '#') {
                if (first) {
                    stringstream ss(line);

                    int ind = 0;
                    while (ss.good()) {
                        string substr;
                        getline(ss, substr, ',');

                        // First 4 are not considered raw features (edge ID, timestamp, source ID, target ID)
                        if (ind >= 4) {
                            rawEdgeFeatureNames.push_back(substr);
                        }
                        ind++;
                    }
                }
                continue;
            }

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

            // Hash the edge IDs
            if (edgeIdMap.find(edgeID) != edgeIdMap.end()) {
                throw std::invalid_argument("Edge with the same ID = " + to_string(edgeID) + " already exists.");
                return -1;
            }
            edgeIdMap[edgeID] = edgeNo;

            // Hash the vertex IDs
            if (vertexIdMap.find(sourceID) == vertexIdMap.end())
                vertexIdMap[sourceID] = vertexNo++;
            if (vertexIdMap.find(targetID) == vertexIdMap.end())
                vertexIdMap[targetID] = vertexNo++;

            edgeNo++;

            first = false;
        }

        transFile.close();

        // Create node list
        nodeList.resize(vertexNo);
        for (int i = 0; i < vertexNo; i++) {
            nodeList[i].index = i;
        }
    }

    /// Second pass - populate lists
    {
        // edgeList.reserve(edgeNo);
        ifstream transFile(path);

        Timestamp minTime = std::numeric_limits<Timestamp>::max(), maxTime = 0;
        while (true) {
            string line;
            getline(transFile, line);
            if (transFile.eof())
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

            Edge* edge = new Edge();

            int sourceVertexIndex = vertexIdMap[sourceID];
            int targetVertexIndex = vertexIdMap[targetID];
            if (nullptr != edge) {
                edge->sourceNode = &nodeList[sourceVertexIndex];
                edge->sourceNode->setID(sourceID);

                edge->targetNode = &nodeList[targetVertexIndex];
                edge->targetNode->setID(targetID);

                edge->index  = edgeIdMap[edgeID];
                edge->id     = edgeID;
                edge->tstamp = tstamp;

                minTime = std::min(minTime, edge->tstamp);
                maxTime = std::max(maxTime, edge->tstamp);
            } else {
                return -1;
            }
            double feat;
            int    key = 0;
            while (ss >> feat) {
                edge->setRawFeat(key, feat);
                key++;
            }

            edgeList.push_back(edge);
        }

        sort(edgeList.begin(), edgeList.end(), compareEdges);

        for (unsigned int eind = 0; eind < edgeList.size(); eind++) {
            GraphElemID edgeID    = edgeList[eind]->id;
            edgeIdMap[edgeID]     = eind;
            edgeList[eind]->index = eind;
        }
        lastEdgeIndex = edgeList.size();

        maxTs = maxTime;

        cout << "Num vertices: " << nodeList.size() << " || Num edges: " << edgeList.size() << endl;
        cout << "Total Duration: " << (maxTime - minTime) / (3600 * 24) << " days" << endl;
        totalTime = maxTime;
    }

    return 0;
}

int BaseGraph::readCSVEdgeList(string path)
{
    /// First pass - determine number of vertices and edges
    {
        ifstream transFile(path);

        long vertexNo = 0;
        long edgeNo   = 0;
        bool first    = true;
        while (true) {
            string line;
            getline(transFile, line);
            if (transFile.eof())
                break;

            if (line[0] == '%' || line[0] == '#') {
                continue;
            }

            stringstream ss(line);

            if (first) {
                stringstream ss(line);

                int ind = 0;
                while (ss.good()) {
                    string substr;
                    getline(ss, substr, ',');

                    // First 4 are not considered raw features (edge ID, source ID, target ID, timestamp)
                    if (ind >= 4) {
                        rawEdgeFeatureNames.push_back(substr);
                    }
                    ind++;
                }
                first = false;
            } else {
                double field[4];

                for (int i = 0; i < 4; i++) {
                    string substr;
                    getline(ss, substr, ',');

                    if (!ss.good()) {
                        throw std::invalid_argument("Input file not formatted correctly.");
                        return -1;
                    }

                    field[i] = stod(substr);
                }

                GraphElemID edgeID   = field[0];
                GraphElemID sourceID = field[1];
                GraphElemID targetID = field[2];

                // Hash the edge IDs
                if (edgeIdMap.find(edgeID) != edgeIdMap.end()) {
                    throw std::invalid_argument("Edge with the same ID = " + to_string(edgeID) + " already exists.");
                    return -1;
                }
                edgeIdMap[edgeID] = edgeNo;

                // Hash the vertex IDs
                if (vertexIdMap.find(sourceID) == vertexIdMap.end())
                    vertexIdMap[sourceID] = vertexNo++;
                if (vertexIdMap.find(targetID) == vertexIdMap.end())
                    vertexIdMap[targetID] = vertexNo++;

                edgeNo++;
            }
        }

        transFile.close();

        // Create node list
        nodeList.resize(vertexNo);
        for (int i = 0; i < vertexNo; i++) {
            nodeList[i].index = i;
        }
    }

    /// Second pass - populate lists
    {
        ifstream transFile(path);

        bool      first   = true;
        Timestamp minTime = std::numeric_limits<Timestamp>::max(), maxTime = 0;
        while (true) {
            string line;
            getline(transFile, line);
            if (transFile.eof())
                break;

            if (first) {
                first = false;
                continue;
            }

            stringstream ss(line);

            double field[4];

            for (int i = 0; i < 4; i++) {
                string substr;
                getline(ss, substr, ',');

                if (!ss.good()) {
                    throw std::invalid_argument("Input file not formatted correctly.");
                    return -1;
                }

                field[i] = stod(substr);
            }

            GraphElemID edgeID   = field[0];
            GraphElemID sourceID = field[1];
            GraphElemID targetID = field[2];
            Timestamp   tstamp   = field[3];

            Edge* edge = new Edge();

            int sourceVertexIndex = vertexIdMap[sourceID];
            int targetVertexIndex = vertexIdMap[targetID];
            if (nullptr != edge) {
                edge->sourceNode = &nodeList[sourceVertexIndex];
                edge->sourceNode->setID(sourceID);

                edge->targetNode = &nodeList[targetVertexIndex];
                edge->targetNode->setID(targetID);

                edge->index  = edgeIdMap[edgeID];
                edge->id     = edgeID;
                edge->tstamp = tstamp;

                minTime = std::min(minTime, edge->tstamp);
                maxTime = std::max(maxTime, edge->tstamp);
            } else {
                return -1;
            }
            int key = 0;
            while (ss.good()) {
                string substr;
                getline(ss, substr, ',');
                double feat = stod(substr);
                edge->setRawFeat(key, feat);
                key++;
            }

            edgeList.push_back(edge);
        }

        sort(edgeList.begin(), edgeList.end(), compareEdges);

        for (unsigned int eind = 0; eind < edgeList.size(); eind++) {
            GraphElemID edgeID    = edgeList[eind]->id;
            edgeIdMap[edgeID]     = eind;
            edgeList[eind]->index = eind;
        }
        lastEdgeIndex = edgeList.size();

        maxTs = maxTime;

        cout << "Num vertices: " << nodeList.size() << " || Num edges: " << edgeList.size() << endl;
        cout << "Total Duration: " << (maxTime - minTime) / (3600 * 24) << " days" << endl;
        totalTime = maxTime;
    }

    return 0;
}

int BaseGraph::loadEdgeList(double* features, uint64_t num_edges, uint64_t num_features)
{
    /// First pass - determine number of vertices and edges
    long vertexNo = 0;
    for (unsigned int i = 0; i < num_edges; i++) {
        double* thisFeatureVec = &(features[i * num_features]);

        GraphElemID edgeID   = thisFeatureVec[0];
        GraphElemID sourceID = thisFeatureVec[1];
        GraphElemID targetID = thisFeatureVec[2];

        // Hash the edge IDs
        if (edgeIdMap.find(edgeID) != edgeIdMap.end()) {
            throw std::invalid_argument("Edge with the same ID = " + to_string(edgeID) + " already exists.");
            return -1;
        }
        edgeIdMap[edgeID] = i;

        // Hash the vertex IDs
        if (vertexIdMap.find(sourceID) == vertexIdMap.end())
            vertexIdMap[sourceID] = vertexNo++;
        if (vertexIdMap.find(targetID) == vertexIdMap.end())
            vertexIdMap[targetID] = vertexNo++;
    }

    // Create node list
    nodeList.resize(vertexNo);
    for (unsigned int i = 0; i < vertexNo; i++) {
        nodeList[i].index = i;
    }

    /// Second pass - populate lists
    Timestamp minTime = std::numeric_limits<Timestamp>::max(), maxTime = 0;
    for (unsigned int i = 0; i < num_edges; i++) {
        double* thisFeatureVec = &(features[i * num_features]);

        GraphElemID edgeID   = thisFeatureVec[0];
        GraphElemID sourceID = thisFeatureVec[1];
        GraphElemID targetID = thisFeatureVec[2];
        Timestamp   tstamp   = thisFeatureVec[3];

        Edge* edge = new Edge();

        int sourceVertexIndex = vertexIdMap[sourceID];
        int targetVertexIndex = vertexIdMap[targetID];
        if (nullptr != edge) {
            edge->sourceNode = &nodeList[sourceVertexIndex];
            edge->sourceNode->setID(sourceID);

            edge->targetNode = &nodeList[targetVertexIndex];
            edge->targetNode->setID(targetID);

            edge->index  = edgeIdMap[edgeID];
            edge->id     = edgeID;
            edge->tstamp = tstamp;
        } else {
            return -1;
        }

        minTime = std::min(minTime, edge->tstamp);
        maxTime = std::max(maxTime, edge->tstamp);

        int startRawInd = 4;
        for (unsigned int k = startRawInd; k < num_features; k++) {
            edge->setRawFeat(k - startRawInd, thisFeatureVec[k]);
        }

        edgeList.push_back(edge);
    }

    sort(edgeList.begin(), edgeList.end(), compareEdges);

    for (unsigned int eind = 0; eind < edgeList.size(); eind++) {
        GraphElemID edgeID    = edgeList[eind]->id;
        edgeIdMap[edgeID]     = eind;
        edgeList[eind]->index = eind;
    }
    lastEdgeIndex = edgeList.size();

    maxTs     = maxTime;
    totalTime = maxTime;

    return 0;
}

int BaseGraph::readLabels(string path)
{
    ifstream labFile(path);

    bool first = true;
    while (true) {
        string line;
        getline(labFile, line);
        if (labFile.eof())
            break;

        if (first) {
            first = false;
            continue;
        }

        stringstream ss(line);

        double field[2];

        if (path.substr(path.find_last_of(".") + 1) == "csv") {
            for (int i = 0; i < 2; i++) {
                string substr;
                getline(ss, substr, ',');
                field[i] = stod(substr);
            }
        } else {
            ss >> field[0] >> field[1];
        }

        GraphElemID edgeID = field[0];
        int         isl    = field[1];

        // Hash the edge IDs
        if (edgeIdMap.find(edgeID) != edgeIdMap.end()) {
            int  eind = edgeIdMap[edgeID];
            auto edge = getEdge(eind);

            edge->isLaundering = isl;
        }
    }

    return 0;
}

bool BaseGraph::isEdgeListSorted()
{
    for (unsigned int i = 1; i < edgeList.size(); i++) {
        if (edgeList[i - 1]->getTStamp() > edgeList[i]->getTStamp())
            return false;
    }
    return true;
}

int BaseGraph::getNoOutOfOrderEdges()
{
    int       res     = 0;
    Timestamp prevMax = edgeList[0]->getTStamp();
    for (unsigned int i = 1; i < edgeList.size(); i++) {
        if (prevMax > edgeList[i]->getTStamp()) {
            res++;
        }
        prevMax = max(prevMax, edgeList[i]->getTStamp());
    }
    return res;
}

Edge* BaseGraph::getEdge(unsigned int eindex)
{
    if (edgeList.size() == 0) {
        throw std::runtime_error("The edge list is empty.");
    }

    int firstIndex = edgeList.front()->getIndex();

    if (eindex >= edgeList.size() + firstIndex || eindex < firstIndex) {
        throw std::runtime_error("Edge does not exist.");
    }
    return edgeList[eindex - firstIndex];
}

Node* BaseGraph::getVertex(unsigned int vid)
{
    if (vid >= nodeList.size()) {
        throw std::runtime_error("Vertex does not exist.");
    }
    return &(nodeList[vid]);
}

Edge* BaseGraph::getNextEdge(Edge* e)
{
    if (e == NULL)
        throw std::runtime_error("Input edge pointer cannot be NULL.");

    if (e == edgeList.back())
        return NULL; // NULL if there is no next edge

    unsigned int eid = e->getIndex();
    return getEdge(eid + 1);
}
