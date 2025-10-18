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

from copy import copy
from snapml._import import import_libsnapml
import sys

libsnapml = import_libsnapml(False)


class Model:
    def __init__(self):
        self.model_ptr = libsnapml.model_allocate()

    def get(self):
        return self.model_ptr

    def get_model(self):
        return libsnapml.model_get(self.model_ptr)

    def get_refcount(self):
        return sys.getrefcount(self) - 1
