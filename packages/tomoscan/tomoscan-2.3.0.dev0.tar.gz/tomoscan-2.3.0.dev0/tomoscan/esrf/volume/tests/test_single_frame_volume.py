# coding: utf-8

import os
from glob import glob

import numpy
import pytest

from tomoscan.esrf.identifier.folderidentifier import BaseFolderIdentifierMixIn
from tomoscan.esrf.volume.edfvolume import EDFVolume
from tomoscan.esrf.volume.jp2kvolume import JP2KVolume, has_glymur, has_minimal_openjpeg
from tomoscan.esrf.volume.mock import create_volume
from tomoscan.esrf.volume.tiffvolume import TIFFVolume, has_tifffile
from tomoscan.factory import Factory
from tomoscan.identifier import VolumeIdentifier
from tomoscan.volumebase import VolumeBase

_data = create_volume(
    frame_dims=(100, 100), z_size=11
)  # z_size need to be at least 10 to check loading from file name works
for i in range(len(_data)):
    _data[i] += 1
_data = _data.astype(numpy.uint16)


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


volume_constructors = [
    EDFVolume,
]
if has_tifffile:
    volume_constructors.append(TIFFVolume)
if has_glymur and has_minimal_openjpeg:
    volume_constructors.append(JP2KVolume)


@pytest.mark.parametrize("volume_constructor", volume_constructors)
def test_create_volume_from_folder(tmp_path, volume_constructor):
    """Test a volume can be weel defined from it path"""
    acquisition_dir = tmp_path / "acquisition"
    os.makedirs(acquisition_dir)
    volume_dir = str(acquisition_dir / "volume")
    os.makedirs(volume_dir)
    volume = volume_constructor(folder=volume_dir, data=_data, metadata=_metadata)
    assert (
        len(
            glob(
                os.path.join(
                    volume_dir, f"*.{volume_constructor.DEFAULT_DATA_EXTENSION}"
                )
            )
        )
        == 0
    )
    assert (
        len(
            glob(
                os.path.join(
                    volume_dir, f"*.{volume_constructor.DEFAULT_METADATA_EXTENSION}"
                )
            )
        )
        == 0
    )
    assert tuple(volume.browse_data_files()) == tuple()
    assert tuple(volume.browse_data_urls()) == tuple()
    assert tuple(volume.browse_metadata_files()) == tuple()
    volume.save()
    assert (
        len(
            glob(
                os.path.join(
                    volume_dir, f"*.{volume_constructor.DEFAULT_DATA_EXTENSION}"
                )
            )
        )
        == _data.shape[0]
    )
    assert (
        len(
            glob(
                os.path.join(
                    volume_dir, f"*.{volume_constructor.DEFAULT_METADATA_EXTENSION}"
                )
            )
        )
        == 1
    )

    # check overwrite parameter
    volume.data = numpy.random.random((45, 45, 45))
    with pytest.raises(OSError):
        volume.save()

    volume.overwrite = True
    if isinstance(volume, JP2KVolume):
        volume.rescale_data = False
    volume.save()
    assert volume.get_volume_shape() == (45, 45, 45)
    volume.data = _data
    volume.save()

    # check load data and metadata
    volume.clear_cache()
    assert volume.get_min_max_values() == (_data.min(), _data.max())
    volume.load()
    numpy.testing.assert_array_almost_equal(_data, volume.data)
    assert _metadata == volume.metadata

    # test get_slice function
    numpy.testing.assert_array_equal(
        volume.get_slice(index=2, axis=0),
        _data[2],
    )
    numpy.testing.assert_array_equal(
        volume.get_slice(index=2, axis=1),
        _data[:, 2, :],
    )
    numpy.testing.assert_array_equal(
        volume.get_slice(index=2, axis=2),
        _data[:, :, 2],
    )
    # test deprecated API
    numpy.testing.assert_array_equal(
        volume.get_slice(index=2, axis=0),
        volume.get_slice(xy=2),
    )
    numpy.testing.assert_array_equal(
        volume.get_slice(index=2, axis=1),
        volume.get_slice(xz=2),
    )
    numpy.testing.assert_array_equal(
        volume.get_slice(index=2, axis=2),
        volume.get_slice(yz=2),
    )

    assert len(list(volume.browse_data_files())) == _data.shape[0]
    assert len(list(volume.browse_data_urls())) == _data.shape[0]
    assert len(list(volume.browse_metadata_files())) == 1

    # test browsing frames
    for l_frame, o_frame in zip(volume.browse_slices(), _data):
        numpy.testing.assert_allclose(l_frame, o_frame)

    # test get_min_max values
    volume.data = None
    assert volume.get_min_max() == (_data.min(), _data.max())
    volume.load_data()
    assert volume.get_min_max() == (_data.min(), _data.max())

    if isinstance(volume, JP2KVolume):
        volume.data_extension == "jp2k"
    elif isinstance(volume, EDFVolume):
        volume.data_extension == "edf"
    elif isinstance(volume, TIFFVolume):
        volume.data_extension == "tiff"
    else:
        raise NotImplementedError
    assert volume.metadata_extension == "txt"


