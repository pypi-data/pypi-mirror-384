# coding: utf-8
"""Module with utils in order to define series of scan (TomoScanBase)"""

from __future__ import annotations

import logging
from typing import Iterable

from tomoscan.scanbase import TomoScanBase
from tomoscan.tomoobject import TomoObject
from tomoscan.utils.io import deprecated

from .factory import Factory
from .identifier import BaseIdentifier

_logger = logging.getLogger(__name__)


__all__ = [
    "Serie",
    "Series",
    "sequences_to_series_from_sample_name",
    "check_series_is_consistent_frm_sample_name",
    "series_is_complete_from_group_size",
]


class Series(list):
    """
    A series can be view as an extended list of :class:`TomoObject`.
    This allow the user to define a relation between scans like:

    .. image:: /_static/../img/serie_tomoscanbase_class_diag.png
    """

    def __init__(
        self, name: str | None = None, iterable=None, use_identifiers=False
    ) -> None:
        if name is not None and not isinstance(name, str):
            raise TypeError(
                f"name should be None os an instance of str. Get {type(name)} instead"
            )
        self._name = "Unknow" if name is None else name
        self.__use_identifiers = use_identifiers
        if iterable is None:
            iterable = []
        super().__init__()
        for item in iterable:
            self.append(item)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str):
        if not isinstance(name, str):
            raise TypeError("name is expected to be an instance of str")
        self._name = name

    @property
    def use_identifiers(self):
        return self.__use_identifiers

    def append(self, object: TomoObject):
        if not isinstance(object, TomoObject):
            raise TypeError(
                f"object is expected to be an instance of {TomoObject} not {type(object)}"
            )
        if self.use_identifiers:
            super().append(object.get_identifier().to_str())
        else:
            super().append(object)

    def remove(self, object: TomoObject):
        if not isinstance(object, TomoObject):
            raise TypeError(
                f"object is expected to be an instance of {TomoObject} not {type(object)}"
            )
        if self.use_identifiers:
            super().remove(object.get_identifier().to_str())
        else:
            super().remove(object)

    def to_dict_of_str(self) -> dict:
        """
        call for each scan DatasetIdentifier.to_str() if use dataset identifier.
        Otherwise return a default list with dataset identifiers
        """
        objects = []
        for dataset in self:
            if self.use_identifiers:
                objects.append(dataset)
            else:
                objects.append(dataset.get_identifier().to_str())
        return {
            "objects": objects,
            "name": self.name,
            "use_identifiers": self.use_identifiers,
        }

    @staticmethod
    def from_dict_of_str(dict_, factory=Factory, use_identifiers: bool | None = None):
        """
        create a Series from it definition from a dictionary

        :param_: dictionary containing the series to create
        :param factory: factory to use in order to create scans defined from there Identifier (as an instance of DatasetIdentifier or is str representation)
        :param use_identifiers: use_identifiers can be overwrite when creating the series

        :return: created Series
        """
        name = dict_["name"]
        objects = dict_["objects"]
        if use_identifiers is None:
            use_identifiers = dict_.get("use_identifiers", False)
        instanciated_scans = []
        for tomo_obj in objects:
            if isinstance(tomo_obj, (str, BaseIdentifier)):
                instanciated_scans.append(
                    factory.create_tomo_object_from_identifier(identifier=tomo_obj)
                )
            else:
                raise TypeError(
                    f"elements of dict_['objects'] are expected to be an instance of TomoObject, DatasetIdentifier or str representing a DatasetIdentifier. Not {type(tomo_obj)}"
                )

        return Series(
            name=name, use_identifiers=use_identifiers, iterable=instanciated_scans
        )

    def __contains__(self, tomo_obj: BaseIdentifier):
        if self.use_identifiers:
            key = tomo_obj.get_identifier().to_str()
        else:
            key = tomo_obj
        return super().__contains__(key)

    def __eq__(self, other):
        if not isinstance(other, Series):
            return False
        return self.name == other.name and super().__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)


@deprecated(replacement="tomoscan.series.series", since_version="2.1")
class Serie(Series):
    def __init__(self, name=None, iterable=None, use_identifiers=False):
        super().__init__(name, iterable, use_identifiers)


def sequences_to_series_from_sample_name(scans: Iterable) -> tuple:
    """
    create a series with the same sample name

    :param Iterable scans:
    :return: tuple of series if as_tuple_of_list is false else a tuple of list (of TomoScanBase)
    """
    series = {}
    for scan in scans:
        if not isinstance(scan, TomoScanBase):
            raise TypeError("Elements are expected to be instances of TomoScanBase")
        if scan.sample_name is None:
            _logger.warning(f"no scan sample found for {scan}")
        if scan.sample_name not in series:
            series[scan.sample_name] = Series(use_identifiers=False)
        series[scan.sample_name].append(scan)
    return tuple(series.values())


def check_series_is_consistent_frm_sample_name(scans: Iterable):
    """
    Insure the provided group of scan is valid. Otherwise raise an error

    :param Iterable scans: group of TomoScanBAse to check
    """
    l_scans = set()
    for scan in scans:
        if not isinstance(scan, TomoScanBase):
            raise TypeError("Elements are expected to be instance of TomoScanBase")
        if scan in l_scans:
            raise ValueError("{} is present at least twice")
        elif len(l_scans) > 0:
            first_scan = next(iter((l_scans)))
            if first_scan.sample_name != scan.sample_name:
                raise ValueError(
                    f"{scan} and {first_scan} are from two different sample: {scan.sample_name} and {first_scan.sample_name}"
                )
        l_scans.add(scan)


@deprecated(
    replacement="check_series_is_consistent_frm_sample_name", since_version="2.1"
)
def check_serie_is_consistant_frm_sample_name(scans: Iterable):
    return check_series_is_consistent_frm_sample_name(scans=scans)


def series_is_complete_from_group_size(scans: Iterable) -> bool:
    """
    Insure the provided group of scan is valid. Otherwise raise an error

    :param scans: group of TomoScanBAse to check
    :return: True if the group is complete
    """
    if len(scans) == 0:
        return True
    try:
        check_series_is_consistent_frm_sample_name(scans=scans)
    except Exception as e:
        _logger.error(f"provided group is invalid. {e}")
        raise e
    else:
        group_size = next(iter(scans)).group_size
        if group_size is None:
            _logger.warning("No information found regarding group size")
            return True
        elif group_size == len(scans):
            return True
        elif group_size < len(scans):
            _logger.warning("more scans found than group_size")
            return True
        else:
            return False


@deprecated(replacement="series_is_complete_from_group_size", since_version="2.1")
def serie_is_complete_from_group_size(scans: Iterable) -> bool:
    return series_is_complete_from_group_size(scans=scans)
