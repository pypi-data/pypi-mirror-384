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
#include <set>
#include <unordered_map>
#include <stack>
#include <utility>
#include <ctime>
#include <chrono>
#include <queue>
#include <vector>
#include <atomic>
#include <memory>

#ifdef USE_TBB
using namespace tbb;
#endif

#ifdef MPI_IMPL
#include <mpi.h>
#endif

using namespace std;

namespace ParCycEnum {

extern Timestamp timeWindow;
extern bool      useCUnion;
extern bool      invertSearch;

namespace {

    ConcurrentContainer<CycleHist> pt_chist_jh;

    /// Blocking and unblocking vertices

    void unblockJohnson(int node, BlockedSet& blocked, BlockedList& BMap)
    {
        blocked.remove(node);
        auto it = BMap.find(node);
        if (it == BMap.end())
            return;
        it->second.for_each([&](int w) {
            if (blocked.exists(w)) {
                unblockJohnson(w, blocked, BMap);
            }
        });
        BMap.erase(it);
    }

    void addToBMap(Graph* g, int node, BlockedList& BMap, StrongComponent* scc = NULL, int s = -1,
                   Timestamp tstart = -1, bool invert = false)
    {
        auto beginIt = !invert ? g->beginOut(node) : g->beginIn(node);
        auto endIt   = !invert ? g->endOut(node) : g->endIn(node);

        for (auto colelem = beginIt; colelem != endIt; colelem++) {
            int   w    = colelem->vertex;
            auto& tset = colelem->tstamps;

            // Prevent visiting loops
            if (w == node)
                continue;

            if (s != -1 && tstart != -1 && !edgeInTimeInterval(tstart, timeWindow, s, node, tset, invert))
                continue;

            if (!scc || scc->exists(w)) {
                BMap[w].insert(node);
            }
        }
    }

#ifndef USE_TBB
    int getThreadId() { return omp_get_thread_num(); }
#else
    tbb::atomic<int>                     globalId = 0;
    tbb::enumerable_thread_specific<int> threadIds;

    int getThreadId()
    {
        bool  exists = true;
        auto& myid   = threadIds.local(exists);
        if (!exists)
            myid = globalId++;
        return myid;
    }
#endif

    /// ********************** Task-parallel Johnson's algorithm ***********************

    struct ThreadDataGuard {
    public:
        ThreadDataGuard(Cycle* c, BlockedSet* b, BlockedList* bm)
            : cycle(c)
            , blocked(b)
            , blkMap(bm)
            , refCount(1)
        {
        }

        ThreadDataGuard(ThreadDataGuard* guard, int pathSize)
            : refCount(1)
        {
            // Copy the data from another thread
            {
                guard->dataLock.lock_shared();
                blocked = new BlockedSet(*(guard->blocked));
                blkMap  = new BlockedList(*(guard->blkMap));
                cycle   = new Cycle(*(guard->cycle));
                guard->dataLock.unlock_shared();
            }

            // Remove the invalid vertices
            while (cycle->size() > pathSize) {
                int lastVertex = cycle->back();
                cycle->pop_back();
                unblockJohnson(lastVertex, *blocked, *blkMap);
            }
        }

        ThreadDataGuard(const ThreadDataGuard&) = delete;
        ThreadDataGuard& operator=(const ThreadDataGuard&) = delete;

        void incrementRefCount()
        {
            this->cntLock.lock();
            refCount++;
            this->cntLock.unlock();
        }

        void decrementRefCount()
        {
            this->cntLock.lock();
            refCount--;
            if (refCount <= 0) {
                delete cycle;
                delete blocked;
                delete blkMap;
                cycle   = NULL;
                blocked = NULL;
                blkMap  = NULL;
                delete this;
                return;
            }
            this->cntLock.unlock();
        }

        /// Guarded data
        Cycle*       cycle   = NULL;
        BlockedSet*  blocked = NULL;
        BlockedList* blkMap  = NULL;

        regMutexWrapper dataLock;

    private:
        // Reference counter
        int refCount = 1;

        spinlock cntLock;
    };

