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

#ifndef _CYCLE_DATA_STRUCTS_H_
#define _CYCLE_DATA_STRUCTS_H_

#include <list>
#include <cstring>
#include <unordered_set>
#include <unordered_map>

#ifndef USE_TBB
#include <omp.h>
#else
#include <tbb/combinable.h>
using namespace tbb;
#endif

#include <mutex>
#include <atomic>

#include "Macros.h"
#include "CycleUtils.h"

using namespace std;

namespace ParCycEnum {

enum class MutexType { Spin, Regular };

template <typename T> class ConcurrentContainer {
private:
    const int MAX_THR_SIZE = 256;

public:
#ifndef USE_TBB
    ConcurrentContainer()
        : existVec(MAX_THR_SIZE, 0)
        , vecsize(MAX_THR_SIZE)
    {
        container.resize(MAX_THR_SIZE);
    }
#endif

    T& local()
    {
#ifdef USE_TBB
        return container.local();
#else
        int thrId       = omp_get_thread_num();
        existVec[thrId] = 1;
        return container[thrId];
#endif
    }

    T& local(bool& exists)
    {
#ifdef USE_TBB
        T& ret = container.local(exists);
#else
        int thrId       = omp_get_thread_num();
        T&  ret         = container[thrId];
        exists          = existVec[thrId];
        existVec[thrId] = 1;
#endif
        return ret;
    }

    template <typename UnaryFunc> void combine_each(UnaryFunc f)
    {
#ifdef USE_TBB
        container.combine_each(f);
#else
        for (int i = 0; i < vecsize; i++) {
            if (existVec[i]) {
                f(container[i]);
            }
        }
#endif
    }

    void clear() { container.clear(); }

    void setNumThreads(int nthr)
    {
#ifndef USE_TBB
        vecsize = nthr;
        container.resize(nthr);
        existVec.resize(nthr, 0);
#endif
    }

private:
#ifdef USE_TBB
    tbb::combinable<T> container;
#else
    vector<T>   container;
    vector<int> existVec;
    int         vecsize = 1;
#endif
};

/// Concurrent counter for collecting statistics
template <typename T = unsigned long> class TConcurrentCounter {
public:
    TConcurrentCounter() { }

    void increment(T inc = 1)
    {
        bool  exists = true;
        auto& loc    = pt_counter.local(exists);

        if (!exists)
            loc = 0;
        loc += inc;
    }

    void decrement()
    {
        bool  exists = true;
        auto& loc    = pt_counter.local(exists);

        if (!exists)
            loc = 0;
        loc--;
    }

    T getMax()
    {
        T         maxval;
        vector<T> results;
        pt_counter.combine_each([&](T& t) { results.push_back(t); });

        bool first = true;
        for (auto& num : results) {
            if (first) {
                maxval = num;
                first  = false;
            } else if (num > maxval) {
                maxval = num;
            }
        }
        return maxval;
    }

    T getAvg()
    {
        T   totres = 0;
        int nt     = 0;

        vector<T> results;
        pt_counter.combine_each([&](T& t) { results.push_back(t); });

        for (auto& num : results) {
            totres += num;
            nt++;
        }
        return totres / nt;
    }

    T getResult()
    {
        if (!combined) {
            combined = true;
            result   = 0;

            vector<T> results;
            pt_counter.combine_each([&](T& t) { results.push_back(t); });

            for (auto& num : results) {
                result += num;
            }
        }
        return result;
    }

private:
    ConcurrentContainer<T> pt_counter;

    bool combined = false;
    T    result   = 0;
};

typedef TConcurrentCounter<unsigned long> ConcurrentCounter;

/// Wrapper for dynamic array
template <typename T> class VectorPath {
public:
    VectorPath(int s)
        : vect(new T[s])
    {
    }
    ~VectorPath()
    {
        if (vect)
            delete[] vect;
    }

    void push_back(T x)
    {
        ++it;
        vect[it] = x;
    }

    T back()
    {
        if (it == -1)
            return T();
        return vect[it];
    }

    void pop_back()
    {
        if (it >= 0)
            it--;
    }

    int size() { return it + 1; }

private:
    T*  vect = NULL;
    int it   = -1;
};

class abstractMutex {
public:
    virtual ~abstractMutex() {};

    virtual void lock()        = 0;
    virtual void lock_shared() = 0;

    virtual void unlock()        = 0;
    virtual void unlock_shared() = 0;
};

#ifndef USE_TBB
class ompMutexWrapper : public abstractMutex {
public:
    ompMutexWrapper() { omp_init_lock(&_mutex); };
    ~ompMutexWrapper() override { omp_destroy_lock(&_mutex); };

