"""module dedicated to esrf scans utils"""

from __future__ import annotations


import contextlib
import fnmatch
import logging
import os
import sys
import psutil
import warnings
from typing import Iterable
import resource
import traceback

import fabio
import h5py
import numpy

from nxtomo.application.nxtomo import ImageKey

from silx.io.dictdump import h5todict
from silx.io.url import DataUrl
from silx.io.utils import get_data as silx_get_data
from silx.io.utils import h5py_read_dataset
from silx.utils.deprecation import deprecated
from silx.io.utils import open as hdf5_open

from tomoscan.utils.io import filter_esrf_mounting_points
from tomoscan.scanbase import ReducedFramesInfos, TomoScanBase

_logger = logging.getLogger(__name__)


__all__ = [
    "get_parameters_frm_par_or_info",
    "extract_urls_from_edf",
    "get_compacted_dataslices",
    "from_sequences_to_grps",
    "check_grp_is_valid",
    "grp_is_complete",
    "dataset_has_broken_vds",
    "check_possible_issue_with_rlimit",
    "get_datasets_linked_to_vds",
    "get_unique_files_linked",
    "get_files_from_pattern",
    "dump_info_file",
    "cwd_context",
    "get_data",
    "copy_h5_dict_darks_to",
    "copy_h5_dict_flats_to",
    "from_relative_reduced_frames_to_absolute",
    "from_absolute_reduced_frames_to_relative",
]


def get_parameters_frm_par_or_info(file_: str) -> dict:
    """
    Create a dictionary from the file with the information name as keys and
    their values as values

    :param file_: path to the file to parse
    :raises: ValueError when fail to parse some line.
    """
    assert os.path.exists(file_) and os.path.isfile(file_)
    ddict = {}
    f = open(file_, "r")
    lines = f.readlines()
    for line in lines:
        if "=" not in line:
            continue
        line_ = line.replace(" ", "")
        line_ = line_.rstrip("\n")
        # remove on the line comments
        if "#" in line_:
            line_ = line_.split("#")[0]
        if line_ == "":
            continue
        try:
            key, value = line_.split("=")
        except ValueError:
            raise ValueError(f"fail to extract information from {line_}")
        else:
            # try to cast the value on int, else float else don't
            try:
                value = int(value)
            except Exception:
                try:
                    value = float(value)
                except ValueError:
                    pass
            ddict[key.lower()] = value
    return ddict


def extract_urls_from_edf(
    file_: str, start_index: int | None, n_frames: int | None = None
) -> dict:
    r"""
    return one DataUrl for each frame contain in file\_

    :param file\_: path to the file to parse
    :param n_frames: Number of frames in each edf file (inferred if not told)
    :param start_index:
    """
    res = {}
    index = 0 if start_index is None else start_index
    if n_frames is None:
        with fabio.open(file_) as fabio_file:
            n_frames = fabio_file.nframes
    for i_frame in range(n_frames):
        res[index] = DataUrl(
            scheme="fabio",
            file_path=file_,
            data_slice=[
                i_frame,
            ],
        )
        index += 1
    return res


