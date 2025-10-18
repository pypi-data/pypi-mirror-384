# *****************************************************************
#
# Licensed Materials - Property of IBM
#
# (C) Copyright IBM Corp. 2017, 2020, 2021. All Rights Reserved.
#
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
# ******************************************************************

import numpy as np
import sys

from snapml._import import import_libsnapml

libsnapml = import_libsnapml(False)

from abc import ABC, abstractmethod

from snapml.CommonModel import CommonModel
from snapml.Model import Model


## @ingroup pythonclasses
class DecisionTree(CommonModel):
    @abstractmethod
    def __init__(self):
        # just for reference
        self.criterion = None
        self.splitter = None
        self.max_depth = None
        self.min_samples_leaf = None
        self.max_features = None
        self.random_state = None
        self.n_jobs = None
        self.use_histograms = None
        self.hist_nbins = None
        self.use_gpu = None
        self.gpu_id = None
        self.verbose = None
        self.task_type_ = None
        self.params = None
        self.n_features_in_ = None

    def __getstate__(self):
        attributes = self.__dict__.copy()
        if hasattr(self, "model_ptr_"):
            (
                attributes["model_"],
                attributes["model_size_"],
            ) = self.model_ptr_.get_model()
            del attributes["model_ptr_"]

        return attributes

    def __setstate__(self, d):
        # if the model was trained, let's rebuild the cache

        if "model_size_" in d.keys():
            # create model
            model_ptr_ = Model()
            libsnapml.model_put(d["model_"], d["model_size_"], model_ptr_.get())
            d["model_ptr_"] = model_ptr_
            del d["model_"]
            del d["model_size_"]

        self.__dict__ = d

    def check_gpu(self):
        pass

    def c_fit(
        self,
        max_depth,
        min_samples_leaf,
        max_features,
        random_state,
        num_ex,
        num_ft,
        indptr,
        indices,
        data,
        labs,
        num_classes,
        sample_weight,
    ):
        self.model_ptr_ = Model()

        # Run model training
        self.feature_importances_ = libsnapml.dtc_fit(
            self.task_type_,
            self.criterion,
            max_depth,
            min_samples_leaf,
            max_features,
            random_state,
            self.verbose,
            self.n_jobs,
            self.use_histograms,
            self.hist_nbins,
            self.use_gpu,
            self.gpu_id,
            num_ex,
            num_ft,
            num_classes,
            indptr,
            indices,
            data,
            labs,
            sample_weight,
            self.model_ptr_.get(),
        )

    def c_predict(
        self, num_ex, num_ft, indptr, indices, data, n_jobs, proba, num_classes
    ):

        # Generate predictions
        return libsnapml.dtc_predict(
            num_ex,
            num_ft,
            indptr,
            indices,
            data,
            n_jobs,
            proba,
            num_classes,
            self.model_ptr_.get(),
        )
