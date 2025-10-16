from tomoscan.utils.io import deprecated_warning

deprecated_warning(
    type_="Module",
    name="tomoscan.nexus.paths.nxsource",
    reason="dedicated project created",
    replacement="nxtomo.paths.nxsource",
    since_version=2.0,
)

from nxtomo.paths.nxsource import *  # noqa F401
