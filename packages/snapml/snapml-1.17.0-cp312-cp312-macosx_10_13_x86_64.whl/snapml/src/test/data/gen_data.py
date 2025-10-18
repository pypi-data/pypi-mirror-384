# *********************************************************************
# * Copyright
# *
# * IBM Confidential
# * (C) COPYRIGHT IBM CORP. 2018
# * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
# * All rights reserved.
# *
# * This software contains the valuable trade secrets of IBM or its
# * licensors.  The software is protected under international copyright
# * laws and treaties.  This software may only be used in accordance with
# * the terms of its accompanying license agreement.
# *
# * Authors      : Thomas Parnell
# *                Celestine Duenner
# *                Dimitrios Sarigiannis
# *                Andreea Anghel
# *
# * End Copyright
# ********************************************************************/

import numpy as np
from scipy import sparse
from sklearn.datasets import dump_svmlight_file
from scipy import stats

num_ex = 64
num_ft = 128
density = 0.1

X = sparse.random(
    num_ex, num_ft, density, format="csr", data_rvs=stats.uniform(1, 0).rvs
)
y = 2 * np.random.randint(2, size=num_ex) - 1

print X[0]

from sklearn.preprocessing import normalize

X_norm = normalize(X, norm="l2", axis=1)

print X_norm[0]

with open("small.libsvm", "w") as f:
    dump_svmlight_file(X_norm, y, f, zero_based=False)
