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

#ifndef COMPRESSED_GRAPH_H
#define COMPRESSED_GRAPH_H

#include <algorithm>
#include <exception>

#include "baseGraph.h"

using namespace std;

struct ColElem {
    int                 vertex;
    vector<Timestamp>   tstamps;
    vector<GraphElemID> eids;
};

typedef std::unordered_map<int, ColElem> AdjacencyList;

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

/******************* Compressed Graph interface *******************/

/**
 * Interface of a compressed graph.
 *
 * @tparam D Derived class of CompressedGraphIF. Used for static polymorphism
 */
template <class D> class CompressedGraphIF {
public:
    /**
     * Creates compressed sparse representation of the graph from the list of edges.
     *
     * @param edgeList List of edges of the graph
     */
    void compressEdgeList(EdgeList& edgeList) { static_cast<D*>(this)->compressEdgeList(edgeList); };

    // Used for compatibility with parallell cycle enumeration
    void compressEdgeList(vector<CompressedEdge>& edgeList) { static_cast<D*>(this)->compressEdgeList(edgeList); };

    /**
     * Returns the number of outgoing edges of the vertex v
     *
     * @param v Vertex id of the graph
     */
    int numOutEdges(int v) { return static_cast<D*>(this)->numOutEdges(v); };

    /**
     * Returns the number of incoming edges of the vertex v
     *
     * @param v Vertex id of the graph
     */
    int numInEdges(int v) { return static_cast<D*>(this)->numInEdges(v); };

    /**
     * Returns the number of veritces of the vertex v connected via outgoing edges
     *
     * @param v Vertex id of the graph
     */
    int numOutVertices(int v) { return static_cast<D*>(this)->numOutVertices(v); };

    /**
     * Returns the number of veritces of the vertex v connected via incoming edges
     *
     * @param v Vertex id of the graph
     */
    int numInVertices(int v) { return static_cast<D*>(this)->numInVertices(v); };

    long getVertexNo() { return static_cast<D*>(this)->getVertexNo(); };

    AdjacencyList& getAdjList(int vert, bool out) { return static_cast<D*>(this)->getAdjList(vert, out); }

    // TODO: Class DynamicGraphIF
    int addTempEdge(GraphElemID edgeID, Timestamp tstamp, int fromVertex, int toVertex)
    {
        return static_cast<D*>(this)->addTempEdge(edgeID, tstamp, fromVertex, toVertex);
    };

    void removeEdge(Edge& edge) { static_cast<D*>(this)->removeEdge(edge); };

    void setTimeWindow(Timestamp tw) { static_cast<D*>(this)->setTimeWindow(tw); };

    Timestamp getTimeWindow() { return static_cast<D*>(this)->getTimeWindow(); };
};

using difference_type = std::ptrdiff_t;
using pointer         = ColElem*;
using reference       = ColElem&;

/**
 * Interface of a graph that has iterable adjacency lists.
 * This class defines foreachOutEdge and foreachInEdge template functions.
 *
 * @tparam D Derived class of IterableAdjacencyList. Used for static polymorphism
 * @tparam II Iterator implementation class that has the following format:
 * class IteratorImpl {
 * public:
 *      void increment();
 *      void increment(int i);
 *      void increment(long i);
 *      bool equal(const IteratorImpl& it) const;
 *      bool lessThan(const IteratorImpl& it) const;
 *      difference_type difference(const IteratorImpl& it) const;
 *      reference getReference();
 *      pointer getPointer();
 *  };
 */
