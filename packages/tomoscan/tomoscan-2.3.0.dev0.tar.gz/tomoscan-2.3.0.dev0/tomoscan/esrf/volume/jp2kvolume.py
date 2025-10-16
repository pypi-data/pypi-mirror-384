# coding: utf-8
"""module defining utils for a jp2k volume"""

from __future__ import annotations

import logging
import os

import numpy
from packaging.version import parse as parse_version
from silx.io.url import DataUrl

from tomoscan.esrf.identifier.jp2kidentifier import JP2KVolumeIdentifier
from tomoscan.scanbase import TomoScanBase
from tomoscan.utils import docstring
from tomoscan.utils.volume import rescale_data

from .singleframebase import VolumeSingleFrameBase

try:
    import glymur  # noqa #F401 needed for later possible lazy loading
except ImportError:
    has_glymur = False
    has_minimal_openjpeg = False
    glymur_version = None
    openjpeg_version = None
else:
    has_glymur = True
    from glymur import set_option as glymur_set_option
    from glymur.version import openjpeg_version
    from glymur.version import version as glymur_version

    if openjpeg_version < "2.3.0":
        has_minimal_openjpeg = False
    else:
        has_minimal_openjpeg = True

_logger = logging.getLogger(__name__)

_MISSING_GLYMUR_MSG = "Fail to import glymur. won't be able to load / save volume to jp2k. You can install it by calling pip."

__all__ = [
    "JP2KVolume",
    "has_glymur",
    "has_minimal_openjpeg",
    "glymur_version",
    "openjpeg_version",
    "get_available_threads",
]


