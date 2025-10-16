from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict, field_validator
from nxtomomill.models.utils import filter_str_def, convert_str_to_bool


class SampleSection(BaseModel):

    model_config = ConfigDict(validate_assignment=True, validate_by_name=True)

    sample_name: str | None = Field(default=None, description="Name of the sample")
    force_angle_calculation: bool = Field(
        default=True,
        description="Determines the method for obtaining rotation angles."
        "Options:"
        "* True: Compute from scan range: Uses `numpy.linspace` to generate rotation angles based on the provided scan range."
        "* False: Load from `.edf` header: Attempts to read the rotation angles directly from the `.edf` file header.",
    )
    angle_calculation_endpoint: bool = Field(
        default=False,
        description="Specifies the endpoint behavior for `numpy.linspace` when calculating rotation angles."
        "",
    )
    angle_calculation_rev_neg_scan_range: bool = Field(
        default=True,
        description="Inverts the rotation angle values when the `ScanRange` is negative.",
    )

    @field_validator(
        "sample_name",
        mode="plain",
    )
    @classmethod
    def cast_to_sample_name(cls, value: str | None) -> str | None:
        return filter_str_def(value)

    @field_validator(
        "angle_calculation_endpoint",
        "force_angle_calculation",
        "angle_calculation_rev_neg_scan_range",
        mode="plain",
    )
    @classmethod
    def cast_to_bool(cls, value: bool | str) -> bool:
        return convert_str_to_bool(value)
