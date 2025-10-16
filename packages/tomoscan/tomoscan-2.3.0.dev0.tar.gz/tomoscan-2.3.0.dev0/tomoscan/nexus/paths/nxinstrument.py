from tomoscan.utils.io import deprecated_warning

deprecated_warning(
    type_="Module",
    name="tomoscan.nexus.paths.nxinstrument",
    reason="dedicated project created",
    replacement="nxtomo.paths.nxinstrument",
    since_version=2.0,
)

from nxtomo.paths.nxinstrument import *  # noqa F401
