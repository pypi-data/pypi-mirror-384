# coding: utf-8

from __future__ import annotations

import logging

import numpy
from silx.io.url import DataUrl
from silx.io.utils import get_data

from tomoscan.esrf.scan.utils import get_compacted_dataslices
from tomoscan.framereducer.target import REDUCER_TARGET
from tomoscan.framereducer.framereducerbase import FrameReducerBase
from tomoscan.framereducer.method import ReduceMethod
from tomoscan.scanbase import ReducedFramesInfos

_logger = logging.getLogger(__name__)

__all__ = [
    "HDF5FrameReducer",
]


class HDF5FrameReducer(FrameReducerBase):
    """Frame reducer dedicated to HDF5"""

    def get_series(self, scan, target: REDUCER_TARGET) -> list:
        """
        return a list of dictionary. Dictionaries keys are indexes in the acquisition.
        Values are url

        :param NXtomoScan scan: scan containing frames to reduce
        :param REDUCER_TARGET target: dark of flat to be reduced
        """
        target = REDUCER_TARGET(target)
        if target is REDUCER_TARGET.DARKS:
            raw_what = scan.darks
        elif target is REDUCER_TARGET.FLATS:
            raw_what = scan.flats
        else:
            raise ValueError(f"{target} is not handled")
        if len(raw_what) == 0:
            return []
        else:
            series = []
            indexes = sorted(raw_what.keys())
            # a serie is defined by contiguous indexes
            current_serie = {indexes[0]: raw_what[indexes[0]]}
            current_index = indexes[0]
            for index in indexes[1:]:
                if index == current_index + 1:
                    current_index = index
                else:
                    series.append(current_serie)
                    current_serie = {}
                    current_index = index
                current_serie[index] = raw_what[index]
            if len(current_serie) > 0:
                series.append(current_serie)
            return series

    def get_count_time_serie(self, indexes):
        if self.scan.count_time is None:
            return []
        else:
            return self.scan.count_time[indexes]

    def get_machine_current(self, indexes):
        if self.scan.machine_current is None:
            return []
        else:
            return self.scan.machine_current[indexes]

    def load_data_serie(self, urls) -> dict:
        """load all urls. Trying to reduce load time by calling get_compacted_dataslices"""
        # handle cases where we only have to load one frame for methods is FIRST or LAST
        if self.reduced_method is ReduceMethod.FIRST and len(urls) > 0:
            urls_keys = sorted(urls.keys())
            urls = {
                urls_keys[0]: urls[urls_keys[0]],
            }
        if self.reduced_method is ReduceMethod.LAST and len(urls) > 0:
            urls_keys = sorted(urls.keys())
            urls = {
                urls_keys[-1]: urls[urls_keys[-1]],
            }

        # active loading
        cpt_slices = get_compacted_dataslices(urls)
        url_set = {}
        for url in cpt_slices.values():
            path = url.file_path(), url.data_path(), str(url.data_slice())
            url_set[path] = url

        n_elmts = 0
        for url in url_set.values():
            my_slice = url.data_slice()
            n_elmts += my_slice.stop - my_slice.start

        data = None
        start_z = 0
        for url in url_set.values():
            my_slice = url.data_slice()
            my_slice = slice(my_slice.start, my_slice.stop, 1)
            new_url = DataUrl(
                file_path=url.file_path(),
                data_path=url.data_path(),
                data_slice=my_slice,
                scheme="silx",
            )
            loaded_data = get_data(new_url)

            # init data if dim is not know
            if data is None:
                data = numpy.empty(
                    shape=(
                        n_elmts,
                        self.scan.dim_2 or loaded_data.shape[-2],
                        self.scan.dim_1 or loaded_data.shape[-1],
                    )
                )
            if loaded_data.ndim == 2:
                data[start_z, :, :] = loaded_data
                start_z += 1
            elif loaded_data.ndim == 3:
                delta_z = my_slice.stop - my_slice.start
                data[start_z:delta_z, :, :] = loaded_data
                start_z += delta_z
            else:
                raise ValueError("Dark and ref raw data should be 2D or 3D")

        return data

    def run(self) -> dict:
        if self.reduced_method is ReduceMethod.MEDIAN:
            method_ = numpy.median
        elif self.reduced_method is ReduceMethod.MEAN:
            method_ = numpy.mean
        elif self.reduced_method is ReduceMethod.NONE:
            return ({}, ReducedFramesInfos())
        elif self.reduced_method in (ReduceMethod.FIRST, ReduceMethod.LAST):
            method_ = "raw"
        else:
            raise ValueError(
                f"Mode {self.reduced_method} for {self.reducer_target} is not managed"
            )
        raw_series = self.get_series(self.scan, self.reducer_target)
        if len(raw_series) == 0:
            _logger.warning(
                f"No raw data found for {self.scan} in order to reduce {self.reducer_target}"
            )
            return ({}, ReducedFramesInfos())

        res = {}
        # res: key is serie index (first serie frame index), value is the numpy.array of the reduced frame
        infos = ReducedFramesInfos()

        for series_ in raw_series:
            series_index = min(series_)
            if self.reducer_target is REDUCER_TARGET.DARKS and len(res) > 0:
                continue

            series_frame_data = self.load_data_serie(series_)
            series_count_time = self.get_count_time_serie(indexes=list(series_.keys()))
            series_machine_current = self.get_machine_current(
                indexes=list(series_.keys())
            )

            if method_ == "raw":
                # i method is raw then only the targetted frame (first or last) will be loaded
                data = res[series_index] = series_frame_data.reshape(
                    -1, series_frame_data.shape[-1]
                )
                if self.reduced_method is ReduceMethod.FIRST:
                    index_infos = 0
                elif self.reduced_method is ReduceMethod.LAST:
                    index_infos = -1
                else:
                    raise ValueError(
                        f"reduced method not handle for method 'raw' ({self.reduced_method}). Expects 'first' or 'last'"
                    )
                if len(series_machine_current) > 0:
                    infos.machine_current.append(series_machine_current[index_infos])
                if len(series_count_time) > 0:
                    infos.count_time.append(series_count_time[index_infos])
            else:
                data = method_(series_frame_data, axis=0)
                if len(series_machine_current) > 0:
                    infos.machine_current.append(method_(series_machine_current))
                if len(series_count_time) > 0:
                    infos.count_time.append(method_(series_count_time))

            if self.output_dtype is not None:
                data = data.astype(self.output_dtype)
            res[series_index] = data

        return res, infos
