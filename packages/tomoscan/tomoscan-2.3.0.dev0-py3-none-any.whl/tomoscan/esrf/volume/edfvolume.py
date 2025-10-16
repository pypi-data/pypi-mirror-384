# coding: utf-8
"""module defining utils for an edf volume"""

from __future__ import annotations

import os
import logging
import mmap

import fabio
import fabio.edfimage
import numpy
from silx.io.url import DataUrl

from tomoscan.esrf.identifier.edfidentifier import EDFVolumeIdentifier
from tomoscan.esrf.volume.singleframebase import (
    VolumeSingleFrameBase,
    TIFFLikeDiskAccessor,
)
from tomoscan.scanbase import TomoScanBase
from tomoscan.utils import docstring

_logger = logging.getLogger(__name__)


__all__ = [
    "EDFVolume",
]


class EDFVolume(TIFFLikeDiskAccessor, VolumeSingleFrameBase):
    """
    Save volume data to single frame edf and metadata to .txt files

    :warning: each file saved under {volume_basename}_{index_zfill6}.edf is considered to be a slice of the volume.
    """

    DEFAULT_DATA_SCHEME = "fabio"

    DEFAULT_DATA_EXTENSION = "edf"

    def __init__(
        self,
        folder: str | None = None,
        volume_basename: str | None = None,
        data: numpy.ndarray | None = None,
        source_scan: TomoScanBase | None = None,
        metadata: dict | None = None,
        data_url: DataUrl | None = None,
        metadata_url: DataUrl | None = None,
        overwrite: bool = False,
        header: dict | None = None,
        start_index=0,
        data_extension=DEFAULT_DATA_EXTENSION,
        metadata_extension=VolumeSingleFrameBase.DEFAULT_METADATA_EXTENSION,
    ) -> None:
        if folder is not None:
            url = DataUrl(
                file_path=str(folder),
                data_path=None,
            )
        else:
            url = None
        TIFFLikeDiskAccessor.__init__(self)
        super().__init__(
            volume_basename=volume_basename,
            url=url,
            data=data,
            source_scan=source_scan,
            metadata=metadata,
            data_url=data_url,
            metadata_url=metadata_url,
            overwrite=overwrite,
            start_index=start_index,
            data_extension=data_extension,
            metadata_extension=metadata_extension,
        )

        self._header = header

    @property
    def header(self) -> dict | None:
        """possible header for the edf files"""
        return self._header

    @docstring(VolumeSingleFrameBase)
    def save_frame(self, frame, file_name, scheme):
        if scheme == "fabio":
            header = self.header or {}
            edf_writer = fabio.edfimage.EdfImage(
                data=frame,
                header=header,
            )
            parent_dir = os.path.dirname(file_name)
            if parent_dir != "":
                os.makedirs(parent_dir, exist_ok=True)
            edf_writer.write(file_name)
        else:
            raise ValueError(f"scheme {scheme} is not handled")

    @docstring(VolumeSingleFrameBase)
    def load_frame(self, file_name, scheme):
        if scheme == "fabio":
            return fabio.open(file_name).data
        else:
            raise ValueError(f"scheme {scheme} is not handled")

    @staticmethod
    @docstring(VolumeSingleFrameBase)
    def from_identifier(identifier):
        """Return the Dataset from a identifier"""
        if not isinstance(identifier, EDFVolumeIdentifier):
            raise TypeError(
                f"identifier should be an instance of {EDFVolumeIdentifier}"
            )
        return EDFVolume(
            folder=identifier.folder,
            volume_basename=identifier.file_prefix,
        )

    @docstring(VolumeSingleFrameBase)
    def get_identifier(self) -> EDFVolumeIdentifier:
        if self.url is None:
            raise ValueError("no file_path provided. Cannot provide an identifier")
        return EDFVolumeIdentifier(
            object=self, folder=self.url.file_path(), file_prefix=self._volume_basename
        )

    @staticmethod
    def example_defined_from_str_identifier() -> str:
        return " ; ".join(
            [
                f"{EDFVolume(folder='/path/to/my/my_folder').get_identifier().to_str()}",
                f"{EDFVolume(folder='/path/to/my/my_folder', volume_basename='mybasename').get_identifier().to_str()} (if mybasename != folder name)",
            ]
        )

    # implementation of TIFFLikeAccessor

    def read_n_lines_in_file(self, file_name, line_indices) -> tuple:
        reader = _EDFImageWithReadMMap()
        reader.read(file_name)
        volume_shape = self.get_volume_shape()
        result = []
        for line in line_indices:
            data = reader.read_mmap(
                file_name,
                coords=(
                    slice(0, volume_shape[1]),
                    slice(line, line + 1),
                ),
            ).ravel()
            if data is None:
                # an error might have occur ('fast_read_roi' only accept un-compressed). In this case try the 'good old' .data directly which is safer
                data = reader.data[:, line]
            result.append(data)
        return tuple(result)

    def read_n_columns_in_file(self, file_name, column_indices) -> tuple:
        image = fabio.open(file_name)
        volume_shape = self.get_volume_shape()
        result = []
        for column in column_indices:
            data = image.fast_read_roi(
                file_name,
                coords=[
                    slice(column, column + 1),
                    slice(0, volume_shape[2]),
                ],
            ).ravel()

            if data is None:
                # an error might have occur ('fast_read_roi' only accept un-compressed). In this case try the 'good old' .data directly which is safer
                data = image.data[column,]
            result.append(data)
        return tuple(result)

    def read_file(self, file_name) -> tuple:
        return fabio.open(file_name).data


class _EDFImageWithReadMMap(fabio.edfimage.EdfImage):

    def read_mmap(self, fname: str, coords: tuple) -> numpy.ndarray:

        if len(coords) == 4:
            slice1 = self.make_slice(coords)  # and fix that FIXME ...
        elif (
            len(coords) == 2
            and isinstance(coords[0], slice)
            and isinstance(coords[1], slice)
        ):
            slice1 = coords
        else:
            _logger.warning(
                "readROI: Unable to understand Region Of Interest: got %s", coords
            )
            return
        with open(fname, "rb") as fin:
            fin.seek(0)
            count = self.shape[0] * self.shape[1]
            offset = self._frames[self.currentframe].start
            nbytes = self.bpp * count
            with mmap.mmap(
                fin.fileno(), offset + nbytes, access=mmap.ACCESS_READ
            ) as mem:
                buf = numpy.frombuffer(
                    mem, offset=offset, count=count, dtype=self.bytecode
                )
                buf.shape = self.shape
                ret = buf[slice1].copy()
                del buf
        if self.swap_needed():
            ret.byteswap(True)
        return ret
