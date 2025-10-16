import os
import h5py
import numpy

from tomoscan.io import check_virtual_sources_exist, cast_to_default_types


def test_vds(tmp_path):
    h5_file_without_vds = os.path.join(tmp_path, "h5_file_without_vds.hdf5")

    with h5py.File(h5_file_without_vds, mode="w") as h5f:
        h5f["data"] = numpy.random.random((120, 120))
    assert check_virtual_sources_exist(h5_file_without_vds, "data")

    h5_file_with_vds = os.path.join(tmp_path, "h5_file_with_vds.hdf5")

    # create some dataset
    for i in range(4):
        filename = os.path.join(tmp_path, f"{i}.h5")
        with h5py.File(filename, mode="w") as h5f:
            h5f.create_dataset("data", (100,), "i4", numpy.arange(100))

    layout = h5py.VirtualLayout(shape=(4, 100), dtype="i4")
    for i in range(4):
        filename = os.path.join(tmp_path, f"{i}.h5")
        layout[i] = h5py.VirtualSource(filename, "data", shape=(100,))

    with h5py.File(h5_file_with_vds, mode="w") as h5f:
        # create the virtual dataset
        h5f.create_virtual_dataset("data", layout, fillvalue=-5)
    assert check_virtual_sources_exist(h5_file_with_vds, "data")


def test_cast_to_default_types():
    """test 'cast_to_default_types' function"""
    assert cast_to_default_types(
        {
            "a": numpy.float64(25.6),
            "b": {
                "c": numpy.zeros(5, dtype=numpy.int32),
                "d": numpy.ones(4, dtype=numpy.uint64),
            },
            "e": (numpy.float32(45.5), numpy.float32(5.5)),
            "f": numpy.int16(5),
        }
    ) == {
        "a": 25.6,
        "b": {
            "c": [0] * 5,
            "d": [1] * 4,
        },
        "e": [45.5, 5.5],
        "f": 5,
    }
