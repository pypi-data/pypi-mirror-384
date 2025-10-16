# coding: utf-8

import os
import shutil
import tempfile
import unittest

import h5py
import numpy
import pytest
import pint
from silx.io.url import DataUrl
from silx.io.utils import get_data

from tomoscan.esrf.scan.nxtomoscan import NXtomoScan, ImageKey, TomoFrame
from tomoscan.esrf.scan.mock import MockNXtomo
from tomoscan.nexus.paths.nxtomo import get_paths as get_nexus_paths
from tomoscan.nexus.paths.nxtomo import nx_tomo_path_latest, nx_tomo_path_v_1_0
from tomoscan.scanbase import ReducedFramesInfos
from tomoscan.tests.utils import NXtomoMockContext
from tomoscan.tests.datasets import GitlabDataset
from nxtomo.application.nxtomo import NXtomo

_ureg = pint.get_application_registry()


class HDF5TestBaseClass(unittest.TestCase):
    """base class for hdf5 unit test"""

    def get_dataset(self, hdf5_dataset_name):
        output_dataset_file = os.path.join(
            self.test_dir, os.path.basename(hdf5_dataset_name)
        )
        raw_dataset_file = GitlabDataset.get_dataset(hdf5_dataset_name)
        if raw_dataset_file is None:
            raise ValueError(f"Unable to retrieve {hdf5_dataset_name}")
        shutil.copy(src=raw_dataset_file, dst=output_dataset_file)
        return output_dataset_file

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir)


