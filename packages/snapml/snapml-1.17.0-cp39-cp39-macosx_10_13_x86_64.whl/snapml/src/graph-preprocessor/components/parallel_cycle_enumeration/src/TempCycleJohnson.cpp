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
#include <iostream>
#include <fstream>
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
extern bool      disablePathBundling;
extern int       maxTempCycle;
extern bool      invertSearch;

///************************** Single-threaded temporal Johnson implementation ************************************

void unblock2scent(Graph* g, int node, Timestamp lastts, ClosingTimes& ctime, UnblockLists& Ulists, bool invert = false)
{
    const Timestamp DEF_TS = (!invert ? NINF : PINF);

    if (!invert ? lastts > ctime.at(node) : lastts < ctime.at(node)) {
        ctime.insert(node, lastts);

        vector<pair<int, Timestamp>> tmpArray;
        tmpArray.reserve(Ulists[node].size());

        auto it = Ulists[node].begin();
        while (it != Ulists[node].end()) {
            if (!invert ? it->second < lastts : it->second > lastts) {
                int w = it->first;
                it    = Ulists[node].erase(it);

                Timestamp new_blocked_ts = DEF_TS;
                Timestamp prev_ts        = DEF_TS;

                bool node_found = false;

                auto beginIt = !invert ? g->beginOut(w) : g->beginIn(w);
                auto endIt   = !invert ? g->endOut(w) : g->endIn(w);
                for (auto colelem = beginIt; colelem < endIt; colelem++) {
                    int   u    = colelem->vertex;
                    auto& tset = colelem->tstamps;

                    // Prevent visiting loops
                    if (u == w)
                        continue;

                    for (auto ts : tset) {
                        if (u == node) {
                            node_found = true;
                            if (!invert) {
                                if (ts < lastts)
                                    prev_ts = max(ts, prev_ts);
                                if (ts >= lastts) {
                                    if (new_blocked_ts == DEF_TS)
                                        new_blocked_ts = ts;
                                    else
                                        new_blocked_ts = min(new_blocked_ts, ts);
                                }
                            } else {
                                if (ts > lastts)
                                    prev_ts = min(ts, prev_ts);
                                if (ts <= lastts) {
                                    if (new_blocked_ts == DEF_TS)
                                        new_blocked_ts = ts;
                                    else
                                        new_blocked_ts = max(new_blocked_ts, ts);
                                }
                            }
                        }
                        if (node_found && u != node)
                            break;
                    }
                }

                if (new_blocked_ts != DEF_TS)
                    tmpArray.push_back(std::make_pair(w, new_blocked_ts));
                unblock2scent(g, w, prev_ts, ctime, Ulists, invert);
            } else
                it++;
        }

        for (auto edge : tmpArray)
            Ulists[node].insert(edge);
    }
}

void extend2scent(Graph* g, int node, Timestamp ts, UnblockList& Ul, bool invert = false)
{
    auto it = Ul.find(node);
    if (it == Ul.end() || (it != Ul.end() && (!invert ? it->second > ts : it->second < ts))) {
        Ul[node] = ts;
    }
}

