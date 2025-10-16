"""
fscan: parsing Bliss "fscans": https://gitlab.esrf.fr/bliss/fscan
"""

from __future__ import annotations

import posixpath
from os import path
from datetime import datetime
from silx.io.url import DataUrl
from silx.io.utils import open as hdf5_open
from .h5utils import get_first_hdf5_entry, get_h5obj_value, get_hdf5_dataset_shape
from .fscan_scantypes import get_scan_metadata
from tomoscan.utils.hdf5 import get_data_sources
import logging

_logger = logging.getLogger(__file__)


def is_dataset_entry(entry):
    """
    filter all entries that doesn't contain any detector dataset. By 'design' all entries that doesn't ends with '.1'
    """
    return entry.endswith(".1")


def list_datasets(fname):
    """
    List the entries in the form X.1 in a file
    """
    with hdf5_open(fname) as f:
        entries = list(f.keys())
    entries = [entry for entry in entries if is_dataset_entry(entry)]

    # Sort entries
    def get_entry_scan_num(entry_name):
        return int(entry_name.split(".")[0])

    entries.sort(key=get_entry_scan_num)
    return entries


def list_datasets_with_attributes(fname, attrs, default=None):
    """
    List the entries in the form X.1 in a file with requested attributes.
    If attributes key doesn't exists then take 'default' value
    """
    results = {}
    with hdf5_open(fname) as f:
        entries = list(f.keys())
        entries = [entry for entry in entries if is_dataset_entry(entry)]
        for entry in entries:
            results[entry] = {}
            for attr in attrs:
                if attr not in f[entry]:
                    res = default
                else:
                    res = f[entry][attr][()]
                results[entry][attr] = res
    return results


