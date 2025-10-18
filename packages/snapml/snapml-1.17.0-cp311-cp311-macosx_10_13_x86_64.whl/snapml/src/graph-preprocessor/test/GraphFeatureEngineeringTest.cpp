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
#include <algorithm>
#include <string>
#include <cstdio>
#include <iostream>

#include "utils.h"
#include "graph.h"
#include "testUtils.h"
#include "outputDataStructures.h"
#include "featureEngineering.h"

using namespace std;

// Global data structures

void init(Graph*& g, runSettings& config, bool silent)
{

    string pathToGraph  = pathToInputDir + "/aml-e_small.txt";
    string pathToLabels = pathToInputDir + "/labels.txt";
    string pathToConfig = pathToInputDir + "/config.dat";

    parseConfigFile(pathToConfig, config);

    config.suppressOut        = false;
    config.base_path          = pathToInputDir;
    config.numthreads         = 12;
    config.useShallowFeatures = false; // This is tested in another test

    if (!silent)
        cout << "Reading the input graph" << endl;
#if USE_DYNAMIC_GRAPH == True
    DynamicGraph* dg = new DynamicGraph;
    initDynamicGraph(dg, config);
    g = dg;
#else
    g = new StaticGraph;
#endif
    g->readGraph(pathToGraph);
    g->readLabels(pathToLabels);
    if (!silent)
        cout << "Reading the input graph - done" << endl;
}

int featureEngineeringTest(Graph* g, runSettings& config, string netType, int batchSize, bool silent = false)
{
    config.networkType = netType;

    if (netType == "type1")
        config.vertexFeatures = true;
    else
        config.vertexFeatures = false;

    string outName = string("output_") + config.networkType + "_accumulated.csv";
    if (batchSize > 0)
        outName = string("output_") + config.networkType + "_batch" + to_string(batchSize) + ".csv";

    string pathToIdeal = pathToIdealDir + "/" + outName;

    PerPatternFeatures idealDF;
    if (!silent)
        cout << " *** Reading the ideal features" << endl;
    readDF(pathToIdeal, idealDF);
    if (!silent)
        cout << " *** Reading the ideal features - done" << endl;

    if (!silent)
        cout << " *** Computing features" << endl;
    if (batchSize <= 0) {
        config.batchedFeatures = false;
        computeFeaturesBatched(g, config, 128, config.numthreads, true);
    } else {
        config.batchedFeatures = true;
        computeFeaturesBatched(g, config, batchSize, config.numthreads, true);
    }

    if (!silent)
        cout << " *** Computing features - done" << endl;

    string pathToComputed = config.base_path + "/" + outName;
    if (!silent)
        cout << " *** Reading the computed features" << endl;
    PerPatternFeatures computedDF;
    readDF(pathToComputed, computedDF);
    if (!silent)
        cout << " *** Reading the computed features - done" << endl;
    remove(pathToComputed.c_str());

    if (!silent)
        cout << " *** Checking the computed features" << endl;
    bool pass = true;
    for (int i = 0; i < (int)(Pattern::SIZE); i++) {
        Pattern pat = (Pattern)(i);

        if (!config.patternExists(pat))
            continue;

        if (!silent)
            cout << "   * Testing " << PatternNames[i] << " features" << endl;

        string error_msg;
        int    status = comparePatternFeatures(idealDF[pat], computedDF[pat], error_msg);

        if (status != 0)
            cout << error_msg << endl;
        assert(status == 0); // , error_msg

        if (status < 0)
            pass = false;
    }
    if (!silent)
        cout << " *** Checking the computed features - done" << endl;
    assert(pass);

    return (pass ? 0 : -1);
}

