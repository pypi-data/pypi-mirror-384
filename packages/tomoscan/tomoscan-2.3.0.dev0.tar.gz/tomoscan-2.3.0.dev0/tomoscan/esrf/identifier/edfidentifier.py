# coding: utf-8

from tomoscan.esrf.identifier.folderidentifier import (
    BaseFolderAndfilePrefixIdentifierMixIn,
)
from tomoscan.identifier import ScanIdentifier, VolumeIdentifier
from tomoscan.utils import docstring


__all__ = ["EDFTomoScanIdentifier", "EDFVolumeIdentifier"]


class _BaseEDFIdentifier(BaseFolderAndfilePrefixIdentifierMixIn):
    """Identifier specific to EDF TomoScan"""

    @property
    @docstring(ScanIdentifier)
    def scheme(self) -> str:
        return "edf"


class EDFTomoScanIdentifier(_BaseEDFIdentifier, ScanIdentifier):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, tomo_type=ScanIdentifier.TOMO_TYPE)

    @staticmethod
    def from_str(identifier):
        from tomoscan.esrf.scan.edfscan import EDFTomoScan

        return (
            BaseFolderAndfilePrefixIdentifierMixIn._from_str_to_single_frame_identifier(
                identifier=identifier,
                SingleFrameIdentifierClass=EDFTomoScanIdentifier,
                ObjClass=EDFTomoScan,
            )
        )


class EDFVolumeIdentifier(_BaseEDFIdentifier, VolumeIdentifier):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, tomo_type=VolumeIdentifier.TOMO_TYPE)

    @staticmethod
    def from_str(identifier):
        from tomoscan.esrf.volume.edfvolume import EDFVolume

        return (
            BaseFolderAndfilePrefixIdentifierMixIn._from_str_to_single_frame_identifier(
                identifier=identifier,
                SingleFrameIdentifierClass=EDFVolumeIdentifier,
                ObjClass=EDFVolume,
            )
        )
