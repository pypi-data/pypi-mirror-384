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

#ifdef PROFILE
#include <ittnotify.h>
#endif

using namespace std;

int main(int argc, char* argv[])
{
#ifdef PROFILE
    __itt_pause();
#endif
    if (cmdOptionExists(argv, argv + argc, "-h")) {
        printHelp();
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

    runSettings config;

    /// Reading the input parameters
    if (cmdOptionExists(argv, argv + argc, "-config")) {
        string config_path = getCmdOption(argv, argv + argc, "-config");
        parseConfigFile(config_path, config);
    } else {
        cout << "Please provide the path to the config file" << endl;
        return 0;
    }

    config.graph_path = path;
    config.base_path  = path.substr(0, path.find_last_of("/"));

    int nthr = 12;
    if (cmdOptionExists(argv, argv + argc, "-n")) {
        nthr              = stoi(string(getCmdOption(argv, argv + argc, "-n")));
        config.numthreads = nthr;
    } else {
        nthr = config.numthreads;
    }

    if (cmdOptionExists(argv, argv + argc, "-type")) {
        config.networkType    = string(getCmdOption(argv, argv + argc, "-type"));
        config.vertexFeatures = ((config.networkType == "type1") || (config.networkType == "type3"));
    }

    int batchSize = 2048;
    if (cmdOptionExists(argv, argv + argc, "-batch")) {
        config.batchedFeatures = true;
        batchSize              = stoi(string(getCmdOption(argv, argv + argc, "-batch")));
    } else {
        config.batchedFeatures = false;
    }

    config.suppressOut = false;
    if (cmdOptionExists(argv, argv + argc, "-np"))
        config.suppressOut = true;

    /// Printing the configuration
    cout << " Network Type: " << config.networkType << endl;
    for (int i = 0; i < static_cast<int>(Pattern::SIZE); i++) {
        Pattern pat = static_cast<Pattern>(i);
        if (config.patternExists(pat)) {
            cout << "Pattern: " << PatternNames[i] << endl;
            if (config.timewindows.find(pat) != config.timewindows.end())
                cout << "  Time window size: " << config.timewindows[pat] / 3600 << " h" << endl;
            if (config.maxlengths.find(pat) != config.maxlengths.end())
                cout << "  Max length: " << config.maxlengths[pat] << endl;

            cout << "  Bins (size: " << config.bins[pat].size() << ") ";
            for (auto b : config.bins[pat]) {
                cout << b << " ";
            }
            cout << endl;
        }
    }

/// Reading transaction Graph
#if USE_DYNAMIC_GRAPH == True
    Graph* g = new DynamicGraph;
    if (nullptr == g) {
        return 0;
    }
#else
    Graph* g = new StaticGraph;
#endif

    {
        auto   total_start = chrono::steady_clock::now();
        string extension   = path.substr(path.find_last_of(".") + 1);
        cout << "path: " << path << endl;
        g->readGraph(path);
        auto   total_end = chrono::steady_clock::now();
        double total     = chrono::duration_cast<chrono::milliseconds>(total_end - total_start).count() / 1000.0;
        cout << "Graph read time: " << total << " s" << endl;
    }

    if (cmdOptionExists(argv, argv + argc, "-l")) {
        string labpath = string(getCmdOption(argv, argv + argc, "-l"));
        g->readLabels(labpath);
    }

    config.t0 = 0;
    config.t1 = g->getTotalTime() + 10;
    cout << "Timespan: " << config.t0 << "-" << config.t1 << " (" << (config.t1 - config.t0) / 3600 / 24 << " days)"
         << endl;

    /// Calling feature engineering functions
    computeFeaturesBatched(g, config, batchSize, nthr);

#ifdef PROFILE
    __itt_detach();
#endif

    delete g;

    return 0;
}
