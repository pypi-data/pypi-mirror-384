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

#include <map>
#include <set>
#include <chrono>
#include <thread>
#include <vector>
#include <utility>
#include <fstream>
#include <iostream>
#include <algorithm>
#include <unordered_set>
#include <unordered_map>

#include "featureEngineering.h"
#include "utils.h"

using namespace std;

unordered_map<GraphElemID, int> readLabels(string path)
{
    ifstream labFile(path);

    unordered_map<GraphElemID, int> retMap;

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

        retMap[edgeID] = isl;
    }

    return retMap;
}

inline void printHelpBenchmark()
{
    std::cout << " Performance evaluation of the feature engineering library " << std::endl;
    std::cout << "    -f                Path to the test transactions." << std::endl;
    std::cout << "    -g                Path to the train graph." << std::endl;
    std::cout << "    -l                Path to the labels." << std::endl;
    std::cout << "    -config           Path to the config file." << std::endl;
    std::cout << "    -batch            Batch size." << std::endl;
    std::cout << "    -np               Don't print the output features." << std::endl;
    std::cout << "    -h                Prints this message." << std::endl;
}

int main(int argc, char* argv[])
{

#ifndef USE_DYNAMIC_GRAPH
    cout << "DYNAMIC GRAPH NOT USED" << endl;
    return 0;
#endif

    if (cmdOptionExists(argv, argv + argc, "-h")) {
        printHelpBenchmark();
        return 0;
    }

    /// Reading the input network
    std::string path;
    if (cmdOptionExists(argv, argv + argc, "-f")) {
        path = string(getCmdOption(argv, argv + argc, "-f"));
    } else {
        printHelp();
        return 0;
    }

    std::string graph_file = "";
    if (cmdOptionExists(argv, argv + argc, "-g")) {
        graph_file = string(getCmdOption(argv, argv + argc, "-g"));
    }

    /// Reading the input parameters
    string config_path;
    if (cmdOptionExists(argv, argv + argc, "-config")) {
        config_path = getCmdOption(argv, argv + argc, "-config");
    } else {
        cout << "Please provide the path to the config file" << endl;
        return 0;
    }

    int batchSize = 128;
    if (cmdOptionExists(argv, argv + argc, "-batch"))
        batchSize = stoi(string(getCmdOption(argv, argv + argc, "-batch")));

    string base_path = path.substr(0, path.find_last_of("/"));
    string out_path  = base_path + "/output_features_api.csv";

    unordered_map<GraphElemID, int> labels;
    if (cmdOptionExists(argv, argv + argc, "-np")) {
        out_path = "";
    } else {
        if (cmdOptionExists(argv, argv + argc, "-l")) {
            string labpath = string(getCmdOption(argv, argv + argc, "-l"));
            labels         = readLabels(labpath);
        }
    }

    auto                   read_start = chrono::high_resolution_clock::now();
    vector<vector<double>> edgeList;
    {
        ifstream transFile(path);

        bool first = true;
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

            vector<double> edgeVec;

            if (path.substr(path.find_last_of(".") + 1) == "csv") {
                while (ss.good()) {
                    string substr;
                    getline(ss, substr, ',');
                    double feat = stod(substr);
                    edgeVec.push_back(feat);
                }
            } else {
                double feat;
                while (ss >> feat) {
                    edgeVec.push_back(feat);
                }
            }

            edgeList.push_back(move(edgeVec));
        }
    }
    auto   read_end = chrono::high_resolution_clock::now();
    double readTime = chrono::duration_cast<chrono::milliseconds>(read_end - read_start).count() / 1000.0;
    cout << "    Read edgelist time: " << readTime << " s" << endl;

    computeFeaturesDynamicAPI(edgeList, config_path, graph_file, batchSize, false, out_path, labels);
    return 0;
}
