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

#ifndef _GRAPH_UTILS_H_
#define _GRAPH_UTILS_H_

#include <vector>
#include <map>
#include <set>
#include <cctype>
#include <cstdint>
#include <sstream>
#include <fstream>
#include <cassert>
#include <iostream>
#include <atomic>
#include <limits>
#include <exception>
#include <algorithm>
#include <functional>
#include <unordered_set>
#include <unordered_map>

#include "graph.h"

#ifndef USE_TBB
#include <omp.h>
#else
#include <tbb/task.h>
#include <tbb/combinable.h>
#include <tbb/parallel_for.h>
#include <tbb/tick_count.h>
#include <tbb/task_scheduler_init.h>
#include <tbb/blocked_range.h>
#include <tbb/spin_mutex.h>
#include <tbb/atomic.h>
using namespace tbb;
#endif

using namespace std;

// TODO: Create standard types for Timestamp and ID

// Type II is not a pattern, should not be here
enum class Pattern : int {
    FanIn = 0,
    FanOut,
    DegIn,
    DegOut,
    ScatGat,
    TempCycle,
    LCCycle,
    Biclique,
    Clique,
    TypeII,
    TypeIIa,
    SIZE
};
const int            NUM_PATTERNS = (int)(Pattern::SIZE);
const vector<string> PatternNames = { "FanIn",   "FanOut",   "DegIn",  "DegOut", "ScatGat", "TempCycle",
                                      "LCCycle", "Biclique", "Clique", "TypeII", "TypeIIa" };

enum class StatFeatures : int { Fan = 0, Deg, Ratio, Avg, Sum, Min, Max, Med, Var, Skew, Kurtosis, SIZE };
const vector<string> StatFeaturesNames
    = { "Fan", "Deg", "Ratio", "Avg", "Sum", "Min", "Max", "Med", "Var", "Skew", "Kurtosis" };
const int NumFanDegFeatures = 3;
const int NumStatFeatures   = 8;

struct EnumClassHash {
    template <typename T> std::size_t operator()(T t) const { return static_cast<std::size_t>(t); }
};

namespace {
// Map between pattern name in the config file and the corresponding Pattern value
unordered_map<string, unordered_set<Pattern, EnumClassHash>>
    patternMap({ { "fans", { Pattern::FanIn, Pattern::FanOut } },
                 { "degrees", { Pattern::DegIn, Pattern::DegOut } },
                 { "scatter-gather", { Pattern::ScatGat } },
                 { "temp-cycles", { Pattern::TempCycle } },
                 { "lc-cycles", { Pattern::LCCycle } },
                 { "bicliques", { Pattern::Biclique } },
                 { "cliques", { Pattern::Clique } } });

unordered_map<string, StatFeatures> statFeatureMap({ { "fan", StatFeatures::Fan },
                                                     { "deg", StatFeatures::Deg },
                                                     { "ratio", StatFeatures::Ratio },
                                                     { "avg", StatFeatures::Avg },
                                                     { "sum", StatFeatures::Sum },
                                                     { "min", StatFeatures::Min },
                                                     { "max", StatFeatures::Max },
                                                     { "median", StatFeatures::Med },
                                                     { "var", StatFeatures::Var },
                                                     { "skew", StatFeatures::Skew },
                                                     { "kurtosis", StatFeatures::Kurtosis } });

unordered_set<StatFeatures, EnumClassHash> fanDegFeatureSet({ StatFeatures::Fan, StatFeatures::Deg,
                                                              StatFeatures::Ratio });

// Map between the pattern name used for setting the parameters in the config file and the corresponding Pattern value
// TODO: Change pattern files to enable this file to be removed
unordered_map<string, unordered_set<Pattern, EnumClassHash>>
    patternParamMap({ { "fan", { Pattern::FanIn, Pattern::FanOut } },
                      { "deg", { Pattern::DegIn, Pattern::DegOut } },
                      { "sg", { Pattern::ScatGat } },
                      { "temp-cycle", { Pattern::TempCycle } },
                      { "lc-cycle", { Pattern::LCCycle } },
                      { "biclique", { Pattern::Biclique } },
                      { "clique", { Pattern::Clique } } });
}

inline char* getCmdOption(char** begin, char** end, const std::string& option)
{
    char** itr = std::find(begin, end, option);
    if (itr != end && ++itr != end) {
        return *itr;
    }
    return 0;
}

