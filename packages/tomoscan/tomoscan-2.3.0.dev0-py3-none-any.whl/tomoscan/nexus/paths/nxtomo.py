from tomoscan.utils.io import deprecated_warning

deprecated_warning(
    type_="Module",
    name="tomoscan.nexus.paths.nxtomo",
    reason="dedicated project created",
    replacement="nxtomo.paths.nxtomo",
    since_version=2.0,
)

from nxtomo.paths.nxtomo import *  # noqa F401