template <class D, class II> class IterableAdjacencyList {
public:
    struct Iterator {
        Iterator(II im)
            : impl(im)
        {
        }
        ~Iterator() { }

        Iterator(const Iterator& other)
            : impl(other.impl)
        {
        }
        inline Iterator(Iterator&& other)
            : impl(other.impl)
        {
        }
        inline Iterator& operator=(const Iterator& other)
        {
            impl = other.impl;
            return *this;
        }
        inline Iterator& operator=(Iterator&& other)
        {
            impl = std::move(other.impl);
            return *this;
        }

        inline reference operator*() { return impl.getReference(); }
        inline pointer   operator->() { return impl.getPointer(); }
        inline Iterator& operator++()
        {
            impl.increment();
            return *this;
        }
        inline Iterator operator++(int)
        {
            Iterator tmp = *this;
            ++(*this);
            return tmp;
        }
        inline Iterator& operator+=(int i)
        {
            impl.increment(i);
            return *this;
        }
        inline Iterator& operator+=(long i)
        {
            impl.increment(i);
            return *this;
        }
        inline friend bool operator==(const Iterator& a, const Iterator& b) { return a.impl.equal(b.impl); };
        inline friend bool operator!=(const Iterator& a, const Iterator& b) { return !(a == b); };
        inline friend bool operator<(const Iterator& a, const Iterator& b) { return a.impl.lessThan(b.impl); };
        inline friend bool operator>=(const Iterator& a, const Iterator& b) { return !(a < b); };
        inline friend bool operator>(const Iterator& a, const Iterator& b) { return (!(a < b) && !(a == b)); };
        inline friend bool operator<=(const Iterator& a, const Iterator& b) { return !(a > b); };
        inline friend difference_type operator-(const Iterator& a, const Iterator& b)
        {
            return a.impl.difference(b.impl);
        };

    private:
        II impl;
    };

    // Abstract functions
    inline Iterator beginOut(int vertex) { return static_cast<D*>(this)->beginOut(vertex); };
    inline Iterator endOut(int vertex) { return static_cast<D*>(this)->endOut(vertex); };
    inline Iterator beginIn(int vertex) { return static_cast<D*>(this)->beginIn(vertex); };
    inline Iterator endIn(int vertex) { return static_cast<D*>(this)->endIn(vertex); };

    /**
     * Iterate through the outgoing edges of v and invokes f on every edge
     *
     * Function f is required to have the following declaration
     * void f(int u, Edge* e);
     * Here, u is a neighbor of v, and e is the edge connecting them.
     * This function can be implemented as a lambda expression, for instance:
     * foreachOutEdge(v, [&](int u, Edge* e){
     *      ....
     * });
     *
     * @param v Vertex id of the graph
     * @param f Function with parameters (int, Edge*)
     */
    template <typename TF> void foreachOutEdge(int v, TF&& f)
    {
        for (auto it = beginOut(v); it != endOut(v); it++) {
            int   w    = it->vertex;
            auto& tset = it->tstamps;
            auto& eids = it->eids;

            for (unsigned int i = 0; i < tset.size(); i++) {
                auto ts  = tset[i];
                auto eid = eids[i];

                f(w, ts, eid);
            }
        }
    }

    /**
     * Iterate through the incoming edges of v and invokes f on every edge
     *
     * This function behaves in the similar way to the foreachOutEdge function.
     *
     * @param v Vertex id of the graph
     * @param f Function with parameters (int, Edge*)
     */
    template <typename TF> void foreachInEdge(int v, TF&& f)
    {
        for (auto it = beginIn(v); it != endIn(v); it++) {
            int   w    = it->vertex;
            auto& tset = it->tstamps;
            auto& eids = it->eids;

            for (unsigned int i = 0; i < tset.size(); i++) {
                auto ts  = tset[i];
                auto eid = eids[i];

                f(w, ts, eid);
            }
        }
    }

    /**
     * Iterate through the outgoing edges of v and invokes f on every edge
     *
     * Function f is required to have the following declaration
     * void f(int u, Edge* e);
     * Here, u is a neighbor of v, and e is the edge connecting them.
     * This function can be implemented as a lambda expression, for instance:
     * foreachOutEdge(v, [&](int u, Edge* e){
     *      ....
     * });
     *
     * @param v Vertex id of the graph
     * @param f Function with parameters (int, Edge*)
     */
    template <typename TF> void foreachOutVertex(int v, TF&& f)
    {
        for (auto it = beginOut(v); it != endOut(v); it++) {
            int   w     = it->vertex;
            auto& colel = *it;

            f(w, colel);
        }
    }

    /**
     * Iterate through the incoming edges of v and invokes f on every edge
     *
     * This function behaves in the similar way to the foreachOutEdge function.
     *
     * @param v Vertex id of the graph
     * @param f Function with parameters (int, Edge*)
     */
    template <typename TF> void foreachInVertex(int v, TF&& f)
    {
        for (auto it = beginIn(v); it != endIn(v); it++) {
            int   w     = it->vertex;
            auto& colel = *it;

            f(w, colel);
        }
    }
};

template <class D, class II>
class CompressedGraphBase : public CompressedGraphIF<D>, public IterableAdjacencyList<D, II> {
public:
    CompressedGraphBase() { }
};

#if USE_DYNAMIC_GRAPH == True

/******************* Compressed Dynamic Graph *******************/

