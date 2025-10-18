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

#ifndef VERTEX_STATISTICS_H
#define VERTEX_STATISTICS_H

#include <vector>
#include <cmath>
#include <numeric>

#include "graph.h"

using namespace std;

/******************* Graph *******************/

const double neginf     = -std::numeric_limits<double>::infinity();
const double posinf     = std::numeric_limits<double>::infinity();
const double minfl      = -std::numeric_limits<double>::min();
const double maxfl      = std::numeric_limits<double>::max();
const double zeroThresh = 1e-5;

inline double removeInf(double x)
{
    if (x == neginf)
        return minfl;
    if (x == posinf)
        return maxfl;
    if (isnan(x))
        return 0;
    return x;
}

struct VertexStat {
    int    n   = 0;
    double sum = 0.0;
    double avg = 0.0;
    double m2  = 0.0; // n * second central moment
    double m3  = 0.0; // n * third central moment
    double m4  = 0.0; // n * fourth central moment
};

class IncrementalVertexStatistics {
public:
    IncrementalVertexStatistics() { }

    void setRawFeatIndices(vector<int> featIndices)
    {
        bool equal = true;
        if (rawFeatureColumns.size() == featIndices.size()) {
            for (unsigned int i = 0; i < rawFeatureColumns.size(); i++) {
                if (rawFeatureColumns[i] != featIndices[i]) {
                    equal = false;
                    break;
                }
            }
        } else {
            equal = false;
        }

        if (equal)
            return;

        rawFeatureColumns = featIndices;

        for (unsigned int i = 0; i < rawFeatureColumns.size(); i++) {
            featColToInd[rawFeatureColumns[i]] = i;
        }

        // Reset the state
        int numRawFeats = rawFeatureColumns.size();
        for (int i = 0; i < vertexNo; i++) {
            featureOut[i].resize(0);
            featureOut[i].resize(numRawFeats);
            featureIn[i].resize(0);
            featureIn[i].resize(numRawFeats);
        }
    }

    // Invoking this function while the transformation is happening might lead to unwanted result
    void setStatFeatures(bool sum, bool avg, bool var, bool skew, bool kurtosis)
    {
        if (sum)
            computeSum = true;
        else
            computeSum = false;
        if (avg || var || skew || kurtosis)
            computeAvg = true;
        else
            computeAvg = false;
        if (var || skew || kurtosis)
            computeM2 = true;
        else
            computeM2 = false;
        if (skew || kurtosis)
            computeM3 = true;
        else
            computeM3 = false;
        if (kurtosis)
            computeM4 = true;
        else
            computeM4 = false;
    }

    void insertEdge(Edge* edge);

    void removeEdge(Edge* edge);

    VertexStat getFeatures(int vertexIndex, int featIndex, bool out);

protected:
    // Outer vector is per-vertex
    // Inner vector is per-feature
    vector<vector<VertexStat>> featureOut, featureIn;

    int                     vertexNo = 0;
    vector<int>             rawFeatureColumns;
    unordered_map<int, int> featColToInd;

    int addedEdges   = 0;
    int removedEdges = 0;

    bool computeAvg = false, computeSum = false, computeM2 = false, computeM3 = false, computeM4 = false;
};

inline void IncrementalVertexStatistics::insertEdge(Edge* edge)
{

    if (!edge)
        return;
    int sourceVert = edge->getSourceVertexIndex();
    int targetVert = edge->getTargetVertexIndex();

    vertexNo        = max(max(sourceVert + 1, targetVert + 1), vertexNo);
    int numRawFeats = rawFeatureColumns.size();
    featureOut.resize(vertexNo, vector<VertexStat>(numRawFeats));
    featureIn.resize(vertexNo, vector<VertexStat>(numRawFeats));

    for (unsigned int i = 0; i < rawFeatureColumns.size(); i++) {
        int featInd = rawFeatureColumns[i];

        double featVal;

        // TODO: Don't use magic numbers
        try {
            if (featInd == 0)
                featVal = edge->getID();
            else if (featInd == 1)
                featVal = edge->getSourceVertexID();
            else if (featInd == 2)
                featVal = edge->getTargetVertexID();
            else if (featInd == 3)
                featVal = edge->getTStamp();
            else
                featVal = edge->getRawFeat(featInd - 4);
        } catch (const std::out_of_range& e) {
            throw std::out_of_range("Raw feature column " + to_string(featInd) + " does not exist.");
        }

        for (int rep = 0; rep < 2; rep++) {

            VertexStat& thisVertStat = ((rep == 0) ? featureOut[sourceVert][i] : featureIn[targetVert][i]);

            thisVertStat.n++;

            double n = thisVertStat.n;

            // Sum
            if (computeSum) {
                thisVertStat.sum += featVal;
                thisVertStat.sum = removeInf(thisVertStat.sum);
            }

            // Avg
            double prevAvg = thisVertStat.avg;
            double tmpDiff = featVal - prevAvg;
            if (computeAvg)
                thisVertStat.avg = removeInf(prevAvg + tmpDiff / n);

            // M2
            double prevM2 = thisVertStat.m2;
            if (computeM2) {
                thisVertStat.m2 = removeInf(thisVertStat.m2 + (featVal - thisVertStat.avg) * tmpDiff);
                if (abs(thisVertStat.m2 / prevM2) < zeroThresh)
                    thisVertStat.m2 = 0;
            }

            // M3
            double prevM3 = thisVertStat.m3;
            if (computeM3) {
                thisVertStat.m3 = removeInf(thisVertStat.m3
                                            + tmpDiff / n * (-3 * prevM2 + (n - 1) * (n - 2) * tmpDiff * tmpDiff / n));
            }

            // M4
            if (computeM4)
                thisVertStat.m4 = removeInf(
                    thisVertStat.m4
                    + tmpDiff / n
                          * (-4 * prevM3
                             + tmpDiff / n * (6 * prevM2 + (n - 1) * (n * n - 3 * n + 3) * tmpDiff * tmpDiff / n)));
        }
    }
}

