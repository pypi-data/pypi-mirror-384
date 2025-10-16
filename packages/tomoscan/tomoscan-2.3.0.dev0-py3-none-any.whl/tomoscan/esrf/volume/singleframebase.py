# coding: utf-8
"""module defining utils for a jp2k volume"""
from __future__ import annotations

from __future__ import annotations

import logging
import os
import re

import numpy
from silx.io.dictdump import dicttoini
from silx.io.dictdump import load as load_ini
from silx.io.url import DataUrl

from tomoscan.scanbase import TomoScanBase
from tomoscan.utils import docstring
from tomoscan.volumebase import VolumeBase, SliceTuple
from tomoscan.io import cast_to_default_types
from tomoscan.utils.io import deprecated_warning

_logger = logging.getLogger(__name__)


__all__ = ["VolumeSingleFrameBase", "TIFFLikeDiskAccessor"]


class VolumeSingleFrameBase(VolumeBase):
    """
    Base class for Volume where each slice is saved in a separate file like edf, jp2k or tiff.

    :param start_index: users can provide a shift on fill name when saving the file. This is interesting if you want to create
                        create a volume from several writer.
    """

    DEFAULT_DATA_SCHEME = None

    DEFAULT_DATA_PATH_PATTERN = "{volume_basename}_{index_zfill6}.{data_extension}"

    DEFAULT_METADATA_EXTENSION = "txt"

    # information regarding metadata
    DEFAULT_METADATA_SCHEME = "ini"

    DEFAULT_METADATA_PATH_PATTERN = "{volume_basename}_infos.{metadata_extension}"

    def __init__(
        self,
        url: DataUrl | None = None,
        data: numpy.ndarray | None = None,
        source_scan: TomoScanBase | None = None,
        metadata: dict | None = None,
        data_url: DataUrl | None = None,
        metadata_url: DataUrl | None = None,
        overwrite: bool = False,
        start_index: int = 0,
        volume_basename: str | None = None,
        data_extension=None,
        metadata_extension="txt",
    ) -> None:
        self._volume_basename = volume_basename
        super().__init__(
            url,
            data,
            source_scan,
            metadata,
            data_url,
            metadata_url,
            overwrite,
            data_extension,
            metadata_extension,
        )
        self._start_index = start_index
        self._skip_existing_data_files_removal = False

    def get_first_file(self):
        try:
            first_file = next(self.browse_data_files())
        except StopIteration:
            first_file = None
        return first_file

    def get_file_slice_index(self, filename):
        if (
            self.DEFAULT_DATA_PATH_PATTERN
            != VolumeSingleFrameBase.DEFAULT_DATA_PATH_PATTERN
        ):
            raise ValueError("Non-default file name pattern not handled")
        return int(filename.split(".")[0].split("_")[-1])

    @property
    def start_index(self) -> int:
        return self._start_index

    @start_index.setter
    def start_index(self, start_idx: int) -> None:
        self._start_index = start_idx

    def get_volume_basename(self, url=None):
        if self._volume_basename is not None:
            return self._volume_basename
        else:
            url = url or self.data_url
            return os.path.basename(url.file_path())

    @property
    def skip_existing_data_files_removal(self) -> bool:
        """The loading of the volume for single frame base is done by loading all the file
        contained in a folder data_url.file_path(). When saving the data we make sure there is no 'remaining' of
        any previous saving by using the file pattern.
        But when we want to save a volume from several thread (one thread save the n first frame, second the n next frame ...) this
        could be a limitation.
        So in this case we can use the 'ignore_existing_files' that will avoid calling '_remove_existing_data_files'
        """
        return self._skip_existing_data_files_removal

    @skip_existing_data_files_removal.setter
    def skip_existing_data_files_removal(self, ignore: bool) -> None:
        if not isinstance(ignore, bool):
            raise TypeError(f"ignore should be a bool. Got {type(ignore)}")
        self._skip_existing_data_files_removal = ignore

    @docstring(VolumeBase)
    def deduce_data_and_metadata_urls(self, url: DataUrl | None) -> tuple:
        """
        Deduce automatically data and metadata url.
        Default data will be saved as single frame edf.
        Default metadata will be saved as a text file
        """
        if url is None:
            return None, None
        else:
            metadata_keywords = {
                "volume_basename": self.get_volume_basename(url),
                "metadata_extension": self.metadata_extension,
            }
            metadata_data_path = self.DEFAULT_METADATA_PATH_PATTERN.format(
                **metadata_keywords
            )

            return (
                # data url
                DataUrl(
                    file_path=url.file_path(),
                    data_path=self.DEFAULT_DATA_PATH_PATTERN,
                    scheme=url.scheme() or self.DEFAULT_DATA_SCHEME,
                    data_slice=url.data_slice(),
                ),
                # medata url
                DataUrl(
                    file_path=url.file_path(),
                    data_path=metadata_data_path,
                    scheme=url.scheme() or self.DEFAULT_METADATA_SCHEME,
                ),
            )

    @docstring(VolumeBase)
    def load_metadata(self, url: DataUrl | None = None, store: bool = True) -> dict:
        url = url or self.metadata_url
        if url is None:
            raise ValueError(
                "Cannot get metadata_url. An url should be provided. Don't know where to save this."
            )
        if url.scheme() == "ini":
            metadata_file = url.file_path()
            if url.data_path() is not None:
                metadata_file = os.path.join(metadata_file, url.data_path())
                _logger.info(f"load data to {metadata_file}")
            try:
                metadata = load_ini(metadata_file, "ini")
            except FileNotFoundError:
                _logger.warning(
                    f"unable to load metadata from {metadata_file} - File not found"
                )
                metadata = {}
            except Exception as e:
                _logger.error(
                    f"Failed to load metadata from {metadata_file}. Error is {e}"
                )
                metadata = {}
        else:
            raise ValueError(f"scheme {url.scheme()} is not handled")

        if store:
            self.metadata = metadata
        return metadata

    @docstring(VolumeBase)
    def save_metadata(self, url: DataUrl | None = None) -> None:
        if self.metadata is None:
            raise ValueError("No data to be saved")
        url = url or self.metadata_url
        if url is None:
            raise ValueError(
                "Cannot get metadata_url. An url should be provided. Don't know where to save this."
            )
        else:
            if url.scheme() == "ini":
                metadata_file = url.file_path()
                if url.data_path() is not None:
                    metadata_file = os.path.join(metadata_file, url.data_path())
                    _logger.info(f"save data to {metadata_file}")
                    if len(self.metadata) > 0:
                        metadata = cast_to_default_types(self.metadata)
                        dicttoini(metadata, metadata_file)
            else:
                raise ValueError(f"scheme {url.scheme()} is not handled")

    # utils to format file path

    def format_data_path_for_data(
        self, data_path: str, index: int, volume_basename: str
    ) -> str:
        """
        Return file path to save the frame at `index` of the current volume
        """
        keywords = {
            "index_zfill4": str(index + self.start_index).zfill(4),
            "index_zfill6": str(index + self.start_index).zfill(6),
            "volume_basename": volume_basename,
            "data_extension": self.data_extension,
        }
        return data_path.format(**keywords)

    def get_data_path_pattern_for_data(
        self, data_path: str, volume_basename: str
    ) -> str:
        """
        Return file path **pattern** (and not full path) to  load data.
        For example in edf it can return 'myacquisition_*.edf' in order to be handled by
        """
        keywords = {
            "index_zfill4": "[0-9]{3,4}",
            "index_zfill6": "[0-9]{3,6}",
            "volume_basename": volume_basename,
            "data_extension": self.data_extension,
        }
        return data_path.format(**keywords)

    def remove_existing_data_files(self, url: DataUrl | None = None) -> None:
        """Clean any existing files (if overwrite and rights) that must be used for saving"""
        url = url or self.data_url
        if not os.path.exists(url.file_path()):
            return

        research_pattern = self.get_data_path_pattern_for_data(
            data_path=url.data_path(),
            volume_basename=self.get_volume_basename(url=url),
        )
        try:
            research_pattern = re.compile(research_pattern)
        except Exception:
            _logger.error(
                f"Fail to compute regular expression for {research_pattern}. Unable to load data"
            )
            return None
        for file_ in sorted(os.listdir(url.file_path())):
            if research_pattern.match(file_):
                full_file_path = os.path.join(url.file_path(), file_)
                if self.overwrite:
                    os.remove(full_file_path)
                else:
                    raise OSError(
                        f"Output file '{full_file_path}' already exists. No overwrite required. Skip writting"
                    )

    @docstring(VolumeBase)
    def save_data(self, url: DataUrl | None = None) -> None:
        if self.data is None:
            raise ValueError("No data to be saved")
        url = url or self.data_url
        if url is None:
            raise ValueError(
                "Cannot get data_url. An url should be provided. Don't know where to save this."
            )
        else:
            if not self.skip_existing_data_files_removal:
                self.remove_existing_data_files(url=url)

            _logger.info(f"save data to {url.path()}")
            # if necessary create output directory (some third part writer does not do it for us)
            try:
                os.makedirs(url.file_path(), exist_ok=True)
            except FileNotFoundError:
                # can raise FileNotFoundError if file path is '.' for example
                pass

            assert self.data.ndim == 3
            for frame, frame_dumper in zip(
                self.data,
                self.data_file_saver_generator(
                    n_frames=self.data.shape[0], data_url=url, overwrite=self.overwrite
                ),
            ):
                frame_dumper[:] = frame

    def data_file_name_generator(self, n_frames, data_url):
        """
        browse output files for n_frames
        """
        for i_frame in range(n_frames):
            file_name = self.format_data_path_for_data(
                data_url.data_path(),
                index=i_frame,
                volume_basename=self.get_volume_basename(data_url),
            )
            file_name = os.path.join(data_url.file_path(), file_name)
            yield file_name

    @docstring(VolumeBase)
    def data_file_saver_generator(self, n_frames, data_url: DataUrl, overwrite: bool):
        class _FrameDumper:
            def __init__(self, url_scheme, file_name, callback) -> None:
                self.url_scheme = url_scheme
                self.file_name = file_name
                self.overwrite = overwrite
                self.__callback = callback

            def __setitem__(self, key, value):
                if not self.overwrite and os.path.exists(self.file_name):
                    raise OSError(
                        f"{self.file_name} already exists. If you want you can ask for the volume to overwriting existing files."
                    )
                if key != slice(None, None, None):
                    raise ValueError("item setting only handle ':' for now")
                self.__callback(
                    frame=value, file_name=self.file_name, scheme=self.url_scheme
                )

        os.makedirs(data_url.file_path(), exist_ok=True)
        for file_name in self.data_file_name_generator(
            n_frames=n_frames, data_url=data_url
        ):
            yield _FrameDumper(
                file_name=file_name,
                url_scheme=data_url.scheme(),
                callback=self.save_frame,
            )

    def get_volume_shape(self, url=None):
        if self.data is not None:
            return self.data.shape
        else:
            first_slice = next(self.browse_slices(url=url))
            n_slices = len(tuple(self.browse_data_urls()))
            return n_slices, first_slice.shape[0], first_slice.shape[1]

    @docstring(VolumeBase)
    def load_data(
        self, url: DataUrl | None = None, store: bool = True
    ) -> numpy.ndarray:
        url = url or self.data_url
        if url is None:
            raise ValueError(
                "Cannot get data_url. An url should be provided. Don't know where to save this."
            )
        data = list(self.browse_slices(url=url))

        if data == []:
            data = None
            _logger.warning(
                f"Failed to load any data for {self.get_identifier().short_description}"
            )
        else:
            data = numpy.asarray(data)
            if data.ndim != 3:
                raise ValueError(f"data is expected to be 3D not {data.ndim}.")

        if store:
            self.data = data

        return data

    def _read_frame_from_fast_axis(self, index: int, url: DataUrl) -> numpy.ndarray:
        """
        Read a single frame along the 'fast axis' (0 aka Z).
        Raise "IndexError if not accessible
        """
        data_files = tuple(self.browse_data_files())
        file_path = data_files[index]
        return self.load_frame(file_name=file_path, scheme=url.scheme())

    def get_slice(
        self,
        index: int | str = None,
        axis=None,
        xy=None,
        xz=None,
        yz=None,
        url: DataUrl | None = None,
    ):
        # if we are on the 'fast' read axis then we can directly read a single file. Else we must fall back on the default reading mechanism
        if axis == 0 or xy is not None:
            if xy is not None:
                deprecated_warning(
                    type_="parameter",
                    name="xy",
                    replacement="axis and index",
                )
                if axis is None and index is None:
                    axis = 0
                    index = xy
                else:
                    raise ValueError("several axis (previously xy, xz, yz requested")
            return self._read_frame_from_fast_axis(
                index=index, url=(url or self.data_url)
            )
        else:
            return super().get_slice(index=index, axis=axis, xy=xy, xz=xz, yz=yz)

    def save_frame(self, frame: numpy.ndarray, file_name: str, scheme: str):
        """
        Function dedicated for volune saving each frame on a single file

        :param frame: frame to be save
        :param file_name: path to store the data
        :param scheme: scheme to save the data
        """
        raise NotImplementedError("Base class")

    def load_frame(self, file_name: str, scheme: str) -> numpy.ndarray:
        """
        Function dedicated for volume saving each frame on a single file

        :param file_name: path to store the data
        :param scheme: scheme to save the data
        """
        raise NotImplementedError("Base class")

    @docstring(VolumeBase)
    def browse_metadata_files(self, url=None):
        url = url or self.metadata_url
        if url is None:
            return
        elif url.file_path() is not None:
            if url.scheme() == "ini":
                metadata_file = url.file_path()
                if url.data_path() is not None:
                    metadata_file = os.path.join(metadata_file, url.data_path())
                    if os.path.exists(metadata_file):
                        yield metadata_file
            else:
                raise ValueError(f"scheme {url.scheme()} is not handled")

    @docstring(VolumeBase)
    def browse_data_files(self, url=None):
        url = url or self.data_url
        if url is None:
            return
        research_pattern = self.get_data_path_pattern_for_data(
            url.data_path(), volume_basename=self.get_volume_basename(url)
        )
        try:
            research_pattern = re.compile(research_pattern)
        except Exception:
            _logger.error(
                f"Fail to compute regular expression for {research_pattern}. Unable to load data"
            )
            return None

        # use case of a single file
        if not os.path.exists(url.file_path()):
            return
        elif os.path.isfile(url.file_path()):
            yield url.file_path()
        else:
            for file_ in sorted(os.listdir(url.file_path())):
                if research_pattern.match(file_):
                    full_file_path = os.path.join(url.file_path(), file_)
                    yield full_file_path

    @docstring(VolumeBase)
    def browse_data_urls(self, url=None):
        url = url or self.data_url
        for data_file in self.browse_data_files(url=url):
            yield DataUrl(
                file_path=data_file,
                scheme=url.scheme(),
            )

    @docstring(VolumeBase)
    def browse_slices(self, url=None):
        if url is None and self.data is not None:
            for data_slice in self.data:
                yield data_slice
        else:
            url = url or self.data_url
            if url is None:
                raise ValueError(
                    "No data and data_url know and no url provided. Unable to browse slices"
                )

            for file_path in self.browse_data_files(url=url):
                yield self.load_frame(file_name=file_path, scheme=url.scheme())


