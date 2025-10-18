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

#include <vector>
#include <map>
#include <unordered_map>
#include <unordered_set>
#include <fstream>
#include <algorithm>
#include <atomic>
#include <cmath>
#include <numeric>

#include "featureEngineering.h"
#include "graph.h"
#include "utils.h"

#ifdef USE_TBB
using namespace tbb;
#endif

using namespace std;

namespace {
template <class T> inline T median(vector<T>& v)
{

    if (v.empty())
        return 0.0;
    auto n = v.size() / 2;
    nth_element(v.begin(), v.begin() + n, v.end());
    auto med = v[n];
    if (!(v.size() & 1U)) { // If the set size is even
        auto max_it = max_element(v.begin(), v.begin() + n);
        med         = (*max_it + med) / 2.0;
    }
    return med;
}

template <class T> inline T removeInf(T x)
{
    if (x == -std::numeric_limits<T>::infinity())
        return -std::numeric_limits<T>::min();
    if (x == std::numeric_limits<T>::infinity())
        return std::numeric_limits<T>::max();
    if (isnan(x))
        return 0;
    return x;
}

// returns [sum, avg, min, max]
template <class T> inline vector<T> sumAvgMinMax(vector<T>& v, runSettings& config)
{
    vector<T> result(4);
    result[0] = result[1] = result[2] = result[3] = 0.0;

    if (v.size() <= 0)
        return result;

    T min = v[0], max = v[0], sum = 0;
    for (unsigned int i = 0; i < v.size(); i++) {
        if (config.statFeatExists(StatFeatures::Min))
            min = min < v[i] ? min : v[i];
        if (config.statFeatExists(StatFeatures::Max))
            max = max > v[i] ? max : v[i];
        if (config.statFeatExists(StatFeatures::Sum) || config.statFeatExists(StatFeatures::Avg))
            sum += v[i];
    }

    result[0] = removeInf<T>(sum);
    result[1] = sum / v.size();
    result[2] = min;
    result[3] = max;

    return result;
}

template <class T> inline T getAvg(vector<T>& v)
{
    if (v.size() <= 0)
        return 0.0;

    T sum = 0;
    for (unsigned int i = 0; i < v.size(); i++)
        sum += v[i];

    return sum / v.size();
}

// returns [var, skew, kurtosis]
template <class T> inline vector<T> varSkewKurtosis(vector<T>& v, T mean, runSettings& config)
{
    vector<T> result(3);
    result[0] = result[1] = result[2] = 0.0;

    if (v.size() <= 0)
        return result;

    T m2 = 0, m3 = 0, m4 = 0;
    for (unsigned int i = 0; i < v.size(); i++) {
        T diff = v[i] - mean;
        if (config.statFeatExists(StatFeatures::Var) || config.statFeatExists(StatFeatures::Skew)
            || config.statFeatExists(StatFeatures::Kurtosis))
            m2 += pow(diff, 2);
        if (config.statFeatExists(StatFeatures::Skew))
            m3 += pow(diff, 3);
        if (config.statFeatExists(StatFeatures::Kurtosis))
            m4 += pow(diff, 4);
    }

    m2 = removeInf<T>(m2);
    m3 = removeInf<T>(m3);
    m4 = removeInf<T>(m4);

    result[0] = m2 / v.size();
    result[1] = (m2 == 0) ? 0.0 : sqrt(v.size()) * m3 / pow(m2, 1.5);
    result[2] = (m2 == 0) ? 0.0 : v.size() * m4 / pow(m2, 2);

    return result;
}
}

