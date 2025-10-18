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

#include "featureEngineering.h"

#include <thread>
#include <utility>
#include <fstream>
#include <iomanip>
#include <algorithm>

#include "utils.h"
#include "graph.h"

#include "GraphFeatures.h"

// These TODOs do not affect python interface
// TODO: shallow features with type3
// TODO: change the name of type3 feature generation
// TODO: dynamic account feature generation is not working properly, fix this
// TODO: change the name of "Is Laundering" column to "Is Phishing" for ethereum

namespace {
inline void reportFeatureEngineeringTimes(runSettings& config)
{
    cout << "**************** Running Times ****************" << endl;
    cout << "Feature extraction time: " << config.totalProcessingTime << "s" << endl;

    if (config.patternExists(Pattern::FanIn) || config.patternExists(Pattern::FanOut)
        || config.patternExists(Pattern::DegIn) || config.patternExists(Pattern::DegOut)) {
        cout << "------------------------------------------------" << endl;
        cout << "Fans/degrees time window: " << config.timewindows[Pattern::FanIn] / 3600 << "h" << endl;
        cout << "Fans/degrees time: " << config.processingTime[Pattern::FanIn] << " s" << endl;
    }
    if (config.patternExists(Pattern::ScatGat)) {
        cout << "------------------------------------------------" << endl;
        cout << "Scatter Gather time window: " << config.timewindows[Pattern::ScatGat] / 3600 << "h" << endl;
        cout << "Scatter Gather time: " << config.processingTime[Pattern::ScatGat] << " s" << endl;
    }
    if (config.patternExists(Pattern::TempCycle)) {
        cout << "------------------------------------------------" << endl;
        cout << "Temporal cycle window: " << config.timewindows[Pattern::TempCycle] / 3600 << "h" << endl;
        cout << "Temporal cycle time: " << config.processingTime[Pattern::TempCycle] << " s" << endl;
    }
    if (config.patternExists(Pattern::LCCycle)) {
        cout << "------------------------------------------------" << endl;
        cout << "Length-constrained cycle window: " << config.timewindows[Pattern::LCCycle] / 3600 << "h" << endl;
        cout << "Maximum cycle size: " << config.maxlengths[Pattern::LCCycle] << endl;
        cout << "Length-constrained cycle time: " << config.processingTime[Pattern::LCCycle] << " s" << endl;
    }
    if (config.patternExists(Pattern::Biclique)) {
        cout << "------------------------------------------------" << endl;
        cout << "Biclique time window: " << config.timewindows[Pattern::Biclique] / 3600 << "h" << endl;
        cout << "Biclique time: " << config.processingTime[Pattern::Biclique] << " s" << endl;
    }
    if (config.patternExists(Pattern::Clique)) {
        cout << "------------------------------------------------" << endl;
        cout << "Clique time: " << config.processingTime[Pattern::Clique] << " s" << endl;
    }
    if (config.useShallowFeatures) {
        cout << "------------------------------------------------" << endl;
        cout << "Shallow feature computation time: " << config.shallowProcTime << " s" << endl;
    }
    cout << "------------------------------------------------" << endl;
    cout << "Postprocessing time: " << config.postprocessingTime << " s" << endl;

    if (!config.suppressOut) {
        cout << "------------------------------------------------" << endl;
        cout << "TIme to write to file: " << config.printingTime << " s" << endl;
    }
    cout << "------------------------------------------------" << endl;
}

inline void reportTransactionPerSecond(runSettings& config)
{
    cout << "**************** Transactions per second ****************" << endl;
    if (config.patternExists(Pattern::FanIn) || config.patternExists(Pattern::FanOut)
        || config.patternExists(Pattern::DegIn) || config.patternExists(Pattern::DegOut)) {
        cout << "------------------------------------------------" << endl;
        unsigned long avgFanTps = config.transNum / config.processingTime[Pattern::FanIn];
        cout << "Fans/degrees average tps: " << avgFanTps << endl;
    }
    if (config.patternExists(Pattern::ScatGat)) {
        cout << "------------------------------------------------" << endl;
        unsigned long avgSgTps = config.transNum / config.processingTime[Pattern::ScatGat];
        cout << "Scatter Gather average tps: " << avgSgTps << endl;
    }
    if (config.patternExists(Pattern::TempCycle)) {
        cout << "------------------------------------------------" << endl;
        unsigned long avgCycTps = config.transNum / config.processingTime[Pattern::TempCycle];
        cout << "Temporal cycle average tps: " << avgCycTps << endl;
    }
    if (config.patternExists(Pattern::LCCycle)) {
        cout << "------------------------------------------------" << endl;
        unsigned long avgCycTps = config.transNum / config.processingTime[Pattern::LCCycle];
        cout << "Length-constrained cycle average tps: " << avgCycTps << endl;
    }
    if (config.patternExists(Pattern::Biclique)) {
        cout << "------------------------------------------------" << endl;
        unsigned long avgBcTps = config.transNum / config.processingTime[Pattern::ScatGat];
        cout << "Biclique average tps: " << avgBcTps << endl;
    }
    if (config.patternExists(Pattern::Clique)) {
        cout << "------------------------------------------------" << endl;
        unsigned long avgClqTps = config.transNum / config.processingTime[Pattern::Clique];
        cout << "Clique average tps: " << avgClqTps << endl;
    }
    if (config.useShallowFeatures) {
        cout << "------------------------------------------------" << endl;
        unsigned long avgShTps = config.transNum / config.shallowProcTime;
        cout << "Shallow feature computation average tps: " << avgShTps << endl;
    }
    cout << "------------------------------------------------" << endl;
    unsigned long avgPprocTps = config.transNum / config.postprocessingTime;
    cout << "Postprocessing average tps: " << avgPprocTps << endl;
    cout << "------------------------------------------------" << endl;
    unsigned long avgTotalTps = config.transNum / config.totalProcessingTime;
    cout << "Overall average tps: " << avgTotalTps << endl;
    cout << "------------------------------------------------" << endl;
}
}