@pytest.mark.parametrize("volume_constructor", volume_constructors)
def test_get_start_index(tmp_path, volume_constructor):
    """Test setting start_index parameter"""
    acquisition_dir = tmp_path / "acquisition"
    os.makedirs(acquisition_dir)
    volume_dir = str(acquisition_dir / "volume")
    os.makedirs(volume_dir)

    # use data which has a different value for each frame
    data = _data.copy()
    data += numpy.arange(data.shape[0], dtype=_data.dtype).reshape((-1, 1, 1))
    #

    start_index_list = [0, 7]  # one default and one non-default
    for start_index in start_index_list:
        volume_basename = f"test_startindex{start_index}"

        volume = volume_constructor(
            folder=volume_dir, volume_basename=volume_basename, start_index=start_index
        )
        assert volume.get_first_file() is None
        volume.data = _data
        volume.save()

        expected_first_file_name = os.path.join(
            volume_dir,
            "%s_%06d.%s"
            % (volume_basename, start_index, volume_constructor.DEFAULT_DATA_EXTENSION),
        )
        assert volume.get_first_file() == expected_first_file_name
        assert volume.get_file_slice_index(volume.get_first_file()) == start_index

        # Now create another XXVolume object using the same basename, while there are existing files
        volume2 = volume_constructor(
            folder=volume_dir, volume_basename=volume_basename, start_index=start_index
        )
        assert volume2.get_first_file() == expected_first_file_name
        assert (
            volume2.get_file_slice_index(volume.get_first_file()) == start_index
        )  # This used to be False before this patch


@pytest.mark.parametrize("volume_constructor", volume_constructors)
def test_reset_slice_index(tmp_path, volume_constructor):
    """
    Test a case that might happen during volume casting: existing files have start_index > 0,
    so we should re-define start_index for the new Volume object before writing
    """
    acquisition_dir = tmp_path / "acquisition"
    os.makedirs(acquisition_dir)
    volume_dir = str(acquisition_dir / "volume")
    os.makedirs(volume_dir)
    volume_dir2 = str(acquisition_dir / "volume2")
    os.makedirs(volume_dir2)

    # use data which has a different value for each frame
    data = _data.copy()
    data += numpy.arange(data.shape[0], dtype=_data.dtype).reshape((-1, 1, 1))
    #

    # Step 1: a Volume is created during reconstruction, with start_z > 0
    volume = volume_constructor(
        folder=volume_dir, volume_basename="test_reset_slice_index", start_index=500
    )
    if isinstance(volume, JP2KVolume):
        volume.rescale_data = False
    volume.data = data
    volume.save()

    # Step 2: after reconstruction, volume casting is triggered.
    # The "input_volume" object has to detect the actual start_index
    input_volume = volume_constructor(
        folder=volume_dir, volume_basename="test_reset_slice_index"
    )
    output_volume = volume_constructor(
        folder=volume_dir2, volume_basename="test_reset_slice_index"
    )
    if isinstance(output_volume, JP2KVolume):
        output_volume.rescale_data = False
    input_vol_start_idx = input_volume.get_file_slice_index(
        input_volume.get_first_file()
    )
    assert input_vol_start_idx == 500
    output_volume.start_index = input_vol_start_idx
    output_volume.data = data + 10
    output_volume.save()

    # Check !
    vol_check = volume_constructor(
        folder=volume_dir2, volume_basename="test_reset_slice_index", start_index=500
    )
    assert numpy.allclose(vol_check.load_data(), volume.load_data() + 10)


@pytest.mark.parametrize("volume_constructor", volume_constructors)
def test_data_file_saver_generator(tmp_path, volume_constructor):
    """
    data_file_saver_generator (dumping frame by frame a volume to disk)
    """
    volume_dir = str(tmp_path / "volume")
    os.makedirs(volume_dir)
    volume = volume_constructor(folder=volume_dir)
    if isinstance(volume, JP2KVolume):
        volume.rescale_data = False
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