class TestHDF5Scan(HDF5TestBaseClass):
    """Basic test for the hdf5 scan"""

    def setUp(self) -> None:
        super(TestHDF5Scan, self).setUp()
        self.dataset_file = self.get_dataset(
            "h5_datasets/frm_edftomomill_twoentries.nx"
        )
        assert os.path.exists(self.dataset_file)
        self.scan = NXtomoScan(scan=self.dataset_file)
        self.scan.nexus_version = 1.0

    def testGeneral(self):
        """some general on the HDF5Scan"""
        self.assertEqual(self.scan.master_file, self.dataset_file)
        self.assertEqual(self.scan.path, os.path.dirname(self.dataset_file))
        self.assertEqual(self.scan.type, "hdf5")
        self.assertEqual(self.scan.entry, "/entry0000")
        self.assertEqual(len(self.scan.flats), 42)
        self.assertEqual(len(self.scan.darks), 1)
        self.assertEqual(
            len(self.scan.return_projs), 0
        )  # because frm_edftomomill_twoentries doesn't contain the image_key_control dataset. So in this case we always have 0 alignment projections
        self.assertEqual(self.scan.tomo_n, None)
        self.assertEqual(self.scan.start_time, None)
        self.assertEqual(self.scan.end_time, None)
        self.assertEqual(self.scan.energy, 17.05)
        self.assertEqual(self.scan.field_of_view, None)
        self.assertEqual(self.scan.x_rotation_axis_pixel_position, None)
        self.assertEqual(len(self.scan.x_translation), 1546)
        self.assertEqual(len(self.scan.y_translation), 1546)
        self.assertEqual(len(self.scan.z_translation), 1546)

        proj_angles = self.scan.get_proj_angle_url()
        self.assertEqual(
            len(proj_angles), 1500 + 3 - 1
        )  # -1 because the dataset has twice the same example defined. Has there is no image_key_control return projection are not handled.
        self.assertTrue(90 in proj_angles)
        self.assertTrue(24.0 in proj_angles)
        self.assertTrue(179.88 not in proj_angles)

        url_1 = proj_angles[0]
        self.assertTrue(url_1.is_valid())
        self.assertTrue(url_1.is_absolute())
        self.assertEqual(url_1.scheme(), "silx")
        # check conversion to dict
        _dict = self.scan.to_dict()
        scan2 = NXtomoScan.from_dict(_dict)
        self.assertEqual(scan2.master_file, self.scan.master_file)
        self.assertEqual(scan2.entry, self.scan.entry)

    def testFrames(self):
        """Check the `frames` property which is massively used under the
        NXtomoScan class"""
        frames = self.scan.frames
        # check some projections
        proj_2 = frames[24]
        self.assertTrue(isinstance(proj_2, TomoFrame))
        self.assertEqual(proj_2.index, 24)
        numpy.isclose(proj_2.rotation_angle, 0.24)
        self.assertFalse(proj_2.is_control)
        self.assertEqual(proj_2.url.file_path(), self.scan.master_file)
        self.assertEqual(proj_2.url.data_path(), "/entry0000/instrument/detector/data")
        self.assertEqual(proj_2.url.data_slice(), 24)
        self.assertEqual(proj_2.image_key, ImageKey.PROJECTION)
        self.assertEqual(get_data(proj_2.url).shape, (20, 20))
        # check last two non-return projection
        for frame_index in (1520, 1542):
            with self.subTest(frame_index=frame_index):
                frame = frames[frame_index]
                self.assertTrue(frame.image_key, ImageKey.PROJECTION)
                self.assertFalse(frame.is_control)

        # check some darks
        dark_0 = frames[0]
        self.assertEqual(dark_0.index, 0)
        numpy.isclose(dark_0.rotation_angle, 0.0)
        self.assertFalse(dark_0.is_control)
        self.assertEqual(dark_0.url.file_path(), self.scan.master_file)
        self.assertEqual(dark_0.url.data_path(), "/entry0000/instrument/detector/data")
        self.assertEqual(dark_0.url.data_slice(), 0)
        self.assertEqual(dark_0.image_key, ImageKey.DARK_FIELD)
        self.assertEqual(get_data(dark_0.url).shape, (20, 20))

        # check some flats
        flat_1 = frames[2]
        self.assertEqual(flat_1.index, 2)
        numpy.isclose(flat_1.rotation_angle, 0.0)
        self.assertFalse(flat_1.is_control)
        self.assertEqual(flat_1.url.file_path(), self.scan.master_file)
        self.assertEqual(flat_1.url.data_path(), "/entry0000/instrument/detector/data")
        self.assertEqual(flat_1.url.data_slice(), 2)
        self.assertEqual(flat_1.image_key, ImageKey.FLAT_FIELD)
        self.assertEqual(get_data(flat_1.url).shape, (20, 20))

        # check some return projections
        r_proj_0 = frames[1543]
        self.assertTrue(isinstance(r_proj_0, TomoFrame))
        self.assertEqual(r_proj_0.index, 1543)
        numpy.isclose(r_proj_0.rotation_angle, 180)
        self.assertFalse(
            r_proj_0.is_control
        )  # there is no image_key_control dataset in the current dataset
        self.assertEqual(r_proj_0.url.file_path(), self.scan.master_file)
        self.assertEqual(
            r_proj_0.url.data_path(), "/entry0000/instrument/detector/data"
        )
        self.assertEqual(r_proj_0.url.data_slice(), 1543)
        self.assertEqual(r_proj_0.image_key, ImageKey.PROJECTION)
        self.assertEqual(get_data(r_proj_0.url).shape, (20, 20))

    def testProjections(self):
        """Make sure projections are valid"""
        projections = self.scan.projections
        self.assertEqual(len(self.scan.projections), 1503)
        url_0 = projections[list(projections.keys())[0]]
        self.assertEqual(url_0.file_path(), os.path.join(self.scan.master_file))
        self.assertEqual(url_0.data_slice(), 22)
        # should be 4 but angles are truely missleading: 179.88, 180.0, 90, 0.
        # in this case we are not using any information from image_key_control
        # and we wait deduce 'return mode' from angles.
        self.assertEqual(
            len(self.scan.alignment_projections), 0
        )  # frm_edftomomill_twoentries doesn't contain the image_key_control

    def testDark(self):
        """Make sure darks are valid"""
        n_dark = 1
        self.assertEqual(self.scan.dark_n, n_dark)
        darks = self.scan.darks
        self.assertEqual(len(darks), 1)
        # TODO check accumulation time

    def testFlats(self):
        """Make sure flats are valid"""
        n_flats = 42
        flats = self.scan.flats
        self.assertEqual(len(flats), n_flats)
        self.assertEqual(
            self.scan.flat_n, n_flats // 2
        )  # because get two series of flat
        with self.assertRaises(NotImplementedError):
            self.scan.ff_interval

    def testDims(self):
        self.assertEqual(self.scan.dim_1, 20)
        self.assertEqual(self.scan.dim_2, 20)

    def testAxisUtils(self):
        self.assertEqual(self.scan.scan_range, 180)
        self.assertEqual(len(self.scan.projections), 1503)

        radios_urls_evolution = self.scan.get_proj_angle_url()
        self.assertEqual(
            len(radios_urls_evolution), 1502
        )  # get 1502 because there is one overwrite because get twice the same exact position
        self.assertEqual(radios_urls_evolution[0].file_path(), self.scan.master_file)
        self.assertEqual(radios_urls_evolution[0].data_slice(), 22)
        self.assertEqual(
            radios_urls_evolution[0].data_path(), "/entry0000/instrument/detector/data"
        )

    def testDarkRefUtils(self):
        self.assertEqual(len(self.scan.projections), 1503)
        pixel_size = self.scan.pixel_size
        self.assertTrue(pixel_size is not None)
        self.assertTrue(
            numpy.isclose(self.scan.pixel_size * _ureg.meter, 0.05 * _ureg.millimeter)
        )
        self.assertTrue(numpy.isclose(self.scan.get_pixel_size(unit="micrometer"), 50))
        self.assertTrue(
            numpy.isclose(
                self.scan.sample_x_pixel_size * _ureg.meter,
                0.05 * _ureg.millimeter,
            )
        )
        self.assertTrue(
            numpy.isclose(
                self.scan.sample_y_pixel_size * _ureg.meter,
                0.05 * _ureg.millimeter,
            )
        )

    def testNabuUtil(self):
        self.assertTrue(numpy.isclose(self.scan.sample_detector_distance, -19.9735))
        self.assertTrue(
            numpy.isclose(self.scan.get_sample_detector_distance(unit="cm"), -1997.35)
        )

    def testCompactedProjs(self):
        projs_compacted = self.scan.projections_compacted
        self.assertEqual(projs_compacted.keys(), self.scan.projections.keys())
        for i in range(22, 1520 + 1):
            self.assertEqual(projs_compacted[i].data_slice(), slice(22, 1521, None))
        for i in range(1542, 1543):
            self.assertEqual(projs_compacted[i].data_slice(), slice(1542, 1546, None))