bool cycles2scent(Graph* g, EdgeData e, Cycle* current, Timestamps* tss, ClosingTimes& ctime, UnblockLists& Ulists,
                  CycleHist& result, Seed* seed = NULL, bool invert = false)
{

    // We have not found the cycle, but it might be here, so we need to unlock
    if (maxTempCycle != -1 && current->size() > maxTempCycle - 1)
        return true;

    const Timestamp DEF_TS = (!invert ? NINF : PINF);

    current->push_back(e.vertex);

    tss->push_back(e.tstamp);
    ctime.insert(e.vertex, e.tstamp);

    Timestamp lastp      = DEF_TS;
    Timestamp end_tstamp = !invert ? timeWindow + tss->front() : tss->front() - timeWindow;
    if (!invert && seed != NULL && seed->te != -1)
        end_tstamp = seed->te; // ??

    auto beginIt = !invert ? g->beginOut(e.vertex) : g->beginIn(e.vertex);
    auto endIt   = !invert ? g->endOut(e.vertex) : g->endIn(e.vertex);

    for (auto colelem = beginIt; colelem < endIt; colelem++) {
        int   w    = colelem->vertex;
        auto& tset = colelem->tstamps;

        // Prevent visiting loops
        if (w == e.vertex)
            continue;

        auto it_start = tset.begin();
        auto it_end   = tset.end();

        if (tss->size() != 0) {
            if (!invert) {
                it_start = upper_bound(tset.begin(), tset.end(), e.tstamp);
                it_end   = upper_bound(it_start, tset.end(), end_tstamp);
            } else {
                it_start = lower_bound(tset.begin(), tset.end(), end_tstamp);
                it_end   = lower_bound(it_start, tset.end(), e.tstamp);
            }
        }

        // Skip vertex
        if ((it_start >= it_end) || ((seed != NULL) && (seed->cands.find(w) == seed->cands.end())))
            continue;

        for (auto it = !invert ? it_start : (it_end - 1); !invert ? (it != it_end) : (it != (it_start - 1));
             !invert ? (it++) : (it--)) {
            Timestamp ts = *it;

            if (w == current->front()) {
                if (!invert ? (ts > lastp) : (ts < lastp))
                    lastp = ts;
                tss->push_back(ts);
                recordCycle(current, result);
                tss->pop_back();
            } else {
                bool pass = false;
                if (!invert ? ctime.at(w) > ts : ctime.at(w) < ts) {
                    pass = cycles2scent(g, EdgeData(w, ts), current, tss, ctime, Ulists, result, seed, invert);
                } else {
                    extend2scent(g, e.vertex, ts, Ulists[w], invert);
                }

                if (pass) {
                    if (!invert ? (ts > lastp) : (ts < lastp))
                        lastp = ts;
                } else {
                    break;
                }
            }
        }
    }

    if (lastp != DEF_TS) {
        unblock2scent(g, e.vertex, lastp, ctime, Ulists, invert);
    }

    current->pop_back();
    tss->pop_back();

    if (lastp == DEF_TS) {
        extend2scent(g, current->back(), e.tstamp, Ulists[e.vertex], invert);
    }

    return (lastp != DEF_TS);
}

Timestamp cycles2scentBundled(Graph* g, EdgeData e, EdgeData start, Cycle* current, TimestampGroups* tg,
                              ClosingTimes& ctime, UnblockLists& Ulists, CycleHist& result, Seed* seed = NULL,
                              bool invert = false)
{

    const Timestamp DEF_TS = (!invert ? NINF : PINF);

    // We have not found the cycle, but it might be here, so we need to unlock
    if (maxTempCycle != -1 && current->size() > maxTempCycle - 1)
        return (invert ? NINF : PINF);

    current->push_back(e.vertex);

    if (tg->size() != 0) {
        Timestamp tmin = tg->back().first_ts;
        ctime.insert(e.vertex, tmin);
    }

    Timestamp lastp = DEF_TS;

    Timestamp prev_min_ts = tg->back().first_ts;
    Timestamp end_tstamp  = !invert ? timeWindow + start.tstamp : start.tstamp - timeWindow;

    if (!invert && seed != NULL && seed->te != -1)
        end_tstamp = seed->te;

    /// Iterate through the neighbors of e.vertex
    auto beginIt = !invert ? g->beginOut(e.vertex) : g->beginIn(e.vertex);
    auto endIt   = !invert ? g->endOut(e.vertex) : g->endIn(e.vertex);

    for (auto colelem = beginIt; colelem < endIt; colelem++) {
        auto& colElem = *colelem;
        int   w       = colelem->vertex;
        auto& tset    = colelem->tstamps;

        // Prevent visiting loops
        if (w == e.vertex)
            continue;

        /// Determining the timestamps in the edge bundle
        auto      it_start = tset.begin();
        auto      it_end   = tset.end();
        Timestamp ts;

        if (!invert) {
            it_start = upper_bound(tset.begin(), tset.end(), prev_min_ts);
            if (it_start == tset.end() || *it_start > end_tstamp)
                continue;
            ts = *(it_start);
        } else {
            it_end = lower_bound(tset.begin(), tset.end(), prev_min_ts);
            if (it_end == tset.begin() || *(it_end - 1) < end_tstamp)
                continue;
            ts = *(it_end - 1);
        }

        if ((seed != NULL) && (seed->cands.find(w) == seed->cands.end()))
            continue;

        if (!invert)
            it_end = upper_bound(it_start, tset.end(), end_tstamp);
        else
            it_start = lower_bound(tset.begin(), it_end, end_tstamp);

        /// Progress recursivelly
        if (w == current->front()) {
            tg->push_back(TempEdge(w, ts, &(colElem), it_start - tset.begin(), it_end - tset.begin()));
            recordBundledCycle(current, tg, result, invert);
            tg->pop_back();

            if (!invert) {
                Timestamp tmax = *(it_end - 1);
                lastp          = ((tmax > lastp) ? tmax : lastp);
            } else {
                Timestamp tmin = *(it_start);
                lastp          = ((tmin < lastp) ? tmin : lastp);
            }
        } else {
            if (!invert ? (ts < ctime.at(w)) : (ts > ctime.at(w))) {
                if (!invert) {
                    auto it_ctime = lower_bound(it_start, tset.end(), ctime.at(w));
                    tg->push_back(TempEdge(w, ts, &(colElem), it_start - tset.begin(), it_ctime - tset.begin()));
                } else {
                    auto it_ctime = upper_bound(tset.begin(), it_end, ctime.at(w));
                    tg->push_back(TempEdge(w, ts, &(colElem), it_ctime - tset.begin(), it_end - tset.begin()));
                }

                Timestamp lastx
                    = cycles2scentBundled(g, EdgeData(w, ts), start, current, tg, ctime, Ulists, result, seed, invert);
                tg->pop_back();

                Timestamp prev_ts = DEF_TS;

                if (!invert) {
                    Timestamp new_lastp = DEF_TS;

                    auto it_lastx = lower_bound(it_start, it_end, lastx);
                    if (it_lastx != it_start)
                        new_lastp = *(it_lastx - 1);
                    if (it_lastx != it_end)
                        prev_ts = *it_lastx;

                    lastp = ((new_lastp > lastp) ? new_lastp : lastp);
                } else {
                    Timestamp new_lastp = DEF_TS;

                    auto it_lastx = upper_bound(it_start, it_end, lastx);
                    if (it_lastx != it_start)
                        prev_ts = *(it_lastx - 1);
                    if (it_lastx != it_end)
                        new_lastp = *it_lastx;

                    lastp = ((new_lastp < lastp) ? new_lastp : lastp);
                }

                if (prev_ts != DEF_TS) {
                    extend2scent(g, e.vertex, prev_ts, Ulists[w], invert);
                }
            } else if (!invert ? (ts >= ctime.at(w)) : (ts <= ctime.at(w))) {
                extend2scent(g, e.vertex, ts, Ulists[w], invert);
            }
        }
    }

    if (!invert ? (lastp > DEF_TS) : (lastp < DEF_TS))
        unblock2scent(g, e.vertex, lastp, ctime, Ulists, invert);
    current->pop_back();

    return lastp;
}

