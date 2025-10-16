"""module dedicated to nexus - NXtomo - scan class (NXtomoScan) and utils. Based on HDF5 file format"""

from __future__ import annotations

import io
import json
import logging
import os
import pint
from typing import Iterable
import h5py
import numpy
from silx.io.url import DataUrl
from silx.io.utils import get_data, h5py_read_dataset, h5py_read_attribute
from silx.io.utils import open as open_hdf5

from nxtomo.paths.nxtomo import get_paths as _get_nexus_paths
from nxtomo.utils.transformation import (
    DetXFlipTransformation,
    DetYFlipTransformation,
    DetZFlipTransformation,
)
from nxtomo.nxobject.nxdetector import NXdetector
from nxtomo.paths.nxtomo import LATEST_VERSION as LATEST_NXTOMO_VERSION
from nxtomo.application.nxtomo import ImageKey, NXtomo as _NXtomo
from nxtomo.nxobject.nxdetector import FieldOfView as FOV

from tomoscan.utils.io import deprecated, deprecated_warning
from tomoscan.esrf.identifier.hdf5Identifier import NXtomoScanIdentifier
from tomoscan.esrf.scan.framereducer.hdf5framereducer import HDF5FrameReducer
from tomoscan.identifier import ScanIdentifier
from tomoscan.scanbase import Source, TomoScanBase
from tomoscan.utils import BoundingBox1D, BoundingBox3D, docstring
from tomoscan.esrf.scan.utils import (
    dataset_has_broken_vds,
    check_possible_issue_with_rlimit,
)
from tomoscan._CoordinateSystem import CoordinateSystem


from .utils import get_compacted_dataslices

_ureg = pint.get_application_registry()
_logger = logging.getLogger(__name__)

__all__ = [
    "get_nexus_paths",
    "NXtomoScan",
    "TomoFrame",
    "HDF5TomoScan",
]


@deprecated(reason="moved", replacement="nxtomo.paths.nxtomo", since_version="0.8.0")
def get_nexus_paths(version: float):
    return _get_nexus_paths(version=version)


