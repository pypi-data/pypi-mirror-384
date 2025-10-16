# coding: utf-8


import os

import h5py
import numpy
import pytest
from silx.io.url import DataUrl

from tomoscan.esrf.identifier.hdf5Identifier import HDF5VolumeIdentifier
from tomoscan.esrf.scan.mock import MockNXtomo as _MockNXtomo
from tomoscan.esrf.volume.hdf5volume import HDF5Volume, get_default_data_path_for_volume
from tomoscan.esrf.volume.mock import create_volume
from tomoscan.identifier import VolumeIdentifier

_data = create_volume(frame_dims=(20, 20), z_size=5)


_metadata = {
    "nabu_config": {
        "dataset": {
            "location": "toto.hdf5",
            "entry": "entry0000",
        },
        "phase": {
            "method": "None",
            "padding_type": "edge",
        },
    },
    "processing_option": {
        "build_sino": {
            "axis_correction": "None",
            "enable_halftomo": True,
        },
        "flatfield": {
            "binning": "11",
            "do_flat_distortion": False,
        },
    },
}


def test_hdf5volume_file_path(tmp_path):
    """test creation of an hdf5volume by providing url to the constructor"""
    test_dir = tmp_path / "test_volume_url"
    os.makedirs(test_dir)

    volume_file = os.path.join(test_dir, "volume.hdf5")
    assert not os.path.exists(volume_file)

    volume = HDF5Volume(
        file_path=volume_file,
        data_path="/entry0000/reconstruction",
        data=_data,
        metadata=_metadata,
    )
    assert volume.get_min_max_values() == (_data.min(), _data.max())

    url = DataUrl(file_path=volume_file, data_path="/entry0000/reconstruction")
    assert volume.url.file_path() == url.file_path()
    assert volume.url.data_path() == url.data_path()
    assert volume.data_url is not None
    assert volume.metadata_url is not None
    volume_identifier = volume.get_identifier()
    assert isinstance(volume_identifier, VolumeIdentifier)

    # insure data_url and metadata_url cannot be write
    with pytest.raises(AttributeError):
        volume.data_url = None

    with pytest.raises(AttributeError):
        volume.metadata_url = None

    volume.save()
    assert os.path.exists(volume_file)

    volume_loaded = HDF5Volume(
        file_path=volume_file, data_path="/entry0000/reconstruction"
    )
    assert volume_loaded._data is None
    assert volume_loaded._metadata is None
    # check loading function won't save loaded data in cache
    data_no_cache = volume_loaded.load_data(volume_loaded.data_url, store=False)
    metadata_no_cache = volume_loaded.load_metadata(
        volume_loaded.metadata_url, store=False
    )
    assert data_no_cache is not None
    assert metadata_no_cache is not None
    assert volume_loaded._data is None
    assert volume_loaded._metadata is None
    numpy.testing.assert_array_almost_equal(_data, data_no_cache)
    assert _metadata == metadata_no_cache
    # check data and metadata properties will load and set data in cache
    volume_loaded.load()
    data_cache = volume_loaded.data
    assert data_cache is not None
    metadata_cache = volume_loaded.metadata
    assert metadata_cache is not None
    numpy.testing.assert_array_almost_equal(_data, data_cache)
    assert _metadata == metadata_cache
    volume_loaded.data = None
    volume_loaded.metadata = None
    with pytest.raises(ValueError):
        volume_loaded.save_data()

    with pytest.raises(ValueError):
        volume_loaded.save_metadata()

    with pytest.raises(TypeError):
        volume_loaded.data = "toto"

    volume_loaded.data = create_volume(frame_dims=(20, 20), z_size=2)
    with pytest.raises(ValueError):
        volume_loaded.data = create_volume(frame_dims=(20, 20), z_size=2)[0]

    other_hdf5_file = os.path.join(test_dir, "other_hdf5_file.h5")
    new_volume_url = DataUrl(file_path=other_hdf5_file, data_path="data", scheme="silx")
    volume_loaded.save_data(url=new_volume_url)
    with pytest.raises(OSError):
        volume_loaded.save_data(
            url=DataUrl(file_path=other_hdf5_file, data_path="data", scheme="silx")
        )
    volume_loaded.overwrite = True
    volume_loaded.save_data(url=DataUrl(file_path=other_hdf5_file, data_path="data"))

    assert isinstance(volume_loaded.data, numpy.ndarray)
    assert isinstance(volume_loaded.load_data(url=new_volume_url), numpy.ndarray)
    numpy.testing.assert_array_almost_equal(
        volume_loaded.load_data(url=new_volume_url), volume_loaded.data
    )

    new_metadata_url = DataUrl(
        file_path=other_hdf5_file, data_path="metadata", scheme="silx"
    )
    with pytest.raises(ValueError):
        volume_loaded.save_metadata(url=new_metadata_url)

    volume_loaded.metadata = {"meta": False}
    volume_loaded.save_metadata(url=new_metadata_url)
    assert volume_loaded.load_metadata(url=new_metadata_url) == {"meta": False}

    # get the volume from the identifier
    volume_from_id = HDF5Volume.from_identifier(identifier=volume_identifier)
    assert volume_from_id.data is None
    assert volume_from_id.metadata is None

    # get the volume from the identifier str
    volume_from_str = HDF5Volume.from_identifier(
        identifier=HDF5VolumeIdentifier.from_str(volume_identifier.to_str())
    )
    assert volume_from_str.data is None
    assert volume_from_str.metadata is None

    # test browsing frames
    for l_frame, o_frame in zip(volume.browse_slices(), _data):
        numpy.testing.assert_allclose(l_frame, o_frame)

    # test hash
    hash(volume_from_str)

    # test get_min_max values
    assert volume_from_str.get_min_max() == (_data.min(), _data.max())
    volume_from_str.load_data()
    assert volume_from_str.get_min_max() == (_data.min(), _data.max())
    assert volume.data_extension == "hdf5"
    assert volume.metadata_extension == "hdf5"


