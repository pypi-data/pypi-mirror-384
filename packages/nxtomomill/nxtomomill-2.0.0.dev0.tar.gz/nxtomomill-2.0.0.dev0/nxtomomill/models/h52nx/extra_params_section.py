from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, ConfigDict


class ExtraParamsSection(BaseModel):

    model_config = ConfigDict(validate_assignment=True, validate_by_name=True)

    energy_kev: float | None = Field(default=None, description="Energy in keV")
    x_sample_pixel_size_m: float | None = Field(
        default=None, description="X sample pixel size in meters"
    )
    y_sample_pixel_size_m: float | None = Field(
        default=None, description="Y sample pixel size in meters"
    )
    x_detector_pixel_size_m: float | None = Field(
        default=None, description="X detector pixel size in meters"
    )
    y_detector_pixel_size_m: float | None = Field(
        default=None, description="Y detector pixel size in meters"
    )
    detector_sample_distance_m: float | None = Field(
        default=None, description="Detector sample distance in meters"
    )
    source_sample_distance_m: float | None = Field(
        default=None, description="Source sample distance in meters"
    )

    @field_validator(
        "energy_kev",
        "x_sample_pixel_size_m",
        "y_sample_pixel_size_m",
        "x_detector_pixel_size_m",
        "y_detector_pixel_size_m",
        "detector_sample_distance_m",
        "source_sample_distance_m",
        mode="plain",
    )
    @classmethod
    def cast_to_scalar_value_or_None(cls, value: str) -> float | None:
        if value in ("", None, "None"):
            return None
        else:
            return float(value)
