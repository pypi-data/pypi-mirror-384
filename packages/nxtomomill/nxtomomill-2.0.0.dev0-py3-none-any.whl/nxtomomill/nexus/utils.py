from nxtomomill.utils.io import deprecated_warning
from nxtomomill.utils.nexus import *  # noqa F401

deprecated_warning(
    type_="Module",
    name="nxtomomill.nexus.utils",
    reason="dedicated project created",
    replacement="nxtomomill.utils.nexus",
    since_version=1.0,
)
