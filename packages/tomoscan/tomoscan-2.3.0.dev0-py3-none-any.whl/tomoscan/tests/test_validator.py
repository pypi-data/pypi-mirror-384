# coding: utf-8

import os
import sys
import tempfile

import h5py
import numpy
import pytest

import tomoscan.validator
from tomoscan.tests.utils import NXtomoMockContext

frame_validators = (
    tomoscan.validator.FlatEntryValidator,
    tomoscan.validator.DarkEntryValidator,
    tomoscan.validator.ProjectionEntryValidator,
)


@pytest.mark.parametrize("validator_cls", frame_validators)
def test_frames_validator(validator_cls):
    """Test frame validator on a complete dataset"""
    with NXtomoMockContext(
        scan_path=os.path.join(tempfile.mkdtemp(), "scan_test"),
        n_proj=10,
        n_ini_proj=10,
    ) as scan:
        validator = validator_cls(scan)
        assert validator.is_valid(), "scan contains all kind of frames"


@pytest.mark.parametrize("validator_cls", frame_validators)
def test_frames_validator_2(validator_cls):
    """Test frame validator on a empty dataset"""
    with NXtomoMockContext(
        scan_path=os.path.join(tempfile.mkdtemp(), "scan_test"),
        n_proj=0,
        n_ini_proj=0,
        create_ini_dark=False,
        create_ini_ref=False,
        create_final_ref=False,
    ) as scan:
        validator = validator_cls(scan)
        assert not validator.is_valid(), "scan doesn't contains any projection"


@pytest.mark.parametrize("validator_cls", frame_validators)
def test_frames_validator_3(validator_cls):
    """Test frame validator on a dataset missing some projections"""
    tomo_n = 20
    with NXtomoMockContext(
        scan_path=os.path.join(tempfile.mkdtemp(), "scan_test"),
        n_proj=tomo_n,
        n_ini_proj=tomo_n - 1,
        create_ini_dark=False,
        create_ini_ref=False,
        create_final_ref=False,
    ) as scan:
        with h5py.File(scan.master_file, mode="a") as h5f:
            entry = h5f[scan.entry]
            entry.require_group("instrument").require_group("detector")[
                "tomo_n"
            ] = tomo_n
        validator = validator_cls(scan)
        assert not validator.is_valid(), "scan doesn't contains tomo_n projections"


phase_retrieval_validators = (
    tomoscan.validator.EnergyValidator,
    tomoscan.validator.DistanceValidator,
    tomoscan.validator.PixelValidator,
)


@pytest.mark.parametrize("validator_cls", phase_retrieval_validators)
def test_phase_retrieval_validator(validator_cls):
    """Test dark and flat validator on a complete dataset"""
    with NXtomoMockContext(
        scan_path=os.path.join(tempfile.mkdtemp(), "scan_test"),
        n_proj=10,
        n_ini_proj=10,
    ) as scan:
        with h5py.File(scan.master_file, mode="a") as h5f:
            entry_grp = h5f[scan.entry]

            # We also have to remove instrument/detector/xy_pixel_size !
            for key in [
                "sample/x_pixel_size",
                "sample/y_pixel_size",
                "instrument/detector/x_pixel_size",
                "instrument/detector/y_pixel_size",
            ]:
                if key in entry_grp:
                    del entry_grp[key]

        validator = validator_cls(scan)
        assert (
            not validator.is_valid()
        ), "scan have missing energy, distance and pixel size"
        with h5py.File(scan.master_file, mode="a") as h5f:
            beam_grp = h5f[scan.entry].require_group("beam")
            if "incident_energy" in beam_grp:
                del beam_grp["incident_energy"]
            beam_grp["incident_energy"] = 1.0
            beam_grp_2 = h5f[scan.entry].require_group("instrument/beam")
            if "incident_energy" in beam_grp_2:
                del beam_grp_2["incident_energy"]
            beam_grp_2["incident_energy"] = 1.0

            detector_grp = h5f[scan.entry].require_group("instrument/detector")
            if "distance" in detector_grp:
                del detector_grp["distance"]
            detector_grp["distance"] = 1.0

            sample_grp = h5f[scan.entry].require_group("sample")
            sample_grp["x_pixel_size"] = 2.0
            sample_grp["y_pixel_size"] = 1.0

        validator.clear()
        assert validator.is_valid(), "scan contains all information for phase retrieval"


frame_values_validators = (
    tomoscan.validator.DarkDatasetValidator,
    tomoscan.validator.FlatDatasetValidator,
    tomoscan.validator.ProjectionDatasetValidator,
)


@pytest.mark.parametrize("validator_cls", frame_values_validators)
def test_frame_broken_vds(validator_cls):
    with NXtomoMockContext(
        scan_path=os.path.join(tempfile.mkdtemp(), "scan_test"),
        n_proj=10,
        n_ini_proj=10,
        create_ini_dark=True,
        create_ini_ref=True,
        create_final_ref=False,
    ) as scan:
        validator = validator_cls(scan=scan, check_vds=True, check_values=False)
        assert (
            validator.is_valid()
        ), "if data is unchanged then validator should valid the entry"
        validator.clear()

        # modify 'data' dataset to set a virtual dataset with broken link (file does not exists)
        with h5py.File(scan.master_file, mode="a") as h5f:
            detector_grp = h5f[scan.entry]["instrument/detector"]
            shape = detector_grp["data"].shape
            del detector_grp["data"]

            # create invalid VDS
            layout = h5py.VirtualLayout(shape=shape, dtype="i4")

            filename = "toto.h5"
            vsource = h5py.VirtualSource(filename, "data", shape=shape)
            layout[0 : shape[0]] = vsource

            detector_grp.create_virtual_dataset("data", layout)

        assert not validator.is_valid(), "should return broken dataset"


