# coding: utf-8
from __future__ import annotations

import os

import fabio
import numpy

from tomoscan.esrf.mock import MockEDF as _MockEDF
from tomoscan.factory import Factory
from tomoscan.scanbase import ReducedFramesInfos


class MockEDFWithRawRef(_MockEDF):
    def __init__(
        self,
        scan_path,
        n_radio,
        flats: dict,
        darks: dict,
        n_extra_radio=0,
        scan_range=360,
        n_recons=0,
        n_pag_recons=0,
        recons_vol=False,
        dim=200,
        scene="noise",
        machine_current: numpy.array | None = None,
        count_time: numpy.array | None = None,
    ):
        self.flat_n = len(flats[list(flats.keys())[0]]) if len(flats) > 0 else 0
        self.dark_n = len(flats[list(darks.keys())[0]]) if len(darks) > 0 else 0
        self.flats = flats
        self.darks = darks
        self.dim = dim
        self._machine_current = machine_current
        self._count_time = count_time
        super().__init__(
            scan_path,
            n_radio,
            n_ini_radio=n_radio,
            n_extra_radio=n_extra_radio,
            scan_range=scan_range,
            n_recons=n_recons,
            n_pag_recons=n_pag_recons,
            recons_vol=recons_vol,
            dim=dim,
            scene=scene,
            dark_n=self.dark_n,
            flat_n=self.flat_n,
        )

        # add some raw dark and raw flat
        self.add_darks()
        self.add_flats()

        # add some darkHST and rehHST containing other data...
        self.addFalseReducedFlats()
        self.addFalseReducedDark()

    def add_dark(self, index):
        pass

    def add_flat(self, index):
        pass

    def add_flats(self):
        for i_serie, flats in self.flats.items():
            for i_flat, flat in enumerate(flats):
                file_name = f"ref{str(i_flat).zfill(4)}_{str(i_serie).zfill(4)}.edf"
                file_path = os.path.join(self.scan_path, file_name)
                if not os.path.exists(file_path):
                    header = {
                        "motor_pos": f"{i_serie} 0.0 1.0 2.0",
                        "motor_mne": "srot sx sy sz",
                    }
                    edf_writer = fabio.edfimage.EdfImage(
                        data=flat,
                        header=header,
                    )
                    edf_writer.write(file_path)

    def add_darks(self):
        for i_serie, darks in self.darks.items():
            assert darks.ndim == 3
            assert darks.shape[0] == 1
            file_name = f"darkend{i_serie:04}.edf"
            file_path = os.path.join(self.scan_path, file_name)
            if not os.path.exists(file_path):
                edf_writer = fabio.edfimage.EdfImage(
                    data=darks.reshape(darks.shape[1], darks.shape[2]),
                    header={
                        "motor_pos": f"{i_serie} 0.0 1.0 2.0",
                        "motor_mne": "srot sx sy sz",
                    },
                )
                edf_writer.write(file_path)

    def addFalseReducedDark(self):
        data = numpy.zeros((self.dim, self.dim)) - 1
        file_name = "dark.edf"
        file_path = os.path.join(self.scan_path, file_name)
        if not os.path.exists(file_path):
            edf_writer = fabio.edfimage.EdfImage(
                data=data,
                header={
                    "motor_pos": f"{-1} 0.0 1.0 2.0",
                    "motor_mne": "srot sx sy sz",
                },
            )
            edf_writer.write(file_path)

    def addFalseReducedFlats(self):
        for i_serie, flats in self.flats.items():
            data = numpy.zeros((self.dim, self.dim)) - 1
            file_name = f"refHST{i_serie:04}.edf"
            file_path = os.path.join(self.scan_path, file_name)
            if not os.path.exists(file_path):
                edf_writer = fabio.edfimage.EdfImage(
                    data=data,
                    header={
                        "motor_pos": f"{-1} 0.0 1.0 2.0",
                        "motor_mne": "srot sx sy sz",
                    },
                )
            edf_writer.write(file_path)

    def write_metadata(self, n_radio, scan_range, flat_n, dark_n):
        super().write_metadata(
            n_radio=n_radio, scan_range=scan_range, flat_n=flat_n, dark_n=dark_n
        )
        info_file = self.get_info_file()
        with open(info_file, "a") as info_file:
            if self._machine_current is not None:
                info_file.write("SrCurrent=    " + str(self._machine_current) + "\n")
            if self._count_time is not None:
                info_file.write("Count_time=    " + str(self._count_time) + "\n")


