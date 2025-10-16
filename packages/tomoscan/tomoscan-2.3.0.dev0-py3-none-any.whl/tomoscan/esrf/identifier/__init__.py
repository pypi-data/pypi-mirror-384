# coding: utf-8

"""This module is dedicated to instances of :class:`BaseIdentifier` used at esrf"""

from .edfidentifier import EDFTomoScanIdentifier  # noqa F401
from .hdf5Identifier import NXtomoScanIdentifier  # noqa F401
from .jp2kidentifier import JP2KVolumeIdentifier  # noqa F401
from .rawidentifier import RawVolumeIdentifier  # noqa F401
from .tiffidentifier import MultiTiffVolumeIdentifier  # noqa F401
from .tiffidentifier import TIFFVolumeIdentifier  # noqa F401