class TestFlatFieldCorrection(HDF5TestBaseClass):
    """Test the flat field correction"""

    def setUp(self) -> None:
        super(TestFlatFieldCorrection, self).setUp()
        self.dataset_file = self.get_dataset(
            "h5_datasets/frm_edftomomill_twoentries.nx"
        )
        self.scan = NXtomoScan(scan=self.dataset_file)

    def testFlatAndDarksSet(self):
        self.scan.set_reduced_flats(
            {
                21: numpy.random.random(20 * 20).reshape((20, 20)),
                1520: numpy.random.random(20 * 20).reshape((20, 20)),
            }
        )
        self.scan.set_reduced_darks({0: numpy.random.random(20 * 20).reshape((20, 20))})

        projs = []
        proj_indexes = []
        for proj_index, proj in self.scan.projections.items():
            projs.append(proj)
            proj_indexes.append(proj_index)
        normed_proj = self.scan.flat_field_correction(
            projs=projs, proj_indexes=proj_indexes
        )
        self.assertEqual(len(normed_proj), len(self.scan.projections))
        raw_data = get_data(projs[50])
        self.assertFalse(numpy.array_equal(raw_data, normed_proj[50]))

    def testNoFlatOrDarkSet(self):
        projs = []
        proj_indexes = []
        for proj_index, proj in self.scan.projections.items():
            projs.append(proj)
            proj_indexes.append(proj_index)
        with self.assertLogs("tomoscan", level="ERROR"):
            normed_proj = self.scan.flat_field_correction(
                projs=projs, proj_indexes=proj_indexes
            )
        self.assertEqual(len(normed_proj), len(self.scan.projections))
        raw_data = get_data(projs[50])
        self.assertTrue(numpy.array_equal(raw_data, normed_proj[50]))


class TestGetSinogram(HDF5TestBaseClass):
    """Test the get_sinogram function"""

    def setUp(self) -> None:
        super(TestGetSinogram, self).setUp()
        self.dataset_file = self.get_dataset(
            "h5_datasets/frm_edftomomill_twoentries.nx"
        )

        self.scan = NXtomoScan(scan=self.dataset_file)
        # set some random dark and flats
        self.scan.set_reduced_flats(
            {
                21: numpy.random.random(20 * 20).reshape((20, 20)),
                1520: numpy.random.random(20 * 20).reshape((20, 20)),
            }
        )
        dark = numpy.random.random(20 * 20).reshape((20, 20))
        self.scan.set_reduced_darks({0: dark})
        self.scan._flats_weights = self.scan._get_flats_weights()
        self._raw_frame = []
        for index, url in self.scan.projections.items():
            self._raw_frame.append(get_data(url))
        self._raw_frame = numpy.asarray(self._raw_frame)

        assert self._raw_frame.ndim == 3

        normed_frames = []
        for proj_i, z_frame in enumerate(self._raw_frame):
            normed_frames.append(
                self.scan._frame_flat_field_correction(
                    data=z_frame,
                    dark=dark,
                    flat_weights=(
                        self.scan._flats_weights[proj_i]
                        if proj_i in self.scan._flats_weights
                        else None
                    ),
                )
            )
        self._normed_volume = numpy.array(normed_frames)
        assert self._normed_volume.ndim == 3
        self._normed_sinogram_12 = self._normed_volume[:, 12, :]
        assert self._normed_sinogram_12.ndim == 2
        assert self._normed_sinogram_12.shape == (1503, 20)

    def testGetSinogram1(self):
        sinogram = self.scan.get_sinogram(line=12, subsampling=1)
        self.assertEqual(sinogram.shape, (1503, 20))

    def testGetSinogram2(self):
        """Test if subsampling is negative"""
        with self.assertRaises(ValueError):
            self.scan.get_sinogram(line=0, subsampling=-1)

    def testGetSinogram3(self):
        sinogram = self.scan.get_sinogram(line=0, subsampling=3)
        self.assertEqual(sinogram.shape, (501, 20))

    def testGetSinogram4(self):
        """Test if line is not in the projection"""
        with self.assertRaises(ValueError):
            self.scan.get_sinogram(line=-1, subsampling=1)

    def testGetSinogram5(self):
        """Test if line is not in the projection"""
        with self.assertRaises(ValueError):
            self.scan.get_sinogram(line=25, subsampling=1)

    def testGetSinogram6(self):
        """Test if line is not in the projection"""
        with self.assertRaises(TypeError):
            self.scan.get_sinogram(line=0, subsampling="tata")


class TestIgnoredProjections(HDF5TestBaseClass):
    """Test the ignore_projections parameter"""

    def setUp(self) -> None:
        super(TestIgnoredProjections, self).setUp()
        self.dataset_file = self.get_dataset("h5_datasets/frm_edftomomill_oneentry.nx")

    def testIgnoreProjectionsIndices(self):
        ignored_projs_indices = [387, 388, 389, 390, 391, 392, 393, 394, 395, 396]
        scan = NXtomoScan(
            scan=self.dataset_file,
            ignore_projections={"kind": "indices", "values": ignored_projs_indices},
        )
        for idx in ignored_projs_indices:
            self.assertFalse(
                idx in scan.projections,
                "Projection index %d is supposed to be ignored" % idx,
            )

    def testIgnoreProjectionsAngles(self):
        ignored_projs_angles = [102, 102.12, 102.24, 102.36, 103.8]
        corresponding_projs_indices = [872, 873, 874, 875, 887]  # mind the jump
        scan = NXtomoScan(
            scan=self.dataset_file,
            ignore_projections={"kind": "angles", "values": ignored_projs_angles},
        )
        self.assertTrue(
            numpy.allclose(
                corresponding_projs_indices, scan.get_ignored_projection_indices()
            )
        )
        for idx in scan.projections.keys():
            assert_func = (
                self.assertFalse
                if idx in corresponding_projs_indices
                else self.assertTrue
            )
            assert_func(
                idx in scan.projections,
                "Something off with projection index %d. The scan has projections %s, but should have the following excluded: %s"
                % (idx, sorted(scan.projections.keys()), corresponding_projs_indices),
            )

    def testIgnoreProjectionsAngularRange(self):
        ignored_projs_angular_range = [40.18, 58.8]
        corresponding_projs_indices = list(range(357, 512 + 1))
        scan = NXtomoScan(
            scan=self.dataset_file,
            ignore_projections={"kind": "range", "values": ignored_projs_angular_range},
        )
        self.assertTrue(
            numpy.allclose(
                corresponding_projs_indices, scan.get_ignored_projection_indices()
            )
        )
        for idx in scan.projections.keys():
            assert_func = (
                self.assertFalse
                if idx in corresponding_projs_indices
                else self.assertTrue
            )
            assert_func(
                idx in scan.projections,
                "Something off with projection index %d. The scan has projections %s, but should have the following excluded: %s"
                % (idx, sorted(scan.projections.keys()), corresponding_projs_indices),
            )


