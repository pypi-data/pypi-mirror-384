"""Scan dedicated for bliss format - based on EDF files"""

from __future__ import annotations

import pint
import copy
import io
import json
import logging
import os
import re
from typing import Iterable
import warnings

import fabio
import numpy
from lxml import etree
from silx.io.url import DataUrl


from tomoscan.utils.io import deprecated, deprecated_warning
from tomoscan.esrf.identifier.edfidentifier import EDFTomoScanIdentifier
from tomoscan.identifier import ScanIdentifier
from tomoscan.scanbase import Source, TomoScanBase
from tomoscan.utils import docstring

from .framereducer import EDFFrameReducer
from .utils import extract_urls_from_edf, get_parameters_frm_par_or_info

_ureg = pint.get_application_registry()
_logger = logging.getLogger(__name__)


__all__ = [
    "EDFTomoScan",
]


class EDFTomoScan(TomoScanBase):
    """
    TomoScanBase instanciation for scan defined from .edf files

    :param scan: path to the root folder containing the scan.
    :param dataset_basename: prefix of the dataset to handle
    :param scan_info: dictionary providing dataset information. Provided keys will overwrite information contained in .info.
                      Valid keys are: TODO
    :param n_frames: Number of frames in each EDF file.
        If not provided, it will be inferred by reading the files.
        In this case, the frame number is guessed from the file name.
    """

    _TYPE = "edf"

    INFO_EXT = ".info"

    ABORT_FILE = ".abo"

    _REFHST_PREFIX = "refHST"

    _DARKHST_PREFIX = "dark.edf"

    _SCHEME = "fabio"

    REDUCED_DARKS_DATAURLS = (
        DataUrl(
            file_path="{scan_prefix}_darks.hdf5",
            data_path="{entry}/darks/{index}",
            scheme="silx",
        ),  # _darks.hdf5 and _flats.hdf5 are the default location of the reduced darks and flats.
        DataUrl(file_path="dark.edf", scheme=_SCHEME),
    )

    REDUCED_DARKS_METADATAURLS = (
        DataUrl(
            file_path="{scan_prefix}_darks.hdf5",
            data_path="{entry}/darks/",
            scheme="silx",
        ),
        # even if no metadata urls are provided for EDF. If the output is the EDF metadata will be stored in the headers
    )

    REDUCED_FLATS_DATAURLS = (
        DataUrl(
            file_path="{scan_prefix}_flats.hdf5",
            data_path="{entry}/flats/{index}",
            scheme="silx",
        ),  # _darks.hdf5 and _flats.hdf5 are the default location of the reduced darks and flats.
        DataUrl(
            file_path="refHST{index_zfill4}.edf", scheme=_SCHEME
        ),  # .edf is kept for compatiblity
    )

    REDUCED_FLATS_METADATAURLS = (
        DataUrl(
            file_path="{scan_prefix}_flats.hdf5",
            data_path="{entry}/flats/",
            scheme="silx",
        ),
        # even if no metadata urls are provided for EDF. If the output is the EDF metadata will be stored in the headers
    )

    FRAME_REDUCER_CLASS = EDFFrameReducer

    def __init__(
        self,
        scan: str | None,
        dataset_basename: str | None = None,
        scan_info: dict | None = None,
        n_frames: int | None = None,
        ignore_projections: Iterable | None = None,
    ):
        TomoScanBase.__init__(
            self, scan=scan, type_=self._TYPE, ignore_projections=ignore_projections
        )

        # data caches
        self._darks = None
        self._flats = None
        self.__tomo_n = None
        self.__flat_n = None
        self.__dark_n = None
        self.__dim1 = None
        self.__dim2 = None
        self.__pixel_size = None
        self.__flat_on = None
        self.__scan_range = None
        self._edf_n_frames = n_frames
        self.__energy = None
        self._source = Source()
        """Source is not handle by EDFScan"""
        self._scan_info = None
        self.scan_info = scan_info
        self._dataset_basename = dataset_basename
        self._ignore_init = False
        # Used to handle ignored projections with EDF (done during reloading projections)
        self._projs_indices_and_angles = None

    def _rotation_angle(self):
        """
        Unofficial method for retrieving rotation angles.
        Can't do better without proper metadata.
        """
        if self.scan_range is None:
            raise ValueError("Need scan_range")
        fullturn = abs(self.scan_range - 360) < abs(self.scan_range - 180)
        angles = numpy.linspace(
            0, self.scan_range, num=self.tomo_n, endpoint=fullturn, dtype="f"
        )

        return angles

    def rotation_angle(self):
        if self.ignore_projections is None:
            return self._rotation_angle()
        else:
            all_indices, all_angles = self._projs_indices_and_angles
            ignored_indices = self.get_ignored_projection_indices()
            indices = sorted(list(set(all_indices) - set(ignored_indices)))
            return all_angles[indices]

    def _get_projs_indices_and_angles(self):
        # Caching is important, as projections indices will change once the ignore mechanism is applied!
        if self._projs_indices_and_angles is None:
            if self._projections is None:
                raise ValueError(
                    "Need _reload_projections (or evaluate self.projections)"
                )
            projs_indices = sorted(self._projections.keys())
            rot_angles = self._rotation_angle()  # heuristic, see above
            self._projs_indices_and_angles = projs_indices, rot_angles
        else:
            projs_indices, rot_angles = self._projs_indices_and_angles
        return projs_indices, rot_angles

    @property
    def scan_info(self) -> dict | None:
        return self._scan_info

    @scan_info.setter
    def scan_info(self, scan_info: dict | None) -> None:
        if not isinstance(scan_info, (type(None), dict)):
            raise TypeError("scan info is expected to be None or an instance of dict")
        used_keys = (
            "TOMO_N",
            "DARK_N",
            "REF_N",
            "REF_ON",
            "ScanRange",
            "Dim_1",
            "Dim_2",
            "Distance",
            "PixelSize",
            "SrCurrent",
        )
        other_keys = (
            "Prefix",
            "Directory",
            "Y_STEP",
            "Count_time",
            "Col_end",
            "Col_beg",
            "Row_end",
            "Row_beg",
            "Optic_used",
            "Date",
            "Scan_Type",
            "CCD_Mode",
            "CTAngle",
            "Min",
            "Max",
            "Sub_vols",
        )
        valid_keys = used_keys + other_keys
        valid_keys = [key.lower() for key in valid_keys]
        if isinstance(scan_info, dict):
            for key in scan_info.keys():
                if key not in valid_keys:
                    _logger.warning(f"{key} unrecognized. Valid keys are {valid_keys}")
        self._scan_info = scan_info

    @docstring(TomoScanBase.clear_cache)
    def clear_cache(self):
        super().clear_cache()
        self._projections = None
        self.__dim1 = None
        self.__dim2 = None
        self.__pixel_size = None

    def clear_frames_cache(self):
        self._darks = None
        self._flats = None
        self.__tomo_n = None
        self.__flat_n = None
        self.__dark_n = None
        self.__flat_on = None
        self.__scan_range = None
        super().clear_frames_cache()

    @docstring(TomoScanBase.tomo_n)
    @property
    def tomo_n(self) -> int | None:
        if self.__tomo_n is None:
            self.__tomo_n = EDFTomoScan.get_tomo_n(
                scan=self.path,
                dataset_basename=self.dataset_basename,
                scan_info=self.scan_info,
            )
        return self.__tomo_n

    @property
    @docstring(TomoScanBase.dark_n)
    def dark_n(self) -> int | None:
        if self.__dark_n is None:
            self.__dark_n = EDFTomoScan.get_dark_n(
                scan=self.path,
                dataset_basename=self.dataset_basename,
                scan_info=self.scan_info,
            )
        return self.__dark_n

    @property
    @docstring(TomoScanBase.flat_n)
    def flat_n(self) -> int | None:
        if self.__flat_n is None:
            self.__flat_n = EDFTomoScan.get_ref_n(
                scan=self.path,
                dataset_basename=self.dataset_basename,
                scan_info=self.scan_info,
            )
        return self.__flat_n

    @property
    @docstring(TomoScanBase.pixel_size)
    def pixel_size(self) -> int | None:
        """

        :return: pixel size
        """
        if self.__pixel_size is None:
            self.__pixel_size = EDFTomoScan._get_pixel_size(
                scan=self.path,
                dataset_basename=self.dataset_basename,
                scan_info=self.scan_info,
            )
        return self.__pixel_size

    @property
    def sample_x_pixel_size(self) -> float | None:
        """For EDF only square pixel size is handled"""
        return self.pixel_size

    @property
    def sample_y_pixel_size(self) -> float | None:
        """For EDF only square pixel size is handled"""
        return self.pixel_size

    @property
    def detector_x_pixel_size(self) -> float | None:
        # not provided by EDF at the moment
        return None

    @property
    def detector_y_pixel_size(self) -> float | None:
        # not provided by EDF at the moment
        return None

    @property
    @deprecated(replacement="", since_version="1.1.0")
    def x_real_pixel_size(self) -> float | None:
        if self.pixel_size is not None and self.magnification is not None:
            return self.pixel_size * self.magnification
        else:
            return None

    @property
    @deprecated(replacement="", since_version="1.1.0")
    def y_real_pixel_size(self) -> float | None:
        if self.pixel_size is not None and self.magnification is not None:
            return self.pixel_size * self.magnification
        else:
            return None

    @property
    @docstring(TomoScanBase.dim_1)
    def dim_1(self) -> int | None:
        """

        :return: image dim1
        """
        if self.__dim1 is None and self.path is not None:
            self.__dim1, self.__dim2 = EDFTomoScan.get_dim1_dim2(
                scan=self.path,
                dataset_basename=self.dataset_basename,
                scan_info=self.scan_info,
            )
        return self.__dim1

    @property
    @docstring(TomoScanBase.dim_2)
    def dim_2(self) -> int | None:
        """

        :return: image dim2
        """
        if self.__dim2 is None and self.path is not None:
            self.__dim1, self.__dim2 = EDFTomoScan.get_dim1_dim2(
                scan=self.path,
                dataset_basename=self.dataset_basename,
                scan_info=self.scan_info,
            )
        return self.__dim2

    @property
    @docstring(TomoScanBase.x_translation)
    def x_translation(self) -> tuple | None:
        _logger.warning("x_translation Not supported for EDF")
        return None

    @property
    @docstring(TomoScanBase.y_translation)
    def y_translation(self) -> tuple | None:
        _logger.warning("y_translation Not supported for EDF")
        return None

    @property
    @docstring(TomoScanBase.z_translation)
    def z_translation(self) -> tuple | None:
        _logger.warning("z_translation Not supported for EDF")
        return None

    @property
    @docstring(TomoScanBase.ff_interval)
    def ff_interval(self) -> int | None:
        if self.__flat_on is None and self.path is not None:
            self.__flat_on = EDFTomoScan.get_ff_interval(
                scan=self.path,
                dataset_basename=self.dataset_basename,
                scan_info=self.scan_info,
            )
        return self.__flat_on

    @property
    @docstring(TomoScanBase.scan_range)
    def scan_range(self) -> int | None:
        if self.__scan_range is None and self.path is not None:
            self.__scan_range = EDFTomoScan.get_scan_range(
                scan=self.path,
                dataset_basename=self.dataset_basename,
                scan_info=self.scan_info,
            )
        return self.__scan_range

    @property
    @docstring(TomoScanBase.flats)
    def flats(self) -> dict | None:
        """
        flats are given as a dictionary with index as key and DataUrl as
        value"""
        if self._flats is None and self.path is not None:
            self._flats = self.get_flats_url(
                scan_path=self.path,
                dataset_basename=self.dataset_basename,
            )
        return self._flats

    @property
    @docstring(TomoScanBase.projections)
    def projections(self) -> dict | None:
        if self._projections is None and self.path is not None:
            self._reload_projections()
        return self._projections

    @property
    @docstring(TomoScanBase.alignment_projections)
    def alignment_projections(self) -> None:
        if self._alignment_projections is None and self.path is not None:
            self._reload_projections()
        return self._alignment_projections

    @docstring(TomoScanBase.is_tomoscan_dir)
    @staticmethod
    def is_tomoscan_dir(
        directory: str, dataset_basename: str | None = None, **kwargs
    ) -> bool:
        return os.path.isfile(
            EDFTomoScan.get_info_file(
                directory=directory, dataset_basename=dataset_basename, kwargs=kwargs
            )
        )

    @staticmethod
    def get_info_file(
        directory: str, dataset_basename: str | None = None, **kwargs
    ) -> str:
        if dataset_basename is None:
            dataset_basename = os.path.basename(directory)
        assert dataset_basename != ""
        info_file = os.path.join(directory, dataset_basename + EDFTomoScan.INFO_EXT)

        if "src_pattern" in kwargs and kwargs["src_pattern"] is not None:
            assert "dest_pattern" in kwargs
            info_file = info_file.replace(
                kwargs["src_pattern"], kwargs["dest_pattern"], 1
            )
        return info_file

    @docstring(TomoScanBase.is_abort)
    def is_abort(self, **kwargs) -> bool:
        abort_file = self.dataset_basename + self.ABORT_FILE
        abort_file = os.path.join(self.path, abort_file)
        if "src_pattern" in kwargs and kwargs["src_pattern"] is not None:
            assert "dest_pattern" in kwargs
            abort_file = abort_file.replace(
                kwargs["src_pattern"], kwargs["dest_pattern"]
            )
        return os.path.isfile(abort_file)

    @property
    @docstring(TomoScanBase.darks)
    def darks(self) -> dict:
        if self._darks is None and self.path is not None:
            self._darks = self.get_darks_url(
                scan_path=self.path, dataset_basename=self.dataset_basename
            )
        return self._darks

    @docstring(TomoScanBase.get_proj_angle_url)
    def get_proj_angle_url(self) -> dict:
        # TODO: we might use fabio.open_serie instead
        if self.path is None:
            _logger.warning(
                "no path specified for scan, unable to retrieve the projections"
            )
            return {}
        n_projection = self.tomo_n
        data_urls = EDFTomoScan.get_proj_urls(
            self.path, dataset_basename=self.dataset_basename
        )
        return TomoScanBase.map_urls_on_scan_range(
            urls=data_urls, n_projection=n_projection, scan_range=self.scan_range
        )

    @docstring(TomoScanBase.update)
    def update(self):
        if self.path is not None:
            self._reload_projections()
            self._darks = EDFTomoScan.get_darks_url(self.path)
            self._flats = EDFTomoScan.get_flats_url(self.path)

    @docstring(TomoScanBase.load_from_dict)
    def load_from_dict(self, desc: dict | io.TextIOWrapper):
        if isinstance(desc, io.TextIOWrapper):
            data = json.load(desc)
        else:
            data = desc
        if not (self.DICT_TYPE_KEY in data and data[self.DICT_TYPE_KEY] == self._TYPE):
            raise ValueError("Description is not an EDFScan json description")

        assert self.DICT_PATH_KEY in data
        self.path = data[self.DICT_PATH_KEY]
        return self

    @staticmethod
    def get_proj_urls(
        scan: str,
        dataset_basename: str | None = None,
        n_frames: int | None = None,
    ) -> dict:
        """
        Return the dict of radios / projection for the given scan.
        Keys of the dictionary is the slice number
        Return all the file on the root of scan starting by the name of scan and
        ending by .edf

        :param scan: is the path to the folder of acquisition
        :param n_frames: Number of frames in each EDF file.
            If not provided, it is inferred by reading each file.
        :return: dict of radios files with radio index as key and file as value
        """
        urls = dict({})
        if (scan is None) or not (os.path.isdir(scan)):
            return urls
        if dataset_basename is None:
            dataset_basename = os.path.basename(scan)

        if os.path.isdir(scan):
            for f in os.listdir(scan):
                if EDFTomoScan.is_a_proj_path(
                    fileName=f, dataset_basename=dataset_basename, scanID=scan
                ):
                    gfile = os.path.join(scan, f)
                    index = EDFTomoScan.guess_index_frm_file_name(
                        gfile, basename=dataset_basename
                    )
                    urls.update(
                        extract_urls_from_edf(
                            start_index=index, file_=gfile, n_frames=n_frames
                        )
                    )

        return urls

    @staticmethod
    def is_a_proj_path(
        fileName: str, scanID: str, dataset_basename: str | None = None
    ) -> bool:
        """Return True if the given fileName can fit to a Radio name"""
        fileBasename = os.path.basename(fileName)
        if dataset_basename is None:
            dataset_basename = os.path.basename(scanID)

        if fileBasename.endswith(".edf") and fileBasename.startswith(dataset_basename):
            localstring = fileName.rstrip(".edf")
            # remove the scan
            localstring = re.sub(dataset_basename, "", localstring)
            if "slice_" in localstring:
                # case of a reconstructed file
                return False
            if "refHST" in localstring:
                return False
            s = localstring.split("_")
            if s[-1].isdigit():
                # check that the next value is a digit
                return True

        return False

    @staticmethod
    def guess_index_frm_file_name(_file: str, basename: str) -> int | None:
        """
        Guess the index of the file. Index is most of the an integer but can be
        a float for 'ref' for example if several are taken.

        :param _file:
        :param basename:
        """

        def extract_index(my_str, type_):
            res = []
            modified_str = copy.copy(my_str)
            while modified_str != "" and modified_str[-1].isdigit():
                res.append(modified_str[-1])
                modified_str = modified_str[:-1]
            if len(res) == 0:
                return None, modified_str
            else:
                orignalOrder = res[::-1]
                if type_ is int:
                    return int("".join(orignalOrder)), modified_str
                else:
                    return float(".".join(("0", "".join(orignalOrder)))), modified_str

        _file = os.path.basename(_file)
        if _file.endswith(".edf"):
            name = _file.replace(basename, "", 1)
            name = name.rstrip(".edf")

            part_1, name = extract_index(name, type_=int)
            if name.endswith("_"):
                name = name.rstrip("_")
                part_2, name = extract_index(name, type_=float)
            else:
                part_2 = None

            if part_1 is None:
                return None
            if part_2 is None:
                if part_1 is None:
                    return None
                else:
                    return int(part_1)
            else:
                return float(part_1) + part_2
        else:
            raise ValueError("only edf files are managed")

    @staticmethod
    def get_tomo_n(
        scan: str,
        dataset_basename: str | None = None,
        scan_info: dict | None = None,
    ) -> int | None:
        return EDFTomoScan.retrieve_information(
            scan=os.path.abspath(scan),
            dataset_basename=dataset_basename,
            ref_file=None,
            key="TOMO_N",
            type_=int,
            key_aliases=["tomo_N", "Tomo_N"],
            scan_info=scan_info,
        )

    @staticmethod
    def get_dark_n(
        scan: str,
        dataset_basename: str | None = None,
        scan_info: dict | None = None,
    ) -> int | None:
        return EDFTomoScan.retrieve_information(
            scan=os.path.abspath(scan),
            dataset_basename=dataset_basename,
            ref_file=None,
            key="DARK_N",
            type_=int,
            key_aliases=[
                "dark_N",
            ],
            scan_info=scan_info,
        )

    @staticmethod
    def get_ref_n(
        scan: str,
        dataset_basename: str | None = None,
        scan_info: dict | None = None,
    ) -> int | None:
        return EDFTomoScan.retrieve_information(
            scan=os.path.abspath(scan),
            dataset_basename=dataset_basename,
            ref_file=None,
            key="REF_N",
            type_=int,
            key_aliases=[
                "ref_N",
            ],
            scan_info=scan_info,
        )

    @staticmethod
    def get_ff_interval(
        scan: str,
        dataset_basename: str | None = None,
        scan_info: dict | None = None,
    ) -> int | None:
        return EDFTomoScan.retrieve_information(
            scan=os.path.abspath(scan),
            dataset_basename=dataset_basename,
            ref_file=None,
            key="REF_ON",
            type_=int,
            key_aliases=[
                "ref_On",
            ],
            scan_info=scan_info,
        )

    @staticmethod
    def get_scan_range(
        scan: str,
        dataset_basename: str | None = None,
        scan_info: dict | None = None,
    ) -> int | None:
        return EDFTomoScan.retrieve_information(
            scan=os.path.abspath(scan),
            dataset_basename=dataset_basename,
            ref_file=None,
            key="ScanRange",
            type_=int,
            key_aliases=[
                "scanRange",
            ],
            scan_info=scan_info,
        )

    @staticmethod
    def get_dim1_dim2(
        scan: str,
        dataset_basename: str | None = None,
        scan_info: dict | None = None,
    ) -> tuple | None:
        d1 = EDFTomoScan.retrieve_information(
            scan=os.path.abspath(scan),
            dataset_basename=dataset_basename,
            ref_file=None,
            key="Dim_1",
            key_aliases=["projectionSize/DIM_1"],
            type_=int,
            scan_info=scan_info,
        )
        d2 = EDFTomoScan.retrieve_information(
            scan=os.path.abspath(scan),
            dataset_basename=dataset_basename,
            ref_file=None,
            key="Dim_2",
            key_aliases=["projectionSize/DIM_2"],
            type_=int,
        )

        return d1, d2

    @property
    @docstring(TomoScanBase.instrument_name)
    def instrument_name(self) -> str | None:
        """

        :return: instrument name
        """
        return None

    @property
    @docstring(TomoScanBase.title)
    def title(self) -> str | None:
        """

        :return: title
        """
        return None

    @property
    @docstring(TomoScanBase.source_name)
    def source_name(self) -> str | None:
        """

        :return: source name
        """
        return None

    @property
    @docstring(TomoScanBase.source_type)
    def source_type(self) -> str | None:
        """

        :return: source type
        """
        return None

    @property
    def propagation_distance(self) -> float | None:
        """Not handled by EDF"""
        return None

    @property
    @docstring(TomoScanBase.sample_detector_distance)
    def sample_detector_distance(self) -> float | None:
        """sample / detector distance in meter"""
        if self._sample_detector_distance is None:
            self._sample_detector_distance = EDFTomoScan.retrieve_information(
                self.path,
                dataset_basename=self.dataset_basename,
                ref_file=None,
                key="Distance",
                type_=float,
                key_aliases=("distance",),
                scan_info=self.scan_info,
            )
        if self._sample_detector_distance is None:
            return None
        else:
            return (
                (self._sample_detector_distance * _ureg.millimeter)
                .to(_ureg.meter)
                .magnitude
            )

    @property
    def source_sample_distance(self) -> float | None:
        """Not handled for EDF"""
        return None

    @property
    @docstring(TomoScanBase.field_of_view)
    def field_of_view(self):
        # not managed for EDF files
        return None

    @property
    @docstring(TomoScanBase.x_rotation_axis_pixel_position)
    def x_rotation_axis_pixel_position(self):
        # not managed for EDF files
        return None

    @property
    @docstring(TomoScanBase.energy)
    def energy(self):
        if self.__energy is None:
            self.__energy = EDFTomoScan.retrieve_information(
                self.path,
                dataset_basename=self.dataset_basename,
                ref_file=None,
                key="Energy",
                type_=float,
                key_aliases=("energy",),
                scan_info=self.scan_info,
            )
        return self.__energy

    @property
    def count_time(self) -> list | None:
        if self._count_time is None:
            count_time = EDFTomoScan.retrieve_information(
                self.path,
                dataset_basename=self.dataset_basename,
                ref_file=None,
                key="Count_time",
                type_=float,
                key_aliases=("CountTime"),
                scan_info=self.scan_info,
            )
            if count_time is not None:
                if self.tomo_n is not None:
                    self._count_time = [count_time] * self.tomo_n
                else:
                    self._count_time = count_time

        return self._count_time

    @property
    def electric_current(self) -> tuple:
        warnings.warn(
            "electric_current is deprecated and will be removed in a future version. Use machine_current instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.machine_current

    @property
    @docstring(TomoScanBase.machine_current)
    def machine_current(self) -> tuple:
        if self._machine_current is None:
            machine_current = EDFTomoScan.retrieve_information(
                self.path,
                dataset_basename=self.dataset_basename,
                ref_file=None,
                key="SrCurrent",
                type_=float,
                key_aliases=("SRCUR", "machineCurrentStart"),
                scan_info=self.scan_info,
            )
            if machine_current is not None:
                if self.tomo_n is not None:
                    self._machine_current = [machine_current] * self.tomo_n
                else:
                    self._machine_current = machine_current

        return self._machine_current

    @staticmethod
    def _get_pixel_size(
        scan: str,
        dataset_basename: str | None = None,
        scan_info: dict | None = None,
    ) -> float | None:
        if os.path.isdir(scan) is False:
            return None
        value = EDFTomoScan.retrieve_information(
            scan=scan,
            dataset_basename=dataset_basename,
            ref_file=None,
            key="PixelSize",
            type_=float,
            key_aliases=[
                "pixelSize",
            ],
            scan_info=scan_info,
        )
        if value is None:
            parFile = os.path.join(scan, scan.dataset_basename + ".par")
            if os.path.exists(parFile):
                try:
                    ddict = get_parameters_frm_par_or_info(parFile)
                except ValueError as e:
                    _logger.error(e)
                if "IMAGE_PIXEL_SIZE_1".lower() in ddict:
                    value = float(ddict["IMAGE_PIXEL_SIZE_1".lower()])
        # for now pixel size are stored in microns.
        # We want to return them in meter
        if value is not None:
            return (value * _ureg.micrometer).to(_ureg.meter).magnitude
        else:
            return None

    @staticmethod
    def get_darks_url(
        scan_path: str,
        dataset_basename: str | None = None,
        prefix: str = "dark",
        file_ext: str = ".edf",
    ) -> dict:
        """

        :param scan_path:
        :param prefix: flat file prefix
        :param file_ext: flat file extension
        :return: list of flat frames as silx's `DataUrl`
        """
        res = {}
        if os.path.isdir(scan_path) is False:
            _logger.error(
                scan_path + " is not a directory. Cannot extract " "DarkHST files"
            )
            return res
        if dataset_basename is None:
            dataset_basename = os.path.basename(scan_path)
        for file_ in os.listdir(scan_path):
            _prefix = prefix
            if prefix.endswith(file_ext):
                _prefix = prefix.rstrip(file_ext)
            if file_.startswith(_prefix) and file_.endswith(file_ext):
                # usuelly the dark file name should be dark.edf, but some
                # darkHSTXXXX remains...
                file_fp = file_.lstrip(_prefix).rstrip(file_ext).lstrip("HST")
                if file_fp == "" or file_fp.isnumeric() is True:
                    index = EDFTomoScan.guess_index_frm_file_name(
                        _file=file_, basename=dataset_basename
                    )
                    urls = extract_urls_from_edf(
                        os.path.join(scan_path, file_), start_index=index
                    )
                    res.update(urls)
        return res

    @staticmethod
    def get_flats_url(
        scan_path: str,
        dataset_basename: str | None = None,
        prefix: str = "refHST",
        file_ext: str = ".edf",
        ignore=None,
    ) -> dict:
        """

        :param scan_path:
        :param prefix: flat frame file prefix
        :param file_ext: flat frame file extension
        :return: list of refs as silx's `DataUrl`
        """
        res = {}
        if os.path.isdir(scan_path) is False:
            _logger.error(
                scan_path + " is not a directory. Cannot extract " "RefHST files"
            )
            return res

        def get_next_free_index(key, keys):
            """return next free key from keys by converting it to a string
            with `key_value (n)` after it
            """
            new_key = key
            index = 2
            while new_key in keys:
                new_key = f"{key} ({index})"
                index += 1
            return new_key

        def ignore_file(file_name, to_ignore):
            if to_ignore is None:
                return False
            for pattern in to_ignore:
                if pattern in file_name:
                    return True
            return False

        if dataset_basename is None:
            dataset_basename = os.path.basename(scan_path)

        for file_ in os.listdir(scan_path):
            if (
                file_.startswith(prefix)
                and file_.endswith(file_ext)
                and not ignore_file(file_, ignore)
            ):
                index = EDFTomoScan.guess_index_frm_file_name(
                    _file=file_,
                    basename=dataset_basename,
                )
                file_fp = os.path.join(scan_path, file_)
                urls = extract_urls_from_edf(start_index=index, file_=file_fp)
                for key in urls:
                    if key in res:
                        key_ = get_next_free_index(key, res.keys())
                    else:
                        key_ = key
                    res[key_] = urls[key]
        return res

    @property
    def x_flipped(self) -> bool:
        deprecated_warning(
            type_="property",
            name="x_flipped",
            replacement="get_detector_transformations",
            since_version="1.3",
        )
        return None

    @property
    def y_flipped(self) -> bool:
        deprecated_warning(
            type_="property",
            name="y_flipped",
            replacement="detector_transformations",
            since_version="1.3",
        )
        return None

    @property
    def detector_transformations(self) -> tuple | None:
        """
        not handled for EDF
        """
        return None

    def _reload_projections(self):
        if self.path is None:
            return
        all_projections = EDFTomoScan.get_proj_urls(
            self.path,
            n_frames=self._edf_n_frames,
            dataset_basename=self.dataset_basename,
        )

        def select_proj(ddict, from_, to_):
            indexes = sorted(set(ddict.keys()))
            sel_indexes = indexes[from_:to_]
            res = {}
            for index in sel_indexes:
                res[index] = ddict[index]
            return res

        if self.tomo_n is not None and len(all_projections) > self.tomo_n:
            self._projections = select_proj(all_projections, 0, self.tomo_n)
            self._alignment_projections = select_proj(
                all_projections, self.tomo_n, None
            )
        else:
            self._projections = all_projections
            self._alignment_projections = {}
        if self._ignore_init is False:
            for idx in self.get_ignored_projection_indices():
                self._projections.pop(idx, None)
            self._ignore_init = True

    @staticmethod
    def retrieve_information(
        scan: str,
        dataset_basename: str | None,
        ref_file: str | None,
        key: str,
        type_: type,
        key_aliases: list | tuple | None = None,
        scan_info: dict | None = None,
    ):
        """
        Try to retrieve information a .info file, an .xml or a flat field file.

        file.
        Look for the key 'key' or one of it aliases.

        :param scan: root folder of an acquisition. Must be an absolute path
        :param ref_file: the refXXXX_YYYY which should contain information
                         about the scan. Ref in esrf reference is a flat.
        :param key: the key (information) we are looking for
        :param type_: required out type if the information is found
        :param key_aliases: aliases of the key in the different file
        :param scan_info: dict containing keys that could overwrite .info file content
        :return: the requested information or None if not found
        """
        info_aliases = [key]
        if key_aliases is not None:
            assert type(key_aliases) in (tuple, list)
            [info_aliases.append(alias) for alias in key_aliases]

        # if user provided 'scan_info' then he might want ot overwrite the metadata value
        if scan_info is not None:
            info = scan_info.get(key, scan_info.get(key.lower(), None))
            if info is not None:
                return info

        if not os.path.isdir(scan):
            return None

        # 1st look for ref file if any given
        def parseRefFile(filePath):
            with fabio.open(filePath) as ref_file:
                header = ref_file.header
            for k in key_aliases:
                if k in header:
                    return type_(header[k])
            return None

        if ref_file is not None and os.path.isfile(ref_file):
            try:
                info = parseRefFile(ref_file)
            except IOError as e:
                _logger.warning(e)
            else:
                if info is not None:
                    return info

        # 2nd look for .info file
        def parseInfoFile(filePath):
            metadata = get_parameters_frm_par_or_info(filePath)
            for alias in info_aliases:
                if alias.lower() in metadata:
                    return type_(metadata[alias.lower()])
            return None

        if dataset_basename is None:
            dataset_basename = os.path.basename(scan)
        infoFiles = [os.path.join(scan, dataset_basename + ".info")]
        infoOnDataVisitor = infoFiles[0].replace("lbsram", "")
        # Note: hack to check in /data/dataset instead of /lbsram/data.
        # when data is saved to /lbsram with spec the dataset is saved in /lbsram/data/{dataset} and the .info in /data/{dataset}
        if os.path.isfile(infoOnDataVisitor):
            infoFiles.append(infoOnDataVisitor)
        for infoFile in infoFiles:
            if os.path.isfile(infoFile) is True:
                info = parseInfoFile(infoFile)
                if info is not None:
                    return info

        # 3td look for xml files
        def parseXMLFile(filePath):
            try:
                for alias in info_aliases:
                    tree = etree.parse(filePath)
                    elmt = tree.find("acquisition/" + alias)
                    if elmt is None:
                        continue
                    else:
                        info = type_(elmt.text)
                        if info == -1:
                            return None
                        else:
                            return info
            except etree.XMLSyntaxError as e:
                _logger.warning(e)
                return None

        xmlFiles = [os.path.join(scan, dataset_basename + ".xml")]
        xmlOnDataVisitor = xmlFiles[0].replace("lbsram", "")
        # hack to check in lbsram, would need to be removed to add some consistency
        if os.path.isfile(xmlOnDataVisitor):
            xmlFiles.append(xmlOnDataVisitor)
        for xmlFile in xmlFiles:
            if os.path.isfile(xmlFile) is True:
                info = parseXMLFile(xmlFile)
                if info is not None:
                    return info

        return None

    def get_range(self):
        if self.path is not None:
            return self.get_scan_range(self.path, self.scan_info)
        else:
            return None

    def get_flat_expected_location(self):
        return os.path.join(self.dataset_basename, "refHST[*].edf")

    def get_dark_expected_location(self):
        return os.path.join(self.dataset_basename, "dark[*].edf")

    def get_projection_expected_location(self):
        return os.path.join(os.path.basename(self.path), self.dataset_basename, "*.edf")

    def _get_info_file_path_short_name(self):
        info_file = self.get_info_file_path(scan=self)
        return os.path.join(
            os.path.basename(os.path.dirname(info_file)), self.dataset_basename
        )

    def get_energy_expected_location(self):
        return "::".join((self._get_info_file_path_short_name(), "Energy"))

    def get_sample_detector_distance_expected_location(self):
        return "::".join((self._get_info_file_path_short_name(), "Distance"))

    def get_pixel_size_expected_location(self):
        return "::".join((self._get_info_file_path_short_name(), "PixelSize"))

    @staticmethod
    def get_info_file_path(scan):
        if not isinstance(scan, EDFTomoScan):
            raise TypeError(f"{scan} is expected to be an {EDFTomoScan}")
        if scan.path is None:
            return None
        scan_path = os.path.abspath(scan.path)
        return os.path.join(scan_path, scan.dataset_basename + ".info")

    def __str__(self):
        return f" edf scan({os.path.basename(os.path.abspath(self.path))})"

    @docstring(TomoScanBase.get_relative_file)
    def get_relative_file(self, file_name: str, with_dataset_prefix=True) -> str | None:
        if self.path is not None:
            if with_dataset_prefix:
                basename = self.dataset_basename
                basename = "_".join((basename, file_name))
                return os.path.join(self.path, basename)
            else:
                return os.path.join(self.path, file_name)
        else:
            return None

    def get_dataset_basename(self) -> str:
        return self.dataset_basename

    @property
    def dataset_basename(self) -> str | None:
        if self._dataset_basename is not None:
            return self._dataset_basename
        elif self.path is None:
            return None
        else:
            return os.path.basename(self.path)

    @docstring(TomoScanBase)
    def save_reduced_darks(
        self,
        darks: dict,
        output_urls: tuple = REDUCED_DARKS_DATAURLS,
        darks_infos=None,
        metadata_output_urls=REDUCED_DARKS_METADATAURLS,
        overwrite: bool = False,
    ):
        if len(darks) > 1:
            _logger.warning(
                "EDFTomoScan expect at most one dark. Only one will be save"
            )
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
        metadata_input_urls: tuple = REDUCED_DARKS_METADATAURLS,
        return_as_url: bool = False,
        return_info: bool = False,
    ) -> dict:
        darks = super().load_reduced_darks(
            inputs_urls=inputs_urls,
            metadata_input_urls=metadata_input_urls,
            return_as_url=return_as_url,
            return_info=return_info,
        )
        if return_info is True:
            darks, info = darks
        else:
            info = None
        # for edf we don't expect dark to have a index and we set it by default at frame index 0
        if None in darks:
            dark_frame = darks[None]
            del darks[None]
            if 0 in darks:
                _logger.warning("Two frame found for index 0")
            else:
                darks[0] = dark_frame
        if return_info is True:
            return darks, info
        else:
            return darks

    @docstring(TomoScanBase)
    def save_reduced_flats(
        self,
        flats: dict,
        output_urls: tuple = REDUCED_FLATS_DATAURLS,
        flats_infos=None,
        metadata_output_urls=REDUCED_FLATS_METADATAURLS,
        overwrite: bool = False,
    ) -> dict:
        super().save_reduced_flats(
            flats=flats,
            output_urls=output_urls,
            flats_infos=flats_infos,
            metadata_output_urls=metadata_output_urls,
            overwrite=overwrite,
        )

    @docstring(TomoScanBase)
    def load_reduced_flats(
        self,
        inputs_urls: tuple = REDUCED_FLATS_DATAURLS,
        metadata_input_urls: tuple = REDUCED_FLATS_METADATAURLS,
        return_as_url: bool = False,
        return_info=False,
    ) -> dict:
        return super().load_reduced_flats(
            inputs_urls=inputs_urls,
            return_as_url=return_as_url,
            return_info=return_info,
            metadata_input_urls=metadata_input_urls,
        )

    @docstring(TomoScanBase.compute_reduced_flats)
    def compute_reduced_flats(
        self,
        reduced_method="median",
        overwrite=True,
        output_dtype=numpy.int32,
        return_info=False,
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
        output_dtype=numpy.uint16,
        return_info=False,
    ):
        return super().compute_reduced_darks(
            reduced_method=reduced_method,
            overwrite=overwrite,
            output_dtype=output_dtype,
            return_info=return_info,
        )

    @staticmethod
    def from_identifier(identifier):
        """Return the Dataset from a identifier"""
        if not isinstance(identifier, EDFTomoScanIdentifier):
            raise TypeError(
                f"identifier should be an instance of {EDFTomoScanIdentifier} not {type(identifier)}"
            )
        return EDFTomoScan(scan=identifier.folder)

    @docstring(TomoScanBase)
    def get_identifier(self) -> ScanIdentifier:
        return EDFTomoScanIdentifier(
            object=self, folder=self.path, file_prefix=self.dataset_basename
        )
