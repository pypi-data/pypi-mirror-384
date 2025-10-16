# coding: utf-8

"""Module dedicated to input / output utils"""

from __future__ import annotations

import logging
import os
import numpy
from h5py import File as HDF5File  # noqa F401
from silx.io.utils import open as hdf5_open

_logger = logging.getLogger(__name__)

_DEFAULT_SWMR_MODE = None

__all__ = [
    "get_swmr_mode",
    "check_virtual_sources_exist",
]


def get_swmr_mode() -> bool | None:
    """
    Return True if the swmr should be used in the tomoools scope
    """
    swmr_mode = os.environ.get("TOMOTOOLS_SWMR", _DEFAULT_SWMR_MODE)
    if swmr_mode in (None, "None", "NONE"):
        return None
    else:
        return swmr_mode in (
            True,
            "True",
            "true",
            "TRUE",
            "1",
            1,
        )


def check_virtual_sources_exist(fname, data_path):
    """
    Check that a virtual dataset points to actual data.

    :param fname: HDF5 file path
    :param data_path: Path within the HDF5 file

    :return bool res: Whether the virtual dataset points to actual data.
    """
    with hdf5_open(fname) as f:
        if data_path not in f:
            _logger.error(f"No dataset {data_path} in file {fname}")
            return False
        dptr = f[data_path]
        if not dptr.is_virtual:
            return True
        for vsource in dptr.virtual_sources():
            vsource_fname = os.path.join(
                os.path.dirname(dptr.file.filename), vsource.file_name
            )
            if not os.path.isfile(vsource_fname):
                _logger.error(f"No such file: {vsource_fname}")
                return False
            elif not check_virtual_sources_exist(vsource_fname, vsource.dset_name):
                _logger.error(f"Error with virtual source {vsource_fname}")
                return False
    return True


def cast_to_default_types(data: any):
    """Function that cast non default python types to default python type"""
    if isinstance(data, dict):
        # If data is a dictionary, recursively process each value
        return {key: cast_to_default_types(value) for key, value in data.items()}
    elif isinstance(data, (list, tuple)):
        # If data is a list, recursively process each element
        return [cast_to_default_types(item) for item in data]
    elif isinstance(data, (numpy.integer, numpy.int_)):
        # Convert NumPy integers to Python int
        return int(data)
    elif isinstance(data, numpy.floating):
        # Convert NumPy floats to Python float
        return float(data)
    elif isinstance(data, numpy.ndarray):
        # Convert NumPy arrays to list of default python type
        return data.tolist()
    elif isinstance(data, numpy.bool):
        # Convert NumPy booleans to Python bool
        return bool(data)
    else:
        # Return the data as-is if it doesn't match any of the above types
        return data
