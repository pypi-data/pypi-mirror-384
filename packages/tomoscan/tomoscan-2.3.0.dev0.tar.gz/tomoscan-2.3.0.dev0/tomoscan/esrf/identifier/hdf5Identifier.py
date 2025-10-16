# coding: utf-8

import os
from urllib.parse import ParseResult, urlparse

from tomoscan.esrf.identifier.url_utils import (
    UrlSettings,
    join_path,
    join_query,
    split_path,
    split_query,
)
from tomoscan.identifier import ScanIdentifier, VolumeIdentifier
from tomoscan.utils import docstring
from tomoscan.utils.io import deprecated_warning

__all__ = ["NXtomoScanIdentifier", "HDF5VolumeIdentifier", "HDF5TomoScanIdentifier"]


class _HDF5IdentifierMixIn:
    def __init__(self, object, hdf5_file, entry, tomo_type):
        super().__init__(object)
        self._file_path = os.path.abspath(os.path.abspath(hdf5_file))
        self._data_path = entry
        self._tomo_type = tomo_type

    @property
    def tomo_type(self):
        return self._tomo_type

    @docstring(ScanIdentifier)
    def short_description(self) -> str:
        return ParseResult(
            scheme=self.scheme,
            path=join_path(
                (self.tomo_type, os.path.basename(self._file_path)),
            ),
            query=join_query(
                ((UrlSettings.DATA_PATH_KEY, self.data_path),),
            ),
            netloc=None,
            params=None,
            fragment=None,
        ).geturl()

    @property
    def file_path(self):
        return self._file_path

    @property
    def data_path(self):
        return self._data_path

    @property
    @docstring(ScanIdentifier)
    def scheme(self) -> str:
        return "hdf5"

    def __str__(self):
        return ParseResult(
            scheme=self.scheme,
            path=join_path(
                (self.tomo_type, self._file_path),
            ),
            query=join_query(
                ((UrlSettings.DATA_PATH_KEY, self.data_path),),
            ),
            netloc=None,
            params=None,
            fragment=None,
        ).geturl()

    def __eq__(self, other):
        if isinstance(other, NXtomoScanIdentifier):
            return (
                self.tomo_type == other.tomo_type
                and self._file_path == other._file_path
                and self._data_path == other._data_path
            )
        else:
            return super().__eq__(other)

    def __hash__(self):
        return hash((self._file_path, self._data_path))


class NXtomoScanIdentifier(_HDF5IdentifierMixIn, ScanIdentifier):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, tomo_type=ScanIdentifier.TOMO_TYPE)

    @staticmethod
    def from_str(identifier):
        info = urlparse(identifier)
        paths = split_path(info.path)
        if len(paths) == 1:
            hdf5_file = paths[0]
            tomo_type = None
        elif len(paths) == 2:
            tomo_type, hdf5_file = paths
        else:
            raise ValueError("Failed to parse path string:", info.path)
        if tomo_type is not None and tomo_type != NXtomoScanIdentifier.TOMO_TYPE:
            raise TypeError(
                f"provided identifier fits {tomo_type} and not {NXtomoScanIdentifier.TOMO_TYPE}"
            )

        queries = split_query(info.query)
        entry = queries.get(UrlSettings.DATA_PATH_KEY, None)
        if entry is None:
            raise ValueError(f"expects to get {UrlSettings.DATA_PATH_KEY} query")
        from tomoscan.esrf.scan.nxtomoscan import NXtomoScan

        return NXtomoScanIdentifier(object=NXtomoScan, hdf5_file=hdf5_file, entry=entry)


class HDF5VolumeIdentifier(_HDF5IdentifierMixIn, VolumeIdentifier):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, tomo_type=VolumeIdentifier.TOMO_TYPE)

    @staticmethod
    def from_str(identifier):
        info = urlparse(identifier)
        paths = split_path(info.path)
        if len(paths) == 1:
            hdf5_file = paths[0]
            tomo_type = None
        elif len(paths) == 2:
            tomo_type, hdf5_file = paths
        else:
            raise ValueError("Failed to parse path string:", info.path)
        if tomo_type is not None and tomo_type != VolumeIdentifier.TOMO_TYPE:
            raise TypeError(
                f"provided identifier fits {tomo_type} and not {VolumeIdentifier.TOMO_TYPE}"
            )

        queries = split_query(info.query)
        entry = queries.get(UrlSettings.DATA_PATH_KEY, None)
        if entry is None:
            raise ValueError("expects to get a data_path")
        from tomoscan.esrf.volume.hdf5volume import HDF5Volume

        return HDF5VolumeIdentifier(object=HDF5Volume, hdf5_file=hdf5_file, entry=entry)


class HDF5TomoScanIdentifier(NXtomoScanIdentifier):
    def __init__(self, *args, **kwargs):
        deprecated_warning(
            type_="class",
            name="tomoscan.esrf.identifier.hdf5identifier.HDF5TomoScanIdentifier",
            replacement="tomoscan.esrf.identifier.hdf5identifier.NXtomoScanIdentifier",
            reason="improve coherence",
            since_version="2.0",
        )
        super().__init__(*args, **kwargs)
