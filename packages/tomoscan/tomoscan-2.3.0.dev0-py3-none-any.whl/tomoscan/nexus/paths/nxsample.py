from tomoscan.utils.io import deprecated_warning

deprecated_warning(
    type_="Module",
    name="tomoscan.nexus.paths.nxsample",
    reason="dedicated project created",
    replacement="nxtomo.paths.nxsample",
    since_version=2.0,
)

from nxtomo.paths.nxsample import *  # noqa F401
