#######################################################################
# Copyright (c) 2019-present, Blosc Development Team <blosc@blosc.org>
# All rights reserved.
#
# This source code is licensed under a BSD-style license (found in the
# LICENSE file in the root directory of this source tree)
#######################################################################

import numpy as np

import blosc2

nchunks = 10
# Set the compression and decompression parameters
cparams = blosc2.CParams(codec=blosc2.Codec.LZ4HC, typesize=4)
dparams = blosc2.DParams()
contiguous = True
urlpath = "filename"

storage = blosc2.Storage(contiguous=contiguous, urlpath=urlpath)
blosc2.remove_urlpath(urlpath)

# Create the SChunk
data = np.arange(200 * 1000 * nchunks)
schunk = blosc2.SChunk(
    chunksize=200 * 1000 * 4, data=data, cparams=cparams, dparams=dparams, storage=storage
)

cframe = schunk.to_cframe()

schunk2 = blosc2.schunk_from_cframe(cframe, False)
data2 = np.empty(data.shape, dtype=data.dtype)
schunk2.get_slice(out=data2)
assert np.array_equal(data, data2)

blosc2.remove_urlpath(urlpath)
