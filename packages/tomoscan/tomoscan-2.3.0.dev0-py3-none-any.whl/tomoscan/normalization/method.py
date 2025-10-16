from enum import Enum


class Method(Enum):
    NONE = "none"
    SUBTRACTION = "subtraction"
    DIVISION = "division"
    CHEBYSHEV = "chebyshev"
    LSQR_SPLINE = "lsqr spline"
