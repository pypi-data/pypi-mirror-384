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

#ifdef USE_TBB
using namespace tbb;
#endif

#ifdef MPI_IMPL
#include <mpi.h>
#endif

using namespace std;

namespace ParCycEnum {

extern int  timeWindow;
extern bool useCUnion;

extern bool invertSearch;

namespace {

    typedef HashMap BarrierMap;

    pair<int, int> getTimeInterval(Timestamp tstart, Timestamp timeWindow, int vstart, int vert, TimestampSet& tset,
                                   bool invert = false)
    {
        if (!invert) {
            auto it_start = (vstart >= vert) ? lower_bound(tset.begin(), tset.end(), tstart)
                                             : upper_bound(tset.begin(), tset.end(), tstart);
            auto it_end = upper_bound(it_start, tset.end(), tstart + timeWindow);
            return make_pair(it_start - tset.begin(), it_end - tset.begin());
        } else {
            auto it_end = (vstart >= vert) ? upper_bound(tset.begin(), tset.end(), tstart)
                                           : lower_bound(tset.begin(), tset.end(), tstart);
            auto it_start = lower_bound(tset.begin(), tset.end(), tstart - timeWindow);
            return make_pair(it_start - tset.begin(), it_end - tset.begin());
        }
    }

    /// Preprocessing for LC cycles

    void findKHopAncestors(Graph* g, int start, int k, BarrierMap*& spath, Timestamp tstart = -1, bool invert = false)
    {
        spath->setDefaultValue(k + 1);

        /// BFS k-hop
        // vertex and depth
        list<pair<int, int>> queue;

        spath->insert(start, 0);
        queue.push_back(make_pair(start, 0));

        while (!queue.empty()) {
            auto pair = queue.front();
            queue.pop_front();

            int vert  = pair.first;
            int depth = pair.second;

            if (depth >= k)
                continue;

            auto beginIt = !invert ? g->beginIn(vert) : g->beginOut(vert);
            auto endIt   = !invert ? g->endIn(vert) : g->endOut(vert);
            for (auto colelem = beginIt; colelem != endIt; colelem++) {
                int   w    = colelem->vertex;
                auto& tset = colelem->tstamps;

                // Prevent visiting loops
                if (w == vert)
                    continue;

                if (tstart != -1) {
                    if (!edgeInTimeInterval(tstart, timeWindow, start, w, tset, invert))
                        continue;
                } else {
                    if (w < start)
                        continue;
                }

                if (!spath->exists(w)) {
                    spath->insert(w, depth + 1);
                    queue.push_back(make_pair(w, depth + 1));
                }
            }
        }
    }

    /// ********************** Length-constrained Johnson's algorithm **********************

    void updateBarrier(Graph* g, int u, int l, Cycle* cycle, BarrierMap& bars, Timestamp tstart = -1,
                       bool unstacked = false, bool invert = false)
    {

        if (bars.at(u) > l || unstacked) {

            // Unblock the vertex
            bars.insert(u, l);

            // Iterate through the corresponding blocked list
            auto beginIt = !invert ? g->beginIn(u) : g->beginOut(u);
            auto endIt   = !invert ? g->endIn(u) : g->endOut(u);
            for (auto colelem = beginIt; colelem != endIt; colelem++) {
                int   w    = colelem->vertex;
                auto& tset = colelem->tstamps;

                // Prevent visiting loops
                if (w == u)
                    continue;

                if (tstart != -1) {
                    if (!edgeInTimeInterval(tstart, timeWindow, cycle->front(), w, tset, invert))
                        continue;
                } else {
                    if (w < cycle->front())
                        continue;
                }

                // Check if w exists in the cycle
                bool exists = false;
                for (int i = 1; i < cycle->size(); i++) {
                    if (cycle->at(i) == w) {
                        exists = true;
                        break;
                    }
                }

                // Recursivelly unblock
                if (!exists) {
                    updateBarrier(g, w, l + 1, cycle, bars, tstart, false, invert);
                }
            }
        }
    }