class DynIteratorImpl {
public:
    DynIteratorImpl(AdjacencyList::iterator it)
        : iter(it)
    {
    }
    DynIteratorImpl(const DynIteratorImpl& other)
        : iter(other.iter)
    {
    }
    DynIteratorImpl(DynIteratorImpl&& other)
        : iter(std::move(other.iter))
    {
    }
    inline DynIteratorImpl& operator=(const DynIteratorImpl& other)
    {
        iter = other.iter;
        return *this;
    }
    inline DynIteratorImpl& operator=(DynIteratorImpl&& other)
    {
        iter = std::move(other.iter);
        return *this;
    }

    inline void            increment() { iter++; };
    inline void            increment(int i) { std::advance(iter, i); };
    inline void            increment(long i) { std::advance(iter, i); };
    inline bool            equal(const DynIteratorImpl& it) const { return it.iter == iter; };
    inline bool            lessThan(const DynIteratorImpl& it) const { return std::distance(iter, it.iter) > 0; };
    inline difference_type difference(const DynIteratorImpl& it) const { return std::distance(it.iter, iter); };

    inline reference getReference() { return iter->second; };
    inline pointer   getPointer() { return &(iter->second); };

protected:
    AdjacencyList::iterator iter;
};

class CompressedGraph : public CompressedGraphBase<CompressedGraph, DynIteratorImpl> {
public:
    CompressedGraph() { }

    ~CompressedGraph() { }

    // CompressedGraphIF methods
    void compressEdgeList(EdgeList& edgeList);

    void compressEdgeList(vector<CompressedEdge>& edgeList);

    int numOutEdges(int v);

    int numInEdges(int v);

    int numOutVertices(int v);

    int numInVertices(int v);

    long getVertexNo() { return vertNo; };

    // DynamicGraphIF methods
    int addTempEdge(GraphElemID edgeID, Timestamp tstamp, int fromVertex, int toVertex);

    void removeEdge(Edge& edge);

    void setTimeWindow(Timestamp tw) { timeWindow = tw; }
    void setWindowSize(int ws) { windowSize = ws; }

    Timestamp getTimeWindow() { return timeWindow; }
    int       getWindowSize() { return windowSize; }

    AdjacencyList& getAdjList(int vert, bool out);

public:
    // IterableAdjacencyList methods
    inline Iterator beginOut(int v) { return Iterator(DynIteratorImpl(outVertMap[v].begin())); }
    inline Iterator endOut(int v) { return Iterator(DynIteratorImpl(outVertMap[v].end())); }
    inline Iterator beginIn(int v) { return Iterator(DynIteratorImpl(inVertMap[v].begin())); }
    inline Iterator endIn(int v) { return Iterator(DynIteratorImpl(inVertMap[v].end())); }

private:
    std::vector<AdjacencyList> outVertMap;
    std::vector<AdjacencyList> inVertMap;

    // Used for numOutEdges and numInEdges
    vector<int> outDegrees, inDegrees;

    int vertNo = 0;
    int edgeNo = 0;

    Timestamp currTimestamp;
    Timestamp timeWindow;
    int       windowSize;
};

inline AdjacencyList& CompressedGraph::getAdjList(int vert, bool out)
{
    return (out ? outVertMap[vert] : inVertMap[vert]);
}

inline void CompressedGraph::compressEdgeList(EdgeList& edgeList)
{
    for (auto& edge : edgeList) {
        addTempEdge(edge->getIndex(), edge->getTStamp(), edge->getSourceVertexIndex(), edge->getTargetVertexIndex());
    }
}

inline void CompressedGraph::compressEdgeList(vector<CompressedEdge>& edgeList)
{
    for (auto& edge : edgeList) {
        addTempEdge(edge.eid, edge.tstamp, edge.fromV, edge.toV);
    }
}

