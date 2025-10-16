from __future__ import annotations

import numpy
from tomoscan.scanbase import TomoScanBase
from tomoscan.framereducer.method import ReduceMethod
from tomoscan.framereducer.target import REDUCER_TARGET
from tomoscan.utils import is_numpy_scalar_dtype

__all__ = [
    "FrameReducerBase",
]


class FrameReducerBase:
    """
    Base class for frame reduced. We expect one per file format
    """

    def __init__(
        self,
        scan: TomoScanBase,
        reduced_method: ReduceMethod,
        target: REDUCER_TARGET,
        output_dtype: numpy.dtype | None = None,
        overwrite=False,
    ):
        self._reduced_method = ReduceMethod(reduced_method)
        if not isinstance(scan, TomoScanBase):
            raise TypeError(
                f"{scan} is expected to be an instance of TomoscanBase not {type(scan)}"
            )
        self._scan = scan
        self._reducer_target = REDUCER_TARGET(target)
        if not isinstance(overwrite, bool):
            raise TypeError(
                f"overwrite is expected to be a boolean not {type(overwrite)}"
            )
        self._overwrite = overwrite
        if output_dtype is not None and not is_numpy_scalar_dtype(output_dtype):
            raise TypeError(
                f"output_dtype is expected to be None or a numpy.dtype, not {type(output_dtype)}"
            )
        self._output_dtype = output_dtype

    @property
    def reduced_method(self) -> ReduceMethod:
        return self._reduced_method

    @property
    def scan(self) -> TomoScanBase:
        return self._scan

    @property
    def reducer_target(self) -> REDUCER_TARGET:
        return self._reducer_target

    @property
    def overwrite(self):
        return self._overwrite

    @property
    def output_dtype(self) -> numpy.dtype | None:
        return self._output_dtype

    def run(self):
        raise NotImplementedError