    int lenConstrainedJohnson(Graph* g, int vert, int k, Cycle* cycle, TimestampGroups* tg, BarrierMap& bars,
                              CycleHist& result, BarrierMap* spath = NULL, Timestamp tstart = -1, bool invert = false)
    {

        int F = k + 1;
        cycle->push_back(vert);

        if (vert == cycle->front()) {
            cycle->pop_back();
            recordCycle(cycle, result, tg);
            return 0;
        } else if (cycle->size() < k) {
            auto beginIt = !invert ? g->beginOut(vert) : g->beginIn(vert);
            auto endIt   = !invert ? g->endOut(vert) : g->endIn(vert);
            for (auto colelem = beginIt; colelem != endIt; colelem++) {
                auto& colElem = *colelem;
                int   w       = colelem->vertex;
                auto& tset    = colelem->tstamps;

                // Prevent visiting loops
                if (w == vert)
                    continue;

                // Check if w exists in the cycle
                bool exists = false;
                for (int i = 1; i < cycle->size(); i++) {
                    if (cycle->at(i) == w) {
                        exists = true;
                        break;
                    }
                }

                if (exists)
                    continue;

                TempEdge tedge;

                if (tstart != -1) {
                    if (tg == NULL) {
                        if (!edgeInTimeInterval(tstart, timeWindow, cycle->front(), vert, tset, invert))
                            continue;
                    } else {
                        auto ret_pair = getTimeInterval(tstart, timeWindow, cycle->front(), vert, tset, invert);
                        if (ret_pair.first >= ret_pair.second)
                            continue;
                        tedge = TempEdge(w, tset[ret_pair.first], &(colElem), ret_pair.first, ret_pair.second);
                    }
                } else {
                    if (w < cycle->front())
                        continue;
                }

                if ((w != cycle->front()) && !(!spath || (spath->at(w) + cycle->size() + 1 <= k)))
                    continue;

                if (cycle->size() + 1 + bars.at(w) <= k) {
                    if (tg)
                        tg->push_back(tedge);
                    int f = lenConstrainedJohnson(g, w, k, cycle, tg, bars, result, spath, tstart, invert);
                    if (tg)
                        tg->pop_back();

                    if (f != k + 1) {
                        F = min(F, f + 1);
                    }
                }
            }
        }

        if (F == k + 1)
            bars.insert(vert, k - cycle->size() + 1);
        else
            updateBarrier(g, vert, F, cycle, bars, tstart, true, invert);

        cycle->pop_back();

        return F;
    }

    /// ********************** Fine-grained length-constrained Johnson's algorithm ***********************

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

    struct ThreadDataGuard {
    public:
        ThreadDataGuard(Graph* gg, int kk, Timestamp tst, Cycle* c, TimestampGroups* t, BarrierMap* l, bool inv = false)
            : g(gg)
            , k(kk)
            , tstart(tst)
            , cycle(c)
            , tg(t)
            , bars(l)
            , invert(inv)
        {
        }

        ThreadDataGuard(ThreadDataGuard* guard, int pathSize)
            : g(guard->g)
            , k(guard->k)
            , tstart(guard->tstart)
            , invert(guard->invert)
        {
            // Copy the data from another thread
            {
                guard->dataLock.lock_shared();
                bars  = new BarrierMap(*(guard->bars));
                cycle = new Cycle(*(guard->cycle));
                if (guard->tg)
                    tg = guard->tg->clone(pathSize - 1);
                guard->dataLock.unlock_shared();
            }

            // Remove the invalid vertices
            while (cycle->size() > pathSize) {
                int lastVertex = cycle->back();
                cycle->pop_back();
                updateBarrier(g, lastVertex, 0, cycle, *bars, tstart, true, invert);
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
                delete bars;
                delete tg;
                cycle = NULL;
                bars  = NULL;
                tg    = NULL;
                delete this;
                return;
            }
            this->cntLock.unlock();
        }

        /// Input graph
        Graph* g = NULL;
        /// Length constraint
        int k;
        /// Starting time window
        Timestamp tstart = -1;

        /// Guarded data
        Cycle*           cycle = NULL;
        TimestampGroups* tg    = NULL;
        BarrierMap*      bars  = NULL;

        regMutexWrapper dataLock;
        // ompMutexWrapper dataLock;
    private:
        // Reference counter
        int refCount = 1;

        bool invert = false;

        spinlock cntLock;
        // ompMutexWrapper cntLock;
    };

