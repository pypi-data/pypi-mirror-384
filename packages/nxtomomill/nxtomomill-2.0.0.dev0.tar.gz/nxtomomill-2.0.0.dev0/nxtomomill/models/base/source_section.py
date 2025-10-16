from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, ConfigDict, field_serializer
from nxtomo.nxobject.nxsource import ProbeType, SourceType
from nxtomomill.models.utils import filter_str_def


class SourceSection(BaseModel):

    model_config = ConfigDict(validate_assignment=True, validate_by_name=True)

    source_name: str | None = Field(
        default="ESRF", description="Name of the instrument"
    )

    source_type: SourceType | None = Field(
        default=SourceType.SYNCHROTRON_X_RAY_SOURCE, description="Source type"
    )

    source_probe: ProbeType | None = Field(
        default=ProbeType.X_RAY, description="Probe type"
    )

    @field_validator(
        "source_type",
        mode="plain",
    )
    @classmethod
    def cast_to_source_type(cls, value: str | SourceType | None) -> SourceType:
        if value in (None, "", "None"):
            return None
        elif isinstance(value, str):
            value = filter_str_def(value)
        return SourceType(value)

    @field_serializer(
        "source_type",
    )
    @classmethod
    def serialize_source_type(cls, source_type: SourceType | None) -> str:
        if source_type is None:
            return ""
        else:
            return source_type.value

    @field_validator(
        "source_probe",
        mode="plain",
    )
    @classmethod
    def cast_to_source_probe(cls, value: str | ProbeType | None) -> ProbeType:
        if value in (None, ""):
            return None
        elif isinstance(value, str):
            value = filter_str_def(value)
        return ProbeType(value)

    @field_serializer(
        "source_probe",
    )
    @classmethod
    def serialize_source_probe(cls, source_probe: ProbeType | None) -> str:
        if source_probe is None:
            return ""
        else:
            return source_probe.value

    @field_validator(
        "source_name",
        mode="plain",
    )
    @classmethod
    def cast_to_str(cls, value: str | None) -> tuple | None:
        return filter_str_def(value)
