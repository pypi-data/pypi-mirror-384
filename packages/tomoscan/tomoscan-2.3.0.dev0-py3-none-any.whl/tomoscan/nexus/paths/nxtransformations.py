from tomoscan.utils.io import deprecated_warning

deprecated_warning(
    type_="Module",
    name="tomoscan.nexus.paths.nxtransformations",
    reason="dedicated project created",
    replacement="nxtomo.paths.nxtransformations",
    since_version=2.0,
)

from nxtomo.paths.nxtransformations import *  # noqa F401
