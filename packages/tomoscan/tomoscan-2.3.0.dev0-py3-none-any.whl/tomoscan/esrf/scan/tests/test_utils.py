# coding: utf-8

import os
from copy import deepcopy

import numpy
import pytest
import h5py
import resource
from silx.io.dictdump import dicttoh5
from silx.io.url import DataUrl

from nxtomo.application.nxtomo import ImageKey

from tomoscan.esrf.scan.edfscan import EDFTomoScan
from tomoscan.esrf.scan.nxtomoscan import NXtomoScan
from tomoscan.esrf.scan.mock import MockEDF, MockNXtomo
from tomoscan.esrf.scan.utils import (
    check_possible_issue_with_rlimit,
    copy_h5_dict_darks_to,
    copy_h5_dict_flats_to,
    from_absolute_reduced_frames_to_relative,
    from_relative_reduced_frames_to_absolute,
    from_bliss_original_file_to_raw,
    get_files_from_pattern,
    get_series_slice,
    get_n_series,
    get_parameters_frm_par_or_info,
)
from tomoscan.tests.utils import NXtomoMockContext
from tomoscan.scanbase import ReducedFramesInfos


def test_get_files_from_index_pattern(tmp_path):
    """
    Insure we can properly find files with the `index` pattern as
    myfile{index}.edf
    """
    test_dir = tmp_path / "test_dir"
    os.makedirs(test_dir, exist_ok=True)

    # create files to be tested
    indexes = (0, 10, 100, 1000, 2025)
    for index in indexes:
        open(os.path.join(test_dir, f"file{index}.EDF"), "w").close()
    # add some noise for test
    open(os.path.join(test_dir, "file.EDF"), "w").close()
    open(os.path.join(test_dir, "tata.edf"), "w").close()
    open(os.path.join(test_dir, "file3.hdf5"), "w").close()

    found_files = get_files_from_pattern(
        file_pattern="file{index}.edf",
        pattern="index",
        research_dir=str(test_dir),
    )

    assert len(found_files) == len(indexes)
    for index in indexes:
        assert index in found_files


def test_get_files_from_index_zfill4_pattern(tmp_path):
    """
    Insure we can properly find files with the `index` pattern as
    myfile{index_zfill4}.edf
    """
    test_dir = tmp_path / "test_dir"
    os.makedirs(test_dir, exist_ok=True)

    indexes = (0, 10, 100, 1000, 2025)
    for index in indexes:
        index_zfill4 = str(index).zfill(4)
        open(os.path.join(test_dir, f"file{index_zfill4}.edf"), "w").close()

    # add some noise for test
    open(os.path.join(test_dir, "file.EDF"), "w").close()
    open(os.path.join(test_dir, "tata0000.edf"), "w").close()
    open(os.path.join(test_dir, "file0003.hdf5"), "w").close()

    found_files = get_files_from_pattern(
        file_pattern="file{index}.edf",
        pattern="index",
        research_dir=str(test_dir),
    )

    assert len(found_files) == len(indexes)
    for index in indexes:
        assert index in found_files


