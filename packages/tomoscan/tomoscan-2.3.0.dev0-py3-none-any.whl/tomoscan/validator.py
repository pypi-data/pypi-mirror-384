# coding: utf-8
"""Module containing validators"""

from __future__ import annotations

import logging
import weakref

import numpy
from silx.io.utils import get_data

from tomoscan.esrf.scan.utils import dataset_has_broken_vds, get_compacted_dataslices
from tomoscan.scanbase import TomoScanBase

_logger = logging.getLogger(__name__)

__all__ = [
    "ValidatorBase",
    "DarkEntryValidator",
    "DarkDatasetValidator",
    "FlatEntryValidator",
    "FlatDatasetValidator",
    "ProjectionEntryValidator",
    "ProjectionDatasetValidator",
    "EnergyValidator",
    "DistanceValidator",
    "PixelValidator",
    "BasicScanValidator",
    "ReconstructionValidator",
    "is_valid_for_reconstruction",
]

_VALIDATOR_NAME_TXT_AJUST = 15

_LOCATION_TXT_AJUST = 40

_SCAN_NAME_TXT_AJUST = 30

_BOMB_UCODE = "\U0001f4a3"

_EXPLOSION_UCODE = "\U0001f4a5"

_THUMB_UP_UCODE = "\U0001f44d"

_OK_UCODE = "\U0001f44c"


class ValidatorBase:
    """Base validator class"""

    def is_valid(self) -> bool:
        raise NotImplementedError("Base class")

    def run(self) -> bool:
        raise NotImplementedError("Base class")

    def clear(self) -> None:
        raise NotImplementedError("Base class")


class _ScanParamValidator(ValidatorBase):
    def __init__(self, scan: TomoScanBase, name: str, location: str | None):
        if not isinstance(scan, TomoScanBase):
            raise TypeError(f"{scan} is expected to be an instance of {TomoScanBase}")
        self._scan = weakref.ref(scan)
        self.__name = name
        self.__location = location
        self._valid = None

    @property
    def name(self):
        return self.__name

    def __str__(self):
        return self.info()

    def info(self, with_scan=True):
        info = [
            self.name.ljust(_VALIDATOR_NAME_TXT_AJUST) + ":",
            "VALID".ljust(7) if self.is_valid() else "INVALID".ljust(7),
        ]
        if with_scan:
            info.insert(
                0,
                str(self.scan).ljust(_SCAN_NAME_TXT_AJUST) + " - ",
            )
        if not self.is_valid():
            info.append(
                f"Expected location: {self.__location}".ljust(_LOCATION_TXT_AJUST)
            )
        return " ".join(info)

    def _run(self):
        """Function to overwrite to compute the validity condition"""
        raise NotImplementedError("Base class")

    @property
    def scan(self) -> TomoScanBase | None:
        if self._scan and self._scan():
            return self._scan()
        else:
            return None

    def is_valid(self) -> bool:
        if self._valid is None:
            self._valid = self.run()
        return self._valid

    def clear(self):
        self._valid = None

    def run(self) -> bool | None:
        """
        Return None if unable to find if valid or not. Otherwise a boolean
        """
        if self.scan is None:
            self._valid = None
            return None
        else:
            return self._run()


class DarkEntryValidator(_ScanParamValidator):
    """
    Check darks are present and valid
    """

    def __init__(self, scan):
        super().__init__(
            scan=scan,
            name="dark(s)",
            location=scan.get_dark_expected_location(),
        )

    def _run(self) -> None:
        return self.scan.darks is not None and len(self.scan.darks) > 0


class _VdsAndValuesValidatorMixIn:
    def __init__(self, check_values, check_vds):
        self._check_values = check_values
        self._check_vds = check_vds
        self._has_data = None
        self._vds_ok = None
        self._no_nan = None

    @property
    def is_valid(self):
        raise NotImplementedError("Base class")

    @property
    def name(self):
        raise NotImplementedError("Base class")

    @property
    def scan(self):
        raise NotImplementedError("Base class")

    @property
    def location(self):
        raise NotImplementedError("Base class")

    @property
    def check_values(self):
        return self._check_values

    @property
    def check_vds(self):
        return self._check_vds

    def check_urls(self, urls: dict):
        if urls is None:
            return True

        _, compacted_urls = get_compacted_dataslices(urls, return_url_set=True)

        if self.check_vds:
            # compact urls to speed up
            for _, url in compacted_urls.items():
                if dataset_has_broken_vds(url=url):
                    self._vds_ok = False
                    return False
            else:
                self._vds_ok = True

        if self.check_values:
            self._no_nan = True
            for _, url in compacted_urls.items():
                data = get_data(url)
                self._no_nan = self._no_nan and not numpy.isnan(data).any()
            return self._no_nan
        return True

    def clear(self):
        self._has_data = None
        self._vds_ok = None
        self._no_nan = None

    def info(self, with_scan=True):
        text = "VALID".ljust(7) if self.is_valid() else "INVALID".ljust(7)
        if not self._has_data:
            text = " - ".join(
                (text, f"Unable to find data. Expected location: {self.location}")
            )
        elif self.check_vds and not self._vds_ok:
            text = " - ".join((text, "At least one dataset seems to have broken link"))
        elif self.check_values and not self._no_nan:
            text = " - ".join(
                (text, "At least one dataset seems to contains `nan` value")
            )

        text = [
            f"{self.name}".ljust(_VALIDATOR_NAME_TXT_AJUST) + ":",
            text,
        ]
        if with_scan:
            text.insert(0, f"{str(self.scan)}".ljust(_SCAN_NAME_TXT_AJUST) + ",")

        return " ".join(text)