def get_compacted_dataslices(
    urls: dict,
    max_grp_size=None,
    return_merged_indices=False,
    return_url_set=False,
    subsampling=1,
):
    """
    Regroup urls to get the data more efficiently.
    Build a structure mapping files indices to information on
    how to load the data: `{indices_set: data_location}`
    where `data_location` contains contiguous indices.

    :param urls: Dictionary where the key is an integer and the value is
                      a silx `DataUrl`.
    :param max_grp_size: maximum size of url grps
    :param return_merged_indices: if True return the last merged indices.
                                       Deprecated
    :param return_url_set: return a set with url containing `urls` slices
                                and data path

    :return: Dictionary where the key is a list of indices, and the value is
             the corresponding `silx.io.url.DataUrl` with merged data_slice
    """

    def _convert_to_slice(idx):
        if numpy.isscalar(idx):
            return slice(idx, idx + 1)
        # otherwise, assume already slice object
        return idx

    def is_contiguous_slice(slice1, slice2):
        if numpy.isscalar(slice1):
            slice1 = slice(slice1, slice1 + 1)
        if numpy.isscalar(slice2):
            slice2 = slice(slice2, slice2 + 1)
        return slice2.start == slice1.stop

    def merge_slices(slice1, slice2):
        return slice(slice1.start, slice2.stop)

    if return_merged_indices is True:
        warnings.warn(
            "return_merged_indices is deprecated. It will be removed in version 0.8"
        )

    if max_grp_size is None:
        max_grp_size = sys.maxsize

    if subsampling is None:
        subsampling = 1

    sorted_files_indices = sorted(urls.keys())
    idx0 = sorted_files_indices[0]
    first_url = urls[idx0]
    merged_indices = [[idx0]]
    data_location = [
        [
            first_url.file_path(),
            first_url.data_path(),
            _convert_to_slice(first_url.data_slice()),
            first_url.scheme(),
        ]
    ]
    pos = 0
    grp_size = 0
    curr_fp, curr_dp, curr_slice, curr_scheme = data_location[pos]
    for idx in sorted_files_indices[1:]:
        url = urls[idx]
        next_slice = _convert_to_slice(url.data_slice())
        if (
            (grp_size <= max_grp_size)
            and (url.file_path() == curr_fp)
            and (url.data_path() == curr_dp)
            and is_contiguous_slice(curr_slice, next_slice)
            and (url.scheme() == curr_scheme)
        ):
            merged_indices[pos].append(idx)
            merged_slices = merge_slices(curr_slice, next_slice)
            data_location[pos][-2] = merged_slices
            curr_slice = merged_slices
            grp_size += 1
        else:  # "jump"
            pos += 1
            merged_indices.append([idx])
            data_location.append(
                [
                    url.file_path(),
                    url.data_path(),
                    _convert_to_slice(url.data_slice()),
                    url.scheme(),
                ]
            )
            curr_fp, curr_dp, curr_slice, curr_scheme = data_location[pos]
            grp_size = 0

    # Format result
    res = {}
    for ind, dl in zip(merged_indices, data_location):
        res.update(
            dict.fromkeys(
                ind,
                DataUrl(
                    file_path=dl[0], data_path=dl[1], data_slice=dl[2], scheme=dl[3]
                ),
            )
        )

    # Subsample
    if subsampling > 1:
        next_pos = 0
        for idx in sorted_files_indices:
            url = res[idx]
            ds = url.data_slice()
            res[idx] = DataUrl(
                file_path=url.file_path(),
                data_path=url.data_path(),
                data_slice=slice(next_pos + ds.start, ds.stop, subsampling),
            )
            n_imgs = ds.stop - (ds.start + next_pos)
            next_pos = abs(-n_imgs % subsampling)

    if return_url_set:
        url_set = {}
        for _, url in res.items():
            path = url.file_path(), url.data_path(), str(url.data_slice())
            url_set[path] = url

        if return_merged_indices:
            return res, merge_slices, url_set
        else:
            return res, url_set

    if return_merged_indices:
        return res, merged_slices
    else:
        return res


@deprecated(
    replacement="tomoscan.serie.from_sequences_to_series", since_version="0.8.0"
)
def from_sequences_to_grps(scans: Iterable) -> tuple:
    from tomoscan.serie import sequences_to_series_from_sample_name

    return sequences_to_series_from_sample_name(scans)


@deprecated(replacement="tomoscan.serie.check_serie_is_valid", since_version="0.8.0")
def check_grp_is_valid(scans: Iterable):
    from tomoscan.serie import check_series_is_consistent_frm_sample_name

    return check_series_is_consistent_frm_sample_name(scans)


