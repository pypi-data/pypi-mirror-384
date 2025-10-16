# coding: utf-8
"""This modules contains base class for TomoScanBase"""

from __future__ import annotations

import pint
import logging
import os
import pathlib
from bisect import bisect_left
from collections import OrderedDict
from math import ceil
from typing import Iterable
import warnings

import fabio
import h5py
import numpy
import silx.io.utils
from silx.io.url import DataUrl
from silx.io.utils import get_data
from silx.io.utils import open as hdf5_open
from tomoscan.utils.io import deprecated, deprecated_warning
from tomoscan.framereducer.ReduceFrameSaver import ReduceFrameSaver

from tomoscan.identifier import ScanIdentifier
from tomoscan.normalization import IntensityNormalization
from tomoscan.normalization import Method as _IntensityMethod
from tomoscan.normalization import normalize_chebyshev_2D, normalize_lsqr_spline_2D
from tomoscan.framereducer.reducedframesinfos import ReducedFramesInfos

from .progress import Progress
from .tomoobject import TomoObject
from .source import *  # noqa F401

_ureg = pint.get_application_registry()
_logger = logging.getLogger(__name__)

__all__ = [
    "TomoScanBase",
    "projections_angles_to_indices",
    "projection_angular_range_to_indices",
]


class TomoScanBase(TomoObject):
    """
    Base Class representing a scan.
    It is used to obtain core information regarding an acquisition like
    projections, dark and flat field...

    :param scan: path to the root folder containing the scan.
    """

    DICT_TYPE_KEY = "type"

    DICT_PATH_KEY = "path"

    _SCHEME = None
    """scheme to read data url for this type of acquisition"""

    FRAME_REDUCER_CLASS = None
    """Frame reducer class to be use in order to compute reduced darks and reduced flats"""

    def __init__(
        self,
        scan: str | None,
        type_: str,
        ignore_projections: Iterable | None = None,
    ):
        super().__init__()
        self.path = scan
        self._type = type_
        self._reduced_flats = None
        """darks once reduced. We must have one per s. When set a dict is expected with index as the key
           and median or median of darks series as value"""
        self._reduced_flats_infos = ReducedFramesInfos()

        self._reduced_darks = None
        """flats once reduced.  We must have one per series. When set a dict is expected with index as the key
           and median or median of darks series as value"""
        self._reduced_darks_infos = ReducedFramesInfos()

        self._notify_ffc_rsc_missing = True
        """Should we notify the user if ffc fails because cannot find dark or
        flat. Used to avoid several warnings. Only display one"""
        self._projections = None
        self._alignment_projections = None
        self._flats_weights = None
        """list flats indexes to use for flat field correction and associate
        weights"""
        self._ignore_projections = ignore_projections
        self._configure_ignore_projections()
        """Extra information for normalization"""
        self._intensity_monitor = None
        """monitor of the intensity during acquisition. Can be a diode
        for example"""
        self._source = None
        self._intensity_normalization = IntensityNormalization()
        """Extra information for normalization"""
        self._machine_current = None
        self._count_time = None
        self._sample_detector_distance = None
        self._source_sample_distance = None
        self._propagation_distance: float | None = None
        self._source_type = None
        self._source_name = None
        self._instrument_name = None
        self._title = None

    def clear_cache(self):
        """clear caches. Might be call if some data changed after
        first read of data or metadata"""
        self._notify_ffc_rsc_missing = True
        self._source_type = None
        self._source_name = None
        self._instrument_name = None
        self._title = None
        self._sample_detector_distance = None
        self._source_sample_distance = None
        self._propagation_distance: float | None = None
        self.clear_frames_cache()

    @deprecated(replacement="clear_cache", since_version="2.2", reason="renaming")
    def clear_caches(self) -> None:
        self.clear_cache()

    def clear_frames_cache(self):
        self._alignment_projections = None
        self._flats_weights = None
        self._projections = None

    @deprecated(
        replacement="clear_frames_cache", since_version="2.2", reason="renaming"
    )
    def clear_frames_caches(self) -> None:
        self.clear_frames_cache()

    def _configure_ignore_projections(self):
        if self._ignore_projections is None:
            return
        usage_msg = (
            "Please provide a dictionary in the form {'kind': kind, 'values': values}"
        )
        if not (isinstance(self._ignore_projections, dict)):
            deprecated_warning(
                type_="Function",
                name="_configure_ignore_projections",
                reason=usage_msg,
                since_version="2.0.6",
            )
            self._ignore_projections = {
                "kind": "indices",
                "values": self._ignore_projections,
            }
        # Assuming dict from now on
        ignore_projections = self._ignore_projections
        if (
            "kind" not in ignore_projections
            or "values" not in ignore_projections
            or ignore_projections["kind"] not in ["indices", "angles", "range"]
        ):
            raise ValueError(usage_msg)
        if ignore_projections["kind"] == "indices" and numpy.array(
            ignore_projections["values"]
        ).dtype.kind not in ["u", "i"]:
            raise ValueError("Expected integer numbers for indices")

    @property
    def ignore_projections(self):
        return self._ignore_projections

    @ignore_projections.setter
    def ignore_projections(self, val):
        raise ValueError(
            "ignore_projections should not be modified after class initialization"
        )

    def get_ignored_projection_indices(self):
        if self.ignore_projections is None:
            return []
        ignore_kind = self.ignore_projections["kind"]
        if ignore_kind == "indices":
            return self.ignore_projections["values"]
        else:
            return self._get_excluded_projections_from_angles(ignore_kind)

    def _get_excluded_projections_from_angles(self, kind):
        if kind == "angles":
            mapping_func = projections_angles_to_indices
        elif kind == "range":
            mapping_func = projection_angular_range_to_indices
        else:
            raise ValueError
        projections_indices, rotation_angles = self._get_projs_indices_and_angles()
        return mapping_func(
            self.ignore_projections["values"], projections_indices, rotation_angles
        )

    def _get_projs_indices_and_angles(self):
        raise NotImplementedError("Base class")

    @property
    def reduced_darks(self):
        return self._reduced_darks

    def set_reduced_darks(
        self, darks, darks_infos: ReducedFramesInfos | dict | None = None
    ):
        self._reduced_darks = darks
        self.reduced_darks_infos = darks_infos

    @property
    def reduced_flats(self):
        return self._reduced_flats

    def set_reduced_flats(
        self, flats, flats_infos: ReducedFramesInfos | dict | None = None
    ):
        self._reduced_flats = flats
        self.reduced_flats_infos = flats_infos

    @property
    def reduced_darks_infos(self):
        return self._reduced_darks_infos

    @reduced_darks_infos.setter
    def reduced_darks_infos(self, infos: ReducedFramesInfos | dict | None):
        if infos is None:
            self._reduced_darks_infos.clear()
        elif isinstance(infos, ReducedFramesInfos):
            self._reduced_darks_infos = infos
        elif isinstance(infos, dict):
            self._reduced_darks_infos.load_from_dict(dict)
        else:
            raise TypeError

    @property
    def reduced_flats_infos(self):
        return self._reduced_flats_infos

    @reduced_flats_infos.setter
    def reduced_flats_infos(self, infos: ReducedFramesInfos | dict | None):
        if infos is None:
            self._reduced_flats_infos.clear()
        elif isinstance(infos, ReducedFramesInfos):
            self._reduced_flats_infos = infos
        elif isinstance(infos, dict):
            self._reduced_flats_infos.load_from_dict(dict)
        else:
            raise TypeError(f"unexpected error ({type(infos)})")

    @property
    def path(self) -> str | None:
        """

        :return: path of the scan root folder.
        """
        return self._path

    @path.setter
    def path(self, path: str | None) -> None:
        if path is None:
            self._path = path
        else:
            if not isinstance(path, (str, pathlib.Path)):
                raise TypeError(
                    f"path is expected to be a str or a pathlib.Path not {type(path)}"
                )
            self._path = os.path.abspath(str(path))

    @property
    def type(self) -> str:
        """

        :return: type of the scanBase (can be 'edf' or 'hdf5' for now).
        """
        return self._type

    @staticmethod
    def is_tomoscan_dir(directory: str, **kwargs) -> bool:
        """
        Check if the given directory is holding an acquisition

        :param directory:
        :return: does the given directory contains any acquisition
        """
        raise NotImplementedError("Base class")

    def is_abort(self, **kwargs) -> bool:
        """

        :return: True if the acquisition has been abort
        """
        raise NotImplementedError("Base class")

    @property
    def source(self):
        return self._source

    @property
    def flats(self) -> dict | None:
        """list of flats files"""
        return self._flats

    @flats.setter
    def flats(self, flats: dict | None) -> None:
        self._flats = flats

    @property
    def darks(self) -> dict | None:
        """list of darks files"""
        return self._darks

    @darks.setter
    def darks(self, darks: dict | None) -> None:
        self._darks = darks

    @property
    def projections(self) -> dict | None:
        """if found dict of projections urls with index during acquisition as
        key"""
        return self._projections

    @projections.setter
    def projections(self, projections: dict) -> None:
        self._projections = projections

    @property
    def alignment_projections(self) -> dict | None:
        """
        dict of projections made for alignment with acquisition index as key
        None if not found
        """
        return self._alignment_projections

    @alignment_projections.setter
    def alignment_projections(self, alignment_projs):
        self._alignment_projections = alignment_projs

    @property
    def dark_n(self) -> int | None:
        raise NotImplementedError("Base class")

    @property
    def tomo_n(self) -> int | None:
        """number of projection WITHOUT the return projections"""
        raise NotImplementedError("Base class")

    @property
    def flat_n(self) -> int | None:
        """number of flat per series (computed on the first series)"""
        raise NotImplementedError("Base class")

    @property
    def pixel_size(self) -> float | None:
        raise NotImplementedError("Base class")

    @property
    @deprecated(replacement="", since_version="1.1.0")
    def x_real_pixel_size(self) -> float | None:
        raise NotImplementedError("Base class")

    @property
    @deprecated(replacement="", since_version="1.1.0")
    def y_real_pixel_size(self) -> float | None:
        raise NotImplementedError("Base class")

    def get_pixel_size(self, unit="m") -> float | None:
        if self.pixel_size:
            return (self.pixel_size * _ureg.meter).to(unit).magnitude
        else:
            return None

    @property
    def instrument_name(self) -> str | None:
        """

        :return: instrument name
        """
        raise NotImplementedError("Base class")

    @property
    def dim_1(self) -> int | None:
        raise NotImplementedError("Base class")

    @property
    def dim_2(self) -> int | None:
        raise NotImplementedError("Base class")

    @property
    def ff_interval(self) -> int | None:
        raise NotImplementedError("Base class")

    @property
    def scan_range(self) -> int | None:
        raise NotImplementedError("Base class")

    @property
    def energy(self) -> float | None:
        """

        :return: incident beam energy in keV
        """
        raise NotImplementedError("Base class")

    @property
    def intensity_monitor(self):
        raise NotImplementedError("Base class")

    @property
    def sample_detector_distance(self) -> float | None:
        """

        :return: sample / detector distance in meter
        """
        raise NotImplementedError("Base class")

    @property
    @deprecated(replacement="sample_detector_distance", since_version="2.2.0")
    def distance(self) -> float | None:
        return self.sample_detector_distance

    @property
    def source_sample_distance(self) -> float | None:
        """

        :return: source / sample distance (in meter). Expected to be negative (NXtomo convention).
        """
        raise NotImplementedError("Base class")

    @property
    def field_of_view(self):
        """

        :return: field of view of the scan. None if unknown else Full or Half
        """
        raise NotImplementedError("Base class")

    @property
    def estimated_cor_frm_motor(self):
        deprecated_warning(
            type_="property",
            name="estimated_cor_frm_motor",
            replacement="x_rotation_axis_pixel_position",
            since_version="2.1",
        )
        return self.x_rotation_axis_pixel_position

    @property
    def x_rotation_axis_pixel_position(self):
        """

        :return: Estimated center of rotation estimated from motor position. In [-frame_width, +frame_width]. None if unable to find it
        """
        raise NotImplementedError("Base class")

    @property
    def x_translation(self) -> None | tuple:
        raise NotImplementedError("Base class")

    @property
    def y_translation(self) -> None | tuple:
        raise NotImplementedError("Base class")

    @property
    def z_translation(self) -> None | tuple:
        raise NotImplementedError("Base class")

    def get_sample_detector_distance(self, unit="m") -> float | None:
        """

        :param unit: unit requested for the distance
        :return: sample / detector distance with the requested unit
        """
        if self.sample_detector_distance:
            return (self.distance * _ureg.meter).to(unit).magnitude
        else:
            return None

    @deprecated(replacement="get_sample_detector_distance", since_version="2.0.0")
    def get_distance(self, *args, **kwargs):
        return self.get_sample_detector_distance(*args, **kwargs)

    @property
    @deprecated(
        replacement="sample_x_pixel_size", since_version="2.2", reason="renaming"
    )
    def x_pixel_size(self) -> float | None:
        return self.sample_x_pixel_size

    @property
    @deprecated(
        replacement="sample_y_pixel_size", since_version="2.2", reason="renaming"
    )
    def y_pixel_size(self) -> float | None:
        return self.sample_y_pixel_size

    @property
    def sample_x_pixel_size(self) -> float | None:
        raise NotImplementedError("Base class")

    @property
    def sample_y_pixel_size(self) -> float | None:
        raise NotImplementedError("Base class")

    @property
    def detector_x_pixel_size(self) -> float | None:
        raise NotImplementedError("Base class")

    @property
    def detector_y_pixel_size(self) -> float | None:
        raise NotImplementedError("Base class")

    @property
    def magnification(self) -> float | None:
        raise NotImplementedError("Base class")

    def update(self) -> None:
        """Parse the root folder and files to update information"""
        raise NotImplementedError("Base class")

    @property
    def sequence_name(self):
        """Return the sequence name"""
        raise NotImplementedError("Base class")

    @property
    def sample_name(self):
        """Return the sample name"""
        raise NotImplementedError("Base class")

    @property
    def propagation_distance(self) -> float | None:
        raise NotImplementedError("Base class")

    @property
    def group_size(self):
        """Used in the case of z-series for example. Return the number of
        sequence expected on the acquisition"""
        raise NotImplementedError("Base class")

    @property
    def count_time(self) -> list | None:
        raise NotImplementedError("Base class")

    @property
    def electric_current(self) -> tuple:
        warnings.warn(
            "electric_current is deprecated and will be removed in a future version. Use machine_current instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.machine_current

    @electric_current.setter
    def electric_current(self, current: tuple | None) -> None:
        warnings.warn(
            "electric_current is deprecated and will be removed in a future version. Use machine_current instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.machine_current = current

    @property
    def machine_current(self) -> tuple:
        """Return the sample name"""
        raise NotImplementedError("Base class")

    @machine_current.setter
    def machine_current(self, current: tuple | None) -> None:
        if not isinstance(current, (type(None), tuple)):
            raise TypeError(
                f"current is expected to be None or a tuple. Not {type(current)}"
            )
        self._machine_current = current

    @property
    def title(self):
        raise NotImplementedError("Base class")

    @property
    def source_name(self):
        raise NotImplementedError("Base class")

    @property
    def source_type(self):
        raise NotImplementedError("Base class")

    @property
    def x_flipped(self) -> bool:
        """
        warning: deprecated !!!!!
        return True if  the frames are flip through x
        """
        raise NotImplementedError("Base class")

    @property
    def y_flipped(self) -> bool:
        """
        warning: deprecated !!!!!
        return True if  the frames are flip through y
        """
        raise NotImplementedError("Base class")

    def get_x_flipped(self, default=None):
        deprecated_warning(
            type_="property",
            name="get_x_flipped",
            replacement="get_detector_transformations",
            since_version="1.3",
        )
        if self.x_flipped is None:
            return default
        else:
            return self.x_flipped

    def get_y_flipped(self, default=None):
        deprecated_warning(
            type_="property",
            name="get_y_flipped",
            replacement="get_detector_transformations",
            since_version="1.3",
        )
        if self.y_flipped is None:
            return default
        else:
            return self.y_flipped

    @property
    def detector_transformations(self) -> tuple | None:
        """
        return tuple of `Transformation` applied to the detector
        """
        raise NotImplementedError

    def get_detector_transformations(self, default):
        if self.detector_transformations is None:
            return default
        else:
            return self.detector_transformations

    def get_identifier(self) -> ScanIdentifier:
        """
        return the dataset identifier of the scan.
        The identifier is insure to be unique for each scan and
        allow the user to store the scan as a string identifier
        and to retrieve it later from this single identifier.
        """
        raise NotImplementedError("Base class")

    def to_dict(self) -> dict:
        """

        :return: convert the TomoScanBase object to a dictionary.
                 Used to serialize the object for example.
        """
        res = dict()
        res[self.DICT_TYPE_KEY] = self.type
        res[self.DICT_PATH_KEY] = self.path
        return res

    def load_from_dict(self, _dict: dict):
        """
        Load properties contained in the dictionary.

        :param _dict: dictionary to load
        :return: self
        :raises: ValueError if dict is invalid
        """
        raise NotImplementedError("Base class")

    def equal(self, other) -> bool:
        """

        :param instance to compare with
        :return: True if instance are equivalent

        ..note:: we cannot use the __eq__ function because this object need to be
                 picklable
        """
        return (
            isinstance(other, self.__class__)
            or isinstance(self, other.__class__)
            and self.type == other.type
            and self.path == other.path
        )

    def get_proj_angle_url(self) -> dict:
        """
        return a dictionary of all the projection. key is the angle of the
        projection and value is the url.

        Keys are int for 'standard' projections and strings for return
        projections.

        :return: angles as keys, radios as value.
        """
        raise NotImplementedError("Base class")

    @staticmethod
    def map_urls_on_scan_range(urls, n_projection, scan_range) -> dict:
        """
        map given urls to an angle regarding scan_range and number of projection.
        We take the hypothesis that 'extra projection' are taken regarding the
        'id19' policy:

         * If the acquisition has a scan range of 360 then:

            * if 4 extra projection, the angles are (270, 180, 90, 0)

            * if 5 extra projection, the angles are (360, 270, 180, 90, 0)

         * If the acquisition has a scan range of 180 then:

            * if 2 extra projections: the angles are (90, 0)

            * if 3 extra projections: the angles are (180, 90, 0)

        ..warning:: each url should contain only one radio.

        :param urls: dict with all the urls. First url should be
                     the first radio acquire, last url should match the last
                     radio acquire.
        :param n_projection: number of projection for the sample.
        :param scan_range: acquisition range (usually 180 or 360)
        :return: angle in degree as key and url as value

        :raises: ValueError if the number of extra images found and scan_range
                 are incoherent
        """
        assert n_projection is not None
        ordered_url = OrderedDict(sorted(urls.items(), key=lambda x: x))

        res = {}
        # deal with the 'standard' acquisitions
        for proj_i in range(n_projection):
            url = list(ordered_url.values())[proj_i]
            if n_projection == 1:
                angle = 0.0
            else:
                angle = proj_i * scan_range / (n_projection - 1)
            if proj_i < len(urls):
                res[angle] = url

        if len(urls) > n_projection:
            # deal with extra images (used to check if the sampled as moved for
            # example)
            extraImgs = list(ordered_url.keys())[n_projection:]
            if len(extraImgs) in (4, 5):
                if scan_range < 360:
                    _logger.warning(
                        "incoherent data information to retrieve"
                        "scan extra images angle"
                    )
                elif len(extraImgs) == 4:
                    res["270(1)"] = ordered_url[extraImgs[0]]
                    res["180(1)"] = ordered_url[extraImgs[1]]
                    res["90(1)"] = ordered_url[extraImgs[2]]
                    res["0(1)"] = ordered_url[extraImgs[3]]
                else:
                    res["360(1)"] = ordered_url[extraImgs[0]]
                    res["270(1)"] = ordered_url[extraImgs[1]]
                    res["180(1)"] = ordered_url[extraImgs[2]]
                    res["90(1)"] = ordered_url[extraImgs[3]]
                    res["0(1)"] = ordered_url[extraImgs[4]]
            elif len(extraImgs) in (2, 3):
                if scan_range > 180:
                    _logger.warning(
                        "incoherent data information to retrieve"
                        "scan extra images angle"
                    )
                elif len(extraImgs) == 3:
                    res["180(1)"] = ordered_url[extraImgs[0]]
                    res["90(1)"] = ordered_url[extraImgs[1]]
                    res["0(1)"] = ordered_url[extraImgs[2]]
                else:
                    res["90(1)"] = ordered_url[extraImgs[0]]
                    res["0(1)"] = ordered_url[extraImgs[1]]
            elif len(extraImgs) == 1:
                res["0(1)"] = ordered_url[extraImgs[0]]
            else:
                raise ValueError(
                    "incoherent data information to retrieve scan" "extra images angle"
                )
        return res

    @property
    def intensity_normalization(self):
        return self._intensity_normalization

    @intensity_normalization.setter
    def intensity_normalization(self, value):
        try:
            method = _IntensityMethod(value)
        except ValueError:
            pass
        else:
            self._intensity_normalization.method = method

    def get_sinogram(
        self,
        line,
        subsampling=1,
        norm_method: str | None = None,
        **kwargs,
    ):
        """
        extract the sinogram from projections

        :param line: which sinogram we want
        :param subsampling: subsampling to apply. Allows to skip some io

        :return: computed sinogram from projections
        """
        if (
            self.projections is not None
            and self.dim_2 is not None
            and line > self.dim_2
        ) or line < 0:
            raise ValueError(f"requested line {line} is not in the scan")
        if self.projections is not None:
            y_dim = ceil(len(self.projections) / subsampling)
            sinogram = numpy.empty((y_dim, self.dim_1))
            _logger.debug(
                f"compute sinogram for line {line} of {self.path} (subsampling: {subsampling})"
            )
            advancement = Progress(
                name=f"compute sinogram for {os.path.basename(self.path)}, line={line},sampling={subsampling}"
            )
            advancement.setMaxAdvancement(len(self.projections))
            projections = self.projections
            o_keys = list(projections.keys())
            o_keys.sort()
            for i_proj, proj_index in enumerate(o_keys):
                if i_proj % subsampling == 0:
                    proj_url = projections[proj_index]
                    proj = silx.io.utils.get_data(proj_url)
                    proj = self.flat_field_correction(
                        projs=[proj], proj_indexes=[proj_index]
                    )[0]
                    sinogram[i_proj // subsampling] = proj[line]
                advancement.increaseAdvancement(1)

            return self._apply_sino_norm(
                sinogram,
                line=line,
                norm_method=norm_method,
                subsampling=subsampling,
                **kwargs,
            )
        else:
            return None

    def _apply_sino_norm(
        self, sinogram, line, norm_method: _IntensityMethod, subsampling=1, **kwargs
    ) -> numpy.ndarray | None:
        if norm_method is not None:
            norm_method = _IntensityMethod(norm_method)
        if norm_method in (None, _IntensityMethod.NONE):
            return sinogram
        elif norm_method is _IntensityMethod.CHEBYSHEV:
            return normalize_chebyshev_2D(sinogram)
        elif norm_method is _IntensityMethod.LSQR_SPLINE:
            return normalize_lsqr_spline_2D(sinogram)
        elif norm_method in (_IntensityMethod.DIVISION, _IntensityMethod.SUBTRACTION):
            # get intensity factor
            if "value" in kwargs:
                intensities = kwargs["value"]
                _logger.info("Apply sinogram normalization from 'value' key")
            elif "dataset_url" in kwargs:
                _logger.info("Apply sinogram normalization from 'dataset_url' key")
                try:
                    if isinstance(kwargs["dataset_url"], DataUrl):
                        url = kwargs["dataset_url"]
                    else:
                        url = DataUrl(path=kwargs["dataset_url"])
                    intensities = get_data(url)
                except Exception as e:
                    _logger.error(f"Fail to load intensities. Error is {e}")
                    return
            else:
                raise KeyError(
                    f"{norm_method.value} requires a value or an url to be computed"
                )
            if intensities is None:
                raise ValueError("provided normalization intensities is None")

            # apply normalization
            if numpy.isscalar(intensities):
                if norm_method is _IntensityMethod.SUBTRACTION:
                    sinogram = sinogram - intensities
                elif norm_method is _IntensityMethod.DIVISION:
                    sinogram = sinogram / intensities
                else:
                    raise NotImplementedError
            elif not isinstance(intensities, numpy.ndarray):
                raise TypeError(
                    f"intensities is expected to be a numpy array not a ({type(intensities)})"
                )
            elif intensities.ndim == 1:
                # in the case intensities is a 1D array: we expect to have one value per projection
                for sl, value in enumerate(intensities):
                    if norm_method is _IntensityMethod.SUBTRACTION:
                        sinogram[sl] = sinogram[sl] - value
                    elif norm_method is _IntensityMethod.DIVISION:
                        sinogram[sl] = sinogram[sl] / value
            elif intensities.ndim in (2, 3):
                # in the case intensities is a 2D array: we expect to have one array per projection (each line has a value)
                # in the case intensities is a 3D array: we expect to have one frame per projection
                for sl, value in enumerate(intensities):
                    if norm_method is _IntensityMethod.SUBTRACTION:
                        sinogram[sl] = sinogram[sl] - value[line]
                    elif norm_method is _IntensityMethod.DIVISION:
                        sinogram[sl] = sinogram[sl] / value[line]
            else:
                raise ValueError(
                    f"{kwargs['dataset_url']} is expected to be 1D, 2D or 3D"
                )
            return sinogram
        else:
            raise ValueError("norm method not handled", norm_method)

    def _frame_flat_field_correction(
        self,
        data: numpy.ndarray | DataUrl,
        dark,
        flat_weights: dict,
        line: None | int = None,
    ):
        """
        compute flat field correction for a provided data from is index
        one dark and two flats (require also indexes)
        """
        assert isinstance(data, (numpy.ndarray, DataUrl))
        if isinstance(data, DataUrl):
            data = get_data(data)
        can_process = True
        if flat_weights in (None, {}):
            if self._notify_ffc_rsc_missing:
                _logger.error(
                    f"cannot make flat field correction, flat not found from {self} or weights not computed"
                )
            can_process = False
        else:
            for flat_index, _ in flat_weights.items():
                if flat_index not in self.reduced_flats:
                    _logger.error(
                        f"flat {flat_index} has been removed, unable to apply flat field"
                    )
                    can_process = False
                elif (
                    self.reduced_flats is not None
                    and self.reduced_flats[flat_index].ndim != 2
                ):
                    _logger.error(
                        "cannot make flat field correction, flat should be of dimension 2"
                    )
                    can_process = False

        if can_process is False:
            self._notify_ffc_rsc_missing = False
            if line is None:
                return data
            else:
                return data[line]

        if len(flat_weights) == 1:
            flat_value = self.reduced_flats[list(flat_weights.keys())[0]]
        elif len(flat_weights) == 2:
            flat_keys = list(flat_weights.keys())
            flat_1 = flat_keys[0]
            flat_2 = flat_keys[1]
            flat_value = (
                self.reduced_flats[flat_1] * flat_weights[flat_1]
                + self.reduced_flats[flat_2] * flat_weights[flat_2]
            )
        else:
            raise ValueError(
                "no more than two flats are expected and"
                "at least one shuold be provided"
            )
        if line is None:
            assert data.ndim == 2
            div = flat_value - dark
            div[div == 0] = 1.0
            return (data - dark) / div
        else:
            assert data.ndim == 1
            div = flat_value[line] - dark[line]
            div[div == 0] = 1
            return (data - dark[line]) / div

    def flat_field_correction(
        self,
        projs: Iterable,
        proj_indexes: Iterable,
        line: int | None = None,
    ):
        """Apply flat field correction on the given data

        :param Iterable projs: list of projection (numpy array) to apply correction
                              on
        :param Iterable data proj_indexes: list of indexes of the projection in
                                         the acquisition sequence. Values can
                                         be int or None. If None then the
                                         index take will be the one in the
                                         middle of the flats taken.
        :param line: index of the line to apply flat filed. If not provided
                     consider we want to apply flat filed on the entire frame
        :return: corrected data: list of numpy array
        """
        assert isinstance(projs, Iterable)
        assert isinstance(proj_indexes, Iterable)
        assert isinstance(line, (type(None), int))

        def has_missing_keys():
            if proj_indexes is None:
                return False
            for proj_index in proj_indexes:
                if proj_index not in self._flats_weights:
                    return False
            return True

        def return_without_correction():
            def load_data(proj):
                if isinstance(proj, DataUrl):
                    return get_data(proj)
                else:
                    return proj

            if line is not None:
                res = [
                    load_data(proj)[line] if isinstance(proj, DataUrl) else proj
                    for proj in projs
                ]
            else:
                res = [
                    load_data(proj) if isinstance(proj, DataUrl) else proj
                    for proj in projs
                ]

            return res

        if self._flats_weights in (None, {}) or has_missing_keys():
            self._flats_weights = self._get_flats_weights()

        if self._flats_weights in (None, {}):
            if self._notify_ffc_rsc_missing:
                _logger.error("Unable to compute flat weights")
                self._notify_ffc_rsc_missing = False
            return return_without_correction()

        darks = self._reduced_darks
        if darks is not None and len(darks) > 0:
            # take only one dark into account for now
            dark = list(darks.values())[0]
        else:
            dark = None

        if dark is None:
            if self._notify_ffc_rsc_missing:
                _logger.error("cannot make flat field correction, dark not found")
                self._notify_ffc_rsc_missing = False
            return return_without_correction()

        if dark is not None and dark.ndim != 2:
            if self._notify_ffc_rsc_missing:
                _logger.error(
                    "cannot make flat field correction, dark should be of "
                    "dimension 2"
                )
                self._notify_ffc_rsc_missing = False
                return return_without_correction()

        return numpy.array(
            [
                self._frame_flat_field_correction(
                    data=frame,
                    dark=dark,
                    flat_weights=(
                        self._flats_weights[proj_i]
                        if proj_i in self._flats_weights
                        else None
                    ),
                    line=line,
                )
                for frame, proj_i in zip(projs, proj_indexes)
            ]
        )

    def _get_flats_weights(self):
        """compute flats indexes to use and weights for each projection"""
        if self.reduced_flats is None:
            return None
        flats_indexes = sorted(self.reduced_flats.keys())

        def get_weights(proj_index):
            if proj_index in flats_indexes:
                return {proj_index: 1.0}
            pos = bisect_left(flats_indexes, proj_index)
            left_pos = flats_indexes[pos - 1]
            if pos == 0:
                return {flats_indexes[0]: 1.0}
            elif pos > len(flats_indexes) - 1:
                return {flats_indexes[-1]: 1.0}
            else:
                right_pos = flats_indexes[pos]
                delta = right_pos - left_pos
                return {
                    left_pos: 1 - (proj_index - left_pos) / delta,
                    right_pos: 1 - (right_pos - proj_index) / delta,
                }

        if self.reduced_flats is None or len(self.reduced_flats) == 0:
            return {}
        else:
            res = {}
            for proj_index in self.projections:
                res[proj_index] = get_weights(proj_index=proj_index)
            return res

    def get_projections_intensity_monitor(self):
        """return intensity monitor values for projections"""
        raise NotImplementedError("Base class")

    def get_flat_expected_location(self):
        raise NotImplementedError("Base class")

    def get_dark_expected_location(self):
        raise NotImplementedError("Base class")

    def get_projection_expected_location(self):
        raise NotImplementedError("Base class")

    def get_energy_expected_location(self):
        raise NotImplementedError("Base class")

    def get_sample_detector_distance_expected_location(self):
        raise NotImplementedError("Base class")

    def get_pixel_size_expected_location(self):
        raise NotImplementedError("Base class")

    def get_relative_file(self, file_name: str, with_dataset_prefix=True) -> str | None:
        """
        :param file_name: name of the file to create
        :param with_dataset_prefix: If True will prefix the requested file by the dataset name like datasetname_file_name

        :return: path to the requested file according to the 'Scan' / 'dataset' location. Return none if Scan has no path
        """
        raise NotImplementedError("Base class")

    def get_dataset_basename(self) -> str:
        raise NotImplementedError("Base class")

    def _dump_frame_dict(
        self,
        frames: dict[int, numpy.ndarray],
        output_urls,
        frames_metadata: ReducedFramesInfos | None,
        metadata_output_urls: tuple | None,
        overwrite: bool = False,
    ):
        """
        utils function to save some frames in set of output_urls

        Behavior with HDF5: it expects to have a dedicated group where it can save the different frame with indices.
        It will do a first iteration at this group level to remove unused dataset and will overwrite the one he can in order to reduced memory print
        """
        saver = ReduceFrameSaver(
            frames=frames,
            output_urls=[self._format_url(url) for url in output_urls],
            frames_metadata=frames_metadata,
            metadata_output_urls=[
                self._format_url(url) for url in metadata_output_urls
            ],
            overwrite=overwrite,
        )
        saver.save()

    def _format_url(self, url: DataUrl):
        """
        Format an url according to the scan metadata. Solves ''entry' and 'scan_prefix' keywords
        """
        assert isinstance(
            url, DataUrl
        ), f"url should be an instance of {DataUrl}. Got {type(url)}"
        if hasattr(self, "entry"):
            entry = self.entry
        else:
            entry = "entry"

        def format_data_path(data_path) -> str:
            """Format only 'entry' field. This is up to the 'ReduceFrameSaver' to take care of 'index' and 'index_zfill4'"""
            if data_path is not None:
                data_path = data_path.format(
                    entry=entry, index="{index}", index_zfill4="{index_zfill4}"
                )
            return data_path

        def format_file_path(file_path) -> str:
            """Format only 'entry' and 'scan_prefix' field. This is up to the 'ReduceFrameSaver' to take care of 'index' and 'index_zfill4'"""
            if file_path is not None:
                if not os.path.isabs(file_path):
                    if self.path is None:
                        raise ValueError("No dataset path provided")

                    file_path = os.path.join(self.path, file_path)

                file_path = file_path.format(
                    entry=entry,
                    scan_prefix=self.get_dataset_basename(),
                    index="{index}",
                    index_zfill4="{index_zfill4}",
                )
            return file_path

        return DataUrl(
            file_path=format_file_path(url.file_path()),
            data_path=format_data_path(url.data_path()),
            scheme=url.scheme(),
            data_slice=url.data_slice(),
        )

    def _load_frame_dict(
        self, inputs_urls, metadata_input_urls, return_as_url=False
    ) -> dict:
        """
        :note: note on pattern:
            * handled patterns are:
                * file_path pattern:
                    * {index}: only handled for edf files
                    * {index_zfill4}: only handled for edf files
                    * Only one usage of index and index_zfill4 can be done. Having several {index} or one {index} and one {index_zfill4} will fail
                * data_path pattern:
                    * {entry}
                    * {index}: works only if set at the end of the path (as dataset name)
                    * {index_zfill4}: works only if set at the end of the path (as dataset name)
        :return: tuple(frames_data, frames_metadata).
                 * frames_data: dict with frame index in the acquisition sequence as key. Value is the frame as a numpy array if return_as_url is False else this is a DataUrl to the frame
                 * frames_metadata: return an instance of ReducedFramesInfos. We consider this is too small to use the DataUrl mecanism when return_as_url set to True
        """
        from tomoscan.esrf.scan.utils import (
            get_files_from_pattern,
        )  # avoid cyclic import

        if self.path is None:
            raise ValueError("No dataset path provided")

        res_data = {}
        entry = "entry"
        if hasattr(self, "entry"):
            entry = self.entry

        res_metadata = ReducedFramesInfos()

        # load frames infos
        for url in inputs_urls:
            data_path = url.data_path()
            if data_path is not None:
                data_path = data_path.format(
                    entry=entry, index_zfill4="{index_zfill4}", index="{index}"
                )
                # we don't want to handle index_zfill4 and index at this level
            file_pattern = url.file_path()
            if file_pattern is not None:
                file_pattern = file_pattern.format(
                    entry,
                    entry,
                    index_zfill4="{index_zfill4}",
                    index="{index}",
                    scan_prefix=self.get_dataset_basename(),
                )
                # we don't want to handle index_zfill4 and index at this level
            scheme = url.scheme()

            frames_path_and_index = []
            # list of tuples (frame_file, frame_index). frame_index can be None if not found
            patterns = ("index_zfill4", "index")
            contains_patterns = False
            for pattern in patterns:
                if pattern in file_pattern:
                    contains_patterns = True
                    files_from_pattern = get_files_from_pattern(
                        file_pattern=file_pattern,
                        pattern=pattern,
                        research_dir=self.path,
                    )
                    for frame_index, frame_file in files_from_pattern.items():
                        frames_path_and_index.append(
                            (os.path.join(self.path, frame_file), frame_index)
                        )
            if not contains_patterns:
                frames_path_and_index.append(
                    (os.path.join(self.path, file_pattern), None)
                )

            def format_data_path(data_path):
                index_zfill4_pattern = False
                if data_path.endswith("{index_zfill4}"):
                    index_zfill4_pattern = True
                    data_path = data_path[: -len("{index_zfill4}")]
                if data_path.endswith("{index}"):
                    data_path = data_path[: -len("{index}")]
                if data_path.endswith("/"):
                    data_path = data_path[:-1]
                return data_path, index_zfill4_pattern

            for frame_file_path, frame_index in frames_path_and_index:
                if scheme == "fabio":
                    if not os.path.exists(frame_file_path):
                        continue
                    try:
                        handler = fabio.open(frame_file_path)
                        with fabio.open(frame_file_path) as handler:
                            if handler.nframes > 1:
                                _logger.warning(
                                    f"{frame_file_path} is expected to have one frame. Only the first one will be picked"
                                )
                            if frame_index in res_data:
                                _logger.error(
                                    f"two frames found with the same index {frame_index}"
                                )
                            if return_as_url:
                                res_data[frame_index] = DataUrl(
                                    file_path=frame_file_path, scheme="fabio"
                                )
                            else:
                                res_data[frame_index] = handler.data
                            if "SRCUR" in handler.header:
                                res_metadata.machine_current.append(
                                    float(handler.header["SRCUR"])
                                )
                            if "CountTime" in handler.header:
                                res_metadata.count_time.append(
                                    float(handler.header["CountTime"])
                                )

                    except OSError as e:
                        _logger.error(e)
                elif scheme in ("hdf5", "silx"):
                    data_path, index_zfill4_pattern = format_data_path(data_path)

                    if not os.path.exists(frame_file_path):
                        continue
                    with hdf5_open(frame_file_path) as h5s:
                        dataset_or_group = h5s[data_path]
                        if isinstance(dataset_or_group, h5py.Dataset):
                            idx = None
                            if dataset_or_group.name.isnumeric():
                                try:
                                    idx = int(dataset_or_group)
                                except ValueError:
                                    idx = None
                            if return_as_url:
                                res_data[idx] = DataUrl(
                                    file_path=frame_file_path,
                                    data_path=data_path,
                                    scheme="silx",
                                )
                            else:
                                res_data[idx] = dataset_or_group[()]
                        else:
                            assert isinstance(
                                dataset_or_group, h5py.Group
                            ), f"expect a group not {type(dataset_or_group)}"
                            # browse children
                            for name, item in dataset_or_group.items():
                                if isinstance(item, h5py.Dataset):
                                    if name.isnumeric():
                                        if index_zfill4_pattern and not len(name) == 4:
                                            continue
                                        else:
                                            try:
                                                idx = int(name)
                                            except ValueError:
                                                _logger.info(
                                                    f"fail to cast {name} as a integer"
                                                )
                                                continue
                                            if return_as_url:
                                                res_data[idx] = DataUrl(
                                                    file_path=frame_file_path,
                                                    data_path=data_path + "/" + name,
                                                    scheme="silx",
                                                )
                                            else:
                                                res_data[idx] = dataset_or_group[name][
                                                    ()
                                                ]
                else:
                    raise ValueError(
                        f"scheme {scheme} is not handled. Should be fabio, silx of hdf5"
                    )

        def get_unit(attrs) -> pint.Unit | None:
            if "unit" in attrs:
                unit = attrs["unit"]
            elif "units":
                unit = attrs["units"]
            if unit == "kev":
                unit = _ureg.keV
            if unit is not None:
                return pint.Unit(unit)

            return None

        # load frames metadata
        if metadata_input_urls is not None:
            for url in metadata_input_urls:
                metadata_file = url.file_path()
                metadata_file = metadata_file.format(
                    scan_prefix=self.get_dataset_basename(),
                )
                if not os.path.isabs(metadata_file):
                    metadata_file = os.path.join(self.path, metadata_file)
                data_path = url.data_path().format(
                    entry=entry,
                )

                if scheme in ("hdf5", "silx"):
                    if not os.path.exists(metadata_file):
                        continue
                    with hdf5_open(metadata_file) as h5s:
                        if data_path not in h5s:
                            continue
                        parent_group = h5s[data_path]
                        if ReducedFramesInfos.COUNT_TIME_KEY in parent_group:
                            count_time = silx.io.utils.h5py_read_dataset(
                                parent_group[ReducedFramesInfos.COUNT_TIME_KEY]
                            )
                            unit = get_unit(
                                attrs=parent_group[
                                    ReducedFramesInfos.COUNT_TIME_KEY
                                ].attrs,
                            )
                            if unit is None:
                                unit = _ureg.second
                            res_metadata.count_time = (
                                (count_time * unit).to(_ureg.second).magnitude
                            )

                        if ReducedFramesInfos.MACHINE_ELECT_CURRENT_KEY in parent_group:
                            machine_current = silx.io.utils.h5py_read_dataset(
                                parent_group[
                                    ReducedFramesInfos.MACHINE_ELECT_CURRENT_KEY
                                ]
                            )

                            unit = get_unit(
                                attrs=parent_group[
                                    ReducedFramesInfos.MACHINE_ELECT_CURRENT_KEY
                                ].attrs,
                            )
                            if unit is None:
                                unit = _ureg.ampere
                            res_metadata.machine_current = (
                                (machine_current * unit).to(_ureg.ampere).magnitude
                            )

        return res_data, res_metadata

    def save_reduced_darks(
        self,
        darks: dict,
        output_urls: tuple,
        darks_infos: ReducedFramesInfos | None = None,
        metadata_output_urls: tuple | None = None,
        overwrite: bool = False,
    ) -> None:
        """
        Dump computed dark (median / mean...) into files.

        :param darks: dictionary with frame indices as key (int) and a 2D numpy array as value.
        :param output_urls: tuple of silx DataUrl, where to save the darks. Default value is usually provided by children class directly.
                            You better know what you are doing if you modify the default value.
        :param darks_infos: information regarding darks (metadata) like the machine current, exposure time...
        :param metadata_output_urls: tuple of silx DataUrl, where to save the metadata / darks information.  Default value is usually provided by children class directly
                            You better know what you are doing if you modify the default value.
        :param overwrtie: if the output files exist then will overwrite them.

        Here is an example on how to save your own reduced dark / flat

        .. code-block:: python

            from tomoscan.framereducer.reducedframesinfos import ReducedFramesInfos
            ...

            scan = ... # scan must be an instance of TomoScanBase like NXtomoScan()
            darks_infos.count_time = [2.5]
            darks_infos.machine_current = [13.1]
            scan.save_reduced_darks(
                darks={
                    0: dark_frame,  # dark_frame is a 2d numpy array
                },
                darks_infos=darks_infos,
                overwrite=True,
            )
        """
        self._dump_frame_dict(
            frames=darks,
            output_urls=output_urls,
            frames_metadata=darks_infos,
            metadata_output_urls=metadata_output_urls,
            overwrite=overwrite,
        )

    def load_reduced_darks(
        self,
        inputs_urls: tuple,
        metadata_input_urls=None,
        return_as_url: bool = False,
        return_info: bool = False,
    ) -> dict | tuple:
        """
        load reduced dark (median / mean...) into files

        :param inputs_urls: where to load the reduced darks. A default value is provided by the children class.
                            You better know what you are doing if you modify the default value.
        :param metadata_input_urls: where to load the reduced darks metadata. A default value is provided by the children class.
                                    You better know what you are doing if you modify the default value.
        :param return_as_url: if True then instead of returning the reduced frames as 2D numpy arrays it will return them as a silx DataUrl
        :param return_info: if False only return return the dict of reduced frames (frame index as key (int) and frame as a 2D numpy array or silx Data Url as value)
                            if True then return (dict of reduced frames, darks info / metadata)

        Here is an example of usage:

        .. code-block:: python

            scan = ... # scan must be an instance of TomoScanBase like NXtomoScan()
            reduced_darks = scan.load_reduced_darks()
            reduced_darks, darks_infos = scan.load_reduced_darks(return_info=True)

            dark_frame_np_array = reduced_darks[0]
        """
        darks, infos = self._load_frame_dict(
            inputs_urls=inputs_urls,
            return_as_url=return_as_url,
            metadata_input_urls=metadata_input_urls,
        )
        if return_info:
            return darks, infos
        else:
            return darks

    def save_reduced_flats(
        self,
        flats: dict,
        output_urls: tuple,
        flats_infos: ReducedFramesInfos | None = None,
        metadata_output_urls: tuple | None = None,
        overwrite: bool = False,
    ) -> None:
        """
        Dump computed dark (median / mean...) into files.

        :param flats: dictionary with frame indices as key (int) and a 2D numpy array as value.
        :param output_urls: tuple of silx DataUrl, where to save the flats. Default value is usually provided by children class directly.
                            You better know what you are doing if you modify the default value.
        :param flats_infos: information regarding flats (metadata) like the machine current, exposure time...
        :param metadata_output_urls: tuple of silx DataUrl, where to save the metadata / flats information.  Default value is usually provided by children class directly
                            You better know what you are doing if you modify the default value.
        :param overwrite: if the output files exist then will overwrite them.

        Here is an example on how to save your own reduced dark / flat

        .. code-block:: python

            from tomoscan.framereducer.reducedframesinfos import ReducedFramesInfos
            ...

            scan = ... # scan must be an instance of TomoScanBase like NXtomoScan()
            flats_infos = ReducedFramesInfos()
            flats_infos.count_time = [2.5, 1.2]
            flats_infos.machine_current = [12.5, 13.1]
            # for normalization the first reduced flat (at index 1) will have 2.5 as count time and 12.5 as machine current
            # the second reduced flat frame (at index 1002) will have 1.2 as count time and 13.1 as machine current
            scan.save_reduced_darks(
                darks={
                    1: flat_frame_1,     # flat_frame_1 is a 2d numpy array
                    1002: flat_frame_2,  # flat_frame_2 is another 2d numpy array
                },
                flats_infos=flats_infos,
                overwrite=True,
            )
        """
        self._dump_frame_dict(
            frames=flats,
            output_urls=output_urls,
            frames_metadata=flats_infos,
            metadata_output_urls=metadata_output_urls,
            overwrite=overwrite,
        )

    def load_reduced_flats(
        self,
        inputs_urls: tuple,
        metadata_input_urls=None,
        return_as_url: bool = False,
        return_info: bool = False,
    ) -> dict | tuple:
        """
        load reduced flats frames

        :param inputs_urls: where to load the reduced flats. A default value is provided by the children class.
                            You better know what you are doing if you modify the default value.
        :param metadata_input_urls: where to load the reduced flats metadata. A default value is provided by the children class.
                                    You better know what you are doing if you modify the default value.
        :param return_as_url: if True then instead of returning the reduced frames as 2D numpy arrays it will return them as a silx DataUrl
        :param return_info: if False only return return the dict of reduced frames (frame index as key (int) and frame as a 2D numpy array or silx Data Url as value)
                            if True then return (dict of reduced frames, flats info / metadata)

        Here is an example of usage:

        .. code-block:: python

            scan = ... # scan must be an instance of TomoScanBase like NXtomoScan()
            reduced_flats = scan.load_reduced_flats()
            reduced_flats, flats_infos = scan.load_reduced_flats(return_info=True)

        """
        flats, infos = self._load_frame_dict(
            inputs_urls=inputs_urls,
            return_as_url=return_as_url,
            metadata_input_urls=metadata_input_urls,
        )
        if return_info:
            return flats, infos
        else:
            return flats

    def compute_reduced_flats(
        self,
        reduced_method="median",
        overwrite=True,
        output_dtype=None,
        return_info=False,
    ):
        """
        :param ReduceMethod method: method to compute the flats
        :param overwrite: if some flats have already been computed will overwrite them
        :param return_info: do we return (reduced_frames, info) or directly reduced_frames
        """
        if self.FRAME_REDUCER_CLASS is None:
            raise ValueError("no frame reducer class provided")
        frame_reducer = self.FRAME_REDUCER_CLASS(  # pylint: disable=E1102
            scan=self,
            reduced_method=reduced_method,
            target="flats",
            overwrite=overwrite,
            output_dtype=output_dtype,
        )
        reduced_frames, infos = frame_reducer.run()
        if return_info:
            return reduced_frames, infos
        else:
            return reduced_frames

    def compute_reduced_darks(
        self,
        reduced_method="mean",
        overwrite=True,
        output_dtype=None,
        return_info=False,
    ):
        """
        :param ReduceMethod method: method to compute the flats
        :param overwrite: if some darks have already been computed will overwrite them
        :param return_info: do we return (reduced_frames, info) or directly reduced_frames
        """
        if self.FRAME_REDUCER_CLASS is None:
            raise ValueError("no frame reducer class provided")
        frame_reducer = self.FRAME_REDUCER_CLASS(  # pylint: disable=E1102
            scan=self,
            reduced_method=reduced_method,
            target="darks",
            overwrite=overwrite,
            output_dtype=output_dtype,
        )
        reduced_frames, infos = frame_reducer.run()
        if return_info:
            return reduced_frames, infos
        else:
            return reduced_frames

    @staticmethod
    def get_volume_output_file_name(z=None, suffix=None):
        """if used by tomwer and nabu this should help for tomwer to find out the output files of anbu from a configuration file. Could help to get some normalization there"""
        raise NotImplementedError


def _find_closest_index(values, query):
    pos = bisect_left(values, query)
    if pos == 0:
        return 0
    if pos >= len(values):
        return len(values) - 1
    return pos - 1 if abs(values[pos - 1] - query) < abs(values[pos] - query) else pos


def projections_angles_to_indices(
    angles: list, projections_indices: list, rotation_angles: list
):
    """
    From a list of angles (in degrees), return the corresponding indices.

    :param angles: Rotation angles
    :param projections_indices: List of indices corresponding to each projection
    :param rotation_angles: List of all rotation angles of the projections
    """
    ignore_projections_indices = []
    for angle in angles:
        proj_idx0 = _find_closest_index(rotation_angles, angle)
        proj_idx = projections_indices[proj_idx0]
        ignore_projections_indices.append(proj_idx)
    return ignore_projections_indices


def projection_angular_range_to_indices(
    angular_range: tuple, projections_indices: list, rotation_angles: list
):
    """
    From an angular range, return the corresponding indices of projections.

    :param angular_range: Tuple defining the angular range [min, max] where boundaries are included.
    :param projections_indices: List of indices corresponding to each projection
    :param rotation_angles: List of all rotation angles of the projections
    """
    ignore_projections_indices = []
    angle_min, angle_max = angular_range
    projections_indices = numpy.array(projections_indices)
    for proj_idx, angle in zip(projections_indices, rotation_angles):
        if angle_min <= angle and angle <= angle_max:
            ignore_projections_indices.append(proj_idx)
    return ignore_projections_indices