/// ********************** Fine-grained temporal Johnson algorithm ***********************

namespace {
    ConcurrentContainer<CycleHist> pt_cycleHist;

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

    typedef ConcurrentList<Timestamp> OldLockStack;

    struct ThreadDataGuard {
    public:
        ThreadDataGuard(Graph* g, Cycle* c, TimestampGroups* t, ClosingTimes* ct, UnblockLists* ul, bool inv = false)
            : graph(g)
            , cycle(c)
            , tg(t)
            , ctime(ct)
            , ulists(ul)
            , oldCtimes(new OldLockStack)
            , invert(inv)
        {
        }

        ThreadDataGuard(ThreadDataGuard* guard, int pathSize)
            : graph(guard->graph)
            , invert(guard->invert)
        {
            // Copy the data from another thread
            {
                guard->dataLock.lock_shared();
                ctime     = new ClosingTimes(*(guard->ctime));
                ulists    = new UnblockLists(*(guard->ulists));
                cycle     = new Cycle(*(guard->cycle));
                tg        = guard->tg->clone(pathSize - 1);
                oldCtimes = new OldLockStack(*(guard->oldCtimes));
                guard->dataLock.unlock_shared();
            }
            // Remove the invalid vertices
            while (cycle->size() > pathSize) {
                int lastVertex = cycle->back();
                cycle->pop_back();
                Timestamp lastCtime = oldCtimes->back();
                oldCtimes->pop_back();
                unblock2scent(graph, lastVertex, lastCtime, *ctime, *ulists, invert);
            }

            for (int i = 1; i < pathSize; i++) {
                int       vert = cycle->at(i);
                Timestamp tmin = tg->at(i - 1).first_ts;
                ctime->insert(vert, tmin);
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
                delete tg;
                delete ctime;
                delete ulists;
                delete oldCtimes;
                cycle     = NULL;
                tg        = NULL;
                ctime     = NULL;
                ulists    = NULL;
                oldCtimes = NULL;
                delete this;
                return;
            }
            this->cntLock.unlock();
        }

        // Global graph data
        Graph* graph;

        // Guarded data
        Cycle*           cycle  = NULL;
        TimestampGroups* tg     = NULL;
        ClosingTimes*    ctime  = NULL;
        UnblockLists*    ulists = NULL;