@deprecated(replacement="tomoscan.serie.serie_is_complete", since_version="0.8.0")
def grp_is_complete(scans: Iterable) -> bool:
    from tomoscan.serie import series_is_complete_from_group_size

    return series_is_complete_from_group_size(scans)


def __get_log_fct(log_level):
    if log_level is logging.WARNING:
        return _logger.warning
    elif log_level is logging.ERROR:
        return _logger.error
    elif log_level is logging.DEBUG:
        return _logger.debug
    elif log_level is logging.INFO:
        return _logger.info
    elif log_level is logging.CRITICAL:
        return _logger.critical
    else:
        raise ValueError("logging level unrecognized")


def dataset_has_broken_vds(
    url: DataUrl,
    raise_error=False,
    log_level=logging.WARNING,
    return_unique_files=False,
) -> bool:
    """
    check that the provided url is not a VDS with broken links.


    :param DataUrl url: url to the dataset to treat
    :param raise_error: if True and dataset not existing will raise an error
    :param return_unique_files: if True return unique files. As this step can be time consuming and reused it can sometimes be convenients
    """
    if not isinstance(url, DataUrl):
        raise TypeError(f"{url} is expected to be an instance of {DataUrl}")

    uniques_files = ()

    with hdf5_open(url.file_path()) as h5f:
        dataset = h5f.get(url.data_path(), None)
        if dataset is None:
            msg = f"no data found at {url.file_path()}://{url.data_path()}"
            if raise_error:
                raise ValueError(msg)
            else:
                __get_log_fct(log_level)(msg)
            if return_unique_files:
                return (True, None)
            else:
                return True

        if not dataset.is_virtual:
            if return_unique_files:
                return (False, (url.file_path(),))
            else:
                return False

        else:
            # free dataset in case it point to another file. Else won't free the object before calling get_unique_files_linked
            dataset = None
            h5f.close()
            uniques_files = get_unique_files_linked(url=url)
            missing_files = tuple(
                filter(
                    lambda file_: not os.path.exists(file_),
                    uniques_files,
                )
            )
            if len(missing_files) > 0:
                msg = f"dataset {url.file_path()} has broken virtual-dataset at {url.data_path()}. {missing_files} missing"

                __get_log_fct(log_level)(msg)
                if raise_error:
                    raise OSError(msg)
                if return_unique_files:
                    return (True, uniques_files)
                else:
                    return True

    if return_unique_files:
        return (False, uniques_files)
    else:
        return False


def check_possible_issue_with_rlimit(
    url: DataUrl | None,
    raise_error=False,
    log_level=logging.WARNING,
    delta_n_file=0,
    substract_current_open=True,
    unique_files: tuple | None = None,
) -> bool:
    """
    check that the provided url does not contain more external file than (ulimit - delta_ulimit).
    Else if this limit is reached we will probably met some troubles when reading data.
    Once this limit is reached - vds data will return 0 only - silently
    """
    if unique_files is None and url is None:
        raise ValueError("'unique_files' or 'url' should be provided")

    if unique_files is None:
        # first check if dataset is virtual, else skip test
        with hdf5_open(url.file_path()) as h5f:
            dataset = h5f.get(url.data_path(), None)
            if dataset is None:
                msg = f"no data found at {url.file_path()}://{url.data_path()}"
                if raise_error:
                    raise ValueError(msg)
                else:
                    __get_log_fct(log_level)(msg)
                return True

            if not dataset.is_virtual:
                return False

        unique_files = get_unique_files_linked(url=url)

    n_files = len(unique_files)
    if substract_current_open:
        current_process = psutil.Process()
        n_open_file_currently = len(current_process.open_files())
    else:
        n_open_file_currently = 0
    try:
        rlimit = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
    except (ValueError, OSError):
        _logger.warning("Failed to check_possible_issue_with_rlimit")
    else:
        might_met_troubles = n_files > (rlimit - delta_n_file - n_open_file_currently)
        if might_met_troubles:
            msg = f"too much external files to open from {url.path()} - contains {n_files} external files. OS rlimit is set to {rlimit}"
            __get_log_fct(log_level)(msg)
            if raise_error:
                raise OSError(msg)


