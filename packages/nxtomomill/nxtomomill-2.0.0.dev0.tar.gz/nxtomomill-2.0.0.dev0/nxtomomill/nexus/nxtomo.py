from nxtomomill.utils.io import deprecated_warning
from nxtomo.application.nxtomo import *  # noqa F401

deprecated_warning(
    type_="Module",
    name="nxtomomill.nexus.nxtomo",
    reason="dedicated project created",
    replacement="nxtomo.application.nxtomo",
    since_version=1.0,
)
