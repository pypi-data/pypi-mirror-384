from tomoscan.utils.io import deprecated_warning

deprecated_warning(
    "Module",
    name="tomoscan.serie",
    reason="Fix typo",
    replacement="tomoscan.series",
    only_once=True,
)

from .series import *  # noqa F401