inline bool cmdOptionExists(char** begin, char** end, const std::string& option)
{
    return std::find(begin, end, option) != end;
}

inline void printHelp()
{
    std::cout << " AML pattern detection " << std::endl;
    std::cout << "    -f                Path to the input file graph." << std::endl;
    std::cout << "    -l                Path to the input edge label file." << std::endl;
    std::cout << "    -config           Path to the config file." << std::endl;
    std::cout << "    -sim              Type of the aml simulator that generated the input graph" << std::endl;
    std::cout << "                      Can be used to override the simulator information from the config file."
              << std::endl;
    std::cout << "                      Possible input values: \"aml-sim\" and \"aml-e\"" << std::endl;
    std::cout << "    -type             Feature type to be generated." << std::endl;
    std::cout << "                      Can be used to override the feature type information from the config file."
              << std::endl;
    std::cout << "                      Possible input values: \"type1\", \"type2\", and \"type3\"." << std::endl;
    std::cout << "                      \"type1\" - vertex features." << std::endl;
    std::cout << "                      \"type2\" - edge features." << std::endl;
    std::cout
        << "                      \"type3\" - edge features generated by concatenating src and dest vertex features."
        << std::endl;
    std::cout << "    -batch            Enables batched execution of feature engineering." << std::endl;
    std::cout << "                      The input value represents the batch size." << std::endl;
    std::cout << "                      If it is not defined, accumulated features are generated" << std::endl;
    std::cout << "    -convert          Generate typeII network based on the forwarded time window value." << std::endl;
    std::cout << "                      The input value represents the time window in hours." << std::endl;
    std::cout << "    -np               Suppress printing the output to a file." << std::endl;
    std::cout << "    -n                Number of threads available." << std::endl;
    std::cout << "    -h                Prints this message." << std::endl;
}

template <typename T> inline std::vector<T> arange(T start, T stop, T step = 1)
{
    std::vector<T> values;
    for (T value = start; value < stop; value += step) {
        values.push_back(value);
    }
    values.push_back(stop);
    return values;
}

inline std::vector<std::vector<int>> create2DArray(unsigned height, unsigned width)
{
    return std::vector<std::vector<int>>(height, std::vector<int>(width, 0));
}

const unsigned long MAX_LONG = std::numeric_limits<unsigned long>::max();

class runSettings {
public:
    // General configuration
    // Rename to featureType
    string    networkType, simulator;
    Timestamp timewindow = -1;
    int       windowsize = -1;
    int       numthreads = 12;

    bool batchedFeatures = false;
    bool vertexFeatures  = false;

    // Pattern parameters
    unordered_set<Pattern, EnumClassHash>              patterns;
    unordered_map<Pattern, Timestamp, EnumClassHash>   timewindows;
    unordered_map<Pattern, vector<int>, EnumClassHash> bins;
    unordered_map<Pattern, int, EnumClassHash>         maxlengths;

    // Statistical patterns
    bool                                       useShallowFeatures = false;
    Timestamp                                  vertStatTW         = 0;
    unordered_set<StatFeatures, EnumClassHash> fanDegFeatures;
    unordered_set<StatFeatures, EnumClassHash> statFeatures;
    vector<int>                                rawFeatureColumns;
    vector<int>                                fanDegFeatureIndices;
    vector<int>                                statFeatureIndices;

    bool patternExists(Pattern p) { return (patterns.find(p) != patterns.end()); }
    bool statFeatExists(StatFeatures p)
    {
        bool fdExists   = (fanDegFeatures.find(p) != fanDegFeatures.end());
        bool statExists = (statFeatures.find(p) != statFeatures.end());
        return (fdExists || statExists);
    }

    // Other parameters
    bool   suppressOut = false;
    string graph_path, base_path;
    int    t0, t1;
    int    transNum = 1;

    // Processing time
    unordered_map<Pattern, double, EnumClassHash> processingTime;
    double totalProcessingTime = 0.0, postprocessingTime = 0.0, type2ProcessingTime = 0.0, shallowProcTime = 0.0;
    double printingTime = 0.0;

    runSettings()
        : fanDegFeatureIndices(NumFanDegFeatures, -1)
        , statFeatureIndices(NumStatFeatures, -1)
    {
    }

    bool nonincStat = false;

