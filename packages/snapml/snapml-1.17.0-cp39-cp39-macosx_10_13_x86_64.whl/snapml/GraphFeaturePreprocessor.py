# *****************************************************************
#
# Licensed Materials - Property of IBM
#
# (C) Copyright IBM Corp. 2022. All Rights Reserved.
#
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
# ******************************************************************

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

from snapml._import import import_libsnapml

libsnapml = import_libsnapml(False)


class GraphFeaturePreprocessor(TransformerMixin, BaseEstimator):

    """
    Graph Feature Preprocessor

    This class implements a preprocessor for real-time extraction of graph-based features.

    There are two types of graph-based features that this preprocessor computes:

    1) graph patterns - for each edge in the input edge list, this preprocessor searches for
    graph patterns in which that edge participates. The graph patterns that can be used are:
    fan in/out, degree in/out, scatter-gather, temporal cycle, and length-constrained simple cycle.
    For each edge and each pattern type, this preprocessor computes a pattern histogram
    that contains the number of patterns of a given size.

    2) graph vertex statistics - for each vertex in the input edge list, this preprocessor
    computes various statistical properties based on the selected raw features of the outgoing
    or incoming edges. The statistical properties that can be computed are: number of neighboring
    vertices (fan), number of incident edges (degree), fan/degree ratio, as well as average, sum,
    minimum, maximum, median, var, skew, and kurtosis of the selected raw features.

    To generate graph-based features, this preprocessor maintains an in-memory graph.
    Whenever ``fit``, ``partial_fit``, or ``transform`` is called with an edge list as input,
    the edges in this list are inserted into the in-memory graph in the order they are provided.
    Edges that already exist in the in-memory graph are ignored during the insertion.
    Each edge insertion can also lead to the removal of some existing edges of the graph.
    More specifically, if the timestamp of an edge being inserted is ts_now, the edges
    with timestamps smaller than or equal to ts_now - ``time_window`` will be removed.
    Note that ``time_window`` can be set by calling ``set_params``. In addition, if
    ``max_no_edges`` is specified and it is a positive value, only ``max_no_edges`` most
    recently added edges are kept in the dynamic graph. Lastly, the edge list does not
    have to be sorted. However, the pattern detection is most effective when the edges
    in the list are sorted in the increasing order of their timestamps.

    Attributes
    ----------
    params : dict
        Parameters of this graph preprocessor.

        These parameters are used to define which graph pattern and graph vertex statistics
        features are going to be computed in ``transform()``. Valid parameter keys and their
        default values can be listed with ``get_params()`` and can be modified using
        ``set_params()``. The parameters in ``params`` are the following:

        num_threads : int, default=12
            Number of threads used in the computation.
        time_window : int, default=-1
            Time window size of the dynamic graph. If this parameter is set to a negative
            value, it is overwritten with the largest time window value ``<graph-feat>_tw``
            defined for a graph feature ``<graph-feat>``. The unit of time is the same as
            the one used for timestamps of edges.
        max_no_edges : int, default=-1
            Maximum number of edges that can exist in the dynamic graph. If this
            parameter is set to a negative value, the number of edges in the dynamic graph
            is defined only using the time window.


        vertex_stats : bool, default=True
            Enable generation of features based on vertex statistics.
        vertex_stats_tw : int
            Time window used for computing the vertex statistics. The unit of time is
            the same as the one used for timestamps of edges.
        vertex_stats_cols : array-like of int, default: [3]
            Columns of the input numpy array used for generating vertex statistics features.
        vertex_stats_feats : array-like of int, default: [0, 1, 2, 3, 4, 8, 9, 10]
            Array indicating which statistical properties are computed for each vertex.
            The mapping between the values of this array and the statistical properties is:
            0:fan, 1:degree, 2:ratio, 3:average, 4:sum, 5:minimum,
            6:maximum, 7:median, 8:var, 9:skew, 10:kurtosis.

        In the following parameters, <pattern-name> denotes one of the graph pattern names:
        fan, degree, scatter-gather, temp-cycle, and lc-cycle. These graph pattern names
        correspond to fan in/out, degree in/out, scatter-gather, temporal cycle, and
        length-constrained simple cycle patterns, respectively.

        <pattern-name> : bool
            Enable generation of graph pattern features based on <pattern-name> pattern.
        <pattern-name>_tw : int
            Time window used for computing the <pattern-name> patterns. The unit of time is
            the same as the one used for timestamps of edges.Increasing the time window enables
            finding more patters, but it also makes the problem more time consuming.
        <pattern-name>_bins : array-like of int
            Array used for specifying the bins of the pattern histogram for <pattern-name> pattern.
            Bin i in that histogram contains the number of patterns <pattern-name> of size S, where
            bin[i] <= S < bin[i+1]. The last bin contains the patterns of size greater than or equal
            to bin[i].

        lc-cycle_len : int, default=10
            Length constraint used when searching for length-constrained simple cycles. Increasing
            the value of this parameter enables finding longer cycles, but it also makes the problem
            more time consuming.

    """

    def __init__(self):
        self.preproc = libsnapml.gf_allocate()

        self.params = {
            "num_threads": 12,  # number of software threads to be used
            "time_window": -1,
            "max_no_edges": -1,
            "vertex_stats": True,  # produce vertex statistics
            "vertex_stats_tw": 480 * 3600,
            "vertex_stats_cols": [
                3
            ],  # produce vertex statistics using the selected input columns
            # features: 0:fan,1:deg,2:ratio,3:avg,4:sum,5:min,6:max,7:median,8:var,9:skew,10:kurtosis
            "vertex_stats_feats": [
                0,
                1,
                2,
                3,
                4,
                8,
                9,
                10,
            ],  # fan,deg,ratio,avg,sum,var,skew,kurtosis
            # fan in/out parameters
            "fan": True,
            "fan_tw": 12 * 3600,
            "fan_bins": [
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
                20,
                21,
                22,
                23,
                24,
                25,
                26,
                27,
                28,
                29,
                30,
            ],
            # in/out degree parameters
            "degree": False,
            "degree_tw": 12 * 3600,
            "degree_bins": [
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
                20,
                21,
                22,
                23,
                24,
                25,
                26,
                27,
                28,
                29,
                30,
            ],
            # scatter gather parameters
            "scatter-gather": False,
            "scatter-gather_tw": 120 * 3600,
            "scatter-gather_bins": [
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
                20,
                21,
                22,
                23,
                24,
                25,
                26,
                27,
                28,
                29,
                30,
            ],
            # temporal cycle parameters
            "temp-cycle": False,
            "temp-cycle_tw": 480 * 3600,
            "temp-cycle_bins": [
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
                20,
                21,
                22,
                23,
                24,
                25,
                26,
                27,
                28,
                29,
                30,
            ],
            # length-constrained simple cycle parameters
            "lc-cycle": False,
            "lc-cycle_tw": 240 * 3600,
            "lc-cycle_len": 10,
            "lc-cycle_bins": [2, 3, 4, 5, 6, 7, 8, 9, 10],
        }
        libsnapml.gf_set_params(self.preproc, self.params)

    def __setstate__(self, state):
        self.params = state[1]
        preproc = libsnapml.gf_allocate()
        libsnapml.gf_set_params(preproc, self.params)
        libsnapml.gf_import_graph(preproc, state[0])
        self.preproc = preproc

    def __getstate__(self):
        out_dims = libsnapml.gf_get_output_array_dims(self.preproc)
        features = np.zeros((out_dims[0], out_dims[1]), dtype="float64")
        libsnapml.gf_export_graph(self.preproc, features)
        state = [features, self.params]
        return state

    #######################################
    # GET PARAMETERS
    def get_params(self, deep=False):

        """
        Get the parameters of this graph preprocessor.

        Returns
        -------
        params : dict
        """

        if deep:
            return copy.deepcopy(self.params)
        else:
            return self.params

    #######################################
    # SET PARAMETERS
    def set_params(self, params):

        """
        Set the parameters of this graph preprocessor.

        Valid parameter keys can be listed with ``get_params()``.

        Invoking this function clears the existing in-memory graph.

        Returns
        -------
        params : dict
        """

        for key in params:
            if key in self.params:
                self.params[key] = params[key]
            else:
                raise KeyError("Unsupported key: " + key)
        libsnapml.gf_set_params(self.preproc, self.params)

    def __sklearn_clone__(self):
        gfp_clone = GraphFeaturePreprocessor()
        gfp_clone.set_params(self.get_params())
        return gfp_clone

    #######################################
    # LOAD THE GRAPH FROM NUMPY ARRAY
    def fit(self, features, y=None):

        """
        Create the in-memory graph using the edges from the input edge list ``features``.

        This function clears the existing in-memory graph before creating a new
        graph using the edges from the input edge list ``features``.

        Parameters
        ----------
        features : array-like of float, shape = (n_edges, n_raw_features)
            Input edge list. Each edge of this edge list should have the following format:
            [Edge ID, Source Vertex ID, Target Vertex ID, Timestamp, <other raw features>].
        """

        features = np.ascontiguousarray(features, dtype=np.float64)
        libsnapml.gf_import_graph(self.preproc, features)

    #######################################
    # UPDATE THE GRAPH
    def partial_fit(self, features):

        """
        Update the in-memory graph with the edges from the input edge list ``features``.

        This function inserts the edges from the input edge list ``features`` into the in-memory graph.

        Parameters
        ----------
        features : array-like of float, shape = (n_edges, n_raw_features)
            Input edge list. Each edge of this edge list should have the following format:
            [Edge ID, Source Vertex ID, Target Vertex ID, Timestamp, <other raw features>].
        """

        features = np.ascontiguousarray(features, dtype=np.float64)
        libsnapml.gf_partial_fit(self.preproc, features)

    #######################################
    # ENRICH FEATURE VECTORS
    def transform(self, features_in):

        """
        Generate graph-based features for each edge in the input edge list ``features_in``.

        This function inserts the edges from the input edge list ``features_in`` into the in-memory graph of
        this preprocessor and computes the graph-based features using the updated graph. The input edge list
        is updated with the graph-based features and is returned as the output.

        The computed graph-based features have the following format:
        <graph-based features> = <graph-pattern features> <vertex statistics features>

        The graph-pattern features <graph-pattern features> are created by concatenating the calculated pattern
        histograms for the patterns in the following order: fan-in, fan-out, degree-in, degree-out, scatter-gather,
        temporal cycle, length-constrained simple cycles. Only the histograms of the graph patterns that are enabled
        in ``params`` are present in <graph-pattern features>.

        The graph vertex statistics features <vertex statistics features> contain the features for the source
        and the target vertex of an edge. These vertex features are calculated separately for outgoing and incoming
        edges of each vertex:
        <vertex statistics features> = <source vertex features - outgoing edges> <source vertex features - incoming edges>
                                       <target vertex features - outgoing edges> <target vertex features - incoming edges>

        Source/target vertex features for both outgoing and incoming edges have the following format:
        <fan> <degree> <ratio> <average,sum,...,kurtosis for c_0>...<average,sum,...,kurtosis for c_k>
        where c_0,...,c_k are raw feature columns specified in ``vertex_stats_cols`` of ``params``.
        The vertex statistics features other than fan, degree, and ratio are calculated for each raw feature
        column from ``vertex_stats_cols``. Only the vertex statistics features that are selected in
        ``vertex_stats_feats`` of ``params`` are present in <vertex statistics features>.

        Parameters
        ----------
        features_in : array-like of float, shape = (n_edges, n_raw_features)
            Input edge list. Each edge of this edge list should have the following format:
            [Edge ID, Source Vertex ID, Target Vertex ID, Timestamp, <other raw features>].

        Returns
        -------
        features_out: array-like of float, shape = (n_edges, n_raw_features + n_eng_features)
            Input edge list with additional n_eng_features graph-based features per edge.
            Each edge of this edge list has the following format:
            [Edge ID, Source Vertex ID, Target Vertex ID, Timestamp, <other raw features>, <graph-based features>].
        """

        features_in = np.ascontiguousarray(features_in, dtype=np.float64)
        num_out_features = (
            libsnapml.gf_get_num_engineered_features(self.preproc)
            + features_in.shape[1]
        )
        features_out = np.zeros(
            (features_in.shape[0], num_out_features), dtype="float64"
        )

        libsnapml.gf_transform(self.preproc, features_in, features_out)

        return features_out

    #######################################
    # EQUIVALENT TO TRANSFORM
    def fit_transform(self, features_in, y=None):

        """
        Generate graph-based features for each edge in the input edge list ``features_in``.

        This function is equivalent to performing ``fit`` followed by ``transform`` using
        the same input edge list ``features_in``.

        Parameters
        ----------
        features_in : array-like of float, shape = (n_edges, n_raw_features)
            Input edge list. Each edge of this edge list should have the following format:
            [Edge ID, Source Vertex ID, Target Vertex ID, Timestamp, <other raw features>].

        Returns
        -------
        features_out: array-like of float, shape = (n_edges, n_raw_features + n_eng_features)
            Input edge list with additional n_eng_features graph-based features per edge.
            Each edge of this edge list has the following format:
            [Edge ID, Source Vertex ID, Target Vertex ID, Timestamp, <other raw features>, <graph-based features>].
        """

        features_in = np.ascontiguousarray(features_in, dtype=np.float64)

        self.fit(features_in)

        features_out = self.transform(features_in)

        return features_out

    #######################################
