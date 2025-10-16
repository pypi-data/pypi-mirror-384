from nxtomomill.utils.io import deprecated_warning
from nxtomo.nxobject.nxinstrument import *  # noqa F401

deprecated_warning(
    type_="Module",
    name="nxtomomill.nexus.nxinstrument",
    reason="dedicated project created",
    replacement="nxtomo.nxobject.nxinstrument",
    since_version=1.0,
)
