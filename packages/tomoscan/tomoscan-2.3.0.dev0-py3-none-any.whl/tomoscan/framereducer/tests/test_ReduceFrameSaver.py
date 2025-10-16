from __future__ import annotations

import os
import numpy
import h5py

from silx.io.url import DataUrl

from tomoscan.framereducer.ReduceFrameSaver import ReduceFrameSaver
from tomoscan.framereducer.reducedframesinfos import ReducedFramesInfos


def test_ReduceFrameSaver(tmp_path):
    """
    Make sure the API of 'ReducedFramesInfos' is accessible as a standalone
    """
    output_file = os.path.join(tmp_path, "output.hdf5")
    frames_metadata = ReducedFramesInfos()
    frames_metadata.machine_current = (12.3,)
    frames_metadata.count_time = (1.0,)

    ReduceFrameSaver(
        frames={
            0: numpy.ones((100, 100)),
        },
        output_urls=(
            DataUrl(
                file_path=output_file,
                data_path="entry0000/flats/{index}",
                scheme="silx",
            ),
        ),
        metadata_output_urls=(
            DataUrl(
                file_path=output_file,
                data_path="entry0000/flats/",
                scheme="silx",
            ),
        ),
        frames_metadata=frames_metadata,
    ).save()

    assert os.path.exists(output_file)
    with h5py.File(output_file, mode="r") as h5f:
        my_flat_dataset = h5f["entry0000/flats/0"]
        numpy.testing.assert_almost_equal(my_flat_dataset[:], numpy.ones((100, 100)))

        count_time = h5f["entry0000/flats/count_time"]
        numpy.testing.assert_almost_equal(
            count_time[:],
            numpy.array(
                [
                    1,
                ]
            ),
        )
        machine_current = h5f["entry0000/flats/machine_current"]
        numpy.testing.assert_almost_equal(
            machine_current[:],
            numpy.array(
                [
                    12.3,
                ]
            ),
        )