def test_dark_and_flat_copy(tmp_path):
    """
    test copy_darks_to and copy_flats_to functions
    """
    scan_path = os.path.join(tmp_path, "my_acqui")
    scan = MockNXtomo(
        scan_path=scan_path,
        dim=100,
        n_proj=1,
        n_ini_proj=1,
        create_ini_flat=False,
        create_ini_dark=False,
        create_final_flat=False,
    ).scan

    # create darks and flats
    darks = {
        0: numpy.ones((100, 100), dtype=numpy.float32),
    }
    flats = {
        1: numpy.ones((100, 100), dtype=numpy.float32) * 2.0,
        100: numpy.ones((100, 100), dtype=numpy.float32) * 2.0,
    }

    original_dark_flat_file = os.path.join(tmp_path, "originals.hdf5")

    dicttoh5(darks, h5file=original_dark_flat_file, h5path="darks", mode="a")
    dicttoh5(flats, h5file=original_dark_flat_file, h5path="flats", mode="a")

    darks_url = DataUrl(
        file_path=original_dark_flat_file,
        data_path="/darks",
        scheme="silx",
    )
    flats_url = DataUrl(
        file_path=original_dark_flat_file,
        data_path="/flats",
        scheme="silx",
    )

    # check copy is correctly made
    expected_dark_file = os.path.join(scan.path, "my_acqui_darks.hdf5")
    expected_flat_file = os.path.join(scan.path, "my_acqui_flats.hdf5")
    assert not os.path.exists(expected_dark_file)
    assert not os.path.exists(expected_flat_file)
    copy_h5_dict_darks_to(scan=scan, darks_url=darks_url, save=False)
    assert not os.path.exists(expected_dark_file)
    assert not os.path.exists(expected_flat_file)
    copy_h5_dict_darks_to(scan=scan, darks_url=darks_url, save=True)
    assert os.path.exists(expected_dark_file)
    assert not os.path.exists(expected_flat_file)
    copy_h5_dict_flats_to(scan=scan, flats_url=flats_url, save=False)
    assert not os.path.exists(expected_flat_file)
    copy_h5_dict_flats_to(scan=scan, flats_url=flats_url, save=True)
    assert os.path.exists(expected_flat_file)

    # check a new scan can retrieve darks and flats
    new_scan = NXtomoScan(scan_path, scan.entry)
    assert new_scan.load_reduced_darks().keys() == darks.keys()
    assert new_scan.load_reduced_flats().keys() == flats.keys()

    # check behavior if DataUrl lead to no data:
    url = DataUrl(file_path=None, data_path=None)
    with pytest.raises(Exception):
        copy_h5_dict_darks_to(scan=scan, darks_url=url, raise_error_if_url_empty=True)
    with pytest.raises(Exception):
        copy_h5_dict_flats_to(scan=scan, flats_url=url, raise_error_if_url_empty=True)

    copy_h5_dict_darks_to(scan=scan, darks_url=url, raise_error_if_url_empty=False)
    copy_h5_dict_flats_to(scan=scan, flats_url=url, raise_error_if_url_empty=False)

    # test metadata
    darks_with_metadata = deepcopy(darks)
    darks_with_metadata[ReducedFramesInfos.COUNT_TIME_KEY] = [1.0]
    darks_with_metadata[ReducedFramesInfos.MACHINE_ELECT_CURRENT_KEY] = [12.3]
    dicttoh5(
        darks_with_metadata, h5file=original_dark_flat_file, h5path="darks", mode="a"
    )

    flats_with_metadata = deepcopy(flats)
    flats_with_metadata[ReducedFramesInfos.COUNT_TIME_KEY] = [2.0, 2.1]
    flats_with_metadata[ReducedFramesInfos.MACHINE_ELECT_CURRENT_KEY] = [14.3, 14.2]
    dicttoh5(
        flats_with_metadata, h5file=original_dark_flat_file, h5path="flats", mode="a"
    )

    scan.set_reduced_darks({})
    scan.set_reduced_flats({})
    scan.reduced_darks_infos = None
    scan.reduced_flats_infos = None
    copy_h5_dict_darks_to(
        scan=scan,
        darks_url=darks_url,
        raise_error_if_url_empty=False,
        save=True,
        overwrite=True,
    )
    copy_h5_dict_flats_to(
        scan=scan,
        flats_url=flats_url,
        raise_error_if_url_empty=False,
        save=True,
        overwrite=True,
    )
    assert scan.reduced_darks not in (None, {})
    assert scan.reduced_flats not in (None, {})
    assert numpy.array_equal(
        numpy.array(scan.reduced_darks_infos.count_time), numpy.array([1.0])
    )
    assert numpy.array_equal(
        numpy.array(scan.reduced_darks_infos.machine_current),
        numpy.array([12.3]),
    )
    assert numpy.array_equal(
        numpy.array(scan.reduced_flats_infos.count_time), numpy.array([2.0, 2.1])
    )
    assert numpy.array_equal(
        numpy.array(scan.reduced_flats_infos.machine_current),
        numpy.array([14.3, 14.2]),
    )


