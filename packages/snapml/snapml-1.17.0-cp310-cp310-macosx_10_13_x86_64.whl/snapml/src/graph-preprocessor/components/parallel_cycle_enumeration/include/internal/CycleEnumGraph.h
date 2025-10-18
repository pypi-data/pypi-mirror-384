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

#ifndef CYCLE_ENUM_GRAPH_H
#define CYCLE_ENUM_GRAPH_H

#include <set>
#include <unordered_map>
#include "CycleUtils.h"
#include "Macros.h"

#ifdef USE_EXT_GRAPH
#include "compressedGraph.h"
#endif

using namespace std;

namespace ParCycEnum {

typedef std::vector<int> TimestampSet;

struct EdgeData {
    int       vertex;
    Timestamp tstamp;
    EdgeData(int v = -1, Timestamp t = -1)
        : vertex(v)
        , tstamp(t)
    {
    }
};

#ifndef USE_EXT_GRAPH
struct CompressedEdge {
    int         fromV, toV;
    Timestamp   tstamp;
    GraphElemID eid;

    CompressedEdge(int f = -1, int t = -1, Timestamp ts = -1, GraphElemID ei = -1)
        : fromV(f)
        , toV(t)
        , tstamp(ts)
        , eid(ei)
    {
    }
};

struct ColElem {
    int                      vertex;
    TimestampSet             tstamps;
    std::vector<GraphElemID> eids;
};
#endif

/******************************** CSR Graph ******************************************/

class CSRGraph {
protected:
    struct IteratorImpl;

    using difference_type = std::ptrdiff_t;
    using pointer         = ColElem*;
    using reference       = ColElem&;

public:
    CSRGraph() {};
    virtual ~CSRGraph()
    {
        delete[] offsArray;
        delete[] edgeArray;
        delete[] inOffsArray;
        delete[] inEdgeArray;
    };

    virtual void readTemporalGraph(string path);

    virtual int getVertexNo() { return vertexNo; }
    virtual int numNeighbors(int node) { return offsArray[node + 1] - offsArray[node]; }
    virtual int numInEdges(int node) { return inOffsArray[node + 1] - inOffsArray[node]; }

    // Abstract iterator
    template <class II> struct AbstrIterator {
        AbstrIterator(II im)
            : impl(im)
        {
        }
        ~AbstrIterator() { }

        AbstrIterator(const AbstrIterator& other)
            : impl(other.impl)
        {
        }
        inline AbstrIterator(AbstrIterator&& other)
            : impl(other.impl)
        {
        }
        inline AbstrIterator& operator=(const AbstrIterator& other)
        {
            impl = other.impl;
            return *this;
        }
        inline AbstrIterator& operator=(AbstrIterator&& other)
        {
            impl = std::move(other.impl);
            return *this;
        }

        inline reference      operator*() { return impl.getReference(); }
        inline pointer        operator->() { return impl.getPointer(); }
        inline AbstrIterator& operator++()
        {
            impl.increment();
            return *this;
        }
        inline AbstrIterator operator++(int)
        {
            AbstrIterator tmp = *this;
            ++(*this);
            return tmp;
        }
        inline AbstrIterator& operator+=(int i)
        {
            impl.increment(i);
            return *this;
        }
        inline AbstrIterator& operator+=(long i)
        {
            impl.increment(i);
            return *this;
        }
        inline friend bool operator==(const AbstrIterator& a, const AbstrIterator& b) { return a.impl.equal(b.impl); };
        inline friend bool operator!=(const AbstrIterator& a, const AbstrIterator& b) { return !(a == b); };
        inline friend bool operator<(const AbstrIterator& a, const AbstrIterator& b)
        {
            return a.impl.lessThan(b.impl);
        };
        inline friend bool operator>=(const AbstrIterator& a, const AbstrIterator& b) { return !(a < b); };
        inline friend bool operator>(const AbstrIterator& a, const AbstrIterator& b)
        {
            return (!(a < b) && !(a == b));
        };
        inline friend bool            operator<=(const AbstrIterator& a, const AbstrIterator& b) { return !(a > b); };
        inline friend difference_type operator-(const AbstrIterator& a, const AbstrIterator& b)
        {
            return a.impl.difference(b.impl);
        };

    private:
        II impl;
    };

    vector<CompressedEdge>& getEdgeList() { return edgeList; }
    long                    getTStampNo() { return edgeList.size(); }

    void print();

private:
    long vertexNo = 0, edgeNo = 0, tstampNo = 0;

    // Adjacency data, CSR format
    int*     offsArray = nullptr;
    ColElem* edgeArray = nullptr;

