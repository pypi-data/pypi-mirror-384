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

#ifndef TEST_UTILS_H
#define TEST_UTILS_H

#include <list>
#include <fstream>
#include <ostream>
#include <iostream>
#include <string>
#include <vector>
#include <unordered_map>

#include "utils.h"
#include "outputDataStructures.h"

using namespace std;

#ifndef PROJECT_SOURCE_DIR
#define PROJECT_SOURCE_DIR ".."
#endif

string pathToIdealDir = string(PROJECT_SOURCE_DIR) + "/test/correctOutput";
string pathToInputDir = string(PROJECT_SOURCE_DIR) + "/test/input";

typedef unordered_map<GraphElemID, unordered_map<int, int>> NodeBins;
typedef unordered_map<Pattern, NodeBins, EnumClassHash>     PerPatternFeatures;
typedef unordered_map<GraphElemID, vector<double>>          FeatureTable;

inline void readDF(string path, PerPatternFeatures& idealDF)
{
    ifstream file(path);

    bool first = true;

    unordered_map<Pattern, vector<int>, EnumClassHash> binLocations;

    while (true) {
        string line;
        getline(file, line);
        if (file.eof())
            break;

        stringstream ss(line);

        // Process header
        if (first) {
            int    colNum = 0;
            string header;
            while (getline(ss, header, ',')) {
                for (int i = 0; i < (int)(Pattern::SIZE); i++) {
                    Pattern pat = (Pattern)(i);
                    if (header.find(string(PatternNames[i])) != std::string::npos) {
                        binLocations[pat].push_back(colNum);
                        break;
                    }
                }
                colNum++;
            }

            first = false;
            continue;
        }

        // Process row
        int    colNum = -1;
        int    nodeID = 0;
        string entry;
        while (getline(ss, entry, ',')) {
            colNum++;
            long x = std::stol(entry);

            if (colNum == 0) {
                nodeID = x;
            } else if (x != 0) {
                for (int i = 0; i < (int)(Pattern::SIZE); i++) {
                    Pattern pat = (Pattern)(i);
                    auto    it  = find(binLocations[pat].begin(), binLocations[pat].end(), colNum);
                    if (it != binLocations[pat].end()) {
                        int index                   = it - binLocations[pat].begin();
                        idealDF[pat][nodeID][index] = x;
                        break;
                    }
                }
            }
        }
    }
}

inline int readFeatureTable(string path, FeatureTable& featTable)
{
    ifstream file(path);
    if (file.fail())
        return -1;

    bool first = true;

    while (true) {
        string line;
        getline(file, line);
        if (file.eof())
            break;

        stringstream ss(line);

        // Process header
        if (first) {
            first = false;
            continue;
        }

        string entry;
        getline(ss, entry, ',');
        if (ss.fail())
            return -1;
        GraphElemID eid = std::stol(entry);

        vector<double> featVec;

        while (getline(ss, entry, ',')) {
            if (ss.fail())
                return -1;
            double feat = std::stod(entry);

            featVec.push_back(feat);
        }

        featTable[eid] = featVec;
    }

    return 0;
}

inline bool double_close(double a, double b, double percent)
{
    if (fabs(a - b) <= 1e-6)
        return true;

    if (a == b)
        return true;

    if (a != 0)
        return (fabs(a - b) / a) < percent;
    else if (b != 0)
        return (fabs(a - b) / b) < percent;

    return true;
}

inline int comparePatternFeatures(NodeBins& ideal, NodeBins& computed, string& error_msg)
{
    for (auto pair : ideal) {
        GraphElemID id        = pair.first;
        auto&       idealBins = pair.second;

        if (computed.find(id) == computed.end()) {
            error_msg = string("No features for the node with id ") + to_string(id) + string(" were computed");
            return -1;
        }

        for (auto binPair : idealBins) {
            int binIndex = binPair.first;
            int binVal   = binPair.second;

            if (computed[id][binIndex] != binVal) {
                error_msg = string("Features for the node with id ") + to_string(id)
                            + string(" were not correctly computed for bin index: ") + to_string(binIndex)
                            + string("; expected=") + to_string(binVal) + string(", computed=")
                            + to_string(computed[id][binIndex]);
                return -1;
            }
        }

        for (auto compBinPair : computed[id]) {
            int compBinIndex = compBinPair.first;
            int compBinVal   = compBinPair.second;

            if (idealBins[compBinIndex] != compBinVal) {
                error_msg = string("Features for the node with id ") + to_string(id)
                            + string(" were not correctly computed for bin index: ") + to_string(compBinIndex)
                            + string("; expected=") + to_string(idealBins[compBinIndex]) + string(", computed=")
                            + to_string(compBinVal);
                return -1;
            }
        }
    }

    for (auto pair : computed) {
        GraphElemID id = pair.first;
        if (ideal.find(id) == ideal.end()) {
            error_msg
                = string("Features computed for the node with id ") + to_string(id) + string(" should not exist.");
            return -1;
        }
    }

    return 0;
}

#endif // TEST_UTILS_H
