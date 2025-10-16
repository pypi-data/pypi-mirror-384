from nxtomomill.utils.io import deprecated_warning
from nxtomo.nxobject.nxobject import *  # noqa F401

deprecated_warning(
    type_="Module",
    name="nxtomomill.nexus.nxobject",
    reason="dedicated project created",
    replacement="nxtomo.nxobject.nxobject",
    since_version=1.0,
)
