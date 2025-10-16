# coding: utf-8
"""module defining utils for an hdf5 volume"""

from __future__ import annotations

import logging
import os

import h5py
import numpy
from silx.io.dictdump import dicttonx, nxtodict
from silx.io.url import DataUrl
from silx.io.utils import open as open_hdf5

from tomoscan.utils.io import deprecated_warning
from tomoscan.esrf.identifier.hdf5Identifier import HDF5VolumeIdentifier
from tomoscan.scanbase import TomoScanBase
from tomoscan.utils import docstring
from tomoscan.volumebase import VolumeBase, SliceTuple

_logger = logging.getLogger(__name__)

__all__ = ["HDF5Volume", "get_default_data_path_for_volume"]


class HDF5Volume(VolumeBase):
    """
    Volume where both data and metadata are store in a HDF5 file but at a different location.
    """

    DATA_DATASET_NAME = "results/data"
    METADATA_GROUP_NAME = "configuration"

    def __init__(
        self,
        file_path: str | None = None,
        data_path: str | None = None,
        data: numpy.ndarray | None = None,
        source_scan: TomoScanBase | None = None,
        metadata: dict | None = None,
        data_url: DataUrl | None = None,
        metadata_url: DataUrl | None = None,
        overwrite: bool = False,
    ) -> None:
        url = self._get_url_from_file_path_data_path(
            file_path=file_path, data_path=data_path
        )

        self._file_path = file_path
        self._data_path = data_path
        super().__init__(
            url=url,
            data=data,
            source_scan=source_scan,
            metadata=metadata,
            data_url=data_url,
            metadata_url=metadata_url,
            overwrite=overwrite,
        )

    @property
    def data_extension(self) -> None | str:
        if self.data_url is not None and self.data_url.file_path() is not None:
            _, extension = os.path.splitext(self.data_url.file_path())
            if extension:
                return extension[1:]

    @property
    def metadata_extension(self) -> None | str:
        if self.metadata_url is not None and self.metadata_url.file_path() is not None:
            _, extension = os.path.splitext(self.metadata_url.file_path())
            if extension:
                return extension[1:]

    @staticmethod
    def _get_url_from_file_path_data_path(
        file_path: str | None, data_path: str | None
    ) -> DataUrl | None:
        if file_path is not None and data_path is not None:
            return DataUrl(file_path=file_path, data_path=data_path, scheme="silx")
        else:
            return None

    @VolumeBase.data.setter
    def data(self, data):
        if not isinstance(data, (numpy.ndarray, type(None), h5py.VirtualLayout)):
            raise TypeError(
                f"data is expected to be None or a numpy array not {type(data)}"
            )
        if isinstance(data, numpy.ndarray) and data.ndim != 3:
            raise ValueError(f"data is expected to be 3D and not {data.ndim}D.")
        self._data = data

    @property
    def file_path(self):
        return self._file_path

    @file_path.setter
    def file_path(self, file_path: str | None):
        if not (file_path is None or isinstance(file_path, str)):
            raise TypeError
        self._file_path = file_path
        self.url = self._get_url_from_file_path_data_path(
            self.file_path, self.data_path
        )

    @property
    def data_path(self):
        return self._data_path

    @data_path.setter
    def data_path(self, data_path: str | None):
        if not (data_path is None or isinstance(data_path, str)):
            raise TypeError
        self._data_path = data_path
        self.url = self._get_url_from_file_path_data_path(
            self.file_path, self.data_path
        )

    @docstring(VolumeBase)
    def deduce_data_and_metadata_urls(self, url: DataUrl | None) -> tuple:
        if url is None:
            return None, None
        else:
            if url.data_slice() is not None:
                raise ValueError(f"data_slice is not handled by the {HDF5Volume}")
            file_path = url.file_path()
            data_path = url.data_path()
            if data_path is None:
                raise ValueError(
                    "data_path not provided from the DataUrl. Please provide one."
                )
            scheme = url.scheme() or "silx"
            return (
                # data url
                DataUrl(
                    file_path=file_path,
                    data_path="/".join([data_path, self.DATA_DATASET_NAME]),
                    scheme=scheme,
                ),
                # medata url
                DataUrl(
                    file_path=file_path,
                    data_path="/".join([data_path, self.METADATA_GROUP_NAME]),
                    scheme=scheme,
                ),
            )

    @docstring(VolumeBase)
    def save_data(self, url: DataUrl | None = None, mode="a", **kwargs) -> None:
        """
        :raises KeyError: if data path already exists and overwrite set to False
        :raises ValueError: if data is None
        """
        # to be discussed. Not sure we should raise an error in this case. Could be usefull but this could also be double edged knife
        if self.data is None:
            raise ValueError("No data to be saved")
        url = url or self.data_url
        if url is None:
            raise ValueError(
                "Cannot get data_url. An url should be provided. Don't know where to save this."
            )
        else:
            _logger.info(f"save data to {url.path()}")

        if url.file_path() is not None and os.path.dirname(url.file_path()) != "":
            os.makedirs(os.path.dirname(url.file_path()), exist_ok=True)
        with h5py.File(url.file_path(), mode=mode) as h5s:
            if url.data_path() in h5s:
                if self.overwrite:
                    _logger.debug(
                        f"overwrite requested. Will remove {url.data_path()} entry"
                    )
                    del h5s[url.data_path()]
                else:
                    raise OSError(
                        f"Unable to save data to {url.data_path()}. This path already exists in {url.file_path()}. If you want you can ask to overwrite it."
                    )
            if isinstance(self.data, h5py.VirtualLayout):
                h5s.create_virtual_dataset(name=url.data_path(), layout=self.data)
            else:
                h5s.create_dataset(url.data_path(), data=self.data, **kwargs)

    @docstring(VolumeBase)
    def data_file_saver_generator(
        self, n_frames, data_url: DataUrl, overwrite: bool, mode: str = "a", **kwargs
    ):
        """
        warning: the file will be open until the generator exists
        """

        class _FrameDumper:
            """
            will not work for VirtualLayout
            """

            Dataset = None
            # shared dataset

            def __init__(
                self,
                root_group,
                data_path,
                create_dataset,
                n_frames,
                i_frame,
                overwrite,
                mode,
            ) -> None:
                self.data_path = data_path
                self.root_group = root_group
                self.create_dataset = create_dataset
                self.n_frames = n_frames
                self.mode = mode
                self.overwrite = overwrite
                self.i_frame = i_frame
                self.__kwargs = kwargs  # keep chunk arguments for example

            def __setitem__(self, key, value):
                frame = value
                if _FrameDumper.Dataset is None:
                    if self.data_path in self.root_group:
                        if self.overwrite:
                            _logger.debug(
                                f"overwrite requested. Will remove {data_url.data_path()} entry"
                            )
                            del h5s[data_url.data_path()]
                        else:
                            raise OSError(
                                f"Unable to save data to {data_url.data_path()}. This path already exists in {data_url.file_path()}. If you want you can ask to overwrite it."
                            )

                    _FrameDumper.Dataset = h5s.create_dataset(  # pylint: disable=E1137
                        name=data_url.data_path(),
                        shape=(n_frames, frame.shape[0], frame.shape[1]),
                        dtype=frame.dtype,
                        **self.__kwargs,
                    )
                if key != slice(None, None, None):
                    raise ValueError("item setting only handle ':' for now")
                _FrameDumper.Dataset[i_frame] = frame  # pylint: disable=E1137

        if (
            data_url.file_path() is not None
            and os.path.dirname(data_url.file_path()) != ""
        ):
            os.makedirs(os.path.dirname(data_url.file_path()), exist_ok=True)
        with h5py.File(data_url.file_path(), mode=mode) as h5s:
            for i_frame in range(n_frames):
                yield _FrameDumper(
                    create_dataset=i_frame == 0,
                    data_path=data_url.data_path(),
                    root_group=h5s,
                    n_frames=n_frames,
                    i_frame=i_frame,
                    overwrite=overwrite,
                    mode=mode,
                )

    @docstring(VolumeBase)
    def save_metadata(self, url: DataUrl | None = None) -> None:
        """
        :raises KeyError: if data path already exists and overwrite set to False
        :raises ValueError: if data is None
        """
        if self.metadata is None:
            raise ValueError("No metadata to be saved")
        url = url or self.metadata_url
        if url is None:
            raise ValueError(
                "Cannot get metadata_url. An url should be provided. Don't know where to save this."
            )
        else:
            _logger.info(f"save metadata to {url.path()}")

        if url.file_path() is not None and os.path.dirname(url.file_path()) != "":
            os.makedirs(os.path.dirname(url.file_path()), exist_ok=True)

        dicttonx(
            self.metadata,
            h5file=url.file_path(),
            h5path=url.data_path(),
            update_mode="replace",
            mode="a",
        )

    @docstring(VolumeBase)
    def load_data(
        self, url: DataUrl | None = None, store: bool = True
    ) -> numpy.ndarray:
        url = url or self.data_url
        if url is None:
            raise ValueError(
                "Cannot get data_url. An url should be provided. Don't know where to save this."
            )

        with open_hdf5(filename=url.file_path()) as h5s:
            if url.data_path() in h5s:
                data = h5s[url.data_path()][()]
            else:
                raise KeyError(f"Data path {url.data_path()} not found.")

        if store:
            self.data = data

        return data

    def get_slice(
        self,
        index: int | str = None,
        axis=None,
        xy=None,
        xz=None,
        yz=None,
        url: DataUrl | None = None,
    ):
        if xy is yz is xz is None and (index is None or axis is None):
            raise ValueError("index and axis should be provided")
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
        elif xz is not None:
            deprecated_warning(
                type_="parameter",
                name="xz",
                replacement="axis and index",
            )
            if axis is None and index is None:
                axis = 1
                index = xz
            else:
                raise ValueError("several axis (previously xy, xz, yz requested")
        elif yz is not None:
            deprecated_warning(
                type_="parameter",
                name="yz",
                replacement="axis and index",
            )
            if axis is None and index is None:
                axis = 2
                index = yz
            else:
                raise ValueError("several axis (previously xy, xz, yz requested")

        if isinstance(index, str):
            if index == "first":
                index = 0
            elif index == "middle":
                index = self.get_volume_shape()[axis] // 2
            elif index == "last":
                index = -1
            else:
                raise ValueError(f"index '{index}' is not handled")

        if self.data is not None:
            return self.select(volume=self.data, axis=axis, index=index)
        else:
            url = url or self.data_url
            if url is None:
                raise ValueError(
                    "Cannot get data_url. An url should be provided. Don't know where to save this."
                )
            with open_hdf5(filename=url.file_path()) as h5s:
                if url.data_path() in h5s:
                    return self.select(
                        volume=h5s[url.data_path()], axis=axis, index=index
                    )
                else:
                    raise KeyError(f"Data path {url.data_path()} not found.")

    def _get_slices_from_disk(
        self, slices: tuple[SliceTuple], url: DataUrl | None = None
    ) -> dict[SliceTuple, numpy.ndarray]:
        """
        read from files a couple of slices along any axis.
        """
        url = url or self.data_url
        with open_hdf5(filename=url.file_path()) as h5s:
            if url.data_path() in h5s:
                return self.select_slices(volume=h5s[url.data_path()], slices=slices)

    @docstring(VolumeBase)
    def load_metadata(self, url: DataUrl | None = None, store: bool = True) -> dict:
        url = url or self.metadata_url
        if url is None:
            raise ValueError(
                "Cannot get metadata_url. An url should be provided. Don't know where to save this."
            )
        try:
            metadata = nxtodict(
                h5file=url.file_path(), path=url.data_path(), asarray=False
            )
        except KeyError:
            _logger.warning(f"no metadata found in {url.data_path()}")
            metadata = {}
        if store:
            self.metadata = metadata
        return metadata

    def browse_metadata_files(self, url=None):
        """
        return a generator go through all the existings files associated to the data volume
        """
        url = url or self.metadata_url
        if url is None:
            return
        elif url.file_path() is not None and os.path.exists(url.file_path()):
            yield url.file_path()

    def browse_data_files(self, url=None):
        """
        return a generator go through all the existings files associated to the data volume
        """
        url = url or self.data_url
        if url is None:
            return
        elif url.file_path() is not None and os.path.exists(url.file_path()):
            yield url.file_path()

    def browse_data_urls(self, url=None):
        url = url or self.data_url
        if url is not None and os.path.exists(url.file_path()):
            yield url

    @staticmethod
    @docstring(VolumeBase)
    def from_identifier(identifier):
        """Return the Dataset from a identifier"""
        if not isinstance(identifier, HDF5VolumeIdentifier):
            raise TypeError(
                f"identifier should be an instance of {HDF5VolumeIdentifier}"
            )
        return HDF5Volume(
            file_path=identifier.file_path,
            data_path=identifier.data_path,
        )

    @docstring(VolumeBase)
    def get_identifier(self) -> HDF5VolumeIdentifier:
        if self.url is None:
            raise ValueError("no file_path provided. Cannot provide an identifier")
        return HDF5VolumeIdentifier(
            object=self, hdf5_file=self.url.file_path(), entry=self.url.data_path()
        )

    @staticmethod
    def example_defined_from_str_identifier() -> str:
        return (
            HDF5Volume(file_path="/path/to/file_path", data_path="entry0000")
            .get_identifier()
            .to_str()
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
                    "No data and data_url know and no url provided. Uanble to browse slices"
                )
            with open_hdf5(filename=url.file_path()) as h5s:
                if url.data_path() in h5s:
                    for data_slice in h5s[url.data_path()]:
                        yield data_slice
                else:
                    raise KeyError(f"Data path {url.data_path()} not found.")

    @docstring(VolumeBase)
    def load_chunk(self, chunk, url=None):
        url = url or self.data_url
        if url is None:
            raise ValueError("Cannot get data_url. An url should be provided.")
        with open_hdf5(filename=url.file_path()) as h5s:
            if url.data_path() in h5s:
                return h5s[url.data_path()][chunk]
            else:
                raise KeyError(f"Data path {url.data_path()} not found.")

    def get_volume_shape(self, url=None):
        if self.data is not None:
            return self.data.shape
        url = url or self.data_url
        if url is None:
            raise ValueError("Cannot get data_url. An url should be provided.")
        else:
            with open_hdf5(filename=url.file_path()) as h5s:
                if url.data_path() in h5s:
                    return h5s[url.data_path()].shape
                else:
                    return None


def get_default_data_path_for_volume(scan: TomoScanBase) -> str:
    if not isinstance(scan, TomoScanBase):
        raise TypeError(
            f"scan is expected to be an instance of {TomoScanBase} not {type(scan)}"
        )
    entry = getattr(scan, "entry", "entry")
    return "/".join([entry, "reconstruction"])