void writeHeader(std::ofstream& outputData, runSettings& config, vector<string>& rawEdgeFeatureNames, bool printLabels)
{
    // raw features
    if (config.networkType == "type1") {
        outputData << "NodeID";
    } else if (config.networkType == "type2" || config.networkType == "type3") {
        outputData << "EdgeID,SourceVertexID,DestinationVertexID,Timestamp";

        for (auto name : rawEdgeFeatureNames) {
            outputData << "," << name;
        }
    }

    // Engineered features

    if (config.networkType == "type1" || config.networkType == "type2") {
        for (int i = 0; i < static_cast<int>(Pattern::SIZE); i++) {
            Pattern pat = static_cast<Pattern>(i);
            if (config.patternExists(pat)) {
                outputData << ",";
                for (unsigned int j = 0; j < config.bins[pat].size() - 1; j++) {
                    outputData << PatternNames[i] << " [" << config.bins[pat][j] << ":" << config.bins[pat][j + 1]
                               << "),";
                }
                // Write the last bin
                outputData << PatternNames[i] << " [" << config.bins[pat].back() << ":inf)";
            }
        }
    }

    if (config.networkType == "type3") {
        for (int i = 0; i < 2; i++) {
            string prefix = (i == 0) ? "Source " : "Destination ";
            for (int i = 0; i < static_cast<int>(Pattern::SIZE); i++) {
                Pattern pat = static_cast<Pattern>(i);
                if (config.patternExists(pat)) {
                    outputData << ",";
                    for (unsigned int j = 0; j < config.bins[pat].size() - 1; j++) {
                        outputData << prefix << PatternNames[i] << " [" << config.bins[pat][j] << ":"
                                   << config.bins[pat][j + 1] << "),";
                    }
                    // Write the last bin
                    outputData << prefix << PatternNames[i] << " [" << config.bins[pat].back() << ":inf)";
                }
            }
        }
    }

    // Shallow features
    // TODO: Write correctly the feature names
    if (config.useShallowFeatures) {
        vector<string> headers = getStatFeatureNames(config);

        outputData << ", ";
        if (config.networkType == "type1") {
            // Write header
            for (unsigned int i = 0; i < headers.size(); i++) {
                outputData << headers[i];
                if (i != headers.size() - 1)
                    outputData << ",";
            }
        } else {
            for (unsigned int i = 0; i < headers.size(); i++) {
                outputData << "Source " << headers[i] << ",";
            }
            for (unsigned int i = 0; i < headers.size(); i++) {
                outputData << "Destination " << headers[i];
                if (i != headers.size() - 1)
                    outputData << ",";
            }
        }
    }

    // Labels
    if ((config.networkType == "type2" || config.networkType == "type3") && printLabels) {
        outputData << ", Is Laundering";
    }
    outputData << endl;
}

void writeFeature(std::ofstream& outputData, std::unordered_map<int, int> featureData, int featureSize)
{
    for (int i = 0; i < featureSize; i++) {
        outputData << "," << featureData[i];
    }
}

int getNumFeats(runSettings& config)
{
    int numPatternFeats = 0;

    for (int i = 0; i < static_cast<int>(Pattern::SIZE); i++) {
        Pattern pat = static_cast<Pattern>(i);
        if (config.patternExists(pat)) {
            numPatternFeats += config.bins[pat].size();
        }
    }

    return numPatternFeats;
}

