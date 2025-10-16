"""data exchange (dx) configuration module"""

from __future__ import annotations

from nxtomo.nxobject.nxdetector import FieldOfView
from .base.general_section import GeneralSection
from pydantic import Field, ConfigDict, field_serializer, field_validator


__all__ = [
    "DX2nxModel",
]


class DX2nxModel(GeneralSection):
    """Configuration file to run a conversion from data-exchange file to NXtomo format"""

    model_config: ConfigDict = ConfigDict(validate_assignment=True)

    input_file: str = Field(
        description="Path to input file at data-file-exchange format to be converted to NXtomo format"
    )
    copy_data: bool = Field(
        default=True,
        description="If True frames will be duplicated. Otherwise we will create (relative) link to the input file.",
    )
    input_entry: str = Field(
        default="/",
        description="Path to the HDF5 group to convert. For now it looks each file can only contain one dataset. Just to ensure any future compatibility if it evolve with time.",
    )
    output_entry: str = Field(
        "entry0000", description="Path to store the NxTomo created."
    )
    scan_range: tuple[float, float] = Field(
        default=(0.0, 180.0),
        description="Tuple of two elements with the minimum scan range. Projections are expected to be taken with equal angular spaces.",
    )
    pixel_size: tuple[float | None, float | None] = Field(
        default=(None, None),
        description="Pixel size can be provided - in meter - as (x_pizel_size, y_pixel_size)",
    )
    field_of_view: FieldOfView | None = Field(
        default=None, description="Detector field of view"
    )
    sample_detector_distance: float | None = Field(
        default=1.0, description="sample / detector distance in meter"
    )
    energy: float | None = Field(default=None, description="Energy in keV")

    @field_validator(
        "field_of_view",
    )
    @classmethod
    def cast_to_field_of_view(cls, value: str | FieldOfView) -> FieldOfView | None:
        if value in (None, ""):
            return None
        return FieldOfView(value)

    @field_serializer(
        "field_of_view",
        when_used="always",
    )
    @classmethod
    def serialize_field_of_view(cls, field_of_view: FieldOfView | None) -> str:
        if field_of_view is None:
            return None
        else:
            return field_of_view.value
