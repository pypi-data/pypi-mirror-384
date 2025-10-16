from nxtomomill.utils.io import deprecated_warning
from nxtomo.nxobject.nxdetector import *  # noqa F401

deprecated_warning(
    type_="Module",
    name="nxtomomill.nexus.nxdetector",
    reason="dedicated project created",
    replacement="nxtomo.nxobject.nxdetector",
    since_version=1.0,
)
