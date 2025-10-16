# coding: utf-8
"""utils function for esrf volumes"""

from __future__ import annotations

import logging
import os

import h5py
from silx.io.utils import open as hdf5_open

from tomoscan.volumebase import SliceTuple

from tomoscan.esrf.identifier.edfidentifier import EDFVolumeIdentifier
from tomoscan.esrf.identifier.hdf5Identifier import HDF5VolumeIdentifier
from tomoscan.esrf.identifier.jp2kidentifier import JP2KVolumeIdentifier
from tomoscan.esrf.identifier.rawidentifier import RawVolumeIdentifier
from tomoscan.esrf.identifier.tiffidentifier import (
    MultiTiffVolumeIdentifier,
    TIFFVolumeIdentifier,
)
from tomoscan.esrf.volume.edfvolume import EDFVolume
from tomoscan.esrf.volume.hdf5volume import HDF5Volume
from tomoscan.esrf.volume.jp2kvolume import JP2KVolume
from tomoscan.esrf.volume.rawvolume import RawVolume
from tomoscan.esrf.volume.tiffvolume import MultiTIFFVolume, TIFFVolume

_logger = logging.getLogger(__name__)

__all__ = [
    "guess_hdf5_volume_data_paths",
    "guess_volumes",
    "get_most_common_extension",
    "group_slices_by_axis",
]

_DEFAULT_SCHEME_TO_VOL = {
    EDFVolumeIdentifier.scheme: EDFVolume,
    HDF5VolumeIdentifier.scheme: HDF5Volume,
    TIFFVolumeIdentifier.scheme: TIFFVolume,
    MultiTiffVolumeIdentifier.scheme: MultiTIFFVolume,
    JP2KVolumeIdentifier.scheme: JP2KVolume,
    RawVolumeIdentifier.scheme: RawVolume,
}


def guess_hdf5_volume_data_paths(file_path, data_path="/", depth=3) -> tuple:
    """
    browse hdf5 file 'file_path' from 'data_path' on 'depth' level and check for possible defined volumes.

    :param file_path: file path to the hdf5 file to browse
    :param data_path: path in the file to start research
    :param depth: on which layer we should apply research
    :return: tuple of data_path that could fit a volume
    """
    if not h5py.is_hdf5(file_path):
        raise ValueError(f"{file_path} is not a hdf5 file path")
    with hdf5_open(filename=file_path) as h5f:
        group = h5f[data_path]
        if isinstance(group, h5py.Group):
            if HDF5Volume.DATA_DATASET_NAME in group:
                return (data_path,)
            elif depth > 0:
                res = []
                for key in group.keys():
                    res.extend(
                        guess_hdf5_volume_data_paths(
                            file_path=file_path,
                            data_path="/".join((data_path, key)).replace("//", "/"),
                            depth=depth - 1,
                        )
                    )
                return tuple(res)

        return tuple()