    void clear()
    {
        patterns.clear();
        timewindows.clear();
        bins.clear();
        maxlengths.clear();
        processingTime.clear();
        totalProcessingTime = postprocessingTime = 0.0;
        type2ProcessingTime = printingTime = 0.0;
        fanDegFeatures.clear();
        statFeatures.clear();
        rawFeatureColumns.clear();
        fanDegFeatureIndices.resize(0);
        fanDegFeatureIndices.resize(NumFanDegFeatures, -1);
        statFeatureIndices.resize(0);
        statFeatureIndices.resize(NumStatFeatures, -1);

        transNum           = 1;
        timewindow         = -1;
        windowsize         = -1;
        vertStatTW         = 0;
        useShallowFeatures = false;
        batchedFeatures    = false;
        vertexFeatures     = false;
        nonincStat         = false;
        suppressOut        = false;
    }
};

inline int getNumStatFeatures(runSettings& config)
{
    return 2 * (config.fanDegFeatures.size() + config.rawFeatureColumns.size() * config.statFeatures.size());
}

// This function does not check if the pattern exists in config
inline int getVertStatIndex(runSettings& config, StatFeatures f, int rawFeatureIndex, bool out)
{
    const int fdFeatures   = config.fanDegFeatures.size();
    const int statFeatures = config.statFeatures.size();
    const int numColls     = config.rawFeatureColumns.size();
    const int halfSize     = (fdFeatures + numColls * statFeatures);

    int returnIndex = out ? 0 : halfSize;

    if (config.fanDegFeatures.find(f) != config.fanDegFeatures.end()) {

        returnIndex += config.fanDegFeatureIndices[static_cast<int>(f)];

    } else if (config.statFeatures.find(f) != config.statFeatures.end()) {

        returnIndex += fdFeatures + statFeatures * rawFeatureIndex
                       + config.statFeatureIndices[static_cast<int>(f) - NumFanDegFeatures];
    }

    return returnIndex;
}

inline vector<string> getStatFeatureNames(runSettings& config)
{
    const int fdFeatures   = config.fanDegFeatures.size();
    const int statFeatures = config.statFeatures.size();
    const int numColls     = config.rawFeatureColumns.size();
    const int halfSize     = (fdFeatures + numColls * statFeatures);

    vector<string> headers(getNumStatFeatures(config));

    for (int rep = 0; rep < 2; rep++) {

        int startIndex = (rep == 0) ? 0 : halfSize;

        string suffix = (rep == 0) ? "Out" : "In";

        for (auto f : config.fanDegFeatures) {
            int currentIndex      = startIndex + config.fanDegFeatureIndices[static_cast<int>(f)];
            headers[currentIndex] = StatFeaturesNames[static_cast<int>(f)] + " " + suffix;
        }

        for (unsigned int ind = 0; ind < config.rawFeatureColumns.size(); ind++) {
            int featInd = config.rawFeatureColumns[ind];

            for (auto f : config.statFeatures) {
                int currentIndex = startIndex + fdFeatures + statFeatures * ind
                                   + config.statFeatureIndices[static_cast<int>(f) - NumFanDegFeatures];

                string fname;
                if (featInd == 0)
                    fname = "EdgeID";
                else if (featInd == 1)
                    fname = "SourceVertexID";
                else if (featInd == 2)
                    fname = "DestinationVertexID";
                else if (featInd == 3)
                    fname = "Timestamp";
                else
                    fname = "RawFeat" + to_string(featInd);

                headers[currentIndex] = StatFeaturesNames[static_cast<int>(f)] + " " + fname + " " + suffix;
            }
        }
    }

    return headers;
}

