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

#include "CycleEnumeration.h"

#include <unordered_set>
#include <unordered_map>
#include <stack>
#include <utility>
#include <ctime>
#include <chrono>
#include <queue>

#ifdef MPI_IMPL
#include <mpi.h>
#endif

using namespace std;

namespace ParCycEnum {

extern Timestamp timeWindow;

// vert is source vertex
bool edgeInTimeInterval(Timestamp tstart, Timestamp timeWindow, int vstart, int vert, TimestampSet& tset, bool invert)
{
    if (!invert) {
        auto it_start = (vstart >= vert) ? lower_bound(tset.begin(), tset.end(), tstart)
                                         : upper_bound(tset.begin(), tset.end(), tstart);
        auto it_end = upper_bound(it_start, tset.end(), tstart + timeWindow);
        if (it_start >= it_end)
            return false;
        return true;
    } else {
        auto it_end = (vstart >= vert) ? upper_bound(tset.begin(), tset.end(), tstart)
                                       : lower_bound(tset.begin(), tset.end(), tstart);
        auto it_start = lower_bound(tset.begin(), tset.end(), tstart - timeWindow);
        if (it_start >= it_end)
            return false;
        return true;
    }
}

/// *************************** Recording cycles ***************************

void recordCycle(Cycle* current, CycleHist& result, TimestampGroups* tg)
{
    /// Calling the callback function
    {
        vector<int> cycle;
        cycle.reserve(current->size());
        for (int i = 0; i < current->size(); i++) {
            cycle.push_back(current->at(i));
        }

        // Determine timestamp intervals
        vector<vector<GraphElemID>> edgeIDs(cycle.size());
        if (tg != NULL) {
            for (int i = 0; i < tg->size(); i++) {
                auto& tmpEdge = tg->at(i);
                if (tmpEdge.edgeData == NULL) {
                    edgeIDs[i].push_back(tmpEdge.first_eid);
                } else {
                    for (int j = tmpEdge.ind_begin; j < tmpEdge.ind_end; j++) {
                        edgeIDs[i].push_back(tmpEdge.edgeData->eids[j]);
                    }
                }
            }
        }

        processCycleBundle(cycle, edgeIDs);
    }

    int size = current->size();
    if (result.find(size) == result.end())
        result[size] = 0;
    result[size]++;
}

void recordBundledCycle(Cycle* current, TimestampGroups* tg, CycleHist& result, bool invert)
{
    /// Calling the callback function
    {
        vector<int> cycle;
        cycle.reserve(current->size());
        for (int i = 0; i < current->size(); i++) {
            cycle.push_back(current->at(i));
        }

        // Determine timestamp intervals
        vector<vector<GraphElemID>> edgeIDs(cycle.size());
        int                         depth = cycle.size() - 1;

        // Timestamp interval for the final edge
        for (int ind = tg->back().ind_begin; ind < tg->back().ind_end; ind++) {
            edgeIDs[depth].push_back(tg->back().edgeData->eids[ind]);
        }

        depth--;

        if (!invert) {
            // Timestamp interval for other edges in reverse order
            Timestamp prevMax = tg->back().edgeData->tstamps[tg->back().ind_end - 1];
            for (auto tint_ptr = tg->rbegin() + 1; tint_ptr != tg->rend(); ++tint_ptr) {
                if (tint_ptr->edgeData == NULL) {
                    edgeIDs[depth].push_back(tint_ptr->first_eid);
                    depth--;
                    continue;
                }

                Timestamp thisTs = -1;
                int       intEnd = tint_ptr->ind_end - 1;

                for (int it = tint_ptr->ind_begin; it < tint_ptr->ind_end; it++) {
                    thisTs = tint_ptr->edgeData->tstamps[it];
                    if (thisTs >= prevMax) {
                        intEnd = it - 1;
                        break;
                    }
                }
                prevMax = thisTs;

                for (int ind = tint_ptr->ind_begin; ind <= intEnd; ind++) {
                    edgeIDs[depth].push_back(tint_ptr->edgeData->eids[ind]);
                }

                depth--;
            }
        } else {
            // Timestamp interval for other edges in reverse order
            Timestamp prevMin = tg->back().edgeData->tstamps[tg->back().ind_begin];
            for (auto tint_ptr = tg->rbegin() + 1; tint_ptr != tg->rend(); ++tint_ptr) {
                if (tint_ptr->edgeData == NULL) {
                    edgeIDs[depth].push_back(tint_ptr->first_eid);
                    depth--;
                    continue;
                }

                Timestamp thisTs   = -1;
                int       indBegin = tint_ptr->ind_begin;

                for (int it = tint_ptr->ind_begin; it < tint_ptr->ind_end; it++) {
                    thisTs = tint_ptr->edgeData->tstamps[it];
                    if (thisTs > prevMin) {
                        indBegin = it;
                        break;
                    }
                }
                prevMin = thisTs;

                for (int ind = indBegin; ind < tint_ptr->ind_end; ind++) {
                    edgeIDs[depth].push_back(tint_ptr->edgeData->eids[ind]);
                }

                depth--;
            }
        }

        // Invoke the callback function
        processCycleBundle(cycle, edgeIDs);
    }

    /// Check if the budle is consisted of exactly one cycle
    bool allone = true;
    long count  = 1;

    for (auto it = tg->begin(); it != tg->end(); ++it) {
        if (it->edgeData != NULL || (it->ind_end - it->ind_begin > 1)) {
            allone = false;
            break;
        }
    }

    /// Count the number of cycles in the bundle (2SCENT procedure)
    if (!allone) {
        queue<pair<Timestamp, long>>* prevQueue = new queue<pair<Timestamp, long>>;
        if (nullptr == prevQueue) {
            return;
        }
        queue<pair<Timestamp, long>>* currQueue = nullptr;

        prevQueue->push(make_pair(-1, 1));

        for (auto it = (!invert ? tg->begin() : tg->end() - 1); it != (!invert ? tg->end() : tg->begin() - 1);
             (!invert ? ++it : --it)) {
            currQueue = new queue<pair<Timestamp, long>>;
            if (nullptr == currQueue)
                return;
            long n = 0, prev = 0;

            if (it->edgeData == NULL) {
                Timestamp ts = it->first_ts;

                if (!prevQueue->empty()) {
                    auto tmpPair = prevQueue->front();
                    while (tmpPair.first < ts) {
                        prevQueue->pop();
                        n = tmpPair.second;
                        if (prevQueue->empty())
                            break;
                        tmpPair = prevQueue->front();
                    }
                }
                prev += n;
                currQueue->push(make_pair(ts, prev));
            } else {

                for (auto it2 = it->ind_begin; it2 != it->ind_end; ++it2) {
                    Timestamp ts = it->edgeData->tstamps[it2];

                    if (!prevQueue->empty()) {
                        auto tmpPair = prevQueue->front();
                        while (tmpPair.first < ts) {
                            prevQueue->pop();
                            n = tmpPair.second;
                            if (prevQueue->empty())
                                break;
                            tmpPair = prevQueue->front();
                        }
                    }
                    prev += n;
                    currQueue->push(make_pair(ts, prev));
                }
            }
            if (nullptr != prevQueue)
                delete prevQueue;
            prevQueue = currQueue;
            currQueue = nullptr;
        }

        if (nullptr != prevQueue && !prevQueue->empty()) {
            auto tmpPair = prevQueue->back();
            count        = tmpPair.second;
            delete prevQueue;
        }
    }

    long size = current->size();
    if (result.find(size) == result.end())
        result[size] = 0;
    result[size] += count;
}

void combineCycleHistogram(ConcurrentContainer<CycleHist>& pt_chist, CycleHist& result)
{
    int process_rank = 0;

#ifdef MPI_IMPL
    int size_of_cluster = 1;

    MPI_Comm_size(MPI_COMM_WORLD, &size_of_cluster);
    MPI_Comm_rank(MPI_COMM_WORLD, &process_rank);
#endif

    CycleHist histogram;

    pt_chist.combine_each([&](CycleHist hist) {
        for (auto& pair : hist) {
            const int&           cyc_size = pair.first;
            const unsigned long& cyc_num  = pair.second;

            if (histogram.find(cyc_size) == histogram.end())
                histogram[cyc_size] = 0;

            histogram[cyc_size] += cyc_num;
        }
    });
#ifdef MPI_IMPL
    // Tag: 0 - hist size; 1 - histdata
    if (process_rank == 0) {
        for (int r = 1; r < size_of_cluster; r++) {
            int histsize = -1;
            MPI_Recv(&histsize, 1, MPI_INT, r, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);

            long* rec_hist = new long[2 * histsize];
            MPI_Recv(rec_hist, 2 * histsize, MPI_LONG, r, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);

            for (int i = 0; i < histsize; i++) {
                if (histogram.find(rec_hist[2 * i]) == histogram.end())
                    histogram[rec_hist[2 * i]] = 0;
                histogram[rec_hist[2 * i]] += rec_hist[2 * i + 1];
            }

            delete[] rec_hist;
        }

    } else {
        int histsize = histogram.size();
        MPI_Send(&histsize, 1, MPI_INT, 0, 0, MPI_COMM_WORLD);

        long* send_hist = new long[2 * histsize];

        int i = 0;
        for (auto hist : histogram) {
            send_hist[i++] = hist.first;
            send_hist[i++] = hist.second;
        }

        MPI_Send(send_hist, 2 * histsize, MPI_LONG, 0, 1, MPI_COMM_WORLD);

        delete[] send_hist;
    }
#endif

    if (process_rank == 0) {
        for (auto& pair : histogram) {
            const int&           cyc_size = pair.first;
            const unsigned long& cyc_num  = pair.second;

            if (result.find(cyc_size) == result.end())
                result[cyc_size] = 0;

            result[cyc_size] += cyc_num;
        }
    }
}

/// *************************** Find Cycle-Unions ***********************************

// TODO: cycle unions for simple cycles in a time window!
void findTempDescendants(Graph* g, EdgeData u, Timestamp endTs, BlockedMap& visited)
{

    /// Temporary prevent re-visiting this vertex
    visited.insert(u.vertex, NINF);

    Timestamp maxts = NINF;

    for (auto colelem = g->beginOut(u.vertex); colelem != g->endOut(u.vertex); colelem++) {
        int   w    = colelem->vertex;
        auto& tset = colelem->tstamps;

        auto it_start = upper_bound(tset.begin(), tset.end(), u.tstamp);

        /// Update maxts
        if (it_start != tset.begin()) {
            maxts = max(maxts, *(it_start - 1));
        }

        if (it_start == tset.end() || *it_start > endTs)
            continue;

        Timestamp ts = *it_start;
        /// Recursivelly visit the neighbor if it can be visited
        if (!visited.exists(w) || ts < visited.at(w)) {
            findTempDescendants(g, EdgeData(w, ts), endTs, visited);
        }
    }

    /// Update the closing time value
    visited.insert(u.vertex, maxts);
}

void findTempAncestors(Graph* g, EdgeData u, Timestamp firstTs, BlockedMap& visited, BlockedMap* candidates = NULL)
{
    /// Temporary prevent re-visiting this vertex
    visited.insert(u.vertex, NINF);

    Timestamp mints = PINF;
    for (auto colelem = g->beginIn(u.vertex); colelem != g->endIn(u.vertex); colelem++) {
        int   w    = colelem->vertex;
        auto& tset = colelem->tstamps;

        auto it_start = lower_bound(tset.begin(), tset.end(), u.tstamp);

        /// Update maxts
        if (it_start != tset.end()) {
            mints = min(mints, *it_start);
        }

        /// If the timestamp is within the time interval
        if (it_start == tset.begin() || *(it_start - 1) <= firstTs)
            continue;

        Timestamp ts = *(it_start - 1);

        if (candidates && !candidates->exists(w, ts))
            continue;

        /// Recursively visit the neighbor if it can be visited
        if (!visited.exists(w) || ts > visited.at(w)) {
            findTempAncestors(g, EdgeData(w, ts), firstTs, visited, candidates);
        }
    }
    /// Update the closing time value
    visited.insert(u.vertex, mints);
}

void findTWAncestors(Graph* g, int u, int startVert, Timestamp firstTs, Timestamp timeWindow, BlockedMap& visited,
                     BlockedMap* candidates = NULL)
{
    /// Temporary prevent re-visiting this vertex
    visited.insert(u, 1);

    for (auto colelem = g->beginIn(u); colelem != g->endIn(u); colelem++) {
        int   w    = colelem->vertex;
        auto& tset = colelem->tstamps;

        if (!edgeInTimeInterval(firstTs, timeWindow, startVert, w, tset, false))
            continue;

        if (candidates && !candidates->exists(w))
            continue;

        /// Recursively visit the neighbor if it can be visited
        if (!visited.exists(w)) {
            findTWAncestors(g, w, startVert, firstTs, timeWindow, visited, candidates);
        }
    }
}

Timestamp findCycleUnions(Graph* g, EdgeData startEdge, int startVert, Timestamp timeWindow, StrongComponent*& cunion)
{

    BlockedMap tempDescendants, tempAncestors;
    tempDescendants.insert(startVert, NINF);
    tempAncestors.insert(startVert, PINF);

    Timestamp maxInTstamp = NINF;

    /// Find temporal descendants
    findTempDescendants(g, startEdge, startEdge.tstamp + timeWindow, tempDescendants);

    Timestamp firstTs = startEdge.tstamp;
    for (auto colelem = g->beginIn(startVert); colelem != g->endIn(startVert); colelem++) {
        int   w    = colelem->vertex;
        auto& tset = colelem->tstamps;

        auto it_end = upper_bound(tset.begin(), tset.end(), firstTs + timeWindow);
        if (it_end == tset.begin() || *(it_end - 1) <= firstTs)
            continue;

        Timestamp ts = *(it_end - 1);

        if (!tempDescendants.exists(w, ts))
            continue;

        findTempAncestors(g, EdgeData(w, ts), firstTs, tempAncestors, &tempDescendants);

        maxInTstamp = max(maxInTstamp, ts);
    }

    cunion = new StrongComponent(g->getVertexNo());
    if (nullptr == cunion) {
        return -1;
    }
    tempAncestors.for_each([&](int el) { cunion->insert(el); });

    return maxInTstamp;
}

void findCycleUnions(Graph* g, EdgeData startEdge, int startVert, Timestamp timeWindow, StrongComponent*& cunion,
                     bool invert, bool temporal)
{
    cunion = new StrongComponent(g->getVertexNo());
    if (!invert) {
        BlockedMap tempAncestors;
        tempAncestors.insert(startVert, PINF);

        for (auto colelem = g->beginIn(startVert); colelem != g->endIn(startVert); colelem++) {
            int   w    = colelem->vertex;
            auto& tset = colelem->tstamps;

            if (temporal) {
                auto it_end = upper_bound(tset.begin(), tset.end(), startEdge.tstamp + timeWindow);
                if (it_end == tset.begin() || *(it_end - 1) <= startEdge.tstamp)
                    continue;
                Timestamp ts = *(it_end - 1);

                findTempAncestors(g, EdgeData(w, ts), startEdge.tstamp, tempAncestors);
            } else {
                if (!edgeInTimeInterval(startEdge.tstamp, timeWindow, startVert, w, tset, false))
                    continue;

                findTWAncestors(g, w, startVert, startEdge.tstamp, timeWindow, tempAncestors);
            }
        }

        tempAncestors.for_each([&](int el) { cunion->insert(el); });

    } else {
        BlockedMap tempDescendants;
        tempDescendants.insert(startVert, NINF);

        for (auto colelem = g->beginOut(startVert); colelem != g->endOut(startVert); colelem++) {
            int   w    = colelem->vertex;
            auto& tset = colelem->tstamps;

            auto it_start = lower_bound(tset.begin(), tset.end(), startEdge.tstamp - timeWindow);
            if (it_start == tset.end() || *(it_start) >= startEdge.tstamp)
                continue;

            Timestamp ts = *(it_start);

            findTempDescendants(g, EdgeData(w, ts), startEdge.tstamp, tempDescendants);
        }

        tempDescendants.for_each([&](int el) { cunion->insert(el); });
    }
}

/// Compute cycle union by dividing it into two functions
// The goal is to save time. We do not have to compute temporal ancestors every time just to check what is the maximal
// timestamp

Timestamp findMaxTs(Graph* g, EdgeData startEdge, int startVert, Timestamp timeWindow, BlockedMap*& tempDescendants)
{
    tempDescendants = new BlockedMap(g->getVertexNo());
    if (nullptr == tempDescendants) {
        return -1;
    }
    tempDescendants->insert(startVert, NINF);

    Timestamp maxInTstamp = NINF;

    /// Find temporal descendants
    findTempDescendants(g, startEdge, startEdge.tstamp + timeWindow, *tempDescendants);

    Timestamp firstTs = startEdge.tstamp;
    for (auto colelem = g->beginIn(startVert); colelem != g->endIn(startVert); colelem++) {
        int   w    = colelem->vertex;
        auto& tset = colelem->tstamps;

        auto it_end = upper_bound(tset.begin(), tset.end(), firstTs + timeWindow);
        if (it_end == tset.begin() || *(it_end - 1) <= firstTs)
            continue;

        Timestamp ts = *(it_end - 1);

        if (tempDescendants && !tempDescendants->exists(w, ts))
            continue;

        maxInTstamp = max(maxInTstamp, ts);
    }

    return maxInTstamp;
}

void findCycleUnions(Graph* g, EdgeData startEdge, int startVert, Timestamp timeWindow, BlockedMap* tempDescendants,
                     StrongComponent*& cunion)
{

    BlockedMap tempAncestors;
    tempAncestors.insert(startVert, NINF);

    // Hack that enable using the existing algorithms for cycle enumeration on the inverse graph
    Timestamp firstTs = startEdge.tstamp;
    for (auto colelem = g->beginIn(startVert); colelem != g->endIn(startVert); colelem++) {
        int   w    = colelem->vertex;
        auto& tset = colelem->tstamps;

        auto it_end = upper_bound(tset.begin(), tset.end(), firstTs + timeWindow);
        if (it_end == tset.begin() || *(it_end - 1) <= firstTs)
            continue;

        Timestamp ts = *(it_end - 1);

        if (tempDescendants && !tempDescendants->exists(w, ts))
            continue;

        findTempAncestors(g, EdgeData(w, ts), firstTs, tempAncestors, tempDescendants);
    }

    cunion = new StrongComponent(g->getVertexNo());
    if (nullptr == cunion) {
        return;
    }
    tempAncestors.for_each([&](int el) { cunion->insert(el); });
}

}