class DarkDatasetValidator(DarkEntryValidator, _VdsAndValuesValidatorMixIn):
    """Check entries exists and values are valid"""

    def __init__(self, scan, check_vds, check_values):
        DarkEntryValidator.__init__(self, scan=scan)
        _VdsAndValuesValidatorMixIn.__init__(
            self, check_vds=check_vds, check_values=check_values
        )

    def _run(self) -> bool:
        # check darks exists
        self._has_data = DarkEntryValidator._run(self)
        if self._has_data is False:
            return False

        return _VdsAndValuesValidatorMixIn.check_urls(self, self.scan.darks)

    def info(self, with_scan=True):
        return _VdsAndValuesValidatorMixIn.info(self, with_scan)


class FlatEntryValidator(_ScanParamValidator):
    """
    Check flats are present and valid
    """

    def __init__(self, scan):
        super().__init__(
            scan=scan, name="flat(s)", location=scan.get_flat_expected_location()
        )

    def _run(self) -> bool | None:
        return self.scan.flats is not None and len(self.scan.flats) > 0


class FlatDatasetValidator(FlatEntryValidator, _VdsAndValuesValidatorMixIn):
    """Check entries exists and values are valid"""

    def __init__(self, scan, check_vds, check_values):
        FlatEntryValidator.__init__(self, scan=scan)
        _VdsAndValuesValidatorMixIn.__init__(
            self, check_vds=check_vds, check_values=check_values
        )

    def _run(self) -> bool:
        # check darks exists
        self._has_data = FlatEntryValidator._run(self)
        if self._has_data is False:
            return False

        return _VdsAndValuesValidatorMixIn.check_urls(self, self.scan.flats)

    def info(self, with_scan=True):
        return _VdsAndValuesValidatorMixIn.info(self, with_scan)


class ProjectionEntryValidator(_ScanParamValidator):
    """
    Check at projections are present and seems coherent with what is expected
    """

    def __init__(self, scan):
        super().__init__(
            scan=scan,
            name="projection(s)",
            location=scan.get_projection_expected_location(),
        )

    def _run(self) -> bool | None:
        if self.scan.projections is None:
            return False
        elif self.scan.tomo_n is not None:
            return len(self.scan.projections) == self.scan.tomo_n
        else:
            return len(self.scan.projections) > 0


class ProjectionDatasetValidator(ProjectionEntryValidator, _VdsAndValuesValidatorMixIn):
    """Check projections frames exists and values seems valid"""

    def __init__(self, scan, check_vds, check_values):
        ProjectionEntryValidator.__init__(self, scan=scan)
        _VdsAndValuesValidatorMixIn.__init__(
            self, check_vds=check_vds, check_values=check_values
        )

    def _run(self) -> bool:
        # check darks exists
        self._has_data = ProjectionEntryValidator._run(self)
        if self._has_data is False:
            return False

        return _VdsAndValuesValidatorMixIn.check_urls(self, self.scan.projections)

    def info(self, with_scan=True):
        return _VdsAndValuesValidatorMixIn.info(self, with_scan)


class EnergyValidator(_ScanParamValidator):
    """Check energy can be read and is not 0"""

    def __init__(self, scan):
        super().__init__(
            scan=scan,
            name="energy",
            location=scan.get_energy_expected_location(),
        )

    def _run(self) -> bool | None:
        return self.scan.energy not in (None, 0)


class DistanceValidator(_ScanParamValidator):
    """Check distance can be read and is not 0"""

    def __init__(self, scan):
        super().__init__(
            scan=scan,
            name="distance",
            location=scan.get_sample_detector_distance_expected_location(),
        )

    def _run(self) -> bool | None:
        return self.scan.sample_detector_distance not in (None, 0)


class PixelValidator(_ScanParamValidator):
    """Check pixel size can be read and is / are not 0"""

    def __init__(self, scan):
        super().__init__(
            scan=scan,
            name="pixel size",
            location=scan.get_pixel_size_expected_location(),
        )

    def _run(self) -> bool | None:
        from tomoscan.esrf.scan.nxtomoscan import NXtomoScan

        if isinstance(self.scan, NXtomoScan):
            return (self.scan.sample_x_pixel_size not in (None, 0)) and (
                self.scan.sample_y_pixel_size not in (None, 0)
            )
        else:
            return self.scan.pixel_size not in (None, 0)


