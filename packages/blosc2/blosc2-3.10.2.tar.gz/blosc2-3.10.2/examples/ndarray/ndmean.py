#######################################################################
# Copyright (c) 2019-present, Blosc Development Team <blosc@blosc.org>
# All rights reserved.
#
# This source code is licensed under a BSD-style license (found in the
# LICENSE file in the root directory of this source tree)
#######################################################################


import numpy as np

import blosc2

shape = (50, 50)
chunks = (49, 49)
dtype = np.float64
typesize = dtype.itemsize

# Create a NDArray from a NumPy array
random = np.random.default_rng()
array = random.normal(0, 1, np.prod(shape)).reshape(shape)
# Use NDMEAN filter
cparams = blosc2.CParams(filters=[blosc2.Filter.NDMEAN], filters_meta=[4])
a = blosc2.asarray(array, chunks=chunks, cparams=cparams)
print("compression ratio:", a.schunk.cratio)