        // Old ctime values
        OldLockStack* oldCtimes = NULL;

        regMutexWrapper dataLock;

    private:
        // Reference counter
        int refCount = 1;

        spinlock cntLock;
        bool     invert = false;
    };

    class TempJohnsonsTask
#ifdef USE_TBB
        : public tbb::task
#endif
    {
    public:
        TempJohnsonsTask(Graph* g, ConcurrentContainer<CycleHist>& pt_chist, int v, TempEdge e, EdgeData s, Cycle* cyc,
                         TimestampGroups* t, ClosingTimes* ct, UnblockLists* ul, ThreadDataGuard* tdg,
                         StrongComponent* cu = NULL, TempJohnsonsTask* par = NULL, bool inv = false)
            : pt_cycleHist(pt_chist)
            , vert(v)
            , ebundle(e)
            , start(s)
            , cycle(cyc)
            , tg(t)
            , ctime(ct)
            , ulists(ul)
            , graph(g)
            , cunion(cu)
            , parent(par)
            , retLastp(false)
            , invert(inv)
            , it(!inv ? g->beginOut(vert) : g->beginIn(vert))
            , ownerThread(getThreadId())
            , pathSize(cyc->size())
            , thrData(tdg)
            , DEF_TS(!invert ? NINF : PINF)
        {
        }

        virtual ~TempJohnsonsTask() { }
        virtual TASK_RET execute();

        void copyOnSteal();

        /// Return lastx value from the recursive call on edge e
        void returnValue(Timestamp lastx);

        TimestampSet::iterator my_it_end, my_it_begin;

        TASK_RET SpawnTask();
        TASK_RET Continuation();

        ConcurrentContainer<CycleHist>& pt_cycleHist;
        // Parameters
        int              vert = -1;
        TempEdge         ebundle;
        EdgeData         start;
        Cycle*           cycle  = NULL;
        TimestampGroups* tg     = NULL;
        ClosingTimes*    ctime  = NULL;
        UnblockLists*    ulists = NULL;

        Graph*           graph  = NULL;
        StrongComponent* cunion = NULL;

        // Return
        spinlock retLock;
        // ompMutexWrapper retLock;
        TempJohnsonsTask* parent = NULL;
        Timestamp         retLastp;

        // Search for cycles backwards
        bool invert = false;

        // Continuation stealing
        bool            newTask = true;
        Graph::Iterator it;

        // Task control
        bool isContinuation = false;
        int  ownerThread    = -1;
        bool stolenTask     = false;
#ifndef USE_TBB
        vector<TempJohnsonsTask*> childTasks;
#endif

        int              pathSize = 0;
        ThreadDataGuard* thrData  = NULL;

        // Default time stamp
        const Timestamp DEF_TS;
    };

    TASK_RET TempJohnsonsTask::execute()
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

    void TempJohnsonsTask::copyOnSteal()
    {
        /// Copy-on-steal
        int thisThreadId = getThreadId();

        if (ownerThread != thisThreadId) {
            ownerThread = thisThreadId;

            stolenTask = true;

            // Copy on steal
            ThreadDataGuard* newThrData = new ParCycEnum::ThreadDataGuard(thrData, pathSize);

            // Decrement the ref. count of the previous blocked map
            thrData->decrementRefCount();

            thrData = newThrData;
            // Update the pointers
            cycle  = thrData->cycle;
            tg     = thrData->tg;
            ctime  = thrData->ctime;
            ulists = thrData->ulists;
        }
    }

    TASK_RET TempJohnsonsTask::SpawnTask()
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
                tg->push_back(ebundle);
                pathSize++;

                if (tg->size() != 0) {
                    Timestamp tmin      = ebundle.first_ts;
                    Timestamp prevCtime = ctime->at(vert);
                    ctime->insert(vert, tmin);
                    thrData->oldCtimes->push_back(prevCtime);
                }
                thrData->dataLock.unlock();
            }
        }

        // We have not found the cycle, but it might be here, so we need to unlock
        // TODO: Working only when inverting the edges!
        if (maxTempCycle != -1 && cycle->size() > maxTempCycle) {
            retLastp = invert ? NINF : PINF;
#ifndef USE_TBB
            return;
#else
            return NULL;
#endif
        }

#ifdef USE_TBB
        tbb::task* retTask = NULL;