class TestGetSinogramLegacy(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()

        self.proj_data = numpy.arange(1000, 1000 + 10 * 20 * 30).reshape(30, 10, 20)
        self.proj_angle = numpy.linspace(0, 180, 30)
        self.dark_value = 0.5
        self.flat_value = 1
        self.dark_data = numpy.ones((10, 20)) * self.dark_value
        self.dark_angle = 0
        self.flat_data_1 = numpy.ones((10, 20)) * self.flat_value
        self.flat_angle_1 = 0

        self.flat_data_2 = numpy.ones((10, 20)) * self.flat_value
        self.flat_angle_2 = 90
        self.flat_data_3 = numpy.ones((10, 20)) * self.flat_value
        self.flat_angle_3 = 180

        # data dataset
        self.data = numpy.empty((34, 10, 20))
        self.data[0] = self.dark_data
        self.data[1] = self.flat_data_1
        self.data[2:17] = self.proj_data[:15]
        self.data[17] = self.flat_data_2
        self.data[18:33] = self.proj_data[15:]
        self.data[33] = self.flat_data_3

        self.file_path = os.path.join(self.test_dir, "test.h5")
        self.create_arange_dataset(self.file_path)

    def create_arange_dataset(self, file_path):
        if os.path.exists(file_path):
            os.remove(file_path)

        with h5py.File(file_path, mode="a") as h5f:
            entry = h5f.require_group("entry0000")

            # rotation angle
            entry["instrument/detector/data"] = self.data
            rotation_angle = numpy.empty(34)
            rotation_angle[0] = self.dark_angle
            rotation_angle[1] = self.flat_angle_1
            rotation_angle[2:17] = self.proj_angle[:15]
            rotation_angle[17] = self.flat_angle_2
            rotation_angle[18:33] = self.proj_angle[15:]
            rotation_angle[33] = self.flat_angle_3

            entry["sample/rotation_angle"] = rotation_angle

            # image key / images keys
            image_keys = []
            image_keys.append(ImageKey.DARK_FIELD.value)
            image_keys.append(ImageKey.FLAT_FIELD.value)
            image_keys.extend([ImageKey.PROJECTION.value] * 15)
            image_keys.append(ImageKey.FLAT_FIELD.value)
            image_keys.extend([ImageKey.PROJECTION.value] * 15)
            image_keys.append(ImageKey.FLAT_FIELD.value)
            entry["instrument/detector/image_key"] = numpy.array(image_keys)
            entry["instrument/detector/image_key_control"] = numpy.array(image_keys)

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir)

    def testImplementations(self):
        scan = NXtomoScan(self.file_path, "entry0000")
        assert len(scan.projections) == 30
        assert len(scan.flats) == 3
        assert len(scan.darks) == 1

        scan.set_reduced_darks(
            {
                0: self.dark_data,
            }
        )

        scan.set_reduced_flats(
            {
                1: self.flat_data_1,
                17: self.flat_data_2,
                33: self.flat_data_3,
            }
        )

        scan._flats_weights = scan._get_flats_weights()
        sinogram_old = scan._get_sinogram_ref_imp(line=5)
        sinogram_new = scan.get_sinogram(line=5)
        raw_sinogram = self.proj_data[:, 5, :]
        corrected = (raw_sinogram - self.dark_value) / (
            self.flat_value - self.dark_value
        )
        numpy.testing.assert_array_equal(corrected, sinogram_new)
        numpy.testing.assert_array_equal(sinogram_old, sinogram_new)


def test_NXtomoScan_API():
    """several minor test of the NXtomoScan API"""
    with NXtomoMockContext(
        scan_path=os.path.join(tempfile.mkdtemp(), "scan_test"),
        n_proj=10,
        n_ini_proj=10,
        distance=1.0,
        energy=1.0,
    ) as scan:
        scan.clear_cache()
        scan.is_abort()
        scan.nexus_version = 1.1
        scan.sequence_name
        scan.sample_name
        scan.group_size
        scan.exposure_time
        with pytest.raises(NotImplementedError):
            scan.ff_interval


def test_NXtomoScan_source_API():
    """test dedicated API for Source"""
    with NXtomoMockContext(
        scan_path=os.path.join(tempfile.mkdtemp(), "scan_test"),
        n_proj=10,
        n_ini_proj=10,
        distance=1.0,
        energy=1.0,
        field_of_view="Full",
    ) as scan:
        scan.source
        scan.source_name
        scan.source_type
        scan.instrument_name
        assert scan.field_of_view.value == "Full"
        scan.sample_x_pixel_size
        scan.sample_y_pixel_size


def test_TomoFrame_API():
    """Test TomoFrame API"""
    frame = TomoFrame(index=0, sequence_number=0)
    frame.image_key = ImageKey.PROJECTION
    with pytest.raises(TypeError):
        frame.image_key = "projection"
    frame.rotation_angle = 12.0
    frame.x_translation
    frame.y_translation
    frame.z_translation
    frame.is_control


