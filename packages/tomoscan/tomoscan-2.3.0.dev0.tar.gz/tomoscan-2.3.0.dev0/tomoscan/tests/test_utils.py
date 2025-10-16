# coding: utf-8

import pytest

from tomoscan.utils.geometry import BoundingBox1D, BoundingBox3D, _BoundingBox


def test_bounding_box_base():
    bb = _BoundingBox(0, 1)
    with pytest.raises(NotImplementedError):
        bb.get_overlap(None)


def test_bounding_box_1D():
    """
    check if BoundingBox1D is working properly
    """
    # check overlaping
    bb1 = BoundingBox1D(0.0, 1.0)
    bb2 = BoundingBox1D(0.2, 1.0)
    assert bb1.get_overlap(bb2) == BoundingBox1D(0.2, 1.0)
    assert bb2.get_overlap(bb1) == BoundingBox1D(0.2, 1.0)

    bb1 = BoundingBox1D(0.0, 1.0)
    bb2 = BoundingBox1D(0.2, 0.8)
    assert bb1.get_overlap(bb2) == BoundingBox1D(0.2, 0.8)
    assert bb2.get_overlap(bb1) == BoundingBox1D(0.2, 0.8)

    bb1 = BoundingBox1D(0.0, 1.0)
    bb2 = BoundingBox1D(1.0, 1.2)
    assert bb2.get_overlap(bb1) == BoundingBox1D(1.0, 1.0)

    # check outside
    bb1 = BoundingBox1D(0.0, 1.0)
    bb2 = BoundingBox1D(2.0, 2.2)

    assert bb2.get_overlap(bb1) is None
    assert bb1.get_overlap(bb2) is None

    # check on fully including in the other
    bb1 = BoundingBox1D(0.0, 1.0)
    bb2 = BoundingBox1D(0.1, 0.3)
    assert bb2.get_overlap(bb1) == BoundingBox1D(0.1, 0.3)
    assert bb1.get_overlap(bb2) == BoundingBox1D(0.1, 0.3)

    with pytest.raises(TypeError):
        bb1.get_overlap(None)


def test_bounding_box_3D():
    """
    check if BoundingBox3D is working properly
    """
    # check overlaping
    bb1 = BoundingBox3D((0.0, -0.1, 0.0), [1.0, 0.8, 0.9])
    bb2 = BoundingBox3D([0.2, 0.0, 0.1], (1.0, 2.0, 3.0))
    assert bb1.get_overlap(bb2) == BoundingBox3D((0.2, 0.0, 0.1), (1.0, 0.8, 0.9))
    assert bb2.get_overlap(bb1) == BoundingBox3D((0.2, 0.0, 0.1), (1.0, 0.8, 0.9))

    # check outside
    bb1 = BoundingBox3D((0.0, -0.1, 0.0), [1.0, 0.8, 0.9])
    bb2 = BoundingBox3D([0.2, 0.0, -2.1], (1.0, 2.0, -1.0))

    assert bb2.get_overlap(bb1) is None
    assert bb1.get_overlap(bb2) is None

    # check on fully including in the other
    bb1 = BoundingBox3D((0.0, 0.1, 0.2), (1.0, 1.1, 1.2))
    bb2 = BoundingBox3D((-2.0, -3.0, -4.0), (2.0, 2.0, 2.0))
    assert bb2.get_overlap(bb1) == BoundingBox3D((0.0, 0.1, 0.2), (1.0, 1.1, 1.2))
    assert bb1.get_overlap(bb2) == BoundingBox3D((0.0, 0.1, 0.2), (1.0, 1.1, 1.2))

    with pytest.raises(TypeError):
        bb1.get_overlap(None)
