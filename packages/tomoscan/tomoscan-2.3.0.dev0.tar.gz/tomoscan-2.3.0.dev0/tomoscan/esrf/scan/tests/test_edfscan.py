# coding: utf-8

import h5py
import collections
import logging
import os
import shutil
import tempfile
import unittest
from glob import glob

import fabio.edfimage
import numpy
import pytest
import silx.io.utils
from silx.io.url import DataUrl
from silx.io.utils import get_data

from tomoscan.esrf.edfscan import EDFTomoScan
from tomoscan.esrf.mock import MockEDF
from tomoscan.factory import Factory
from tomoscan.scanbase import ReducedFramesInfos, TomoScanBase
from tomoscan.tests.datasets import GitlabDataset

logging.disable(logging.INFO)


class TestTomoBaseHashable(unittest.TestCase):
    """Make sure EDFTomoScan is hashable"""

    def setUp(self):
        self._folder = tempfile.mkdtemp()
        MockEDF.fastMockAcquisition(self._folder, n_radio=100)

    def tearDown(self):
        shutil.rmtree(self._folder)

    def test_is_hashable(self):
        tomo_base = TomoScanBase(scan=self._folder, type_="toto")
        self.assertTrue(isinstance(tomo_base, collections.abc.Hashable))
        tomo_scan = EDFTomoScan(self._folder)
        self.assertTrue(isinstance(tomo_scan, collections.abc.Hashable))


class TestScanFactory(unittest.TestCase):
    """Make sure the Scan factory is correctly working. Able to detect the valid
    scan type for a given file / directory
    """

    def test_no_scan(self):
        scan_dir = tempfile.mkdtemp()
        with self.assertRaises(ValueError):
            Factory.create_scan_object(scan_dir)

    def test_scan_edf(self):
        scan_dir = GitlabDataset.get_dataset("edf_datasets/test10")
        scan = Factory.create_scan_object(scan_dir)
        self.assertTrue(isinstance(scan, EDFTomoScan))
        assert scan.x_translation is None
        assert scan.y_translation is None
        assert scan.z_translation is None
        self.assertEqual(scan.tomo_n, 20)
        scan.clear_cache()
        scan.update()
        self.assertFalse(scan.is_abort())
        self.assertEqual(len(scan.projections), 20)
        self.assertEqual(len(scan.alignment_projections), 13)
        self.assertEqual(scan.scan_range, 180)
        self.assertEqual(scan.field_of_view, None)
        self.assertEqual(scan.x_rotation_axis_pixel_position, None)
        assert scan.dim_1 == 512
        assert scan.dim_2 == 512
        assert scan.ff_interval == 20
        assert len(scan.alignment_projections) > 0
        assert scan.instrument_name is None
        # this information is not provided for edf
        assert numpy.isclose(scan.sample_detector_distance, 0.008)
        assert numpy.isclose(scan.energy, 19.0)
        assert numpy.isclose(scan.pixel_size, 3.02e-06)
        assert numpy.isclose(scan.scan_range, 180)