inline int CompressedGraph::addTempEdge(GraphElemID edgeID, Timestamp tstamp, int sourceVertexIndex,
                                        int targetVertexIndex)
{

    int newVertNo = vertNo;
    newVertNo     = max(newVertNo, sourceVertexIndex + 1);
    newVertNo     = max(newVertNo, targetVertexIndex + 1);

    if (newVertNo > vertNo) {
        vertNo = newVertNo;
        outVertMap.resize(vertNo);
        inVertMap.resize(vertNo);
        outDegrees.resize(vertNo, 0);
        inDegrees.resize(vertNo, 0);
    }

    // Out edges
    auto& adjListOut = outVertMap[sourceVertexIndex];
    auto& outEntry   = adjListOut[targetVertexIndex];

    outEntry.vertex = targetVertexIndex;
    outDegrees[sourceVertexIndex] += 1;
    if (outEntry.tstamps.empty() || outEntry.tstamps.back() <= tstamp) {
        outEntry.tstamps.push_back(tstamp);
        outEntry.eids.push_back(edgeID);
    } else {
        auto it1   = upper_bound(outEntry.tstamps.begin(), outEntry.tstamps.end(), tstamp);
        int  index = it1 - outEntry.tstamps.begin();
        outEntry.tstamps.insert(it1, tstamp);
        auto it2 = outEntry.eids.begin() + index;
        outEntry.eids.insert(it2, edgeID);
    }

    // In edges
    auto& adjListIn = inVertMap[targetVertexIndex];
    auto& inEntry   = adjListIn[sourceVertexIndex];

    inEntry.vertex = sourceVertexIndex;
    inDegrees[targetVertexIndex] += 1;
    if (inEntry.tstamps.empty() || inEntry.tstamps.back() <= tstamp) {
        inEntry.tstamps.push_back(tstamp);
        inEntry.eids.push_back(edgeID);
    } else {
        auto it1   = upper_bound(inEntry.tstamps.begin(), inEntry.tstamps.end(), tstamp);
        int  index = it1 - inEntry.tstamps.begin();
        inEntry.tstamps.insert(it1, tstamp);
        auto it2 = inEntry.eids.begin() + index;
        inEntry.eids.insert(it2, edgeID);
    }

    // Update the edge list
    currTimestamp = tstamp;

    edgeNo++;
    return 0;
}

inline void CompressedGraph::removeEdge(Edge& edge)
{
    // TODO: Consider using circular buffer for faster removal of edges
    GraphElemID eid               = edge.getID();
    int         sourceVertexIndex = edge.getSourceVertexIndex();
    int         targetVertexIndex = edge.getTargetVertexIndex();

    // Out edges
    auto& adjListOut = outVertMap[sourceVertexIndex];
    auto& outEntry   = adjListOut[targetVertexIndex];

    {
        auto eit = outEntry.eids.begin();
        if (*eit != eid)
            eit = find(outEntry.eids.begin(), outEntry.eids.end(), eid);

        if (eit != outEntry.eids.end()) {
            int  ind = eit - outEntry.eids.begin();
            auto tit = outEntry.tstamps.begin() + ind;
            outEntry.eids.erase(eit);
            outEntry.tstamps.erase(tit);

            outDegrees[sourceVertexIndex] -= 1;
        }
    }

    if (outEntry.eids.empty() && outEntry.tstamps.empty()) {
        adjListOut.erase(targetVertexIndex);
    }

    // In edges
    auto& adjListIn = inVertMap[targetVertexIndex];
    auto& inEntry   = adjListIn[sourceVertexIndex];

    {
        auto eit = inEntry.eids.begin();
        if (*eit != eid)
            eit = find(inEntry.eids.begin(), inEntry.eids.end(), eid);

        if (eit != inEntry.eids.end()) {
            int  ind = eit - inEntry.eids.begin();
            auto tit = inEntry.tstamps.begin() + ind;
            inEntry.eids.erase(eit);
            inEntry.tstamps.erase(tit);

            inDegrees[targetVertexIndex] -= 1;
        }
    }

    if (inEntry.eids.empty() && inEntry.tstamps.empty()) {
        adjListIn.erase(sourceVertexIndex);
    }

    edgeNo--;
}

inline int CompressedGraph::numOutEdges(int v)
{
    if (v < 0 || v >= static_cast<int>(outVertMap.size()))
        throw std::out_of_range("Vertex index out of bounds.");
    return outDegrees[v];
}

inline int CompressedGraph::numInEdges(int v)
{
    if (v < 0 || v >= static_cast<int>(inVertMap.size()))
        throw std::out_of_range("Vertex index out of bounds.");
    return inDegrees[v];
}

inline int CompressedGraph::numOutVertices(int v)
{
    if (v < 0 || v >= static_cast<int>(outVertMap.size()))
        throw std::out_of_range("Vertex index out of bounds.");
    return outVertMap[v].size();
}

inline int CompressedGraph::numInVertices(int v)
{
    if (v < 0 || v >= static_cast<int>(inVertMap.size()))
        throw std::out_of_range("Vertex index out of bounds.");
    return inVertMap[v].size();
}

typedef CompressedGraph CompressedDynamicGraph;

#else

/******************* Compressed Sparse Graph *******************/