def test_reduced_frame_conversion(tmp_path):
    """
    test from_relative_reduced_frames_to_absolute and from_absolute_reduced_frames_to_relative functions
    """
    # ressources
    hdf5_scan_path = str(tmp_path / "my_hdf5")
    hdf5_scan = MockNXtomo(
        scan_path=hdf5_scan_path,
        dim=10,
        n_proj=100,
        n_ini_proj=100,
        create_ini_flat=False,
        create_ini_dark=False,
        create_final_flat=False,
    ).scan
    assert len(hdf5_scan.projections) == 100

    edf_scan_path = str(tmp_path / "edf_folder")
    MockEDF.mockScan(
        nRadio=20,
        scanID=edf_scan_path,
        n_extra_radio=2,
        scan_range=180,
        dim=36,
    )

    edf_scan = EDFTomoScan(edf_scan_path)
    assert edf_scan.tomo_n == 20

    # check type input
    with pytest.raises(TypeError):
        from_relative_reduced_frames_to_absolute(reduced_frames=1, scan=hdf5_scan)
    with pytest.raises(TypeError):
        from_relative_reduced_frames_to_absolute(reduced_frames={}, scan=1)
    with pytest.raises(TypeError):
        from_absolute_reduced_frames_to_relative(reduced_frames=1, scan=hdf5_scan)
    with pytest.raises(TypeError):
        from_absolute_reduced_frames_to_relative(reduced_frames={}, scan=1)

    # actual test
    assert from_absolute_reduced_frames_to_relative(
        reduced_frames={0: 0, 10: 1, 100: 2},
        scan=hdf5_scan,
    ) == {
        "0.0r": 0,
        "0.1r": 1,
        "1.0r": 2,
    }

    reduced_frames = {0: 0, 10: 1, 100: 2}
    assert from_relative_reduced_frames_to_absolute(
        from_absolute_reduced_frames_to_relative(
            reduced_frames=reduced_frames,
            scan=hdf5_scan,
        ),
        scan=hdf5_scan,
    )

    assert from_absolute_reduced_frames_to_relative(
        reduced_frames={0: 0, 10: 1, 30: 2},
        scan=edf_scan,
    ) == {
        "0.0r": 0,
        "0.5r": 1,
        "1.5r": 2,
    }

    # insure result won't changed if called twice
    assert from_absolute_reduced_frames_to_relative(
        reduced_frames=from_absolute_reduced_frames_to_relative(
            reduced_frames={0: 0, 10: 1, 30: 2},
            scan=edf_scan,
        ),
        scan=edf_scan,
    ) == {
        "0.0r": 0,
        "0.5r": 1,
        "1.5r": 2,
    }

    assert from_relative_reduced_frames_to_absolute(
        reduced_frames={0: 0, 10: 1, 30: 2},
        scan=edf_scan,
    ) == {0: 0, 10: 1, 30: 2}


__rlimit = resource.getrlimit(resource.RLIMIT_NOFILE)[0]


@pytest.mark.skipif(__rlimit > 1024, reason="rlimit > 1024")
def test_check_possible_issue_with_rlimit(tmp_path):
    tmp_dir = tmp_path / "test_check_possible_issue_with_rlimit"
    tmp_dir.mkdir()

    with NXtomoMockContext(
        scan_path=str(tmp_dir),
        n_proj=10,
        n_ini_proj=10,
        create_ini_dark=True,
        create_ini_ref=True,
        create_final_ref=False,
    ) as scan:
        # first test if no vds
        detector_url = DataUrl(
            file_path=scan.master_file,
            data_path=scan.get_detector_data_path(),
        )
        check_possible_issue_with_rlimit(
            url=detector_url, raise_error=True, delta_n_file=1024
        )

        # modify 'data' dataset to set a virtual dataset with broken link (file does not exists)
        with h5py.File(scan.master_file, mode="a") as h5f:
            detector_grp = h5f[scan.entry]["instrument/detector"]
            shape = detector_grp["data"].shape
            del detector_grp["data"]

            # create invalid VDS
            layout = h5py.VirtualLayout(shape=shape, dtype="i4")

            # this is a false 'vds' - only existances of files is checked
            filename = "toto.h5"
            vsource = h5py.VirtualSource(filename, "data", shape=shape)
            layout[0 : shape[0]] = vsource

            detector_grp.create_virtual_dataset("data", layout)

        # second test with vds
        check_possible_issue_with_rlimit(
            url=detector_url, raise_error=True, delta_n_file=0
        )

        check_possible_issue_with_rlimit(url=detector_url, delta_n_file=0)

        if __rlimit < 1000:
            check_possible_issue_with_rlimit(
                url=detector_url, raise_error=True, delta_n_file=1024
            )