void writeData(std::ofstream& outputData, Graph* g, DataFrame& nodeDF, ShallowFeatureTable featTable,
               runSettings& config, pair<int, int> batch)
{
    auto io_startDF = chrono::steady_clock::now();

    unordered_set<int>      processedRows;
    unordered_map<int, int> vidToRowMap;
    if (config.batchedFeatures) {
        for (unsigned int i = 0; i < featTable.size(); i++) {
            int vid          = featTable[i].first;
            vidToRowMap[vid] = i;
        }
    }

    // Process the rows with subgraph features
    for (auto& pair : nodeDF) {
        int   node  = pair.first;
        auto& feats = pair.second;

        processedRows.insert(node);

        if (config.networkType == "type1") {
            outputData << g->getVertex(node)->getID();
        } else if (config.networkType == "type2") {
            auto eind      = g->edgeIdMap[node];
            auto transInfo = g->getEdge(eind);
            outputData << transInfo->getID() << "," << transInfo->getSourceVertexID() << ","
                       << transInfo->getTargetVertexID() << "," << transInfo->getTStamp();

            for (unsigned int k = 0; k < transInfo->getNumRawFeats(); k++) {
                double feat = transInfo->getRawFeat(k);
                outputData << "," << feat;
            }
        }

        for (int i = 0; i < static_cast<int>(Pattern::SIZE); i++) {
            Pattern pat = static_cast<Pattern>(i);
            if (config.patternExists(pat)) {
                writeFeature(outputData, feats.patternBins[pat], config.bins[pat].size());
            }
        }

        // Shallow features
        if (config.useShallowFeatures) {
            if (config.networkType == "type1") {
                int row = node;
                if (config.batchedFeatures)
                    row = vidToRowMap[node];

                auto& tmptable = featTable[row];
                for (unsigned int i = 0; i < tmptable.second.size(); i++) {
                    auto val = tmptable.second[i];
                    outputData << "," << setprecision(20) << val;
                }
            } else {
                // Write source and destination vertex features
                auto eind      = g->edgeIdMap[node];
                auto transInfo = g->getEdge(eind);
                for (int rep = 0; rep < 2; rep++) {
                    int vert = (rep == 0) ? transInfo->getSourceVertexIndex() : transInfo->getTargetVertexIndex();

                    int row = vert;
                    if (config.batchedFeatures)
                        row = vidToRowMap[vert];

                    auto& tmptable = featTable[row];
                    for (unsigned int i = 0; i < tmptable.second.size(); i++) {
                        auto val = tmptable.second[i];
                        outputData << "," << setprecision(20) << val;
                    }
                }
            }
        }

        if (config.networkType == "type2") {
            auto eind      = g->edgeIdMap[node];
            auto transInfo = g->getEdge(eind);
            outputData << "," << transInfo->getLabel();
        }
        outputData << endl;
    }

    int numPatternFeats = getNumFeats(config);

    // Process the rest of the rows

    if (config.networkType == "type1" && config.batchedFeatures == true) {

        outputData << "##### END OF BATCH #####" << endl;
    } else {
        for (int node = batch.first; node < batch.second + 1; node++) {
            if (processedRows.find(node) != processedRows.end())
                continue;

            if (config.networkType == "type1") {
                outputData << g->getVertex(node)->getID();
            } else if (config.networkType == "type2") {
                auto eind      = g->edgeIdMap[node];
                auto transInfo = g->getEdge(eind);
                outputData << transInfo->getID() << "," << transInfo->getSourceVertexID() << ","
                           << transInfo->getTargetVertexID() << "," << transInfo->getTStamp();

                for (unsigned int k = 0; k < transInfo->getNumRawFeats(); k++) {
                    double feat = transInfo->getRawFeat(k);
                    outputData << "," << feat;
                }
            }

            // Print zeros for other patterns
            for (int i = 0; i < numPatternFeats; i++) {
                outputData << "," << 0;
            }

            // Shallow features
            if (config.useShallowFeatures) {
                if (config.networkType == "type1") {
                    int row = node;
                    if (config.batchedFeatures)
                        row = vidToRowMap[node];

                    auto& tmptable = featTable[row];
                    for (unsigned int i = 0; i < tmptable.second.size(); i++) {
                        auto val = tmptable.second[i];
                        outputData << "," << val;
                    }
                } else {
                    // Write source and destination vertex features
                    auto eind      = g->edgeIdMap[node];
                    auto transInfo = g->getEdge(eind);
                    for (int rep = 0; rep < 2; rep++) {
                        int vert = (rep == 0) ? transInfo->getSourceVertexIndex() : transInfo->getTargetVertexIndex();

                        int row = vert;
                        if (config.batchedFeatures)
                            row = vidToRowMap[vert];

                        auto& tmptable = featTable[row];
                        for (unsigned int i = 0; i < tmptable.second.size(); i++) {
                            auto val = tmptable.second[i];
                            outputData << "," << val;
                        }
                    }
                }
            }

            // Labels
            if (config.networkType == "type2") {
                auto eind      = g->edgeIdMap[node];
                auto transInfo = g->getEdge(eind);
                outputData << "," << transInfo->getLabel();
            }
            outputData << endl;
        }
    }

    auto   io_endDF   = chrono::steady_clock::now();
    double io_totalDF = chrono::duration_cast<chrono::milliseconds>(io_endDF - io_startDF).count() / 1000.0;
    config.printingTime += io_totalDF;
}