class TestDarksFlats(unittest.TestCase):
    """unit test for the FTSerieReconstruction functions"""

    def setUp(self):
        def saveData(data, _file, folder):
            file_desc = fabio.edfimage.EdfImage(data=data)
            file_desc.write(os.path.join(folder, _file))

        unittest.TestCase.setUp(self)
        self.folderTwoFlats = tempfile.mkdtemp()
        self.folderOneFlat = tempfile.mkdtemp()

        self.darkData = numpy.arange(100).reshape(10, 10)
        self.flatField_0 = numpy.arange(start=10, stop=110).reshape(10, 10)
        self.flatField_600 = numpy.arange(start=-10, stop=90).reshape(10, 10)
        self.flatField = numpy.arange(start=0, stop=100).reshape(10, 10)

        # save configuration one
        saveData(self.darkData, "darkHST.edf", self.folderTwoFlats)
        saveData(self.flatField_0, "refHST_0000.edf", self.folderTwoFlats)
        saveData(self.flatField_600, "refHST_0600.edf", self.folderTwoFlats)

        # save configuration two
        saveData(self.darkData, "dark.edf", self.folderOneFlat)
        saveData(self.flatField, "refHST.edf", self.folderOneFlat)

        self.acquiOneFlat = EDFTomoScan(self.folderOneFlat)
        self.acquiTwoFlats = EDFTomoScan(self.folderTwoFlats)

    def tearDown(self):
        for f in (self.folderOneFlat, self.folderTwoFlats):
            shutil.rmtree(f)
        unittest.TestCase.tearDown(self)

    def testDarks(self):
        self.assertTrue(isinstance(self.acquiOneFlat.darks, dict))
        self.assertEqual(len(self.acquiOneFlat.darks), 1)
        self.assertTrue(isinstance(self.acquiTwoFlats.darks, dict))
        self.assertEqual(len(self.acquiTwoFlats.darks), 1)

        self.assertTrue(
            numpy.array_equal(
                silx.io.utils.get_data(self.acquiOneFlat.darks[0]), self.darkData
            )
        )
        self.assertTrue(
            numpy.array_equal(
                silx.io.utils.get_data(self.acquiTwoFlats.darks[0]), self.darkData
            )
        )

    def testFlats(self):
        """test that refHST flats are correctly found"""
        # check one flat file with two ref
        self.assertEqual(len(self.acquiOneFlat.flats), 1)
        self.assertTrue(isinstance(self.acquiOneFlat.flats[0], silx.io.url.DataUrl))

        data = silx.io.utils.get_data(self.acquiOneFlat.flats[0])
        numpy.array_equal(data, self.flatField)

        # check two flat files
        self.assertTrue(
            numpy.array_equal(
                silx.io.utils.get_data(self.acquiTwoFlats.flats[600]),
                self.flatField_600,
            )
        )
        self.assertTrue(
            numpy.array_equal(
                silx.io.utils.get_data(self.acquiTwoFlats.flats[0]), self.flatField_0
            )
        )
        self.assertTrue(12 not in self.acquiTwoFlats.flats)
        self.acquiTwoFlats.clear_frames_cache()
        os.remove(os.path.join(self.folderTwoFlats, "refHST_0000.edf"))
        os.remove(os.path.join(self.folderTwoFlats, "refHST_0600.edf"))
        self.assertEqual(self.acquiTwoFlats.flats, {})


