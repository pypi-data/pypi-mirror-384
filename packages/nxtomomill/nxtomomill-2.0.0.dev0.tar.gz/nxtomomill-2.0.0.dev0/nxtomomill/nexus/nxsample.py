from nxtomomill.utils.io import deprecated_warning
from nxtomo.nxobject.nxsample import *  # noqa F401

deprecated_warning(
    type_="Module",
    name="nxtomomill.nexus.nxsample",
    reason="dedicated project created",
    replacement="nxtomo.nxobject.nxsample",
    since_version=1.0,
)
