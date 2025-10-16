# coding: utf-8

import pytest

from tomoscan.esrf.scan.mock import MockNXtomo
from tomoscan.framereducer.framereducerbase import FrameReducerBase


def test_FrameReducerBase_instanciation(tmp_path):
    scan = MockNXtomo(tmp_path, n_proj=2).scan
    reducer = FrameReducerBase(scan=scan, reduced_method="mean", target="darks")
    with pytest.raises(NotImplementedError):
        reducer.run()