inline void parseConfigFile(const string& configPath, runSettings& config)
{
    // TODO: check the validity of the config file and throw exceptions
    ifstream configFile(configPath);
    if (!configFile.is_open()) {
        cout << "Could not find config file, provide the correct path" << endl;
        std::exit(EXIT_FAILURE);
    }

    // Default values
    config.vertexFeatures  = false;
    config.batchedFeatures = true;

    // parsing first few lines
    string line;
    string key, val;
    while (getline(configFile, line)) {
        if (line[0] == '%' || line[0] == '#')
            continue;
        if (line == "end_global_params")
            break;

        istringstream iss(line);
        getline(iss, key, ':');
        getline(iss, val);
        if (key.find("network_type") != string::npos) {
            config.networkType    = val;
            config.vertexFeatures = ((val == "type1") || (val == "type3"));
        } else if (key.find("simulator") != string::npos) {
            config.simulator = val;
        } else if (key.find("time_window") != string::npos) {
            config.timewindow = stoi(val) * 3600;
        } else if (key.find("max_no_edges") != string::npos) {
            config.windowsize = stoi(val);
        } else if (key.find("num_threads") != string::npos) {
            config.numthreads = stoi(val);
        }
    };

    // parsing remainder for patterns, they follow the same format
    while (getline(configFile, line)) {
        if (line[0] == '%' || line[0] == '#' || line.empty())
            continue;

        istringstream iss(line);
        getline(iss, key, ':');

        if (key == "vertstat") {
            getline(iss, val);
            if (val == "true")
                config.useShallowFeatures = true;
            else
                config.useShallowFeatures = false;
            continue;
        }

        // Check if the pattern is enabled
        if (patternMap.find(key) != patternMap.end()) {
            getline(iss, val);
            // config.patterns[key] = (val == "true");
            auto& patterns = patternMap.at(key);
            if (val == "true")
                config.patterns.insert(patterns.begin(), patterns.end());
        } else {
            // Character "_" is a delimiter
            auto delimPos = key.find("_");
            if (delimPos != string::npos) {
                string patternParamName = key.substr(0, delimPos);
                string paramName        = key.substr(delimPos + 1, key.size() - delimPos - 1);

                if (patternParamName == "vertstat") {
                    if (config.useShallowFeatures) {
                        if (paramName == "cols") {
                            while (getline(iss, val, ',')) {
                                config.rawFeatureColumns.push_back(stoi(val));
                            }
                        } else if (paramName == "tw") {
                            while (getline(iss, val, ',')) {
                                config.vertStatTW = stoi(val) * 3600;
                            }
                        } else if (paramName == "feats") {
                            while (getline(iss, val, ',')) {
                                auto featName = statFeatureMap[val];
                                if (fanDegFeatureSet.find(featName) != fanDegFeatureSet.end()) {
                                    config.fanDegFeatures.insert(featName);

                                    for (int cnt = 0, ind = 0;
                                         ind < static_cast<int>(config.fanDegFeatureIndices.size()); ind++) {
                                        if (ind >= static_cast<int>(featName)) {
                                            if (config.fanDegFeatureIndices[ind] != -1
                                                || ind == static_cast<int>(featName)) {
                                                config.fanDegFeatureIndices[ind] = cnt;
                                            }
                                        }

                                        if (config.fanDegFeatureIndices[ind] != -1)
                                            cnt++;
                                    }
                                } else {
                                    config.statFeatures.insert(featName);

                                    for (int cnt = 0, ind = 0; ind < static_cast<int>(config.statFeatureIndices.size());
                                         ind++) {
                                        int statFeatIndex = static_cast<int>(featName) - NumFanDegFeatures;
                                        if (ind >= statFeatIndex) {
                                            if (config.statFeatureIndices[ind] != -1 || ind == statFeatIndex) {
                                                config.statFeatureIndices[ind] = cnt;
                                            }
                                        }

                                        if (config.statFeatureIndices[ind] != -1)
                                            cnt++;
                                    }
                                }
                            }
                        }
                    }
                } else if (patternParamMap.find(patternParamName) != patternParamMap.end()) {

                    // TODO: change config files to use tw instead of dt
                    if (paramName == "dt") {
                        getline(iss, val);
                        int tw = stoi(val) * 3600;
                        for (auto pat : patternParamMap[patternParamName]) {
                            config.timewindows[pat] = tw;
                        }
                    } else if (paramName == "len") {
                        getline(iss, val);
                        int len = stoi(val);
                        for (auto pat : patternParamMap[patternParamName]) {
                            config.maxlengths[pat] = len;
                        }
                    } else if (paramName == "bins") {
                        while (getline(iss, val, ',')) {
                            int binVal = stoi(val);
                            for (auto pat : patternParamMap[patternParamName]) {
                                config.bins[pat].push_back(binVal);
                            }
                        }
                    }
                }
            }
        }
    }

    if (config.timewindow <= -1) {
        for (auto pair : config.timewindows)
            config.timewindow = max(config.timewindow, pair.second);
    }

    if (config.timewindow <= 0)
        throw std::invalid_argument("Time window size must be greater than zero.");
}

