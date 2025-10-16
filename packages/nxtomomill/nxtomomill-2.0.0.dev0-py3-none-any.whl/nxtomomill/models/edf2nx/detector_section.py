from __future__ import annotations

from nxtomo.nxobject.nxdetector import FieldOfView
from nxtomomill.models.utils import filter_str_def

from pydantic import BaseModel, Field, field_validator, ConfigDict, field_serializer


class DetectorSection(BaseModel):

    model_config = ConfigDict(validate_assignment=True, validate_by_name=True)

    field_of_view: FieldOfView | None = Field(
        default=None,
        description="Detector field of view. If set must be in `Half` or `Full`",
    )

    @field_validator(
        "field_of_view",
        mode="plain",
    )
    @classmethod
    def cast_to_field_of_view(cls, value: str | FieldOfView) -> FieldOfView | None:
        if value in (None, ""):
            return None
        if isinstance(value, str):
            value = filter_str_def(value)
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
