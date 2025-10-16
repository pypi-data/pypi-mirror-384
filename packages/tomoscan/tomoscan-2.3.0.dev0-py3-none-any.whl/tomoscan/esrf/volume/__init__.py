# coding: utf-8

"""This module is dedicated to instances of :class:`VolumeBase` used at esrf"""

from .edfvolume import EDFVolume  # noqa F401
from .hdf5volume import HDF5Volume  # noqa F401
from .jp2kvolume import JP2KVolume  # noqa F401
from .rawvolume import RawVolume  # noqa F401
from .tiffvolume import MultiTIFFVolume, TIFFVolume  # noqa F401