class TestOriDarksFlats(unittest.TestCase):
    """
    Test that original ref* and dark* before creation of refHST  and darkHST
    are correctly found
    """

    def setUp(self) -> None:
        unittest.TestCase.setUp(self)
        self.pixel_size = 0.05
        self.det_width = 10
        self.det_height = 10

        self.folder = tempfile.mkdtemp()
        # create 2 series of ref with 20 frames each and 2 refHST file
        for ref_index in ("0000", "1500"):
            # ref files
            for ref_sub_index in range(20):
                file_desc = fabio.edfimage.EdfImage(
                    data=numpy.random.random((self.det_height, self.det_width))
                )
                file_name = "_".join(
                    (
                        "ref",
                        str(ref_sub_index).zfill(4),
                        str(ref_index).zfill(4) + ".edf",
                    )
                )
                file_name = os.path.join(self.folder, file_name)
                file_desc.write(file_name)
            # simulate two refHST generated by tomwer
            file_desc = fabio.edfimage.EdfImage(
                data=numpy.random.random((self.det_height, self.det_width))
            )
            file_name = "refHST" + str(ref_index).zfill(4) + ".edf"
            file_name = os.path.join(self.folder, file_name)
            file_desc.write(file_name)

        # create one dark with 10 frames
        file_desc = fabio.edfimage.EdfImage(
            data=numpy.random.random((self.det_height, self.det_width))
        )
        for frame in range(9):
            file_desc.append_frame(
                data=numpy.random.random((self.det_height, self.det_width))
            )
        self._dark_file_name = os.path.join(self.folder, "darkend0000.edf")
        file_desc.write(self._dark_file_name)

        self.scan = EDFTomoScan(self.folder)
        # create a .info for mocking the acquisition
        self.write_metadata(n_radio=0, scan_range=360, flat_n=20, dark_n=1)
        assert self.scan.dark_n == 1
        assert self.scan.flat_n == 20
        assert numpy.isclose(self.scan.pixel_size * 10e5, self.pixel_size)

    def get_info_file(self):
        return os.path.join(self.scan.path, os.path.basename(self.scan.path) + ".info")

    def write_metadata(self, n_radio, scan_range, flat_n, dark_n):
        info_file = self.get_info_file()
        if not os.path.exists(info_file):
            # write the info file
            with open(self.get_info_file(), "w") as info_file:
                info_file.write("TOMO_N=    " + str(n_radio) + "\n")
                info_file.write("ScanRange= " + str(scan_range) + "\n")
                info_file.write("REF_N=     " + str(flat_n) + "\n")
                info_file.write("REF_ON=    " + str(n_radio) + "\n")
                info_file.write("DARK_N=    " + str(dark_n) + "\n")
                info_file.write("Dim_1=     " + str(self.det_width) + "\n")
                info_file.write("Dim_2=     " + str(self.det_height) + "\n")
                info_file.write("Col_beg=    0" + "\n")
                info_file.write("Col_end=   " + str(self.det_width) + "\n")
                info_file.write("Row_beg=    0" + "\n")
                info_file.write("Row_end=    " + str(self.det_height) + "\n")
                info_file.write("PixelSize=  " + str(self.pixel_size) + "\n")

    def tearDown(self) -> None:
        shutil.rmtree(self.folder)
        unittest.TestCase.tearDown(self)

    def testFlatsOri(self):
        flat_urls = self.scan.get_flats_url(prefix="ref", scan_path=self.scan.path)
        self.assertEqual(len(flat_urls), 42)
        # checks some random files
        file_paths = [url.file_path() for url in flat_urls.values()]
        for ref_file in ("ref_0000_1500.edf", "ref_0004_0000.edf", "ref_0019_1500.edf"):
            ref_full_path = os.path.join(self.scan.path, ref_file)
            self.assertTrue(ref_full_path in file_paths)
        flat_urls = self.scan.get_flats_url(prefix="refHST", scan_path=self.scan.path)
        self.assertEqual(len(flat_urls), 2)

        flat_urls = self.scan.get_flats_url(
            prefix="ref", scan_path=self.scan.path, ignore=("HST",)
        )
        self.assertEqual(len(flat_urls), 40)

    def testDarksOri(self):
        darks = self.scan.get_darks_url(prefix="darkend", scan_path=self.scan.path)
        self.assertEqual(len(darks), 10)
        # check one random url
        url = DataUrl(
            file_path=self._dark_file_name,
            data_slice=[
                4,
            ],
            scheme="fabio",
        )
        self.assertTrue(url in darks.values())


class TestProjections(unittest.TestCase):
    """Test that the"""

    def setUp(self) -> None:
        self.folder = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.folder)

    def testProjectionNoExtra(self):
        mock = MockEDF(
            scan_path=self.folder, n_radio=10, n_ini_radio=10, n_extra_radio=0
        )
        mock.end_acquisition()
        scan = EDFTomoScan(scan=self.folder)
        self.assertEqual(len(scan.projections), 10)

    def testProjectionUpdate(self):
        mock = MockEDF(scan_path=self.folder, n_radio=10, n_ini_radio=3)
        scan = EDFTomoScan(scan=self.folder)
        self.assertEqual(len(scan.projections), 3)
        mock.add_radio()
        self.assertEqual(len(scan.projections), 3)
        scan.update()
        self.assertEqual(len(scan.projections), 4)

        index_0 = list(scan.projections.keys())[0]
        self.assertTrue(isinstance(scan.projections[index_0], silx.io.url.DataUrl))

    def testProjectionWithExtraRadio(self):
        mock = MockEDF(
            scan_path=self.folder,
            n_radio=11,
            n_ini_radio=11,
            n_extra_radio=2,
            scan_range=180,
        )
        mock.end_acquisition()
        scan = EDFTomoScan(scan=self.folder)
        self.assertEqual(len(scan.projections), 11)
        self.assertEqual(len(scan.alignment_projections), 2)
        proj_angle_dict = scan.get_proj_angle_url()
        self.assertEqual(len(proj_angle_dict), 11 + 2)
        self.assertTrue(90 in proj_angle_dict)
        self.assertTrue(180 in proj_angle_dict)
        self.assertTrue("90(1)" in proj_angle_dict)
        self.assertTrue("0(1)" in proj_angle_dict)
        self.assertTrue(360 not in proj_angle_dict)


