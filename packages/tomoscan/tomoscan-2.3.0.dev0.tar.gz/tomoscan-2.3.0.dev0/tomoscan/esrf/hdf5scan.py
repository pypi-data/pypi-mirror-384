from tomoscan.utils.io import deprecated_warning

deprecated_warning(
    "Module",
    name="tomoscan.esrf.hdf5scan",
    reason="Have been moved",
    replacement="tomoscan.esrf.scan.nxtomoscan",
    only_once=True,
)

from .scan.nxtomoscan import *  # noqa F401
