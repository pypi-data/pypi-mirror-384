from tomoscan.utils.io import deprecated_warning

deprecated_warning(
    "Module",
    name="tomoscan.framereducerbase",
    reason="Have been replaced by a dedicated module",
    replacement="tomoscan.framereducer",
    only_once=True,
)

from tomoscan.framereducer import *  # noqa F401