void writeType3Data(std::ofstream& outputData, Graph* g, DataFrame& nodeDF, runSettings& config, pair<int, int> batch)
{
    auto io_startDF = chrono::steady_clock::now();

    // vertexDF indexing
    unordered_map<int, int> indexToRowMap;
    int                     rowNum = 0;
    for (auto& pair : nodeDF) {
        int node            = pair.first;
        indexToRowMap[node] = rowNum;
        rowNum++;
    }

    int startBatchInd = batch.first;
    int endBatchInd   = batch.second;

    unordered_set<int> processedRows;

    int numPatternFeats = getNumFeats(config);

    // Process the rows with subgraph features
    for (int i = startBatchInd; i <= endBatchInd; i++) {
        int edgeIndex = i;

        processedRows.insert(edgeIndex);

        auto transInfo = g->getEdge(edgeIndex);
        outputData << transInfo->getID() << "," << transInfo->getSourceVertexID() << ","
                   << transInfo->getTargetVertexID() << "," << transInfo->getTStamp();

        for (unsigned int k = 0; k < transInfo->getNumRawFeats(); k++) {
            double feat = transInfo->getRawFeat(k);
            outputData << "," << feat;
        }

        // Write source and destination vertex features
        for (int i = 0; i < 2; i++) {
            int vertIndex = (i == 0) ? transInfo->getSourceVertexIndex() : transInfo->getTargetVertexIndex();

            bool found = indexToRowMap.find(vertIndex) != indexToRowMap.end();

            if (found) {
                auto& vertfeats = nodeDF[indexToRowMap[vertIndex]].second;

                for (int i = 0; i < static_cast<int>(Pattern::SIZE); i++) {
                    Pattern pat = static_cast<Pattern>(i);
                    if (config.patternExists(pat)) {
                        writeFeature(outputData, vertfeats.patternBins[pat], config.bins[pat].size());
                    }
                }
            } else {
                for (int i = 0; i < numPatternFeats; i++) {
                    outputData << "," << 0;
                }
            }
        }

        // Write the label
        outputData << "," << transInfo->getLabel();
        outputData << endl;
    }

    auto   io_endDF   = chrono::steady_clock::now();
    double io_totalDF = chrono::duration_cast<chrono::milliseconds>(io_endDF - io_startDF).count() / 1000.0;
    config.printingTime += io_totalDF;
}

