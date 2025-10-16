from tomoscan.utils.io import deprecated_warning
from .tests import *  # noqa F401,F403

deprecated_warning(
    type_="Module",
    name="tomoscan.test",
    reason="renamed",
    replacement="tomoscan.tests",
    since_version=2.1,
)
