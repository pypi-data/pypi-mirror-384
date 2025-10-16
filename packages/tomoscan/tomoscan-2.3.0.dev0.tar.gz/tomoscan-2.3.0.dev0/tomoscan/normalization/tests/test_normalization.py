# coding: utf-8
from __future__ import annotations

import os
import tempfile

import h5py
import numpy
import pytest
from silx.io.url import DataUrl

import tomoscan.esrf.scan.nxtomoscan
import tomoscan.normalization.normalization
from tomoscan.normalization.normalization import _DatasetInfos
from tomoscan.normalization.datasetscope import DatasetScope
from tomoscan.nexus.paths.nxtomo import nx_tomo_path_latest
from tomoscan.tests.utils import NXtomoMockContext

try:
    import scipy.interpolate  # noqa F401
except ImportError:
    has_scipy = False
else:
    has_scipy = True


@pytest.mark.parametrize("method", ["subtraction", "division"])
def test_normalization_scalar_normalization(method):
    """test scalar normalization"""
    with NXtomoMockContext(
        scan_path=os.path.join(tempfile.mkdtemp(), "scan_test"),
        n_proj=10,
        n_ini_proj=10,
    ) as scan:
        with pytest.raises(KeyError):
            scan.get_sinogram(line=2, norm_method=method)

        scan.get_sinogram(line=2, norm_method=method, value=12.2)


def test_normalize_chebyshev_2D():
    """Test checbychev 2D normalization"""
    with NXtomoMockContext(
        scan_path=os.path.join(tempfile.mkdtemp(), "scan_test"),
        n_proj=10,
        n_ini_proj=10,
    ) as scan:
        sinogram = scan.get_sinogram(line=2)
        tomoscan.normalization.normalize_chebyshev_2D(sinogram)
        sinogram_2 = scan.get_sinogram(line=2, norm_method="chebyshev")
        assert numpy.array_equal(sinogram, sinogram_2)


@pytest.mark.skipif(condition=not has_scipy, reason="scipy missing")
def test_normalize_lsqr_spline_2D():
    """test lsqr_spline_2D normalization"""
    with NXtomoMockContext(
        scan_path=os.path.join(tempfile.mkdtemp(), "scan_test"),
        n_proj=10,
        n_ini_proj=10,
    ) as scan:
        sinogram = scan.get_sinogram(line=2)
        tomoscan.normalization.normalize_lsqr_spline_2D(sinogram)
        sinogram_2 = scan.get_sinogram(line=2, norm_method="lsqr spline")
        assert numpy.array_equal(sinogram, sinogram_2)


def test_normalize_dataset():
    """Test extra information that can be provided relative to a dataset"""
    with NXtomoMockContext(
        scan_path=os.path.join(tempfile.mkdtemp(), "scan_test"),
        n_proj=10,
        n_ini_proj=10,
        dim=100,
        intensity_monitor=True,
    ) as scan:
        datasetinfo = _DatasetInfos()
        datasetinfo.file_path = scan.master_file
        datasetinfo.data_path = "/".join(
            [scan.entry, nx_tomo_path_latest.INTENSITY_MONITOR_PATH]
        )
        assert isinstance(datasetinfo.data_path, str)
        assert isinstance(datasetinfo.file_path, str)
        datasetinfo.scope = DatasetScope.GLOBAL
        assert isinstance(datasetinfo.scope, DatasetScope)
        scan.intensity_normalization.set_extra_infos(datasetinfo)


def test_normalize_roi():
    """Test extra information that can be provided relative to a roi"""
    with NXtomoMockContext(
        scan_path=os.path.join(tempfile.mkdtemp(), "scan_test"),
        n_proj=10,
        n_ini_proj=10,
        dim=100,
        intensity_monitor=True,
    ) as scan:
        roi_info = tomoscan.normalization.normalization._ROIInfo()
        scan.intensity_normalization.set_extra_infos(roi_info)
        scan.intensity_normalization.method = None
        scan.intensity_normalization.method = "lsqr spline"
        assert isinstance(
            scan.intensity_normalization.method, tomoscan.normalization.Method
        )
        str(scan.intensity_normalization)


@pytest.mark.parametrize("norm_method", ("subtraction", "division"))
@pytest.mark.parametrize("as_url", (True, False))
@pytest.mark.parametrize(
    "values",
    (
        0.5,
        numpy.arange(1, 11),
        numpy.arange(1, 101).reshape(10, 10),
        numpy.arange(1, 1001).reshape(10, 10, 10),
    ),
)
def test_get_sinogram(tmp_path, norm_method, as_url, values: float | numpy.ndarray):
    test_dir = tmp_path / "test1"
    test_dir.mkdir()
    params = {}
    if as_url:
        file_path = str(test_dir / "tmp_file.hdf5")
        with h5py.File(file_path, mode="w") as root:
            root["data"] = values
        params["dataset_url"] = DataUrl(
            file_path=file_path, data_path="data", scheme="silx"
        )
    else:
        params["value"] = values

    with NXtomoMockContext(
        scan_path=os.path.join(test_dir, "scan_test"),
        n_proj=10,
        n_ini_proj=10,
        dim=10,
    ) as scan:
        raw_sinogram = scan.get_sinogram(line=2)
        norm_sinogram = scan.get_sinogram(line=2, norm_method=norm_method, **params)
        assert isinstance(raw_sinogram, numpy.ndarray)
        assert isinstance(norm_sinogram, numpy.ndarray)
        if numpy.isscalar(values):
            if norm_method == "subtraction":
                numpy.testing.assert_almost_equal(norm_sinogram, raw_sinogram - values)
            elif norm_method == "division":
                numpy.testing.assert_almost_equal(norm_sinogram, raw_sinogram / values)
            else:
                raise ValueError
        elif values.ndim == 1:
            expected_sinogram = raw_sinogram.copy()
            for i_proj, proj_value in enumerate(values):
                if norm_method == "subtraction":
                    expected_sinogram[i_proj] = raw_sinogram[i_proj] - proj_value
                elif norm_method == "division":
                    expected_sinogram[i_proj] = raw_sinogram[i_proj] / proj_value
                else:
                    raise ValueError(norm_method)
            numpy.testing.assert_almost_equal(norm_sinogram, expected_sinogram)
        elif values.ndim in (2, 3):
            expected_sinogram = raw_sinogram.copy()
            for i_proj, proj_value in enumerate(values):
                if norm_method == "subtraction":
                    expected_sinogram[i_proj] = raw_sinogram[i_proj] - proj_value[2]
                elif norm_method == "division":
                    expected_sinogram[i_proj] = raw_sinogram[i_proj] / proj_value[2]
                else:
                    raise ValueError(norm_method)
            numpy.testing.assert_almost_equal(norm_sinogram, expected_sinogram)
