# coding: utf-8
"""
Test of the tiffmodule.
Note: some test are also perform on the test_single_frame_volume
"""


import os

import numpy
import pytest
from silx.io.url import DataUrl
from tifffile import TiffFile

from tomoscan.esrf.identifier.tiffidentifier import MultiTiffVolumeIdentifier
from tomoscan.esrf.volume.mock import create_volume
from tomoscan.esrf.volume.tiffvolume import MultiTIFFVolume, TIFFVolume
from tomoscan.identifier import VolumeIdentifier

_data = create_volume(frame_dims=(20, 20), z_size=5)
_data = _data.astype(numpy.uint8)

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


def test_multi_tiff_volume(tmp_path):
    test_dir = str(tmp_path / "test_volume_url")
    os.makedirs(test_dir)
    volume_file = os.path.join(test_dir, "volume.tiff")

    volume = MultiTIFFVolume(
        file_path=volume_file,
        data=_data,
        metadata=_metadata,
    )

    assert volume.url.file_path() == volume_file
    assert volume.url.data_path() is None
    assert volume.data_url.scheme() == "tifffile"
    assert volume.data_url.file_path() == volume_file
    assert volume.data_url.data_path() is None
    assert volume.metadata_url.scheme() == "ini"
    expected_metadata_file = os.path.join(test_dir, "volume_infos.txt")
    assert volume.metadata_url.file_path() == expected_metadata_file
    assert volume.metadata_url.data_path() is None

    volume_identifier = volume.get_identifier()
    assert isinstance(volume_identifier.short_description(), str)
    assert isinstance(volume_identifier, VolumeIdentifier)

    assert not os.path.exists(volume_file)
    assert tuple(volume.browse_data_files()) == tuple()
    assert tuple(volume.browse_data_urls()) == tuple()
    assert tuple(volume.browse_metadata_files()) == tuple()

    volume.save()
    assert os.path.exists(volume_file)
    assert tuple(volume.browse_metadata_files()) == (expected_metadata_file,)
    assert tuple(volume.browse_data_files()) == (volume_file,)
    assert len(list(volume.browse_data_urls())) == len((volume.data_url,))

    volume_loaded = MultiTIFFVolume(
        file_path=volume_file,
    )
    assert volume_loaded.metadata_url.file_path() == expected_metadata_file
    assert volume_loaded.metadata_url.data_path() is None

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
    assert volume.get_min_max_values() == (_data.min(), _data.max())

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

    # get the volume from the identifier
    volume_from_id = MultiTIFFVolume.from_identifier(identifier=volume_identifier)
    assert volume_from_id.data is None
    assert volume_from_id.metadata is None

    # get the volume from the identifier str
    volume_from_str = MultiTIFFVolume.from_identifier(
        identifier=MultiTiffVolumeIdentifier.from_str(volume_identifier.to_str())
    )
    assert volume_from_str.data is None
    assert volume_from_str.metadata is None
    assert volume_from_str.get_identifier() == volume_from_id.get_identifier()
    assert volume_from_str.get_identifier() != "toto"

    # test browsing frames
    for l_frame, o_frame in zip(volume_from_str.browse_slices(), _data):
        numpy.testing.assert_allclose(l_frame, o_frame)

    # test hash
    hash(volume_from_str)

    # test append param
    volume_file_append = os.path.join(test_dir, "volume_append.tiff")
    volume_append = MultiTIFFVolume(
        file_path=volume_file_append, data=_data, metadata=_metadata, append=True
    )
    volume_append.data = create_volume(frame_dims=(20, 20), z_size=2)
    volume_append.save()
    volume_append2 = MultiTIFFVolume(
        file_path=volume_file_append, data=_data, metadata=_metadata, append=True
    )
    volume_append2.data = create_volume(frame_dims=(20, 20), z_size=3) + 10
    volume_append2.save()
    tiff_append = TiffFile(volume_file_append)
    assert len(tiff_append.series) == 5

    # test load_chunk
    chunks_to_test = [
        (slice(None, None), slice(0, 5), slice(None, None)),
        (slice(0, 4), slice(0, 15), slice(None, None)),
    ]
    for chunk in chunks_to_test:
        data_chunk = volume.load_chunk(chunk)
        assert data_chunk.shape == _data[chunk].shape
        assert numpy.allclose(data_chunk, _data[chunk])
    assert volume.data_extension == "tiff"
    assert volume.metadata_extension == "txt"


def test_data_file_saver_generator(tmp_path):
    """
    data_file_saver_generator (dumping frame by frame a volume to disk)
    """
    volume_file_path = str(tmp_path / "volume.h5")
    volume = MultiTIFFVolume(file_path=volume_file_path)
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