class TIFFLikeDiskAccessor:
    """
    Class to define a common implementation of '_get_slices_from_disk' for 'tiff like' format (!!! single frame per file !!!).
    (format unable to implement 'read_n_lines_in_file', 'read_n_columns_in_file' and 'read_file' functions

    .. warning:: a class that want to inherit from TIFFLikeDiskAccessor should also inherit from VolumeSingleFrameBase.
        a separated class has been created instead of a direct inheritance to clearly separate the '_get_slices_from_disk' instantiation
    """

    def _get_slices_from_disk(
        self, slices: tuple[SliceTuple], url: DataUrl | None = None
    ) -> dict[SliceTuple, numpy.ndarray]:

        _logger.debug("Try to read %s from disk", slices)
        volume_shape = self.get_volume_shape()  # pylint: disable=E1101
        _logger.debug("volume shape is %s", volume_shape)

        def get_output_slice_shape(axis):
            if axis == 0:
                return (volume_shape[1], volume_shape[2])
            elif axis == 1:
                return (volume_shape[0], volume_shape[2])
            elif axis == 2:
                return (volume_shape[0], volume_shape[1])
            else:
                raise ValueError(f"unknown requested axis ({axis})")

        # init resulting data
        result = {
            slice_: numpy.empty(shape=get_output_slice_shape(slice_.axis))
            for slice_ in slices
        }
        _logger.debug(
            "Reserve numpy arrays for reading %s",
            {slice_: (data.shape, data.dtype) for (slice_, data) in result.items()},
        )
        from tomoscan.esrf.volume.utils import (
            group_slices_by_axis,
        )  # avoid cyclic import

        indices_to_read_per_axis: dict[int, set[int]] = group_slices_by_axis(
            slices=slices, volume_shape=volume_shape
        )
        _logger.debug("slices ordered by axis %s", indices_to_read_per_axis)

        for i_axis_0, file_name in enumerate(
            self.browse_data_files()  # pylint: disable=E1101
        ):
            # browse all files. Each file represent a slice along the axis 0
            data_cache = None
            # used to cache data in the case a full slice
            # needs to be read along axis 0. Then we can reuse it for over axis

            # handle axis 0
            if i_axis_0 in indices_to_read_per_axis[0]:
                data_cache = self.read_file(file_name=file_name)
                result[(0, i_axis_0)][:] = data_cache
                indices_to_read_per_axis[0].remove(i_axis_0)

            # test: if all slices are read avoid going through all the slices
            if numpy.sum([len(indices_to_read_per_axis[i]) for i in range(3)]) == 0:
                break

            # if data has been read already let's benefit from it
            if data_cache is not None:
                for index in indices_to_read_per_axis[1]:
                    result[(1, index)][i_axis_0:] = data_cache[index, :]
                for index in indices_to_read_per_axis[2]:
                    result[(2, index)][i_axis_0, :] = data_cache[:, index]
            else:
                # else read lines and / or columns directly
                if len(indices_to_read_per_axis[1]) > 0:
                    data = self.read_n_columns_in_file(
                        file_name=file_name, column_indices=indices_to_read_per_axis[1]
                    )
                    assert len(data) == len(indices_to_read_per_axis[1])
                    for column, index in zip(data, indices_to_read_per_axis[1]):
                        result[(1, index)][i_axis_0, :] = column

                if len(indices_to_read_per_axis[2]) > 0:
                    data = self.read_n_lines_in_file(
                        file_name=file_name, line_indices=indices_to_read_per_axis[2]
                    )
                    assert len(data) == len(indices_to_read_per_axis[2])
                    for line, index in zip(data, indices_to_read_per_axis[2]):
                        result[(2, index)][i_axis_0, :] = line

        return result

    def read_n_lines_in_file(self, file_name, line_indices) -> tuple:
        raise NotImplementedError("Base class")

    def read_n_columns_in_file(self, file_name, column_indices) -> tuple:
        raise NotImplementedError("Base class")

    def read_file(self, file_name) -> tuple:
        raise NotImplementedError("Base class")
