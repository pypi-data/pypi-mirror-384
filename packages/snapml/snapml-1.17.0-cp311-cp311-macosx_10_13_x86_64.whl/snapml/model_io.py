# *****************************************************************
#
# Licensed Materials - Property of IBM
#
# (C) Copyright IBM Corp. 2018, 2020. All Rights Reserved.
#
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
# *****************************************************************

from snapml.Model import Model

from snapml.BoostingMachine import BoostingMachine
from snapml.BoostingMachineRegressor import BoostingMachineRegressor
from snapml.BoostingMachineClassifier import BoostingMachineClassifier
from snapml.RandomForestRegressor import RandomForestRegressor
from snapml.RandomForestClassifier import RandomForestClassifier

from snapml._import import import_libsnapml

import os

libsnapml = import_libsnapml(False)


def import_model(
    input_file,
    input_type="pmml",
    tree_format="auto",
    X=None,
    remap_feature_indices=False,
    verbose=False,
):
    """
    Import a pre-trained tree ensemble model and optimize the trees for fast inference.

    This function will detect the ensemble type (e.g. boosting or forest) and task type
    (classification or regression) from the model file and return the correct Snap ML class.

    Currently only models stored as PMML are supported.

    Depending on how the tree_format argument is set, this function will return a different
    optimized model format. This format determines which inference engine is used for subsequent
    calls to 'predict' or 'predict_proba'.

    If tree_format is set to 'zdnn_tensors', the model will be optimized for execution on the IBM z16 AI accelerator,
    using a matrix-based inference algorithm leveraging the zDNN library.

    By default tree_format is set to 'auto'. A check is performed and if the IBM z16 AI accelerator is available the model
    will be optimized according to 'zdnn_tensors', otherwise it will be optimized according to 'compress_trees'. The selected
        optimized tree format can be read by parameter self.optimized_tree_format_.

    Information regarding the PMML input/output schema is stored in the `schema_` attribute of the model that is returned.

    Note: If the input file contains features that are not supported by the import function, then an exception is thrown
    indicating the feature and the line number within the input file containing the feature.

    Parameters
    ----------
    input_file : str
        Input filename

    input_type : {'pmml'}
        Input file type

    tree_format : {'auto', 'compress_trees', 'zdnn_tensors'}
        Tree format

    X : dense matrix (ndarray)
        Optional input dataset used for compressing trees

    remap_feature_indices : bool
        If enabled, predict and predict_proba functions will expect numpy arrays containing only the (ordered) features
        that are listed in the model file. This can often be a subset of the full set of feature that were provided during
        training. These features are stored in the `used_features_` attribute in the imported model.

    verbose : bool
        Print off information useful for debugging (e.g., whether the z16 AI accelerator was detected; how n_jobs gets set).

    Returns
    -------
    self : Snap ML object ready for scoring
    """

    if input_type != "pmml":
        raise ValueError(
            "Generic model import currently supports only 'pmml' as the input type. "
            + "Model-specific import functions (e.g., the import_model member function of BoostingMachineClassifer) support additional formats such as 'onnx', 'xgb_json' and 'lightgbm'."
        )

    model_ptr = Model()

    (
        task_type,
        model_type,
        classes,
        n_classes,
        used_features,
        schema,
    ) = libsnapml.generic_import(
        input_file, input_type, remap_feature_indices, model_ptr.get()
    )

    if classes is not None:
        ind2class = {}
        for i, c in enumerate(classes):
            ind2class[i] = c
    else:
        ind2class = None

    optimized_tree_format = None

    if model_type == "forest":
        out = (
            RandomForestClassifier()
            if task_type == "classification"
            else RandomForestRegressor()
        )
        out.used_features_ = used_features
        out.schema_ = schema
        out.model_ptr_ = model_ptr
        out.classes_ = classes
        out.n_classes_ = n_classes
        out.ind2class_ = ind2class
        out.optimize_trees(tree_format, X)
        optimized_tree_format = out.optimized_tree_format_
    else:
        out = (
            BoostingMachineClassifier()
            if task_type == "classification"
            else BoostingMachineRegressor()
        )
        out.used_features_ = used_features
        out.schema_ = schema
        out.booster_ = BoostingMachine(out.make_boosting_params())
        out.booster_.model_ptr_ = model_ptr
        out.booster_.classes_ = classes
        out.booster_.n_classes_ = n_classes
        out.booster_.ind2class_ = ind2class
        out.booster_.optimize_trees(tree_format, X)
        optimized_tree_format = out.booster_.optimized_tree_format_

    # detect and set n_jobs
    if optimized_tree_format == "zdnn_tensors":
        n_jobs = min(os.cpu_count(), 4)
        out.set_params(n_jobs=n_jobs)

    # print off information
    if verbose:
        n_jobs = out.n_jobs
        if optimized_tree_format == "compress_trees":
            print(">> Inference will run on CPU using %d threads." % (n_jobs))
        elif optimized_tree_format == "zdnn_tensors":
            print(
                ">> Inference will run on z16 integrated AI accelerator using %d CPU threads"
                % (n_jobs)
            )
        else:
            raise RuntimeError("Optimized tree format not detected")
        print(
            ">> To change the number of CPU threads to t call set_params(n_jobs=t) on the returned model object before calling predict or predict_proba."
        )

    return out