void computeVertexStatisticsFeatures(Graph* g, ShallowFeatureTable& featTable, runSettings& config,
                                     vector<int> vertexIDs, pair<Timestamp, Timestamp> TW)
{

    unsigned int upper = g->getVertexNo();
    if (vertexIDs.size() != 0)
        upper = vertexIDs.size();

    featTable.resize(0);
    featTable.resize(upper);

    Timestamp fromTs = TW.first, toTs = TW.second;

#ifndef USE_TBB
#pragma omp parallel default(shared)
#pragma omp single
    {
#pragma omp taskloop
        for (unsigned int ii = 0; ii < upper; ii++) {
#else
    parallel_for(size_t(0), size_t(upper), [&](size_t ii) {
#endif
            int vert = ii;
            if (vertexIDs.size() != 0)
                vert = vertexIDs[ii];

            ShallowFeatureVector shFeat(getNumStatFeatures(config));

            // rep == 0 -> outgoing edges
            // rep == 1 -> incoming edges
            for (int rep = 0; rep < 2; rep++) {

                vector<vector<double>> neighborhoodFeatureVectors(config.rawFeatureColumns.size());

                unordered_set<int> fanVertices;
                int                fanInOut = 0, degreeInOut = 0;

                if (rep == 0) {
                    g->foreachOutEdge(vert, [&](int v, Timestamp tv, GraphElemID eiv) {
                        if (fromTs == -1 || ((tv >= fromTs) && (tv <= toTs))) {
                            if (config.statFeatExists(StatFeatures::Deg) || config.statFeatExists(StatFeatures::Ratio))
                                degreeInOut += 1;
                            if (config.statFeatExists(StatFeatures::Fan) || config.statFeatExists(StatFeatures::Ratio))
                                fanVertices.insert(v);

                            for (unsigned int ind = 0; ind < config.rawFeatureColumns.size(); ind++) {
                                int featInd = config.rawFeatureColumns[ind];

                                double featVal;

                                try {
                                    if (featInd == 0)
                                        featVal = eiv;
                                    else if (featInd == 1)
                                        featVal = vert;
                                    else if (featInd == 2)
                                        featVal = v;
                                    else if (featInd == 3)
                                        featVal = tv;
                                    else {
                                        int eindex = g->edgeIdMap[eiv];
                                        featVal    = g->getEdge(eindex)->getRawFeat(featInd - 4);
                                    }
                                } catch (const std::out_of_range& e) {
                                    throw std::out_of_range("Raw feature column " + to_string(featInd)
                                                            + " does not exist.");
                                }

                                neighborhoodFeatureVectors[ind].push_back(featVal);
                            }
                        }
                    });
                } else {
                    g->foreachInEdge(vert, [&](int u, Timestamp tu, GraphElemID eiu) {
                        if (fromTs == -1 || ((tu >= fromTs) && (tu <= toTs))) {
                            if (config.statFeatExists(StatFeatures::Deg) || config.statFeatExists(StatFeatures::Ratio))
                                degreeInOut += 1;
                            if (config.statFeatExists(StatFeatures::Fan) || config.statFeatExists(StatFeatures::Ratio))
                                fanVertices.insert(u);

                            for (unsigned int ind = 0; ind < config.rawFeatureColumns.size(); ind++) {
                                int featInd = config.rawFeatureColumns[ind];

                                double featVal;

                                try {
                                    if (featInd == 0)
                                        featVal = eiu;
                                    else if (featInd == 1)
                                        featVal = u;
                                    else if (featInd == 2)
                                        featVal = vert;
                                    else if (featInd == 3)
                                        featVal = tu;
                                    else {
                                        int eindex = g->edgeIdMap[eiu];
                                        featVal    = g->getEdge(eindex)->getRawFeat(featInd - 4);
                                    }
                                } catch (const std::out_of_range& e) {
                                    throw std::out_of_range("Raw feature column " + to_string(featInd)
                                                            + " does not exist.");
                                }

                                neighborhoodFeatureVectors[ind].push_back(featVal);
                            }
                        }
                    });
                }
                fanInOut          = fanVertices.size();
                double ratioInOut = degreeInOut ? (static_cast<double>(degreeInOut) / fanInOut) : 0.0;

                // Set Fan, Deg, and Ratio
                if (config.statFeatExists(StatFeatures::Fan))
                    shFeat[getVertStatIndex(config, StatFeatures::Fan, -1, (rep == 0))] = fanInOut;
                if (config.statFeatExists(StatFeatures::Deg))
                    shFeat[getVertStatIndex(config, StatFeatures::Deg, -1, (rep == 0))] = degreeInOut;
                if (config.statFeatExists(StatFeatures::Ratio))
                    shFeat[getVertStatIndex(config, StatFeatures::Ratio, -1, (rep == 0))] = ratioInOut;

                for (unsigned int ind = 0; ind < config.rawFeatureColumns.size(); ind++) {
                    vector<double>& featureVec = neighborhoodFeatureVectors[ind];

                    if (config.statFeatExists(StatFeatures::Med)) {
                        double medval = median<double>(featureVec);

                        shFeat[getVertStatIndex(config, StatFeatures::Med, ind, (rep == 0))] = medval;
                    }

                    double avg = 0.0;
                    if (config.statFeatExists(StatFeatures::Avg) || config.statFeatExists(StatFeatures::Sum)
                        || config.statFeatExists(StatFeatures::Min) || config.statFeatExists(StatFeatures::Max)) {
                        auto result = sumAvgMinMax<double>(featureVec, config);

                        if (config.statFeatExists(StatFeatures::Avg)) {
                            shFeat[getVertStatIndex(config, StatFeatures::Avg, ind, (rep == 0))] = result[1];
                            avg                                                                  = result[1];
                        }
                        if (config.statFeatExists(StatFeatures::Sum))
                            shFeat[getVertStatIndex(config, StatFeatures::Sum, ind, (rep == 0))] = result[0];
                        if (config.statFeatExists(StatFeatures::Min))
                            shFeat[getVertStatIndex(config, StatFeatures::Min, ind, (rep == 0))] = result[2];
                        if (config.statFeatExists(StatFeatures::Max))
                            shFeat[getVertStatIndex(config, StatFeatures::Max, ind, (rep == 0))] = result[3];
                    }

                    if (config.statFeatExists(StatFeatures::Var) || config.statFeatExists(StatFeatures::Skew)
                        || config.statFeatExists(StatFeatures::Kurtosis)) {

                        if (!config.statFeatExists(StatFeatures::Avg))
                            avg = getAvg<double>(featureVec);
                        auto result = varSkewKurtosis<double>(featureVec, avg, config);

                        if (config.statFeatExists(StatFeatures::Var))
                            shFeat[getVertStatIndex(config, StatFeatures::Var, ind, (rep == 0))] = result[0];
                        if (config.statFeatExists(StatFeatures::Skew))
                            shFeat[getVertStatIndex(config, StatFeatures::Skew, ind, (rep == 0))] = result[1];
                        if (config.statFeatExists(StatFeatures::Kurtosis))
                            shFeat[getVertStatIndex(config, StatFeatures::Kurtosis, ind, (rep == 0))] = result[2];
                    }
                }
            }

            featTable[ii].first  = vert;
            featTable[ii].second = std::move(shFeat);
#ifndef USE_TBB
        }
    }
#else
    });
#endif
}

