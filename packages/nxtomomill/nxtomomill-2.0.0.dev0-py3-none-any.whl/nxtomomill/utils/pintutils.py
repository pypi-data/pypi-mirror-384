"""pint utils"""

from __future__ import annotations

import pint

_ureg = pint.get_application_registry()


VALID_CURRENT_VALUES: tuple[str] = [
    str(unit) for unit in (_ureg.ampere, _ureg.kiloampere, _ureg.milliampere)
]
VALID_ENERGY_VALUES: tuple[str] = [
    str(unit)
    for unit in (_ureg.joule, _ureg.eV, _ureg.keV, _ureg.meV, _ureg.GeV, _ureg.kJ)
]
VALID_METRIC_VALUES: tuple[str] = [
    str(unit)
    for unit in (
        _ureg.nanometer,
        _ureg.micrometer,
        _ureg.millimeter,
        _ureg.centimeter,
        _ureg.meter,
    )
]
