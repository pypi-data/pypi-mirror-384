from tomoscan.utils.io import deprecated_warning

deprecated_warning(
    type_="Module",
    name="tomoscan.nexus.paths.nxmonitor",
    reason="dedicated project created",
    replacement="nxtomo.paths.nxmonitor",
    since_version=2.0,
)

from nxtomo.paths.nxmonitor import *  # noqa F401
