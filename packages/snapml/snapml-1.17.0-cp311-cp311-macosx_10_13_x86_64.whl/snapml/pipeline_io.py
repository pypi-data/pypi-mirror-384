# *****************************************************************
#
# Licensed Materials - Property of IBM
#
# (C) Copyright IBM Corp. 2023. All Rights Reserved.
#
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
# *****************************************************************

from sklearn.pipeline import Pipeline
import sklearn.preprocessing
from sklearn.preprocessing import (
    Normalizer,
    OneHotEncoder,
    KBinsDiscretizer,
    FunctionTransformer,
    OrdinalEncoder,
)

import sys
import os

from snapml import GraphFeaturePreprocessor

if "TargetEncoder" in sklearn.preprocessing.__dict__:
    from sklearn.preprocessing import TargetEncoder
import json
import numpy as np
from sklearn.compose import ColumnTransformer
import types


def pipeline_step_analysis(transformer: object, columns: list):
    preprocessing_step = {}

    if isinstance(transformer, FunctionTransformer):
        preprocessing_step["type"] = "FunctionTransformer"
        func_params = transformer.get_params()
        if (not isinstance(func_params["func"], types.BuiltinFunctionType)) and (
            not isinstance(func_params["func"], np.ufunc)
        ):
            raise ValueError(
                "FuncTransformer: Support available only for functions that are built-in or numpy functions (log10, log1p, log, log2)."
            )
        if func_params["func"].__name__ not in ["log1p", "log10", "log2", "log"]:
            raise ValueError(
                "FuncTransformer : Support available only for the following logarithmic functions: log1p, log10, log2 or log."
            )
        func_params["func"] = func_params["func"].__name__
        preprocessing_step["params"] = func_params
        preprocessing_step["data"] = {}
        preprocessing_step["columns"] = columns
        is_numeric_feature = True
    elif isinstance(transformer, Normalizer):
        preprocessing_step["type"] = "Normalizer"
        preprocessing_step["params"] = transformer.get_params()
        if preprocessing_step["params"]["norm"] not in ["l2", "l1", "max"]:
            raise ValueError(
                "Normalizer: Parameter <<norm>> must be 'l2', 'l1' or 'max'."
            )
        preprocessing_step["data"] = {}
        preprocessing_step["columns"] = columns
        is_numeric_feature = True
    elif isinstance(transformer, KBinsDiscretizer):
        preprocessing_step["type"] = "KBinsDiscretizer"
        preprocessing_step["params"] = transformer.get_params()
        if preprocessing_step["params"]["encode"] != "ordinal":
            raise ValueError(
                "KBinsDiscretizer: Parameter <<encode>> must be 'ordinal'."
            )
        preprocessing_step["data"] = {}
        bin_edges = [r.tolist() for r in transformer.bin_edges_]
        preprocessing_step["columns"] = columns
        preprocessing_step["data"]["bin_edges"] = bin_edges
        is_numeric_feature = True
    elif isinstance(transformer, OneHotEncoder):
        preprocessing_step["type"] = "OneHotEncoder"
        onehot_params = transformer.get_params()
        if onehot_params["categories"] != "auto":
            raise ValueError("OneHotEncoder: Parameter <<categories>> must be 'auto'.")
        if onehot_params["sparse_output"] != False:
            raise ValueError("OneHotEncoder: Sparse output is not supported.")
        if onehot_params["handle_unknown"] != "ignore":
            raise ValueError(
                "OneHotEncoder: Parameter <<handle_unknown>> must be set to 'ignore'."
            )
        onehot_params["dtype"] = onehot_params["dtype"].__name__
        preprocessing_step["params"] = onehot_params
        preprocessing_step["data"] = {}
        categories = [r.tolist() for r in transformer.categories_]
        preprocessing_step["data"]["categories"] = categories
        preprocessing_step["columns"] = columns
        is_numeric_feature = False
    elif isinstance(transformer, OrdinalEncoder):
        preprocessing_step["type"] = "OrdinalEncoder"
        ordinal_params = transformer.get_params()
        if ordinal_params["categories"] != "auto":
            raise ValueError("OrdinalEncoder: Parameter <<categories>> must be 'auto'.")
        if ordinal_params["handle_unknown"] != "use_encoded_value":
            raise ValueError(
                "OrdinalEncoder: Parameter <<handle_unknown>> must be set to 'use_encoded_value'."
            )
        ordinal_params["dtype"] = ordinal_params["dtype"].__name__
        removed_value = ordinal_params.pop("encoded_missing_value", "Not found")
        preprocessing_step["params"] = ordinal_params
        preprocessing_step["data"] = {}
        categories = [r.tolist() for r in transformer.categories_]
        preprocessing_step["data"]["categories"] = categories
        preprocessing_step["columns"] = columns
        is_numeric_feature = False
    elif isinstance(transformer, TargetEncoder):
        preprocessing_step["type"] = "TargetEncoder"
        target_params = transformer.get_params()
        if target_params["categories"] != "auto":
            raise ValueError("TargetEncoder: Parameter <<categories>> must be 'auto'.")
        preprocessing_step["params"] = target_params
        preprocessing_step["data"] = {}
        categories = [r.tolist() for r in transformer.categories_]
        encodings = [r.tolist() for r in transformer.encodings_]
        preprocessing_step["data"]["categories"] = categories
        preprocessing_step["data"]["encodings"] = encodings
        preprocessing_step["data"]["target_mean"] = transformer.target_mean_
        preprocessing_step["columns"] = columns
        is_numeric_feature = False
    elif isinstance(transformer, GraphFeaturePreprocessor):
        preprocessing_step["type"] = "GraphFeaturePreprocessor"
        gfp_params = transformer.get_params()
        preprocessing_step["params"] = gfp_params
        preprocessing_step["data"] = {}
        preprocessing_step["columns"] = columns
        is_numeric_feature = True
    else:
        raise ValueError("Transformer not supported.")

    return preprocessing_step, is_numeric_feature