def get_datasets_linked_to_vds(url: DataUrl):
    """
    Return set([file-path, data_path]) linked to the provided url
    """
    if not isinstance(url, DataUrl):
        raise TypeError(f"{url} is expected to be an instance of {DataUrl}")
    start_file_path = url.file_path()
    start_dataset_path = url.data_path()
    start_dataset_slice = url.data_slice()
    if isinstance(start_dataset_slice, slice):
        start_dataset_slice = tuple(
            range(
                start_dataset_slice.start,
                start_dataset_slice.stop,
                start_dataset_slice.step or 1,
            )
        )
    virtual_dataset_to_treat = set()
    final_dataset = set()
    already_checked = set()

    # first datasets to be tested
    virtual_dataset_to_treat.add(
        (start_file_path, start_dataset_path, start_dataset_slice),
    )

    while len(virtual_dataset_to_treat) > 0:
        to_treat = list(virtual_dataset_to_treat)
        virtual_dataset_to_treat.clear()
        for file_path, dataset_path, dataset_slice in to_treat:
            if (file_path, dataset_path, dataset_slice) in already_checked:
                continue
            if os.path.exists(file_path):
                with hdf5_open(file_path) as h5f:
                    dataset = h5f[dataset_path]
                    if dataset.is_virtual:
                        for vs_info in dataset.virtual_sources():
                            min_frame_bound = vs_info.vspace.get_select_bounds()[0][0]
                            max_frame_bound = vs_info.vspace.get_select_bounds()[1][0]
                            if isinstance(dataset_slice, int):
                                if (
                                    not min_frame_bound
                                    <= dataset_slice
                                    <= max_frame_bound
                                ):
                                    continue
                            elif isinstance(dataset_slice, tuple):
                                if (
                                    min_frame_bound > dataset_slice[-1]
                                    or max_frame_bound < dataset_slice[0]
                                ):
                                    continue

                            with cwd_context():
                                os.chdir(os.path.dirname(file_path))
                                # Fixme: For now will look at the entire dataset of the n +1 file.
                                # if those can also contains virtual dataset and we want to handle
                                # the case a part of it is broken but not ours this should handle
                                # hyperslab
                                if vs_info.file_name != ".":
                                    # do not check self contained dataset
                                    virtual_dataset_to_treat.add(
                                        (
                                            os.path.abspath(vs_info.file_name),
                                            # avoid calling os.path.abspath if the dataset is in the same file. Otherwise mess up with paths
                                            str(vs_info.dset_name),
                                            None,
                                        )
                                    )
                    else:
                        final_dataset.add((file_path, dataset_path, dataset_slice))
                    dataset = None

            else:
                final_dataset.add((file_path, dataset_path, dataset_slice))
            already_checked.add((file_path, dataset_path, dataset_slice))
    return final_dataset


def get_unique_files_linked(url: DataUrl):
    """
    Return the list of unique files linked to the DataUrl without depth limitation
    """
    unique_files = set()
    datasets_linked = get_datasets_linked_to_vds(url=url)
    [unique_files.add(file_path) for (file_path, _, _) in datasets_linked]
    return unique_files