def guess_volumes(
    path, scheme_to_vol: dict | None = None, filter_histograms=True
) -> tuple:
    """
    from a file path or a folder path try to guess volume(s)

    :param path: file or folder path
    :param scheme_to_vol: dict to know which constructor to call. Key if the scheme, value if the volume constructor.
                               usefull for libraries redefining volume or adding some like tomwer.
                               If none provided will take the tomoscan default one
    :return: tuple of volume
    """
    if not os.path.exists(path):
        raise OSError("path doesn't exists")

    if scheme_to_vol is None:
        scheme_to_vol = _DEFAULT_SCHEME_TO_VOL

    if os.path.isfile(path):
        if h5py.is_hdf5(path):
            res = []
            for data_path in guess_hdf5_volume_data_paths(path):
                assert isinstance(data_path, str)
                res.append(
                    scheme_to_vol[HDF5VolumeIdentifier.scheme](
                        file_path=path,
                        data_path=data_path,
                    )
                )
            # filter potential 'nabu histogram'
            # as nabu histograms looks like volume simply look at the name
            # could also be on data ndim
            if filter_histograms is True:

                def is_not_histogram(vol_identifier):
                    return not (
                        hasattr(vol_identifier, "data_path")
                        and vol_identifier.data_path.endswith("histogram")
                    )

                res = tuple(filter(is_not_histogram, res))

            return tuple(res)
        elif path.lower().endswith((".tif", ".tiff")):
            return (scheme_to_vol[MultiTiffVolumeIdentifier.scheme](file_path=path),)
        elif path.lower().endswith((".vol", ".raw")):
            return (scheme_to_vol[RawVolumeIdentifier.scheme](file_path=path),)
    elif os.path.isdir(path):
        most_common_extension = get_most_common_extension(path)
        if most_common_extension is None:
            return tuple()

        basename = _guess_volume_basename(path, extension=most_common_extension)
        if most_common_extension in ("tiff", "tif"):
            return (
                scheme_to_vol[TIFFVolumeIdentifier.scheme](
                    folder=path,
                    volume_basename=basename,
                    data_extension=most_common_extension,
                ),
            )
        elif most_common_extension in ("jp2", "jp2k"):
            return (
                scheme_to_vol[JP2KVolumeIdentifier.scheme](
                    folder=path,
                    volume_basename=basename,
                    data_extension=most_common_extension,
                ),
            )
        elif most_common_extension == "edf":
            return (
                scheme_to_vol[EDFVolumeIdentifier.scheme](
                    folder=path,
                    volume_basename=basename,
                    data_extension=most_common_extension,
                ),
            )
        else:
            _logger.warning(
                f"most common extension is {most_common_extension}. Unable to create a volume from it"
            )
            return tuple()
    else:
        raise NotImplementedError("guess_volumes only handle file and folder...")


def get_most_common_extension(folder_path):
    if not os.path.isdir(folder_path):
        raise ValueError(f"a folder path is expected. {folder_path} isn't")

    extensions = {}
    for file_path in os.listdir(folder_path):
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip(".")
        if ext in extensions:
            extensions[ext] += 1
        else:
            extensions[ext] = 1

    # filter not handled extensions
    def is_valid_extension(extension):
        return extension in ("edf", "tif", "tiff", "jp2", "jp2k")

    extensions = {
        key: value for (key, value) in extensions.items() if is_valid_extension(key)
    }

    if len(extensions) == 0:
        _logger.warning(f"no valid extensions found in {folder_path}")
    else:
        sort_extensions = sorted(extensions.items(), key=lambda x: x[1], reverse=True)
        return sort_extensions[0][0]


def _guess_volume_basename(folder_path, extension):
    # list all the files matching the file and guessing the file parttern
    files_to_check = []
    possible_basenames = {}
    for file_path in os.listdir(folder_path):
        if file_path.lower().endswith(extension):
            files_to_check.append(os.path.splitext(file_path)[0])
            # the expected way to save those files is basename_XXXX with XXXX is the index over 4 char
            basename = "_".join(file_path.split("_")[:-1])
            if basename in possible_basenames:
                possible_basenames[basename] += 1
            else:
                possible_basenames[basename] = 1

    if len(possible_basenames) == 0:
        _logger.warning(f"no valid basename found in {folder_path}")
    else:
        sort_basenames = sorted(
            possible_basenames.items(), key=lambda x: x[1], reverse=True
        )
        if len(sort_basenames) > 1:
            _logger.warning(
                f"more than one basename found. Take the most probable one ({sort_basenames[0][0]})"
            )
        return sort_basenames[0][0]


def group_slices_by_axis(
    slices: tuple[SliceTuple], volume_shape: tuple[int] | None
) -> dict[int, set]:
    """
    group a tuple of slices provided as SliceTuple (axis, slice) to a dict.
    Dict contains predetermined keys (0, 1, 2). For each key with have a set of int (slice indices to be read)

    volume_shape: shape of the reference volume to perform test on slice indices (if provided)
    """
    indices_to_read_per_axis: dict[int, set[int]] = {
        0: set(),
        1: set(),
        2: set(),
    }
    for slice_ in slices:
        if volume_shape is not None and (slice_.index >= volume_shape[slice_.axis]):
            raise IndexError(
                f"index {slice_.index} is out of bounds for axis {slice_.axis}. (Volume shape is {volume_shape})"
            )
        indices_to_read_per_axis[slice_.axis].add(slice_.index)
    return indices_to_read_per_axis