@pytest.mark.parametrize("validator_cls", frame_values_validators)
def test_frame_data_with_nan(validator_cls):
    with NXtomoMockContext(
        scan_path=os.path.join(tempfile.mkdtemp(), "scan_test"),
        n_proj=10,
        n_ini_proj=10,
    ) as scan:
        validator = validator_cls(scan=scan, check_vds=False, check_values=True)
        assert (
            validator.is_valid()
        ), "if data is unchanged then validor should valid the entry"
        validator.clear()

        # modify 'data' dataset to add nan values
        with h5py.File(scan.master_file, mode="a") as h5f:
            data = h5f[scan.entry]["instrument/detector/data"][()]
            del h5f[scan.entry]["instrument/detector/data"]
            data[:] = numpy.nan
            h5f[scan.entry]["instrument/detector/data"] = data

        assert not validator.is_valid(), "should return data contains nan"


high_level_validators = (
    tomoscan.validator.BasicScanValidator,
    tomoscan.validator.ReconstructionValidator,
)


@pytest.mark.parametrize("only_issue", (True, False))
@pytest.mark.parametrize("validator_cls", high_level_validators)
def test_high_level_validators_ok(capsys, validator_cls, only_issue):
    with NXtomoMockContext(
        scan_path=os.path.join(tempfile.mkdtemp(), "scan_test"),
        n_proj=10,
        n_ini_proj=10,
        distance=1.0,
        energy=1.0,
    ) as scan:
        validator = validator_cls(scan=scan)

        assert validator.is_valid()
        sys.stdout.write(validator.checkup(only_issues=only_issue))
        captured = capsys.readouterr()
        assert "No issue" in captured.out, "check print as been done on stdout"
        validator.clear()


@pytest.mark.parametrize("only_issue", (True, False))
@pytest.mark.parametrize("check_values", (True, False))
@pytest.mark.parametrize("check_dark", (True, False))
@pytest.mark.parametrize("check_flat", (True, False))
@pytest.mark.parametrize("check_phase_retrieval", (True, False))
def test_reconstruction_validator_not_ok(
    capsys, only_issue, check_values, check_dark, check_flat, check_phase_retrieval
):
    with NXtomoMockContext(
        scan_path=os.path.join(tempfile.mkdtemp(), "scan_test"),
        n_proj=10,
        n_ini_proj=10,
    ) as scan:
        validator = tomoscan.validator.ReconstructionValidator(
            scan=scan,
            check_values=check_values,
            check_flat=check_flat,
            check_dark=check_dark,
            check_phase_retrieval=check_phase_retrieval,
        )

        sys.stdout.write(validator.checkup(only_issues=only_issue))
        captured = capsys.readouterr()
        if check_phase_retrieval:
            assert "2 issues" in captured.out, "should have found 2 issues"
        else:
            "no issue" in captured.out, "should not have found any issue"

        validator.clear()
        # modify 'data' dataset to set nan inside. Now dark, flat and projection should fail
        with h5py.File(scan.master_file, mode="a") as h5f:
            data = h5f[scan.entry]["instrument/detector/data"][()]
            del h5f[scan.entry]["instrument/detector/data"]
            data[:] = numpy.nan
            h5f[scan.entry]["instrument/detector/data"] = data

        sys.stdout.write(validator.checkup(only_issues=only_issue))
        captured = capsys.readouterr()
        n_issues = 0
        if check_phase_retrieval:
            # there is no energy / distance
            n_issues += 2
        if check_values and check_flat:
            # flat contains nan
            n_issues += 1
        if check_values and check_dark:
            # dark contains nan
            n_issues += 1
        if check_values:
            # projections contains nan
            n_issues += 1

        if n_issues == 0:
            "no issue" in captured.out, "should not have found any issue"
        else:
            assert (
                f"{n_issues} issues" in captured.out
            ), f"should have found {n_issues} issues"


def test_validatorbase():
    """Test the Validator base class API"""
    validator = tomoscan.validator.ValidatorBase()

    with pytest.raises(NotImplementedError):
        validator.is_valid()

    with pytest.raises(NotImplementedError):
        validator.run()

    with pytest.raises(NotImplementedError):
        validator.clear()


def test_is_valid_for_reconstruction():
    """test is_valid_for_reconstruction function."""
    with NXtomoMockContext(
        scan_path=os.path.join(tempfile.mkdtemp(), "scan_test"),
        n_proj=10,
        n_ini_proj=10,
        distance=1.0,
        energy=1.0,
    ) as scan:
        assert tomoscan.validator.is_valid_for_reconstruction(
            scan=scan, need_phase_retrieval=True, check_values=True
        ), "This dataset should be valid for reconstruction with phase retrieval"