class CSRIteratorImpl {
public:
    CSRIteratorImpl(ColElem* array, int i)
        : edgeArray(array)
        , ind(i)
    {
    }
    CSRIteratorImpl(const CSRIteratorImpl& other)
        : edgeArray(other.edgeArray)
        , ind(other.ind)
    {
    }
    CSRIteratorImpl(CSRIteratorImpl&& other)
        : edgeArray(std::move(other.edgeArray))
        , ind(std::move(other.ind))
    {
    }
    inline CSRIteratorImpl& operator=(const CSRIteratorImpl& other)
    {
        edgeArray = other.edgeArray;
        ind       = other.ind;
        return *this;
    }
    inline CSRIteratorImpl& operator=(CSRIteratorImpl&& other)
    {
        edgeArray = std::move(other.edgeArray);
        ind       = std::move(other.ind);
        return *this;
    }

    inline void increment(int i = 1) { ind += i; };
    inline void increment(long i) { ind += i; };
    inline bool equal(const CSRIteratorImpl& it) const { return ind == it.ind && edgeArray == it.edgeArray; };
    inline bool lessThan(const CSRIteratorImpl& it) const { return ind < it.ind && edgeArray == it.edgeArray; };
    inline difference_type difference(const CSRIteratorImpl& it) const
    {
        return edgeArray != it.edgeArray ? 0 : ind - it.ind;
    };

    inline reference getReference() { return edgeArray[ind]; };
    inline pointer   getPointer() { return &(edgeArray[ind]); };

protected:
    ColElem* edgeArray = nullptr;
    int      ind;
};

class CompressedGraph : public CompressedGraphBase<CompressedGraph, CSRIteratorImpl> {
public:
    CompressedGraph() { }

    CompressedGraph(EdgeList& edgeList) { compressEdgeList(edgeList); };

    ~CompressedGraph();

    // CompressedGraphIF methods
    void compressEdgeList(EdgeList& edgeList);

    // Used for compatibility with parallell cycle enumeration
    void compressEdgeList(vector<CompressedEdge>& edgeList);

    int numOutEdges(int v);

    int numInEdges(int v);

    int numOutVertices(int v);

    int numInVertices(int v);

    long getVertexNo() { return vertexNo; };

    // DynamicGraphIF methods
    int       addTempEdge(GraphElemID edgeID, Timestamp tstamp, int fromVertex, int toVertex) { return 0; }
    void      removeEdge(Edge& edge) { }
    void      setTimeWindow(Timestamp tw) { }
    Timestamp getTimeWindow() { return -1; }

private:
    long vertexNo = 0, edgeNo = 0, tstampNo = 0;

    // Adjacency data, CSR format
    int*     offsArray = nullptr;
    ColElem* edgeArray = nullptr;

    int* outDegrees = nullptr;

    // Adjacency data, CSC format
    int*     inOffsArray = nullptr;
    ColElem* inEdgeArray = nullptr;

    int* inDegrees = nullptr;

public:
    // IterableAdjacencyList methods
    inline Iterator beginOut(int v) { return Iterator(CSRIteratorImpl(edgeArray, offsArray[v])); }
    inline Iterator endOut(int v) { return Iterator(CSRIteratorImpl(edgeArray, offsArray[v + 1])); }
    inline Iterator beginIn(int v) { return Iterator(CSRIteratorImpl(inEdgeArray, inOffsArray[v])); }
    inline Iterator endIn(int v) { return Iterator(CSRIteratorImpl(inEdgeArray, inOffsArray[v + 1])); }
};

inline CompressedGraph::~CompressedGraph()
{
    delete[] offsArray;
    delete[] edgeArray;
    delete[] inOffsArray;
    delete[] inEdgeArray;
    delete[] outDegrees;
    delete[] inDegrees;
    vertexNo = 0;
    edgeNo   = 0;
    tstampNo = 0;
}

// TODO: This actually returns the number of adjacent vertices, rather than edges. Fix this
inline int CompressedGraph::numOutEdges(int v)
{
    if (v < 0 || v >= vertexNo)
        throw std::out_of_range("Vertex index out of bounds.");
    return outDegrees[v];
}
inline int CompressedGraph::numInEdges(int v)
{
    if (v < 0 || v >= vertexNo)
        throw std::out_of_range("Vertex index out of bounds.");
    return inDegrees[v];
}

inline int CompressedGraph::numOutVertices(int v)
{
    if (v < 0 || v >= vertexNo)
        throw std::out_of_range("Vertex index out of bounds.");
    return offsArray[v + 1] - offsArray[v];
}

inline int CompressedGraph::numInVertices(int v)
{
    if (v < 0 || v >= vertexNo)
        throw std::out_of_range("Vertex index out of bounds.");
    return inOffsArray[v + 1] - inOffsArray[v];
}

typedef CompressedGraph CompressedSparseGraph;

#endif

#endif