class TestFlatFieldCorrection(unittest.TestCase):
    """Test the flat field correction"""

    def setUp(self) -> None:
        self.folder = tempfile.mkdtemp()
        mock = MockEDF(
            scan_path=self.folder, n_radio=30, n_ini_radio=30, n_extra_radio=0, dim=20
        )
        mock.end_acquisition()
        self.scan = EDFTomoScan(scan=self.folder)

    def tearDown(self) -> None:
        shutil.rmtree(self.folder)

    def testFlatAndDarksSet(self):
        """Test no error is log if `normed` dark and flat are provided"""
        self.scan.set_reduced_flats(
            {
                1: numpy.random.random(20 * 20).reshape((20, 20)),
                21: numpy.random.random(20 * 20).reshape((20, 20)),
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
        raw_data = get_data(projs[10])
        self.assertFalse(numpy.array_equal(raw_data, normed_proj[10]))

    def testNoFlatOrDarkSet(self):
        """Test an error is log if `normed` dark and flat aren't provided"""
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
        raw_data = get_data(projs[10])
        numpy.testing.assert_array_equal(raw_data, normed_proj[10])


class TestGetSinogram(unittest.TestCase):
    """Test the get_sinogram function"""

    def setUp(self) -> None:
        self.folder = tempfile.mkdtemp()
        mock = MockEDF(
            scan_path=self.folder, n_radio=30, n_ini_radio=30, n_extra_radio=0, dim=20
        )
        mock.end_acquisition()
        self.scan = EDFTomoScan(scan=self.folder)
        self.scan.set_reduced_flats(
            {
                21: numpy.random.random(20 * 20).reshape((20, 20)),
                1520: numpy.random.random(20 * 20).reshape((20, 20)),
            }
        )
        self.scan.set_reduced_darks({0: numpy.random.random(20 * 20).reshape((20, 20))})

    def tearDown(self) -> None:
        shutil.rmtree(self.folder)

    def testGetSinogram1(self):
        sinogram = self.scan.get_sinogram(line=12, subsampling=1)
        self.assertEqual(sinogram.shape, (30, 20))

    def testGetSinogram2(self):
        """Test if subsampling is negative"""
        with self.assertRaises(ValueError):
            self.scan.get_sinogram(line=0, subsampling=-1)

    def testGetSinogram3(self):
        sinogram = self.scan.get_sinogram(line=0, subsampling=3)
        self.assertEqual(sinogram.shape, (10, 20))

    def testGetSinogram4(self):
        """Test if line is not in the projection"""
        with self.assertRaises(ValueError):
            self.scan.get_sinogram(line=-1, subsampling=1)

    def testGetSinogram5(self):
        """Test if line is not in the projection"""
        with self.assertRaises(ValueError):
            self.scan.get_sinogram(line=35, subsampling=1)


class TestScanValidatorFindFiles(unittest.TestCase):
    """Function testing the getReconstructionsPaths function is correctly
    functioning"""

    DIM_MOCK_SCAN = 10

    N_RADIO = 20
    N_RECONS = 10
    N_PAG_RECONS = 5

    def setUp(self):
        # create scan folder
        self.path = tempfile.mkdtemp()
        MockEDF.mockScan(
            scanID=self.path,
            nRadio=self.N_RADIO,
            nRecons=self.N_RECONS,
            nPagRecons=self.N_PAG_RECONS,
            dim=self.DIM_MOCK_SCAN,
        )
        basename = os.path.basename(self.path)

        # add some random files
        for _file in ("45gfdgfg1.edf", "465slicetest1.edf", "slice_ab.edf"):
            with open(os.path.join(self.path, basename + _file), "w+") as ofile:
                ofile.write("test")

    def tearDown(self):
        if os.path.isdir(self.path):
            shutil.rmtree(self.path)


class TestRadioPath(unittest.TestCase):
    """Test static method getRadioPaths for EDFTomoScan"""

    def test(self):
        files = [
            "essai1_0008.edf",
            "essai1_0019.edf",
            "essai1_0030.edf",
            "essai1_0041.edf",
            "essai1_0052.edf",
            "essai1_0063.edf",
            "essai1_0074.edf",
            "essai1_0085.edf",
            "essai1_0096.edf",
            "essai1_.par",
            "refHST0100.edf",
            "darkend0000.edf",
            "essai1_0009.edf",
            "essai1_0020.edf",
            "essai1_0031.edf",
            "essai1_0042.edf",
            "essai1_0053.edf",
            "essai1_0064.edf",
            "essai1_0075.edf",
            "essai1_0086.edf",
            "essai1_0097.edf",
            "essai1_.rec",
            "essai1_0000.edf",
            "essai1_0010.edf",
            "essai1_0021.edf",
            "essai1_0032.edf",
            "essai1_0043.edf",
            "essai1_0054.edf",
            "essai1_0065.edf",
            "essai1_0076.edf",
            "essai1_0087.edf",
            "essai1_0098.edf",
            "essai1_slice_1023.edf",
            "essai1_0001.edf",
            "essai1_0011.edf",
            "essai1_0022.edf",
            "essai1_0033.edf",
            "essai1_0044.edf",
            "essai1_0055.edf",
            "essai1_0066.edf",
            "essai1_0077.edf",
            "essai1_0088.edf",
            "essai1_0099.edf",
            "essai1_slice.info",
            "essai1_0001.par",
            "essai1_0012.edf",
            "essai1_0023.edf",
            "essai1_0034.edf",
            "essai1_0045.edf",
            "essai1_0056.edf",
            "essai1_0067.edf",
            "essai1_0078.edf",
            "essai1_0089.edf",
            "essai1_0100.edf",
            "essai1_slice.par",
            "essai1_0002.edf",
            "essai1_0013.edf",
            "essai1_0024.edf",
            "essai1_0035.edf",
            "essai1_0046.edf",
            "essai1_0057.edf",
            "essai1_0068.edf",
            "essai1_0079.edf",
            "essai1_0090.edf",
            "essai1_0101.edf",
            "essai1_slice.xml",
            "essai1_0003.edf",
            "essai1_0014.edf",
            "essai1_0025.edf",
            "essai1_0036.edf",
            "essai1_0047.edf",
            "essai1_0058.edf",
            "essai1_0069.edf",
            "essai1_0080.edf",
            "essai1_0091.edf",
            "essai1_0102.edf",
            "essai1_.xml",
            "essai1_0004.edf",
            "essai1_0015.edf",
            "essai1_0026.edf",
            "essai1_0037.edf",
            "essai1_0048.edf",
            "essai1_0059.edf",
            "essai1_0070.edf",
            "essai1_0081.edf",
            "essai1_0092.edf",
            "essai1_0103.edf",
            "histogram_essai1_slice",
            "essai1_0005.edf",
            "essai1_0016.edf",
            "essai1_0027.edf",
            "essai1_0038.edf",
            "essai1_0049.edf",
            "essai1_0060.edf",
            "essai1_0071.edf",
            "essai1_0082.edf",
            "essai1_0093.edf",
            "essai1_0104.edf",
            "machinefile",
            "essai1_0006.edf",
            "essai1_0017.edf",
            "essai1_0028.edf",
            "essai1_0039.edf",
            "essai1_0050.edf",
            "essai1_0061.edf",
            "essai1_0072.edf",
            "essai1_0083.edf",
            "essai1_0094.edf",
            "essai1_.cfg",
            "pyhst_out.txt",
            "essai1_0007.edf",
            "essai1_0018.edf",
            "essai1_0029.edf",
            "essai1_0040.edf",
            "essai1_0051.edf",
            "essai1_0062.edf",
            "essai1_0073.edf",
            "essai1_0084.edf",
            "essai1_0095.edf",
        ]

        nbRadio = 0
        for f in files:
            nbRadio += EDFTomoScan.is_a_proj_path(f, "essai1_")
        self.assertTrue(nbRadio == 105)


class TestIgnoredProjections(unittest.TestCase):
    """Test the ignore_projections parameter"""

    def setUp(self) -> None:
        self.folder = tempfile.mkdtemp()
        self.mock = MockEDF(self.folder, 18, n_ini_radio=18, dim=10, scan_range=180)
        self.all_angles = numpy.linspace(0, 180, self.mock.n_radio, False)
        self.mock.end_acquisition()

    def tearDown(self) -> None:
        shutil.rmtree(self.folder)

    def testIgnoreProjectionsIndices(self):
        ignored_projs_indices = [5, 6, 7]
        scan = EDFTomoScan(scan=self.folder, ignore_projections=ignored_projs_indices)
        for idx in ignored_projs_indices:
            self.assertFalse(
                idx in scan.projections,
                "Projection index %d is supposed to be ignored" % idx,
            )

    def testIgnoreProjectionAngles(self):
        ignored_projs_angles = [40.0, 50.0, 60.0, 83.3333, 156.5]
        # In this case idx k <-> angle 10*k
        corresponding_projs_indices = [4, 5, 6, 8, 16]
        scan = EDFTomoScan(
            scan=self.folder,
            ignore_projections={"kind": "angles", "values": ignored_projs_angles},
        )
        for idx in scan.projections.keys():
            assert_func = (
                self.assertFalse
                if idx in corresponding_projs_indices
                else self.assertTrue
            )
            assert_func(idx in scan.projections, "Projection index %d" % idx)

    def testIgnoreProjectionAngularRange(self):
        ignored_projs_angular_range = [95.5, 120]
        # In this case idx k <-> angle 10*k
        corresponding_projs_indices = [10, 11, 12]
        scan = EDFTomoScan(
            scan=self.folder,
            ignore_projections={"kind": "range", "values": ignored_projs_angular_range},
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


def test_EDFTomoScan_API():
    """some simple test of the EDFTomoScan API"""
    with tempfile.TemporaryDirectory() as folder:
        MockEDF.mockScan(
            scanID=folder,
            n_extra_radio=2,
            scan_range=180,
            dim=36,
        )

        scan = EDFTomoScan(folder)
        scan.clear_cache()
        for fct in (
            "get_flat_expected_location",
            "get_dark_expected_location",
            "get_projection_expected_location",
            "get_energy_expected_location",
            "get_sample_detector_distance_expected_location",
            "get_pixel_size_expected_location",
        ):
            assert isinstance(getattr(scan, fct)(), str)
        # check str conversion
        str(scan)


def test_get_relative_file(tmpdir):
    """Test that get_relative_file function is working correctly for EDFScan"""
    folder_path = os.path.join(tmpdir, "myscan")
    MockEDF.mockScan(
        scanID=folder_path,
        n_extra_radio=2,
        scan_range=180,
        dim=36,
    )

    scan = EDFTomoScan(folder_path)
    expected_f1 = os.path.join(folder_path, "myscan_tomwer_processes.h5")
    assert (
        scan.get_relative_file("tomwer_processes.h5", with_dataset_prefix=True)
        == expected_f1
    )

    expected_f2 = os.path.join(folder_path, "tomwer_processes.h5")
    assert (
        scan.get_relative_file("tomwer_processes.h5", with_dataset_prefix=False)
        == expected_f2
    )


def test_save_and_load_dark(tmp_path):
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    MockEDF.mockScan(
        scanID=str(test_dir),
        n_extra_radio=2,
        scan_range=180,
        dim=36,
    )

    scan = EDFTomoScan(test_dir)
    assert scan.load_reduced_darks() == {}
    assert scan.load_reduced_flats() == {}
    dark_frame = numpy.ones((100, 100))
    scan.save_reduced_darks({0: dark_frame})
    loaded_darks = scan.load_reduced_darks()
    assert 0 in loaded_darks
    numpy.testing.assert_array_equal(loaded_darks[0], dark_frame)
    assert scan.load_reduced_flats() == {}


def test_save_and_load_flats(tmp_path):
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    MockEDF.mockScan(
        scanID=str(test_dir),
        n_extra_radio=2,
        scan_range=180,
        dim=36,
        nRecons=0,
    )

    scan = EDFTomoScan(test_dir)
    assert scan.load_reduced_darks() == {}
    flat_frame_1 = numpy.ones((100, 100))
    flat_frame_1000 = numpy.zeros((100, 100))
    assert len(glob(os.path.join(test_dir, "*.hdf5"))) == 0

    scan.save_reduced_flats(
        {
            1: flat_frame_1,
            1000: flat_frame_1000,
        }
    )
    # check hdf5 as also been created
    assert tuple(glob(os.path.join(test_dir, "*.hdf5"))) == (
        os.path.join(test_dir, "test_dir_flats.hdf5"),
    )

    loaded_flats = scan.load_reduced_flats()
    assert 1 in loaded_flats
    assert 1000 in loaded_flats
    numpy.testing.assert_array_equal(loaded_flats[1], flat_frame_1)
    numpy.testing.assert_array_equal(loaded_flats[1000], flat_frame_1000)
    assert scan.load_reduced_darks() == {}


def test_save_dark_flat_reduced_several_urls(tmp_path):
    """test saving and loading dark and flat providing several urls"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    MockEDF.mockScan(
        scanID=str(test_dir),
        n_extra_radio=2,
        scan_range=180,
        dim=36,
    )
    scan = EDFTomoScan(test_dir)
    url_flats_edf = EDFTomoScan.REDUCED_FLATS_DATAURLS[0]
    url_flats_processes = DataUrl(
        file_path=scan.get_relative_file(
            file_name="my_processes.h5", with_dataset_prefix=False
        ),
        data_path="/{entry}/process_1/results/flats/{index}",
        scheme="hdf5",
    )
    url_darks_edf = EDFTomoScan.REDUCED_DARKS_DATAURLS[0]
    url_darks_processes = DataUrl(
        file_path=scan.get_relative_file(
            file_name="my_processes.h5", with_dataset_prefix=False
        ),
        data_path="/{entry}/process_1/results/darks/{index}",
        scheme="silx",
    )

    scan = EDFTomoScan(test_dir)
    assert scan.load_reduced_darks(return_info=False) == {}
    flat_frame_1 = numpy.ones((100, 100))
    flat_frame_1000 = numpy.ones((100, 100)) * 1.2
    dark_frame = numpy.zeros((100, 100))
    scan.save_reduced_flats(
        flats={
            1: flat_frame_1,
            1000: flat_frame_1000,
        },
        output_urls=(
            url_flats_edf,
            url_flats_processes,
        ),
    )
    scan.save_reduced_darks(
        darks={
            0: dark_frame,
        },
        output_urls=(
            url_darks_edf,
            url_darks_processes,
        ),
    )
    assert len(scan.load_reduced_flats(return_info=False)) == 2
    assert len(scan.load_reduced_darks(return_info=False)) == 1

    _, load_infos_darks = scan.load_reduced_darks(return_info=True)
    assert load_infos_darks == ReducedFramesInfos()  # no data saved
    _, load_infos_flats = scan.load_reduced_flats(return_info=True)
    assert load_infos_flats == ReducedFramesInfos()  # no data saved

    processes_file = os.path.join(test_dir, "my_processes.h5")
    assert os.path.exists(processes_file)
    with h5py.File(processes_file) as h5s:
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

    # check flats when provided as DataUrl as HDF5File
    loaded_reduced_darks_hdf5 = scan.load_reduced_darks(
        (url_darks_processes,), return_as_url=True
    )
    assert isinstance(loaded_reduced_darks_hdf5[0], DataUrl)
    assert loaded_reduced_darks_hdf5[0].file_path() == processes_file
    assert (
        loaded_reduced_darks_hdf5[0].data_path() == "/entry/process_1/results/darks/0"
    )
    assert loaded_reduced_darks_hdf5[0].scheme() == "silx"
    loaded_reduced_flats = scan.load_reduced_flats(
        (url_flats_processes,), return_as_url=True
    )
    assert len(loaded_reduced_flats) == 2
    assert len(loaded_reduced_darks_hdf5) == 1

    # check flats when provided as DataUrl as EDFFile
    loaded_reduced_darks_edf = scan.load_reduced_darks(return_as_url=True)
    assert isinstance(loaded_reduced_darks_edf[0], DataUrl)
    assert loaded_reduced_darks_edf[0].file_path() == os.path.join(
        scan.path, "test_dir_darks.hdf5"
    )
    assert loaded_reduced_darks_edf[0].data_path() == "entry/darks/0"
    assert loaded_reduced_darks_edf[0].scheme() == "silx"

    # test metadata
    flats_infos = ReducedFramesInfos()
    flats_infos.count_time = [1.0, 1.0]
    flats_infos.machine_current = [13.0, 13.0]

    scan.save_reduced_flats(
        flats={
            1: flat_frame_1,
            1000: flat_frame_1000,
        },
        flats_infos=flats_infos,
        overwrite=True,
    )
    darks_infos = ReducedFramesInfos()
    darks_infos.count_time = [
        2.0,
    ]
    darks_infos.machine_current = [13.1]
    scan.save_reduced_darks(
        darks={
            0: dark_frame,
        },
        darks_infos=darks_infos,
        overwrite=True,
    )
    _, load_infos_darks = scan.load_reduced_darks(return_info=True)
    assert load_infos_darks == darks_infos
    _, load_infos_flats = scan.load_reduced_flats(return_info=True)
    assert load_infos_flats == flats_infos


folder_test_input = (
    "myacquisition",
    "my_acquisition",
    "my_acquisition_",
    "_my_acquisition_",
)
folder_test_output = ("new_dir", "new_dir_", "newdir", "_new_dir")


@pytest.mark.parametrize("original_dir_name", folder_test_input)
@pytest.mark.parametrize("final_dir_name", folder_test_output)
def test_EDFTomoScan_provide_file_prefix(tmp_path, original_dir_name, final_dir_name):
    """Test EDFTomoScan works if the file_prefix is provided and if folder name is different that the file_prefix"""
    original_dir = tmp_path / original_dir_name
    original_dir.mkdir()
    new_dir = tmp_path / final_dir_name

    n_projection = 6

    MockEDF.mockScan(
        scanID=str(original_dir),
        n_extra_radio=2,
        scan_range=180,
        nRadio=n_projection,
        dim=36,
    )
    shutil.copytree(original_dir, new_dir)
    scan = EDFTomoScan(new_dir, dataset_basename=original_dir_name)
    assert len(scan.projections) == n_projection, "not all projection were found"


def test_EDFTomoScan_provide_scan_info(tmp_path):
    """Test EDFTomoScan works as expected if scan_info is provided and insure .info information is overwrite"""
    original_dir = tmp_path / "my_acquisition"
    original_dir.mkdir()

    n_projection = 6

    MockEDF.mockScan(
        scanID=str(original_dir),
        n_extra_radio=2,
        scan_range=180,
        nRadio=n_projection,
        dim=36,
    )
    scan = EDFTomoScan(
        str(original_dir),
    )
    assert scan.scan_range == 180

    scan = EDFTomoScan(str(original_dir), scan_info={"ScanRange": 360})
    assert scan.scan_range == 360
