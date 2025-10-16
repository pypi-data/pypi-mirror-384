from nxtomomill.utils.io import deprecated_warning
from nxtomo.nxobject.nxsource import *  # noqa F401

deprecated_warning(
    type_="Module",
    name="nxtomomill.nexus.nxsource",
    reason="dedicated project created",
    replacement="nxtomo.nxobject.nxsource",
    since_version=1.0,
)
