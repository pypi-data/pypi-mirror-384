from __future__ import annotations


from pydantic import BaseModel, ConfigDict, Field, field_validator
from nxtomomill.models.utils import filter_str_def


class InstrumentSection(BaseModel):

    model_config = ConfigDict(validate_assignment=True, validate_by_name=True)

    instrument_name: str | None = Field(
        default=None, description="Name of the instrument"
    )

    @field_validator(
        "instrument_name",
        mode="plain",
    )
    @classmethod
    def cast_instrument_name(cls, value: str | None) -> str | None:
        res = filter_str_def(value)
        return res
