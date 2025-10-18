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

#include "outputDataStructures.h"

#include <algorithm>
#include <iostream>
#include <atomic>

#include "utils.h"

using namespace std;
#ifdef USE_TBB
using namespace tbb;
#endif

unsigned long memLogger   = 0;
unsigned long curMemUsage = 0;

void PerThreadDataFrame::incrementPatternCount(int node, Pattern p, int bin)
{
    auto& localDF = ptDataframe.local();
    localDF[node].patternBins[p][bin]++;
}

void PerThreadDataFrame::combine(DataFrame& nodeDF, int numNodes)
{
    vector<DataFrameMap*> dfArray;
    ptDataframe.combine_each([&](DataFrameMap& localDF) { dfArray.push_back(&localDF); });

    if (dfArray.size() == 0)
        return;

    nodeDF.resize(numNodes);

    std::mutex outMutex;

    int numChunks = dfArray.size();

    int chunkSize = numNodes / numChunks;

    if (chunkSize == 0)
        chunkSize = 10;

    std::atomic<int> nextStartInterval(0);

#ifndef USE_TBB
#pragma omp parallel for default(shared)
    for (int r = 0; r < numNodes; r += chunkSize) {
#else
    parallel_for(size_t(0), size_t(numNodes), size_t(chunkSize), [&](size_t r) {
#endif
        DataFrameMap tempMap;

        for (int node = r; node < std::min(static_cast<int>(r) + chunkSize, numNodes); node++) {

            for (auto& localPtr : dfArray) {
                if (localPtr->find(node) == localPtr->end())
                    continue;

                nodeFeatures& entryDF = localPtr->at(node);

                if (tempMap.find(node) == tempMap.end()) {
                    tempMap[node] = std::move(entryDF);
                    continue;
                }

                for (int pi = 0; pi < static_cast<int>(Pattern::SIZE); pi++) {
                    Pattern p = static_cast<Pattern>(pi);
                    for (auto& it2 : entryDF.patternBins[p]) {
                        tempMap[node].patternBins[p][it2.first] += it2.second;
                    }
                }

                entryDF.clear();
            }
        }

        int startInterval = nextStartInterval.fetch_add(tempMap.size(), std::memory_order_relaxed);
        int i             = 0;
        for (auto& tmp : tempMap) {
            nodeDF[startInterval + i] = std::move(tmp);
            i++;
        }
    }
#ifdef USE_TBB
    , simple_partitioner());
#endif

    nodeDF.resize(nextStartInterval);
}

void PerThreadDataFrame::combineAPI(DataFrame& nodeDF, vector<GraphElemID> edgeIDs)
{
    vector<DataFrameMap*> dfArray;
    ptDataframe.combine_each([&](DataFrameMap& localDF) { dfArray.push_back(&localDF); });

    if (dfArray.size() == 0)
        return;

    int numEdgeIndices = edgeIDs.size();

    nodeDF.resize(numEdgeIndices);

    std::mutex outMutex;

    int numChunks = dfArray.size();

    int chunkSize = numEdgeIndices / numChunks;

    if (chunkSize == 0)
        chunkSize = 10;

    std::atomic<int> nextStartInterval(0);

#ifndef USE_TBB
#pragma omp parallel for default(shared)
    for (int r = 0; r < numEdgeIndices; r += chunkSize) {
#else
    parallel_for(size_t(0), size_t(numEdgeIndices), size_t(chunkSize), [&](size_t r) {
#endif
        DataFrameMap tempMap;

        for (int ni = r; ni < std::min(static_cast<int>(r) + chunkSize, numEdgeIndices); ni++) {

            int node = edgeIDs[ni];

            for (auto& localPtr : dfArray) {
                if (localPtr->find(node) == localPtr->end())
                    continue;

                nodeFeatures& entryDF = localPtr->at(node);

                if (tempMap.find(node) == tempMap.end()) {
                    tempMap[node] = std::move(entryDF);
                    continue;
                }

                for (int pi = 0; pi < static_cast<int>(Pattern::SIZE); pi++) {
                    Pattern p = static_cast<Pattern>(pi);
                    for (auto& it2 : entryDF.patternBins[p]) {
                        tempMap[node].patternBins[p][it2.first] += it2.second;
                    }
                }

                entryDF.clear();
            }
        }

        int startInterval = nextStartInterval.fetch_add(tempMap.size(), std::memory_order_relaxed);
        int i             = 0;
        for (auto& tmp : tempMap) {
            nodeDF[startInterval + i] = std::move(tmp);
            i++;
        }
    }
#ifdef USE_TBB
    , simple_partitioner());
#endif

    nodeDF.resize(nextStartInterval);
}

PatternCount::PatternCount(const PatternCount& other) { myList = other.myList; }

PatternCount::PatternCount(PatternCount&& other) { myList = std::move(other.myList); }

PatternCount& PatternCount::operator=(const PatternCount& other)
{
    myList = other.myList;
    return *this;
}

PatternCount& PatternCount::operator=(PatternCount&& other)
{
    myList = std::move(other.myList);
    return *this;
}

void nodeFeatures::clear() { freeContainer(patternBins); }