@pytest.mark.parametrize("volume_constructor", volume_constructors)
def test_several_writer(tmp_path, volume_constructor):
    """
    Test writing a volume from several instance of VolumeSingleFrameBase and reading the entire volume back
    """
    acquisition_dir = tmp_path / "acquisition"
    os.makedirs(acquisition_dir)
    volume_dir = acquisition_dir / "volume"
    os.makedirs(volume_dir)

    volume_1 = volume_constructor(
        folder=volume_dir,
        data=_data[:5],
        metadata=_metadata,
    )
    volume_2 = volume_constructor(folder=volume_dir, data=_data[5:], start_index=5)
    if isinstance(volume_1, JP2KVolume):
        volume_1.rescale_data = (
            False  # keep coherence between all the volumes. Simplify test
        )
        volume_2.rescale_data = False
    volume_1.save()
    volume_2.skip_existing_data_files_removal = True
    volume_2.save()

    full_volume = volume_constructor(folder=volume_dir)
    full_volume.load()
    numpy.testing.assert_array_almost_equal(full_volume.data, _data)
    assert full_volume.metadata == _metadata
    full_volume.data = None
    assert full_volume.get_volume_shape() == _data.shape


@pytest.mark.parametrize("volume_constructor", volume_constructors)
def test_volume_identifier(tmp_path, volume_constructor):
    """
    Insure each type of volume can provide an identifier and recover the data store from it
    """
    acquisition_dir = tmp_path / "acquisition"
    os.makedirs(acquisition_dir)
    volume_dir = acquisition_dir / "volume"
    os.makedirs(volume_dir)

    volume = volume_constructor(
        folder=volume_dir,
        data=_data,
        metadata=_metadata,
    )
    if isinstance(volume, JP2KVolume):
        volume.rescale_data = (
            False  # keep coherence between all the volumes. Simplify test
        )
    volume.save()
    identifier = volume.get_identifier()
    assert isinstance(identifier, VolumeIdentifier)

    del volume
    volume_loaded = volume_constructor.from_identifier(identifier)
    volume_loaded.load()
    numpy.testing.assert_array_almost_equal(volume_loaded.data, _data)
    assert volume_loaded.metadata == _metadata

    # check API Identifier.to() and identifier.from_str()
    identifier_from_str = identifier.to_str()
    duplicate_id = identifier.from_str(identifier_from_str)
    assert duplicate_id == identifier
    assert identifier_from_str == identifier.to_str()
    assert identifier != object()
    assert identifier != "toto"
    assert isinstance(identifier.short_description(), str)

    # check it can be reconstructed from the Factory
    assert isinstance(identifier, VolumeIdentifier)
    tomo_obj_from_str = Factory.create_tomo_object_from_identifier(
        identifier=identifier
    )
    assert isinstance(tomo_obj_from_str, type(volume_loaded))
    tomo_obj_from_identifier = Factory.create_tomo_object_from_identifier(
        identifier=identifier.to_str()
    )
    assert isinstance(tomo_obj_from_identifier, type(volume_loaded))

    # test hash
    hash(tomo_obj_from_str)
    hash(tomo_obj_from_str.get_identifier())


def test_folder_mix_in():
    """simple test of the BaseFolderIdentifierMixIn class"""

    class FolderIdentifierTest(BaseFolderIdentifierMixIn, VolumeIdentifier):
        pass

    class VolumeTest(VolumeBase):
        pass

    obj = FolderIdentifierTest(object=VolumeTest, folder="toto", tomo_type="Volume")
    with pytest.raises(NotImplementedError):
        obj.scheme