    class LCCyclesTask
#ifdef USE_TBB
        : public tbb::task
#endif
    {
    public:
        LCCyclesTask(Graph* g, ConcurrentContainer<CycleHist>& pt_res, int v, TempEdge te, int kk, Cycle* cyc,
                     TimestampGroups* tgg, BarrierMap* l, ThreadDataGuard* tdg, LCCyclesTask* par = NULL,
                     BarrierMap* spats = NULL, Timestamp tst = -1, bool inv = false)
            : pt_chist(pt_res)
            , vert(v)
            , tedge(te)
            , cycle(cyc)
            , tg(tgg)
            , bars(l)
            , graph(g)
            , k(kk)
            , tstart(tst)
            , parent(par)
            , retF(kk + 1)
            , myShPaths(spats)
            , it(!inv ? g->beginOut(vert) : g->beginIn(vert))
            , invert(inv)
            , ownerThread(getThreadId())
            , pathSize(cyc->size())
            , thrData(tdg)
        {
        }

        virtual ~LCCyclesTask() { }
        TASK_RET execute();

        void copyOnSteal();

        void returnValue(int blen);
        // protected:

        TASK_RET SpawnTask();
        TASK_RET Continuation();

        ConcurrentContainer<CycleHist>& pt_chist;
        // Parameters
        int              vert;
        TempEdge         tedge;
        Cycle*           cycle = NULL;
        TimestampGroups* tg    = NULL;
        BarrierMap*      bars  = NULL;
        Graph*           graph = NULL;

        int       k      = 0; // max cycle length
        Timestamp tstart = -1;

        // Return
        LCCyclesTask* parent = NULL;
        spinlock      retLock;
        int           retF; // backward path length

        // Strongly connected components
        BarrierMap* myShPaths = NULL;

        // Continuation stealing
        bool            newTask = true;
        Graph::Iterator it;

        bool invert = false;

        // Task control
        bool isContinuation = false;
        int  ownerThread    = -1;
        bool stolenTask     = false;

#ifndef USE_TBB
        vector<LCCyclesTask*> childTasks;
#endif

        int              pathSize = 0;
        ThreadDataGuard* thrData  = NULL;
    };

    TASK_RET LCCyclesTask::execute()
    {
#ifdef USE_TBB
        if (!isContinuation)
            return SpawnTask();
        else
            return Continuation();
#else
        SpawnTask();
#pragma omp taskwait
        for (auto& child : childTasks)
            delete child;
        if (isContinuation)
            Continuation();
#endif
    }

    void LCCyclesTask::copyOnSteal()
    {
        /// Copy-on-steal
        int thisThreadId = getThreadId();
        // if (is_stolen_task()) {
        if (ownerThread != thisThreadId) {
            stolenTask  = true;
            ownerThread = thisThreadId;

            // Copy on steal
            ThreadDataGuard* newThrData = new ThreadDataGuard(thrData, pathSize);

            // Decrement the ref. count of the previous blocked map
            thrData->decrementRefCount();

            thrData = newThrData;
            // Update the pointers
            cycle = thrData->cycle;
            tg    = thrData->tg;
            bars  = thrData->bars;
        }
    }

