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

__all__ = ["BaseFolderIdentifierMixIn", "BaseFolderAndfilePrefixIdentifierMixIn"]


class BaseFolderIdentifierMixIn:
    """Identifier specific to a folder. Used for single frame edf and jp2g for example"""

    def __init__(self, object, folder, tomo_type):
        super().__init__(object)
        self._folder = os.path.abspath(os.path.abspath(folder))
        self.__tomo_type = tomo_type

    def short_description(self) -> str:
        return ParseResult(
            scheme=self.scheme,
            path=join_path((self.tomo_type, os.path.basename(self.folder))),
            query=None,
            netloc=None,
            params=None,
            fragment=None,
        ).geturl()

    @property
    def tomo_type(self):
        # warning: this property will probably be overwrite
        return self.__tomo_type

    @property
    def folder(self):
        return self._folder

    @property
    def scheme(self) -> str:
        raise NotImplementedError("base class")

    def __str__(self):
        return ParseResult(
            scheme=self.scheme,
            path=join_path((self.tomo_type, self.folder)),
            query=None,
            netloc=None,
            params=None,
            fragment=None,
        ).geturl()

    def __eq__(self, other):
        if isinstance(other, BaseFolderIdentifierMixIn):
            return self.folder == other.folder and self.tomo_type == other.tomo_type
        else:
            return super().__eq__(other)

    def __hash__(self):
        return hash(self.folder)


class BaseFolderAndfilePrefixIdentifierMixIn(BaseFolderIdentifierMixIn):
    def __init__(self, object, folder, file_prefix, tomo_type):
        super().__init__(object, folder, tomo_type)
        self._file_prefix = file_prefix

    def short_description(self) -> str:
        query = []
        if self.file_prefix not in (None, ""):
            query.append(
                ("file_prefix", self.file_prefix),
            )
        return ParseResult(
            scheme=self.scheme,
            path=join_path((self.tomo_type, self.folder)),
            query=join_query(query),
            netloc=None,
            params=None,
            fragment=None,
        ).geturl()

    @property
    def file_prefix(self) -> str:
        return self._file_prefix

    def __str__(self):
        query = []
        if self.file_prefix not in (None, ""):
            query.append(
                ("file_prefix", self.file_prefix),
            )
        return ParseResult(
            scheme=self.scheme,
            path=join_path((self.tomo_type, self.folder)),
            query=join_query(query),
            netloc=None,
            params=None,
            fragment=None,
        ).geturl()

    def __eq__(self, other):
        return super().__eq__(other) and self.file_prefix == other.file_prefix

    def __hash__(self):
        return hash(self.folder) + hash(self.file_prefix)

    @staticmethod
    def _from_str_to_single_frame_identifier(
        identifier: str, SingleFrameIdentifierClass, ObjClass: type
    ):
        """
        Common function to build an identifier from a str. Might be moved to the factory directly one day ?
        """
        info = urlparse(identifier)
        paths = split_path(info.path)
        if len(paths) == 1:
            jp2k_folder = paths[0]
            tomo_type = None
        elif len(paths) == 2:
            tomo_type, jp2k_folder = paths
        else:
            raise ValueError("Failed to parse path string:", info.path)
        if tomo_type is not None and tomo_type != SingleFrameIdentifierClass.TOMO_TYPE:
            raise TypeError(
                f"provided identifier fits {tomo_type} and not {SingleFrameIdentifierClass.TOMO_TYPE}"
            )

        queries = split_query(info.query)
        file_prefix = queries.get(UrlSettings.FILE_PREFIX, None)

        return SingleFrameIdentifierClass(
            object=ObjClass, folder=jp2k_folder, file_prefix=file_prefix
        )
