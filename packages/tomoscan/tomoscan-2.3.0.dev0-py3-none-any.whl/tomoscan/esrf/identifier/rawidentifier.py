# coding: utf-8

import os

from tomoscan.identifier import VolumeIdentifier
from tomoscan.utils import docstring

__all__ = [
    "RawVolumeIdentifier",
]


class RawVolumeIdentifier(VolumeIdentifier):
    """Identifier for the .vol volume"""

    def __init__(self, object, file_path):
        super().__init__(object)
        self._file_path = os.path.abspath(os.path.abspath(file_path))

    @docstring(VolumeIdentifier)
    def short_description(self) -> str:
        return f"{self.scheme}:{self.tomo_type}:{os.path.basename(self._file_path)}"

    @property
    def file_path(self):
        return self._file_path

    @property
    @docstring(VolumeIdentifier)
    def scheme(self) -> str:
        return "raw"

    def __str__(self):
        return f"{self.scheme}:{self.tomo_type}:{self._file_path}"

    def __eq__(self, other):
        if isinstance(other, RawVolumeIdentifier):
            return (
                self.tomo_type == other.tomo_type
                and self._file_path == other._file_path
            )
        else:
            return False

    def __hash__(self):
        return hash(self._file_path)

    @staticmethod
    def from_str(identifier):
        identifier_no_scheme = identifier.split(":")[-1]
        vol_file = identifier_no_scheme
        from tomoscan.esrf.volume.rawvolume import RawVolume

        return RawVolumeIdentifier(object=RawVolume, file_path=vol_file)