    TASK_RET LCCyclesTask::SpawnTask()
    {
        copyOnSteal();

        /// If we are executing the task for the first time
        if (newTask) {
            newTask = false;
#ifdef USE_TBB
            set_ref_count(1);
#endif

            {
                thrData->dataLock.lock();
                cycle->push_back(vert);
                pathSize++;
                if (tg)
                    tg->push_back(tedge);
                thrData->dataLock.unlock();
            }
        }

#ifdef USE_TBB
        tbb::task* retTask = NULL;
#endif

        if (vert == cycle->front()) {
            {
                thrData->dataLock.lock();
                cycle->pop_back();
                pathSize--;
                thrData->dataLock.unlock();
            }
            auto& my_hist = pt_chist.local();
            recordCycle(cycle, my_hist, tg);
            {
                thrData->dataLock.lock();
                if (tg)
                    tg->pop_back();
                thrData->dataLock.unlock();
            }
            thrData->decrementRefCount();
            if (parent)
                parent->returnValue(0);

#ifndef USE_TBB
            return;
#else
            return retTask;
#endif
        } else if (cycle->size() < k) {

/// Iterate through the neighbors
#ifndef USE_TBB
            auto it = (!invert ? graph->beginOut(vert) : graph->beginIn(vert));
#endif
            while (it < (!invert ? graph->endOut(vert) : graph->endIn(vert))) {
                int   w        = it->vertex;
                auto& tset     = it->tstamps;
                auto& edgeData = *it;
                it++;

                TempEdge tedge;
                if (tstart != -1) {
                    if (tg == NULL) {
                        if (!edgeInTimeInterval(tstart, timeWindow, cycle->front(), vert, tset, invert))
                            continue;
                    } else {
                        auto ret_pair = getTimeInterval(tstart, timeWindow, cycle->front(), vert, tset, invert);
                        if (ret_pair.first >= ret_pair.second)
                            continue;
                        tedge = TempEdge(w, tset[ret_pair.first], &edgeData, ret_pair.first, ret_pair.second);
                    }
                } else {
                    if (w < cycle->front())
                        continue;
                }

                if ((w != cycle->front()) && !(!myShPaths || myShPaths->at(w) + cycle->size() + 1 <= k))
                    continue;

                // Check if w exists in the cycle
                bool exists = false;
                for (int i = 1; i < cycle->size(); i++) {
                    if (cycle->at(i) == w) {
                        exists = true;
                        break;
                    }
                }

                if (exists)
                    continue;

                if (cycle->size() + 1 + bars->at(w) <= k) {

                    thrData->incrementRefCount();

#ifndef USE_TBB
                    auto* a = new LCCyclesTask(graph, pt_chist, w, tedge, k, cycle, tg, bars, thrData, this, myShPaths,
                                               tstart, invert);
                    this->childTasks.push_back(a);

#pragma omp task firstprivate(a)
                    a->execute();
#else
                    increment_ref_count();
                    LCCyclesTask* a = new (allocate_child()) LCCyclesTask(graph, pt_chist, w, tedge, k, cycle, tg, bars,
                                                                          thrData, this, myShPaths, tstart, invert);

                    // Continuation stealing
                    if (it < (!invert ? graph->endOut(vert) : graph->endIn(vert))) {
                        recycle_to_reexecute();
                        return a;
                    } else
                        retTask = a;
#endif
                }
            }
        }

        isContinuation = true;

#ifdef USE_TBB
        recycle_as_safe_continuation();
        return retTask;
#endif
    }

    void LCCyclesTask::returnValue(int f)
    {
        retLock.lock();
        if (f != k + 1) {
            retF = min(retF, f + 1);
        }
        retLock.unlock();
    }

    TASK_RET LCCyclesTask::Continuation()
    {
        {
            thrData->dataLock.lock();

            if (retF == k + 1)
                bars->insert(vert, k - cycle->size() + 1);
            else
                updateBarrier(graph, vert, retF, cycle, *bars, tstart, true, invert);

            if (tg)
                tg->pop_back();
            cycle->pop_back();
            pathSize--;
            thrData->dataLock.unlock();
        }

        // Return
        if (parent)
            parent->returnValue(retF);

        thrData->decrementRefCount();

        if (!parent && myShPaths) {
            delete myShPaths;
            myShPaths = NULL;
        }

#ifdef USE_TBB
        return NULL;
#endif
    }

}

// COARSE-GRAINED ALGORITHM

void allLenConstrainedCyclesCoarseGrained(Graph* g, int k, CycleHist& result, int numThreads)
{
    int process_rank    = 0;
    int size_of_cluster = 1;

#ifdef MPI_IMPL
    MPI_Comm_size(MPI_COMM_WORLD, &size_of_cluster);
    MPI_Comm_rank(MPI_COMM_WORLD, &process_rank);
#endif

    ConcurrentContainer<CycleHist> pt_chist_jh;
    pt_chist_jh.setNumThreads(numThreads);

    parallelOuterLoop(g, numThreads, invertSearch, process_rank, size_of_cluster,
                      [&](int from, int to, Timestamp ts, GraphElemID eid) {
                          BarrierMap* spath = new BarrierMap(g->getVertexNo());
                          if (nullptr == spath) {
                              return;
                          }
                          if (useCUnion)
                              findKHopAncestors(g, from, k, spath, ts, invertSearch);

                          BarrierMap bars(g->getVertexNo());

                          Cycle* cycle = new Cycle();
                          if (nullptr == cycle)
                              return;
                          cycle->push_back(from);

                          TimestampGroups* tg = new TimestampGroups();
                          if (nullptr == tg)
                              return;
                          tg->push_back(TempEdge(to, ts, eid));

                          auto& my_hist = pt_chist_jh.local();
                          lenConstrainedJohnson(g, to, k + 1, cycle, tg, bars, my_hist, spath, ts, invertSearch);

                          if (cycle) {
                              delete cycle;
                              cycle = nullptr;
                          }
                          if (tg) {
                              delete tg;
                              tg = nullptr;
                          }
                          if (spath) {
                              delete spath;
                              spath = nullptr;
                          }
                      });

    combineCycleHistogram(pt_chist_jh, result);
}

// FINE-GRAINED ALGORITHM

namespace {
    class RootLCCyclesTask
#ifdef USE_TBB
        : public tbb::task
#endif
    {
    public:
        RootLCCyclesTask(Graph* _g, ConcurrentContainer<CycleHist>& pt_res, int k, int nthr, int rank = 0,
                         int nclust = 1)
            : isContinuation(false)
            , numThreads(nthr)
            , g(_g)
            , len(k)
            , pt_chist(pt_res)
            , process_rank(rank)
            , size_of_cluster(nclust)
        {
        }

        virtual ~RootLCCyclesTask() { }

        virtual TASK_RET execute();

    protected:
        bool   isContinuation;
        int    numThreads;
        Graph* g;
        int    len;

        ConcurrentContainer<CycleHist>& pt_chist;
        int                             process_rank;
        int                             size_of_cluster;
    };