def test_hdf5volume_data_url_and_metadata_url(tmp_path):
    """test creation of an hdf5volume by providing a data url and a metadata url"""
    test_dir = tmp_path / "test_volume_data_url_metadata_url"
    os.makedirs(test_dir)

    hdf5_data_file = os.path.join(test_dir, "my_data_file.hdf5")
    hdf5_metadata_file = os.path.join(test_dir, "my_metadata_file.hdf5")
    data_url = DataUrl(
        file_path=hdf5_data_file,
        data_path="data",
        scheme="silx",
    )
    metadata_url = DataUrl(
        file_path=hdf5_metadata_file,
        data_path="metadata",
        scheme="silx",
    )
    volume = HDF5Volume(
        data_url=data_url, metadata_url=metadata_url, data=_data, metadata=_metadata
    )

    with pytest.raises(ValueError):
        assert volume.get_identifier()

    assert tuple(volume.browse_data_files()) == tuple()
    assert tuple(volume.browse_data_urls()) == tuple()
    assert tuple(volume.browse_metadata_files()) == tuple()
    assert not os.path.exists(hdf5_data_file)
    volume.save_data()
    assert os.path.exists(hdf5_data_file)
    assert not os.path.exists(hdf5_metadata_file)
    volume.save_metadata()
    assert os.path.exists(hdf5_metadata_file)

    volume_loaded = HDF5Volume(data_url=data_url, metadata_url=metadata_url)
    assert volume_loaded.metadata is None
    volume_loaded.load_metadata()
    assert volume_loaded.metadata is not None
    assert volume_loaded.data is None

    # test get_slice
    numpy.testing.assert_array_equal(
        volume_loaded.get_slice(index=2, axis=0), _data[2, :, :]
    )
    numpy.testing.assert_array_equal(
        volume_loaded.get_slice(index=2, axis=1), _data[:, 2, :]
    )
    numpy.testing.assert_array_equal(
        volume_loaded.get_slice(index=2, axis=2), _data[:, :, 2]
    )

    # test old API (deprecated)
    numpy.testing.assert_array_equal(
        volume_loaded.get_slice(index=2, axis=0), volume_loaded.get_slice(xy=2)
    )
    numpy.testing.assert_array_equal(
        volume_loaded.get_slice(index=2, axis=1), volume_loaded.get_slice(xz=2)
    )
    numpy.testing.assert_array_equal(
        volume_loaded.get_slice(index=2, axis=2), volume_loaded.get_slice(yz=2)
    )

    volume_loaded.load_data()
    assert volume_loaded.data is not None

    # test get_slice
    numpy.testing.assert_array_equal(
        volume_loaded.get_slice(index=2, axis=0), _data[2, :, :]
    )
    numpy.testing.assert_array_equal(
        volume_loaded.get_slice(index=2, axis=1), _data[:, 2, :]
    )
    numpy.testing.assert_array_equal(
        volume_loaded.get_slice(index=2, axis=2), _data[:, :, 2]
    )

    numpy.testing.assert_array_equal(
        volume_loaded.data,
        _data,
    )

    assert tuple(volume_loaded.browse_data_files()) == (hdf5_data_file,)
    assert tuple(volume_loaded.browse_data_urls()) == (volume_loaded.data_url,)
    assert tuple(volume_loaded.browse_metadata_files()) == (hdf5_metadata_file,)

    # test load_chunk
    chunks_to_test = [
        (slice(None, None), slice(0, 5), slice(None, None)),
        (slice(0, 4), slice(0, 15), slice(None, None)),
    ]
    for chunk in chunks_to_test:
        data_chunk = volume.load_chunk(chunk)
        assert data_chunk.shape == _data[chunk].shape
        assert numpy.allclose(data_chunk, _data[chunk])