    void lock() override { omp_set_lock(&_mutex); }
    void lock_shared() override { omp_set_lock(&_mutex); }

    void unlock() override { omp_unset_lock(&_mutex); }
    void unlock_shared() override { omp_unset_lock(&_mutex); }

private:
    mutable omp_lock_t _mutex;
};
#endif

class spinlock : public abstractMutex {
public:
    ~spinlock() override {};

    void lock() override { lock_int(); }
    void lock_shared() override { lock_int(); }

    void unlock() override { unlock_int(); }
    void unlock_shared() override { unlock_int(); }

private:
    mutable std::atomic<bool> _lock = { false };

    void lock_int()
    {
        for (;;) {
            if (!_lock.exchange(true, std::memory_order_acquire)) {
                break;
            }
        }
    }

    void unlock_int() { _lock.store(false, std::memory_order_release); }
};

class regMutexWrapper : public abstractMutex {
public:
    ~regMutexWrapper() override {};

    void lock() override { _mutex.lock(); }
    void lock_shared() override { _mutex.lock(); }

    void unlock() override { _mutex.unlock(); }
    void unlock_shared() override { _mutex.unlock(); }

private:
    mutable std::mutex _mutex;
};

inline abstractMutex* createMutex(MutexType type = MutexType::Regular)
{
    if (type == MutexType::Spin)
        return new spinlock();
    return new regMutexWrapper();
}

class mutexWrapper {
public:
    mutexWrapper(MutexType type = MutexType::Regular)
        : mutex_ptr(createMutex(type))
    {
    }

    ~mutexWrapper() { delete mutex_ptr; }

    void lock() { mutex_ptr->lock(); }

    void lock_shared() { mutex_ptr->lock_shared(); }

    void unlock() { mutex_ptr->unlock(); }

    void unlock_shared() { mutex_ptr->unlock_shared(); }

private:
    abstractMutex* mutex_ptr = NULL;
};

/// Wrapper for std::unordered_set
class HashSet {
public:
    HashSet()
        : elems() {};
    HashSet(int s)
        : elems() {};
    HashSet(const HashSet& hs)
        : elems(hs.elems) {};

    void insert(int el) { elems.insert(el); }

    void remove(int el)
    {
        auto it = elems.find(el);
        if (it != elems.end())
            elems.erase(it);
    }

    bool exists(int el)
    {
        if (elems.find(el) != elems.end())
            return true;
        return false;
    }
    void include(const HashSet& other)
    {
        for (auto el : other.elems)
            insert(el);
    }

    int  size() { return elems.size(); }
    void clear() { elems.clear(); }

    template <typename TF> void for_each(TF&& f)
    {
        for (auto el : elems)
            f(el);
    }
    std::unordered_set<int>::iterator begin() { return elems.begin(); }
    std::unordered_set<int>::iterator end() { return elems.end(); }
    std::unordered_set<int>::iterator erase(std::unordered_set<int>::iterator it) { return elems.erase(it); }

private:
    friend class HashSetStack;
    unordered_set<int> elems;
};

class HashSetStack {
private:
    spinlock HashSetMutex;

public:
    HashSetStack(bool conc = false)
        : curLevel(0)
        , elems()
        , concurrent(conc) {};
    HashSetStack(int s, bool conc = false)
        : curLevel(0)
        , elems()
        , concurrent(conc) {};
    HashSetStack(const HashSetStack& hs)
        : curLevel(hs.curLevel)
        , elems(hs.elems)
        , concurrent(hs.concurrent) {};

    HashSetStack* clone()
    {
        if (concurrent)
            HashSetMutex.lock();
        HashSetStack* ret = new HashSetStack(*this);
        if (concurrent)
            HashSetMutex.unlock();
        return ret;
    }

    HashSetStack* clone(int lvl)
    {
        HashSetStack* ret = new HashSetStack();
        ret->curLevel     = lvl;
        ret->concurrent   = concurrent;

        if (concurrent)
            HashSetMutex.lock();
        for (auto it = elems.begin(); it != elems.end(); ++it) {
            if (it->second <= lvl)
                ret->elems.insert({ it->first, it->second });
        }
        if (concurrent)
            HashSetMutex.unlock();

        return ret;
    }

    void reserve(int s) { }

    void incrementLevel()
    {
        if (concurrent)
            HashSetMutex.lock();
        curLevel++;
        if (concurrent)
            HashSetMutex.unlock();
    }