    class JohnsonsTask
#ifdef USE_TBB
        : public tbb::task
#endif
    {
    public:
        JohnsonsTask(Graph* g, int v, Cycle* cyc, BlockedSet* blk, BlockedList* bmap, ThreadDataGuard* tdg,
                     JohnsonsTask* par = NULL, StrongComponent* cu = NULL, bool inv = false)
            : vert(v)
            , cycle(cyc)
            , blocked(blk)
            , blkMap(bmap)
            , graph(g)
            , cunion(cu)
            , parent(par)
            , retCycleFound(false)
            , invert(inv)
            , it(!inv ? g->beginOut(vert) : g->beginIn(vert))
            , ownerThread(getThreadId())
            , pathSize(cyc->size())
            , thrData(tdg)
        {
        }

        JohnsonsTask(Graph* g, int v, Timestamp tst, Cycle* cyc, BlockedSet* blk, BlockedList* bmap,
                     ThreadDataGuard* tdg, JohnsonsTask* par = NULL, StrongComponent* cu = NULL, bool inv = false)
            : vert(v)
            , tstart(tst)
            , cycle(cyc)
            , blocked(blk)
            , blkMap(bmap)
            , graph(g)
            , cunion(cu)
            , parent(par)
            , retCycleFound(false)
            , invert(inv)
            , it(!inv ? g->beginOut(vert) : g->beginIn(vert))
            , ownerThread(getThreadId())
            , pathSize(cyc->size())
            , thrData(tdg)
        {
        }

        virtual ~JohnsonsTask() { }

        TASK_RET execute();

        void copyOnSteal();

        void returnValue(bool found);
        // protected:

        TASK_RET SpawnTask();

        TASK_RET Continuation();

        // Parameters
        int              vert;
        Timestamp        tstart  = -1;
        Cycle*           cycle   = NULL;
        BlockedSet*      blocked = NULL;
        BlockedList*     blkMap  = NULL;
        Graph*           graph   = NULL;
        StrongComponent* cunion  = NULL;

        // Return
        JohnsonsTask*     parent = NULL;
        std::atomic<bool> retCycleFound;

        bool invert = false;

        // Continuation stealing
        bool            newTask = true;
        Graph::Iterator it;

        // Task control
        bool isContinuation = false;
        int  ownerThread    = -1;
        bool stolenTask     = false;

#ifndef USE_TBB
        vector<JohnsonsTask*> childTasks;
#endif

        int              pathSize = 0;
        ThreadDataGuard* thrData  = NULL;
    };

    TASK_RET JohnsonsTask::execute()
    {
#ifdef USE_TBB
        TASK_RET ret = NULL;
        if (!isContinuation)
            ret = SpawnTask();
        else
            ret = Continuation();
        return ret;
#else
        SpawnTask();
#pragma omp taskwait
        for (auto& child : childTasks)
            delete child;
        Continuation();
#endif
    }

    void JohnsonsTask::copyOnSteal()
    {
        int thisThreadId = getThreadId();
        if (ownerThread != thisThreadId) {
            stolenTask  = true;
            ownerThread = thisThreadId;

            // Copy on steal
            ThreadDataGuard* newThrData = new ThreadDataGuard(thrData, pathSize);

            // Decrement the ref. count of the previous blocked map
            thrData->decrementRefCount();

            thrData = newThrData;
            // Update the pointers
            cycle   = thrData->cycle;
            blocked = thrData->blocked;
            blkMap  = thrData->blkMap;
        }
    };

