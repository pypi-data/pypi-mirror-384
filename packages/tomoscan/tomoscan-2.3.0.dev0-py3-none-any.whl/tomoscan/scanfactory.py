"""deprecated module. Use 'factory' instead"""

from tomoscan.utils.io import deprecated_warning


deprecated_warning(
    "Class",
    name="tomoscan.scanfactory.ScanFactory",
    reason="Has been moved",
    replacement="tomoscan.factory.Factory",
    only_once=True,
)
from tomoscan.factory import Factory as ScanFactory  # noqa F401
