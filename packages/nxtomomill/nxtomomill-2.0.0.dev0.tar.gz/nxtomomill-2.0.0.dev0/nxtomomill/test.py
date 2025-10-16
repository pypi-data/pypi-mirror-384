from nxtomomill.utils.io import deprecated_warning
from nxtomomill.tests import *  # noqa F401

deprecated_warning(
    type_="Module",
    name="nxtomomill.test",
    reason="renamed",
    replacement="nxtomomill.tests",
    since_version=1.1,
)