def get_files_from_pattern(file_pattern: str, pattern: str, research_dir: str) -> dict:
    """
    return: all files using a {pattern} to store the index. Key is the index and value is the file name
    """
    files_frm_patterm = {}
    if ("{" + pattern + "}") not in file_pattern:
        return files_frm_patterm
    if not isinstance(file_pattern, str):
        raise TypeError(f"file_pattern is expected to be str not {type(file_pattern)}")
    if not isinstance(pattern, str):
        raise TypeError(f"pattern is expected to be str not {type(pattern)}")
    if not isinstance(research_dir, str):
        raise TypeError(
            f"research_dir is expected to be a str not {type(research_dir)}"
        )
    if not os.path.exists(research_dir):
        raise FileNotFoundError(f"{research_dir} does not exists")
    # look for some index_zfill4
    file_path_fn = file_pattern.format(**{pattern: "*"})
    for file in os.listdir(research_dir):
        if fnmatch.fnmatch(file.lower(), file_path_fn.lower()):
            # try to deduce the index from pattern
            idx_start = file_pattern.find("{" + pattern + "}")
            idx_end = len(file_pattern.replace("{" + pattern + "}", "")) - idx_start
            idx_as_str = file[idx_start:-idx_end]
            if idx_as_str != "":  # handle case of an empty string
                try:
                    idx_as_int = int(idx_as_str)
                except ValueError:
                    _logger.warning("Could not determined")
                else:
                    files_frm_patterm[idx_as_int] = file

    return files_frm_patterm


def dump_info_file(
    file_path,
    tomo_n,
    scan_range,
    flat_n,
    flat_on,
    dark_n,
    dim_1,
    dim_2,
    col_beg,
    col_end,
    row_beg,
    row_end,
    pixel_size,
    distance,
    energy,
):
    # write the info file
    with open(file_path, "w") as info_file:
        info_file.write("TOMO_N=    " + str(tomo_n) + "\n")
        info_file.write("ScanRange= " + str(scan_range) + "\n")
        info_file.write("REF_N=     " + str(flat_n) + "\n")
        info_file.write("REF_ON=    " + str(flat_on) + "\n")
        info_file.write("DARK_N=    " + str(dark_n) + "\n")
        info_file.write("Dim_1=     " + str(dim_1) + "\n")
        info_file.write("Dim_2=     " + str(dim_2) + "\n")
        info_file.write("Col_beg=   " + str(col_beg) + "\n")
        info_file.write("Col_end=   " + str(col_end) + "\n")
        info_file.write("Row_beg=   " + str(row_beg) + "\n")
        info_file.write("Row_end=   " + str(row_end) + "\n")
        info_file.write("PixelSize= " + str(pixel_size) + "\n")
        info_file.write("Distance=  " + str(distance) + "\n")
        info_file.write("Energy=    " + str(energy) + "\n")


@contextlib.contextmanager
def cwd_context(new_cwd=None):
    try:
        curdir = os.getcwd()
    except Exception:
        traceback.print_stack(limit=3)
        _logger.error("Working directory has been delated. Will move to '~'")
        curdir = os.path.expanduser("~")
    try:
        if new_cwd is not None and os.path.isfile(new_cwd):
            new_cwd = os.path.dirname(new_cwd)
        if new_cwd not in (None, ""):
            os.chdir(new_cwd)
        yield
    finally:
        if curdir is not None:
            os.chdir(curdir)


def get_data(url: DataUrl):
    # update the current working dircetory for external dataset
    if url.file_path() is not None and h5py.is_hdf5(url.file_path()):
        # convert path to real path to insure it will be constant when changing current working directory
        file_path = os.path.abspath(url.file_path())
        with cwd_context(file_path):
            with hdf5_open(file_path) as h5f:
                if url.data_path() in h5f:
                    if url.data_slice() is None:
                        return h5py_read_dataset(h5f[url.data_path()])
                    else:
                        return h5py_read_dataset(
                            h5f[url.data_path()], index=url.data_slice()
                        )
    else:
        # for other file format don't need to do the same
        return silx_get_data(url)


