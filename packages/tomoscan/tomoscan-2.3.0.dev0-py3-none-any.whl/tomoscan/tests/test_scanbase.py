# coding: utf-8

import os
from copy import deepcopy

import h5py
import numpy.random
import pytest
from silx.io.url import DataUrl

from tomoscan.scanbase import ReducedFramesInfos, Source, SourceType, TomoScanBase
from tomoscan.tests.utils import NXtomoMockContext


def test_flat_field_correction(tmp_path):
    # set up
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    scan = TomoScanBase(None, None)
    scan.set_reduced_darks(
        {
            0: numpy.random.random(100).reshape((10, 10)),
        }
    )

    scan.set_reduced_flats(
        {
            1: numpy.random.random(100).reshape((10, 10)),
            12: numpy.random.random(100).reshape((10, 10)),
            21: numpy.random.random(100).reshape((10, 10)),
        }
    )

    data_urls = {}
    projections = {}
    file_path = os.path.join(data_dir, "data_file.h5")

    for i in range(-2, 30):
        projections[i] = numpy.random.random(100).reshape((10, 10))
        data_path = "/".join(("data", str(i)))
        data_urls[i] = DataUrl(file_path=file_path, data_path=data_path, scheme="silx")
        with h5py.File(file_path, mode="a") as h5s:
            h5s[data_path] = projections[i]

    scan.projections = projections

    # test get_flats_weights
    flat_weights = scan._get_flats_weights()
    assert isinstance(flat_weights, dict)
    assert len(flat_weights) == 32
    assert flat_weights.keys() == scan.projections.keys()
    assert flat_weights[-2] == {1: 1.0}
    assert flat_weights[0] == {1: 1.0}
    assert flat_weights[1] == {1: 1.0}
    assert flat_weights[12] == {12: 1.0}
    assert flat_weights[21] == {21: 1.0}
    assert flat_weights[24] == {21: 1.0}

    def assertAlmostEqual(ddict1, ddict2):
        assert ddict1.keys() == ddict2.keys()
        for key in ddict1.keys():
            assert numpy.isclose(ddict1[key], ddict2[key])

    print("flat_weights[2]", flat_weights[2])
    assertAlmostEqual(flat_weights[2], {1: 10.0 / 11.0, 12: 1.0 / 11.0})
    assertAlmostEqual(flat_weights[10], {1: 2.0 / 11.0, 12: 9.0 / 11.0})
    assertAlmostEqual(flat_weights[18], {12: 3.0 / 9.0, 21: 6.0 / 9.0})

    # test flat_field_data_url
    """ensure the flat_field is computed. Simple processing test when
    provided data is a DataUrl"""
    projections_keys = [key for key in scan.projections.keys()]
    projections_urls = [scan.projections[key] for key in projections_keys]
    scan.flat_field_correction(projections_urls, projections_keys)

    # test flat_field_data_numpy_array
    """ensure the flat_field is computed. Simple processing test when
    provided data is a numpy array"""
    scan.projections = data_urls
    projections_keys = [key for key in scan.projections.keys()]
    projections_urls = [scan.projections[key] for key in projections_keys]
    scan.flat_field_correction(projections_urls, projections_keys)


def test_Source_API():
    """Test Source API"""
    source = Source(name="my source", type=SourceType.SYNCHROTRON_X_RAY_SOURCE)
    source.name = "toto"
    with pytest.raises(TypeError):
        source.name = 12
    assert isinstance(source.name, str)
    source.type = SourceType.FREE_ELECTRON_LASER
    assert isinstance(source.type, SourceType)
    source.type = None
    str(source)


def test_TomoScanBase_API():
    """Test TomoScanBase API"""
    with pytest.raises(NotImplementedError):
        TomoScanBase.is_tomoscan_dir("")
    with pytest.raises(NotImplementedError):
        TomoScanBase(scan="", type_="undefined").is_abort()
    scan = TomoScanBase(scan="", type_="undefined")
    scan.source
    scan.flats = {1: numpy.random.random(100 * 100).reshape(100, 100)}
    assert len(scan.flats) == 1

    scan.darks = {0: numpy.random.random(100 * 100).reshape(100, 100)}
    assert len(scan.darks) == 1

    scan.alignment_projections = {
        2: numpy.random.random(100 * 100).reshape(100, 100),
        3: numpy.random.random(100 * 100).reshape(100, 100),
    }
    assert len(scan.alignment_projections) == 2

    for prop in (
        "dark_n",
        "tomo_n",
        "flat_n",
        "pixel_size",
        "instrument_name",
        "dim_1",
        "dim_2",
        "scan_range",
        "ff_interval",
        "energy",
        "intensity_monitor",
        "field_of_view",
        "x_translation",
        "y_translation",
        "z_translation",
        "sequence_name",
        "sample_name",
        "group_size",
        "x_rotation_axis_pixel_position",
    ):
        with pytest.raises(NotImplementedError):
            getattr(scan, prop)

    assert isinstance(scan.to_dict(), dict)

    for fct in (
        "update",
        "get_proj_angle_url",
        "get_projections_intensity_monitor",
        "get_flat_expected_location",
        "get_dark_expected_location",
        "get_projection_expected_location",
        "get_energy_expected_location",
        "get_sample_detector_distance_expected_location",
        "get_pixel_size_expected_location",
    ):
        with pytest.raises(NotImplementedError):
            getattr(scan, fct)()


def test_save_load_reduced_darks(tmpdir):
    with NXtomoMockContext(
        scan_path=os.path.join(tmpdir, "test_save_load_reduced_darks"),
        n_proj=10,
        n_ini_proj=10,
        distance=1.0,
        energy=1.0,
    ) as scan:
        with pytest.raises(TypeError):
            scan.save_reduced_darks(
                darks=None,
                output_urls=scan.REDUCED_DARKS_DATAURLS,
            )

        with pytest.raises(TypeError):
            scan.save_reduced_darks(
                darks={
                    0: numpy.ones((10, 10)),
                },
                output_urls=None,
            )

        scan.path = None
        with pytest.raises(ValueError):
            scan.save_reduced_darks(
                darks={
                    0: numpy.ones((10, 10)),
                },
                output_urls=scan.REDUCED_DARKS_DATAURLS,
            )

        with pytest.raises(ValueError):
            scan.save_reduced_darks(
                darks={
                    0: numpy.ones((10, 10)),
                },
                output_urls=scan.REDUCED_DARKS_DATAURLS,
            )


def test_ReducedFramesInfo():
    """
    test ReducedFramesInfos class
    """
    infos = ReducedFramesInfos()
    assert infos.to_dict() == {}
    infos.count_time = numpy.array([12.3, 13.0])
    assert infos.count_time == [12.3, 13.0]
    infos.machine_current = [23.5, 56.9]
    assert infos.machine_current == [23.5, 56.9]
    my_dict = deepcopy(infos.to_dict())
    assert my_dict == {
        ReducedFramesInfos.COUNT_TIME_KEY: [12.3, 13.0],
        ReducedFramesInfos.MACHINE_ELECT_CURRENT_KEY: [23.5, 56.9],
    }

    infos.clear()
    assert infos.to_dict() == {}
    new_infos = ReducedFramesInfos()
    new_infos.load_from_dict(my_dict)
    assert new_infos.to_dict() == my_dict

    with pytest.raises(TypeError):
        new_infos.count_time = 12
    with pytest.raises(TypeError):
        new_infos.machine_current = 12

    str(new_infos)