class JP2KVolume(VolumeSingleFrameBase):
    """
    Save volume data to single frame jp2k files and metadata to .txt file

    :param cratios: list of ints. compression ratio for each jpeg2000 layer
    :param psnr: list of int.
                                The PSNR (Peak Signal-to-Noise ratio) for each jpeg2000 layer.
                                This defines a quality metric for lossy compression.
                                The number "0" stands for lossless compression.
    :param n_threads: number of thread to use for writing. If None will try to get as much as possible
    :param clip_values: optional tuple of two float (min, max) to clamp volume value
    :param rescale_data: rescale data before dumping each frame. Expected to be True when dump a new volume and False
                              when save volume cast for example (and when histogram is know...)

    :warning: each file saved under {volume_basename}_{index_zfill6}.jp2k is considered to be a slice of the volume.
    """

    DEFAULT_DATA_EXTENSION = "jp2"

    DEFAULT_DATA_SCHEME = "glymur"

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
        start_index=0,
        data_extension=DEFAULT_DATA_EXTENSION,
        metadata_extension=VolumeSingleFrameBase.DEFAULT_METADATA_EXTENSION,
        cratios: list | None = None,
        psnr: list | None = None,
        n_threads: int | None = None,
        clip_values: tuple | None = None,
        rescale_data: bool = True,
    ) -> None:
        if folder is not None:
            url = DataUrl(
                file_path=str(folder),
                data_path=None,
            )
        else:
            url = None
        super().__init__(
            url=url,
            data=data,
            volume_basename=volume_basename,
            source_scan=source_scan,
            metadata=metadata,
            data_url=data_url,
            metadata_url=metadata_url,
            overwrite=overwrite,
            start_index=start_index,
            data_extension=data_extension,
            metadata_extension=metadata_extension,
        )
        if not has_glymur:
            _logger.warning(_MISSING_GLYMUR_MSG)
        else:
            if not has_minimal_openjpeg:
                _logger.warning(
                    "You must have at least version 2.3.0 of OpenJPEG "
                    "in order to write jp2k images."
                )
        self._cratios = cratios
        self._psnr = psnr
        self._clip_values = None
        self._cast_already_logged = False
        """bool used to avoid logging potential data cast for each frame when save a volume"""
        self._rescale_data = rescale_data
        """should we rescale data before dumping the frame"""
        self.setup_multithread_encoding(n_threads=n_threads)
        self.clip_values = clip_values  # execute test about the type...

    @property
    def cratios(self) -> list | None:
        return self._cratios

    @cratios.setter
    def cratios(self, cratios: list | None):
        self._cratios = cratios

    @property
    def psnr(self) -> list | None:
        return self._psnr

    @psnr.setter
    def psnr(self, psnr: list | None):
        self._psnr = psnr

    @property
    def rescale_data(self) -> bool:
        return self._rescale_data

    @rescale_data.setter
    def rescale_data(self, rescale: bool) -> None:
        if not isinstance(rescale, bool):
            raise TypeError
        self._rescale_data = rescale

    @property
    def clip_values(self) -> tuple | None:
        """
        :return: optional min and max value to clip - as float.
        """
        return self._clip_values

    @clip_values.setter
    def clip_values(self, values: tuple | None) -> None:
        if values is None:
            self._clip_values = None
        elif not isinstance(values, (tuple, list)):
            raise TypeError
        elif not len(values) == 2:
            raise ValueError("clip values are expected to be two floats")
        elif not values[1] >= values[0]:
            raise ValueError
        else:
            self._clip_values = values

    @docstring(VolumeSingleFrameBase)
    def save_data(self, url: DataUrl | None = None) -> None:
        self._cast_already_logged = False
        super().save_data(url=url)

    @docstring(VolumeSingleFrameBase)
    def save_frame(self, frame, file_name, scheme):
        if not has_glymur:
            raise RuntimeError(_MISSING_GLYMUR_MSG)

        expected_output_dtype = frame.dtype
        if self.clip_values is not None:
            frame = numpy.clip(frame, self.clip_values[0], self.clip_values[1])
        if expected_output_dtype not in (numpy.uint8, numpy.uint16):
            _logger.info(
                f"{self.get_identifier().to_str()} get {frame.dtype}. Cast it as {numpy.uint16}"
            )
            expected_output_dtype = numpy.uint16
        if self.rescale_data:
            max_uint = numpy.iinfo(expected_output_dtype).max
            frame = rescale_data(
                data=frame,
                new_min=0,
                new_max=max_uint,
                data_min=self.clip_values[0] if self.clip_values is not None else None,
                data_max=self.clip_values[1] if self.clip_values is not None else None,
            )
        frame = frame.astype(expected_output_dtype)

        if scheme == "glymur":
            glymur.Jp2k(file_name, data=frame, psnr=self.psnr, cratios=self.cratios)
        else:
            raise ValueError(f"Scheme {scheme} is not handled")

    @docstring(VolumeSingleFrameBase)
    def load_frame(self, file_name, scheme):
        if not has_glymur:
            raise RuntimeError(_MISSING_GLYMUR_MSG)

        if scheme == "glymur":
            jp2_file = glymur.Jp2k(file_name)
            return jp2_file[:]
        else:
            raise ValueError(f"Scheme {scheme} is not handled")

    @staticmethod
    def setup_multithread_encoding(
        n_threads: int | None = None, what_if_not_available: str = "ignore"
    ):
        """
        Setup OpenJpeg multi-threaded encoding.

        :param n_threads: Number of threads. If not provided, all available threads are used.
        :param what_if_not_available: What to do if requirements are not fulfilled. Possible values are:
            - "ignore": do nothing, proceed
            - "print": show an information message
            - "raise": raise an error

        """
        required_glymur_version = "0.9.3"
        required_openjpeg_version = "2.4.0"

        def not_available(msg):
            if what_if_not_available == "raise":
                raise ValueError(msg)
            elif what_if_not_available == "print":
                print(msg)

        if not has_glymur:
            not_available(f"glymur not installed. {required_glymur_version} required")
            return
        elif parse_version(glymur_version) < parse_version(required_glymur_version):
            not_available(
                f"glymur >= {required_glymur_version} is required for multi-threaded encoding (current version: {glymur_version})"
            )
            return
        elif not has_minimal_openjpeg:
            not_available(
                f"libopenjpeg >= {required_openjpeg_version} is required for multi-threaded encoding (current version: {openjpeg_version})"
            )
            return

        if n_threads is None:
            n_threads = get_available_threads()
        glymur_set_option("lib.num_threads", n_threads)

    @staticmethod
    @docstring(VolumeSingleFrameBase)
    def from_identifier(identifier):
        """Return the Dataset from a identifier"""
        if not isinstance(identifier, JP2KVolumeIdentifier):
            raise TypeError(
                f"identifier should be an instance of {JP2KVolumeIdentifier}"
            )
        return JP2KVolume(
            folder=identifier.folder,
            volume_basename=identifier.file_prefix,
        )

    @docstring(VolumeSingleFrameBase)
    def get_identifier(self) -> JP2KVolumeIdentifier:
        if self.url is None:
            raise ValueError("no file_path provided. Cannot provide an identifier")
        return JP2KVolumeIdentifier(
            object=self, folder=self.url.file_path(), file_prefix=self._volume_basename
        )

    @staticmethod
    def example_defined_from_str_identifier() -> str:
        return " ; ".join(
            [
                f"{JP2KVolume(folder='/path/to/my/my_folder').get_identifier().to_str()}",
                f"{JP2KVolume(folder='/path/to/my/my_folder', volume_basename='mybasename').get_identifier().to_str()} (if mybasename != folder name)",
            ]
        )


def get_available_threads():
    return len(os.sched_getaffinity(0))