def copy_h5_dict_darks_to(
    scan,
    darks_url: DataUrl,
    save: bool = False,
    raise_error_if_url_empty: bool = True,
    overwrite: bool = False,
):
    """
    :param TomwerScanBase scan: target to copy darks
    :param DataUrl darks_url: DataUrl to find darks to be copied
    :param save: should we save the darks to disk. If not will only be set on scan cache
    :param raise_error_if_url_empty: if the provided DataUrl lead to now data shoudl we raise an error (like file or dataset missing...)
    """
    from tomoscan.scanbase import TomoScanBase  # avoid cyclic import

    if not isinstance(scan, TomoScanBase):
        raise TypeError(
            f"scan is expected to be an instance of {TomoScanBase}. {type(scan)} provided"
        )
    if not isinstance(darks_url, DataUrl):
        raise TypeError(
            f"darks_url is expected to be an instance of {DataUrl}. {type(darks_url)} provided"
        )
    if darks_url.scheme() not in (None, "silx", "h5py"):
        raise ValueError("handled scheme are 'silx' and 'h5py'")
    try:
        with cwd_context(darks_url.file_path()):
            my_dict = h5todict(
                h5file=darks_url.file_path(),
                path=darks_url.data_path(),
            )
    except Exception as e:
        if raise_error_if_url_empty:
            raise e
        else:
            return
    data, metadata = ReducedFramesInfos.split_data_and_metadata(my_dict)
    # handle relative frame position if any
    data = from_relative_reduced_frames_to_absolute(reduced_frames=data, scan=scan)
    scan.set_reduced_darks(darks=data, darks_infos=metadata)
    if save:
        scan.save_reduced_darks(darks=data, darks_infos=metadata, overwrite=overwrite)


def copy_h5_dict_flats_to(
    scan,
    flats_url: DataUrl,
    save=False,
    raise_error_if_url_empty=True,
    overwrite: bool = False,
):
    """
    :param TomwerScanBase scan: target to copy darks
    :param DataUrl darks_url: DataUrl to find darks to be copied
    :param save: should we save the darks to disk. If not will only be set on scan cache
    :param raise_error_if_url_empty: if the provided DataUrl lead to now data shoudl we raise an error (like file or dataset missing...)
    """
    from tomoscan.scanbase import TomoScanBase  # avoid cyclic import

    if not isinstance(scan, TomoScanBase):
        raise TypeError(
            f"scan is expected to be an instance of {TomoScanBase}. {type(scan)} provided"
        )
    if not isinstance(flats_url, DataUrl):
        raise TypeError(
            f"flats_url is expected to be an instance of {DataUrl}. {type(flats_url)} provided"
        )
    if flats_url.scheme() not in (None, "silx", "h5py"):
        raise ValueError("handled scheme are 'silx' and 'h5py'")
    try:
        with cwd_context(flats_url.file_path()):
            my_dict = h5todict(
                h5file=flats_url.file_path(),
                path=flats_url.data_path(),
            )
    except Exception as e:
        if raise_error_if_url_empty:
            raise ValueError("DataUrl is not pointing to any data") from e
        else:
            return
    data, metadata = ReducedFramesInfos.split_data_and_metadata(my_dict)
    # handle relative frame position if any
    data = from_relative_reduced_frames_to_absolute(reduced_frames=data, scan=scan)
    scan.set_reduced_flats(flats=data, flats_infos=metadata)
    if save:
        scan.save_reduced_flats(flats=data, flats_infos=metadata, overwrite=overwrite)


def from_relative_reduced_frames_to_absolute(reduced_frames: dict, scan: TomoScanBase):
    if not isinstance(reduced_frames, dict):
        raise TypeError(
            f"reduced_frames is expected to be a dict, {type(reduced_frames)} provided"
        )
    if not isinstance(scan, TomoScanBase):
        raise TypeError(f"scan is expected to be a TomoScanBase, {type(scan)} provided")

    frame_n = len(scan.projections) + len(scan.darks) + len(scan.flats)

    def convert(index):
        if isinstance(index, str) and index.endswith("r"):
            return int(float(index[:-1]) * (frame_n - 1))
        else:
            return index

    return {convert(key): value for key, value in reduced_frames.items()}


