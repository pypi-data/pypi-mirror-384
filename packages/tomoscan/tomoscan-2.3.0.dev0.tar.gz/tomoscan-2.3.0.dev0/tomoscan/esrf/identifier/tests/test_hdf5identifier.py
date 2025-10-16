# coding: utf-8

import os

import pytest

from tomoscan.esrf.edfscan import EDFTomoScan
from tomoscan.esrf.scan.nxtomoscan import NXtomoScan
from tomoscan.esrf.identifier.hdf5Identifier import NXtomoScanIdentifier
from tomoscan.factory import Factory
from tomoscan.identifier import ScanIdentifier
from tomoscan.tests.utils import NXtomoMockContext


def test_hdf5_identifier(tmp_path):
    """insure identifier is working for hdf5"""
    test_dir = tmp_path / "test_dir"
    os.makedirs(test_dir)
    with NXtomoMockContext(
        scan_path=str(test_dir),
        n_proj=10,
        n_ini_proj=10,
        distance=1.0,
        energy=1.0,
    ) as scan:
        identifier = scan.get_identifier()
        assert isinstance(identifier, ScanIdentifier)
        assert str(identifier).startswith(f"hdf5:{NXtomoScanIdentifier.TOMO_TYPE}:")
        scan_from_identifier = NXtomoScan.from_identifier(identifier)
        assert scan_from_identifier.entry == scan.entry
        assert os.path.abspath(scan_from_identifier.path) == os.path.abspath(scan.path)
        assert os.path.abspath(scan_from_identifier.master_file) == os.path.abspath(
            scan.master_file
        )

        scan_from_factory = Factory.create_tomo_object_from_identifier(
            identifier=str(identifier)
        )
        assert scan_from_factory.entry == scan.entry
        assert os.path.abspath(scan_from_factory.path) == os.path.abspath(scan.path)
        assert os.path.abspath(scan_from_factory.master_file) == os.path.abspath(
            scan.master_file
        )

        with pytest.raises(TypeError):
            EDFTomoScan.from_identifier(identifier)

        # insure if TOMO_TYPE is not provided then it will still be considered as a scan
        identifier_as_str = str(identifier)
        identifier_manual_def = ":".join(
            [identifier_as_str.split(":")[0], identifier_as_str.split(":")[-1]]
        )
        scan_from_factory = Factory.create_tomo_object_from_identifier(
            identifier=str(identifier_manual_def)
        )
        assert scan_from_factory is not None
        assert isinstance(identifier.short_description(), str)
        assert identifier == identifier.from_str(identifier.to_str())
        assert identifier != "toto"
