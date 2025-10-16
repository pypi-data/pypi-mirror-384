# coding: utf-8

"""module to define base class for a volume"""

from __future__ import annotations

import pint
from typing import NamedTuple
import logging
import numpy
from silx.io.url import DataUrl
from silx.math.combo import (  # pylint: disable=E0611 (not found from the pyx file)
    min_max,
)

from tomoscan.utils.io import deprecated, deprecated_warning
from tomoscan.identifier import VolumeIdentifier
from tomoscan.scanbase import TomoScanBase
from tomoscan.tomoobject import TomoObject
from tomoscan.utils import BoundingBox1D, BoundingBox3D
from tomoscan.utils import drac as drac_utils

_ureg = pint.get_application_registry()
_logger = logging.getLogger(__name__)


__all__ = ["SliceTuple", "VolumeBase"]


class SliceTuple(NamedTuple):
    axis: int
    index: int


class VolumeBase(TomoObject):
    """
    context: we aim at having a common way of saving and loading volumes through the tomotools suite.
    The goal is to aim handling of volumes when creating them or doing some operations with those like stitching...

    :param url: url of the volume. Could be path to a master file if we can provide one per each volume. Otherwise could be a pattern of edf files or tiff file with a data range
    :param source_scan: potential instance of TomoScanBase in order to get extra information. This could be saved in the volume file to (external link)
    :param data: volume data. Expected to be 3D
    :param metadata: metadata associated to the volume. Must be a dict of serializable object
    :param data_url: url to save the data. If provided url must not be provided. If an object is constructed from data and metadata url then no rule to create a VolumeIdentifier can be created and call to et_identifier will raise an error.
    :param metadata_url: url to save the metadata. If provided url must not be provided. If an object is constructed from data and metadata url then no rule to create a VolumeIdentifier can be created and call to et_identifier will raise an error.
    :param overwrite: when save the data if encounter a resource already existing overwrite it (if True) or not.
    :param overwrite: when save the data if encounter a resource already existing overwrite it (if True) or not.

    :raises TypeError:
    :raises ValueError: * if data is a numpy array and not 3D.
    :raises OSError:
    """

    EXTENSION = None

    def __init__(
        self,
        url: DataUrl | None = None,
        data: numpy.ndarray | None = None,
        source_scan: TomoScanBase | None = None,
        metadata: dict | None = None,
        data_url: DataUrl | None = None,
        metadata_url: DataUrl | None = None,
        overwrite: bool = False,
        data_extension: str | None = None,
        metadata_extension: str | None = None,
    ) -> None:
        super().__init__()
        if url is not None and (data_url is not None or metadata_url is not None):
            raise ValueError(
                "Either url or (data_url and / or metadata_url) can be provided not both"
            )

        # warning on source_scan: should be defined before the url because deduce_data_and_metadata_urls might need it
        # Then as source scan can imply several modification of url... we can only define it during construction and this
        # must not involve with object life
        if not isinstance(source_scan, (TomoScanBase, type(None))):
            raise TypeError(
                f"source scan is expected to be None or an instance of TomoScanBase. Not {type(source_scan)}"
            )
        self.__source_scan = source_scan
        self._data_extension = data_extension
        self._metadata_extension = metadata_extension

        self.overwrite = overwrite
        self.url = url
        self.metadata = metadata
        self.data = data

        if url is None:
            self._data_url = data_url
            self._metadata_url = metadata_url
        else:
            # otherwise have be set from call to 'deduce_data_and_metadata_urls'
            pass

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, url: DataUrl | None) -> None:
        if url is not None and not isinstance(url, DataUrl):
            raise TypeError
        self._url = url
        self._data_url, self._metadata_url = self.deduce_data_and_metadata_urls(url)

    def deduce_data_and_metadata_urls(self, url: DataUrl | None) -> tuple:
        """
        compute data and metadata urls from 'parent url'
        :return: data_url: DataUrl | None, metadata_url: DataUrl | None
        """
        raise NotImplementedError("Base class")

    @property
    def data_extension(self):
        return self._data_extension

    @property
    def metadata_extension(self):
        return self._metadata_extension

    @property
    def data_url(self):
        return self._data_url

    @property
    def metadata_url(self):
        return self._metadata_url

    @property
    def data(self) -> numpy.ndarray | None:
        return self._data

    @data.setter
    def data(self, data):
        if not isinstance(data, (numpy.ndarray, type(None))):
            raise TypeError(
                f"data is expected to be None or a numpy array not {type(data)}"
            )
        if isinstance(data, numpy.ndarray) and data.ndim != 3:
            raise ValueError(f"data is expected to be 3D and not {data.ndim}D.")
        self._data = data

    def get_slice(
        self,
        index: str | int = None,
        axis=None,
        xy=None,
        xz=None,
        yz=None,
        url: DataUrl | None = None,
    ) -> None | numpy.ndarray:
        "read a single slice of the volume"
        if xy is yz is xz is axis is None:
            raise ValueError("axis should be provided")

        if self.data is None:
            self.load_data(url=url, store=True)

        if isinstance(index, str):
            if index == "middle":
                index = self.get_volume_shape()[axis] // 2
            elif index == "first":
                index = 0
            elif index == "last":
                index = -1

        if self.data is not None:
            return self.select(
                volume=self.data, xy=xy, xz=xz, yz=yz, axis=axis, index=index
            )
        else:
            return None

    def get_slices(
        self, slices: tuple[SliceTuple | tuple]
    ) -> dict[SliceTuple, numpy.ndarray]:
        """
        retrieve a couple of slices along any axis:

        For example, if you want to retrieve slice number 2 of axis 0 and slice number 56 of axis 1:

        .. code-block:: python

            slices = volume.get_slices(
                (0, 2),
                (1, 56),
            )
            for (axis, slice), data in slices:
                ...
        """
        if not isinstance(slices, tuple):
            raise TypeError(f"slices should be a tuple. Got {type(slices)}")
        for elmt in slices:
            if not isinstance(elmt, (tuple, NamedTuple)):
                raise TypeError(
                    f"slices is expected to be a tuple of tuple or a tuple of SliceTuple. Get {type(elmt)} as an element of the tuple"
                )

        # cast 2 element tuple to SliceTuple
        slices = tuple([SliceTuple(*slice_) for slice_ in slices])
        if self.data is not None:
            return self.select_slices(volume=self.data, slices=slices)
        else:
            return self._get_slices_from_disk(slices=slices)

    def _get_slices_from_disk(
        self, slices: tuple[SliceTuple], url: DataUrl | None = None
    ) -> dict[SliceTuple, numpy.ndarray]:
        """
        read from files a couple of slices along any axis.
        """

        data = self.load_data(url=url, store=False)
        if data is None:
            raise RuntimeError(
                f"Enable to load data from disk for {self.get_identifier()}"
            )
        return self.select_slices(volume=data, slices=slices)

    @property
    def metadata(self) -> dict | None:
        return self._metadata

    @metadata.setter
    def metadata(self, metadata: dict | None):
        if not isinstance(metadata, (dict, type(None))):
            raise TypeError(
                f"metadata is expected to be None or a dict not {type(metadata)}"
            )
        self._metadata = metadata

    @staticmethod
    def example_defined_from_str_identifier() -> str:
        """example as string to explain how users can defined identifiers from a string"""
        raise NotImplementedError("Base class")

    def clear_cache(self):
        """remove object stored in data and metadata"""
        self.data = None
        self.metadata = None

    # generic function requested
    @property
    def source_scan(self) -> TomoScanBase | None:
        return self.__source_scan

    @property
    def overwrite(self) -> bool:
        return self._overwrite

    @overwrite.setter
    def overwrite(self, overwrite: bool) -> None:
        if not isinstance(overwrite, bool):
            raise TypeError
        self._overwrite = overwrite

    # function to be loaded to an url
    @staticmethod
    def from_identifier(identifier: str | VolumeIdentifier):
        """Return the Dataset from a identifier"""
        raise NotImplementedError("Base class")

    def get_identifier(self) -> VolumeIdentifier:
        """dataset unique identifier. Can be for example a hdf5 and
        en entry from which the dataset can be rebuild"""
        raise NotImplementedError("Base class")

    # utils required for operations like stitching

    @staticmethod
    def _insure_reconstruction_dict_exists(ddict):
        if "processing_options" not in ddict:
            ddict["processing_options"] = {}
        if "reconstruction" not in ddict["processing_options"]:
            ddict["processing_options"]["reconstruction"] = {}

    @property
    def position(self) -> tuple | None:
        """position are provided as a tuple using the same reference for axis as the volume data.
        position is returned as (axis_0_pos, axis_1_pos, axis_2_pos). Can also be see as (z_position, y_position, x_position)
        """
        metadata = self.metadata or self.load_metadata()
        position = (
            metadata.get("processing_options", {})
            .get("reconstruction", {})
            .get("position", None)
        )
        if position is None:
            return None
        else:
            return tuple(position)

    @position.setter
    def position(self, position) -> None:
        if self.metadata is None:
            self.metadata = {}
        self._insure_reconstruction_dict_exists(self.metadata)
        self.metadata["processing_options"]["reconstruction"]["position"] = numpy.array(
            position
        )

    @property
    @deprecated(replacement="voxel_size", since_version="1.3.0")
    def pixel_size(self):
        return self.voxel_size

    @pixel_size.setter
    @deprecated(replacement="voxel_size", since_version="1.3.0")
    def pixel_size(self, pixel_size) -> None:
        if numpy.isscalar(pixel_size):
            pixel_size = [pixel_size] * 3
            _logger.warning(
                "pixel_size is expected to be a tuple. Conversion will be removed soon. Please update your code"
            )
        self.voxel_size = pixel_size

    @property
    def voxel_size(self) -> tuple[float] | None:
        """
        voxel size as (axis 0 dim - aka z, axis 1 dim - aka y, axis 2 dim aka z)
        Returned in meter
        """
        metadata = self.metadata or self.load_metadata()

        voxel_size = (
            metadata.get("processing_options", {})
            .get("reconstruction", {})
            .get("voxel_size_cm", None)
        )
        if voxel_size is None:
            # ensure backward compatibility with old volumes (before nabu 2023.1)
            # try fall back on pixel_size_cm for old volumes
            voxel_size = (
                metadata.get("processing_options", {})
                .get("reconstruction", {})
                .get("pixel_size_cm", None)
            )

        if voxel_size is not None:
            if numpy.isscalar(voxel_size):
                # be safer and handle the case voxel size is a scalar
                voxel_size = [voxel_size] * 3
            # voxel are in cm -> convert them to meter
            voxel_size = (voxel_size * _ureg.centimeter).to(_ureg.meter).magnitude
            # convert to float
            return tuple([float(value) for value in voxel_size])
        return None

    @voxel_size.setter
    def voxel_size(self, voxel_size: tuple) -> None:
        if self.metadata is None:
            self.metadata = {}
        if numpy.isscalar(voxel_size):
            raise TypeError("voxel is expected to be a tuple of three values")
        self._insure_reconstruction_dict_exists(self.metadata)
        voxel_size_m = voxel_size * _ureg.meter
        voxel_size_cm = voxel_size_m.to(_ureg.centimeter)
        self.metadata["processing_options"]["reconstruction"]["voxel_size_cm"] = (
            numpy.array(voxel_size_cm.magnitude)
        )

    def get_volume_shape(self, url=None) -> tuple:
        """return volume shape as a tuple"""
        raise NotImplementedError("Base class")

    def get_bounding_box(self, axis: str | int | None = None):
        if axis is None:
            x_bb = self.get_bounding_box(axis=2)
            y_bb = self.get_bounding_box(axis=1)
            z_bb = self.get_bounding_box(axis=0)
            return BoundingBox3D(
                (z_bb.min, y_bb.min, x_bb.min),
                (z_bb.max, y_bb.max, x_bb.max),
            )

        position = self.position
        shape = self.get_volume_shape()
        # TODO: does it make sense that pixel size is a scalar ?
        voxel_size = self.voxel_size
        missing = []
        if position is None:
            missing.append("position")
        if shape is None:
            missing.append("shape")
            raise ValueError("Unable to find volume shape")
        if voxel_size is None:
            missing.append("pixel_size")

        if len(missing) > 0:
            raise ValueError(
                f"Unable to get bounding box. Missing information: {'; '.join(missing)}"
            )
        assert axis is not None
        if isinstance(axis, str):
            if axis == "x":
                axis = 2
            elif axis == "y":
                axis = 1
            elif axis == "z":
                axis = 0
            else:
                raise ValueError(f"axis '{axis}' is not handled")
        min_pos_in_meter = position[axis] - voxel_size[axis] * shape[axis] / 2.0
        max_pos_in_meter = position[axis] + voxel_size[axis] * shape[axis] / 2.0
        return BoundingBox1D(min_pos_in_meter, max_pos_in_meter)

    def get_min_max(self) -> tuple:
        """
        compute min max of the volume. Can take some time but avoid to load the full volume in memory
        """
        if self.data is not None:
            return self.data.min(), self.data.max()
        else:
            min_v, max_v = None, None
            for s in self.browse_slices():
                min_v = min(min_v, s.min()) if min_v is not None else s.min()
                max_v = max(max_v, s.max()) if max_v is not None else s.max()
            return min_v, max_v

    # load / save stuff

    @property
    def extension(self) -> str:
        return self.EXTENSION

    def load(self):
        self.load_metadata(store=True)
        # always load metadata first because we might expect to get some information from
        # it in order to load data next
        self.load_data(store=True)

    def save(self, url: DataUrl | None = None, **kwargs):
        """save volume data and metadata to disk"""
        if url is not None:
            data_url, metadata_url = self.deduce_data_and_metadata_urls(url=url)
        else:
            data_url = self.data_url
            metadata_url = self.metadata_url
        self.save_data(data_url, **kwargs)
        if self.metadata is not None:
            # a volume is not force to have metadata to save. But calling save_metadata direclty might raise an error
            # if no metadata found
            self.save_metadata(metadata_url)

    def save_data(self, url: DataUrl | None = None, **kwargs) -> None:
        """
        save data to the provided url or existing one if none is provided
        """
        raise NotImplementedError("Base class")

    def save_metadata(self, url: DataUrl | None = None) -> None:
        """
        save metadata to the provided url or existing one if none is provided
        """
        raise NotImplementedError("Base class")

    def load_data(
        self, url: DataUrl | None = None, store: bool = True
    ) -> numpy.ndarray:
        """load volume data from disk"""
        raise NotImplementedError("Base class")

    def load_metadata(self, url: DataUrl | None = None, store: bool = True) -> dict:
        """load volume metadata from disk"""
        raise NotImplementedError("Base class")

    def check_can_provide_identifier(self):
        if self.url is None:
            raise ValueError(
                "Unable to provide an identifier. No url has been provided"
            )

    @staticmethod
    def select_slices(volume: numpy.ndarray, slices: tuple[SliceTuple]) -> dict:
        return {
            SliceTuple(axis=slice_.axis, index=slice_.index): VolumeBase.select(
                volume=volume, index=slice_.index, axis=slice_.axis
            )
            for slice_ in slices
        }

    @staticmethod
    def select(
        volume: numpy.ndarray,
        xy: int | None = None,
        xz: int | None = None,
        yz: int | None = None,
        axis: int | None = None,
        index: int | None = None,
    ) -> numpy.array:
        """
        select a slice at 'index' along an axis (axis)
        """
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

        if not volume.ndim == 3:
            raise TypeError(f"volume is expected to be 3D. {volume.ndim}D provided")
        if axis == 0:
            return volume[index]
        elif axis == 1:
            return volume[:, index]
        elif axis == 2:
            return volume[:, :, index]
        else:
            raise ValueError(f"axis {axis} is not handled")

    def browse_data_files(self, url=None):
        """
        :param url: data url. If not provided will take self.data_url

        return a generator go through all the existing files associated to the data volume
        """
        raise NotImplementedError("Base class")

    def browse_metadata_files(self, url=None):
        """
        :param url: metadata url. If not provided will take self.metadata_url

        return a generator go through all the existing files associated to the data volume
        """
        raise NotImplementedError("Base class")

    def browse_data_urls(self, url=None):
        """
        generator on data urls used.

        :param url: data url to be used. If not provided will take self.data_url
        """
        raise NotImplementedError("Base class")

    def browse_slices(self, url=None):
        """
        generator of 2D numpy array representing a slice

        :param url: data url to be used. If not provided will browse self.data if exists else self.data_url
        :warning: this will get the slice from the data on disk and never use `data` property.
                  so before browsing slices you might want to check if data is already loaded
        """
        raise NotImplementedError("Base class")

    def load_chunk(self, chunk, url=None):
        """
        Load a sub-volume.

        :param chunk: tuple of slice objects indicating which chunk of the volume has to be loaded.
        :param url: data url to be used. If not provided will take self.data_url
        """
        raise NotImplementedError("Base class")

    def get_min_max_values(self, url=None) -> tuple:
        """
        compute min max over 'data' if exists else browsing the volume slice by slice

        :param url: data url to be used. If not provided will take self.data_url
        """
        min_v = None
        max_v = None
        if self.data is not None:
            data = self.data
        else:
            data = self.browse_slices(url=url)
        for data_slice in data:
            if min_v is None:
                min_v = data_slice.min()
                max_v = data_slice.max()
            else:
                min_lv, max_lv = min_max(data_slice, finite=True)
                min_v = min(min_v, min_lv)
                max_v = max(max_v, max_lv)
        return min_v, max_v

    def data_file_saver_generator(self, n_frames, data_url: DataUrl, overwrite: bool):
        """
        Provide a helper class to dump data frame by frame. For know the only possible interaction is
        Helper[:] = frame

        :param n_frames: number of frame the final volume will contain
        :param DataUrl data_url: url to dump data
        :param overwrite: overwrite existing file ?
        """
        raise NotImplementedError("Base class")

    def build_drac_metadata(self) -> dict:
        """
        build the drac (successor of icat) metadata dict from existing volume metadata.
        """
        metadata = self.metadata or self.load_metadata()
        flatten_metadata = drac_utils.flatten_vol_metadata(metadata)
        icat_metadata = drac_utils.map_nabu_keys_to_drac(flatten_metadata)
        return icat_metadata
