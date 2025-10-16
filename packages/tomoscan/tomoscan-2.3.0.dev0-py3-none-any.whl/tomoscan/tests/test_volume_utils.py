import os
from copy import deepcopy

import numpy
import pytest

from tomoscan.esrf.volume.edfvolume import EDFVolume
from tomoscan.esrf.volume.hdf5volume import HDF5Volume
from tomoscan.esrf.volume.jp2kvolume import JP2KVolume, has_minimal_openjpeg
from tomoscan.esrf.volume.tiffvolume import TIFFVolume, has_tifffile
from tomoscan.utils.volume import concatenate, update_metadata

_clases_to_test = [EDFVolume, HDF5Volume]
if has_minimal_openjpeg:
    _clases_to_test.append(JP2KVolume)
if has_tifffile:
    _clases_to_test.append(TIFFVolume)


def test_concatenate_volume_errors():
    """test some error raised by tomoscan.utils.volume.concatenate function"""
    vol = HDF5Volume(
        file_path="toto",
        data_path="test",
    )
    with pytest.raises(TypeError):
        concatenate(output_volume=1, volumes=(), axis=1),

    with pytest.raises(TypeError):
        concatenate(output_volume=vol, volumes=(), axis="1")

    with pytest.raises(TypeError):
        concatenate(output_volume=vol, volumes=(), axis="1")

    with pytest.raises(ValueError):
        concatenate(output_volume=vol, volumes=(), axis=6)

    with pytest.raises(ValueError):
        concatenate(output_volume=vol, volumes=(1,), axis=1)

    with pytest.raises(TypeError):
        concatenate(output_volume=vol, volumes="toto", axis=1)


@pytest.mark.parametrize("axis", (0, 1, 2))
@pytest.mark.parametrize("volume_class", _clases_to_test)
def test_concatenate_volume(tmp_path, volume_class, axis):
    """
    test concatenation of 3 volumes into a single one
    """
    # create folder to save data (and debug)
    raw_data_dir = tmp_path / "raw_data"
    raw_data_dir.mkdir()
    output_dir = tmp_path / "output_dir"
    output_dir.mkdir()

    param_set_1 = {
        "data": numpy.ones((100, 100, 100), dtype=numpy.uint16),
        "metadata": {
            "this": {
                "is": {"metadata": 1},
            },
        },
    }

    param_set_2 = {
        "data": numpy.arange(100 * 100 * 100, dtype=numpy.uint16).reshape(
            100, 100, 100
        ),
        "metadata": {
            "this": {
                "is": {"metadata": 2},
                "isn't": {
                    "something": 12.3,
                },
            },
        },
    }

    param_set_3 = {
        "data": numpy.zeros((100, 100, 100), dtype=numpy.uint16),
        "metadata": {
            "yet": {
                "another": {
                    "metadata": 12,
                },
            },
        },
    }

    volumes = []
    param_sets = (param_set_1, param_set_2, param_set_3)
    for i_vol, vol_params in enumerate(param_sets):
        if volume_class == HDF5Volume:
            vol_params.update(
                {
                    "file_path": os.path.join(raw_data_dir, f"volume_{i_vol}.hdf5"),
                    "data_path": "volume",
                }
            )
        else:
            vol_params.update({"folder": os.path.join(raw_data_dir, f"volume_{i_vol}")})
        volume = volume_class(**vol_params)
        if isinstance(volume, JP2KVolume):
            volume.rescale_data = False  # simplify test
        volume.save()
        volumes.append(volume)
        volume.data = None
        volume.metadata = None
    volumes = tuple(volumes)

    # apply concatenation
    if volume_class == HDF5Volume:
        final_volume = HDF5Volume(
            file_path=os.path.join(output_dir, "final_vol.hdf5"),
            data_path="volume",
        )
    else:
        final_volume = volume_class(
            folder=os.path.join(output_dir, "final_vol"),
        )
        if isinstance(final_volume, JP2KVolume):
            final_volume.rescale_data = False

    concatenate(output_volume=final_volume, volumes=volumes, axis=axis)
    if axis == 0:
        expected_final_shape = (300, 100, 100)
    elif axis == 1:
        expected_final_shape = (100, 300, 100)
    elif axis == 2:
        expected_final_shape = (100, 100, 300)
    else:
        raise RuntimeError("axis should be in (0, 1, 2)")

    assert final_volume.data is None
    assert final_volume.get_volume_shape() == expected_final_shape
    final_volume.load()
    assert "this" in final_volume.metadata

    [volume.load() for volume in volumes]

    if axis == 0:
        numpy.testing.assert_almost_equal(final_volume.data[0:100], volumes[0].data)
        numpy.testing.assert_almost_equal(final_volume.data[100:200], volumes[1].data)
        numpy.testing.assert_almost_equal(final_volume.data[200:300], volumes[2].data)
    elif axis == 1:
        numpy.testing.assert_almost_equal(final_volume.data[:, 0:100], volumes[0].data)
        numpy.testing.assert_almost_equal(
            final_volume.data[:, 100:200], volumes[1].data
        )
        numpy.testing.assert_almost_equal(
            final_volume.data[:, 200:300], volumes[2].data
        )
    elif axis == 2:
        numpy.testing.assert_almost_equal(
            final_volume.data[:, :, 0:100], volumes[0].data
        )
        numpy.testing.assert_almost_equal(
            final_volume.data[:, :, 100:200], volumes[1].data
        )
        numpy.testing.assert_almost_equal(
            final_volume.data[:, :, 200:300], volumes[2].data
        )

    final_volume.overwrite = False
    with pytest.raises(OSError):
        concatenate(output_volume=final_volume, volumes=volumes, axis=axis)

    final_volume.overwrite = True
    concatenate(output_volume=final_volume, volumes=volumes, axis=axis)


def test_update_metadata():
    ddict_1 = {
        "key": {
            "sub_key_1": "toto",
            "sub_key_2": "tata",
        },
        "second_key": "test",
    }
    ddict_2 = {
        "key": {
            "sub_key_1": "test",
            "sub_key_3": "test",
        },
        "third_key": "test",
    }

    assert update_metadata(deepcopy(ddict_1), deepcopy(ddict_2)) == {
        "key": {
            "sub_key_1": "test",
            "sub_key_2": "tata",
            "sub_key_3": "test",
        },
        "second_key": "test",
        "third_key": "test",
    }

    assert update_metadata(deepcopy(ddict_2), deepcopy(ddict_1)) == {
        "key": {
            "sub_key_1": "toto",
            "sub_key_2": "tata",
            "sub_key_3": "test",
        },
        "second_key": "test",
        "third_key": "test",
    }
    with pytest.raises(TypeError):
        update_metadata(1, 2)