def from_absolute_reduced_frames_to_relative(reduced_frames: dict, scan: TomoScanBase):
    if not isinstance(reduced_frames, dict):
        raise TypeError(
            f"reduced_frames is expected to be a dict, {type(reduced_frames)} provided"
        )
    if not isinstance(scan, TomoScanBase):
        raise TypeError(f"scan is expected to be a TomoScanBase, {type(scan)} provided")

    frame_n = len(scan.projections) + len(scan.darks) + len(scan.flats)

    def convert(index):
        if isinstance(index, str) and index.endswith("r"):
            return index
        else:
            return f"{int(index) / frame_n}r"

    return {convert(key): value for key, value in reduced_frames.items()}


def get_n_series(image_key_values: tuple | list, image_key_type: ImageKey) -> int:
    """
    Return the number of series of an image_key. Image key can be dark, flat, or projection.
    A series is defined as a contiguous elements in image_key_values

    :param image_key_values: list or tuple of image_keys to consider. Can be integers or tomoscan.esrf.scan.hdf5scan.ImageKey
    :param image_key_type: The kind of image key we want number of series for
    """
    image_key_type = ImageKey(image_key_type)
    if image_key_type is ImageKey.INVALID:
        raise ValueError(
            "we can't count Invalid image keys series because those are ignored from tomoscan"
        )
    image_key_values = [ImageKey(img_key) for img_key in image_key_values]

    # remove invalid frames
    image_key_values = numpy.array(
        image_key_values
    )  # for filtering invalid value a numpy array is requested
    image_key_values = image_key_values[image_key_values != ImageKey.INVALID]

    n_series = 0
    is_in_a_series = False
    for frame in image_key_values:
        if frame == image_key_type and not is_in_a_series:
            is_in_a_series = True
            n_series += 1
        elif frame != image_key_type:
            is_in_a_series = False
    return n_series


def get_series_slice(
    image_key_values: tuple[int], image_key_type: ImageKey, series_index: int
) -> slice | None:
    """
    return the DataUrl corresponding to the to the serie at `series_index` for the type of image_key_type.

    Examples: with the following image_key_values:
    (
        ImageKey.DARK_FIELD
        ImageKey.DARK_FIELD
        ImageKey.FLAT_FIELD
        ImageKey.FLAT_FIELD
        ImageKey.FLAT_FIELD
        ImageKey.PROJECTION
        ImageKey.PROJECTION
        ImageKey.PROJECTION
        ImageKey.PROJECTION
    )

    .. code-block:: python

        get_serie_url(image_key_values, ImageKey.FLAT_FIELD, serie_index=0) == slice(2, 5)
        get_serie_url(image_key_values, ImageKey.FLAT_FIELD, serie_index=1) == None
        get_serie_url(image_key_values, ImageKey.FLAT_FIELD, serie_index=-1) == slice(2, 5)
    """
    image_key_type = ImageKey(image_key_type)
    if series_index == -1:
        series_index = (
            get_n_series(
                image_key_values=image_key_values, image_key_type=image_key_type
            )
            - 1
        )
    n_series = -1
    start = None
    is_in_a_series = False
    for i_frame, frame in enumerate(image_key_values):
        frame = ImageKey(frame)
        if frame.value == image_key_type.value and not is_in_a_series:
            n_series += 1
            is_in_a_series = True
            if n_series == series_index:
                start = i_frame
        elif frame.value != image_key_type.value and is_in_a_series:
            is_in_a_series = False
            if n_series == series_index:
                return slice(start, i_frame, 1)
    if start is not None:
        return slice(start, len(image_key_values), 1)
    return None


def from_bliss_original_file_to_raw(bliss_original_file: str | None) -> str | None:
    """
    convert NXtomo 'bliss_original_files' to drac raw parameter (folder containing the raw)
    without some possible noise added by 'realpath' like '/mnt/multipath-shares' or '/gpfs/easy'
    """
    if bliss_original_file is None:
        return None

    bliss_original_file = filter_esrf_mounting_points(bliss_original_file)
    return os.path.dirname(bliss_original_file)
