from __future__ import annotations

import logging
import numpy
from .datasetscope import DatasetScope
from .method import Method

_logger = logging.getLogger(__name__)


class _DatasetInfos:
    def __init__(self):
        self._scope = DatasetScope.GLOBAL
        self._file_path = None
        self._data_path = None

    @property
    def scope(self) -> DatasetScope:
        return self._scope

    @scope.setter
    def scope(self, scope: str | DatasetScope):
        self._scope = DatasetScope(scope)

    @property
    def file_path(self):
        return self._file_path

    @file_path.setter
    def file_path(self, file_path):
        self._file_path = file_path

    @property
    def data_path(self):
        return self._data_path

    @data_path.setter
    def data_path(self, data_path: str):
        self._data_path = data_path


class _ROIInfo:
    def __init__(self, x_min=None, x_max=None, y_min=None, y_max=None):
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max


class IntensityNormalization:
    """Information regarding the intensity normalization to be done"""

    def __init__(self):
        self._method = Method.NONE
        self._extra_info = {}

    @property
    def method(self):
        return self._method

    @method.setter
    def method(self, method: str | Method | None):
        if method is None:
            method = Method.NONE
        self._method = Method(method)

    def set_extra_infos(self, info: dict | _DatasetInfos | _ROIInfo):
        if info is None:
            self._extra_info = None
        elif not isinstance(info, (_DatasetInfos, _ROIInfo, dict)):
            raise TypeError(
                "info is expected to be an instance of _DatasetInfos or _ROIInfo"
            )
        else:
            self._extra_info = info

    def get_extra_infos(self) -> dict | _DatasetInfos | _ROIInfo:
        return self._extra_info

    def to_dict(self) -> dict:
        res = {
            "method": self.method.value,
        }
        if self._extra_info not in (None, {}):
            res["extra_infos"] = self.get_extra_infos()
        return res

    def load_from_dict(self, dict_):
        if "method" in dict_:
            self.method = dict_["method"]
        if "extra_infos" in dict_:
            self.set_extra_infos(dict_["extra_infos"])
        return self

    @staticmethod
    def from_dict(dict_):
        res = IntensityNormalization()
        res.load_from_dict(dict_)
        return res

    def __str__(self):
        return f"method: {self.method}, extra-infos: {self.get_extra_infos()}"


def normalize_chebyshev_2D(sino):
    Nr, Nc = sino.shape
    J = numpy.arange(Nc)
    x = 2.0 * (J + 0.5 - Nc / 2) / Nc
    sum0 = Nc
    f2 = 3.0 * x * x - 1.0
    sum1 = (x**2).sum()
    sum2 = (f2**2).sum()
    for i in range(Nr):
        ff0 = sino[i, :].sum()
        ff1 = (x * sino[i, :]).sum()
        ff2 = (f2 * sino[i, :]).sum()
        sino[i, :] = sino[i, :] - (ff0 / sum0 + ff1 * x / sum1 + ff2 * f2 / sum2)
    return sino


def normalize_lsqr_spline_2D(sino):
    try:
        from scipy.interpolate import splev, splrep
    except ImportError:
        _logger.error("You should install scipy to do the lsqr spline normalization")
        return None

    Nr, Nc = sino.shape
    # correction = numpy.zeros_like(sino)
    for i in range(Nr):
        line = sino[i, :]
        spline = splrep(range(len(line)), sino[i, :], k=1)
        correct = splev(range(len(line)), spline)
        sino[i, :] = line - correct
    return sino
