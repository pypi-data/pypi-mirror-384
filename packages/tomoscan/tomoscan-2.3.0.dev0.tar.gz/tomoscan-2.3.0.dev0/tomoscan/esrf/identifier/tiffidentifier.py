# coding: utf-8

import os

from tomoscan.esrf.identifier.folderidentifier import (
    BaseFolderAndfilePrefixIdentifierMixIn,
)
from tomoscan.identifier import VolumeIdentifier
from tomoscan.utils import docstring

__all__ = ["TIFFVolumeIdentifier", "MultiTiffVolumeIdentifier"]


class TIFFVolumeIdentifier(BaseFolderAndfilePrefixIdentifierMixIn, VolumeIdentifier):
    """Identifier specific to (single frame) tiff volume"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, tomo_type=VolumeIdentifier.TOMO_TYPE)

    @property
    @docstring(VolumeIdentifier)
    def scheme(self) -> str:
        return "tiff"

    @staticmethod
    def from_str(identifier):
        from tomoscan.esrf.volume.tiffvolume import TIFFVolume

        return (
            BaseFolderAndfilePrefixIdentifierMixIn._from_str_to_single_frame_identifier(
                identifier=identifier,
                SingleFrameIdentifierClass=TIFFVolumeIdentifier,
                ObjClass=TIFFVolume,
            )
        )


class MultiTiffVolumeIdentifier(VolumeIdentifier):
    def __init__(self, object, tiff_file):
        super().__init__(object)
        self._file_path = os.path.abspath(os.path.abspath(tiff_file))

    @docstring(VolumeIdentifier)
    def short_description(self) -> str:
        return f"{self.scheme}:{self.tomo_type}:{os.path.basename(self._file_path)}"

    @property
    def file_path(self):
        return self._file_path

    @property
    @docstring(VolumeIdentifier)
    def scheme(self) -> str:
        return "tiff3d"

    def __str__(self):
        return f"{self.scheme}:{self.tomo_type}:{self._file_path}"

    def __eq__(self, other):
        if isinstance(other, MultiTiffVolumeIdentifier):
            return (
                self.tomo_type == other.tomo_type
                and self._file_path == other._file_path
            )
        else:
            return super().__eq__(other)

    def __hash__(self):
        return hash(self._file_path)

    @staticmethod
    def from_str(identifier):
        identifier_no_scheme = identifier.split(":")[-1]
        # TODO: check tomo_type ?
        tiff_file = identifier_no_scheme
        from tomoscan.esrf.volume.tiffvolume import TIFFVolume

        return MultiTiffVolumeIdentifier(object=TIFFVolume, tiff_file=tiff_file)
