# coding: utf-8

from __future__ import annotations

import h5py
import numpy

from nxtomo.application.nxtomo import ImageKey
from tomoscan.esrf.scan.mock import MockNXtomo as _MockNXtomo
from tomoscan.scanbase import ReducedFramesInfos


class MockNXtomo(_MockNXtomo):
    def __init__(
        self,
        scan_path,
        ini_dark: numpy.array | None,
        ini_flats: numpy.array | None,
        final_flats: numpy.array | None,
        dim: int,
        n_proj: int,
        count_time: numpy.array | None = None,
        machine_current: numpy.array | None = None,
    ):
        assert ini_dark is None or ini_dark.ndim == 3, "ini_dark should be a 3d array"
        assert ini_flats is None or ini_flats.ndim == 3, "ini_dark should be a 3d array"
        assert (
            final_flats is None or final_flats.ndim == 3
        ), "ini_dark should be a 3d array"
        self._ini_darks = ini_dark
        self._ini_flats = ini_flats
        self._final_flats = final_flats
        self._count_time = count_time
        super().__init__(
            scan_path=scan_path,
            dim=dim,
            create_ini_dark=ini_dark is not None,
            create_ini_flat=ini_flats is not None,
            create_final_flat=final_flats is not None,
            n_ini_proj=n_proj,
            n_proj=n_proj,
        )

        # append count_time and machine_current to the HDF5 file
        with h5py.File(self.scan_master_file, "a") as h5_file:
            entry_one = h5_file.require_group(self.scan_entry)
            if machine_current is not None:
                monitor_grp = entry_one.require_group("control")
                monitor_grp["data"] = machine_current
            # rewrite count_time
            if count_time is not None:
                instrument_grp = entry_one.require_group("instrument")
                detector_grp = instrument_grp.require_group("detector")
                if "count_time" in detector_grp:
                    del detector_grp["count_time"]
                detector_grp["count_time"] = count_time

    def add_initial_dark(self):
        for frame in self._ini_darks:
            self._append_frame(
                data_=frame.reshape(1, frame.shape[0], frame.shape[1]),
                rotation_angle=self.rotation_angle[-1],
                image_key=ImageKey.DARK_FIELD.value,
                image_key_control=ImageKey.DARK_FIELD.value,
                diode_data=None,
            )

    def add_initial_flat(self):
        for frame in self._ini_flats:
            self._append_frame(
                data_=frame.reshape(1, frame.shape[0], frame.shape[1]),
                rotation_angle=self.rotation_angle[-1],
                image_key=ImageKey.FLAT_FIELD.value,
                image_key_control=ImageKey.FLAT_FIELD.value,
                diode_data=None,
            )

    def add_final_flat(self):
        for frame in self._final_flats:
            self._append_frame(
                data_=frame.reshape(1, frame.shape[0], frame.shape[1]),
                rotation_angle=self.rotation_angle[-1],
                image_key=ImageKey.FLAT_FIELD.value,
                image_key_control=ImageKey.FLAT_FIELD.value,
                diode_data=None,
            )