    TASK_RET JohnsonsTask::SpawnTask()
    {
        /// Copy-on-steal
        copyOnSteal();

        /// If we are executing the task for the first time
        if (newTask) {
#ifdef USE_TBB
            set_ref_count(1);
#endif
            newTask = false;
            {
                thrData->dataLock.lock();
                cycle->push_back(vert);
                pathSize++;
                blocked->insert(vert);
                thrData->dataLock.unlock();
            }
        }

#ifdef USE_TBB
        tbb::task* retTask = NULL;
#endif

        /// Iterate through the neighbors
        while (it < (!invert ? graph->endOut(vert) : graph->endIn(vert))) {
            int   w    = it->vertex;
            auto& tset = it->tstamps;
            it++;

            // Prevent visiting loops
            if (w == vert)
                continue;

            if (tstart != -1) {
                if (!edgeInTimeInterval(tstart, timeWindow, cycle->front(), vert, tset, invert))
                    continue;
            }

            /// Skip if a vertex is not in the cycle union
            if ((cunion != NULL) && (!cunion->exists(w)))
                continue;

            if (w == cycle->front()) {
                auto& my_hist = pt_chist_jh.local();
                recordCycle(cycle, my_hist);
                retCycleFound = true;
            } else if (((tstart != -1) || ((tstart == -1) && (w > cycle->front()))) && !blocked->exists(w)) {

                thrData->incrementRefCount();

#ifndef USE_TBB
                JohnsonsTask* a
                    = new JohnsonsTask(graph, w, tstart, cycle, blocked, blkMap, thrData, this, cunion, invert);
                this->childTasks.push_back(a);

#pragma omp task firstprivate(a)
                a->execute();
#else
                JohnsonsTask* a = new (allocate_child())
                    JohnsonsTask(graph, w, tstart, cycle, blocked, blkMap, thrData, this, cunion, invert);

                increment_ref_count();

                /// Continuation stealing
                if (it < (!invert ? graph->endOut(vert) : graph->endIn(vert))) {
                    recycle_to_reexecute();
                    return a;
                } else
                    retTask = a;
#endif
            }
        }

        isContinuation = true;

#ifdef USE_TBB
        recycle_as_safe_continuation();
        return retTask;
#endif
    }

    void JohnsonsTask::returnValue(bool found)
    {
        if (found)
            retCycleFound = true;
    };

    TASK_RET JohnsonsTask::Continuation()
    {
        int v = cycle->back();

        if (retCycleFound) {
            thrData->dataLock.lock();
            unblockJohnson(v, *thrData->blocked, *thrData->blkMap);
            thrData->dataLock.unlock();
        } else {
            thrData->dataLock.lock();
            if (tstart == -1)
                addToBMap(graph, v, *thrData->blkMap, NULL, -1, -1, invert);
            else
                addToBMap(graph, v, *thrData->blkMap, NULL, cycle->front(), tstart, invert);
            thrData->dataLock.unlock();
        }

        thrData->dataLock.lock();
        cycle->pop_back();
        thrData->dataLock.unlock();

        // Return
        if (parent)
            parent->returnValue(retCycleFound);

        thrData->decrementRefCount();
#ifdef USE_TBB
        return NULL;
#endif
    }
}
/// ************ Johnson algorithm with time window ************

// Johnsons algorithm
bool cyclesJohnsonTW(Graph* g, int vert, Timestamp tstart, Cycle* cycle, BlockedSet& blocked, BlockedList& BMap,
                     CycleHist& result, StrongComponent* cunion, bool invert)
{

    bool cycleFound = false;
    cycle->push_back(vert);
    blocked.insert(vert);

    auto beginIt = !invert ? g->beginOut(vert) : g->beginIn(vert);
    auto endIt   = !invert ? g->endOut(vert) : g->endIn(vert);
    for (auto colelem = beginIt; colelem != endIt; colelem++) {
        int   w    = colelem->vertex;
        auto& tset = colelem->tstamps;

        // Prevent visiting loops
        if (w == vert)
            continue;

        if (!edgeInTimeInterval(tstart, timeWindow, cycle->front(), vert, tset, invert))
            continue;

        if (cunion && !cunion->exists(w))
            continue;

        if (w == cycle->front()) {
            recordCycle(cycle, result);
            cycleFound = true;
        } else if (!blocked.exists(w)) {
            if (cyclesJohnsonTW(g, w, tstart, cycle, blocked, BMap, result, cunion, invert))
                cycleFound = true;
        }
    }

    cycle->pop_back();
    if (cycleFound)
        unblockJohnson(vert, blocked, BMap);
    else
        addToBMap(g, vert, BMap, NULL, cycle->front(), tstart, invert);

    return cycleFound;
}

namespace {
    class RootJohnTask
#ifdef USE_TBB
        : public tbb::task
#endif
    {
    public:
        RootJohnTask(Graph* _g, int nthr, int rank = 0, int nclust = 1)
            : isContinuation(false)
            , numThreads(nthr)
            , g(_g)
            , process_rank(rank)
            , size_of_cluster(nclust)
        {
        }

        virtual ~RootJohnTask() { }

        virtual TASK_RET execute();

    protected:
        bool   isContinuation = false;
        int    numThreads;
        Graph* g;

        int process_rank;
        int size_of_cluster;
    };

