from __future__ import annotations

import pint
from nxtomo.nxobject.nxdetector import FieldOfView
from nxtomomill.utils.io import deprecated

from pydantic import BaseModel, Field, field_validator, field_serializer, ConfigDict

_ureg = pint.get_application_registry()


class UnitSection(BaseModel):

    model_config = ConfigDict(
        validate_assignment=True, arbitrary_types_allowed=True, validate_by_name=True
    )

    pixel_size_unit: pint.Unit = Field(
        default_factory=lambda: _ureg.micrometer,
        description="Unit used to save pixel size. Must be in of ['nanometer', 'micrometer', 'millimeter', 'centimeter', 'meter']",
        alias="expected_unit_for_pixel_size",
    )
    sample_detector_distance_unit: pint.Unit | None = Field(
        default_factory=lambda: _ureg.millimeter,
        description="Unit used by SPEC to save sample to detector distance. Must be in of ['nanometer', 'micrometer', 'millimeter', 'centimeter', 'meter']",
        alias="expected_unit_for_distance",
    )
    energy_unit: pint.Unit | None = Field(
        default_factory=lambda: _ureg.keV,
        description="Unit used by SPEC to save energy. Must be in of ['joule', 'electron_volt', 'kiloelectron_volt', 'millielectron_volt', 'gigaelectron_volt', 'kilojoule']",
        alias="expected_unit_for_energy",
    )
    x_translation_unit: pint.Unit | None = Field(
        default_factory=lambda: _ureg.millimeter,
        description="Unit used by SPEC to save x translation. Must be in of ['nanometer', 'micrometer', 'millimeter', 'centimeter', 'meter']",
        alias="expected_unit_for_x_translation",
    )
    y_translation_unit: pint.Unit | None = Field(
        default_factory=lambda: _ureg.millimeter,
        description="Unit used by SPEC to save y translation. Must be in of ['nanometer', 'micrometer', 'millimeter', 'centimeter', 'meter']",
        alias="expected_unit_for_y_translation",
    )
    z_translation_unit: pint.Unit | None = Field(
        default_factory=lambda: _ureg.millimeter,
        description="Unit used by SPEC to save z translation. Must be in of ['nanometer', 'micrometer', 'millimeter', 'centimeter', 'meter']",
        alias="expected_unit_for_z_translation",
    )
    machine_current_unit: pint.Unit | None = Field(
        default_factory=lambda: _ureg.mA,
        description="Unit used by SPEC to save machine current (also aka SRcurrent). Must be in of ['ampere', 'kiloampere', 'milliampere']",
        alias="expected_unit_for_machine_current",
    )

    @field_validator(
        "pixel_size_unit",
        "sample_detector_distance_unit",
        "energy_unit",
        "x_translation_unit",
        "y_translation_unit",
        "z_translation_unit",
        "machine_current_unit",
        mode="before",
    )
    @classmethod
    def cast_to_pint_unit(cls, value: str | FieldOfView) -> pint.Unit | None:
        if value in ("kiloelectron_volt", "kev"):
            return _ureg.keV
        if value == "milliampere":
            return _ureg.mA
        return pint.Unit(value)

    @field_serializer(
        "pixel_size_unit",
        "sample_detector_distance_unit",
        "energy_unit",
        "x_translation_unit",
        "y_translation_unit",
        "z_translation_unit",
        "machine_current_unit",
        when_used="always",
    )
    @classmethod
    def serialized_unit(cls, value) -> str:
        return f"{value}"

    @property
    @deprecated(
        reason="renamed",
        replacement="sample_detector_distance_unit",
        since_version="2.0",
    )
    def distance_unit(self):
        return self.sample_detector_distance_unit

    @distance_unit.setter
    @deprecated(
        reason="renamed",
        replacement="sample_detector_distance_unit",
        since_version="2.0",
    )
    def distance_unit(self, unit):
        self.sample_detector_distance_unit = unit


UnitSection.model_rebuild()