@pytest.mark.parametrize("volume_constructor", volume_constructors)
def test_volume_with_prefix(tmp_path, volume_constructor):
    """
    Test writing and reading volume with a file_prefix and using the identifier
    """
    acquisition_dir = tmp_path / "acquisition"
    os.makedirs(acquisition_dir)
    volume_dir = acquisition_dir / "volume"
    os.makedirs(volume_dir)
    file_prefix = "test"

    volume_1 = volume_constructor(
        folder=volume_dir,
        data=_data[:5],
        metadata=_metadata,
        volume_basename=file_prefix,
    )
    if isinstance(volume_1, JP2KVolume):
        volume_1.rescale_data = (
            False  # keep coherence between all the volumes. Simplify test
        )
    volume_1.save()

    full_volume = volume_constructor(folder=volume_dir, volume_basename=file_prefix)
    full_volume.load()
    numpy.testing.assert_array_almost_equal(full_volume.data, _data[:5])
    assert full_volume.metadata == _metadata

    obj_recreated = Factory.create_tomo_object_from_identifier(
        full_volume.get_identifier()
    )
    assert isinstance(obj_recreated, volume_constructor)
    obj_recreated.load()

    numpy.testing.assert_array_equal(
        obj_recreated.data,
        volume_1.data,
    )

    numpy.testing.assert_array_equal(
        obj_recreated.metadata,
        volume_1.metadata,
    )


@pytest.mark.parametrize("volume_constructor", volume_constructors)
def test_example(volume_constructor):
    """test static function 'example'"""
    assert isinstance(volume_constructor.example_defined_from_str_identifier(), str)


def test_backward_compatibility_z_index_4(tmp_path):
    """
    make sure we are still able to read old volumes with the new class
    """
    acquisition_dir = tmp_path / "acquisition"
    os.makedirs(acquisition_dir)
    volume_dir = str(acquisition_dir / "volume")
    os.makedirs(volume_dir)

    class LegacyEDFVolume(EDFVolume):
        DEFAULT_DATA_PATH_PATTERN = "{volume_basename}_{index_zfill4}.{data_extension}"

    legacy_volume = LegacyEDFVolume(
        folder=volume_dir,
        data=_data,
    )
    legacy_volume.save()
    first_frame_path = os.path.join(volume_dir, "volume_0000.edf")
    assert os.path.exists(first_frame_path)

    # test loading with the legacy class
    legacy_volume.clear_cache()

    legacy_volume.load()
    numpy.testing.assert_array_almost_equal(_data, legacy_volume.data)

    # test loading with the updated EDFVolume class
    volume = EDFVolume(
        folder=volume_dir,
    )
    volume.load()
    numpy.testing.assert_array_almost_equal(_data, legacy_volume.data)


@pytest.mark.parametrize("save_volume_to_file", (True, False))
@pytest.mark.parametrize("volume_constructor", volume_constructors)
def test_get_slices(tmp_path, volume_constructor, save_volume_to_file):
    """test the volume 'get_slices' function"""
    test_dir = tmp_path / "test_get_slices"
    test_dir.mkdir()

    volume_dir = os.path.join(test_dir, "volume")
    volume_shape = 20, 100, 50
    volume_n_elemts = volume_shape[0] * volume_shape[1] * volume_shape[2]
    data = numpy.linspace(
        0,
        volume_n_elemts,
        num=volume_n_elemts,
        endpoint=False,
    ).reshape(volume_shape)
    volume = volume_constructor(folder=volume_dir, data=data, metadata={})

    if save_volume_to_file:
        volume.save()
        volume.clear_cache()

    # test raising error

    with pytest.raises(TypeError):
        volume.get_slices(
            "toto",
        )

    with pytest.raises(TypeError):
        volume.get_slices(
            (0, 10),
        )

    # test retrieving results
    slices_axis_0 = volume.get_slices(((0, 2), (0, 5)))
    slices_axis_1 = volume.get_slices(((1, 0), (1, 6)))
    slices_axis_2 = volume.get_slices(((2, 8), (2, 9)))
    slices_several_axis = volume.get_slices(((0, 2), (1, 0), (2, 9)))

    if volume_constructor is JP2KVolume:
        # JP2K is modifying original slice values. So we cannot compare them with
        # the original one.
        return

    numpy.testing.assert_array_almost_equal(
        slices_axis_0[(0, 2)],
        data[2],
    )

    numpy.testing.assert_array_almost_equal(
        slices_axis_1[(1, 6)],
        data[:, 6, :],
    )

    numpy.testing.assert_array_almost_equal(
        slices_axis_2[(2, 9)],
        data[:, :, 9],
    )

    numpy.testing.assert_array_almost_equal(
        slices_several_axis[(0, 2)],
        slices_axis_0[(0, 2)],
    )

    numpy.testing.assert_array_almost_equal(
        slices_several_axis[(1, 0)],
        slices_axis_1[(1, 0)],
    )

    numpy.testing.assert_array_almost_equal(
        slices_several_axis[(2, 9)],
        slices_axis_2[(2, 9)],
    )
