import pytest
from silx.io.url import DataUrl

from tomoscan.utils.hdf5 import DatasetReader


def test_errors_DatasetReader():
    with pytest.raises(TypeError):
        with DatasetReader("toto"):
            pass

    with pytest.raises(ValueError):
        with DatasetReader(DataUrl()):
            pass

    with pytest.raises(ValueError):
        with DatasetReader(DataUrl(file_path="test", data_path="dssad", data_slice=2)):
            pass
