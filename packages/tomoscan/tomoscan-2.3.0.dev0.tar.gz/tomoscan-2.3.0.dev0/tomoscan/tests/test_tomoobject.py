# coding: utf-8

"""test of the tomoscan.tomoobject module"""


import pytest

from tomoscan.tomoobject import TomoObject


def test_tomoobject():
    obj = TomoObject()
    with pytest.raises(NotImplementedError):
        obj.from_identifier("test")

    with pytest.raises(NotImplementedError):
        obj.get_identifier()