class NXtomoScan(TomoScanBase):
    """
    This is the class to be used to read an `NXtomo <https://manual.nexusformat.org/classes/applications/NXtomo.html>`_.

    .. note::

        nxtomo has moved from esrf coordinate system to McStas coordinate.
        NXtomoScan should absorb this transition.

        Tomoscan coordinate system is the following:

        .. image:: ../development/img/coordinate_system/coordinate_system_esrf.svg
            :width: 600 px
            :align: center


        When McStas coordinate system is the following:

        .. image:: ../development/img/coordinate_system/coordinate_system_nexus.svg
            :width: 600 px
            :align: center

        .. warning:

            NXtomoScan doesn't handle directly detector frame flips. Detector frame flips can be obtained by :ref:`detector_is_lr_flip` and :ref:`detector_is_ud_flip` must be handled downstream.
            The flip contained on the NXtomo should be the result of soft and mechanical flips.


    .. warning::

        HDF5 may have broken links in virtual layout. By default, this class
        performs an integrity check on all the links, and this
        can be very long for huge data sets with tens of thousands of links.
        This check can be set by defining and export in the shell environment variable
        TOMOTOOLS_SKIP_DET_CHECK  set either to 1 or y.


    :param scan: path to the nexus file.
    :param entry: name of the NXtomo entry to select. If given
                                   index is ignored.
    :param index: of the NXtomo entry to select. Ignored if
                                   an entry is specified. For consistency
                                   entries are ordered alphabetically
    :param nx_version: Version of the Nexus convention to use.
                                          By default (None) it will take the latest one
    :param ignore_projections: projection indices to be ignored.
        If a list of integers is provided: exclude the projections corresponding to these indices in "image_key".
        Otherwise, a dict should be provided in the form {"kind": kind, "values": values}
        where "kind" can be: "indices", "angles", "range".
    """

    _NEXUS_VERSION_PATH = "version"

    _TYPE = "hdf5"

    _DICT_ENTRY_KEY = "entry"

    SCHEME = "silx"

    REDUCED_DARKS_DATAURLS = (
        DataUrl(
            file_path="{scan_prefix}_darks.hdf5",
            data_path="{entry}/darks/{index}",
            scheme=SCHEME,
        ),
    )

    REDUCED_DARKS_METADATAURLS = (
        DataUrl(
            file_path="{scan_prefix}_darks.hdf5",
            data_path="{entry}/darks/",
            scheme=SCHEME,
        ),
    )

    REDUCED_FLATS_DATAURLS = (
        DataUrl(
            file_path="{scan_prefix}_flats.hdf5",
            data_path="{entry}/flats/{index}",
            scheme=SCHEME,
        ),
    )

    REDUCED_FLATS_METADATAURLS = (
        DataUrl(
            file_path="{scan_prefix}_flats.hdf5",
            data_path="{entry}/flats/",
            scheme=SCHEME,
        ),
    )

    PCA_FLATS_DATAURLS = (
        DataUrl(
            file_path="{scan_prefix}_PCAFlats.hdf5",
            data_path="{entry}",
            scheme=SCHEME,
        ),
    )

    PCA_FLATS_METADATAURLS = (
        DataUrl(
            file_path="{scan_prefix}_PCAFlats.hdf5",
            data_path="{entry}",
            scheme=SCHEME,
        ),
    )

    FRAME_REDUCER_CLASS = HDF5FrameReducer

    def __init__(
        self,
        scan: str | None,
        entry: str = None,
        index: int | None = 0,
        ignore_projections: dict | Iterable | None = None,
        nx_version=None,
    ):
        if entry is not None:
            index = None
        # if the user give the master file instead of the scan dir...
        if scan is not None:
            if not os.path.exists(scan) and "." in os.path.split(scan)[-1]:
                self.master_file = scan
                scan = os.path.dirname(scan)
            elif os.path.isfile(scan) or ():
                self.master_file = scan
                scan = os.path.dirname(scan)
            else:
                self.master_file = self.get_master_file(scan)
        else:
            self.master_file = None

        super(NXtomoScan, self).__init__(
            scan=scan, type_=NXtomoScan._TYPE, ignore_projections=ignore_projections
        )

        if scan is None:
            self._entry = None
        else:
            self._entry = entry or self._get_entry_at(
                index=index, file_path=self.master_file
            )
            if self._entry is None:
                raise ValueError(f"unable to find a valid entry for {self.master_file}")
        # for now the default entry is 1_tomo but should change with time
        self._name = None
        self._sample_name = None
        self._grp_size = None
        # data caches
        self._projections_compacted = None
        self._flats = None
        self._darks = None
        self._tomo_n = None
        # number of projections / radios
        self._dark_n = None
        # number of dark image made during acquisition
        self._flat_n = None
        # number of flat field made during acquisition
        self._scan_range = None
        # scan range, in degree
        self._dim_1, self._dim_2 = None, None
        # image dimensions
        self._sample_x_pixel_size: float | None = None
        self._sample_y_pixel_size: float | None = None
        self._detector_x_pixel_size: float | None = None
        self._detector_y_pixel_size: float | None = None
        # pixel dimensions (tuple)
        self._frames = None
        self._image_keys = None
        self._image_keys_control = None
        self._sequence_number = None
        self._rotation_angles = None
        self._fov = None
        self._energy = None
        self._x_rotation_axis_pixel_position = None
        self._start_time = None
        self._end_time = None
        self._x_translations = None
        self._y_translations = None
        self._z_translations = None
        self._nexus_paths = None
        self._nexus_version = None
        self._user_nx_version = nx_version
        self.__detector_broken_vds_behavior = {
            "run_check": True,  # check vds
            "raise_error": False,  # if met an error raise it
            "log_level": logging.WARNING,  # if met an error log it with the following level
        }
        self.__coordinate_system = None
        # behavior to get when check detector vds
        self._x_flipped = None
        self._y_flipped = None
        self._detector_transformations = None
        self._bliss_orginal_files = None

    def _get_projs_indices_and_angles(self):
        mask = self.image_key == ImageKey.PROJECTION.value
        projs_indices = numpy.where(mask)[0]
        rot_angles = numpy.array(self.rotation_angle)[mask]
        return projs_indices, rot_angles

    def set_check_behavior(
        self, run_check=True, raise_error=False, log_level=logging.WARNING
    ):
        """
        when user require to access to scan frames NXtomoScan build them (`frames` property).
        Some check can be made during this stage to know if the scan has some broken virtual-dataset (vds) or
        if the vds is linked to more file than the system might handle.

        In this case the 'vds-check' can either raise an error or log potential issues with a specific log level
        """
        self.__detector_broken_vds_behavior = {
            "run_check": run_check,
            "raise_error": raise_error,
            "log_level": log_level,
        }

    @staticmethod
    def get_master_file(scan_path):
        if os.path.isfile(scan_path):
            master_file = scan_path
        else:
            master_file = os.path.join(scan_path, os.path.basename(scan_path))
            if os.path.exists(master_file + ".nx"):
                master_file = master_file + ".nx"
            elif os.path.exists(master_file + ".hdf5"):
                master_file = master_file + ".hdf5"
            elif os.path.exists(master_file + ".h5"):
                master_file = master_file + ".h5"
            else:
                master_file = master_file + ".nx"
        return master_file

    @docstring(TomoScanBase.clear_cache)
    def clear_cache(self) -> None:
        self._dim_1, self._dim_2 = None, None
        self._sample_x_pixel_size = None
        self._sample_y_pixel_size = None
        self._detector_x_pixel_size = None
        self._detector_y_pixel_size = None
        self._x_magnified_pixel_size = None
        self._y_magnified_pixel_size = None
        self._fov = None
        self._source = None
        self._energy = None
        self._x_flipped = None
        self._y_flipped = None
        self._detector_transformations = None
        self._x_rotation_axis_pixel_position = None
        super().clear_cache()

    def clear_frames_cache(self):
        self._projections_compacted = None
        self._flats = None
        self._darks = None
        self._tomo_n = None
        self._dark_n = None
        self._flat_n = None
        self._scan_range = None
        self._frames = None
        self._image_keys = None
        self._image_keys_control = None
        self._sequence_number = None
        self._count_time = None
        self._x_flipped = None
        self._y_flipped = None
        self._detector_transformations = None
        self._x_translations = None
        self._y_translations = None
        self._z_translations = None
        self._rotation_angles = None
        super().clear_frames_cache()

    @staticmethod
    def _get_entry_at(index: int, file_path: str) -> str:
        """

        :param index:
        :param file_path:
        :return:
        """
        entries = _NXtomo.get_valid_entries(file_path)
        if len(entries) == 0:
            return None
        else:
            return entries[index]

    @staticmethod
    @deprecated(replacement="NXtomo.get_valid_entries", since_version="2.0")
    def get_valid_entries(file_path: str) -> tuple:
        """
        return the list of 'Nxtomo' entries at the root level

        :param file_path:
        :return: list of valid Nxtomo node (ordered alphabetically)

        ..note: entries are sorted to insure consistency
        """
        return _NXtomo.get_valid_entries(file_path=file_path)

    @staticmethod
    @deprecated(replacement="NXtomo.node_is_nxtomo", since_version="2.0")
    def node_is_nxtomo(node: h5py.Group) -> bool:
        """check if the given h5py node is an nxtomo node or not"""
        return _NXtomo.node_is_nxtomo(node)

    @docstring(TomoScanBase.is_tomoscan_dir)
    @staticmethod
    def is_tomoscan_dir(directory: str, **kwargs) -> bool:
        if os.path.isfile(directory):
            master_file = directory
        else:
            master_file = NXtomoScan.get_master_file(scan_path=directory)
        if master_file:
            entries = _NXtomo.get_valid_entries(file_path=master_file)
            return len(entries) > 0

    @docstring(TomoScanBase.is_abort)
    def is_abort(self, **kwargs):
        # for now there is no abort definition in .hdf5
        return False

    @docstring(TomoScanBase.to_dict)
    def to_dict(self) -> dict:
        res = super().to_dict()
        res[self.DICT_PATH_KEY] = self.master_file
        res[self._DICT_ENTRY_KEY] = self.entry
        return res

    @staticmethod
    def from_dict(_dict: dict):
        scan = NXtomoScan(scan=None)
        scan.load_from_dict(_dict=_dict)
        return scan

    @docstring(TomoScanBase.load_from_dict)
    def load_from_dict(self, _dict: dict) -> TomoScanBase:
        """

        :param _dict:
        :return:
        """
        if isinstance(_dict, io.TextIOWrapper):
            data = json.load(_dict)
        else:
            data = _dict
        if not (self.DICT_TYPE_KEY in data and data[self.DICT_TYPE_KEY] == self._TYPE):
            raise ValueError("Description is not an HDF5Scan json description")
        if NXtomoScan._DICT_ENTRY_KEY not in data:
            raise ValueError("No hdf5 entry specified")

        assert self.DICT_PATH_KEY in data
        self._entry = data[self._DICT_ENTRY_KEY]
        self.master_file = self.get_master_file(data[self.DICT_PATH_KEY])

        if os.path.isdir(data[self.DICT_PATH_KEY]):
            self.path = data[self.DICT_PATH_KEY]
        else:
            self.path = os.path.dirname(data[self.DICT_PATH_KEY])
        return self

    @property
    def entry(self) -> str:
        return self._entry

    @property
    def nexus_version(self):
        if self._user_nx_version is not None:
            return self._user_nx_version
        return self._get_generic_key(
            "_nexus_version", self._NEXUS_VERSION_PATH, is_attribute=True
        )

    @nexus_version.setter
    def nexus_version(self, version) -> float | None:
        """nexus version of the file read currently. Reminder: if None then we expect it to be the latest version"""
        if not isinstance(version, float):
            raise TypeError("version expect to be a float")
        self._nexus_version = version

    @property
    def nexus_path(self):
        if self._nexus_paths is None:
            self._nexus_paths = _get_nexus_paths(self.nexus_version)
        return self._nexus_paths

    @property
    def coordinate_system(self) -> CoordinateSystem | None:
        """
        Coordinate system used in the NXtomo file.

        :param default_old_nxtomo: value to return for old nxtomo (<3.0).
            Before nxtomo 3.0 there was no information about the coordinate system. The ESRF coordinate system was used.
        :param default: default value for recent nxtomo (>=3.0)
        """
        if self.__coordinate_system is None:
            self.__coordinate_system = self._get_coordinate_system()
        return self.__coordinate_system

    def _get_coordinate_system(
        self, default=CoordinateSystem.McStas, default_old_nxtomo=CoordinateSystem.ESRF
    ) -> CoordinateSystem | None:
        """
        return the coordinate system used in the NXtomo file.

        :param default_old_nxtomo: value to return for NXTOMO_VERSION (<2.0. Warning != from the nxtomo project).
            Before nxtomo 3.0 there was no information about the coordinate system. The ESRF coordinate system was used.
        :param default: default value for recent nxtomo (>=3.0)
        """
        self._check_hdf5scan_validity()
        with open_hdf5(self.master_file) as h5_file:
            key = "NeXus_Coordinate_System"
            if key in h5_file[self._entry].attrs:
                coordinate_system = h5py_read_attribute(
                    h5_file[self._entry].attrs, name=key
                )
            else:
                coordinate_system = None

        if coordinate_system is None:
            if (self.nexus_version or LATEST_NXTOMO_VERSION) < 2.0:
                return default_old_nxtomo
            else:
                return default
        return CoordinateSystem(coordinate_system)

    @property
    @docstring(TomoScanBase.source)
    def source(self):
        if self._source is None:
            self._source = Source(
                name=self.source_name,
                type=self.source_type,
            )
        return self._source

    @property
    def title(self):
        return self._get_generic_key("_title", self.nexus_path.NAME_PATH)

    @property
    def source_name(self):
        return self._get_generic_key("_source_name", self.nexus_path.SOURCE_NAME)

    @property
    def source_type(self):
        return self._get_generic_key("_source_type", self.nexus_path.SOURCE_TYPE)

    @property
    @docstring(TomoScanBase.instrument_name)
    def instrument_name(self) -> str | None:
        """

        :return: instrument name
        """
        return self._get_generic_key(
            "_instrument_name", self.nexus_path.INSTRUMENT_NAME
        )

    @property
    def sequence_name(self):
        """Return the sequence name"""
        return self._get_generic_key("_name", self.nexus_path.NAME_PATH)

    @property
    @docstring(TomoScanBase.projections)
    def sample_name(self):
        return self._get_generic_key("_sample_name", self.nexus_path.SAMPLE_NAME_PATH)

    @property
    @docstring(TomoScanBase.projections)
    def group_size(self):
        return self._get_generic_key("_grp_size", self.nexus_path.GRP_SIZE_ATTR)

    @property
    @docstring(TomoScanBase.projections)
    def projections(self) -> dict | None:
        if self._projections is None:
            if self.frames:
                ignored_projs = self.get_ignored_projection_indices()
                proj_frames = tuple(
                    filter(
                        lambda x: (
                            x.image_key is ImageKey.PROJECTION
                            and x.index not in ignored_projs
                            and x.is_control is False
                        ),
                        self.frames,
                    )
                )
                self._projections = {}
                for proj_frame in proj_frames:
                    self._projections[proj_frame.index] = proj_frame.url
        return self._projections

    @projections.setter
    def projections(self, projections: dict):
        self._projections = projections

    def get_projections_intensity_monitor(self) -> dict:
        """return intensity monitor values for projections"""
        if self.frames:
            ignored_projs = []
            if self.ignore_projections is not None:
                ignored_projs = self.ignore_projections
            proj_frames = tuple(
                filter(
                    lambda x: (
                        x.image_key is ImageKey.PROJECTION
                        and x.index not in ignored_projs
                        and x.is_control is False
                    ),
                    self.frames,
                )
            )
            intensity_monitor = {}
            for proj_frame in proj_frames:
                intensity_monitor[proj_frame.index] = proj_frame.intensity_monitor
            return intensity_monitor
        else:
            return {}

    @property
    @docstring(TomoScanBase.alignment_projections)
    def alignment_projections(self) -> dict | None:
        if self._alignment_projections is None:
            if self.frames:
                proj_frames = tuple(
                    filter(
                        lambda x: x.image_key == ImageKey.PROJECTION
                        and x.is_control is True,
                        self.frames,
                    )
                )
                self._alignment_projections = {}
                for proj_frame in proj_frames:
                    self._alignment_projections[proj_frame.index] = proj_frame.url
        return self._alignment_projections

    @property
    @docstring(TomoScanBase.darks)
    def darks(self) -> dict | None:
        if self._darks is None:
            if self.frames:
                dark_frames = tuple(
                    filter(lambda x: x.image_key is ImageKey.DARK_FIELD, self.frames)
                )
                self._darks = {}
                for dark_frame in dark_frames:
                    self._darks[dark_frame.index] = dark_frame.url
        return self._darks

    @property
    @docstring(TomoScanBase.flats)
    def flats(self) -> dict | None:
        if self._flats is None:
            if self.frames:
                flat_frames = tuple(
                    filter(lambda x: x.image_key is ImageKey.FLAT_FIELD, self.frames)
                )
                self._flats = {}
                for flat_frame in flat_frames:
                    self._flats[flat_frame.index] = flat_frame.url
        return self._flats

    @docstring(TomoScanBase.update)
    def update(self) -> None:
        """update list of radio and reconstruction by parsing the scan folder"""
        if self.master_file is None or not os.path.exists(self.master_file):
            return
        self.projections = self._get_projections_url()
        # TODO: update darks and flats too

    @docstring(TomoScanBase.get_proj_angle_url)
    def _get_projections_url(self):
        if self.master_file is None or not os.path.exists(self.master_file):
            return
        frames = self.frames
        if frames is not None:
            urls = {}
            for frame in frames:
                if frame.image_key is ImageKey.PROJECTION:
                    urls[frame.index] = frame.url
            return urls
        else:
            return None

    @docstring(TomoScanBase.tomo_n)
    @property
    def tomo_n(self) -> int | None:
        """we are making two assumptions for computing tomo_n:
        - if a rotation = scan_range +/- EPSILON this is a return projection
        - The delta between each projections is constant
        """
        return self._get_generic_key("_tomo_n", self.nexus_path.TOMO_N_SCAN)

    @docstring(TomoScanBase.tomo_n)
    @property
    def magnification(self):
        return self._get_generic_key(
            "_magnification",
            "/".join(
                [
                    self.nexus_path.INSTRUMENT_PATH,
                    self.nexus_path.nx_instrument_paths.DETECTOR_PATH,
                    self.nexus_path.nx_detector_paths.MAGNIFICATION,
                ]
            ),
        )

    @property
    def return_projs(self) -> list | None:
        """ """
        frames = self.frames
        if frames:
            return_frames = list(filter(lambda x: x.is_control is True, frames))
            return return_frames
        else:
            return None

    @property
    def rotation_angle(self) -> tuple | None:
        """
        Return rotation angle (expected counter-clockwise in case we are reading from McStas)
        """
        cast_to_float = lambda values: [float(val) for val in values]
        return self._get_generic_key(
            "_rotation_angles",
            self.nexus_path.ROTATION_ANGLE_PATH,
            apply_function=cast_to_float,
        )

    @property
    def x_translation(self) -> tuple | None:
        cast_to_float = lambda values: [float(val) for val in values]
        """
        x translation **according to the esrf coordinate system**

        .. note::

            coordinate system: NXtomo before 1.5 used to be stored within the esrf coordinate system

                       Z axis
                              ^    Y axis
                              | /
            x-ray             |/
            -------->          ------> X axis

            but Nexus is using the McStas coordinate system

                            Y axis
                              ^   X axis
                              |  /
            x-ray             | /
            -------->          ------> Z axis

            which is now used by NXtomo (and correctly filled with nxtomomill > 1.2.0dev1)
        """
        if self.coordinate_system is CoordinateSystem.McStas:
            path = self.nexus_path.Z_TRANS_PATH
        else:
            path = self.nexus_path.X_TRANS_PATH
        return self._get_generic_key(
            "_x_translations",
            path,
            apply_function=cast_to_float,
            returned_unit=_ureg.meter,
            default_unit=_ureg.millimeter,
        )

    @property
    def y_translation(self) -> tuple | None:
        """
        y translation **according to the esrf coordinate system**

        .. note::

            coordinate system: NXtomo before 1.5 used to be stored within the esrf coordinate system

                       Z axis
                              ^    Y axis
                              | /
            x-ray             |/
            -------->          ------> X axis

            but Nexus is using the McStas coordinate system

                            Y axis
                              ^   X axis
                              |  /
            x-ray             | /
            -------->          ------> Z axis

            which is now used by NXtomo (and correctly filled with nxtomomill > 1.2.0dev1)
        """
        if self.coordinate_system is CoordinateSystem.McStas:
            path = self.nexus_path.X_TRANS_PATH
        else:
            path = self.nexus_path.Y_TRANS_PATH

        return self._get_generic_key(
            "_y_translations",
            path,
            returned_unit=_ureg.meter,
            default_unit=_ureg.millimeter,
            apply_function=lambda values: [float(val) for val in values],
        )

    @property
    def z_translation(self) -> tuple | None:
        """
        z translation **according to the esrf coordinate system**

        .. note::

            coordinate system: NXtomo before 1.5 used to be stored within the esrf coordinate system

                       Z axis
                              ^    Y axis
                              | /
            x-ray             |/
            -------->          ------> X axis

            but Nexus is using the McStas coordinate system

                            Y axis
                              ^   X axis
                              |  /
            x-ray             | /
            -------->          ------> Z axis

            which is now used by NXtomo (and correctly filled with nxtomomill > 1.2.0dev1)
        """
        cast_to_float = lambda values: [float(val) for val in values]
        if self.coordinate_system is CoordinateSystem.McStas:
            path = self.nexus_path.Y_TRANS_PATH
        else:
            path = self.nexus_path.Z_TRANS_PATH
        return self._get_generic_key(
            "_z_translations",
            path,
            apply_function=cast_to_float,
            returned_unit=_ureg.meter,
            default_unit=_ureg.millimeter,
        )

    @property
    def image_key(self) -> list | None:
        return self._get_generic_key("_image_keys", self.nexus_path.IMG_KEY_PATH)

    @property
    def image_key_control(self) -> list | None:
        return self._get_generic_key(
            "_image_keys_control", self.nexus_path.IMG_KEY_CONTROL_PATH
        )

    @property
    def sequence_number(self) -> tuple[int] | None:
        """index of each frame in the acquisition sequence. Specific to nexus"""
        if self.nexus_version is None or self.nexus_version >= 1.5:
            sequence_number = self._get_generic_key(
                "_sequence_number",
                "/".join(
                    [
                        self.nexus_path.INSTRUMENT_PATH,
                        self.nexus_path.nx_instrument_paths.DETECTOR_PATH,
                        self.nexus_path.nx_detector_paths.SEQUENCE_NUMBER,
                    ]
                ),
            )
            if sequence_number is not None:
                return tuple([int(index) for index in sequence_number])
        else:
            return None

    @property
    def count_time(self) -> list | None:
        return self._get_generic_key(
            "_count_time",
            self.nexus_path.EXPOSURE_TIME_PATH,
            returned_unit=_ureg.second,
            default_unit=_ureg.second,
        )

    @property
    @deprecated(replacement="count_time", since_version="1.0.0")
    def exposure_time(self) -> list | None:
        return self.count_time

    @property
    def machine_current(self) -> list | None:
        return self._get_generic_key(
            "_machine_current",
            self.nexus_path.ELECTRIC_CURRENT_PATH,
            default_unit=_ureg.ampere,
            returned_unit=_ureg.ampere,
        )

    @property
    @deprecated(
        replacement="detector_is_lr_flip", since_version="2.2.0", reason="renaming"
    )
    def x_flipped(self) -> bool:
        return self.detector_is_lr_flip

    @property
    def detector_is_lr_flip(self) -> bool:
        if self.nexus_path.nx_detector_paths.X_FLIPPED is not None:
            # backward compatibily: before NXTransformations was implemented
            return self._get_generic_key(
                "_x_flipped",
                "/".join(
                    [
                        self.nexus_path.INSTRUMENT_PATH,
                        self.nexus_path.nx_instrument_paths.DETECTOR_PATH,
                        self.nexus_path.nx_detector_paths.X_FLIPPED,
                    ]
                ),
            )
        elif self.nexus_path.nx_detector_paths.NX_TRANSFORMATIONS:
            transformations = self.detector_transformations
            if transformations is None:
                return None
            elif self.coordinate_system is CoordinateSystem.ESRF:
                # backward compatibily: before NXtomomill 2.0 and nxtomo 3.0 (not matching McStas)
                return DetZFlipTransformation(flip=True) in transformations
            elif self.coordinate_system is CoordinateSystem.McStas:
                return DetYFlipTransformation(flip=True) in transformations
            else:
                raise NotImplementedError
        else:
            return None

    @property
    @deprecated(
        replacement="detector_is_lr_flip", since_version="2.2.0", reason="renaming"
    )
    def y_flipped(self) -> bool:
        return self.detector_is_ud_flip

    @property
    def detector_is_ud_flip(self) -> bool:
        if self.nexus_path.nx_detector_paths.Y_FLIPPED is not None:
            # backward compatibily: before NXTransformations was implemented
            return self._get_generic_key(
                "_y_flipped",
                "/".join(
                    [
                        self.nexus_path.INSTRUMENT_PATH,
                        self.nexus_path.nx_instrument_paths.DETECTOR_PATH,
                        self.nexus_path.nx_detector_paths.Y_FLIPPED,
                    ]
                ),
            )
        elif self.nexus_path.nx_detector_paths.NX_TRANSFORMATIONS:
            transformations = self.detector_transformations
            if transformations is None:
                return None
            elif self.coordinate_system is CoordinateSystem.ESRF:
                return DetYFlipTransformation(flip=True) in transformations
            elif self.coordinate_system is CoordinateSystem.McStas:
                return DetXFlipTransformation(flip=True) in transformations
        else:
            return None

    @property
    def detector_transformations(self) -> tuple | None:
        """
        return tuple of `Transformation` affecting the NXdetector
        """
        if self._detector_transformations is None:
            det_transformations = []
            # bacward compatiblity, try to find x_flipped and y_flipped and convert it to `transformation`
            if (self.nexus_version or LATEST_NXTOMO_VERSION) < 1.3:
                try:
                    with open_hdf5(self.master_file) as h5_file:
                        x_flipped = h5_file.get(
                            "/".join(
                                [
                                    self._entry,
                                    self.nexus_path.INSTRUMENT_PATH,
                                    self.nexus_path.nx_instrument_paths.DETECTOR_PATH,
                                    self.nexus_path.nx_detector_paths.X_FLIPPED,
                                ]
                            )
                        )
                        y_flipped = h5_file.get(
                            "/".join(
                                [
                                    self._entry,
                                    self.nexus_path.INSTRUMENT_PATH,
                                    self.nexus_path.nx_instrument_paths.DETECTOR_PATH,
                                    self.nexus_path.nx_detector_paths.Y_FLIPPED,
                                ]
                            )
                        )
                except (OSError, KeyError):
                    _logger.info(
                        f"Failed to find any track of detector flip (nexus version is {self.nexus_version})"
                    )
                    return None
                else:
                    det_transformations = []
                    prev_trans = None
                    prev_trans = DetZFlipTransformation(
                        flip=x_flipped, depends_on=prev_trans
                    )
                    det_transformations.append(
                        prev_trans,
                    )
                    prev_trans = DetYFlipTransformation(
                        flip=y_flipped, depends_on=prev_trans.axis_name
                    )
                    det_transformations.append(
                        prev_trans,
                    )

            else:
                transformations = NXdetector.load_transformations(
                    file_path=self.master_file,
                    data_path="/".join(
                        [
                            self.entry,
                            self.nexus_path.INSTRUMENT_PATH,
                            self.nexus_path.nx_instrument_paths.DETECTOR_PATH,
                        ]
                    ),
                    nexus_version=self.nexus_version,
                )
                if transformations is not None:
                    det_transformations = transformations.transformations
            self._detector_transformations = tuple(det_transformations)
        return tuple(self._detector_transformations)

    @docstring(TomoScanBase)
    def get_bounding_box(self, axis: str | int | None = None) -> tuple:
        """
        Return the bounding box covered by the scan (only take into account the projections).
        axis is expected to be in (0, 1, 2) or (x==0, y==1, z==2)

        :note: current pixel size is given with magnification. To move back to sample space (x_translation, y_translation, z_translation)
               we need to `unmagnified` this is size
        """
        if axis is None:
            x_bb = self.get_bounding_box(axis="x")
            y_bb = self.get_bounding_box(axis="y")
            z_bb = self.get_bounding_box(axis="z")
            return BoundingBox3D(
                (z_bb.min, y_bb.min, x_bb.min),
                (z_bb.max, y_bb.max, x_bb.max),
            )

        if axis == 0:
            axis = "z"
        elif axis == 1:
            axis = "y"
        elif axis == 2:
            axis = "x"
        if axis not in ("x", "y", "z"):
            raise ValueError(
                f"Axis is expected to be in ('x', 'y', 'z', 0, 1, 2). Got {axis}."
            )

        if axis == "x":
            translations = self.x_translation
            default_pixel_size = self.sample_x_pixel_size
            n_pixel = self.dim_1
        elif axis == "y":
            translations = self.y_translation
            default_pixel_size = self.sample_y_pixel_size
            n_pixel = self.dim_2
        elif axis == "z":
            translations = self.z_translation
            default_pixel_size = self.sample_y_pixel_size
            n_pixel = self.dim_2
        else:
            raise ValueError(
                f"Axis is expected to be in ('x', 'y', 'z', 0, 1, 2). Got {axis}."
            )

        if translations is None or len(translations) == 0:
            raise ValueError(f"Unable to find translation for axis {axis}")
        translations = numpy.asarray(translations)
        # TODO: might need to filter only the projection one ?
        filetered_translation_for_proj = translations[
            self.image_key_control == ImageKey.PROJECTION.value
        ]
        min_axis_translation = filetered_translation_for_proj.min()
        max_axis_translation = filetered_translation_for_proj.max()
        if default_pixel_size is None:
            raise ValueError(f"Unable to find pixel size for axis {axis}")
        if n_pixel is None:
            raise ValueError(f"Unable to find number of pixel for axis {axis}")

        min_pos_in_meter = min_axis_translation - (n_pixel / 2.0 * default_pixel_size)
        max_pos_in_meter = max_axis_translation + (n_pixel / 2.0 * default_pixel_size)
        return BoundingBox1D(min_pos_in_meter, max_pos_in_meter)

    def _get_generic_key(
        self,
        key_name,
        path_key_name,
        returned_unit: pint.Unit | None = None,
        default_unit: pint.Unit | None = None,
        apply_function=None,
        is_attribute=False,
    ):
        if not isinstance(default_unit, (type(None), pint.Unit)):
            raise TypeError(
                f"'default_unit' must be an instance of {pint.Unit} or None. Not {type(default_unit)}"
            )
        if not isinstance(returned_unit, (type(None), pint.Unit)):
            raise TypeError(
                f"'returned_unit' must be an instance of {pint.Unit} or None. Not {type(returned_unit)}"
            )

        if getattr(self, key_name, None) is None:
            self._check_hdf5scan_validity()
            with open_hdf5(self.master_file) as h5_file:
                if is_attribute and path_key_name in h5_file[self._entry].attrs:
                    attr_val = h5py_read_attribute(
                        h5_file[self._entry].attrs, name=path_key_name
                    )
                    if apply_function is not None:
                        attr_val = apply_function(attr_val)
                elif not is_attribute and path_key_name in h5_file[self._entry]:
                    if default_unit is not None:
                        attr_val = self._get_value(
                            h5_file[self._entry][path_key_name],
                            default_unit=default_unit,
                        )
                        attr_val = attr_val.to(returned_unit).magnitude
                    else:
                        attr_val = h5py_read_dataset(
                            h5_file[self._entry][path_key_name]
                        )
                    if apply_function is not None:
                        attr_val = apply_function(attr_val)
                else:
                    attr_val = None
            setattr(self, key_name, attr_val)
        return getattr(self, key_name)

    @docstring(TomoScanBase.dark_n)
    @property
    def dark_n(self) -> int | None:
        if self.darks is not None:
            return len(self.darks)
        else:
            return None

    @docstring(TomoScanBase.flat_n)
    @property
    def flat_n(self) -> int | None:
        splitted_flats = self.splitted_flat_series
        if splitted_flats is not None and len(splitted_flats) > 0:
            return len(splitted_flats[0])
        else:
            return None

    @property
    @deprecated(replacement="splitted_flat_series", since_version="2.1")
    def splitted_flat_serie(self):
        return self.splitted_flat_series

    @property
    def splitted_flat_series(self) -> dict | None:
        """split flat according to flat indices"""
        if self.flats is None:
            return None
        else:
            flat_indexes = numpy.array(tuple(self.flats.keys()))
            # group contiguous flats (if differences of indices is > 1 then we consider this is part of another series)
            group_indices = numpy.split(
                flat_indexes, numpy.where(numpy.diff(flat_indexes) != 1)[0] + 1
            )
            # previous function can return some 'empty' arrays. Let's filter them
            contiguous_indices_groups = filter(
                lambda array: len(array) > 0,
                group_indices,
            )
            #  lets recreate the dict of flats with index as key and original value
            series = list()
            for contiguous_indices in contiguous_indices_groups:
                series.append(
                    {
                        flat_index: self.flats[flat_index]
                        for flat_index in contiguous_indices
                    }
                )
            return tuple(series)

    @docstring(TomoScanBase.ff_interval)
    @property
    def ff_interval(self):
        raise NotImplementedError(
            "not implemented for hdf5. But we have " "acquisition sequence instead."
        )

    @docstring(TomoScanBase.scan_range)
    @property
    def scan_range(self) -> int | None:
        """For now scan range should return 180 or 360. We don't expect other value."""
        if (
            self._scan_range is None
            and self.master_file
            and os.path.exists(self.master_file)
            and self._entry is not None
        ):
            rotation_angle = self.rotation_angle
            if rotation_angle is not None:
                angle_range = numpy.max(rotation_angle) - numpy.min(rotation_angle)
                dist_to180 = abs(180 - angle_range)
                dist_to360 = abs(360 - angle_range)
                if dist_to180 < dist_to360:
                    self._scan_range = 180
                else:
                    self._scan_range = 360
        return self._scan_range

    @property
    def dim_1(self) -> int | None:
        if self._dim_1 is None:
            self._get_dim1_dim2()
        return self._dim_1

    @property
    def dim_2(self) -> int | None:
        if self._dim_2 is None:
            self._get_dim1_dim2()
        return self._dim_2

    @property
    def pixel_size(self) -> float | None:
        return self.sample_x_pixel_size

    def get_sample_pixel_size(self, which="x", fallback_to_det_pixel_size: bool = True):
        """
        Retrieve x or y sample pixel size.

        :param fallback_to_det_pixel_size: In some case we want to make sure we retrieve a pixel size no matter of the nexus version (when reconstructing in nabu for example).
            but sometime having an empty value (even if the detector pixel size is given) can also be expected.
        """
        which = which.lower()
        nxpath = self.nexus_path
        if which == "x":
            attr_name = "_sample_x_pixel_size"
            det_pix_size_path = nxpath.nx_detector_paths.X_PIXEL_SIZE
            sample_pix_size_path = nxpath.nx_sample_paths.X_PIXEL_SIZE
        elif which == "y":
            attr_name = "_sample_y_pixel_size"
            det_pix_size_path = nxpath.nx_detector_paths.Y_PIXEL_SIZE
            sample_pix_size_path = nxpath.nx_sample_paths.Y_PIXEL_SIZE
        else:
            raise ValueError("Expected 'which' to be either 'x' or 'y'")

        # before nxtomo version 1.5 there was only one "pixel size" considered: the detectors + optics pixel size.
        # The sample voxel size was taken equal to this pixel size, which only works in parallel geometry
        detector_pixel_size_path = f"{nxpath.INSTRUMENT_PATH}/{nxpath.nx_instrument_paths.DETECTOR_PATH}/{det_pix_size_path}"
        sample_pixel_size_path = f"{nxpath.SAMPLE_PATH}/{sample_pix_size_path}"
        lookup_paths = []

        # Starting from nxtomo 1.5, sample voxel size is accessed at 'sample/{x|y}_pixel_size'
        if self.nexus_version is None or self.nexus_version >= 1.5:
            lookup_paths = [sample_pixel_size_path]
        if fallback_to_det_pixel_size:
            lookup_paths.append(detector_pixel_size_path)

        ret = None
        for path in lookup_paths:
            ret = self._get_generic_key(
                attr_name,
                path,
                returned_unit=_ureg.meter,
                default_unit=_ureg.micrometer,
            )
            if ret is not None:
                return ret
        return ret

    @property
    def sample_x_pixel_size(self) -> float | None:
        """sample x pixel size in meter"""
        return self.get_sample_pixel_size(which="x")

    @property
    def sample_y_pixel_size(self) -> float | None:
        """sample y pixel size in meter"""
        return self.get_sample_pixel_size(which="y")

    @property
    @deprecated(
        reason="will be removed",
        replacement="detector_x_pixel_size",
        since_version="2.2",
    )
    def x_real_pixel_size(self) -> float | None:
        return self.detector_x_pixel_size

    @property
    @deprecated(
        reason="will be removed",
        replacement="detector_y_pixel_size",
        since_version="2.2",
    )
    def y_real_pixel_size(self) -> float | None:
        return self.detector_y_pixel_size

    @property
    def detector_x_pixel_size(self) -> float | None:
        """return y pixel size in meter"""

        return self._get_generic_key(
            "_detector_x_pixel_size",
            "/".join(
                (
                    self.nexus_path.INSTRUMENT_PATH,
                    self.nexus_path.nx_instrument_paths.DETECTOR_PATH,
                    self.nexus_path.nx_detector_paths.X_PIXEL_SIZE,
                )
            ),
            returned_unit=_ureg.meter,
            default_unit=_ureg.micrometer,
        )

    @property
    def detector_y_pixel_size(self) -> float | None:
        """return y pixel size in meter"""

        return self._get_generic_key(
            "_detector_y_pixel_size",
            "/".join(
                (
                    self.nexus_path.INSTRUMENT_PATH,
                    self.nexus_path.nx_instrument_paths.DETECTOR_PATH,
                    self.nexus_path.nx_detector_paths.Y_PIXEL_SIZE,
                )
            ),
            returned_unit=_ureg.meter,
            default_unit=_ureg.micrometer,
        )

    def _get_fov(self):
        with open_hdf5(self.master_file) as h5_file:
            if self.nexus_path.FOV_PATH in h5_file[self._entry]:
                fov = h5py_read_dataset(h5_file[self._entry][self.nexus_path.FOV_PATH])
                return FOV(fov)
            else:
                return None

    def _get_dim1_dim2(self):
        if self.master_file and os.path.exists(self.master_file):
            if self.projections is not None:
                if len(self.projections) > 0:
                    url = list(self.projections.values())[0]
                    try:
                        with open_hdf5(url.file_path()) as h5s:
                            self._dim_2, self._dim_1 = h5s[url.data_path()].shape[-2:]
                    except Exception:
                        self._dim_2, self._dim_1 = get_data(
                            list(self.projections.values())[0]
                        ).shape

    @property
    def sample_detector_distance(self) -> float | None:
        """return sample detector distance in meter"""
        return self._get_generic_key(
            "_sample_detector_distance",
            self.nexus_path.SAMPLE_DETECTOR_DISTANCE_PATH,
            returned_unit=_ureg.meter,
            default_unit=_ureg.millimeter,
        )

    @property
    @docstring(TomoScanBase.source_sample_distance)
    def source_sample_distance(self) -> float | None:
        return self._get_generic_key(
            "_source_sample_distance",
            "/".join(
                [
                    self.nexus_path.INSTRUMENT_PATH,
                    self.nexus_path.nx_instrument_paths.SOURCE,
                    self.nexus_path.nx_source_paths.DISTANCE,
                ]
            ),
            returned_unit=_ureg.meter,
            default_unit=_ureg.millimeter,
        )

    @property
    def propagation_distance(self) -> float | None:
        if self.nexus_version is None or self.nexus_version >= 1.5:
            return self._get_generic_key(
                key_name="_propagation_distance",
                path_key_name="/".join(
                    [
                        self.nexus_path.SAMPLE_PATH,
                        self.nexus_path.nx_sample_paths.PROPAGATION_DISTANCE,
                    ]
                ),
                returned_unit=_ureg.meter,
                default_unit=_ureg.meter,
            )
        else:
            return None

    @property
    @docstring(TomoScanBase.field_of_view)
    def field_of_view(self):
        if self._fov is None and self.master_file and os.path.exists(self.master_file):
            self._fov = self._get_fov()
        return self._fov

    @property
    @docstring(TomoScanBase.x_rotation_axis_pixel_position)
    def x_rotation_axis_pixel_position(self):
        cast_to_float = lambda x: float(x)
        x_rot_path = (
            self.nexus_path.nx_detector_paths.X_ROTATION_AXIS_PIXEL_POSITION
            or self.nexus_path.nx_detector_paths.ESTIMATED_COR_FRM_MOTOR
        )
        if x_rot_path is not None:
            nexus_paths = _get_nexus_paths(self.nexus_version)
            x_rot_path = f"{nexus_paths.INSTRUMENT_PATH}/{self.nexus_path.nx_instrument_paths.DETECTOR_PATH}/{x_rot_path}"

            return self._get_generic_key(
                "_x_rotation_axis_pixel_position",
                x_rot_path,
                apply_function=cast_to_float,
            )

    @property
    def energy(self) -> float | None:
        """energy in keV"""
        energy_si: float | None = self._get_generic_key(
            "_energy",
            self.nexus_path.ENERGY_PATH,
            default_unit=_ureg.keV,
            returned_unit=_ureg.eV,
        )
        if energy_si is None:
            return None
        else:
            # has for energy we do an exception we don't use SI but kev
            energy_kev = (energy_si * _ureg.eV).to(_ureg.keV).magnitude
            return energy_kev

    @property
    def start_time(self):
        return self._get_generic_key("_start_time", self.nexus_path.START_TIME_PATH)

    @property
    def end_time(self):
        return self._get_generic_key("_end_time", self.nexus_path.END_TIME_PATH)

    @property
    def intensity_monitor(self):
        return self._get_generic_key(
            "_intensity_monitor", self.nexus_path.INTENSITY_MONITOR_PATH
        )

    @deprecated(
        reason="moved", replacement="get_bliss_original_files", since_version="2.1"
    )
    def get_bliss_orginal_files(self) -> str | None:
        self.get_bliss_original_files()

    def get_bliss_original_files(self) -> str | None:
        return self._get_generic_key("_bliss_original_files", "bliss_original_files")

    @property
    def frames(self) -> tuple | None:
        """return tuple of frames. Frames contains"""
        if self._frames is None:
            image_keys = self.image_key
            rotation_angles = self.rotation_angle
            x_translation = self.x_translation
            if x_translation is None and image_keys is not None:
                x_translation = [None] * len(image_keys)
            y_translation = self.y_translation
            if y_translation is None and image_keys is not None:
                y_translation = [None] * len(image_keys)
            z_translation = self.z_translation
            if z_translation is None and image_keys is not None:
                z_translation = [None] * len(image_keys)
            intensity_monitor = self.intensity_monitor
            if intensity_monitor is None and image_keys is not None:
                intensity_monitor = [None] * len(image_keys)
            if image_keys is not None and len(image_keys) != len(rotation_angles):
                raise ValueError(
                    "`rotation_angle` and `image_key` have incoherent size "
                    f"({len(rotation_angles)} vs {len(image_keys)}). Unable to deduce frame properties"
                )
            self._frames = []
            if self.__detector_broken_vds_behavior["run_check"]:
                self._checkDetectorDataset()

            if image_keys is None:
                # in the case there is no frame / image keys registered at all
                return self._frames

            sequence_number = self.sequence_number
            if sequence_number is None:
                _logger.info("No sequence number found. Will take logical order")
                n_frames = len(rotation_angles)
                sequence_number = [
                    int(index)
                    for index in numpy.linspace(
                        0, n_frames, n_frames, endpoint=False, dtype=numpy.uint32
                    )
                ]
            elif len(sequence_number) != len(rotation_angles):
                _logger.warning(
                    "incoherent number of rotation angle vs sequence number"
                )

            for i_frame, (
                frame_seq_num,
                rot_a,
                img_key,
                x_tr,
                y_tr,
                z_tr,
                i_m,
            ) in enumerate(
                zip(
                    sequence_number,
                    rotation_angles,
                    image_keys,
                    x_translation,
                    y_translation,
                    z_translation,
                    intensity_monitor,
                )
            ):
                url = DataUrl(
                    file_path=self.master_file,
                    data_slice=(i_frame),
                    data_path=self.get_detector_data_path(),
                    scheme="silx",
                )

                frame = TomoFrame(
                    index=i_frame,
                    sequence_number=frame_seq_num,
                    url=url,
                    image_key=img_key,
                    rotation_angle=rot_a,
                    x_translation=x_tr,
                    y_translation=y_tr,
                    z_translation=z_tr,
                    intensity_monitor=i_m,
                )
                if self.image_key_control is not None:
                    try:
                        is_control_frame = (
                            ImageKey(int(self.image_key_control[frame.index]))
                            is ImageKey.ALIGNMENT
                        )
                    except KeyError:
                        _logger.warning(
                            f"Unable to deduce if frame number {frame.index} is a control frame. Consider it is not"
                        )
                        is_control_frame = False
                else:
                    # if there is no image_key_control it is ambiguous to determine which
                    # projection is a return or not. Even if an angle is repeated this wouldn't be sure at 100%
                    # so the better is to consider there is no return / alignment projection
                    is_control_frame = False
                frame.is_control = is_control_frame
                self._frames.append(frame)
            self._frames = tuple(self._frames)
        return self._frames

    @docstring(TomoScanBase.get_proj_angle_url)
    def get_proj_angle_url(self) -> dict | None:
        if self.frames is not None:
            res = {}
            for frame in self.frames:
                if frame.image_key is ImageKey.PROJECTION:
                    if frame.is_control is False:
                        res[frame.rotation_angle] = frame.url
                    else:
                        res[str(frame.rotation_angle) + "(1)"] = frame.url
            return res
        else:
            return None

    def _get_sinogram_ref_imp(self, line, subsampling=1):
        """call the reference implementation of get_sinogram.
        Used for unit test and insure the result is the same as get_sinogram
        """
        return TomoScanBase.get_sinogram(self, line=line, subsampling=subsampling)

    @docstring(TomoScanBase)
    def get_sinogram(
        self,
        line,
        subsampling=1,
        norm_method: str | None = None,
        **kwargs,
    ) -> numpy.array:
        if (
            len(self.projections) is not None
            and self.dim_2 is not None
            and line > self.dim_2
        ) or line < 0:
            raise ValueError(f"requested line {line} is not in the scan")

        if not isinstance(subsampling, int):
            raise TypeError("subsampling expected to be an int")
        if subsampling <= 0:
            raise ValueError("subsampling expected to be higher than 1")

        if self.projections is not None:
            # get the z line
            with open_hdf5(self.master_file) as h5f:
                raw_sinogram = h5f[self.get_detector_data_path()][:, line, :]

            assert raw_sinogram.ndim == 2
            ignored_projs = []
            if self.ignore_projections is not None:
                ignored_projs = self.ignore_projections

            def is_pure_projection(frame: TomoFrame):
                return (
                    frame.image_key is ImageKey.PROJECTION
                    and not frame.is_control
                    and frame.index not in ignored_projs
                )

            is_projection_array = numpy.array(
                [is_pure_projection(frame) for frame in self.frames]
            )
            # TODO: simplify & reduce with filter or map ?
            proj_indexes = []
            for x, y in zip(self.frames, is_projection_array):
                if bool(y) is True:
                    proj_indexes.append(x.index)

            raw_sinogram = raw_sinogram[is_projection_array, :]
            assert len(raw_sinogram) == len(
                proj_indexes
            ), "expect to get project indexes of the sinogram"
            assert raw_sinogram.ndim == 2, "sinogram is expected to be 2D"
            # now apply flat field correction on each line
            res = []
            for z_frame_raw_sino, proj_index in zip(raw_sinogram, proj_indexes):
                assert z_frame_raw_sino.ndim == 1
                line_corrected = self.flat_field_correction(
                    projs=(z_frame_raw_sino,),
                    proj_indexes=[
                        proj_index,
                    ],
                    line=line,
                )[0]
                assert isinstance(line_corrected, numpy.ndarray)
                assert line_corrected.ndim == 1
                res.append(line_corrected)
            sinogram = numpy.array(res)
            assert sinogram.ndim == 2
            # apply subsampling (could be speed up but not sure this is useful
            # compare to complexity that we would need to had
            return self._apply_sino_norm(
                sinogram[::subsampling].copy(),
                line=line,
                norm_method=norm_method,
                **kwargs,
            )
        else:
            return None

    def get_detector_data_path(self) -> str:
        return self.entry + "/instrument/detector/data"

    @property
    def projections_compacted(self):
        """
        Return a compacted view of projection frames.

        :return: Dictionary where the key is a list of indices, and the value
            is the corresponding `silx.io.url.DataUrl` with merged data_slice
        """
        if self._projections_compacted is None:
            self._projections_compacted = get_compacted_dataslices(self.projections)
        return self._projections_compacted

    def __str__(self):
        file_id = os.sep.join(os.path.abspath(self.master_file).split(os.sep)[-3:])
        return f"NXtomo scan(master_file: {file_id}, entry: {self.entry})"

    @staticmethod
    def _get_value(node: h5py.Group, default_unit: pint.Unit) -> pint.Quantity:
        """convert the value contained in the node to the adapted unit.
        Unit can be defined in on of the group attributes. It it is the case
        will pick this unit, otherwise will use the default unit

        default_unit: unit to use if not in the metadata
        """
        if not isinstance(default_unit, pint.Unit):
            raise TypeError(
                f"default_unit must be an instance of {pint.Unit}. Not {type(default_unit)}"
            )
        value = h5py_read_dataset(node)
        if "unit" in node.attrs:
            unit = node.attrs["unit"]
        elif "units" in node.attrs:
            unit = node.attrs["units"]
        else:
            unit = str(default_unit)
        # handle Diamond dataset where unit is stored as bytes
        if hasattr(unit, "decode"):
            unit = unit.decode()
        if unit == "kev":
            unit = "keV"
        unit = pint.Unit(unit)
        return value * unit

    def _check_hdf5scan_validity(self):
        """some basic check to make sure both the master file (.nx file) and requested entry (data_path) exists"""
        if self.master_file is None:
            raise ValueError("No master file provided")
        if self.entry is None:
            raise ValueError("No entry provided")
        with open_hdf5(self.master_file) as h5_file:
            if self._entry not in h5_file:
                raise ValueError(
                    f"Given entry {self._entry} is not in the master file {self.master_file}"
                )

    def _checkDetectorDataset(self):
        """check that detector dataset is valid - especially in the case this is a vds"""

        if os.getenv("TOMOTOOLS_SKIP_DET_CHECK", "0").lower() in (
            "1",
            "y",
        ):
            _logger.warning(
                " skipping virtual datasets check because of SKIP_TOMOSCAN_CHECK"
            )
            return

        url = DataUrl(
            file_path=os.path.abspath(self.master_file),
            data_path=self.get_detector_data_path(),
        )
        _, unique_files = dataset_has_broken_vds(
            url=url,
            raise_error=self.__detector_broken_vds_behavior["raise_error"],
            log_level=self.__detector_broken_vds_behavior["log_level"],
            return_unique_files=True,
        )
        check_possible_issue_with_rlimit(
            url=url,
            raise_error=self.__detector_broken_vds_behavior["raise_error"],
            log_level=self.__detector_broken_vds_behavior["log_level"],
            unique_files=unique_files,
        )

    def get_flat_expected_location(self):
        return DataUrl(
            file_path=self.master_file,
            data_path=_get_nexus_paths(self.nexus_version).PROJ_PATH,
        ).path()

    def get_dark_expected_location(self):
        return DataUrl(
            file_path=self.master_file,
            data_path=_get_nexus_paths(self.nexus_version).PROJ_PATH,
        ).path()

    def get_projection_expected_location(self):
        return DataUrl(
            file_path=self.master_file,
            data_path=_get_nexus_paths(self.nexus_version).PROJ_PATH,
        ).path()

    def get_energy_expected_location(self):
        return DataUrl(
            file_path=self.master_file,
            data_path=_get_nexus_paths(self.nexus_version).ENERGY_PATH,
        ).path()

    def get_sample_detector_distance_expected_location(self):
        return DataUrl(
            file_path=self.master_file,
            data_path=_get_nexus_paths(
                self.nexus_version
            ).SAMPLE_DETECTOR_DISTANCE_PATH,
        ).path()

    def get_pixel_size_expected_location(self):
        return DataUrl(
            file_path=self.master_file,
            data_path=_get_nexus_paths(self.nexus_version).X_PIXEL_SIZE_PATH,
        ).path()

    @docstring(TomoScanBase.get_relative_file)
    def get_relative_file(self, file_name: str, with_dataset_prefix=True) -> str | None:
        if self.path is not None:
            if with_dataset_prefix:
                basename = self.get_dataset_basename()
                basename = "_".join((basename, file_name))
                return os.path.join(self.path, basename)
            else:
                return os.path.join(self.path, file_name)
        else:
            return None

    def get_dataset_basename(self) -> str:
        basename, _ = os.path.splitext(self.master_file)
        return os.path.basename(basename)

    @docstring(TomoScanBase)
    def save_reduced_darks(
        self,
        darks: dict,
        output_urls: tuple = REDUCED_DARKS_DATAURLS,
        darks_infos=None,
        metadata_output_urls=REDUCED_DARKS_METADATAURLS,
        overwrite: bool = False,
    ):
        """
        Dump computed dark (median / mean...) into files
        """
        super().save_reduced_darks(
            darks=darks,
            output_urls=output_urls,
            darks_infos=darks_infos,
            metadata_output_urls=metadata_output_urls,
            overwrite=overwrite,
        )

    @docstring(TomoScanBase)
    def load_reduced_darks(
        self,
        inputs_urls: tuple = REDUCED_DARKS_DATAURLS,
        metadata_input_urls=REDUCED_DARKS_METADATAURLS,
        return_as_url: bool = False,
        return_info: bool = False,
    ) -> dict:
        """
        load computed dark (median / mean...) into files
        """
        return super().load_reduced_darks(
            inputs_urls=inputs_urls,
            metadata_input_urls=metadata_input_urls,
            return_as_url=return_as_url,
            return_info=return_info,
        )

    @docstring(TomoScanBase)
    def save_reduced_flats(
        self,
        flats: dict,
        output_urls: tuple = REDUCED_FLATS_DATAURLS,
        flats_infos=None,
        metadata_output_urls: tuple = REDUCED_FLATS_METADATAURLS,
        overwrite: bool = False,
    ) -> dict:
        """
        Dump computed flats (median / mean...) into files
        """
        super().save_reduced_flats(
            flats=flats,
            metadata_output_urls=metadata_output_urls,
            output_urls=output_urls,
            flats_infos=flats_infos,
            overwrite=overwrite,
        )

    @docstring(TomoScanBase)
    def load_reduced_flats(
        self,
        inputs_urls: tuple = REDUCED_FLATS_DATAURLS,
        metadata_input_urls=REDUCED_FLATS_METADATAURLS,
        return_as_url: bool = False,
        return_info: bool = False,
    ) -> dict:
        """
        load computed dark (median / mean...) into files
        """
        return super().load_reduced_flats(
            inputs_urls=inputs_urls,
            metadata_input_urls=metadata_input_urls,
            return_as_url=return_as_url,
            return_info=return_info,
        )

    @docstring(TomoScanBase.compute_reduced_flats)
    def compute_reduced_flats(
        self,
        reduced_method="median",
        overwrite=True,
        output_dtype=numpy.float32,
        return_info: bool = False,
    ):
        return super().compute_reduced_flats(
            reduced_method=reduced_method,
            overwrite=overwrite,
            output_dtype=output_dtype,
            return_info=return_info,
        )

    @docstring(TomoScanBase.compute_reduced_flats)
    def compute_reduced_darks(
        self,
        reduced_method="mean",
        overwrite=True,
        output_dtype=numpy.float32,
        return_info: bool = False,
    ):
        return super().compute_reduced_darks(
            reduced_method=reduced_method,
            overwrite=overwrite,
            output_dtype=output_dtype,
            return_info=return_info,
        )

    @staticmethod
    @docstring(TomoScanBase)
    def from_identifier(identifier):
        """Return the Dataset from a identifier"""
        if not isinstance(identifier, NXtomoScanIdentifier):
            raise TypeError(
                f"identifier should be an instance of {NXtomoScanIdentifier}"
            )
        return NXtomoScan(scan=identifier.file_path, entry=identifier.data_path)

    @docstring(TomoScanBase)
    def get_identifier(self) -> ScanIdentifier:
        return NXtomoScanIdentifier(
            object=self, hdf5_file=self.master_file, entry=self.entry
        )

    def build_drac_metadata(self) -> dict:
        """
        build icat metadata dictionary filling NXtomo definition following icat definition: https://gitlab.esrf.fr/icat/hdf5-master-config/-/blob/88a975039694d5dba60e240b7bf46c22d34065a0/hdf5_cfg.xml
        """
        UNKNOW_VALUE = "unknow"

        def get_z_delta_and_z_start():
            if self.z_translation is None or len(self.z_translation) == 0:
                return UNKNOW_VALUE, UNKNOW_VALUE
            else:
                projection_z = numpy.array(self.z_translation)[
                    self.image_key_control == ImageKey.PROJECTION.value
                ]
                unique_z = numpy.unique(projection_z)
                if len(unique_z) > 1:
                    delta = unique_z[1] - unique_z[0]
                elif len(projection_z) > 0:
                    # in case z doesn't evolve with time
                    return 0, projection_z[0]
                else:
                    delta = UNKNOW_VALUE
                return unique_z[0], delta

        def get_exposure_time():
            if self.count_time is None or len(self.count_time) == 0:
                return UNKNOW_VALUE
            else:
                proj_count_time = self.count_time[
                    self.image_key_control == ImageKey.PROJECTION.value
                ]
                return proj_count_time[0] if len(proj_count_time) > 0 else UNKNOW_VALUE

        def get_pixel_size_micron():
            # icat expect the pixel size to be in micron...
            if self.pixel_size is None:
                return UNKNOW_VALUE
            else:
                return (self.pixel_size * _ureg.meter).to(_ureg.micrometer).magnitude

        def get_start_angle():
            if self.rotation_angle is None or len(self.rotation_angle) == 0:
                return UNKNOW_VALUE
            else:
                projection_rot_angle = numpy.array(self.rotation_angle)[
                    self.image_key_control == ImageKey.PROJECTION.value
                ]
                return (
                    projection_rot_angle[0]
                    if len(projection_rot_angle) > 0
                    else UNKNOW_VALUE
                )

        z_start, z_delta = get_z_delta_and_z_start()
        # If the information is not here avoid publishing it
        metadata = {
            "definition": "TOMO",
            "TOMO_ZStart": z_start,
            "TOMO_ZDelta": z_delta,
            "TOMO_accExposureTime": get_exposure_time(),
            "TOMO_pixelSize": get_pixel_size_micron(),
            "TOMO_start_angle": get_start_angle(),
            "TOMO_x_pixel_n": self.dim_1 if self.dim_1 is not None else UNKNOW_VALUE,
            "TOMO_y_pixel_n": self.dim_2 if self.dim_2 is not None else UNKNOW_VALUE,
        }
        if self.sample_name is not None:
            metadata["Sample_name"] = self.sample_name
            metadata["sample_name"] = self.sample_name
        if self.scan_range is not None:
            metadata["TOMO_scanRange"] = self.scan_range
        if self.field_of_view is not None:
            metadata["TOMO_halfAcquisition"] = str(self.field_of_view) is FOV.HALF
        if self.get_sample_detector_distance() is not None:
            metadata["TOMO_detectorDistance"] = (
                (self.get_sample_detector_distance() * _ureg.meter)
                .to(_ureg.micrometer)
                .magnitude
            )
        if self.flat_n is not None:
            metadata["TOMO_refN"] = self.flat_n
        if self.dark_n is not None:
            metadata["TOMO_darkN"] = self.dark_n
        if self.projections is not None:
            metadata["TOMO_projN"] = len(self.projections)

        return metadata


