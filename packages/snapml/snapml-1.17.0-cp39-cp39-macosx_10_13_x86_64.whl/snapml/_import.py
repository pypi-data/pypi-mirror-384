# *****************************************************************
#
# Licensed Materials - Property of IBM
#
# (C) Copyright IBM Corp. 2021. All Rights Reserved.
#
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
# ******************************************************************
from importlib import import_module
import warnings
import os
from ctypes import CDLL
import platform
from ctypes.util import find_library

try:
    from numpy.core._multiarray_umath import __cpu_features__ as cpu_features
except:
    warnings.warn(
        "Cannot detect CPU features info from numpy; AVX2 will not be used.",
        category=UserWarning,
    )
    cpu_features = None


def import_libutils():
    if cpu_features is not None and cpu_features["AVX2"]:
        return import_module("snapml.libsnapmlutils_avx2")
    else:
        return import_module("snapml.libsnapmlutils")


def import_libsnapml(mpi_enabled=False):

    is_s390x = platform.machine() == "s390x"

    if is_s390x:
        # Allow overriding the lib path via env if needed
        lib_override = os.getenv("SNAPML_ZDNN_LIB")
        libname = lib_override or find_library("zdnn") or "libzdnn.so"
        try:
            CDLL(libname)
        except OSError as e:
            warnings.warn(
                f"libzdnn not found ('{libname}'); falling back to "
                f"'snapml.libsnapmllocal3' (CPU-only). Warning: {e}",
                RuntimeWarning,
            )
            return import_module("snapml.libsnapmllocal3")

    if cpu_features is not None and cpu_features["AVX2"]:
        if mpi_enabled:
            return import_module("snapml.libsnapmlmpi3_avx2")
        else:
            return import_module("snapml.libsnapmllocal3_avx2")
    else:
        if mpi_enabled:
            return import_module("snapml.libsnapmlmpi3")
        else:
            return import_module("snapml.libsnapmllocal3")
