from enum import Enum


class ReduceMethod(Enum):
    """
    possible method to compute reduced darks / flats
    """

    MEAN = "mean"  # compute the mean of dark / flat frames series
    MEDIAN = "median"  # compute the median of dark / flat frames series
    FIRST = "first"  # take the first frame of the dark / flat series
    LAST = "last"  # take the last frame of the dark / flat series
    NONE = "none"
