# coding: utf-8

from tomoscan.esrf.identifier.folderidentifier import (
    BaseFolderAndfilePrefixIdentifierMixIn,
)
from tomoscan.identifier import VolumeIdentifier
from tomoscan.utils import docstring

__all__ = [
    "JP2KVolumeIdentifier",
]


class JP2KVolumeIdentifier(BaseFolderAndfilePrefixIdentifierMixIn, VolumeIdentifier):
    """Identifier specific to JP2K volume"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, tomo_type=VolumeIdentifier.TOMO_TYPE)

    @property
    @docstring(VolumeIdentifier)
    def scheme(self) -> str:
        return "jp2k"

    @staticmethod
    def from_str(identifier):
        from tomoscan.esrf.volume.jp2kvolume import JP2KVolume

        return (
            BaseFolderAndfilePrefixIdentifierMixIn._from_str_to_single_frame_identifier(
                identifier=identifier,
                SingleFrameIdentifierClass=JP2KVolumeIdentifier,
                ObjClass=JP2KVolume,
            )
        )