void checkEdgeList(runSettings& config, int batchSize, bool silent, int windowSize, bool reverse)
{
    config.windowsize         = windowSize;
    config.useShallowFeatures = false;

    DynamicGraph* dg = new DynamicGraph;

    initDynamicGraph(dg, config);

    string path = pathToInputDir + "/aml-e_small_1h.txt";

    if (!silent)
        cout << " *** Reading edge list" << endl;
    vector<vector<double>> edgeList;
    {
        ifstream transFile(path);
        assert((!transFile.fail()));

        while (true) {
            string line;
            getline(transFile, line);
            if (transFile.eof())
                break;

            if (line[0] == '%' || line[0] == '#')
                continue;

            stringstream ss(line);

            vector<double> edgeVec;

            double feat;
            while (ss >> feat) {
                assert((!ss.fail()));
                edgeVec.push_back(feat);
            }

            edgeList.push_back(std::move(edgeVec));
        }

        if (reverse) {
            std::reverse(edgeList.begin(), edgeList.end());
        }
    }
    if (!silent)
        cout << " *** Reading edge list - done" << endl;

    int edgeListSize = edgeList.size();

    int minEdgeThresh = min(windowSize / 10, MIN_EDGE_THRESHOLD);

    if (!silent) {
        cout << " *** Checking edge list correctness" << endl;
        cout << "   * Batch size = " << to_string(batchSize) << endl;
        cout << "   * Window size = " << to_string(windowSize) << endl;
        cout << "   * Reverse = " << to_string(reverse) << endl;
        cout << "   * Timewindow size = " << static_cast<DynamicGraph*>(dg)->getTimeWindow() << " s" << endl;
    }

    for (int startBatchInd = 0; startBatchInd < edgeListSize; startBatchInd += batchSize) {

        int endBatchInd = min((int)(startBatchInd + batchSize - 1), (int)(edgeListSize - 1));

        for (int i = startBatchInd; i <= endBatchInd; i++) {
            GraphElemID edgeID   = edgeList[i][0];
            GraphElemID sourceID = edgeList[i][1];
            GraphElemID targetID = edgeList[i][2];
            Timestamp   tstamp   = edgeList[i][3];

            FeatureVector featVector(edgeList[i].size() - 4);
            for (unsigned int k = 4; k < edgeList[i].size(); k++) {
                featVector[k - 4] = edgeList[i][k];
            }

            dg->addTempEdge(edgeID, tstamp, sourceID, targetID, featVector);
        }

        // An out-of-order edge is an edge that does not have the maximum timestamp among
        // the edges added before it.

        // If more than a half edges are out-of-order, all of the edges are resorted
        bool checkSort = false;
        if (dg->getEdgeNo() > minEdgeThresh) {
            int oooEdges = dg->getNoOutOfOrderEdges();
            if (2 * oooEdges > dg->getEdgeNo()) {
                checkSort = true;
            }
        }

        // The edge list should not be sorted here but after removeOldEdges
        if (checkSort) {
            assert(!dg->isEdgeListSorted());
        }

        dg->removeOldEdges();

        // Check if the number of edges is less than window size
        if (dg->getEdgeNo() > windowSize) {
            cout << "Window size constraint not satisfied: " << dg->getEdgeNo() << " ! <= " << windowSize << endl;
        }
        assert(dg->getEdgeNo() <= windowSize);

        // We create the edges such that less than a half of the edges are out-of-order
        if (dg->getEdgeNo() > minEdgeThresh) {
            int oooEdges = dg->getNoOutOfOrderEdges();
            if (2 * oooEdges > dg->getEdgeNo()) {
                cout << "Number of out-of-order edges is not satisfied: " << 2 * oooEdges << " ! <= " << dg->getEdgeNo()
                     << endl;
            }
            assert(2 * oooEdges <= dg->getEdgeNo());
        }

        // Check if removeOldEdges has resorted the edges
        if (checkSort) {
            assert(dg->isEdgeListSorted());
        }
    }

    delete dg;
}

int main()
{
    Graph*      g = NULL;
    runSettings config;

    bool silent = false;

    if (!silent)
        cout << "pathToIdealDir = " << pathToIdealDir << endl;
    if (!silent)
        cout << "pathToInputDir = " << pathToInputDir << endl;

    init(g, config, silent);

    if (!silent)
        cout << "********** Type 2 feature test for the batch size of 2048 ********* " << endl;
    featureEngineeringTest(g, config, "type2", 2048, silent);
    if (!silent)
        cout << "********** Type 2 feature test for the batch size of 2048 - done ********* " << endl;

    if (!silent)
        cout << "********** Type 2 feature test for the batch size of 128 ********* " << endl;
    featureEngineeringTest(g, config, "type2", 128, silent);
    if (!silent)
        cout << "********** Type 2 feature test for the batch size of 128 - done ********* " << endl;

    if (g)
        delete g;

    vector<int> windowSizes = { 100, 1000, 10000 };

    if (!silent)
        cout << " ********* Checking window size constraint and resorting correctness *********" << endl;
    for (auto ws : windowSizes) {
        runSettings config;
        parseConfigFile(pathToInputDir + "/config.dat", config);

        checkEdgeList(config, 128, silent, ws, false);
        checkEdgeList(config, 128, silent, ws, true);
    }
    if (!silent)
        cout << " ********* Checking window size constraint and resorting correctness - done *********" << endl;
}