#endif

        Timestamp prev_min_ts = ebundle.first_ts;
        Timestamp end_tstamp  = !invert ? timeWindow + start.tstamp : start.tstamp - timeWindow;

        /// Iterate through the neighbors of vert
        while (it < (!invert ? graph->endOut(vert) : graph->endIn(vert))) {
            auto& edgeData = *it;
            int   w        = it->vertex;
            auto& tset     = it->tstamps;
            it++;

            /// Determining the starting timestamp
            auto      it_start = tset.begin();
            auto      it_end   = tset.end();
            Timestamp ts;

            if (!invert) {
                it_start = upper_bound(tset.begin(), tset.end(), prev_min_ts);
                if (it_start == tset.end() || *it_start > end_tstamp)
                    continue;
                ts = *(it_start);
            } else {
                it_end = lower_bound(tset.begin(), tset.end(), prev_min_ts);
                if (it_end == tset.begin() || *(it_end - 1) < end_tstamp)
                    continue;
                ts = *(it_end - 1);
            }

            /// Skip if a vertex is not in the cycle union
            if ((cunion != NULL) && (!cunion->exists(w)))
                continue;

            if (!invert)
                it_end = upper_bound(it_start, tset.end(), end_tstamp);
            else
                it_start = lower_bound(tset.begin(), it_end, end_tstamp);

            /// Progress recursivelly
            if (w == start.vertex) {
                {
                    thrData->dataLock.lock();
                    tg->push_back(TempEdge(w, ts, &edgeData, it_start - tset.begin(), it_end - tset.begin()));
                    thrData->dataLock.unlock();
                }
                auto& local_hist = pt_cycleHist.local();
                recordBundledCycle(cycle, tg, local_hist, invert);
                {
                    thrData->dataLock.lock();
                    tg->pop_back();
                    thrData->dataLock.unlock();
                }

                {
                    retLock.lock();
                    if (!invert) {
                        if (*(it_end - 1) > retLastp)
                            retLastp = *(it_end - 1);
                    } else {
                        if (*(it_start) < retLastp)
                            retLastp = *(it_start);
                    }
                    retLock.unlock();
                }
            } else {

                if (!invert ? (ts < ctime->at(w)) : (ts > ctime->at(w))) {
                    /// Spawning child task
                    TempEdge ebundle;
                    if (!invert) {
                        auto it_ctime = lower_bound(it_start, it_end, ctime->at(w));
                        ebundle       = TempEdge(w, ts, &edgeData, it_start - tset.begin(), it_ctime - tset.begin());
                    } else {
                        auto it_ctime = upper_bound(tset.begin(), it_end, ctime->at(w));
                        ebundle       = TempEdge(w, ts, &edgeData, it_ctime - tset.begin(), it_end - tset.begin());
                    }

#ifndef USE_TBB
                    TempJohnsonsTask* a = new TempJohnsonsTask(graph, pt_cycleHist, w, ebundle, start, cycle, tg, ctime,
                                                               ulists, thrData, cunion, this, invert);
                    if (nullptr == a)
                        return;
                    this->childTasks.push_back(a);
#else
                    increment_ref_count();
                    TempJohnsonsTask* a
                        = new (allocate_child()) TempJohnsonsTask(graph, pt_cycleHist, w, ebundle, start, cycle, tg,
                                                                  ctime, ulists, thrData, cunion, this, invert);
#endif

                    a->my_it_begin = it_start;
                    a->my_it_end   = it_end;
                    thrData->incrementRefCount();

#ifndef USE_TBB
#pragma omp task firstprivate(a)
                    a->execute();
#else
                    // Continuation stealing
                    if (it < (!invert ? graph->endOut(vert) : graph->endIn(vert))) {
                        recycle_to_reexecute();
                        return a;
                    } else
                        retTask = a;
#endif
                } else if (!invert ? (ts >= ctime->at(w)) : (ts <= ctime->at(w))) {
                    thrData->dataLock.lock();
                    extend2scent(graph, vert, ts, (*ulists)[w], invert);
                    thrData->dataLock.unlock();
                }
            }
        }
        isContinuation = true;

#ifdef USE_TBB
        recycle_as_safe_continuation();
        return retTask;
