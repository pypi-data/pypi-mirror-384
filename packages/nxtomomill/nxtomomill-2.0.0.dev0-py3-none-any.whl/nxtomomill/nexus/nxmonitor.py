from nxtomomill.utils.io import deprecated_warning
from nxtomo.nxobject.nxmonitor import *  # noqa F401

deprecated_warning(
    type_="Module",
    name="nxtomomill.nexus.nxmonitor",
    reason="dedicated project created",
    replacement="nxtomo.nxobject.nxmonitor",
    since_version=1.0,
)