    void decrementLevel()
    {
        if (concurrent)
            HashSetMutex.lock();
        curLevel--;
        for (auto it = elems.begin(); it != elems.end();) {
            if (it->second > curLevel)
                it = elems.erase(it);
            else
                it++;
        }
        if (concurrent)
            HashSetMutex.unlock();
    }

    void setLevel(int lvl)
    {
        if (concurrent)
            HashSetMutex.lock();
        if (lvl < curLevel) {
            curLevel = lvl;
            for (auto it = elems.begin(); it != elems.end();) {
                if (it->second > curLevel)
                    it = elems.erase(it);
                else
                    it++;
            }
        }
        if (concurrent)
            HashSetMutex.unlock();
    }

    void insert(int el)
    {
        if (concurrent)
            HashSetMutex.lock();
        if (elems.find(el) == elems.end())
            elems[el] = curLevel;
        if (concurrent)
            HashSetMutex.unlock();
    }

    void remove(int el)
    {
        auto it = elems.find(el);
        if (it != elems.end())
            elems.erase(it);
    }

    bool exists(int el)
    {
        if (elems.find(el) != elems.end())
            return true;
        return false;
    }

    void include(const HashSet& other)
    {
        for (auto el : other.elems) {
            insert(el);
        }
    }

    template <typename TF> void for_each(TF&& f)
    {
        for (auto el : elems) {
            f(el);
        }
    }

    void exclude(const HashSet& other)
    {
        for (auto el : other.elems) {
            remove(el);
        }
    }

    int size() { return elems.size(); }

    void clear() { elems.clear(); }

    void copy(const HashSet& other)
    {
        elems.clear();

        for (auto el : other.elems) {
            insert(el);
        }
    }

private:
    int                     curLevel = 1;
    unordered_map<int, int> elems;
    bool                    concurrent;
};

/// Wrapper for std::unordered_map
class HashMap {
public:
    HashMap()
        : elems() {};
    HashMap(int s)
        : elems() {};
    HashMap(const HashMap& hs)
        : elems(hs.elems)
        , def(hs.def) {};

    void insert(int el, Timestamp num)
    {
        if (num != def)
            elems[el] = num;
        else
            elems.erase(el);
    }
    void erase(int el) { elems.erase(el); }

    bool exists(int el)
    {
        auto it = elems.find(el);
        if (it != elems.end())
            return (it->second != def);
        return false;
    }

    bool exists(int el, Timestamp ts)
    {
        auto it = elems.find(el);
        if (it == elems.end())
            return false;
        if (it->second == -1 || ts >= it->second)
            return true;
        return false;
    }

    Timestamp at(int el)
    {
        auto it = elems.find(el);
        if (it == elems.end())
            return def;
        return it->second;
    }

    template <typename TF> void for_each(TF&& f)
    {
        for (auto el : elems)
            f(el.first);
    }
    int size() { return elems.size(); }

    void setDefaultValue(Timestamp d) { def = d; }

private:
    friend class HashMapStack;
    unordered_map<int, Timestamp> elems;

    Timestamp def = 0;
};

/// Hash map with a stack
class HashMapStack {
private:
    struct StackElem {
        Timestamp cltime;
        int       level;
        StackElem(Timestamp ct = 0, int l = 0)
            : cltime(ct)
            , level(l) {};
    };
    spinlock HashMapMutex;

public:
    HashMapStack(bool conc = false)
        : curLevel(0)
        , elems()
        , concurrent(conc) {};
    HashMapStack(const HashMapStack& hs)
        : curLevel(hs.curLevel)
        , elems(hs.elems)
        , concurrent(hs.concurrent) {};

    HashMapStack* clone()
    {
        if (concurrent)
            HashMapMutex.lock();
        HashMapStack* ret = new HashMapStack(*this);
        if (concurrent)
            HashMapMutex.unlock();
        return ret;
    }

    HashMapStack* clone(int lvl)
    {
        HashMapStack* ret = new HashMapStack();
        ret->curLevel     = lvl;
        ret->concurrent   = concurrent;

        if (concurrent)
            HashMapMutex.lock();
        for (auto it = elems.begin(); it != elems.end(); ++it) {
            auto& vect = it->second;
            for (int ind = vect.size() - 1; ind >= 0; ind--) {
                if (vect[ind].level <= lvl) {
                    ret->elems.insert({ it->first, vector<StackElem>(1, vect[ind]) });
                    break;
                }
            }
        }
        if (concurrent)
            HashMapMutex.unlock();
        return ret;
    }

    void incrementLevel()
    {
        if (concurrent)
            HashMapMutex.lock();
        curLevel++;
        if (concurrent)
            HashMapMutex.unlock();
    }