    TASK_RET RootLCCyclesTask::execute()
    {
#ifdef USE_TBB
        set_ref_count(1);
#endif

        if (!isContinuation) {
            parallelOuterLoop(g, numThreads, invertSearch, process_rank, size_of_cluster,
                              [&](int from, int to, Timestamp ts, GraphElemID eid) {
                                  BarrierMap* spath = new BarrierMap(g->getVertexNo());
                                  if (nullptr == spath) {
                                      return;
                                  }
                                  if (useCUnion)
                                      findKHopAncestors(g, from, len, spath, ts, invertSearch);

                                  Cycle* cycle = new Cycle();
                                  if (nullptr == cycle)
                                      return;
                                  cycle->push_back(from);

                                  TimestampGroups* tg = new TimestampGroups();
                                  if (nullptr == tg)
                                      return;
                                  TempEdge tedge(to, ts, eid);

                                  BarrierMap* bars = new BarrierMap(g->getVertexNo());
                                  if (nullptr == bars)
                                      return;

                                  ThreadDataGuard* thrData
                                      = new ThreadDataGuard(g, len, ts, cycle, tg, bars, invertSearch);
                                  if (nullptr == thrData)
                                      return;
                                  SPAWN_SINGLE_TASK(LCCyclesTask(g, pt_chist, to, tedge, len + 1, cycle, tg, bars,
                                                                 thrData, NULL, spath, ts, invertSearch));
                              });

#ifdef USE_TBB
            isContinuation = true;
            recycle_as_safe_continuation();
#endif
        }

#ifdef USE_TBB
        return NULL;
#endif
    }
}

void allLenConstrainedCyclesFineGrained(Graph* g, int k, CycleHist& result, int numThreads)
{
    int process_rank    = 0;
    int size_of_cluster = 1;

#ifdef MPI_IMPL
    MPI_Comm_size(MPI_COMM_WORLD, &size_of_cluster);
    MPI_Comm_rank(MPI_COMM_WORLD, &process_rank);
#endif

#ifdef USE_TBB
    task_scheduler_init init(numThreads);
#endif

    ConcurrentContainer<CycleHist> pt_chist;
    pt_chist.setNumThreads(numThreads);

    SPAWN_ROOT_TASK(RootLCCyclesTask(g, pt_chist, k, numThreads, process_rank, size_of_cluster));

    combineCycleHistogram(pt_chist, result);
}

/// Edges arrive in batches
namespace {

    class RootBatchLCCycleTask
#ifdef USE_TBB
        : public tbb::task
#endif
    {
    public:
        RootBatchLCCycleTask(Graph* _g, int nthr, int _k, ConcurrentContainer<CycleHist>& _ch,
                             std::vector<CompressedEdge>* batch, bool tpar = false, bool inv = true)
            : numThreads(nthr)
            , taskPar(tpar)
            , invEdges(inv)
            , k(_k)
            , g(_g)
            , pt_chist(_ch)
            , batchOfEdges(batch)
        {
        }

        virtual ~RootBatchLCCycleTask() { }

        virtual TASK_RET execute();

        void runFineGrained(int fromV, int toV, Timestamp ts, GraphElemID eid);

        void runCoarseGrained(int fromV, int toV, Timestamp ts, GraphElemID eid);

    protected:
        bool                            isContinuation = false;
        int                             numThreads;
        bool                            taskPar  = false;
        bool                            invEdges = true;
        int                             k;
        Graph*                          g;
        ConcurrentContainer<CycleHist>& pt_chist;

        std::vector<CompressedEdge>* batchOfEdges = NULL;
    };