def test_tiff_volume_nabu_single_frame_pattern(tmp_path):
    """
    Insure we can save and load using a specific pattermn (single frame volume) that can happen in nabu for example
    """
    test_dir = str(tmp_path / "test_volume_url")
    os.makedirs(test_dir)
    output_file = os.path.join(test_dir, "frame.tiff")

    class SingleFrameTIFFVolume(TIFFVolume):
        # we are not insure that the output directory name is the base name of the file_path
        DEFAULT_DATA_PATH_PATTERN = "frame.tiff"

    frame = _data[0].reshape(1, _data.shape[1], _data.shape[2])
    volume = SingleFrameTIFFVolume(
        folder=test_dir,
        data=frame,
        metadata=_metadata,
        overwrite=True,
    )
    volume.save()
    assert os.path.exists(output_file)

    volume_loaded_1 = SingleFrameTIFFVolume(
        folder=test_dir,
    )
    volume_loaded_1.load()
    numpy.testing.assert_array_equal(
        frame,
        volume_loaded_1.data,
    )

    volume_loaded_2 = TIFFVolume(
        data_url=DataUrl(
            file_path=output_file,
            data_path="frame.tiff",
            scheme="tifffile",
        ),
    )
    volume_loaded_2.load_data(store=True)
    numpy.testing.assert_array_equal(
        frame,
        volume_loaded_2.data,
    )

    # test get_slice function
    with pytest.raises(IndexError):
        numpy.testing.assert_array_equal(
            volume_loaded_2.get_slice(index=2, axis=0),
            _data[2],
        )
    numpy.testing.assert_array_equal(
        volume_loaded_2.get_slice(index=0, axis=0),
        _data[0],
    )
    numpy.testing.assert_array_equal(
        volume_loaded_2.get_slice(index=2, axis=1),
        frame[:, 2, :],
    )
    numpy.testing.assert_array_equal(
        volume_loaded_2.get_slice(index=2, axis=2),
        frame[:, :, 2],
    )
    volume_loaded_2.data = None

    numpy.testing.assert_array_equal(
        volume_loaded_2.get_slice(index=2, axis=1),
        frame[:, 2, :],
    )
    numpy.testing.assert_array_equal(
        volume_loaded_2.get_slice(index=2, axis=2),
        frame[:, :, 2],
    )


def test_tiff_volume_nabu_multi_frame_pattern(tmp_path):
    """
    Insure we can save and load using a specific pattermn (multi frame volume) that can happen in nabu for example
    """
    test_dir = str(tmp_path / "test_volume_url")
    os.makedirs(test_dir)

    class MultiFrameTIFFVolume(TIFFVolume):
        # we are not insure that the output directory name is the base name of the file_path
        DEFAULT_DATA_PATH_PATTERN = "frame_{index_zfill6}.tiff"

    volume = MultiFrameTIFFVolume(
        folder=test_dir,
        data=_data,
        metadata=_metadata,
        overwrite=True,
    )
    volume.save()
    output_file_first_frame = os.path.join(test_dir, "frame_000000.tiff")
    assert os.path.exists(output_file_first_frame)

    volume_loaded_1 = MultiFrameTIFFVolume(
        folder=test_dir,
    )
    volume_loaded_1.load()
    numpy.testing.assert_array_equal(
        _data,
        volume_loaded_1.data,
    )

    volume_loaded_2 = TIFFVolume(
        data_url=DataUrl(
            file_path=test_dir,
            data_path="frame_{index_zfill6}.tiff",
            scheme="tifffile",
        ),
    )
    volume_loaded_2.load_data(store=True)
    numpy.testing.assert_array_equal(
        _data,
        volume_loaded_2.data,
    )

    # test get_slice function
    numpy.testing.assert_array_equal(
        volume_loaded_2.get_slice(index=2, axis=0),
        _data[2],
    )
    numpy.testing.assert_array_equal(
        volume_loaded_2.get_slice(index=2, axis=1),
        _data[:, 2, :],
    )
    numpy.testing.assert_array_equal(
        volume_loaded_2.get_slice(index=2, axis=2),
        _data[:, :, 2],
    )
    volume_loaded_2.data = None

    numpy.testing.assert_array_equal(
        volume_loaded_2.get_slice(index=2, axis=0),
        _data[2],
    )
    numpy.testing.assert_array_equal(
        volume_loaded_2.get_slice(index=2, axis=1),
        _data[:, 2, :],
    )
    numpy.testing.assert_array_equal(
        volume_loaded_2.get_slice(index=2, axis=2),
        _data[:, :, 2],
    )


def test_example():
    """test static function 'example'"""
    assert isinstance(MultiTIFFVolume.example_defined_from_str_identifier(), str)
