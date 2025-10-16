# coding: utf-8

import os
from datetime import datetime

import fabio
import numpy

from tomoscan.esrf.volume.edfvolume import EDFVolume
from tomoscan.esrf.volume.mock import create_volume

_data = create_volume(
    frame_dims=(20, 20), z_size=11
)  # z_size need to be at least 10 to check loading from file name works
for i in range(len(_data)):
    _data[i] += 1


def test_edf_writer_header(tmp_path):
    """
    Test writing an edf volume from several EDFVolume and reading the entire volume back
    """
    acquisition_dir = tmp_path / "acquisition"
    os.makedirs(acquisition_dir)
    volume_dir = str(acquisition_dir / "volume")
    os.makedirs(volume_dir)

    sub_data = _data[:5]
    header = {"time": datetime.now().timestamp()}
    volume = EDFVolume(
        folder=volume_dir,
        data=sub_data,
        header=header,
    )
    volume.save()
    first_frame_path = os.path.join(volume_dir, "volume_000000.edf")
    assert os.path.exists(first_frame_path)
    assert "time" in fabio.open(first_frame_path).header

    # test get_slice function
    numpy.testing.assert_array_equal(
        volume.get_slice(index=2, axis=0),
        sub_data[2],
    )
    numpy.testing.assert_array_equal(
        volume.get_slice(index=2, axis=1),
        sub_data[:, 2, :],
    )
    numpy.testing.assert_array_equal(
        volume.get_slice(index=2, axis=2),
        sub_data[:, :, 2],
    )
    volume.data = None

    numpy.testing.assert_array_equal(
        volume.get_slice(index=2, axis=0),
        sub_data[2],
    )
    numpy.testing.assert_array_equal(
        volume.get_slice(index=2, axis=1),
        sub_data[:, 2, :],
    )
    numpy.testing.assert_array_equal(
        volume.get_slice(index=2, axis=2),
        sub_data[:, :, 2],
    )

    assert volume.get_min_max_values() == (_data.min(), _data.max())
    assert volume.data_extension == "edf"
    assert volume.metadata_extension == "txt"