    void RootBatchLCCycleTask::runFineGrained(int fromV, int toV, Timestamp ts, GraphElemID eid)
    {
        BarrierMap* spath = new BarrierMap(g->getVertexNo());
        if (nullptr == spath) {
            return;
        }
        if (useCUnion)
            findKHopAncestors(g, fromV, k, spath, ts, invEdges);

        Cycle* cycle = new Cycle();
        if (nullptr == cycle)
            return;
        cycle->push_back(fromV);

        TimestampGroups* tg = new TimestampGroups();
        if (nullptr == tg)
            return;
        TempEdge tedge(toV, ts, eid);

        BarrierMap* bars = new BarrierMap(g->getVertexNo());
        if (nullptr == bars)
            return;
        ThreadDataGuard* thrData = new ThreadDataGuard(g, k, ts, cycle, tg, bars, invEdges);
        if (nullptr == thrData)
            return;
        SPAWN_ROOT_TASK(
            LCCyclesTask(g, pt_chist, toV, tedge, k + 1, cycle, tg, bars, thrData, NULL, spath, ts, invEdges));
    }

    void RootBatchLCCycleTask::runCoarseGrained(int fromV, int toV, Timestamp ts, GraphElemID eid)
    {
        BarrierMap* spath = new BarrierMap(g->getVertexNo());
        if (nullptr == spath) {
            return;
        }
        if (useCUnion)
            findKHopAncestors(g, fromV, k, spath, ts, invEdges);

        BarrierMap bars(g->getVertexNo());

        Cycle* cycle = new Cycle();
        if (nullptr == cycle)
            return;
        cycle->push_back(fromV);

        TimestampGroups* tg = new TimestampGroups();
        if (nullptr == tg)
            return;
        tg->push_back(TempEdge(toV, ts, eid));

        auto& my_hist = pt_chist.local();
        lenConstrainedJohnson(g, toV, k + 1, cycle, tg, bars, my_hist, spath, ts, invEdges);

        if (nullptr != cycle) {
            delete cycle;
            cycle = nullptr;
        }
        if (nullptr != tg) {
            delete tg;
            tg = nullptr;
        }
        if (nullptr != spath) {
            delete spath;
            spath = nullptr;
        }
    }

    TASK_RET RootBatchLCCycleTask::execute()
    {
        int process_rank    = 0;
        int size_of_cluster = 1;

#ifdef MPI_IMPL
        MPI_Comm_size(MPI_COMM_WORLD, &size_of_cluster);
        MPI_Comm_rank(MPI_COMM_WORLD, &process_rank);
#endif

        if (!isContinuation) {
            parallelOuterLoopBatch(batchOfEdges, numThreads, invEdges, process_rank, size_of_cluster,
                                   [&](int from, int to, Timestamp ts, GraphElemID eid) {
                                       if (taskPar)
                                           runFineGrained(from, to, ts, eid);
                                       else
                                           runCoarseGrained(from, to, ts, eid);
                                   });

#ifdef USE_TBB
            recycle_as_safe_continuation();
            isContinuation = true;
#endif
        }

#ifdef USE_TBB
        return NULL;
#endif
    }

}

void allLenConstrainedCyclesCoarseGrainedBatch(Graph* g, int k, std::vector<CompressedEdge>& batch,
                                               ConcurrentContainer<CycleHist>& pt_cycleHist, int numThreads,
                                               bool invEdges)
{
#ifdef USE_TBB
    task_scheduler_init init(numThreads);
#endif

    SPAWN_ROOT_TASK(RootBatchLCCycleTask(g, numThreads, k, pt_cycleHist, &batch, false, invEdges));
}

void allLenConstrainedCyclesFineGrainedBatch(Graph* g, int k, std::vector<CompressedEdge>& batch,
                                             ConcurrentContainer<CycleHist>& pt_cycleHist, int numThreads,
                                             bool invEdges)
{
#ifdef USE_TBB
    task_scheduler_init init(numThreads);
#endif

    SPAWN_ROOT_TASK(RootBatchLCCycleTask(g, numThreads, k, pt_cycleHist, &batch, true, invEdges));
}

}