#endif
    }

    void TempJohnsonsTask::returnValue(Timestamp lastx)
    {
        retLock.lock();
        if (!invert ? (lastx > retLastp) : (lastx < retLastp))
            retLastp = lastx;
        retLock.unlock();
    }

    TASK_RET TempJohnsonsTask::Continuation()
    {
        /// Compute prev_ts and new_lastp

        int prevVert;
        prevVert = cycle->at(cycle->size() - 2);

        Timestamp prev_ts   = DEF_TS;
        Timestamp new_lastp = DEF_TS;
        if (parent) {
            auto it_start = my_it_begin;
            auto it_end   = my_it_end;

            if (!invert) {
                auto it_lastx = lower_bound(it_start, it_end, retLastp);
                if (it_lastx != it_start)
                    new_lastp = *(it_lastx - 1);
                if (it_lastx != it_end)
                    prev_ts = *it_lastx;
            } else {
                auto it_lastx = upper_bound(it_start, it_end, retLastp);
                if (it_lastx != it_start)
                    prev_ts = *(it_lastx - 1);
                if (it_lastx != it_end)
                    new_lastp = *it_lastx;
            }
        }
        /// Atomic update
        {
            thrData->dataLock.lock();

            cycle->pop_back();
            pathSize--;
            thrData->oldCtimes->pop_back();
            tg->pop_back();

            if (!invert ? (retLastp > DEF_TS) : (retLastp < DEF_TS)) {
                unblock2scent(graph, vert, retLastp, *ctime, *ulists, invert);
            }

            if (prev_ts != DEF_TS)
                extend2scent(graph, prevVert, prev_ts, (*ulists)[vert], invert);
            thrData->dataLock.unlock();
        }

        /// Return
        if (parent)
            parent->returnValue(new_lastp);

        thrData->decrementRefCount();

        if (!parent && cunion) {
            delete cunion;
            cunion = NULL;
        }

#ifdef USE_TBB
        return NULL;
#endif
    }
}

/// ************************** Parallel Temporal Johnson - top level **************************

namespace {
    class OuterLoopTempJohnTask
#ifdef USE_TBB
        : public tbb::task
#endif
    {
    public:
        OuterLoopTempJohnTask(Graph* _g, ConcurrentContainer<CycleHist>& _ch, int _vert, int _w, Timestamp _ts,
                              GraphElemID _eid, bool tpar = false, bool inv = false)
            : vert(_vert)
            , w(_w)
            , eid(_eid)
            , ts(_ts)
            , pt_chist(_ch)
            , g(_g)
            , taskPar(tpar)
            , invert(inv)
        {
        }

        virtual ~OuterLoopTempJohnTask() { }

        void runCoarseGrained();
        void runFineGrained();
        void runCoarseGrainedNewPreprocessing();
        void runFineGrainedNewPreprocessing();

        virtual TASK_RET execute();

    protected:
        int                             vert, w;
        GraphElemID                     eid;
        TempEdge                        ebundle; // for new preprocessing
        Timestamp                       ts = -1;
        ConcurrentContainer<CycleHist>& pt_chist;

        TempJohnsonsTask* child = NULL;
        Graph*            g;
        StrongComponent*  cunion = NULL;

        bool isContinuation = false;
        bool taskPar        = false;
        bool invert         = false;
    };

    TASK_RET OuterLoopTempJohnTask::execute()
    {

#ifdef USE_TBB
        set_ref_count(1);
#endif
        if (!isContinuation) {

            if (!taskPar)
                runCoarseGrained();
            else
                runFineGrained();

            isContinuation = true;
#ifdef USE_TBB
            recycle_as_safe_continuation();
#endif
        }

#ifdef USE_TBB
        return NULL;
#endif
    }

    void OuterLoopTempJohnTask::runCoarseGrained()
    {
        auto& my_hist = pt_chist.local();

        StrongComponent* cunion = NULL;
        Seed*            seed   = NULL;

        // Filter-out vertices not belonging to the same cycle-union
        if (useCUnion) {
            findCycleUnions(g, EdgeData(w, ts), vert, timeWindow, cunion, invert);
            seed = new Seed;
            if (nullptr == seed)
                return;
            if (nullptr == cunion)
                return;
            for (auto el : *cunion)
                seed->cands.insert(el);
        }

        ClosingTimes ctime(g->getVertexNo());
        if (invert)
            ctime.setDefaultValue(NINF);
        else
            ctime.setDefaultValue(PINF);
        UnblockLists Ulists;
        Cycle*       current = new Cycle();
        if (nullptr == current) {
            return;
        }
        current->push_back(vert);

        if (!disablePathBundling) {
            TimestampGroups* tg = new TimestampGroups();
            if (nullptr == tg)
                return;
            tg->push_back(TempEdge(w, ts, eid));
            cycles2scentBundled(g, EdgeData(w, ts), EdgeData(vert, ts), current, tg, ctime, Ulists, my_hist, seed,
                                invert);
            if (nullptr != tg) {
                delete tg;
                tg = nullptr;
            }

        } else {
            Timestamps* tss = new Timestamps;
            if (nullptr == tss)
                return;
            cycles2scent(g, EdgeData(w, ts), current, tss, ctime, Ulists, my_hist, seed, invert);
            if (nullptr != tss) {
                delete tss;
                tss = nullptr;
            }
        }
        if (nullptr != current) {
            delete current;
            current = nullptr;
        }
        if (nullptr != seed) {
            delete seed;
            seed = nullptr;
            if (nullptr != cunion) {
                delete cunion;
                cunion = nullptr;
            }
        }
    }