def test_write_hdf5_volume_with_parameter(tmp_path):
    test_dir = tmp_path / "test_volume_data_url_metadata_url"
    os.makedirs(test_dir)

    hdf5_data_file = os.path.join(test_dir, "my_data_file.hdf5")
    hdf5_metadata_file = os.path.join(test_dir, "my_metadata_file.hdf5")
    data_url = DataUrl(
        file_path=hdf5_data_file,
        data_path="data",
        scheme="silx",
    )
    metadata_url = DataUrl(
        file_path=hdf5_metadata_file,
        data_path="metadata",
        scheme="silx",
    )
    volume = HDF5Volume(
        data_url=data_url,
        metadata_url=metadata_url,
        data=_data,
        metadata=_metadata,
        overwrite=True,
    )

    # check chunks
    volume.save(chunks=True)
    with h5py.File(hdf5_data_file, mode="r") as h5f:
        assert h5f["data"].chunks is not None

    # check compression
    volume.save(compression="gzip", compression_opts=9)
    with h5py.File(hdf5_data_file, mode="r") as h5f:
        assert h5f["data"].compression == "gzip"


def test_data_file_saver_generator(tmp_path):
    """
    data_file_saver_generator (dumping frame by frame a volume to disk)
    """
    volume_file_path = str(tmp_path / "volume.h5")
    volume = HDF5Volume(file_path=volume_file_path, data_path="volume")
    for slice_, slice_saver in zip(
        _data,
        volume.data_file_saver_generator(
            n_frames=_data.shape[0], data_url=volume.data_url, overwrite=False
        ),
    ):
        slice_saver[:] = slice_
    assert volume.data is None
    numpy.testing.assert_array_equal(
        volume.load_data(),
        _data,
    )


def test_write_hdf5_with_virtual_layout_as_data(tmp_path):
    """
    insure HDF5Volume.data is safely handling virtual layout
    """
    test_dir = tmp_path / "test_volume_data_url_metadata_url"
    os.makedirs(test_dir)

    n_file = 5
    virtual_layout = h5py.VirtualLayout(shape=(n_file * 10, 100, 100), dtype=float)
    # create raw data
    for i_file in range(n_file):
        file_path = os.path.join(test_dir, f"file{i_file}.hdf5")
        data_path = f"path_to_dataset_{i_file}"
        with h5py.File(file_path, mode="w") as h5f:
            data = numpy.arange(0, 10 * 100 * 100).reshape(10, 100, 100)
            h5f[data_path] = data
            vs = h5py.VirtualSource(h5f[data_path])
            virtual_layout[i_file * 10 : (i_file + 1) * 10] = vs

    hdf5_data_file = os.path.join(test_dir, "my_data_file.hdf5")

    volume = HDF5Volume(
        file_path=hdf5_data_file,
        data_path="/",
        data=virtual_layout,
        metadata=_metadata,
        overwrite=True,
    )

    volume.save()
    with h5py.File(hdf5_data_file, mode="r") as h5f:
        assert h5f["results/data"].is_virtual
        numpy.testing.assert_array_equal(
            h5f["results/data"][:10],
            numpy.arange(0, 10 * 100 * 100).reshape(10, 100, 100),
        )
    volume.data = None
    assert volume.get_volume_shape() == (n_file * 10, 100, 100)


def test_utils(tmp_path):
    """test utils functions of the hdf5volume module"""

    test_dir = str(tmp_path / "test_volume_url")
    os.makedirs(test_dir)

    mock_scan = _MockNXtomo(
        scan_path=test_dir,
        dim=20,
        n_proj=12,
    )
    scan = mock_scan.scan

    assert isinstance(get_default_data_path_for_volume(scan), str)
    with pytest.raises(TypeError):
        get_default_data_path_for_volume("toto")


def test_example():
    """test static function 'example'"""
    assert isinstance(HDF5Volume.example_defined_from_str_identifier(), str)


@pytest.mark.parametrize("save_volume_to_file", (True, False))
def test_get_slices(tmp_path, save_volume_to_file: bool):
    """test the volume 'get_slices' function"""
    test_dir = tmp_path / "test_get_slices"
    test_dir.mkdir()

    volume_file = os.path.join(test_dir, "volume.hdf5")
    assert not os.path.exists(volume_file)
    data = numpy.linspace(0, 1000, num=1000, endpoint=False).reshape(10, 10, 10)

    volume = HDF5Volume(
        file_path=volume_file,
        data_path="/entry0000/reconstruction",
        data=data,
        metadata=_metadata,
    )
    if save_volume_to_file:
        volume.save_data()
        volume.clear_cache()

    slices_axis_0 = volume.get_slices(((0, 2), (0, 5)))
    numpy.testing.assert_array_almost_equal(
        slices_axis_0[(0, 2)],
        data[2],
    )

    slices_axis_1 = volume.get_slices(((1, 0), (1, 6)))
    numpy.testing.assert_array_almost_equal(
        slices_axis_1[(1, 6)],
        data[:, 6, :],
    )
    assert isinstance(slices_axis_1[(1, 6)], numpy.ndarray)

    slices_axis_2 = volume.get_slices(((2, 8), (2, 9)))
    numpy.testing.assert_array_almost_equal(
        slices_axis_2[(2, 9)],
        data[:, :, 9],
    )

    with pytest.raises(TypeError):
        volume.get_slices(
            "toto",
        )

    with pytest.raises(TypeError):
        volume.get_slices(
            (0, 10),
        )
