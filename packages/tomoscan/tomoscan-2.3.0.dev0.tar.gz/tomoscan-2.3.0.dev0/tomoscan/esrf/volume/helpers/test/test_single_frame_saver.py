import os
import pytest
import numpy
from tomoscan.esrf.volume.helpers.single_frame_saver import SingleFrameSaverHelper
from tomoscan.esrf.volume.edfvolume import EDFVolume
from tomoscan.esrf.volume.jp2kvolume import JP2KVolume, has_glymur, has_minimal_openjpeg
from tomoscan.esrf.volume.tiffvolume import TIFFVolume, has_tifffile
from tomoscan.esrf.volume.mock import create_volume


volume_constructors = [
    EDFVolume,
]
if has_tifffile:
    volume_constructors.append(TIFFVolume)
if has_glymur and has_minimal_openjpeg:
    volume_constructors.append(JP2KVolume)


@pytest.mark.parametrize("cache_size", (None, 16, 256, 4096, 65536, numpy.inf))
@pytest.mark.parametrize("dtype", (numpy.uint8, numpy.uint16, numpy.float128))
@pytest.mark.parametrize("axis", (0, 1, 2))
@pytest.mark.parametrize("volume_constructor", volume_constructors)
def test_SingleFrameSaverHelper(tmp_path, axis, dtype, volume_constructor, cache_size):
    """Test SingleFrameSaverHelper along all the axis and with all kind of 'single frame' volume"""

    data = create_volume(frame_dims=(100, 100), z_size=100)
    # rescale data. Because for example jp2k is rescaling it by default
    if dtype is numpy.float128:
        max_val = numpy.finfo(dtype).max
    else:
        max_val = numpy.iinfo(dtype).max
    data = data / data.max() * max_val
    data = data.astype(dtype)

    output_folder = os.path.join(tmp_path, volume_constructor.DEFAULT_DATA_EXTENSION)
    volume = volume_constructor(
        folder=output_folder,
    )

    data_saver_helper = SingleFrameSaverHelper(
        volume=volume,
        data_shape=(100, 100, 100),
        dtype=dtype,
        cache_size=cache_size,
    )
    data_saver_helper.init_saver()

    for i in range(100):
        if axis == 0:
            data_saver_helper[i] = data[i]
        elif axis == 1:
            data_saver_helper[:, i] = data[:, i]
        elif axis == 2:
            data_saver_helper[:, :, i] = data[:, :, i]

    # note: saving is done directly on the file. So this will not affect the volume.data
    # except if loaded and stored
    volume_data = volume.load_data(store=False)

    assert data.shape == volume_data.shape
    assert data.dtype == volume_data.dtype

    numpy.testing.assert_array_equal(
        data,
        volume_data,
    )