    // Adjacency data, CSC format
    int*     inOffsArray = nullptr;
    ColElem* inEdgeArray = nullptr;

protected:
    vector<CompressedEdge> edgeList;

    // iterator implementation
    class CSRIteratorImpl {
    public:
        CSRIteratorImpl(ColElem* array, int i)
            : edgeArrayxxx(array)
            , ind(i)
        {
        }
        CSRIteratorImpl(const CSRIteratorImpl& other)
            : edgeArrayxxx(other.edgeArrayxxx)
            , ind(other.ind)
        {
        }
        CSRIteratorImpl(CSRIteratorImpl&& other)
            : edgeArrayxxx(std::move(other.edgeArrayxxx))
            , ind(std::move(other.ind))
        {
        }
        inline CSRIteratorImpl& operator=(const CSRIteratorImpl& other)
        {
            edgeArrayxxx = other.edgeArrayxxx;
            ind          = other.ind;
            return *this;
        }
        inline CSRIteratorImpl& operator=(CSRIteratorImpl&& other)
        {
            edgeArrayxxx = std::move(other.edgeArrayxxx);
            ind          = std::move(other.ind);
            return *this;
        }

        inline void increment(int i = 1) { ind += i; };
        inline void increment(long i) { ind += i; };
        inline bool equal(const CSRIteratorImpl& it) const { return ind == it.ind && edgeArrayxxx == it.edgeArrayxxx; };
        inline bool lessThan(const CSRIteratorImpl& it) const
        {
            return ind < it.ind && edgeArrayxxx == it.edgeArrayxxx;
        };
        inline difference_type difference(const CSRIteratorImpl& it) const
        {
            return edgeArrayxxx != it.edgeArrayxxx ? 0 : ind - it.ind;
        };

        inline reference getReference() { return edgeArrayxxx[ind]; };
        inline pointer   getPointer() { return &(edgeArrayxxx[ind]); };

    protected:
        ColElem* edgeArrayxxx = nullptr;
        int      ind;
    };

public:
    typedef AbstrIterator<CSRIteratorImpl> Iterator;

    inline Iterator beginOut(int vertex) { return Iterator(CSRIteratorImpl(edgeArray, offsArray[vertex])); }
    inline Iterator endOut(int vertex) { return Iterator(CSRIteratorImpl(edgeArray, offsArray[vertex + 1])); }
    inline Iterator beginIn(int vertex) { return Iterator(CSRIteratorImpl(inEdgeArray, inOffsArray[vertex])); }
    inline Iterator endIn(int vertex) { return Iterator(CSRIteratorImpl(inEdgeArray, inOffsArray[vertex + 1])); }
};

namespace {
    bool sortfirst(const pair<Timestamp, int>& a, const pair<Timestamp, int>& b) { return (a.first < b.first); }
}

inline void CSRGraph::readTemporalGraph(string path)
{
    ifstream graphFile(path);

    typedef vector<pair<Timestamp, int>> edgeInfoSet;

    GraphElemID                               edgeId = 0;
    unordered_map<int, map<int, edgeInfoSet>> adjacencyList;
    unordered_map<int, map<int, edgeInfoSet>> inEdgeList;

    Timestamp minTs = std::numeric_limits<Timestamp>::max(), maxTs = 0;
    int       maxNode = 0;
    tstampNo          = 0;

    while (true) {
        string line;
        getline(graphFile, line);
        if (graphFile.eof())
            break;
        if (line[0] == '%' || line[0] == '#')
            continue;

        stringstream ss(line);
        int          fromV, toV;
        Timestamp    tst = 0;
        ss >> fromV >> toV >> tst;
        if (fromV != toV) {
            tstampNo++;
            adjacencyList[fromV][toV].push_back({ tst, edgeId });
            // Hack that enable using the existing algorithms for cycle enumeration on the inverse graph
            inEdgeList[toV][fromV].push_back({ tst, edgeId });
            maxNode = max(maxNode, max(fromV, toV));
            if (tst != 0)
                minTs = min(minTs, tst);
            maxTs = max(maxTs, tst);
        }
        edgeList.push_back(CompressedEdge(fromV, toV, tst, edgeId));
        edgeId++;
    }
    vertexNo = maxNode + 1;

    for (auto pair : adjacencyList)
        edgeNo += pair.second.size();

    offsArray       = new int[vertexNo + 2];
    edgeArray       = new ColElem[edgeNo + 1];
    int currentOffs = 0;
    offsArray[0]    = 0;
    for (int i = 0; i < vertexNo; i++) {
        if (adjacencyList.find(i) != adjacencyList.end()) {
            for (auto& pair : adjacencyList[i]) {
                sort(pair.second.begin(), pair.second.end(), sortfirst);
                edgeArray[currentOffs].vertex = pair.first;
                for (auto epair : pair.second) {
                    edgeArray[currentOffs].tstamps.push_back(epair.first);
                    edgeArray[currentOffs].eids.push_back(epair.second);
                }
                currentOffs++;
            }
        }
        offsArray[i + 1] = currentOffs;
    }

    inOffsArray    = new int[vertexNo + 1];
    inEdgeArray    = new ColElem[edgeNo];
    currentOffs    = 0;
    inOffsArray[0] = 0;
    for (int i = 0; i < vertexNo; i++) {
        if (inEdgeList.find(i) != inEdgeList.end()) {
            for (auto& pair : inEdgeList[i]) {
                sort(pair.second.begin(), pair.second.end(), sortfirst);
                inEdgeArray[currentOffs].vertex = pair.first;
                for (auto epair : pair.second) {
                    inEdgeArray[currentOffs].tstamps.push_back(epair.first);
                    inEdgeArray[currentOffs].eids.push_back(epair.second);
                }
                currentOffs++;
            }
        }
        inOffsArray[i + 1] = currentOffs;
    }
    graphFile.close();

    cout << "VertexNo = " << vertexNo << "; edgeNo = " << tstampNo << endl;
}

/******************************** External Graph ******************************************/

#ifdef USE_EXT_GRAPH

class ExternalGraph : public CSRGraph {
private:
    CompressedGraph* csGraph = NULL;

public:
    ExternalGraph()
        : csGraph(new CompressedGraph()) {};
    ExternalGraph(CompressedGraph* cgraph)
        : csGraph(cgraph) {};
    virtual ~ExternalGraph() { csGraph = NULL; };