    void OuterLoopTempJohnTask::runFineGrained()
    {

        StrongComponent* cunion = NULL;
        // Filter-out vertices not belonging to the same cycle-union
        if (useCUnion) {
            findCycleUnions(g, EdgeData(w, ts), vert, timeWindow, cunion, invert);
        }

        ClosingTimes* ctime = new ClosingTimes;
        if (nullptr == ctime)
            return;
        if (invert)
            ctime->setDefaultValue(NINF);
        else
            ctime->setDefaultValue(PINF);
        UnblockLists* ulists = new UnblockLists;
        if (nullptr == ulists)
            return;
        TimestampGroups* tg = new TimestampGroups;
        if (nullptr == tg)
            return;
        Cycle* cycle = new Cycle;
        if (nullptr == cycle)
            return;
        cycle->push_back(vert);

        ThreadDataGuard* thrData = new ThreadDataGuard(g, cycle, tg, ctime, ulists, invert);
        if (nullptr == thrData)
            return;
        TempEdge ebundle = TempEdge(w, ts, eid);

#ifndef USE_TBB
        child = new TempJohnsonsTask(g, pt_chist, w, ebundle, EdgeData(vert, ts), cycle, tg, ctime, ulists, thrData,
                                     cunion, NULL, invert);
        if (nullptr == child)
            return;
        child->execute();

        if (nullptr != child) {
            delete child;
            child = nullptr;
        }

#else
        increment_ref_count();
        child = new (allocate_child()) TempJohnsonsTask(g, pt_chist, w, ebundle, EdgeData(vert, ts), cycle, tg, ctime,
                                                        ulists, thrData, cunion, NULL, invert);
        spawn(*child);
#endif
    }
}

namespace {
    class RootTempJohnTask
#ifdef USE_TBB
        : public tbb::task
#endif
    {
    public:
        RootTempJohnTask(Graph* _g, int nthr, ConcurrentContainer<CycleHist>& _ch, bool tpar = false, int rank = 0,
                         int nclust = 1, bool newPp = false, bool inv = false)
            : isContinuation(false)
            , taskPar(tpar)
            , invert(inv)
            , numThreads(nthr)
            , g(_g)
            , pt_chist(_ch)
            , ptChildTasks(nthr)
            , process_rank(rank)
            , size_of_cluster(nclust)
        {
        }

        virtual ~RootTempJohnTask() { }

        virtual TASK_RET execute();

    protected:
        bool                            isContinuation = false;
        bool                            taskPar        = false;
        bool                            invert         = false;
        int                             numThreads;
        Graph*                          g;
        ConcurrentContainer<CycleHist>& pt_chist;

        vector<vector<OuterLoopTempJohnTask*>> ptChildTasks;

        int process_rank;
        int size_of_cluster;
    };