def test_NXtomoScan_nxversion():
    """test various NX versions"""
    with NXtomoMockContext(
        scan_path=os.path.join(tempfile.mkdtemp(), "scan_test"),
        n_proj=10,
        n_ini_proj=10,
        distance=1.0,
        energy=1.0,
    ) as scan:
        hdf5scan = NXtomoScan(scan.master_file)
        # The default behavior is to take NX 1.1 if not present in file metadata
        # This is not future-proof, perhaps do a _NEXUS_PATHS_LATEST class ?
        assert hdf5scan.nexus_path is nx_tomo_path_latest
        energy_path_11 = hdf5scan.nexus_path.ENERGY_PATH

        hdf5scan = NXtomoScan(scan.master_file, nx_version=1.0)
        # Parse with a different NX version.
        # This Mock will provide energy at two different locations (instrument/beam/energy and beam/energy)
        # so we cannot test directly the "legacy files" behavior.
        # Instead we just check that the energy path is different in NX 1.0 and NX 1.1.
        assert hdf5scan.nexus_path is nx_tomo_path_v_1_0
        energy_path_10 = hdf5scan.nexus_path.ENERGY_PATH
        assert energy_path_10 != energy_path_11


def test_get_relative_file(tmpdir):
    """Test that get_relative_file function is working correctly for HDFScan"""
    folder_path = os.path.join(tmpdir, "scan_test")
    with NXtomoMockContext(
        scan_path=folder_path,
        n_proj=10,
        n_ini_proj=10,
        distance=1.0,
        energy=1.0,
    ) as scan:
        expected_f1 = os.path.join(folder_path, "scan_test_nabu_processes.h5")
        assert (
            scan.get_relative_file("nabu_processes.h5", with_dataset_prefix=True)
            == expected_f1
        )

        expected_f2 = os.path.join(folder_path, "nabu_processes.h5")
        assert (
            scan.get_relative_file("nabu_processes.h5", with_dataset_prefix=False)
            == expected_f2
        )


def test_save_and_load_dark(tmp_path):
    """test saving and loading of the dark is workinf for HDF5"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    with NXtomoMockContext(
        scan_path=str(test_dir),
        n_proj=10,
        n_ini_proj=10,
        distance=1.0,
        energy=1.0,
    ) as scan:
        # 1. simple test on loading / saving the darks and flats
        assert scan.load_reduced_darks() == {}
        assert scan.load_reduced_flats() == {}
        dark_frame = numpy.ones((100, 100))
        scan.save_reduced_darks(
            {
                0: dark_frame,
            }
        )
        assert scan.load_reduced_flats() == {}
        loaded_darks = scan.load_reduced_darks()
        assert len(loaded_darks) == 1
        assert 0 in loaded_darks
        numpy.testing.assert_array_equal(loaded_darks[0], dark_frame)

        # 2. test overwrite and make sure we are properly removing the existing dataset
        output_file_name = (
            scan.REDUCED_DARKS_DATAURLS[0]
            .file_path()
            .format(
                entry=scan.entry,
                idx=0,
                idx_zfill4=str(0).zfill(4),
                scan_prefix=os.path.basename(
                    scan.path,
                ),
            )
        )
        output_file_path = os.path.join(scan.path, output_file_name)

        # 2.1 make sure when should overwrite the dataset the adding size is limited (and dataset is overwrite)
        first_file_size = os.path.getsize(output_file_path)
        scan.save_reduced_darks(
            {
                0: dark_frame,
            },
            overwrite=True,
        )
        assert os.path.getsize(output_file_path) < (
            first_file_size + dark_frame.nbytes / 2
        )
        # 2.2 test when the dataset cannot be overwrite
        scan.save_reduced_darks(
            {
                100: dark_frame,
            },
            overwrite=True,
        )
        loaded_darks = scan.load_reduced_darks()
        assert tuple(loaded_darks.keys()) == (100,)
        assert os.path.getsize(output_file_path) > (first_file_size + dark_frame.nbytes)


def test_save_and_load_flats(tmp_path):
    """test saving and loading of the flats is workinf for HDF5"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    with NXtomoMockContext(
        scan_path=str(test_dir),
        n_proj=10,
        n_ini_proj=10,
        distance=1.0,
        energy=1.0,
    ) as scan:
        assert scan.load_reduced_darks() == {}
        assert scan.load_reduced_flats() == {}

        flat_frame_1 = numpy.ones((100, 100))
        flat_frame_222 = numpy.zeros((100, 100))
        scan.save_reduced_flats(
            {
                1: flat_frame_1,
                222: flat_frame_222,
            },
        )
        loaded_flats = scan.load_reduced_flats()
        assert len(loaded_flats) == 2
        assert 1 in loaded_flats
        assert 222 in loaded_flats
        numpy.testing.assert_array_equal(loaded_flats[1], flat_frame_1)
        numpy.testing.assert_array_equal(loaded_flats[222], flat_frame_222)
        assert scan.load_reduced_darks() == {}

        # test to save other flats to insure older one are removed
        flat_frame_333 = numpy.ones((100, 100)) * 3.2
        flat_frame_1 = numpy.ones((100, 100)) * 2.1
        scan.save_reduced_flats(
            {
                1: flat_frame_1,
                333: flat_frame_333,
            },
            overwrite=True,
        )
        loaded_flats = scan.load_reduced_flats()
        assert len(loaded_flats) == 2
        assert 1 in loaded_flats
        assert 333 in loaded_flats
        numpy.testing.assert_array_equal(loaded_flats[1], flat_frame_1)
        numpy.testing.assert_array_equal(loaded_flats[333], flat_frame_333)