    void readTemporalGraph(string path) override;

    int getVertexNo() override { return csGraph->getVertexNo(); }
    int numNeighbors(int node) override { return csGraph->numOutEdges(node); };
    int numInEdges(int node) override { return csGraph->numInEdges(node); };

protected:
    class ExtIteratorImpl {
    public:
        ExtIteratorImpl(CompressedGraph::Iterator i)
            : iter(i)
        {
        }
        ExtIteratorImpl(const ExtIteratorImpl& other)
            : iter(other.iter)
        {
        }
        ExtIteratorImpl(ExtIteratorImpl&& other)
            : iter(std::move(other.iter))
        {
        }
        inline ExtIteratorImpl& operator=(const ExtIteratorImpl& other)
        {
            iter = other.iter;
            return *this;
        }
        inline ExtIteratorImpl& operator=(ExtIteratorImpl&& other)
        {
            iter = std::move(other.iter);
            return *this;
        }

        inline void            increment(int i = 1) { iter += i; };
        inline void            increment(long i) { iter += i; };
        inline bool            equal(const ExtIteratorImpl& it) const { return iter == it.iter; };
        inline bool            lessThan(const ExtIteratorImpl& it) const { return iter < it.iter; };
        inline difference_type difference(const ExtIteratorImpl& it) const { return iter - it.iter; };

        inline reference getReference() { return *iter; };
        inline pointer   getPointer() { return &(*iter); };

    protected:
        CompressedGraph::Iterator iter;
    };

public:
    typedef AbstrIterator<ExtIteratorImpl> Iterator;

    inline Iterator beginOut(int vertex) { return Iterator(ExtIteratorImpl(csGraph->beginOut(vertex))); }
    inline Iterator endOut(int vertex) { return Iterator(ExtIteratorImpl(csGraph->endOut(vertex))); }
    inline Iterator beginIn(int vertex) { return Iterator(ExtIteratorImpl(csGraph->beginIn(vertex))); }
    inline Iterator endIn(int vertex) { return Iterator(ExtIteratorImpl(csGraph->endIn(vertex))); }
};

inline void ExternalGraph::readTemporalGraph(string path)
{
    ifstream graphFile(path);

    GraphElemID edgeId = 0;

    while (true) {
        string line;
        getline(graphFile, line);
        if (graphFile.eof())
            break;
        if (line[0] == '%' || line[0] == '#')
            continue;

        stringstream ss(line);
        int          fromV, toV;
        Timestamp    tst = 0;
        ss >> fromV >> toV >> tst;
        edgeList.push_back(CompressedEdge(fromV, toV, tst, edgeId));
        edgeId++;
    }

    csGraph->compressEdgeList(edgeList);
}

#endif

#ifdef USE_EXT_GRAPH
typedef ExternalGraph Graph;
#else
typedef CSRGraph Graph;
#endif

}

#endif
