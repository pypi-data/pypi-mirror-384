from __future__ import annotations


import numpy
import warnings
from typing import Iterable


class ReducedFramesInfos:
    """contains reduced frames metadata as count_time and machine_current"""

    MACHINE_ELECT_CURRENT_KEY = "machine_current"

    COUNT_TIME_KEY = "count_time"

    def __init__(self) -> None:
        self._count_time = []
        self._machine_current = []

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, dict):
            return ReducedFramesInfos().load_from_dict(__o) == self
        if not isinstance(__o, ReducedFramesInfos):
            return False
        return numpy.array_equal(
            numpy.array(self.count_time), numpy.array(__o.count_time)
        ) and numpy.array_equal(
            numpy.array(self.machine_current),
            numpy.array(__o.machine_current),
        )

    def clear(self):
        self._count_time.clear()
        self._machine_current.clear()

    @property
    def count_time(self) -> list:
        """
        frame exposure time in second
        """
        return self._count_time

    @count_time.setter
    def count_time(self, count_time: Iterable | None):
        if count_time is None:
            self._count_time.clear()
        else:
            self._count_time = list(count_time)

    @property
    def machine_electric_current(self) -> list:
        warnings.warn(
            "machine_electric_current is deprecated and will be removed in a future version. Use machine_current instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.machine_current

    @machine_electric_current.setter
    def machine_electric_current(self, machine_current: Iterable | None):
        warnings.warn(
            "machine_electric_current is deprecated and will be removed in a future version. Use machine_current instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.machine_current = machine_current

    @property
    def machine_current(self) -> list:
        """
        machine electric current in Ampere
        """
        return self._machine_current

    @machine_current.setter
    def machine_current(self, machine_current: Iterable | None):
        if machine_current is None:
            self._machine_current.clear()
        else:
            self._machine_current = list(machine_current)

    def to_dict(self) -> dict:
        res = {}
        if len(self.machine_current) > 0:
            res[self.MACHINE_ELECT_CURRENT_KEY] = self.machine_current
        if len(self.count_time) > 0:
            res[self.COUNT_TIME_KEY] = self.count_time
        return res

    def load_from_dict(self, my_dict: dict):
        self.machine_current = my_dict.get(self.MACHINE_ELECT_CURRENT_KEY, None)
        self.count_time = my_dict.get(self.COUNT_TIME_KEY, None)
        return self

    @staticmethod
    def pop_info_keys(my_dict: dict):
        if not isinstance(my_dict, dict):
            raise TypeError
        my_dict.pop(ReducedFramesInfos.MACHINE_ELECT_CURRENT_KEY, None)
        my_dict.pop(ReducedFramesInfos.COUNT_TIME_KEY, None)
        return my_dict

    @staticmethod
    def split_data_and_metadata(my_dict):
        metadata = ReducedFramesInfos().load_from_dict(my_dict)
        data = ReducedFramesInfos.pop_info_keys(my_dict)

        def cast_keys_to_int(key):
            try:
                return int(key)
            except ValueError:
                return key

        data = {cast_keys_to_int(key): value for key, value in data.items()}
        return data, metadata

    def __str__(self):
        return "\n".join(
            [
                f"machine_current {self.machine_current}",
                f"count_time {self.count_time}",
            ]
        )
