"""
Test the integration of NXtomo 3.0 (and moving to McStas).
Especially that having an old Nxtomo or a recent one won't affect the reading.
"""

from __future__ import annotations

import os
import shutil
import pytest
import numpy

from tomoscan.tests.datasets import GitlabDataset
from tomoscan.esrf.scan.nxtomoscan import NXtomoScan
from tomoscan._CoordinateSystem import CoordinateSystem
from nxtomo.utils.transformation import (
    DetXFlipTransformation,
    DetYFlipTransformation,
    DetZFlipTransformation,
)
from nxtomo.nxobject.nxtransformations import NXtransformations


@pytest.fixture
def nxtomo_beforce_McStas(tmp_path):
    """
    Return a dataset ('Atomium_S2_holo1_HT_010nm_500proj_0003.h5') converted **before** moving from McStas (nxtomomill <2.0 and nxtomo < 3.0)
    """
    src_file = GitlabDataset.get_dataset(
        "h5_datasets/coordinate_system/before_McStas_0000.nx"
    )
    dst_file = os.path.join(tmp_path, "before_McStas_0000.nx")
    shutil.copyfile(src_file, dst_file)
    return dst_file


@pytest.fixture
def nxtomo_after_McStas(tmp_path):
    """
    Return a dataset ('Atomium_S2_holo1_HT_010nm_500proj_0003.h5') converted **after** moving from McStas (nxtomomill == 2.0 and nxtomo == 3.0)
    """
    src_file = GitlabDataset.get_dataset(
        "h5_datasets/coordinate_system/after_McStas_0000.nx"
    )
    dst_file = os.path.join(tmp_path, "after_McStas_0000.nx")
    shutil.copyfile(src_file, dst_file)
    return dst_file


@pytest.mark.parametrize(
    "lr_flip, ud_flip", ((False, False), (True, False), (False, True))
)
def test_transition_to_McStas(
    nxtomo_beforce_McStas, nxtomo_after_McStas, lr_flip, ud_flip
):
    """
    Check that tomoscan API returns the same values before and after moving to McStas.
    This transition affects the NXtomo and NXtomomill but should affect tomoscan.

    Note on flip: the original dataset had no flip. We mock some in order to have a larger case coverage
    """
    # overwrite flips
    mc_stas_transformation = NXtransformations()
    mc_stas_transformation.add_transformation(DetYFlipTransformation(flip=lr_flip))
    mc_stas_transformation.add_transformation(DetXFlipTransformation(flip=ud_flip))
    mc_stas_transformation.save(
        file_path=nxtomo_after_McStas,
        data_path="/entry0000/instrument/detector/transformations",
        overwrite=True,
    )

    esrf_transformations = NXtransformations()
    esrf_transformations.add_transformation(DetZFlipTransformation(flip=lr_flip))
    esrf_transformations.add_transformation(DetYFlipTransformation(flip=ud_flip))
    esrf_transformations.save(
        file_path=nxtomo_beforce_McStas,
        data_path="/entry0000/instrument/detector/transformations",
        overwrite=True,
    )

    # create 'NXtomoScan' instances and test one against the other
    nxtomo_esrf_coord = NXtomoScan(nxtomo_beforce_McStas)
    nxtomo_mc_stas_coord = NXtomoScan(nxtomo_after_McStas)

    # check coordinate system
    assert (
        nxtomo_esrf_coord._get_coordinate_system(default=None) is CoordinateSystem.ESRF
    )
    assert (
        nxtomo_mc_stas_coord._get_coordinate_system(default=None)
        is CoordinateSystem.McStas
    )
    # check rotation angle
    # warning: this dataset has rotation defined 'counter clockwise'. So the value read by tomoscan should be untouched.
    # In nxtomomill < 2.0 this field was not interpreted and the use case of a counter-clockwise rotation was not considered but we should have invert them.

    numpy.testing.assert_almost_equal(
        nxtomo_mc_stas_coord.rotation_angle,
        numpy.array(nxtomo_esrf_coord.rotation_angle),
    )
    # check translations
    numpy.testing.assert_almost_equal(
        nxtomo_mc_stas_coord.x_translation, nxtomo_esrf_coord.x_translation
    )
    numpy.testing.assert_almost_equal(
        nxtomo_mc_stas_coord.y_translation, nxtomo_esrf_coord.y_translation
    )
    numpy.testing.assert_almost_equal(
        nxtomo_mc_stas_coord.z_translation, nxtomo_esrf_coord.z_translation
    )

    # check detector flips
    numpy.testing.assert_almost_equal(
        nxtomo_mc_stas_coord.detector_is_lr_flip, nxtomo_esrf_coord.detector_is_lr_flip
    )
    numpy.testing.assert_almost_equal(
        nxtomo_mc_stas_coord.detector_is_ud_flip, nxtomo_esrf_coord.detector_is_ud_flip
    )
    # check 'x_rotation_axis_pixel_position'
    numpy.testing.assert_almost_equal(
        nxtomo_mc_stas_coord.x_rotation_axis_pixel_position,
        nxtomo_esrf_coord.x_rotation_axis_pixel_position,
    )
