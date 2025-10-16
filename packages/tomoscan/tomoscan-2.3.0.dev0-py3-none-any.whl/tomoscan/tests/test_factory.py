# coding: utf-8
from __future__ import annotations

import os
import tempfile

import pytest

from tomoscan.esrf.edfscan import EDFTomoScan
from tomoscan.esrf.scan.nxtomoscan import NXtomoScan
from tomoscan.esrf.mock import MockEDF
from tomoscan.factory import Factory
from tomoscan.scanbase import TomoScanBase
from tomoscan.tests.datasets import GitlabDataset


def test_scan_edf():
    """can we create a TomoScanBase object from a folder containing a
    valid .edf acquisition"""
    scan_dir = GitlabDataset.get_dataset("edf_datasets/test10")
    scan = Factory.create_scan_object(scan_dir)
    assert isinstance(scan, EDFTomoScan)


def test_one_nx():
    """Can we create a TomoScanBase from a .nx master file containing
    one acquisition"""
    master_file = GitlabDataset.get_dataset("h5_datasets/frm_edftomomill_oneentry.nx")
    scan = Factory.create_scan_object(master_file)
    assert isinstance(scan, NXtomoScan)
    assert scan.path == os.path.dirname(master_file)
    assert scan.master_file == master_file
    assert scan.entry == "/entry"


def test_one_two_nx():
    """Can we create a TomoScanBase from a .nx master file containing
    two acquisitions"""
    master_file = GitlabDataset.get_dataset("h5_datasets/frm_edftomomill_twoentries.nx")
    scan = Factory.create_scan_object(master_file)
    assert isinstance(scan, NXtomoScan)
    assert scan.path == os.path.dirname(master_file)
    assert scan.master_file == master_file
    assert scan.entry == "/entry0000"


def test_two_nx():
    """Can we create two TomoScanBase from a .nx master file containing
    two acquisitions using the Factory"""
    master_file = GitlabDataset.get_dataset("h5_datasets/frm_edftomomill_twoentries.nx")
    scans = Factory.create_scan_objects(master_file)
    assert len(scans) == 2
    for scan, scan_entry in zip(scans, ("/entry0000", "/entry0001")):
        assert isinstance(scan, NXtomoScan) is True
        assert scan.path == os.path.dirname(master_file)
        assert scan.master_file == master_file
        assert scan.entry == scan_entry


def test_invalid_path():
    """Insure an error is raised if the path as no meaning"""
    with pytest.raises(ValueError):
        Factory.create_scan_object("toto")

    with pytest.raises(ValueError):
        Factory.create_scan_objects("toto")

    with tempfile.TemporaryDirectory() as scan_dir:
        with pytest.raises(ValueError):
            Factory.create_scan_object(scan_dir)


def test_edf_scan_creation():
    with tempfile.TemporaryDirectory() as folder:
        scan_dir = os.path.join(folder, "my_scan")
        MockEDF.mockScan(scanID=scan_dir, nRecons=10)
        scan = Factory.create_scan_object(scan_path=scan_dir)
        assert isinstance(scan, EDFTomoScan)
        scans = Factory.create_scan_objects(scan_path=scan_dir)
        assert len(scans) == 1
        assert isinstance(scans[0], EDFTomoScan)
        dict_ = scan.to_dict()
        Factory.create_scan_object_frm_dict(dict_)
        # test invalid dict
        dict_[TomoScanBase.DICT_TYPE_KEY] = "tata"
        with pytest.raises(ValueError):
            Factory.create_scan_object_frm_dict(dict_)
        del dict_[TomoScanBase.DICT_TYPE_KEY]
        with pytest.raises(ValueError):
            Factory.create_scan_object_frm_dict(dict_)
