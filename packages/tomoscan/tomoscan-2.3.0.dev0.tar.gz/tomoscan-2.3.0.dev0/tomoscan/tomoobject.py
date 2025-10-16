# coding: utf-8
"""Module containing the TomoObject class. Parent class of any tomo object"""

from __future__ import annotations

from tomoscan.utils import BoundingBox1D

from .identifier import BaseIdentifier

__all__ = [
    "TomoObject",
]


class TomoObject:
    """Parent class of all tomographic object in tomoscan"""

    @staticmethod
    def from_identifier(identifier: str | BaseIdentifier):
        """Return the Dataset from a identifier"""
        raise NotImplementedError("Base class")

    def get_identifier(self) -> BaseIdentifier:
        """dataset unique identifier. Can be for example a hdf5 and
        en entry from which the dataset can be rebuild"""
        raise NotImplementedError("Base class")

    def get_bounding_box(self, axis: str | int | None = None) -> BoundingBox1D:
        """
        Return the bounding box covered by the Tomo object
        axis is expected to be in (0, 1, 2) or (x==0, y==1, z==2)
        """
        raise NotImplementedError("Base class")

    def build_drac_metadata(self) -> dict:
        """
        build icat metadata dictionary filling NXtomo definition following icat definition: https://gitlab.esrf.fr/icat/hdf5-master-config/-/blob/88a975039694d5dba60e240b7bf46c22d34065a0/hdf5_cfg.xml
        """
        raise NotImplementedError()

    def clear_cache(self) -> None:
        """
        A TomoObj can have some values store in the cache (some metadata read for example).
        This function should clear all caches.
        """
        pass
