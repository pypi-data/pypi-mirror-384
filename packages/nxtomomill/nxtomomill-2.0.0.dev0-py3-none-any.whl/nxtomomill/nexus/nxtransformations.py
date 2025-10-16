from nxtomomill.utils.io import deprecated_warning
from nxtomo.nxobject.nxtransformations import *  # noqa F401

deprecated_warning(
    type_="Module",
    name="nxtomomill.nexus.nxtransformations",
    reason="dedicated project created",
    replacement="nxtomo.nxobject.nxtransformations",
    since_version=1.0,
)