def test_reduce_hdf5(tmp_path):
    """insure calculation of dark and flats are valid for a default use case"""
    dim = 20
    folder_1 = tmp_path / "test1"
    folder_1.mkdir()
    n_proj = 12
    n_darks = 10
    darks = numpy.ones((n_darks, dim, dim), dtype="f")

    darks_count_time = numpy.linspace(
        1.0, 2.0, n_darks, endpoint=True, dtype=numpy.float32
    )
    darks_machine_current = numpy.linspace(
        12.2, 13.3, n_darks, endpoint=True, dtype=numpy.float32
    )

    flats_s1 = numpy.asarray(
        [
            numpy.zeros((dim, dim), dtype="f"),
            numpy.ones((dim, dim), dtype="f"),
            numpy.ones((dim, dim), dtype="f") + 1.0,
        ]
    )
    flats_s1_count_time = numpy.ones(3, dtype=numpy.float32)
    flats_s1_machine_current = numpy.array([14, 13.5, 13.2], dtype=numpy.float32)

    flats_s2 = numpy.asarray(
        [
            numpy.ones((dim, dim), dtype="f") + 10.0,
            numpy.ones((dim, dim), dtype="f") + 11.0,
            numpy.ones((dim, dim), dtype="f") + 12.0,
        ]
    )
    flats_s2_count_time = numpy.array([10.0, 2.0, 3.0], dtype=numpy.float32)
    flats_s2_machine_current = numpy.array([13.6, 13.8, 14.1], dtype=numpy.float32)

    projections_count_time = numpy.linspace(
        100, 200.0, endpoint=True, num=12, dtype=numpy.float32
    )
    projections_machine_current = numpy.linspace(
        13.2, 13.5, endpoint=True, num=12, dtype=numpy.float32
    )

    count_time = numpy.concatenate(
        [
            darks_count_time,
            flats_s1_count_time,
            projections_count_time,
            flats_s2_count_time,
        ]
    )

    machine_current = numpy.concatenate(
        [
            darks_machine_current,
            flats_s1_machine_current,
            projections_machine_current,
            flats_s2_machine_current,
        ]
    )

    scan = MockNXtomo(
        scan_path=folder_1,
        ini_dark=darks,
        ini_flats=flats_s1,
        final_flats=flats_s2,
        dim=dim,
        n_proj=n_proj,
        count_time=count_time,
        machine_current=machine_current,
    ).scan

    assert scan.machine_current is not None
    assert scan.exposure_time is not None

    # test reduced frames

    numpy.testing.assert_array_equal(
        scan.compute_reduced_darks(reduced_method="median")[0],
        scan.compute_reduced_darks(reduced_method="mean")[0],
    )

    numpy.testing.assert_array_equal(
        scan.compute_reduced_flats(reduced_method="median")[n_darks],
        numpy.median(flats_s1, axis=0),
    )
    numpy.testing.assert_array_equal(
        scan.compute_reduced_flats(reduced_method="mean")[n_darks],
        numpy.mean(flats_s1, axis=0),
    )

    numpy.testing.assert_array_equal(
        scan.compute_reduced_flats(reduced_method="median")[n_darks + 3 + n_proj],
        numpy.median(flats_s2, axis=0),
    )
    numpy.testing.assert_array_equal(
        scan.compute_reduced_flats(reduced_method="mean")[n_darks + 3 + n_proj],
        numpy.mean(flats_s2, axis=0),
    )

    numpy.testing.assert_array_equal(
        scan.compute_reduced_flats(reduced_method="first", output_dtype=numpy.float64)[
            n_darks
        ],
        numpy.zeros((dim, dim), dtype=numpy.float64),
    )

    numpy.testing.assert_array_equal(
        scan.compute_reduced_flats(reduced_method="last", output_dtype=numpy.uint8)[
            n_darks
        ],
        numpy.ones((dim, dim), dtype=numpy.uint8) + 1,
    )

    numpy.testing.assert_array_equal(
        scan.compute_reduced_flats(reduced_method="first", output_dtype=numpy.int16)[
            n_darks + 3 + n_proj
        ],
        numpy.ones((dim, dim), dtype=numpy.int16) + 10.0,
    )

    # test reduced metadata on darks
    _, darks_infos = scan.compute_reduced_darks(
        reduced_method="median", return_info=True
    )
    assert isinstance(darks_infos, ReducedFramesInfos)
    assert len(darks_infos.machine_current) == len(darks_infos.count_time) == 1
    numpy.testing.assert_almost_equal(
        darks_infos.machine_current[0], numpy.median(darks_machine_current)
    )
    numpy.testing.assert_almost_equal(
        darks_infos.count_time[0], numpy.median(darks_count_time)
    )

    _, darks_infos = scan.compute_reduced_darks(reduced_method="mean", return_info=True)
    numpy.testing.assert_almost_equal(
        darks_infos.machine_current[0], numpy.mean(darks_machine_current)
    )
    numpy.testing.assert_almost_equal(
        darks_infos.count_time[0], numpy.mean(darks_count_time)
    )

    _, darks_infos = scan.compute_reduced_darks(
        reduced_method="first", return_info=True
    )
    numpy.testing.assert_almost_equal(
        darks_infos.machine_current[0], darks_machine_current[0]
    )
    numpy.testing.assert_almost_equal(darks_infos.count_time[0], darks_count_time[0])

    _, darks_infos = scan.compute_reduced_darks(reduced_method="last", return_info=True)
    numpy.testing.assert_almost_equal(
        darks_infos.machine_current[0], darks_machine_current[-1]
    )
    numpy.testing.assert_almost_equal(darks_infos.count_time[0], darks_count_time[-1])

    # test reduced metadata on flats
    _, flats_infos = scan.compute_reduced_flats(
        reduced_method="median", return_info=True
    )
    assert isinstance(flats_infos, ReducedFramesInfos)
    assert len(flats_infos.machine_current) == len(flats_infos.count_time) == 2
    numpy.testing.assert_almost_equal(
        flats_infos.machine_current[0],
        numpy.median(flats_s1_machine_current),
    )
    numpy.testing.assert_almost_equal(
        flats_infos.machine_current[1],
        numpy.median(flats_s2_machine_current),
    )
    numpy.testing.assert_almost_equal(
        flats_infos.count_time[0], numpy.median(flats_s1_count_time)
    )
    numpy.testing.assert_almost_equal(
        flats_infos.count_time[1], numpy.median(flats_s2_count_time)
    )

    _, flats_infos = scan.compute_reduced_flats(reduced_method="mean", return_info=True)
    numpy.testing.assert_almost_equal(
        flats_infos.machine_current[0], numpy.mean(flats_s1_machine_current)
    )
    numpy.testing.assert_almost_equal(
        flats_infos.machine_current[1], numpy.mean(flats_s2_machine_current)
    )
    numpy.testing.assert_almost_equal(
        flats_infos.count_time[0], numpy.mean(flats_s1_count_time)
    )
    numpy.testing.assert_almost_equal(
        flats_infos.count_time[1], numpy.mean(flats_s2_count_time)
    )
    # no test on first and last but this is the same as for darks


def test_reduce_hdf5_fails(tmp_path):
    folder_1 = tmp_path / "test2"
    scan = MockNXtomo(
        scan_path=folder_1,
        ini_dark=None,
        ini_flats=None,
        final_flats=None,
        dim=20,
        n_proj=12,
    ).scan
    assert scan.compute_reduced_flats(reduced_method="first", return_info=False) == {}
    assert scan.compute_reduced_darks(reduced_method="last", return_info=False) == {}