    TASK_RET RootJohnTask::execute()
    {
#ifdef USE_TBB
        set_ref_count(1);
#endif

        if (!isContinuation) {
            parallelOuterLoop(g, numThreads, invertSearch, process_rank, size_of_cluster,
                              [&](int from, int to, Timestamp ts, GraphElemID eid) {
                                  StrongComponent* cunion = NULL;
                                  if (useCUnion)
                                      findCycleUnions(g, EdgeData(to, ts), from, timeWindow, cunion, invertSearch,
                                                      false);

                                  BlockedSet* blocked = new BlockedSet(g->getVertexNo());
                                  if (nullptr == blocked)
                                      return; /*TODO need to introduce try and catch with throw in all the snapML code*/
                                  BlockedList* BMap = new BlockedList;
                                  if (nullptr == BMap)
                                      return;
                                  Cycle* cycle = new Cycle();
                                  if (nullptr == cycle)
                                      return;
                                  cycle->push_back(from);

                                  ThreadDataGuard* thrData = new ThreadDataGuard(cycle, blocked, BMap);

                                  SPAWN_SINGLE_TASK(JohnsonsTask(g, to, ts, cycle, blocked, BMap, thrData, NULL, cunion,
                                                                 invertSearch));
                              });

            isContinuation = true;
#ifdef USE_TBB
            recycle_as_safe_continuation();
#endif
        }

#ifdef USE_TBB
        return NULL;
#endif
    }
}

/// ************ Johnson algorithm with time window - top level ************

void allCyclesJohnsonCoarseGrainedTW(Graph* g, CycleHist& result, int numThreads)
{
    int process_rank    = 0;
    int size_of_cluster = 1;

#ifdef USE_TBB
    task_scheduler_init init(numThreads);
#endif

#ifdef MPI_IMPL
    MPI_Comm_size(MPI_COMM_WORLD, &size_of_cluster);
    MPI_Comm_rank(MPI_COMM_WORLD, &process_rank);
#endif

    ConcurrentContainer<CycleHist> pt_chist_jh;
    pt_chist_jh.setNumThreads(numThreads);

    parallelOuterLoop(g, numThreads, invertSearch, process_rank, size_of_cluster,
                      [&](int from, int to, Timestamp ts, GraphElemID eid) {
                          auto& my_hist = pt_chist_jh.local();

                          StrongComponent* cunion = NULL;
                          if (useCUnion)
                              findCycleUnions(g, EdgeData(to, ts), from, timeWindow, cunion, invertSearch, false);

                          BlockedSet  blocked(g->getVertexNo());
                          BlockedList BMap;
                          Cycle*      cycle = new Cycle();
                          if (nullptr == cycle)
                              return;
                          cycle->push_back(from);

                          cyclesJohnsonTW(g, to, ts, cycle, blocked, BMap, my_hist, cunion, invertSearch);

                          if (cycle) {
                              delete cycle;
                              cycle = nullptr;
                          }
                      });

    combineCycleHistogram(pt_chist_jh, result);
}

void allCyclesJohnsonFineGrainedTW(Graph* g, CycleHist& result, int numThreads)
{
    int process_rank    = 0;
    int size_of_cluster = 1;

    pt_chist_jh.clear();
    pt_chist_jh.setNumThreads(numThreads);

#ifdef USE_TBB
    task_scheduler_init init(numThreads);
#endif

#ifdef MPI_IMPL
    MPI_Comm_size(MPI_COMM_WORLD, &size_of_cluster);
    MPI_Comm_rank(MPI_COMM_WORLD, &process_rank);
#endif

    SPAWN_ROOT_TASK(RootJohnTask(g, numThreads, process_rank, size_of_cluster));

    combineCycleHistogram(pt_chist_jh, result);
}

}