#if USE_DYNAMIC_GRAPH == True
void computeIncrementalStatisticsFeatures(Graph* g, ShallowFeatureTable& featTable, runSettings& config,
                                          vector<int> vertexIDs)
{

    DynamicGraph* dg = dynamic_cast<DynamicGraph*>(g);

    unsigned int upper = dg->getVertexNo();
    if (vertexIDs.size() != 0)
        upper = vertexIDs.size();

    featTable.resize(0);
    featTable.resize(upper);

#ifndef USE_TBB
#pragma omp parallel default(shared)
#pragma omp single
    {
#pragma omp taskloop
        for (unsigned int ii = 0; ii < upper; ii++) {
#else
    parallel_for(size_t(0), size_t(upper), [&](size_t ii) {
#endif
            int vert = ii;
            if (vertexIDs.size() != 0)
                vert = vertexIDs[ii];

            ShallowFeatureVector shFeat(getNumStatFeatures(config));

            for (int rep = 0; rep < 2; rep++) {
                int fanInOut = (rep == 0) ? g->numOutVertices(vert) : g->numInVertices(vert);
                int degInOut = (rep == 0) ? g->numOutEdges(vert) : g->numInEdges(vert);

                double ratioInOut = degInOut ? (static_cast<double>(degInOut) / fanInOut) : 0.0;

                // Fan, Degree, Ratio
                if (config.statFeatExists(StatFeatures::Fan))
                    shFeat[getVertStatIndex(config, StatFeatures::Fan, -1, (rep == 0))] = fanInOut;
                if (config.statFeatExists(StatFeatures::Deg))
                    shFeat[getVertStatIndex(config, StatFeatures::Deg, -1, (rep == 0))] = degInOut;
                if (config.statFeatExists(StatFeatures::Ratio))
                    shFeat[getVertStatIndex(config, StatFeatures::Ratio, -1, (rep == 0))] = ratioInOut;

                for (unsigned int ind = 0; ind < config.rawFeatureColumns.size(); ind++) {
                    int featInd = config.rawFeatureColumns[ind];

                    VertexStat featureStat;
                    try {
                        featureStat = dg->getStatFeatures(vert, featInd, (rep == 0));
                    } catch (const std::out_of_range& e) {
                        cerr << e.what() << endl;
                        continue;
                    } catch (const std::invalid_argument& e) {
                        cerr << e.what() << endl;
                        break;
                    }

                    // Avg and Sum
                    if (config.statFeatExists(StatFeatures::Avg))
                        shFeat[getVertStatIndex(config, StatFeatures::Avg, ind, (rep == 0))] = featureStat.avg;
                    if (config.statFeatExists(StatFeatures::Sum))
                        shFeat[getVertStatIndex(config, StatFeatures::Sum, ind, (rep == 0))] = featureStat.sum;

                    bool zeroM2 = false;
                    if (abs(featureStat.m2 / (featureStat.n * featureStat.avg * featureStat.avg)) < zeroThresh)
                        zeroM2 = true;

                    // Var, Skew, Kurtosis
                    if (config.statFeatExists(StatFeatures::Var))
                        shFeat[getVertStatIndex(config, StatFeatures::Var, ind, (rep == 0))]
                            = (featureStat.n == 0.0 || zeroM2) ? 0.0 : featureStat.m2 / featureStat.n;
                    if (config.statFeatExists(StatFeatures::Skew))
                        shFeat[getVertStatIndex(config, StatFeatures::Skew, ind, (rep == 0))]
                            = (featureStat.n == 0.0 || zeroM2)
                                  ? 0.0
                                  : removeInf<double>(sqrt(featureStat.n) * featureStat.m3 / pow(featureStat.m2, 1.5));
                    if (config.statFeatExists(StatFeatures::Kurtosis))
                        shFeat[getVertStatIndex(config, StatFeatures::Kurtosis, ind, (rep == 0))]
                            = (featureStat.n == 0.0 || zeroM2) ? 0.0
                                                               : removeInf<double>(featureStat.n * featureStat.m4
                                                                                   / (featureStat.m2 * featureStat.m2));
                }

                /// For compatibility, might not have the best performance
                if (config.statFeatExists(StatFeatures::Min) || config.statFeatExists(StatFeatures::Max)
                    || config.statFeatExists(StatFeatures::Med)) {

                    vector<vector<double>> neighborhoodFeatureVectors(config.rawFeatureColumns.size());

                    if (rep == 0) {
                        g->foreachOutEdge(vert, [&](int v, Timestamp tv, GraphElemID eiv) {
                            for (unsigned int ind = 0; ind < config.rawFeatureColumns.size(); ind++) {
                                int featInd = config.rawFeatureColumns[ind];

                                double featVal;

                                try {
                                    if (featInd == 0)
                                        featVal = eiv;
                                    else if (featInd == 1)
                                        featVal = vert;
                                    else if (featInd == 2)
                                        featVal = v;
                                    else if (featInd == 3)
                                        featVal = tv;
                                    else {
                                        int eindex = g->edgeIdMap[eiv];
                                        featVal    = g->getEdge(eindex)->getRawFeat(featInd - 4);
                                    }
                                } catch (const std::out_of_range& e) {
                                    throw std::out_of_range("Raw feature column " + to_string(featInd)
                                                            + " does not exist.");
                                }

                                neighborhoodFeatureVectors[ind].push_back(featVal);
                            }
                        });
                    } else {
                        g->foreachInEdge(vert, [&](int u, Timestamp tu, GraphElemID eiu) {
                            for (unsigned int ind = 0; ind < config.rawFeatureColumns.size(); ind++) {
                                int featInd = config.rawFeatureColumns[ind];

                                double featVal;

                                try {
                                    if (featInd == 0)
                                        featVal = eiu;
                                    else if (featInd == 1)
                                        featVal = u;
                                    else if (featInd == 2)
                                        featVal = vert;
                                    else if (featInd == 3)
                                        featVal = tu;
                                    else {
                                        int eindex = g->edgeIdMap[eiu];
                                        featVal    = g->getEdge(eindex)->getRawFeat(featInd - 4);
                                    }
                                } catch (const std::out_of_range& e) {
                                    throw std::out_of_range("Raw feature column " + to_string(featInd)
                                                            + " does not exist.");
                                }

                                neighborhoodFeatureVectors[ind].push_back(featVal);
                            }
                        });
                    }

                    for (unsigned int ind = 0; ind < config.rawFeatureColumns.size(); ind++) {
                        vector<double>& featureVec = neighborhoodFeatureVectors[ind];

                        double minVal = 0, maxVal = 0;
                        if (config.statFeatExists(StatFeatures::Min) || config.statFeatExists(StatFeatures::Max)) {
                            if (featureVec.size() > 0) {
                                auto pair = std::minmax_element(featureVec.begin(), featureVec.end());
                                minVal    = *pair.first;
                                maxVal    = *pair.second;
                            } else {
                                minVal = 0;
                                maxVal = 0;
                            }
                        }

                        // Min, Max, Median
                        if (config.statFeatExists(StatFeatures::Min))
                            shFeat[getVertStatIndex(config, StatFeatures::Min, ind, (rep == 0))] = minVal;
                        if (config.statFeatExists(StatFeatures::Max))
                            shFeat[getVertStatIndex(config, StatFeatures::Max, ind, (rep == 0))] = maxVal;
                        if (config.statFeatExists(StatFeatures::Med))
                            shFeat[getVertStatIndex(config, StatFeatures::Med, ind, (rep == 0))]
                                = median<double>(featureVec);
                    }
                }
            }

            featTable[ii].first  = vert;
            featTable[ii].second = std::move(shFeat);
#ifndef USE_TBB
        }
    }
#else
    });
#endif
}
#endif