#if USE_DYNAMIC_GRAPH == True
void computeFeaturesDynamicAPI(vector<vector<double>>& edgeList, string config_file, string graph_path, int batchSize,
                               bool silent, string outPath, unordered_map<GraphElemID, int> labels)
{

    bool printFeatures = (outPath != "");

    std::ofstream outputData;
    bool          isOutputDataValid = true; // Flag to track if file is open and valid for writing
    if (printFeatures) {
        if (!silent)
            cout << "output file location: " << outPath << endl;
        outputData.open(outPath);
        if (!outputData.is_open()) {
            cerr << "Error: Unable to open file: " << outPath << endl;
            isOutputDataValid = false; // Set flag to false if file cannot be opened
        } else {
            vector<string> rawEdgeFeatureNames;
            for (unsigned int i = 4; i < edgeList[0].size(); i++) {
                string fname = "RawFeat" + to_string(i);
                rawEdgeFeatureNames.push_back(fname);
            }
            runSettings config;
            parseConfigFile(config_file, config);
            config.networkType        = "type2";
            config.useShallowFeatures = true;
            writeHeader(outputData, config, rawEdgeFeatureNames, (labels.size() != 0));
        }
    }

    GraphFeatures::GraphFeaturePreprocessor gp;

    gp.loadConfigFile(config_file);

    if (graph_path != "") {
        vector<vector<double>> edgeList;
        ifstream               transFile(graph_path);

        while (true) {
            string line;
            getline(transFile, line);
            if (transFile.eof())
                break;

            if (line[0] == '%' || line[0] == '#')
                continue;

            stringstream ss(line);

            vector<double> edgeVec;

            if (graph_path.substr(graph_path.find_last_of(".") + 1) == "csv") {
                std::string substr;
                while (std::getline(ss, substr, ',')) {
                    if (!substr.empty()) { // Check if the substring is not empty
                        try {
                            double feat = std::stod(substr);
                            edgeVec.push_back(feat);
                        } catch (const std::exception& e) {
                            std::cerr << "Conversion error for value: " << substr << " - " << e.what() << std::endl;
                        }
                    }
                }
            } else {
                double feat;
                while (ss >> feat) {
                    edgeVec.push_back(feat);
                }
            }

            edgeList.push_back(std::move(edgeVec));
        }
        uint64_t num_edges    = edgeList.size();
        uint64_t num_features = (num_edges == 0) ? 0 : edgeList[0].size();
        double*  features     = new double[num_edges * num_features];
        for (unsigned int i = 0; i < num_edges; i++) {
            for (unsigned int k = 0; k < num_features; k++) {
                features[i * num_features + k] = edgeList[i][k];
            }
        }
        gp.loadGraph(features, num_edges, num_features);

        delete[] features;
    }

    int edgeListSize = edgeList.size();

    int batchNo = 0;

    uint64_t num_features_in  = edgeList[0].size();
    uint64_t num_features_out = gp.getNumEngineeredFeatures() + num_features_in;

    double* features_in  = new double[num_features_in * batchSize];
    double* features_out = new double[num_features_out * batchSize];
    // PROCESS THE PATTERNS
    auto processing_start = chrono::high_resolution_clock::now();
    for (int startBatchInd = 0; startBatchInd < edgeListSize; startBatchInd += batchSize) {

        int endBatchInd = std::min(static_cast<int>(startBatchInd + batchSize - 1), static_cast<int>(edgeListSize - 1));

        int bi = 0;
        for (int i = startBatchInd; i <= endBatchInd; i++) {

            for (unsigned int j = 0; j < num_features_in; j++) {
                features_in[bi * num_features_in + j] = edgeList[i][j];
            }

            bi++;
        }

        int thisBatchSize = endBatchInd + 1 - startBatchInd;

        gp.enrichFeatureVectors(thisBatchSize, features_in, num_features_in, features_out, num_features_out);

        if (printFeatures && isOutputDataValid) {
            int bi = 0;
            for (int i = startBatchInd; i <= endBatchInd; i++) {
                double* thisFeaturesOut = &(features_out[bi * num_features_out]);

                for (unsigned int j = 0; j < num_features_out; j++) {
                    if (j < 4) {
                        long outVal = thisFeaturesOut[j];
                        outputData << outVal;
                    } else {
                        outputData << setprecision(20) << thisFeaturesOut[j];
                    }
                    if (j != num_features_out - 1)
                        outputData << ",";
                }

                if (labels.size() != 0) {
                    outputData << "," << labels[thisFeaturesOut[0]];
                }

                outputData << endl;

                bi++;
            }
        }

        batchNo++;

        if (!silent && batchNo % 10000 == 0) {
            cout << "----------------------------------------------" << endl;
            auto   processing_end = chrono::high_resolution_clock::now();
            double execTime = chrono::duration_cast<chrono::milliseconds>(processing_end - processing_start).count();
            cout << "Processed transactions: " << batchNo * batchSize << endl;
            cout << "Feature engineering latency: " << (execTime / batchNo) << " ms" << endl;
            cout << "Throughput: " << (1000.0 * batchNo * batchSize / execTime) << " trans/s" << endl;
        }
    }
    auto   processing_end = chrono::high_resolution_clock::now();
    double totalProcTime
        = chrono::duration_cast<chrono::milliseconds>(processing_end - processing_start).count() / 1000.0;

    delete[] features_in;
    delete[] features_out;

    if (!silent)
        cout << "Total processing time: " << totalProcTime << " s" << endl;

    unsigned long overallTps = edgeListSize / totalProcTime;
    if (!silent)
        cout << "Overall average tps: " << overallTps << endl;
}
#endif