class TomoFrame:
    """class to store all metadata information of a NXTomo frame"""

    def __init__(
        self,
        index: int,
        sequence_number: int,
        url: DataUrl | None = None,
        image_key: None | ImageKey | int = None,
        rotation_angle: float | None = None,
        is_control_proj: bool = False,
        x_translation: float | None = None,
        y_translation: float | None = None,
        z_translation: float | None = None,
        intensity_monitor: float | None = None,
    ):
        if not isinstance(index, int):
            raise TypeError(
                f"index is expected to be an instance of {int}. Got {type(index)}"
            )
        self._index = index
        self._sequence_number = sequence_number
        if image_key is not None:
            self._image_key = ImageKey(image_key)
        else:
            self._image_key = None
        self._rotation_angle = rotation_angle
        self._url = url
        self._is_control_frame = is_control_proj
        self._data = None
        self._x_translation = x_translation
        self._y_translation = y_translation
        self._z_translation = z_translation
        self._intensity_monitor = intensity_monitor

    @property
    def index(self) -> int:
        """Index of the frame in the .nx file"""
        return self._index

    @property
    def sequence_number(self) -> int:
        """Sequence number of the frame in the acquisition !!! can be different from the index"""
        return self._sequence_number

    @property
    def image_key(self) -> ImageKey:
        return self._image_key

    @image_key.setter
    def image_key(self, image_key: ImageKey) -> None:
        if not isinstance(image_key, ImageKey):
            raise TypeError(f"{image_key} is expected to be an instance of {ImageKey}")
        self._image_key = image_key

    @property
    def rotation_angle(self) -> float:
        return self._rotation_angle

    @rotation_angle.setter
    def rotation_angle(self, angle: float) -> None:
        self._rotation_angle = angle

    @property
    def url(self) -> DataUrl:
        return self._url

    @property
    def is_control(self) -> bool:
        return self._is_control_frame

    @property
    def x_translation(self):
        return self._x_translation

    @property
    def y_translation(self):
        return self._y_translation

    @property
    def z_translation(self):
        return self._z_translation

    @property
    def intensity_monitor(self):
        return self._intensity_monitor

    @is_control.setter
    def is_control(self, is_return: bool):
        self._is_control_frame = is_return

    def __str__(self):
        return (
            "Frame {index},: image_key: {image_key},"
            "is_control: {is_control},"
            "rotation_angle: {rotation_angle},"
            "x_translation: {x_translation},"
            "y_translation: {y_translation},"
            "z_translation: {z_translation},"
            "url: {url}".format(
                index=self.index,
                image_key=self.image_key,
                is_control=self.is_control,
                rotation_angle=self.rotation_angle,
                url=self.url.path(),
                x_translation=self.x_translation,
                y_translation=self.y_translation,
                z_translation=self.z_translation,
            )
        )


class HDF5TomoScan(NXtomoScan):
    def __init__(
        self,
        scan: str,
        entry: str = None,
        index: int | None = 0,
        ignore_projections: Iterable | None = None,
        nx_version=None,
    ):
        deprecated_warning(
            type_="class",
            name="tomwer.core.scan.hdf5scan.HDF5TomoScan",
            replacement="tomwer.core.scan.nxtomo.NXtomoScan",
            since_version="2.0",
            reason="coherence",
        )
        super().__init__(scan, entry, index, ignore_projections, nx_version)