class FscanDataset:
    """
    A simple class for parsing ESRF-Fscan datasets
    https://gitlab.esrf.fr/bliss/fscan
    """

    _default_detector_name = None
    _instrument_name = "instrument"
    guess_detector_name_if_missing = True

    def __init__(
        self,
        fname: str,
        entry: str | None = None,
        detector_name: str | None = None,
        on_missing_metadata: str = "raise",
    ):
        """
        Build a Dataset object. Each object is tied to only one entry.

        :param fname: Path to the HDF5 file.
        :param entry: HDF5 entry. If not provided, the first entry is taken.
        :param detector_name: Detector name
        :param on_missing_metadata: behavior when let missing metadata. Valid values are 'print' or 'raise'
        """
        self.fname = fname
        self.entry = entry or get_first_hdf5_entry(fname)
        self.detector_name = detector_name or self._default_detector_name
        if self.detector_name is None and self.guess_detector_name_if_missing:
            self.detector_name = guess_detector_name(self.fname, self.entry)
        self._virtual_sources = None

        self._check_file()
        self._get_toplevel_fields()
        self._get_data_info()
        self._get_metadata(on_missing_metadata)

    def _check_file(self):
        self.data_path = posixpath.join(
            self.entry, self._instrument_name, self.detector_name, "data"
        )
        with hdf5_open(self.fname) as f:
            if self.entry not in f:
                raise ValueError("No entry '%s' in file %s" % (self.entry, self.fname))
            if (
                self._instrument_name not in f[self.entry]
                or "measurement" not in f[self.entry]
            ):
                raise ValueError(
                    "%s or measurement not found in %s/%s"
                    % (self._instrument_name, self.fname, self.entry)
                )
            if self.data_path not in f:
                raise ValueError(
                    "Cannot access data %s in file %s" % (self.data_path, self.fname)
                )

    def _get_toplevel_fields(self):
        with hdf5_open(self.fname) as f:
            current_entry = f[self.entry]
            for name in ["start_time", "end_time", "title"]:
                val = get_string(get_h5obj_value(current_entry, name))
                if name in ["start_time", "end_time"]:
                    val = get_datetime(val)
                setattr(self, name, val)

    def _get_data_info(self):
        with hdf5_open(self.fname) as f:
            self.data_shape = f[self.data_path].shape
        self.dataset_hdf5_url = DataUrl(
            file_path=self.fname, data_path=self.data_path, scheme="silx"
        )

    def _get_generic_key(self, name, h5_path, default=None):
        val = getattr(self, name, None)
        if val is not None:
            return val
        h5_group, h5_name = posixpath.split(h5_path)
        with hdf5_open(self.fname) as f:
            res = get_h5obj_value(f[h5_group], h5_name, default=default)
        setattr(self, name, res)
        return res

    @property
    def exposure_time(self):
        """
        Get the exposure time in seconds
        """
        expotime_path = posixpath.join(
            posixpath.dirname(self.data_path), "acq_parameters", "acq_expo_time"
        )
        return self._get_generic_key("_exposure_time", expotime_path)

    def get_virtual_sources(
        self, remove_nonexisting: bool = True, force_recompute: bool = False
    ):
        """
        Return a dict with the virtual sources of the current dataset.

        :param remove_nonexisting: Whether to check that each target file actually exists, and possibly remove the non-existing files
        :param force_recompute: if False and already get virtual sources in cache return them
        """
        # Do only one recursion - otherwise call get_data_sources()
        if self._virtual_sources is not None and not force_recompute:
            return self._virtual_sources

        sources = get_data_sources(
            fname=self.fname, data_path=self.data_path, recursive=False
        )

        if remove_nonexisting:
            to_discard = [f for f in sources.keys() if not (path.exists(f))]
            if to_discard != []:
                print(
                    "Warning: Scan %s: the following files were declared in master file, but not found: %s"
                    % (
                        path.basename(self.fname) + ":" + self.entry,
                        str([path.basename(f) for f in to_discard]),
                    )
                )
                for fname in to_discard:
                    sources.pop(fname)

        self._virtual_sources = sources
        return sources

    def get_stack_size(self, use_file_n: int = 0):
        """
        Get dataset stack size of one LIMA file (size can be different, if cancel for example)

        :param use_file_n: Which file to take to get stack size. Default is first file.
        """
        virtual_sources = self.get_virtual_sources()
        fnames = list(virtual_sources.keys())

        fname = fnames[use_file_n]
        h5path = virtual_sources[fname]

        shp = get_hdf5_dataset_shape(fname, h5path)
        return shp[0]

    def get_all_stacks_sizes(self):
        """
        Go through all LIMA files and retrieve dataset size (nb frame)
        """
        virtual_sources = self.get_virtual_sources()
        stacks_sizes = []
        for fname, h5path in virtual_sources.items():
            shp = get_hdf5_dataset_shape(fname, h5path)
            stacks_sizes.append(shp[0])
        return stacks_sizes

    def _get_metadata(self, on_missing_metadata):
        self.metadata = get_scan_metadata(
            self.fname, self.entry, self.detector_name, on_error=on_missing_metadata
        )

    def _tostr(self):
        return str(
            "%s(fname=%s, entry=%s)" % (self.__class__.__name__, self.fname, self.entry)
        )

    def __str__(self):
        return self._tostr()

    def __repr__(self):
        return self._tostr()


def guess_detector_name(fname, entry):
    with hdf5_open(fname) as f:
        meas = f[entry]["measurement"]
        for k in meas.keys():
            if hasattr(meas[k], "ndim") and meas[k].ndim == 3:
                return k


def get_string(str_or_bytes):
    if isinstance(str_or_bytes, bytes):
        return str_or_bytes.decode()
    return str_or_bytes


def format_time(timestamp_str):
    try:
        d = datetime.fromisoformat(timestamp_str)
    except ValueError:
        if timestamp_str.endswith("Z"):
            # https://docs.python.org/3/library/datetime.html#technical-detail
            # providing 'Z' is identical to '+00:00'
            timestamp_str = timestamp_str.replace("Z", "+00:00")
            d = datetime.fromisoformat(timestamp_str)
    return d.isoformat()  # long format


def get_datetime(date_str: str) -> str | None:
    """
    try to format the date. If fail return None
    """
    if date_str is None:
        return None
    try:
        date = format_time(date_str)
    except Exception as exc:
        _logger.warning(f"fail to convert {date_str}. Error is {exc}")
        date = None
    return date
