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

#ifndef PAR_CYCLE_ENUM_H
#define PAR_CYCLE_ENUM_H

#include <vector>
#include <string>
#include <utility>
#include <map>

class CompressedGraph;
struct CompressedEdge;

namespace ParCycEnum {

// TODO: This is just a workaround, find a better way to declare Graph
#ifdef USE_EXT_GRAPH
class ExternalGraph;
typedef ExternalGraph Graph;
#else
class CSRGraph;
typedef CSRGraph Graph;
#endif

typedef std::map<int, uint64_t> CycleHist;

template <typename R, typename... ARGS> using function = R (*)(ARGS...);
typedef function<void, std::vector<int>&, std::vector<std::vector<int64_t>>&> CycleBundleCallback;

#ifndef EMPTY_CYCLE_CALLBACK
#define EMPTY_CYCLE_CALLBACK [](std::vector<int>& cycle, std::vector<std::vector<int64_t>>& edgeIDs) {}
#endif

class ParallelCycleEnumerator {
public:
    /**
     * Constructors.
     */
    ParallelCycleEnumerator(std::string graphpath);
    ParallelCycleEnumerator(CompressedGraph* cgraph);

    /**
     * Destructor.
     */
    ~ParallelCycleEnumerator();

    /**
     * Sets the callback function invoked when a cycle bundle is found
     *
     * The callback function needs to have the following declaration
     * void patternCallback (vector<int>& cycle, vector<vector<int64_t>>& edgeIDs);
     * Parameters of the patternCallback function are
     *     cycle - a vector of vertex indices contained in the found cycle.
     *     edgeIDs - a vector containing the set of edge IDs that connect two consecutive vertices of the cycle
     *
     *     For instance, for the following cycle bundle
     *         a --[e1,e2]--> b --[e3,e4,e5]--> c --[e6,e7]--> a
     *     the callback function with the following parameters is invoked:
     *         cycle = [a, b, c]
     *         edgeIDs = [[e1,e2],[e3,e4,e5],[e6,e7]]
     *     where e1...e7 are edge IDs
     *
     * The callback function should be thread-safe because it might be
     * invoked from different threads.
     * The default callback function is an empty function.
     *
     * @param callback Callback function invoked when a cycle is found
     */
    void setCycleBundleFoundCallback(CycleBundleCallback callback);

    /**
     * Runs the cycle enumeration on the entire graph using multiple threads
     *
     * The search for cycles is performed using nthr threads. Each time a cycle is found a callback
     * function is invoked, which defined using setCycleBundleFoundCallback function.
     *
     * @param timeWindow Time window parameter
     * @param lenConstraint Cycle length constraint. Ignored for temporal cycle enumeration.
     * @param nthr Number of threads used to perform cycle enumeration
     * @param algo Algorithm used for temporal cycle enumeration
     *                0 - fine-grained parallel temporal Johnson
     *                1 - coarse-grained parallel temporal Johnson
     *                2 - fine-grained parallel length-constrained cycle enumeration
     *                3 - coarse-grained parallel length-constrained cycle enumeration
     */
    void runCycleEnumeration(int timeWindow, int lenConstraint, int nthr = 1, int algo = 0);

    /**
     * Invokes cycle enumeration procedure that start from the given batch of edges.
     *
     * This function accepts a batch of starting edges and invokes cycle enumeration procedure
     * starting from each edge. The search for cycles is performed using nthr threads.
     * Each time a cycle is found a callback function is invoked, which defined using
     * setCycleBundleFoundCallback function. This function can be used for either temporal cycles
     * or length-constrained simple cycles.
     *
     * @param batch Vector of starting edges for which the cycle enumeration is invoked.
     *              An edge is represented using a vector of size 4: [fromV, toV, tstamp, eid], where:
     *                eid    - edge id
     *                tstamp - timestamp of the edge
     *                fromV  - source vertex
     *                toV    - target vertex
     * @param timeWindow Time window parameter
     * @param lenConstraint Cycle length constraint. Ignored for temporal cycle enumeration if its value is -1.
     * @param nthr Number of threads used to perform cycle enumeration
     * @param algo Algorithm used for cycle enumeration
     *                0 - fine-grained parallel temporal Johnson
     *                1 - coarse-grained parallel temporal Johnson
     *                2 - fine-grained parallel length-constrained cycle enumeration
     *                3 - coarse-grained parallel length-constrained cycle enumeration
     */
    void runCycleEnumerationBatch(std::vector<CompressedEdge>& batch, int timeWindow, int lenConstraint, int nthr = 1,
                                  int algo = 0);

    /**
     * Prints the cycle histogram. Histogram is cleared after deleting the graph.
     */
    void printHist();

private:
    Graph* gg = NULL;

    CycleHist cycleHistogram;

    // Default empty callback
    CycleBundleCallback cycleBundleCallback = EMPTY_CYCLE_CALLBACK;
};

}

#endif // PAR_CYCLE_ENUM_H