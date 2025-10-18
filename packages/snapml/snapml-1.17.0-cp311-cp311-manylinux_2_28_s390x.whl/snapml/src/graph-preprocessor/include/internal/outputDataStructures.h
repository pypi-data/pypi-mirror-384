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

#ifndef OUTPUT_DATA_STRUCTURES_H
#define OUTPUT_DATA_STRUCTURES_H

#include <vector>
#include <map>
#include <set>
#include <mutex>
#include <list>
#include <functional>
#include <unordered_set>
#include <unordered_map>

#include "graph.h"
#include "utils.h"
#include "dataStructures.h"

using namespace std;

struct KeyHasher {
    size_t operator()(const pair<int, int>& k) const
    {

        hash<int> hasher;

        size_t hashRes = 0;

        hashRes ^= hasher(k.first) + 0x9e3779b9 + (hashRes << 6) + (hashRes >> 2);
        hashRes ^= hasher(k.second) + 0x9e3779b9 + (hashRes << 6) + (hashRes >> 2);

        return hashRes;
    }
};

struct PatternCount {
    list<pair<int, Pattern>> myList;

    PatternCount() = default;
    PatternCount(const PatternCount& other);
    PatternCount(PatternCount&& other);
    PatternCount& operator=(const PatternCount& other);
    PatternCount& operator=(PatternCount&& other);
};

class nodeFeatures {
public:
    unordered_map<Pattern, unordered_map<int, int>, EnumClassHash> patternBins;
    void                                                           clear();
};

// typedef unordered_map<int, nodeFeatures> DataFrame;
typedef vector<pair<GraphElemID, nodeFeatures>>  DataFrame;
typedef unordered_map<GraphElemID, nodeFeatures> DataFrameMap;

typedef vector<double>                          ShallowFeatureVector;
typedef vector<pair<int, ShallowFeatureVector>> ShallowFeatureTable;

inline unsigned long getDFSize(DataFrame& df, runSettings& config)
{
    unsigned long dfSize = 0;

    unsigned long entrySize = 0;
    for (int i = 0; i < (int)(Pattern::SIZE); i++) {
        Pattern pat = (Pattern)(i);
        if (config.patternExists(pat)) {
            entrySize += config.bins[pat].size() * sizeof(int);
        }
    }

    dfSize += (sizeof(int) + entrySize) * df.size();

    return dfSize;
}

class PerThreadDataFrame {
public:
    PerThreadDataFrame(int nt = 256)
        : ptDataframe(nt)
    {
    }

    /**
     * Increments the pattern count of the specific bin for the given edge.
     *
     * @param node Vertex/edge id for which the feature count should be incremented
     * @param p Pattern type
     * @param bin Bin of the pattern to be incremented
     */
    void incrementPatternCount(int node, Pattern p, int bin);

    void combine(DataFrame& nodeDF, int numNodes);
    void combineAPI(DataFrame& nodeDF, vector<GraphElemID> edgeIDs);

    void clear() { ptDataframe.clear(); }

private:
    ConcurrentContainer<DataFrameMap> ptDataframe;
};

#endif // OUTPUT_DATA_STRUCTURES_H
