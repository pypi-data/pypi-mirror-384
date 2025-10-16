from tomoscan.utils.io import deprecated_warning

deprecated_warning(
    "Module",
    name="tomoscan.esrf.mock",
    reason="Have been moved",
    replacement="tomoscan.esrf.scan.mock",
    only_once=True,
)

from .scan.mock import *  # noqa F401
