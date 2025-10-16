"""module dedicated to esrf scans"""

from .scan.edfscan import EDFTomoScan  # noqa F401
from .scan.nxtomoscan import NXtomoScan  # noqa F401
from .scan.nxtomoscan import HDF5TomoScan  # noqa F401
from .volume.edfvolume import EDFVolume  # noqa F401
from .volume.hdf5volume import HDF5Volume  # noqa F401
from .volume.jp2kvolume import JP2KVolume  # noqa F401
from .volume.jp2kvolume import has_glymur  # noqa F401
from .volume.rawvolume import RawVolume  # noqa F401
from .volume.tiffvolume import MultiTIFFVolume  # noqa F401
from .volume.tiffvolume import TIFFVolume  # noqa F401
from .volume.tiffvolume import has_tifffile  # noqa F401

TYPES = ["EDF", "HDF5", "FLUO"]