void computeFeaturesBatched(Graph* g, runSettings& config, int batchSize, int nthr, bool silent)
{

#ifndef USE_TBB
    omp_set_num_threads(nthr);
#else
    task_scheduler_init init(nthr);
#endif

    Timestamp tw = 0;
    for (int i = 0; i < static_cast<int>(Pattern::SIZE); i++) {
        Pattern pat = static_cast<Pattern>(i);
        if (config.patternExists(pat)) {
            tw = max(tw, config.timewindows[pat]);
        }
    }

    std::ofstream outputData;
    bool          isOutputDataExists = true;
    if (!config.suppressOut) {
        string outputDataFile;
        if (config.batchedFeatures) {
            outputDataFile
                = config.base_path + "/output_" + config.networkType + "_batch" + to_string(batchSize) + ".csv";
        } else {
            outputDataFile = config.base_path + "/output_" + config.networkType + "_accumulated.csv";
        }

        if (!silent)
            cout << "output file location: " << outputDataFile << endl;
        outputData.open(outputDataFile);
        if (!outputData.is_open()) {
            cerr << "Error: Unable to open file: " << outputDataFile << endl;
            isOutputDataExists = false; // Set flag to false if file cannot be opened
        } else {
            vector<string> rawFeatNames = g->getRawFeatNames();
            writeHeader(outputData, config, rawFeatNames);
        }
    }

    unsigned long dfSize       = 0;
    int           edgeListSize = g->getEdgeNo();

    config.transNum = edgeListSize;

    double totalProcTime = 0;

    // Initialize batched cycle enumeration

    DynamicCycleFinder cycleFinder(g, config);

    int bigBatchNum  = 100;
    int bigBatchSize = edgeListSize / bigBatchNum;

    bigBatchSize = (bigBatchSize / batchSize) * batchSize;
    if (bigBatchSize == 0)
        bigBatchSize = batchSize;

    if (!silent)
        cout << "Big batch size = " << bigBatchSize << endl;

    PerThreadDataFrame  globalDF(nthr);
    ShallowFeatureTable globalFeatTable;

    // BIG BATCH
    auto processing_start = chrono::high_resolution_clock::now();
    for (int ind = 0; ind < edgeListSize; ind += bigBatchSize) {

        int numSmallBatches = bigBatchSize / batchSize;

        if (!silent)
            cout << "numSmallBatches = " << numSmallBatches << endl;
        vector<PerThreadDataFrame>  ptNodeDF_ptr(numSmallBatches, PerThreadDataFrame(nthr));
        vector<ShallowFeatureTable> featTable_ptr(numSmallBatches);

        int startInd = ind;
        int endInd   = std::min(static_cast<int>(startInd + bigBatchSize - 1), static_cast<int>(edgeListSize - 1));

        // FAN-IN/FAN-OUT
        if (config.patternExists(Pattern::FanIn) || config.patternExists(Pattern::FanOut)
            || config.patternExists(Pattern::DegIn) || config.patternExists(Pattern::DegOut)) {
            auto timer_start = chrono::high_resolution_clock::now();
            for (int startBatchInd = startInd; startBatchInd <= endInd; startBatchInd += batchSize) {
                int                 dfInd    = (startBatchInd - startInd) / batchSize;
                PerThreadDataFrame& ptNodeDF = (config.batchedFeatures) ? ptNodeDF_ptr[dfInd] : globalDF;

                int endBatchInd
                    = std::min(static_cast<int>(startBatchInd + batchSize - 1), static_cast<int>(edgeListSize - 1));

                vector<GraphElemID> localEdgeIDs;
                localEdgeIDs.reserve(endBatchInd - startBatchInd + 1);
                for (int i = startBatchInd; i <= endBatchInd; i++) {
                    GraphElemID eid = g->edgeIdMap[i];
                    localEdgeIDs.push_back(eid);
                }
                computeFanDegBatchAPI(g, ptNodeDF, config, localEdgeIDs);
            }
            auto   timer_end = chrono::high_resolution_clock::now();
            double total     = chrono::duration_cast<chrono::milliseconds>(timer_end - timer_start).count();
            config.processingTime[Pattern::FanIn] += total;
            config.processingTime[Pattern::FanOut] += total;
            config.processingTime[Pattern::DegIn] += total;
            config.processingTime[Pattern::DegOut] += total;
            totalProcTime += total;
        }

        // Shallow statistical features
        if (config.useShallowFeatures && config.batchedFeatures) {
            auto timer_start = chrono::high_resolution_clock::now();
            for (int startBatchInd = startInd; startBatchInd <= endInd; startBatchInd += batchSize) {
                int                  dfInd  = (startBatchInd - startInd) / batchSize;
                ShallowFeatureTable& ftable = featTable_ptr[dfInd];

                int endBatchInd
                    = std::min(static_cast<int>(startBatchInd + batchSize - 1), static_cast<int>(edgeListSize - 1));

                Timestamp fromTs = std::numeric_limits<Timestamp>::max(), toTs = -1;

                set<int>    localVertexSet;
                vector<int> localVertexIDs;
                for (int i = startBatchInd; i <= endBatchInd; i++) {
                    int fromV = g->getEdge(i)->getSourceVertexIndex();
                    int toV   = g->getEdge(i)->getTargetVertexIndex();
                    localVertexSet.insert(fromV);
                    localVertexSet.insert(toV);

                    toTs   = max(toTs, g->getEdge(i)->getTStamp());
                    fromTs = min(fromTs, g->getEdge(i)->getTStamp());
                }
                fromTs = max(0, fromTs - tw);
                localVertexIDs.reserve(localVertexSet.size());
                for (auto el : localVertexSet)
                    localVertexIDs.push_back(el);

                computeVertexStatisticsFeatures(g, ftable, config, localVertexIDs, make_pair(fromTs, toTs));
            }
            auto   timer_end = chrono::high_resolution_clock::now();
            double total     = chrono::duration_cast<chrono::milliseconds>(timer_end - timer_start).count();
            config.shallowProcTime += total;
            totalProcTime += total;
        }

        // SCATTER-GATHER
        if (config.patternExists(Pattern::ScatGat)) {
            auto timer_start = chrono::high_resolution_clock::now();
            for (int startBatchInd = startInd; startBatchInd <= endInd; startBatchInd += batchSize) {
                int                 dfInd    = (startBatchInd - startInd) / batchSize;
                PerThreadDataFrame& ptNodeDF = (config.batchedFeatures) ? ptNodeDF_ptr[dfInd] : globalDF;

                int endBatchInd
                    = std::min(static_cast<int>(startBatchInd + batchSize - 1), static_cast<int>(edgeListSize - 1));

                vector<GraphElemID> localEdgeIDs;
                localEdgeIDs.reserve(endBatchInd - startBatchInd + 1);
                for (int i = startBatchInd; i <= endBatchInd; i++) {
                    GraphElemID eid = g->edgeIdMap[i];
                    localEdgeIDs.push_back(eid);
                }

                computeScatterGatherBatchAPI(g, ptNodeDF, config, localEdgeIDs);
            }
            auto   timer_end = chrono::high_resolution_clock::now();
            double total     = chrono::duration_cast<chrono::milliseconds>(timer_end - timer_start).count();
            config.processingTime[Pattern::ScatGat] += total;
            totalProcTime += total;
        }

        // TEMPORAL CYCLES
        if (config.patternExists(Pattern::TempCycle)) {
            auto timer_start = chrono::high_resolution_clock::now();
            for (int startBatchInd = startInd; startBatchInd <= endInd; startBatchInd += batchSize) {
                int                 dfInd    = (startBatchInd - startInd) / batchSize;
                PerThreadDataFrame& ptNodeDF = (config.batchedFeatures) ? ptNodeDF_ptr[dfInd] : globalDF;

                int endBatchInd
                    = std::min(static_cast<int>(startBatchInd + batchSize - 1), static_cast<int>(edgeListSize - 1));

                vector<GraphElemID> localEdgeIDs;
                localEdgeIDs.reserve(endBatchInd - startBatchInd + 1);
                for (int i = startBatchInd; i <= endBatchInd; i++) {
                    GraphElemID eid = g->edgeIdMap[i];
                    localEdgeIDs.push_back(eid);
                }

                cycleFinder.computeTempCyclesBatchAPI(localEdgeIDs, ptNodeDF, nthr);
            }
            auto   timer_end = chrono::high_resolution_clock::now();
            double total     = chrono::duration_cast<chrono::milliseconds>(timer_end - timer_start).count();
            config.processingTime[Pattern::TempCycle] += total;
            totalProcTime += total;
        }

        // LENGTH-CONSTRAINED SIMPLE CYCLES
        if (config.patternExists(Pattern::LCCycle)) {
            auto timer_start = chrono::high_resolution_clock::now();
            for (int startBatchInd = startInd; startBatchInd <= endInd; startBatchInd += batchSize) {
                int                 dfInd    = (startBatchInd - startInd) / batchSize;
                PerThreadDataFrame& ptNodeDF = (config.batchedFeatures) ? ptNodeDF_ptr[dfInd] : globalDF;

                int endBatchInd
                    = std::min(static_cast<int>(startBatchInd + batchSize - 1), static_cast<int>(edgeListSize - 1));

                vector<GraphElemID> localEdgeIDs;
                localEdgeIDs.reserve(endBatchInd - startBatchInd + 1);
                for (int i = startBatchInd; i <= endBatchInd; i++) {
                    GraphElemID eid = g->edgeIdMap[i];
                    localEdgeIDs.push_back(eid);
                }

                cycleFinder.computeLCCyclesBatchAPI(localEdgeIDs, ptNodeDF, nthr);
            }
            auto   timer_end = chrono::high_resolution_clock::now();
            double total     = chrono::duration_cast<chrono::milliseconds>(timer_end - timer_start).count();
            config.processingTime[Pattern::LCCycle] += total;
            totalProcTime += total;
        }

        // POSTPROCESSING
        if (config.batchedFeatures == true) {
            auto timer_start = chrono::high_resolution_clock::now();
            for (int startBatchInd = startInd; startBatchInd <= endInd; startBatchInd += batchSize) {
                int                  dfInd    = (startBatchInd - startInd) / batchSize;
                PerThreadDataFrame&  ptNodeDF = (config.batchedFeatures) ? ptNodeDF_ptr[dfInd] : globalDF;
                ShallowFeatureTable& ftable   = (config.batchedFeatures) ? featTable_ptr[dfInd] : globalFeatTable;

                int endBatchInd
                    = std::min(static_cast<int>(startBatchInd + batchSize - 1), static_cast<int>(edgeListSize - 1));

                vector<GraphElemID> localEdgeIDs;
                localEdgeIDs.reserve(endBatchInd - startBatchInd + 1);
                for (int i = startBatchInd; i <= endBatchInd; i++) {
                    GraphElemID eid = g->edgeIdMap[i];
                    localEdgeIDs.push_back(eid);
                }

                DataFrame tempNodeDF;
                if (config.vertexFeatures == false) {
                    ptNodeDF.combineAPI(tempNodeDF, localEdgeIDs);
                } else {
                    unordered_set<int>  setVertexIDs;
                    vector<GraphElemID> localVertexIDs;
                    for (int i = startBatchInd; i <= endBatchInd; i++) {
                        int fromV = g->getEdge(i)->getSourceVertexIndex();
                        int toV   = g->getEdge(i)->getTargetVertexIndex();
                        setVertexIDs.insert(fromV);
                        setVertexIDs.insert(toV);
                    }
                    localVertexIDs.reserve(setVertexIDs.size());
                    for (auto el : setVertexIDs)
                        localVertexIDs.push_back(el);
                    ptNodeDF.combineAPI(tempNodeDF, localVertexIDs);
                }

                dfSize += tempNodeDF.size();

                if (!config.suppressOut && isOutputDataExists) {
                    if (config.networkType == "type3") {
                        writeType3Data(outputData, g, tempNodeDF, config, { startBatchInd, endBatchInd });
                    } else {
                        writeData(outputData, g, tempNodeDF, ftable, config, { startBatchInd, endBatchInd });
                    }
                }
            }
            auto   timer_end = chrono::high_resolution_clock::now();
            double total     = chrono::duration_cast<chrono::milliseconds>(timer_end - timer_start).count();
            config.postprocessingTime += total;
            totalProcTime += total;
        }

        if (!silent) {
            int endBatchInd = std::min(static_cast<int>(startInd + batchSize - 1), static_cast<int>(edgeListSize - 1));
            cout << "----------------------------------------------" << endl;
            auto   processing_end = chrono::high_resolution_clock::now();
            double execTime = chrono::duration_cast<chrono::milliseconds>(processing_end - processing_start).count();
            cout << "Processed transactions: " << endBatchInd << endl;
            cout << "Throughput: " << (1000.0 * endBatchInd / execTime) << " trans/s" << endl;
            cout << "Execution time per pattern: " << endl;
            if (config.patternExists(Pattern::FanIn)) {
                cout << "    Fans/degrees: " << (config.processingTime[Pattern::FanIn] / 1000.0) << " s" << endl;
            }
            if (config.patternExists(Pattern::ScatGat)) {
                cout << "    Scatter-Gather: " << (config.processingTime[Pattern::ScatGat] / 1000.0) << " s" << endl;
            }
            if (config.patternExists(Pattern::TempCycle)) {
                cout << "    Temporal cycle: " << (config.processingTime[Pattern::TempCycle] / 1000.0) << " s" << endl;
            }
            if (config.patternExists(Pattern::LCCycle)) {
                cout << "    HC cycle: " << (config.processingTime[Pattern::TempCycle] / 1000.0) << " s" << endl;
            }
            cout << "Postprocessing time: " << config.postprocessingTime << " s" << endl;
        }
    }

    // Shallow statistical features - accumulated features
    if (config.useShallowFeatures && !config.batchedFeatures) {
        auto timer_start = chrono::high_resolution_clock::now();

        if (!silent)
            cout << "Computation of static shallow features: " << endl;
        computeVertexStatisticsFeatures(g, globalFeatTable, config);

        auto   timer_end = chrono::high_resolution_clock::now();
        double total     = chrono::duration_cast<chrono::milliseconds>(timer_end - timer_start).count();
        config.shallowProcTime += total;
        totalProcTime += total;
    }

    // POSTPROCESSING - accumulated vertex features
    if (config.batchedFeatures == false) {
        auto timer_start = chrono::high_resolution_clock::now();

        if (!silent)
            cout << "GLOBAL POSTPROCESSING" << endl;

        DataFrame resNodeDF;

        if (config.vertexFeatures == false) {
            globalDF.combine(resNodeDF, edgeListSize);
        } else {
            globalDF.combine(resNodeDF, g->getVertexNo());
        }

        dfSize = resNodeDF.size();

        if (!silent)
            cout << "Total number of edges: " << edgeListSize << endl;
        if (!silent)
            cout << "Total number of vertices: " << g->getVertexNo() << endl;
        if (!config.suppressOut && isOutputDataExists) {
            if (config.networkType == "type3") {
                if (!silent)
                    cout << "resNodeDF size after combining: " << dfSize << endl;
                writeType3Data(outputData, g, resNodeDF, config, { 0, edgeListSize - 1 });
            } else {
                if (config.networkType == "type2") {
                    if (!silent)
                        cout << "resNodeDF size after combining: " << dfSize << endl;
                    writeData(outputData, g, resNodeDF, globalFeatTable, config, { 0, edgeListSize - 1 });
                } else {
                    if (!silent)
                        cout << "resNodeDF size after combining: " << dfSize << endl;
                    writeData(outputData, g, resNodeDF, globalFeatTable, config, { 0, g->getVertexNo() - 1 });
                }
            }
        }

        auto   timer_end = chrono::high_resolution_clock::now();
        double total     = chrono::duration_cast<chrono::milliseconds>(timer_end - timer_start).count();
        config.postprocessingTime += total;
        totalProcTime += total;
    }

    auto processing_end        = chrono::high_resolution_clock::now();
    config.totalProcessingTime = totalProcTime;

    for (int i = 0; i < static_cast<int>(Pattern::SIZE); i++) {
        config.processingTime[static_cast<Pattern>(i)] /= 1000.0;
    }
    config.shallowProcTime /= 1000.0;
    config.postprocessingTime /= 1000.0;
    config.totalProcessingTime /= 1000.0;

    if (!silent)
        cout << "Total number of rows with non-zero features: " << dfSize << endl;
    if (!silent)
        cout << "Total processing time: "
             << chrono::duration_cast<chrono::milliseconds>(processing_end - processing_start).count() / 1000.0 << " s"
             << endl;

    if (!silent)
        reportFeatureEngineeringTimes(config);
    if (!silent)
        reportTransactionPerSecond(config);
}