def test_save_dark_flat_reduced_several_urls(tmp_path):
    """test saving and loading dark and flat providing several urls"""
    test_dir = tmp_path / "test_dir"
    os.makedirs(test_dir)
    with NXtomoMockContext(
        scan_path=str(test_dir),
        n_proj=10,
        n_ini_proj=10,
        distance=1.0,
        energy=1.0,
    ) as scan:
        assert scan.load_reduced_darks() == {}
        assert scan.load_reduced_flats() == {}

        url_flats_edf = NXtomoScan.REDUCED_FLATS_DATAURLS[0]
        url_flats_processes = DataUrl(
            file_path=scan.get_relative_file(
                file_name="my_processes.h5", with_dataset_prefix=False
            ),
            data_path="/{entry}/process_1/results/flats/{index}",
            scheme="hdf5",
        )
        url_darks_edf = NXtomoScan.REDUCED_DARKS_DATAURLS[0]
        url_darks_processes = DataUrl(
            file_path=scan.get_relative_file(
                file_name="my_processes.h5", with_dataset_prefix=False
            ),
            data_path="/{entry}/process_1/results/darks/{index}",
            scheme="silx",
        )

        flat_frame_1 = numpy.ones((100, 100))
        flat_frame_222 = numpy.zeros((100, 100))
        flats_infos = ReducedFramesInfos()

        flats_infos.count_time = [
            1,
        ]
        flats_infos.machine_current = [
            12.3,
        ]

        with pytest.raises(ValueError):
            scan.save_reduced_flats(
                flats={
                    1: flat_frame_1,
                    222: flat_frame_222,
                },
                flats_infos=flats_infos,
            )

        flats_infos.count_time = [1.0, 1.0]
        flats_infos.machine_current = [12.3, 13.2]
        scan.save_reduced_flats(
            flats={
                1: flat_frame_1,
                222: flat_frame_222,
            },
            flats_infos=flats_infos,
        )

        assert scan.load_reduced_darks() == {}
        flat_frame_1 = numpy.ones((100, 100))
        flat_frame_1000 = numpy.ones((100, 100)) * 1.2
        dark_frame = numpy.zeros((100, 100))
        scan.save_reduced_flats(
            flats={
                1: flat_frame_1,
                1000: flat_frame_1000,
            },
            flats_infos=flats_infos,
            output_urls=(
                url_flats_edf,
                url_flats_processes,
            ),
            overwrite=True,
        )
        # test raise a type error if frame is not a numpy array
        with pytest.raises(TypeError):
            scan.save_reduced_darks(
                darks={
                    0: "test",
                },
                output_urls=(
                    url_darks_edf,
                    url_darks_processes,
                ),
                overwrite=True,
            )

        # test raise a type error if frame is not a 2D numpy array
        with pytest.raises(ValueError):
            scan.save_reduced_darks(
                darks={
                    0: numpy.asarray([12, 13]),
                },
                output_urls=(
                    url_darks_edf,
                    url_darks_processes,
                ),
                overwrite=True,
            )

        scan.save_reduced_darks(
            darks={
                0: dark_frame,
            },
            output_urls=(
                url_darks_edf,
                url_darks_processes,
            ),
            overwrite=True,
        )
        darks_infos = ReducedFramesInfos()
        darks_infos.count_time = [2.5]
        darks_infos.machine_current = [13.1]
        scan.save_reduced_darks(
            darks={
                0: dark_frame,
            },
            output_urls=(
                url_darks_edf,
                url_darks_processes,
            ),
            darks_infos=darks_infos,
            overwrite=True,
        )
        assert len(scan.load_reduced_flats(return_info=False)) == 2
        assert len(scan.load_reduced_darks(return_info=False)) == 1

        _, loaded_darks_infos = scan.load_reduced_darks(return_info=True)
        assert loaded_darks_infos == darks_infos

        processes_file = os.path.join(scan.path, "my_processes.h5")
        assert os.path.exists(processes_file)

        _, loaded_flats_infos = scan.load_reduced_flats(return_info=True)
        assert loaded_flats_infos == flats_infos

        with h5py.File(processes_file, mode="r") as h5s:
            assert "/entry/process_1/results/darks" in h5s
            darks_grp = h5s["/entry/process_1/results/darks"]
            assert "0" in darks_grp
            numpy.testing.assert_array_equal(darks_grp["0"][()], dark_frame)
            assert "/entry/process_1/results/flats" in h5s
            flats_grp = h5s["/entry/process_1/results/flats"]
            assert "1" in flats_grp
            assert "1000" in flats_grp
            numpy.testing.assert_array_equal(flats_grp["1"], flat_frame_1)
            numpy.testing.assert_array_equal(flats_grp["1000"], flat_frame_1000)

        assert len(scan.load_reduced_flats((url_flats_processes,))) == 2
        assert len(scan.load_reduced_darks((url_darks_processes,))) == 1
        loaded_reduced_darks = scan.load_reduced_darks(
            (url_darks_processes,), return_as_url=True
        )
        assert isinstance(loaded_reduced_darks[0], DataUrl)
        assert loaded_reduced_darks[0].file_path() == processes_file
        assert loaded_reduced_darks[0].data_path() == "/entry/process_1/results/darks/0"
        assert loaded_reduced_darks[0].scheme() == "silx"