def test_series_utils():
    """test `get_n_series` and `get_series_slice`"""
    images_keys = (
        ImageKey.DARK_FIELD.value,
        ImageKey.DARK_FIELD.value,
        ImageKey.FLAT_FIELD.value,
        ImageKey.FLAT_FIELD.value,
        ImageKey.FLAT_FIELD.value,
        ImageKey.PROJECTION.value,
        ImageKey.PROJECTION.value,
        ImageKey.PROJECTION.value,
        ImageKey.PROJECTION.value,
        ImageKey.FLAT_FIELD.value,
        ImageKey.FLAT_FIELD.value,
        ImageKey.FLAT_FIELD.value,
    )
    # test get_n_series
    assert (
        get_n_series(image_key_values=images_keys, image_key_type=ImageKey.PROJECTION)
        == 1
    )

    assert (
        get_n_series(image_key_values=images_keys, image_key_type=ImageKey.ALIGNMENT)
        == 0
    )

    assert (
        get_n_series(image_key_values=images_keys, image_key_type=ImageKey.DARK_FIELD)
        == 1
    )
    assert (
        get_n_series(image_key_values=images_keys, image_key_type=ImageKey.FLAT_FIELD)
        == 2
    )

    # test get_series_slice
    assert get_series_slice(
        image_key_values=images_keys, image_key_type=ImageKey.DARK_FIELD, series_index=0
    ) == slice(0, 2, 1)
    assert get_series_slice(
        image_key_values=images_keys,
        image_key_type=ImageKey.DARK_FIELD,
        series_index=-1,
    ) == slice(0, 2, 1)
    assert (
        get_series_slice(
            image_key_values=images_keys,
            image_key_type=ImageKey.DARK_FIELD,
            series_index=1,
        )
        is None
    )
    assert get_series_slice(
        image_key_values=images_keys, image_key_type=ImageKey.FLAT_FIELD, series_index=0
    ) == slice(2, 5, 1)
    assert get_series_slice(
        image_key_values=images_keys, image_key_type=ImageKey.FLAT_FIELD, series_index=1
    ) == slice(9, 12, 1)
    assert get_series_slice(
        image_key_values=images_keys, image_key_type=ImageKey.PROJECTION, series_index=0
    ) == slice(5, 9, 1)
    assert (
        get_series_slice(
            image_key_values=images_keys,
            image_key_type=ImageKey.ALIGNMENT,
            series_index=0,
        )
        is None
    )

    # test if images keys are empty
    assert (
        get_series_slice(
            image_key_values=(), image_key_type=ImageKey.DARK_FIELD, series_index=0
        )
        is None
    )
    assert (
        get_series_slice(
            image_key_values=(), image_key_type=ImageKey.DARK_FIELD, series_index=-1
        )
        is None
    )


def test_get_parameters_frm_par_or_info(tmp_path):
    """test the get_parameters_frm_par_or_info function"""
    info_file = os.path.join(tmp_path, "test.info")
    with open(info_file, mode="w") as f:
        f.writelines(
            [
                "Prefix=                 P40_highenergy_100nm_v3_1_\n",
                "Directory=              /data/visitor/blc15659/id16b/20240913/RAW_DATA/Vlad/P40_highenergy_100nm_v3_1_\n",
                "Energy=                 29.4\n",
                "Distance=               91.713\n",
                "ScanRange=              360\n",
                "TOMO_N=                 3203\n",
                "REF_ON=                 3204\n",
                "REF_N=                  21\n",
                "DARK_N=                 20\n",
                "Y_STEP=                 1.0\n",
                "Z_STEP=                 0\n",
                "Dim_1=                  2048\n",
                "Dim_2=                  2048\n",
                "Count_time=             0.07\n",
                "Latency_time (s)=       0.002\n",
                "Shutter_time=           7\n",
                "Col_end=                2047\n",
                "Col_beg=                0\n",
                "Row_end=                2047\n",
                "Row_beg=                0\n",
                "Optic_used=             0.65\n",
                "PixelSize=              0.0999\n",
                "Date=                   Fri Sep 13 20:24:06 2024\n",
                "Scan_Type=              continuous\n",
                "CCD_Mode=               FFM\n",
                "SrCurrent=              196.738\n",
                "CTAngle=                90\n",
                "Comment=                \n",
            ]
        )

    params = get_parameters_frm_par_or_info(info_file)
    assert params["energy"] == 29.4


def test_from_bliss_original_file_to_raw():
    """warning from_bliss_original_file_to_raw return the parent folder of the bliss original file"""
    assert (
        from_bliss_original_file_to_raw("/mnt/multipath-shares/data/toto/my_file.hdf5")
        == "/data/toto"
    )
    assert (
        from_bliss_original_file_to_raw("/gpfs/easy/data/toto/my_file.hdf5")
        == "/data/toto"
    )
    assert (
        from_bliss_original_file_to_raw("/gpfs/jazzy/data/toto/my_file.hdf5")
        == "/data/toto"
    )
    assert from_bliss_original_file_to_raw("/data/toto/my_file.hdf5") == "/data/toto"
    assert (
        from_bliss_original_file_to_raw("/home/data/toto/my_file.hdf5")
        == "/home/data/toto"
    )
    assert (
        from_bliss_original_file_to_raw("/gpfs/easy/home/data/toto/my_file.hdf5")
        == "/gpfs/easy/home/data/toto"
    )
    assert (
        from_bliss_original_file_to_raw("/home/user/documents/data/toto/my_file.hdf5")
        == "/home/user/documents/data/toto"
    )
