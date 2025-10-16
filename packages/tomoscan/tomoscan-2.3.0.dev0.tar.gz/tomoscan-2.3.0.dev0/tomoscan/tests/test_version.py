# coding: utf-8

import tomoscan.version


def test_version():
    assert isinstance(tomoscan.version.version, str), "version should be a str"
