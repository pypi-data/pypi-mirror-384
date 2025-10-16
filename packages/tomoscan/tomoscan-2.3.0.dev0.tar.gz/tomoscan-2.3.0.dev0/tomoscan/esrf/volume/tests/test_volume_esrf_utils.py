# coding: utf-8
"""utils function for esrf volumes"""

import os
import shutil

import numpy
import pytest

from tomoscan.esrf.volume.edfvolume import EDFVolume
from tomoscan.esrf.volume.hdf5volume import HDF5Volume
from tomoscan.esrf.volume.jp2kvolume import JP2KVolume, has_glymur, has_minimal_openjpeg
from tomoscan.esrf.volume.tiffvolume import MultiTIFFVolume, TIFFVolume, has_tifffile
from tomoscan.esrf.volume.utils import guess_hdf5_volume_data_paths, guess_volumes


@pytest.mark.parametrize("file_extension", ("h5", "hdf5"))
def test_guess_volumes_hdf5(tmp_path, file_extension):
    """
    Test `guess_volumes` function within hdf5 file
    """
    assert guess_volumes(path=tmp_path) == tuple()
    file_path = os.path.join(tmp_path, ".".join(["my_file", file_extension]))
    # check error if path does not exists
    with pytest.raises(OSError):
        guess_volumes(path=file_path)

    volume = HDF5Volume(
        file_path=file_path,
        data_path="entry",
        data=numpy.linspace(1, 10, 100).reshape(1, 10, 10),
    )
    volume.save()

    guess_vols = guess_volumes(path=file_path)
    assert len(guess_vols) == 1
    guess_vol = guess_vols[0]
    assert isinstance(guess_vol, HDF5Volume)
    assert guess_vol.file_path == file_path
    assert guess_vol.data_path == "/entry"

    HDF5Volume(
        file_path=file_path,
        data_path="entry0002",
        data=numpy.linspace(1, 10, 100).reshape(1, 10, 10),
    ).save()
    assert len(guess_volumes(path=file_path)) == 2

    # a few more test on 'guess_hdf5_volume_data_paths'
    assert len(guess_hdf5_volume_data_paths(file_path=file_path, depth=0)) == 0
    assert (
        len(
            guess_hdf5_volume_data_paths(
                file_path=file_path, data_path="/entry", depth=0
            )
        )
        == 1
    )


_constructors = [EDFVolume]
if has_glymur and has_minimal_openjpeg:
    _constructors.append(JP2KVolume)
if has_tifffile:
    _constructors.append(TIFFVolume)


@pytest.mark.parametrize("Constructor", _constructors)
def test_guess_volumes_single_frame_file(tmp_path, Constructor):
    """
    Test `guess_volumes` function for single frame volume (like EDFVolume, TIFFVolume and Jp2KVolume)
    """
    assert guess_volumes(path=tmp_path) == tuple()
    folder = os.path.join(tmp_path, "my_volume_folder")
    # check error if path does not exists
    with pytest.raises(OSError):
        guess_volumes(path=folder)

    volume = Constructor(
        folder=folder,
        data=numpy.linspace(1, 10, 30000, dtype=numpy.uint8).reshape(3, 100, 100),
    )
    volume.save()

    guess_vols = guess_volumes(path=folder)
    assert len(guess_vols) == 1
    guess_vol = guess_vols[0]
    assert isinstance(guess_vol, Constructor)
    assert guess_vol.data_url.file_path() == folder
    assert guess_vol.get_volume_basename() == os.path.basename(folder)
    # test adding some noise in the folder
    for _ in range(15):
        file_name = os.path.join(folder, "my_volume_folder.txt")
        with open(file_name, mode="w") as f:
            f.write("almost empty text file")
    for other_file in ("other_file.tif", "other_file.tiff"):
        with open(os.path.join(folder, other_file), mode="w") as f:
            f.write("none")

    guess_vols = guess_volumes(path=folder)
    assert len(guess_vols) == 1
    shutil.rmtree(folder)
    # test with a basename
    volume = Constructor(
        folder=folder,
        volume_basename="other_basename",
        data=numpy.linspace(1, 10, 10000, dtype=numpy.uint8).reshape(1, 100, 100),
    )
    volume.save()
    guess_vols = guess_volumes(path=folder)
    assert len(guess_vols) == 1
    assert guess_vols[0].get_volume_basename() == "other_basename"


@pytest.mark.skipif(not has_tifffile, reason="tiffile not available")
def test_guess_volumes_multitiff(tmp_path):
    """
    Test `guess_volumes` function for MultiTiffVolume
    """
    assert guess_volumes(path=tmp_path) == tuple()
    file_path = os.path.join(tmp_path, "my_multitiff.tiff")
    # check error if path does not exists
    with pytest.raises(OSError):
        guess_volumes(path=file_path)

    volume = MultiTIFFVolume(
        file_path=file_path, data=numpy.linspace(1, 10, 200).reshape(2, 10, 10)
    )
    volume.save()

    guess_vols = guess_volumes(path=file_path)
    assert len(guess_vols) == 1
    guess_vol = guess_vols[0]
    assert isinstance(guess_vol, MultiTIFFVolume)
    assert guess_vol.data_url.file_path() == file_path
