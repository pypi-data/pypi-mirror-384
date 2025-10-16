"""specific test for the jp2kvolume. the large part is in test_single_frame_volume as most of the processing is common"""

import os
import numpy
import pytest

from tomoscan.esrf.volume.jp2kvolume import JP2KVolume
from tomoscan.esrf.volume.mock import create_volume


@pytest.fixture
def raw_data(dtype: numpy.dtype):
    data = create_volume(
        frame_dims=(100, 100), z_size=11
    )  # z_size need to be at least 10 to check loading from file name works
    for i in range(len(data)):
        data[i] += 1
    return data.astype(dtype)


@pytest.mark.parametrize("dtype", (numpy.uint8, numpy.uint16))
def test_jp2kvolume_rescale(raw_data, dtype, tmp_path):
    """
    Test that rescale is correctly applied by default by the JP2KVolume
    """
    acquisition_dir = tmp_path / "acquisition"
    os.makedirs(acquisition_dir)
    volume_dir = str(acquisition_dir / "volume")
    os.makedirs(volume_dir)
    assert raw_data.dtype == dtype
    volume = JP2KVolume(folder=volume_dir, data=raw_data, metadata={})
    assert volume.data.dtype == dtype
    volume.save()

    volume.clear_cache()
    volume.load()
    assert volume.data.dtype == dtype
    assert volume.data.min() == 0
    assert volume.data.max() in (numpy.iinfo(dtype).max, numpy.iinfo(dtype).max - 1)
    assert volume.data_extension == "jp2"
    assert volume.metadata_extension == "txt"