inline void IncrementalVertexStatistics::removeEdge(Edge* edge)
{

    if (!edge)
        return;
    int sourceVert = edge->getSourceVertexIndex();
    int targetVert = edge->getTargetVertexIndex();

    for (unsigned int i = 0; i < rawFeatureColumns.size(); i++) {
        volatile int featInd = rawFeatureColumns[i];

        double featVal;
        // TODO: Don't use magic numbers
        try {
            if (featInd == 0)
                featVal = edge->getID();
            else if (featInd == 1)
                featVal = edge->getSourceVertexID();
            else if (featInd == 2)
                featVal = edge->getTargetVertexID();
            else if (featInd == 3)
                featVal = edge->getTStamp();
            else
                featVal = edge->getRawFeat(featInd - 4);
        } catch (const std::out_of_range& e) {
            throw std::out_of_range("Raw feature column " + to_string(featInd) + " does not exist.");
        }

        for (int rep = 0; rep < 2; rep++) {

            VertexStat& thisVertStat = ((rep == 0) ? featureOut[sourceVert][i] : featureIn[targetVert][i]);

            thisVertStat.n--;

            double n = thisVertStat.n;

            // Sum
            if (computeSum) {
                thisVertStat.sum -= featVal;
                thisVertStat.sum = removeInf(thisVertStat.sum);
            }

            // Avg
            double prevAvg = thisVertStat.avg;
            if (computeAvg)
                thisVertStat.avg = (n == 0) ? 0 : removeInf(prevAvg + (prevAvg - featVal) / n);

            double tmpDiff = featVal - thisVertStat.avg;
            // M2
            double prevM2 = thisVertStat.m2;
            if (computeM2) {
                thisVertStat.m2 = (n == 0) ? 0 : removeInf(thisVertStat.m2 - tmpDiff * (featVal - prevAvg));
                if (abs(thisVertStat.m2 / prevM2) < zeroThresh)
                    thisVertStat.m2 = 0;
            }

            // M3
            if (computeM3)
                thisVertStat.m3
                    = (n == 0) ? 0
                               : removeInf(thisVertStat.m3
                                           + tmpDiff / (n + 1)
                                                 * (3 * thisVertStat.m2 - n * (n - 1) * tmpDiff * tmpDiff / (n + 1)));

            // M4
            if (computeM4)
                thisVertStat.m4
                    = (n == 0) ? 0
                               : removeInf(thisVertStat.m4
                                           + tmpDiff / (n + 1)
                                                 * (4 * thisVertStat.m3
                                                    + tmpDiff / (n + 1)
                                                          * (-6 * thisVertStat.m2
                                                             - n * (n * n - n + 1) * tmpDiff * tmpDiff / (n + 1))));
        }
    }
}

inline VertexStat IncrementalVertexStatistics::getFeatures(int vertexIndex, int featIndex, bool out)
{
    if (featColToInd.find(featIndex) == featColToInd.end()) {
        throw std::invalid_argument("IncrementalVertexStatistics: Feature index does not exist.");
    }

    if (vertexIndex >= static_cast<int>(featureOut.size())) {
        throw std::out_of_range("IncrementalVertexStatistics: Vertex does not exist.");
    }

    if (out) {
        return featureOut[vertexIndex][featColToInd[featIndex]];
    } else {
        return featureIn[vertexIndex][featColToInd[featIndex]];
    }
}

#endif