def test_reduce_edf(tmp_path):
    dim = 20
    folder_1 = tmp_path / "test1"
    folder_1.mkdir()
    n_proj = 12
    n_darks = 1

    count_time = 1.2  # for edf now we only consider a scalar (store in the .info file)
    machine_current = (
        10.2  # for edf now we only consider a scalar (store in the .info file)
    )

    raw_darks = numpy.ones((n_darks, dim, dim), dtype="f")

    raw_flats_s1 = numpy.asarray(
        [
            numpy.ones((dim, dim), dtype=numpy.float32),
            numpy.ones((dim, dim), dtype=numpy.float32) + 1.0,
            numpy.ones((dim, dim), dtype=numpy.float32) + 2.0,
            numpy.ones((dim, dim), dtype=numpy.float32) + 3.0,
            numpy.ones((dim, dim), dtype=numpy.float32) + 4.0,
        ]
    )

    raw_flats_s2 = numpy.asarray(
        [
            numpy.ones((dim, dim), dtype=numpy.float32) + 10.0,
            numpy.ones((dim, dim), dtype=numpy.float32) + 11.0,
            numpy.ones((dim, dim), dtype=numpy.float32) + 12.0,
            numpy.ones((dim, dim), dtype=numpy.float32) + 13.0,
            numpy.ones((dim, dim), dtype=numpy.float32) + 14.0,
        ]
    )

    MockEDFWithRawRef(
        scan_path=str(folder_1),
        n_radio=n_proj,
        flats={0: raw_flats_s1, 12: raw_flats_s2},
        darks={0: raw_darks},
        machine_current=machine_current,
        count_time=count_time,
    )
    scan = Factory.create_scan_object(str(folder_1))

    # test reduced frames

    numpy.testing.assert_array_equal(
        scan.compute_reduced_darks(reduced_method="median")[0],
        scan.compute_reduced_darks(reduced_method="mean")[0],
    )

    numpy.testing.assert_array_equal(
        scan.compute_reduced_flats(reduced_method="median")[0],
        numpy.median(raw_flats_s1, axis=0).astype(numpy.int32),
    )
    numpy.testing.assert_array_equal(
        scan.compute_reduced_flats(reduced_method="mean", output_dtype=numpy.float32)[
            0
        ],
        numpy.mean(raw_flats_s1, axis=0),
    )

    numpy.testing.assert_array_equal(
        scan.compute_reduced_flats(reduced_method="median")[12],
        numpy.median(raw_flats_s2, axis=0).astype(numpy.int32),
    )
    numpy.testing.assert_array_equal(
        scan.compute_reduced_flats(reduced_method="mean")[12],
        numpy.mean(raw_flats_s2, axis=0).astype(numpy.int32),
    )

    numpy.testing.assert_array_equal(
        scan.compute_reduced_flats(reduced_method="first")[0],
        numpy.ones((dim, dim), dtype=numpy.int32),
    )

    numpy.testing.assert_array_equal(
        scan.compute_reduced_flats(reduced_method="last")[0],
        numpy.ones((dim, dim), dtype=numpy.int32) + 4,
    )

    numpy.testing.assert_array_equal(
        scan.compute_reduced_flats(reduced_method="first", output_dtype=None)[12],
        numpy.ones((dim, dim), dtype=numpy.float32) + 10.0,
    )

    # test reduced metadata
    _, darks_metadata = scan.compute_reduced_darks(
        reduced_method="median", return_info=True
    )
    assert isinstance(darks_metadata, ReducedFramesInfos)
    assert len(darks_metadata.count_time) == len(darks_metadata.machine_current) == 1
    # with the current method (only one Srcurrent and Count_time value per acquistion) flats and darks will have the same value
    # and also the same no matter the method to compute it
    assert darks_metadata.count_time[0] == count_time
    assert darks_metadata.machine_current[0] == machine_current
    _, flats_metadata = scan.compute_reduced_flats(
        reduced_method="mean", return_info=True
    )
    assert len(flats_metadata.count_time) == len(flats_metadata.machine_current) == 2
    assert (
        darks_metadata.count_time[0]
        == flats_metadata.count_time[0]
        == flats_metadata.count_time[1]
    )
    assert (
        darks_metadata.machine_current[0]
        == flats_metadata.machine_current[0]
        == flats_metadata.machine_current[1]
    )


def test_reduce_edf_fails(tmp_path):
    folder_1 = tmp_path / "test2"

    MockEDFWithRawRef(scan_path=str(folder_1), n_radio=12, flats={}, darks={})
    scan = Factory.create_scan_object(str(folder_1))
    assert scan.compute_reduced_flats(reduced_method="first", return_info=False) == {}
    assert scan.compute_reduced_darks(reduced_method="last", return_info=False) == {}
