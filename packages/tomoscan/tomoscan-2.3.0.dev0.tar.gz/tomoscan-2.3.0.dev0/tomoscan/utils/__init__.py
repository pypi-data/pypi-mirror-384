"""General utils"""

from .decorator import docstring  # noqa F401
from .geometry import BoundingBox1D, BoundingBox3D, get_subvolume_shape  # noqa F401
import numpy


def is_numpy_scalar_dtype(par):
    try:
        numpy.dtype(par)
        res = True
    except TypeError:
        res = False
    return res