    TASK_RET RootTempJohnTask::execute()
    {

        invert = invertSearch; // OVERRIDE!!!!  TODO: REMOVE THIS

#ifdef USE_TBB
        set_ref_count(1);
#endif

        if (!isContinuation) {
            parallelOuterLoop(g, numThreads, invert, process_rank, size_of_cluster,
                              [&](int from, int to, Timestamp ts, GraphElemID eid) {
                                  SPAWN_SINGLE_TASK(
                                      OuterLoopTempJohnTask(g, pt_chist, from, to, ts, eid, taskPar, invert));
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

void allCyclesTempJohnsonCoarseGrained(Graph* g, CycleHist& result, int numThreads)
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

    ConcurrentContainer<CycleHist> pt_cycleHist;
    pt_cycleHist.setNumThreads(numThreads);

    SPAWN_ROOT_TASK(RootTempJohnTask(g, numThreads, pt_cycleHist, false, process_rank, size_of_cluster));

    combineCycleHistogram(pt_cycleHist, result);
}

void allCyclesTempJohnsonFineGrained(Graph* g, CycleHist& result, int numThreads)
{
    int process_rank    = 0;
    int size_of_cluster = 1;

    pt_cycleHist.clear();
    pt_cycleHist.setNumThreads(numThreads);

#ifdef MPI_IMPL
    MPI_Comm_size(MPI_COMM_WORLD, &size_of_cluster);
    MPI_Comm_rank(MPI_COMM_WORLD, &process_rank);
#endif

#ifdef USE_TBB
    task_scheduler_init init(numThreads);
#endif

    SPAWN_ROOT_TASK(RootTempJohnTask(g, numThreads, pt_cycleHist, true, process_rank, size_of_cluster));

    combineCycleHistogram(pt_cycleHist, result);
}

void allCyclesTempJohnsonCoarseGrainedNew(Graph* g, CycleHist& result, int numThreads)
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

    ConcurrentContainer<CycleHist> pt_cycleHist;
    pt_cycleHist.setNumThreads(numThreads);

    SPAWN_ROOT_TASK(RootTempJohnTask(g, numThreads, pt_cycleHist, false, process_rank, size_of_cluster, true));

    combineCycleHistogram(pt_cycleHist, result);
}

void allCyclesTempJohnsonFineGrainedNew(Graph* g, CycleHist& result, int numThreads)
{
    int process_rank    = 0;
    int size_of_cluster = 1;

    ConcurrentContainer<CycleHist> pt_cycleHist;
    pt_cycleHist.setNumThreads(numThreads);

#ifdef MPI_IMPL
    MPI_Comm_size(MPI_COMM_WORLD, &size_of_cluster);
    MPI_Comm_rank(MPI_COMM_WORLD, &process_rank);
#endif

#ifdef USE_TBB
    task_scheduler_init init(numThreads);
#endif

    SPAWN_ROOT_TASK(RootTempJohnTask(g, numThreads, pt_cycleHist, true, process_rank, size_of_cluster, true));

    combineCycleHistogram(pt_cycleHist, result);
}

/// Edges arrive in batches

namespace {
    class RootBatchTempJohnTask
#ifdef USE_TBB
        : public tbb::task
#endif
    {
    public:
        RootBatchTempJohnTask(Graph* _g, int nthr, ConcurrentContainer<CycleHist>& _ch,
                              std::vector<CompressedEdge>* batch, bool tpar = false, bool inv = true)
            : numThreads(nthr)
            , taskPar(tpar)
            , invEdges(inv)
            , g(_g)
            , pt_chist(_ch)
            , batchOfEdges(batch)
        {
        }

        virtual ~RootBatchTempJohnTask() { }

        virtual TASK_RET execute();

    protected:
        bool                            isContinuation = false;
        int                             numThreads;
        bool                            taskPar  = false;
        bool                            invEdges = true;
        Graph*                          g;
        ConcurrentContainer<CycleHist>& pt_chist;

        std::vector<CompressedEdge>* batchOfEdges = NULL;
    };

    TASK_RET RootBatchTempJohnTask::execute()
    {
        int process_rank    = 0;
        int size_of_cluster = 1;

#ifdef MPI_IMPL
        MPI_Comm_size(MPI_COMM_WORLD, &size_of_cluster);
        MPI_Comm_rank(MPI_COMM_WORLD, &process_rank);
#endif

#ifdef USE_TBB
        set_ref_count(1);
#endif

        if (!isContinuation) {
            parallelOuterLoopBatch(batchOfEdges, numThreads, invEdges, process_rank, size_of_cluster,
                                   [&](int from, int to, Timestamp ts, GraphElemID eid) {
                                       SPAWN_SINGLE_TASK(
                                           OuterLoopTempJohnTask(g, pt_chist, from, to, ts, eid, taskPar, invEdges));
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

void allCyclesTempJohnsonCoarseGrainedBatch(Graph* g, std::vector<CompressedEdge>& batch,
                                            ConcurrentContainer<CycleHist>& pt_cycleHist, int numThreads, bool invEdges)
{
#ifdef USE_TBB
    task_scheduler_init init(numThreads);
#endif

    SPAWN_ROOT_TASK(RootBatchTempJohnTask(g, numThreads, pt_cycleHist, &batch, false, invEdges));
}

void allCyclesTempJohnsonFineGrainedBatch(Graph* g, std::vector<CompressedEdge>& batch,
                                          ConcurrentContainer<CycleHist>& pt_cycleHist, int numThreads, bool invEdges)
{
#ifdef USE_TBB
    task_scheduler_init init(numThreads);
#endif

    SPAWN_ROOT_TASK(RootBatchTempJohnTask(g, numThreads, pt_cycleHist, &batch, true, invEdges));
}

}