def test_get_bounding_box(tmp_path):
    """
    check bounding box and overlap works.
    Warning: the MockNxtomo is using the NXtomo coordinate system ()

                          Z axis
                             ^    Y axis
                             | /
           x-ray             |/
           -------->          ------> X axis

    When tomoscan coordinate system is the ESRF one

                            Y axis
                              ^   X axis
                              |  /
            x-ray             | /
            -------->          ------> Z axis

    """
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    x_pos_nxtomo_coord = 0.0 * _ureg.millimeter
    y_pos_nxtomo_coord = 1.0 * _ureg.millimeter
    z_pos_nxtomo_coord = 3.6 * _ureg.millimeter
    magnification = 2

    scan = MockNXtomo(
        scan_path=str(test_dir),
        n_proj=10,
        n_ini_proj=10,
        distance=1.0,
        energy=1.0,
        magnification=magnification,
        x_pos=x_pos_nxtomo_coord.magnitude,
        y_pos=y_pos_nxtomo_coord.magnitude,
        z_pos=z_pos_nxtomo_coord.magnitude,
    ).scan

    pixel_size = MockNXtomo.SAMPLE_PIXEL_SIZE * _ureg.micrometer
    frame_dim = 200

    # note: pixel size is provided with magnificaton. To get
    min_x_nxtomo_coord = x_pos_nxtomo_coord.to(_ureg.meter).magnitude - (
        frame_dim / 2.0 * pixel_size.to(_ureg.meter).magnitude
    )
    max_x_nxtomo_coord = x_pos_nxtomo_coord.to(_ureg.meter).magnitude + (
        frame_dim / 2.0 * pixel_size.to(_ureg.meter).magnitude
    )
    assert scan.get_bounding_box(axis="y") == (min_x_nxtomo_coord, max_x_nxtomo_coord)

    min_y_nxtomo_coord = y_pos_nxtomo_coord.to(_ureg.meter).magnitude - (
        frame_dim / 2.0 * pixel_size.to(_ureg.meter).magnitude
    )
    max_y_nxtomo_coord = y_pos_nxtomo_coord.to(_ureg.meter).magnitude + (
        frame_dim / 2.0 * pixel_size.to(_ureg.meter).magnitude
    )
    assert scan.get_bounding_box(axis="z") == (min_y_nxtomo_coord, max_y_nxtomo_coord)

    min_z_nxtomo_coord = z_pos_nxtomo_coord.to(_ureg.meter).magnitude - (
        frame_dim / 2.0 * pixel_size.to(_ureg.meter).magnitude
    )
    max_z_nxtomo_coord = z_pos_nxtomo_coord.to(_ureg.meter).magnitude + (
        frame_dim / 2.0 * pixel_size.to(_ureg.meter).magnitude
    )
    assert scan.get_bounding_box(axis="x") == (min_z_nxtomo_coord, max_z_nxtomo_coord)
    assert scan.get_bounding_box(axis=None) is not None


def test_clearing_cache(tmp_path):
    with NXtomoMockContext(
        scan_path=str(tmp_path / "my_scan"),
        n_proj=10,
        n_ini_proj=10,
        distance=1.0,
        energy=1.0,
    ) as scan:
        """Minor test on clearing cache."""
        assert scan.darks not in (None, {})
        assert scan.flats not in (None, {})
        nexus_path = get_nexus_paths(None)
        with h5py.File(scan.master_file, mode="a") as h5f:
            del h5f[f"{scan.entry}/{nexus_path.IMG_KEY_PATH}"]
            h5f[f"{scan.entry}/{nexus_path.IMG_KEY_PATH}"] = [
                ImageKey.INVALID.value
            ] * len(scan._image_keys_control)
            del h5f[f"{scan.entry}/{nexus_path.IMG_KEY_CONTROL_PATH}"]
            h5f[f"{scan.entry}/{nexus_path.IMG_KEY_CONTROL_PATH}"] = [
                ImageKey.INVALID.value
            ] * len(scan._image_keys_control)
        assert scan.darks not in (None, {})
        scan.clear_cache()
        assert scan.darks in (None, {})
        assert scan.flats in (None, {})


configs = (
    {
        "n_proj": 10,
        "with_darks": True,
        "with_flats": True,
        "return_angles": (0,),
    },
    {
        "n_proj": 10,
        "with_darks": False,
        "with_flats": False,
        "return_angles": tuple(),
    },
)


@pytest.mark.parametrize("config", configs)
def test_nxtomo_without_key_control(tmp_path, config):
    scan_path = str(tmp_path / "scan_no_image_key_control")
    mock = MockNXtomo(
        scan_path=scan_path,
        n_proj=config["n_proj"],
        n_ini_proj=config["n_proj"],
        n_alignement_proj=0,
        create_ini_dark=config["with_darks"],
        create_ini_flat=config["with_flats"],
        create_final_flat=False,
    )

    for i_frame, angle in enumerate(config["return_angles"]):
        mock.add_alignment_radio(index=i_frame + config["n_proj"], angle=angle)

    scan = mock.scan
    with h5py.File(scan.master_file, mode="a") as h5f:
        entry = h5f[scan.entry]
        del entry["instrument/detector/image_key_control"]

    clean_scan = NXtomoScan(scan=scan.master_file, entry=scan.entry)
    assert len(clean_scan.projections) == config["n_proj"] + len(
        config["return_angles"]
    )
    # whrn there is not 'image_key_control' we consider there is no alignment / return projections
    assert len(clean_scan.return_projs) == 0
    assert (len(clean_scan.darks) > 0) == config["with_darks"]
    assert (len(clean_scan.flats) > 0) == config["with_flats"]