inline int loadConfigParams(runSettings& config, unordered_map<string, int> intParams,
                            unordered_map<string, vector<int>> vecParams)
{

    // Map between pattern name in the config file and the corresponding Pattern value
    const unordered_map<string, unordered_set<Pattern, EnumClassHash>> patternMap(
        { { "fan", { Pattern::FanIn, Pattern::FanOut } },
          { "degree", { Pattern::DegIn, Pattern::DegOut } },
          { "scatter-gather", { Pattern::ScatGat } },
          { "temp-cycle", { Pattern::TempCycle } },
          { "lc-cycle", { Pattern::LCCycle } } });

    // TODO: This two parameters could be added in the future
    config.vertexFeatures  = false;
    config.batchedFeatures = true;

    if (intParams.find("time_window") != intParams.end()) {
        config.timewindow = intParams["time_window"];
        if (config.timewindow == 0)
            throw std::invalid_argument("Time window size cannot be zero.");
    }
    if (intParams.find("max_no_edges") != intParams.end()) {
        config.windowsize = intParams["max_no_edges"];
        if (intParams["max_no_edges"] == 0)
            throw std::invalid_argument("Max number of edges cannot be zero.");
    }
    if (intParams.find("num_threads") != intParams.end()) {
        config.numthreads = intParams["num_threads"];
        if (intParams["num_threads"] <= 0)
            throw std::invalid_argument("Number of threads must be greater than zero.");
    }

    // Vertex statistics features
    if (intParams.find("vertex_stats") != intParams.end()) {
        if (intParams["vertex_stats"]) {
            config.useShallowFeatures = true;

            if (vecParams.find("vertex_stats_cols") == vecParams.end()
                || vecParams.find("vertex_stats_feats") == vecParams.end()
                || intParams.find("vertex_stats_tw") == intParams.end()) {
                throw std::invalid_argument(
                    "vertex_stats_cols, vertex_stats_feats, or vertex_stats_tw does not exist.");
            }

            // Set the time window for vertex statistics
            config.vertStatTW = intParams["vertex_stats_tw"];
            if (config.vertStatTW <= 0)
                throw std::invalid_argument("Time window size must be greater than zero.");

            // Set the columns
            set<int> colums;
            for (auto el : vecParams["vertex_stats_cols"]) {
                if (el >= 0)
                    colums.insert(el);
                else
                    throw std::invalid_argument(
                        "Columns used for vertex statistics must be greater than or equal to zero.");
            }
            config.rawFeatureColumns.reserve(colums.size());
            for (auto el : colums)
                config.rawFeatureColumns.push_back(el);

            set<int> featInds;
            for (auto el : vecParams["vertex_stats_feats"]) {
                if (el >= 0 && el < static_cast<int>(StatFeatures::SIZE))
                    featInds.insert(el);
                else
                    throw std::invalid_argument("Invalid vertex statistics feature.");
            }

            // Set the features
            for (auto featInd : featInds) {
                auto featName = static_cast<StatFeatures>(featInd);
                if (fanDegFeatureSet.find(featName) != fanDegFeatureSet.end()) {
                    config.fanDegFeatures.insert(featName);

                    for (int cnt = 0, ind = 0; ind < static_cast<int>(config.fanDegFeatureIndices.size()); ind++) {
                        if (ind >= static_cast<int>(featName)) {
                            if (config.fanDegFeatureIndices[ind] != -1 || ind == static_cast<int>(featName)) {
                                config.fanDegFeatureIndices[ind] = cnt;
                            }
                        }

                        if (config.fanDegFeatureIndices[ind] != -1)
                            cnt++;
                    }
                } else {
                    config.statFeatures.insert(featName);

                    for (int cnt = 0, ind = 0; ind < static_cast<int>(config.statFeatureIndices.size()); ind++) {
                        int statFeatIndex = static_cast<int>(featName) - NumFanDegFeatures;
                        if (ind >= statFeatIndex) {
                            if (config.statFeatureIndices[ind] != -1 || ind == statFeatIndex) {
                                config.statFeatureIndices[ind] = cnt;
                            }
                        }

                        if (config.statFeatureIndices[ind] != -1)
                            cnt++;
                    }
                }
            }
        } else {
            config.useShallowFeatures = false;
        }
    }

    // Patterns
    for (auto pair : patternMap) {
        auto  key      = pair.first;
        auto& patterns = pair.second;
        if (intParams.find(key) != intParams.end()) {
            if (intParams[key])
                config.patterns.insert(patterns.begin(), patterns.end());
        }
    }
    for (auto pair : patternMap) {
        auto  key      = pair.first;
        auto& patterns = pair.second;

        bool exists = true;
        for (auto pat : patterns) {
            if (config.patterns.find(pat) == config.patterns.end()) {
                exists = false;
            }
        }

        if (!exists)
            continue;

        // Timewindow
        string twkey = key + "_tw";
        if (intParams.find(twkey) != intParams.end()) {
            int tw = intParams[twkey];
            if (tw <= 0)
                throw std::invalid_argument("Time window size must be greater than zero.");
            for (auto pat : patterns) {
                config.timewindows[pat] = tw;
            }
        } else {
            throw std::invalid_argument("Time window size does not exist.");
        }

        // Length
        string lenkey = key + "_len";
        if (intParams.find(lenkey) != intParams.end()) {
            int len = intParams[lenkey];
            if (len <= 1)
                throw std::invalid_argument("Length constraint must be greater than one.");
            for (auto pat : patterns) {
                config.maxlengths[pat] = len;
            }
        } else {
            if (key == "lc-cycle") {
                throw std::invalid_argument("Length constraint for lc-cycles does not exist.");
            }
        }

        // Bins
        string binkey = key + "_bins";
        if (vecParams.find(binkey) != vecParams.end()) {
            auto& binVec = vecParams[binkey];
            int   prev   = binVec[0];
            for (int i = 0; i < binVec.size(); i++) {
                if (binVec[i] <= 0)
                    throw std::invalid_argument("Bin values must be greater than zero.");
                if (i != 0 && prev >= binVec[i])
                    throw std::invalid_argument("Bin values must be sorted in increasing order.");
                prev = binVec[i];
            }

            for (auto pat : patterns) {
                config.bins[pat] = binVec;
            }
        } else {
            throw std::invalid_argument("Bins do not exist.");
        }
    }

    if (config.timewindow <= -1) {
        for (auto pair : config.timewindows)
            config.timewindow = max(config.timewindow, pair.second);
    }

    if (config.timewindow <= 0)
        throw std::invalid_argument("Time window size must be greater than zero.");

    return 0;
}