class _ValidatorGroupMixIn:
    """
    Represents a group of validators.
    Define a `checkup` function to display a resume of valid and invalid tasks
    """

    def __init__(self):
        self._validators = []

    def checkup(self, only_issues=False) -> str:
        """
        compute a short text with:
         * if only_issues is False: all information checked and the status of the information
         * if only_issues is true: all mandatory information missing
        """

        def _is_invalid(validator):
            return not validator.is_valid()

        validators_with_issues = tuple(filter(_is_invalid, self._validators))

        def get_first_chars(validator):
            if validator.is_valid():
                return "+"
            else:
                return "-"

        if only_issues:
            if len(validators_with_issues) == 0:
                text = self.get_text_no_issue() + "\n"
            else:
                text = [
                    f"   {get_first_chars(validator)} {validator.info(with_scan=False)}"
                    for validator in validators_with_issues
                ]
                text.insert(0, self.get_text_issue(len(validators_with_issues)))
                text.append(" ")
                text = "\n".join(text)
        else:
            text = [
                f"   {get_first_chars(validator)} {validator.info(with_scan=False)}"
                for validator in self._validators
            ]
            if len(validators_with_issues) == 0:
                text.insert(0, self.get_text_no_issue())
            else:
                text.insert(0, self.get_text_issue(len(validators_with_issues)))
            text.append(" ")
            text = "\n".join(text)

        return text

    def is_valid(self) -> bool:
        valid = True
        for validator in self._validators:
            assert isinstance(
                validator, ValidatorBase
            ), "validators should be instances of ValidatorBase"
            valid = valid + validator.is_valid()
        return valid

    def _run(self) -> bool | None:
        run_ok = True
        for validator in self._validators:
            run_ok = run_ok and validator.run()
        return run_ok

    def clear(self) -> None:
        [validator.clear() for validator in self._validators]

    def get_text_no_issue(self) -> str:
        raise NotImplementedError("Base class")

    def get_text_issue(self, n_issue) -> str:
        raise NotImplementedError("Base class")


class BasicScanValidator(_ValidatorGroupMixIn, ValidatorBase):
    """Check that a scan has some basic parameters as dark, flat..."""

    def __init__(
        self, scan, check_vds=True, check_dark=True, check_flat=True, check_values=False
    ):
        super(BasicScanValidator, self).__init__()
        if not isinstance(scan, TomoScanBase):
            raise TypeError(f"{scan} is expected to be an instance of {TomoScanBase}")
        self._scan = scan

        self._validators.append(
            ProjectionDatasetValidator(
                scan=scan, check_values=check_values, check_vds=check_vds
            )
        )

        if check_dark:
            self._validators.append(
                DarkDatasetValidator(
                    scan=scan, check_values=check_values, check_vds=check_vds
                )
            )
        if check_flat:
            self._validators.append(
                FlatDatasetValidator(
                    scan=scan, check_values=check_values, check_vds=check_vds
                )
            )

    @property
    def scan(self):
        return self._scan

    def get_text_no_issue(self) -> str:
        header = f"{_OK_UCODE}{_THUMB_UP_UCODE}{_OK_UCODE}"
        return f"{header}\n No issue found from {self.scan}."

    def get_text_issue(self, n_issue) -> str:
        header = f"{_EXPLOSION_UCODE}{_BOMB_UCODE}{_EXPLOSION_UCODE}"
        return f"{header}\n {n_issue} issues found from {self.scan}"


class ReconstructionValidator(BasicScanValidator):
    """
    Check that a dataset/scan has enough valid parameters to be reconstructed
    by a software like nabu
    """

    def __init__(
        self,
        scan: TomoScanBase,
        check_phase_retrieval=True,
        check_values=False,
        check_vds=True,
        check_dark=True,
        check_flat=True,
    ):
        super().__init__(
            scan=scan,
            check_dark=check_dark,
            check_flat=check_flat,
            check_values=check_values,
            check_vds=check_vds,
        )
        self._need_phase_retrieval = check_phase_retrieval
        if self.check_phase_retrieval:
            self._validators.append(DistanceValidator(scan=scan))
            self._validators.append(EnergyValidator(scan=scan))
            self._validators.append(PixelValidator(scan=scan))

    @property
    def check_phase_retrieval(self):
        return self._need_phase_retrieval

    @check_phase_retrieval.setter
    def check_phase_retrieval(self, check):
        self._need_phase_retrieval = check


def is_valid_for_reconstruction(
    scan: TomoScanBase, need_phase_retrieval: bool = True, check_values: bool = False
):
    """
    check `scan` contains necessary and valid information to be reconstructed.

    :param TomoScanBase scan: scan to be checked
    :param check_values: If true check data for phase retrieval (energy, sample/detector distance...)
    :param check_datasets: open datasets to check for nan values or broken links to file
    """
    checker = ReconstructionValidator(
        scan=scan,
        check_phase_retrieval=need_phase_retrieval,
        check_values=check_values,
    )
    return checker.is_valid()