def export_preprocessing_pipeline(pipeline: object, pipeline_file):
    """
    Dump a preprocessing pipeline to a 'json' file.


    Parameters
    ----------

    pipeline : object
        sklearn pipeline object

    data_columns : object
        DataFrame column info

    pipeline_file : str
        Pipeline filename


    """

    if not isinstance(pipeline, ColumnTransformer):
        raise ValueError(
            "Processing pipeline not supported. Only ColumnTransfomer is currently supported."
        )

    data_columns = []
    for transformer_name, transformer, columns in pipeline.transformers:
        data_columns.extend(columns)

    preprocessing_pipeline = {}
    preprocessing_pipeline["data_schema"] = {}

    index_positional_numeric = []
    index_positional_categorical = []

    # create a list of all the transformers in the pipeline
    preprocessing_pipeline["transformers"] = {}
    trans_index = 0

    for transformer in pipeline.transformers_:
        # check if transformer is a Pipeline
        trans_index = trans_index + 1
        preprocessing_pipeline["transformers"]["transformer" + str(trans_index)] = []
        if isinstance(transformer[1], Pipeline):
            for step in transformer[1].steps:
                cols = [data_columns.index(col) for col in transformer[2]]
                preprocessing_step, is_numeric_feature = pipeline_step_analysis(
                    step[1], cols
                )
                if is_numeric_feature:
                    temp = [num for num in cols if num not in index_positional_numeric]
                    index_positional_numeric = index_positional_numeric + temp
                else:
                    temp = [
                        num for num in cols if num not in index_positional_categorical
                    ]
                    index_positional_categorical = index_positional_categorical + temp
                preprocessing_pipeline["transformers"][
                    "transformer" + str(trans_index)
                ].append(preprocessing_step)
        else:
            cols = [data_columns.index(col) for col in transformer[2]]
            preprocessing_step, is_numeric_feature = pipeline_step_analysis(
                transformer[1], cols
            )
            if is_numeric_feature:
                temp = [num for num in cols if num not in index_positional_numeric]
                index_positional_numeric = index_positional_numeric + temp
            else:
                temp = [num for num in cols if num not in index_positional_categorical]
                index_positional_categorical = index_positional_categorical + temp
            preprocessing_pipeline["transformers"][
                "transformer" + str(trans_index)
            ].append(preprocessing_step)

    index_positional_numeric.sort()
    index_positional_categorical.sort()
    preprocessing_pipeline["data_schema"]["num_indices"] = index_positional_numeric
    preprocessing_pipeline["data_schema"]["cat_indices"] = index_positional_categorical
    preprocessing_pipeline["remainder"] = "passthrough"
    # print(json.JSONEncoder(indent=4).encode(preprocessing_pipeline))

    with open(pipeline_file, "w") as outfile:
        json.dump(preprocessing_pipeline, outfile, indent=4)