def test_build_drac_metadata(tmp_path):
    scan_path = str(tmp_path / "test_build_drac_metadata.hdf5")
    scan = MockNXtomo(
        scan_path=scan_path,
        n_proj=10,
        n_ini_proj=10,
        n_alignement_proj=0,
        create_ini_dark=True,
        create_ini_flat=True,
        create_final_flat=True,
    ).scan
    # append some metadata to the file
    nx_tomo = NXtomo().load(
        scan.master_file, "entry", detector_data_as="as_numpy_array"
    )
    # warning: the Y on the NXtomo side match the MCStats convention when tomoscan coordinate system is the one used at ESRF.
    nx_tomo.sample.y_translation = (
        numpy.concatenate(
            (
                [-1],  # dark frame
                [0] * 10,  # flat frames
                numpy.linspace(1, 1.1, num=10, endpoint=False),  # projections
                [2] * 10,  # flat
            )
        )
        * _ureg.meter
    )
    nx_tomo.sample.x_pixel_size = 2.3 * _ureg.micrometer
    nx_tomo.instrument.detector.distance = 5.6 * _ureg.micrometer

    nx_tomo.save(scan.master_file, "entry", overwrite=True)

    icat_metadata = scan.build_drac_metadata()

    assert numpy.isclose(icat_metadata.pop("TOMO_ZDelta"), 0.01)
    assert numpy.isclose(icat_metadata.pop("TOMO_detectorDistance"), 5.6)
    assert numpy.isclose(icat_metadata.pop("TOMO_pixelSize"), 2.3)
    assert icat_metadata == {
        "definition": "TOMO",
        "TOMO_accExposureTime": numpy.float64(1.0),
        "TOMO_darkN": 1,
        "definition": "TOMO",
        "TOMO_halfAcquisition": False,
        "TOMO_projN": 10,
        "TOMO_refN": 10,
        "sample_name": "test",
        "Sample_name": "test",
        "TOMO_scanRange": 360,
        "TOMO_start_angle": numpy.float64(0.0),
        "TOMO_x_pixel_n": 200,
        "TOMO_y_pixel_n": 200,
        "TOMO_ZStart": 1.0,
    }


def test_splitted_flat_series(tmp_path):
    """test splitted_flat_serie property"""

    file_path = str(tmp_path / "test_flat_split.nx")

    nx_tomo_writer = NXtomo()
    nx_tomo_reader = NXtomoScan(scan=file_path, entry="entry")

    def setImageKey(values):
        nx_tomo_writer.sample.rotation_angle = numpy.linspace(0, 360, 10) * _ureg.degree
        nx_tomo_writer.instrument.detector.data = numpy.arange(10).reshape(10, 1, 1)
        nx_tomo_writer.instrument.detector.image_key_control = values
        nx_tomo_writer.save(file_path, "entry", overwrite=True)
        nx_tomo_reader.clear_frames_cache()

    setImageKey([ImageKey.FLAT_FIELD.value] * 10)

    assert len(nx_tomo_reader.splitted_flat_series) == 1
    assert len(nx_tomo_reader.splitted_flat_series[0]) == 10

    setImageKey(
        numpy.concatenate(
            (
                [ImageKey.FLAT_FIELD.value] * 3,
                [ImageKey.PROJECTION.value] * 3,
                [ImageKey.FLAT_FIELD.value] * 4,
            )
        )
    )

    assert len(nx_tomo_reader.splitted_flat_series) == 2
    assert len(nx_tomo_reader.splitted_flat_series[0]) == 3
    assert len(nx_tomo_reader.splitted_flat_series[1]) == 4

    setImageKey([ImageKey.PROJECTION.value] * 10)
    nx_tomo_reader._image_keys = nx_tomo_reader._image_keys_control = [
        ImageKey.PROJECTION.value
    ] * 10
    assert len(nx_tomo_reader.splitted_flat_series) == 0


def test_get_propagation_distance(tmp_path):
    nx_tomo = NXtomo()
    nx_tomo.instrument.detector.distance = 0.3 * _ureg.cm
    nx_tomo.instrument.source.distance = 1.2 * _ureg.m
    nx_tomo.sample.propagation_distance = (0.3 * _ureg.cm * 1.2 * _ureg.m) / (
        1.2 * _ureg.m + 0.3 * _ureg.cm
    )

    output_file = tmp_path / "my_nxtomo.nx"
    entry_name = "entry"

    nx_tomo.save(str(output_file), entry_name)

    scan = NXtomoScan(output_file, entry_name)
    assert (
        scan.sample_detector_distance
        == nx_tomo.instrument.detector.distance.to_base_units().magnitude
    )
    assert (
        scan.source_sample_distance
        == nx_tomo.instrument.source.distance.to_base_units().magnitude
    )
    z1 = nx_tomo.instrument.source.distance
    z2 = nx_tomo.instrument.detector.distance
    assert (
        scan.propagation_distance == ((z1 * z2) / (z1 + z2)).to_base_units().magnitude
    )


def test_pixel_size_getter(tmp_path):
    nx_tomo = NXtomo()
    nx_tomo.instrument.detector.x_pixel_size = 0.03 * _ureg.micrometer
    nx_tomo.instrument.detector.y_pixel_size = 0.02 * _ureg.micrometer

    nx_tomo.sample.x_pixel_size = 0.1 * _ureg.micrometer
    nx_tomo.sample.y_pixel_size = 0.12 * _ureg.micrometer

    output_file = tmp_path / "my_nxtomo.nx"
    entry_name = "entry"

    nx_tomo.save(str(output_file), entry_name)

    scan = NXtomoScan(output_file, entry_name)

    assert (
        scan.detector_x_pixel_size
        == nx_tomo.instrument.detector.x_pixel_size.to_base_units().magnitude
    )
    assert (
        scan.detector_y_pixel_size
        == nx_tomo.instrument.detector.y_pixel_size.to_base_units().magnitude
    )

    assert (
        scan.sample_x_pixel_size
        == nx_tomo.sample.x_pixel_size.to_base_units().magnitude
    )
    assert (
        scan.sample_y_pixel_size
        == nx_tomo.sample.y_pixel_size.to_base_units().magnitude
    )
