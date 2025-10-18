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

#ifndef GRAPH_FEATURES_H
#define GRAPH_FEATURES_H

#include <string>
#include <vector>
#include <unordered_map>

using namespace std;

class Graph;
class runSettings;
class DynamicCycleFinder;

namespace GraphFeatures {

class GraphFeaturePreprocessor {
public:
    /**
     * Constructor.
     */
    GraphFeaturePreprocessor();

    /**
     * Destructor.
     */
    ~GraphFeaturePreprocessor();

    /**
     * Loads the configuration file.
     *
     * The configuration file defines which subgraph patterns are enabled, their corresponding time window values, and
     * bin sizes.
     *
     * @param[in] path Path to the input configuration file
     *
     * @return 0 if the path is correct, -1 otherwise
     */
    int loadConfigFile(string path);

    /**
     * Sets the configuration parameters.
     *
     * @param[in] intParams Integer parameters
     * @param[in] vecParams Vector parameters
     *
     * @return 0 if the operation was successful, -1 otherwise
     */
    int setParams(unordered_map<string, int> intParams, unordered_map<string, vector<int>> vecParams);

    /**
     * Generates the graph-based features for the current batch of feature vectors.
     *
     * This function searches for subgraph patterns in the dynamic graph defined by the past feature vectors and the
     * time window values given in the configuration file. These subgraph patterns are provided as an additional
     * graph-based features.
     *
     * The input features_in array contains num_samples feature vectors, and each feature vector has
     * the following format:
     *     [edgeID, fromID, toID, timestamp, \<raw features\>]
     * where fromID and toID are the IDs of the source and the destination vertex. Each feature vector in features_in
     * contains num_features_in - 3 raw features that are placed after toID. Feature vectors in features_in are ordered
     * in time. Additionally, the subsequent invocations of this function also receive feature vectors ordered in time.
     *
     * The output of the computation is provided in features_out array, which also contains num_samples feature vectors.
     * A feature vector in features_out has the following format:
     *     [edgeID, fromID, toID, timestamp, \<raw features\>, \<engineered features\>]
     * where timestamp, fromID, toID and \<raw features\> have the same values as in the corresponding vector in
     * features_in. Engineered features are the graph-based features computed by this function.
     *
     * The the configuration file has to be loaded before running this function.
     *
     * @param[in] num_samples Number of rows of the features_in and features_out arrays
     * @param[in] features_in 2D array containing a batch of num_samples input feature vectors along with their raw
     * features
     * @param[in] num_features_in Number of columns of the features_in array
     * @param[out] features_out 2D array containing a batch of num_samples input feature vectors along with their raw
     * features and the engineered graph-based features
     * @param[in] num_features_out Number of columns of the features_out array
     *
     * @return 0 if the operation was successful, -1 otherwise
     */
    int enrichFeatureVectors(uint64_t num_samples, double* features_in, uint64_t num_features_in, double* features_out,
                             uint64_t num_features_out);

    /**
     * Updates the graph based on the input features
     *
     * @return 0 if the operation was successful, -1 otherwise
     */
    int updateGraph(double* features_in, uint64_t num_samples, uint64_t num_features);

    /**
     * Returns the number of engineered graph-based features generated using the current configuration file.
     *
     * If the configuration file has not been loaded before running this function, it will return 0.
     *
     *  @return Number of engineered graph-based features
     */
    uint64_t getNumEngineeredFeatures();

    /**
     * Loads the graph from the path specified by the input parameter.
     *
     * The input graph should be stored in a text file in a coordinate format. Each row of this file contains one edge
     * of the input graph. Each edge has the following format:
     *     edgeID fromID toID timestamp ...
     * where the fields are separated by a whitespace. EdgeID represents the ID of the current edge, fromID is the ID of
     * the source vertex, and toID is the ID of the target vertex.
     *
     * @param[in] path Path to the input graph
     *
     * @return 0 if the path is correct, -1 otherwise
     */
    int loadGraph(string path);

    /**
     * Loads the graph from the list of feature vectors.
     *
     * The list of feature vectors is represented as a table. Each row of this table contains one edge (feature vector)
     * of the input graph. Each edge has the following format:
     *     edgeID, fromID, toID, timestamp, \<raw features\>
     * EdgeID represents the ID of the current edge, fromID is the ID of the source vertex,
     * and toID is the ID of the target vertex.
     *
     * @param[in] features 2D array containing a batch of k input feature vectors along with their raw features
     * @param[in] num_samples Number of rows (feature vectors) of the features array
     * @param[in] num_features Number of columns (features) of the features array
     *
     * @return 0 if the operation was successful, -1 otherwise
     */
    int loadGraph(double* features, uint64_t num_samples, uint64_t num_features);

    /**
     * Saves the current graph to the path specified by the input parameter.
     *
     * The graph is saved using this function can be loaded using loadGraph() function.
     *
     * @param[in] path Path where the graph should be saved
     *
     * @return 0 if the path is correct, -1 otherwise
     */
    int saveGraph(string path);

    /** Returns the dimensions of the 2D array required for exporting the graph.
     *
     * @return [num_samples, num_features], where num_samples is the number of edges in the graph, and num_features is
     * the number of raw features of each edge.
     */
    pair<uint64_t, uint64_t> getOutputArrayDimensions();

    /**
     * Exports the current graph to the 2D array.
     *
     * This functions takes as an input a pointer to the allocated 2D array, along with the dimensions of this array,
     * and writes the graph into this array. Format of the graph is the same as the format required for reading the
     * graph.
     *
     * For this function to work properly, memory to which features points to should have the size of num_samples x
     * num_features. [num_samples, num_features] should be obtained from the getGraphDimensions() function.
     *
     * @param[out] features 2D array containing a batch of num_samples input feature vectors along with their raw
     * features
     * @param[in] num_samples Number of rows (feature vectors) of the features array
     * @param[in] num_features Number of columns (features) of the features array
     *
     * @return 0 if the operation was successful, -1 otherwise
     */
    int exportGraph(double* features, uint64_t num_samples, uint64_t num_features);

    /**
     * Enable or disable computation of vertex statistics features using non-incremental approach. Used for debug
     * purposes.
     */
    void enableNonIncVertStatComputation();
    void disableNonIncVertStatComputation();

private:
    runSettings*        config;
    Graph*              g                    = NULL;
    DynamicCycleFinder* cycleFinder          = NULL;
    bool                preprocessingStarted = false;
};

}

#endif // GRAPH_FEATURES_H