    void decrementLevel()
    {
        if (concurrent)
            HashMapMutex.lock();
        curLevel--;
        for (auto it = elems.begin(); it != elems.end();) {
            if (it->second.back().level > curLevel)
                it->second.pop_back();
            if (it->second.empty())
                it = elems.erase(it);
            else
                ++it;
        }
        if (concurrent)
            HashMapMutex.unlock();
    }

    void setLevel(int lvl)
    {
        if (concurrent)
            HashMapMutex.lock();
        if (lvl < curLevel) {
            curLevel = lvl;
            for (auto it = elems.begin(); it != elems.end();) {
                while (!it->second.empty() && it->second.back().level > curLevel)
                    it->second.pop_back();
                if (it->second.empty())
                    it = elems.erase(it);
                else
                    ++it;
            }
        }
        if (concurrent)
            HashMapMutex.unlock();
    }

    void insert(int el, Timestamp num)
    {
        if (concurrent)
            HashMapMutex.lock();
        if (num != 0) {
            auto it = elems.find(el);
            if (it == elems.end())
                elems[el].push_back(StackElem(num, curLevel));
            else if (it->second.back().level < curLevel)
                it->second.push_back(StackElem(num, curLevel));
            else if (it->second.back().level == curLevel) {
                auto& last  = it->second.back();
                last.cltime = num;
            }
        } else
            elems.erase(el);
        if (concurrent)
            HashMapMutex.unlock();
    }

    bool exists(int el)
    {
        auto it = elems.find(el);
        if (it != elems.end())
            return !!it->second.back().cltime;
        return false;
    }

    bool exists(int el, Timestamp ts)
    {
        auto it = elems.find(el);
        if (it == elems.end())
            return false;
        Timestamp closeTime = it->second.back().cltime;
        if (closeTime == -1 || ts >= closeTime)
            return true;
        return false;
    }

    void include(const HashMap& other)
    {
        for (auto el : other.elems)
            insert(el.first, el.second);
    }

    Timestamp at(int el)
    {
        auto it = elems.find(el);
        if (it == elems.end())
            return 0;
        return it->second.back().cltime;
    }

    int size() { return elems.size(); }

private:
    int                                   curLevel = 1;
    unordered_map<int, vector<StackElem>> elems;
    bool                                  concurrent;
};

/// Concurrent List
template <typename T> class ConcurrentList {
public:
    ConcurrentList(bool conc = false)
        : elems()
        , concurrent(conc)
    {
    }
    ConcurrentList(const ConcurrentList& cl)
        : elems(cl.elems)
        , concurrent(cl.concurrent)
    {
    }
    ConcurrentList(const ConcurrentList& cl, int len)
        : elems(cl.elems.begin(), cl.elems.begin() + len)
        , concurrent(cl.concurrent)
    {
    }

    ConcurrentList* clone()
    {
        if (concurrent)
            CListMutex.lock();
        ConcurrentList* ret = new ConcurrentList(*this);
        if (concurrent)
            CListMutex.unlock();
        return ret;
    }

    ConcurrentList* clone(int len)
    {
        if (concurrent)
            CListMutex.lock();
        ConcurrentList* ret = new ConcurrentList(*this, len);
        if (concurrent)
            CListMutex.unlock();
        return ret;
    }

    void push_back(T x)
    {
        if (concurrent)
            CListMutex.lock();
        elems.push_back(x);
        if (concurrent)
            CListMutex.unlock();
    }

    T front() { return elems.front(); }
    T back() { return elems.back(); }

    void pop_back()
    {
        if (concurrent)
            CListMutex.lock();
        elems.pop_back();
        if (concurrent)
            CListMutex.unlock();
    }

    void pop_back_until(int sz = 1)
    {
        while (elems.size() > sz) {
            if (concurrent)
                CListMutex.lock();
            elems.pop_back();
            if (concurrent)
                CListMutex.unlock();
        }
    }

    int size() { return elems.size(); }

    template <typename TF> void for_each(TF&& f)
    {
        for (auto el : elems)
            f(el);
    }
    T& at(int idx) { return elems[idx]; }

    typename std::vector<T>::iterator         begin() { return elems.begin(); }
    typename std::vector<T>::iterator         end() { return elems.end(); }
    typename std::vector<T>::reverse_iterator rbegin() { return elems.rbegin(); }
    typename std::vector<T>::reverse_iterator rend() { return elems.rend(); }

private:
    vector<T> elems;
    bool      concurrent = false;

    spinlock CListMutex;
};

}

#endif //_DATA_STRUCTS_H_