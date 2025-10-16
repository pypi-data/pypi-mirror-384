# coding: utf-8

import os
import tempfile

import pytest

from tomoscan.esrf.scan.mock import MockNXtomo
from tomoscan.esrf.volume.edfvolume import EDFVolume
from tomoscan.series import (
    Series,
    check_series_is_consistent_frm_sample_name,
    sequences_to_series_from_sample_name,
    series_is_complete_from_group_size,
)


@pytest.mark.parametrize("use_identifiers", [True, False])
def test_series_scan(use_identifiers):
    """simple test of a serie"""
    with tempfile.TemporaryDirectory() as dir_:
        series_1 = Series(use_identifiers=use_identifiers)
        assert isinstance(series_1.name, str)
        series_2 = Series("test", use_identifiers=use_identifiers)
        assert series_2.name == "test"
        assert len(series_2) == 0
        scan1 = MockNXtomo(dir_, n_proj=2).scan
        scan2 = MockNXtomo(dir_, n_proj=2).scan
        series_3 = Series("test", [scan1, scan2], use_identifiers=use_identifiers)
        assert series_3.name == "test"
        assert len(series_3) == 2

        with pytest.raises(TypeError):
            series_1.append("toto")

        assert scan1 not in series_1
        series_1.append(scan1)
        assert len(series_1) == 1
        assert scan1 in series_1
        series_1.append(scan1)
        series_1.remove(scan1)
        series_1.name = "toto"
        with pytest.raises(TypeError):
            series_1.name = 12
        with pytest.raises(TypeError):
            series_1.remove(12)
        series_1.append(scan2)
        series_1.append(scan1)
        assert len(series_1) == 3
        series_1.remove(scan1)
        assert len(series_1) == 2
        series_1 == Series("toto", (scan1, scan2), use_identifiers=use_identifiers)
        assert scan1 in series_1
        assert scan2 in series_1

        identifiers_list = series_1.to_dict_of_str()
        assert type(identifiers_list["objects"]) is list
        assert len(identifiers_list["objects"]) == 2
        for id_str in identifiers_list["objects"]:
            assert isinstance(id_str, str)
        assert series_1 != 12


@pytest.mark.parametrize("use_identifiers", [True, False])
def test_series_volume(use_identifiers):
    volume_1 = EDFVolume(folder="test")
    volume_2 = EDFVolume()
    volume_3 = EDFVolume(folder="test2")
    volume_4 = EDFVolume()

    series_1 = Series("Volume serie", [volume_1, volume_2])
    assert volume_1 in series_1
    assert volume_2 in series_1
    assert volume_3 not in series_1
    assert volume_4 not in series_1
    series_1.remove(volume_2)
    series_1.append(volume_3)

    identifiers_list = series_1.to_dict_of_str()
    assert type(identifiers_list["objects"]) is list
    assert len(identifiers_list["objects"]) == 2
    for id_str in identifiers_list["objects"]:
        assert isinstance(id_str, str)

    series_2 = Series.from_dict_of_str(series_1.to_dict_of_str())
    assert len(series_2) == 2
    with pytest.raises(TypeError):
        Series.from_dict_of_str({"name": "toto", "objects": (12, 13)})


def test_series_utils():
    """test utils function from Series"""
    with tempfile.TemporaryDirectory() as tmp_path:
        dir_1 = os.path.join(tmp_path, "scan1")
        dir_2 = os.path.join(tmp_path, "scan2")
        dir_3 = os.path.join(tmp_path, "scan3")
        for dir_folder in (dir_1, dir_2, dir_3):
            os.makedirs(dir_folder)
        scan_s1_1 = MockNXtomo(dir_1, n_proj=2, sample_name="toto").scan
        scan_s1_2 = MockNXtomo(dir_2, n_proj=2, sample_name="toto").scan
        scan_s2_2 = MockNXtomo(dir_3, n_proj=2, sample_name="titi").scan

        found_series = sequences_to_series_from_sample_name(
            (scan_s1_1, scan_s1_2, scan_s2_2)
        )
        assert len(found_series) == 2
        with pytest.raises(TypeError):
            sequences_to_series_from_sample_name([12])
        for serie in found_series:
            check_series_is_consistent_frm_sample_name(serie)

        with pytest.raises(ValueError):
            check_series_is_consistent_frm_sample_name(
                Series("test", [scan_s1_1, scan_s2_2])
            )

        dir_4 = os.path.join(tmp_path, "scan4")
        dir_5 = os.path.join(tmp_path, "scan5")
        scan_z_series_1 = MockNXtomo(
            dir_4, n_proj=2, sample_name="z-series", group_size=2
        ).scan
        scan_z_series_2 = MockNXtomo(
            dir_5, n_proj=2, sample_name="z-series", group_size=2
        ).scan
        assert not series_is_complete_from_group_size(
            [
                scan_z_series_1,
            ]
        )
        assert series_is_complete_from_group_size([scan_z_series_1, scan_z_series_2])

        dir_6 = os.path.join(tmp_path, "scan6")
        scan_z_series_3 = MockNXtomo(
            dir_6, n_proj=2, sample_name="z-series", group_size=2
        ).scan
        assert series_is_complete_from_group_size(
            [scan_z_series_1, scan_z_series_2, scan_z_series_3]
        )

        with pytest.raises(TypeError):
            series_is_complete_from_group_size([1, 2])
