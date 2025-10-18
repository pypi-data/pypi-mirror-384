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

#ifndef _CYCLE_ENUMERATION_
#define _CYCLE_ENUMERATION_

#include <map>
#include <list>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include "CycleEnumGraph.h"
#include "DataStructs.h"
#include "Macros.h"
#include "ParallelOuterLoop.h"

using namespace std;

namespace ParCycEnum {

const Timestamp NINF = -1;
const Timestamp PINF = std::numeric_limits<Timestamp>::max();

struct TempEdge {
    int         vertex;
    Timestamp   first_ts;
    GraphElemID first_eid;

    ColElem* edgeData = NULL;
    int      ind_begin, ind_end;

    TempEdge()
        : vertex(-1)
        , ind_begin(-1)
        , ind_end(-1)
    {
    }
    TempEdge(int v, Timestamp ft, ColElem* c, int ib, int ie)
        : vertex(v)
        , first_ts(ft)
        , edgeData(c)
        , ind_begin(ib)
        , ind_end(ie)
    {
    }

    TempEdge(int v, Timestamp ft, GraphElemID id)
        : vertex(v)
        , first_ts(ft)
        , first_eid(id)
        , edgeData(NULL)
        , ind_begin(-1)
        , ind_end(-1)
    {
    }
};

typedef ConcurrentList<int>         Cycle;
typedef ConcurrentList<Timestamp>   Timestamps;
typedef ConcurrentList<TempEdge>    TimestampGroups;
typedef HashSet                     BlockedSet;
typedef unordered_map<int, HashSet> BlockedList;
typedef map<int, uint64_t>          CycleHist;
typedef HashSet                     StrongComponent;
typedef list<Cycle*>                CycleList;

/// Recording cycles
void recordCycle(Cycle* current, CycleHist& result, TimestampGroups* tg = NULL);
void recordBundledCycle(Cycle* current, TimestampGroups* tg, CycleHist& result, bool invert = false);
void combineCycleHistogram(ConcurrentContainer<CycleHist>& pt_chist, CycleHist& result);

bool edgeInTimeInterval(Timestamp tstart, Timestamp timeWindow, int vstart, int vert, TimestampSet& tset,
                        bool invert = false);

typedef VectorPath<TempEdge> TempPathBundle;
typedef VectorPath<int>      Path;
typedef HashMap              BlockedMap;

void processCycleBundle(vector<int>& cycle, vector<vector<GraphElemID>>& edgeIDs);

/// Enumerating simple cycles within time window
void allCyclesJohnsonCoarseGrainedTW(Graph* g, CycleHist& result, int numThreads);
void allCyclesJohnsonFineGrainedTW(Graph* g, CycleHist& result, int numThreads);

/// Enumerating length-constrained cycles

void allLenConstrainedCyclesCoarseGrained(Graph* g, int k, CycleHist& result, int numThreads);
void allLenConstrainedCyclesFineGrained(Graph* g, int k, CycleHist& result, int numThreads);

void allLenConstrainedCyclesCoarseGrainedBatch(Graph* g, int k, std::vector<CompressedEdge>& batch,
                                               ConcurrentContainer<CycleHist>& pt_cycleHist, int numThreads,
                                               bool invEdges = true);
void allLenConstrainedCyclesFineGrainedBatch(Graph* g, int k, std::vector<CompressedEdge>& batch,
                                             ConcurrentContainer<CycleHist>& pt_cycleHist, int numThreads,
                                             bool invEdges = true);

/// Enumerating temporal cycles
void allCyclesTempJohnsonFineGrained(Graph* g, CycleHist& result, int numThreads);
void allCyclesTempJohnsonCoarseGrained(Graph* g, CycleHist& result, int numThreads);
void allCyclesTempJohnsonFineGrainedNew(Graph* g, CycleHist& result, int numThreads);
void allCyclesTempJohnsonCoarseGrainedNew(Graph* g, CycleHist& result, int numThreads);

void allCyclesTempJohnsonCoarseGrainedBatch(Graph* g, std::vector<CompressedEdge>& batch,
                                            ConcurrentContainer<CycleHist>& pt_cycleHist, int numThreads,
                                            bool invEdges = true);
void allCyclesTempJohnsonFineGrainedBatch(Graph* g, std::vector<CompressedEdge>& batch,
                                          ConcurrentContainer<CycleHist>& pt_cycleHist, int numThreads,
                                          bool invEdges = true);

/// Preprocessing functions
Timestamp findCycleUnions(Graph* g, EdgeData startEdge, int startVert, Timestamp timeWindow, StrongComponent*& cunion);
// Only searches for ancestors or descendants, depending on invert
void findCycleUnions(Graph* g, EdgeData startEdge, int startVert, Timestamp timeWindow, StrongComponent*& cunion,
                     bool invert, bool temporal = true);
void cycleUnionExecTime(Graph* g, int numThreads);

// The previous findCycleUnions function divided into two functions
Timestamp findMaxTs(Graph* g, EdgeData startEdge, int startVert, Timestamp timeWindow, BlockedMap*& tempDescendants);
void findCycleUnions(Graph* g, EdgeData startEdge, int startVert, Timestamp timeWindow, BlockedMap* tempDescendants,
                     StrongComponent*& cunion);

/// dfs subroutine
bool findPathTemp(Graph* g, TempEdge e, EdgeData start, HashMapStack& blocked, TempPathBundle*& path,
                  StrongComponent* cunion = NULL, bool invEdges = false, bool nopath = false);
bool dfsPruneTemp(Graph* g, TempEdge e, EdgeData start, HashMapStack& blocked, TempPathBundle*& path,
                  StrongComponent* cunion = NULL, bool invEdges = false, bool nopath = false);
bool findPath(Graph* g, int u, int start, HashSetStack& blocked, Path*& path, StrongComponent* cunion = NULL,
              Timestamp tstart = -1, bool invEdges = false);
bool dfsPrune(Graph* g, int u, int start, HashSetStack& blocked, Path*& path, StrongComponent* cunion = NULL,
              Timestamp tstart = -1, bool invEdges = false);

struct TmpEdge {
    int       from;
    Timestamp to, ts;
    TmpEdge(int _f = 0, Timestamp _t = 0, Timestamp _ts = 0)
        : from(_f)
        , to(_t)
        , ts(_ts)
    {
    }
};

typedef unordered_map<int, Timestamp>          UnblockList;
typedef unordered_map<int, UnblockList>        UnblockLists;
typedef unordered_map<int, unordered_set<int>> SummarySet;
typedef unordered_map<int, SummarySet>         SummarySets;
typedef vector<TmpEdge>                        EdgeList;

class ClosingTimes {
private:
    unordered_map<int, Timestamp> elems;
    Timestamp                     def = PINF;

public:
    ClosingTimes(int size = 0) { }
    void insert(int node, Timestamp ts)
    {
        if (ts == def)
            elems.erase(node);
        else
            elems[node] = ts;
    }
    Timestamp at(int node)
    {
        auto it = elems.find(node);
        if (it == elems.end())
            return def;
        return it->second;
    }
    void                                    clear() { elems.clear(); }
    int                                     size() { return elems.size(); }
    unordered_map<int, Timestamp>::iterator begin() { return elems.begin(); }
    unordered_map<int, Timestamp>::iterator end() { return elems.end(); }

    void setDefaultValue(Timestamp d) { def = d; }
};

struct Seed {
    int                root;
    Timestamp          ts, te, tn;
    unordered_set<int> cands;
    Seed(int _r = -1, Timestamp _ts = -1, Timestamp _te = -1)
        : root(_r)
        , ts(_ts)
        , te(_te)
        , tn(-1)
    {
    }
};

}

#endif