inline void enableVertexStatistics(DynamicGraph* dg, runSettings& config)
{
    bool sum      = config.statFeatures.find(StatFeatures::Sum) != config.statFeatures.end();
    bool avg      = config.statFeatures.find(StatFeatures::Avg) != config.statFeatures.end();
    bool var      = config.statFeatures.find(StatFeatures::Var) != config.statFeatures.end();
    bool skew     = config.statFeatures.find(StatFeatures::Skew) != config.statFeatures.end();
    bool kurtosis = config.statFeatures.find(StatFeatures::Kurtosis) != config.statFeatures.end();
    dg->enableVertexStatistics(sum, avg, var, skew, kurtosis);
}

inline void initDynamicGraph(DynamicGraph* dg, runSettings& config)
{
    dg->setTimeWindow(config.timewindow);
    dg->setWindowSize(config.windowsize);
    dg->setVertStatTimeWindow(config.vertStatTW);

    if (config.useShallowFeatures) {
        dg->collectVertStatForColumns(config.rawFeatureColumns);
        enableVertexStatistics(dg, config);
    }
}

inline int binCounts(const std::vector<int> bins, int count)
{
    if (count >= bins.back()) {
        return bins.size() - 1;
    } else {
        for (unsigned int i = 0; i < bins.size(); i++) {
            if (count <= bins[i]) {
                return i;
            }
        }
    }
    return 0;
}

template <typename T> inline void freeContainer(T& container)
{
    T empty;
    using std::swap;
    swap(container, empty);
}

class spinlock {
public:
    ~spinlock() {};

    void lock() { lock_int(); }
    void lock_shared() { lock_int(); }

    void unlock() { unlock_int(); }
    void unlock_shared() { unlock_int(); }

private:
    mutable std::atomic<bool> _lock = { false };

    void lock_int()
    {
        for (;;) {
            if (!_lock.exchange(true, std::memory_order_acquire)) {
                break;
            }
            while (_lock.load(std::memory_order_relaxed)) { }
        }
    }

    void unlock_int() { _lock.store(false, std::memory_order_release); }
};

#endif
