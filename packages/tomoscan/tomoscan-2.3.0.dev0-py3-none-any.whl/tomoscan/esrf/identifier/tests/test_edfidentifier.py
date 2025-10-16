# coding: utf-8

import os

import pytest

from tomoscan.esrf.edfscan import EDFTomoScan
from tomoscan.esrf.scan.nxtomoscan import NXtomoScan
from tomoscan.esrf.mock import MockEDF
from tomoscan.factory import Factory
from tomoscan.identifier import ScanIdentifier


def test_edf_identifier(tmp_path):
    """insure identifier is working for hdf5"""
    test_dir = tmp_path / "test_dir"
    os.makedirs(test_dir)

    scan = MockEDF.mockScan(
        scanID=str(test_dir),
        nRadio=12,
        dim=20,
    )
    identifier = scan.get_identifier()
    assert isinstance(identifier, ScanIdentifier)
    assert str(identifier).startswith("edf:")
    scan_from_identifier = EDFTomoScan.from_identifier(identifier)
    assert scan_from_identifier.path == scan.path
    scan_from_factory = Factory.create_tomo_object_from_identifier(
        identifier=str(identifier)
    )
    assert scan_from_factory.path == scan.path

    with pytest.raises(TypeError):
        NXtomoScan.from_identifier(identifier)

    # insure if TOMO_TYPE is not provided then it will still be considered as a scan
    identifier_as_str = str(identifier)
    identifier = ":".join(
        [identifier_as_str.split(":")[0], identifier_as_str.split(":")[-1]]
    )
    scan_from_factory = Factory.create_tomo_object_from_identifier(
        identifier=str(identifier)
    )
    assert scan_from_factory is not None
