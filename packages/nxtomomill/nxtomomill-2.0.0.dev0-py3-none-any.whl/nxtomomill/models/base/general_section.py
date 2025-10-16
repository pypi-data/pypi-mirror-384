from __future__ import annotations

import logging
from pydantic import BaseModel, Field, field_validator, field_serializer, ConfigDict
from nxtomomill.utils import FileExtension
from nxtomomill.models.utils import filter_str_def


class GeneralSection(BaseModel):
    model_config = ConfigDict(validate_assignment=True, validate_by_name=True)

    output_file: str | None = Field(default=None, description="Output file name")
    file_extension: FileExtension = Field(
        default=FileExtension.NX,
        description="File extension if not given in the output file name",
    )
    overwrite: bool = Field(
        default=False, description="Overwrite output files if exists"
    )
    log_level: int = Field(
        default=logging.WARNING,
        description='Log level: "debug", "info", "warning", "error"',
    )

    @field_validator(
        "log_level",
        mode="before",
    )
    @classmethod
    def cast_to_log_level(cls, value: str | int) -> int:
        if isinstance(value, int):
            return value
        elif isinstance(value, str):
            value = filter_str_def(value)
            return getattr(logging, value.upper())
        else:
            raise TypeError

    @field_validator(
        "file_extension",
        mode="plain",
    )
    @classmethod
    def cast_to_file_extension(cls, value: str | FileExtension) -> FileExtension:
        if isinstance(value, str):
            value = filter_str_def(value)
        return FileExtension(value)

    @field_serializer(
        "log_level",
        when_used="always",
    )
    @classmethod
    def serialize_log_level(cls, value: int) -> str:
        return logging.getLevelName(value).lower()

    @field_serializer(
        "file_extension",
        when_used="always",
    )
    @classmethod
    def serialize_file_extension(cls, file_ext: FileExtension) -> str:
        return file_ext.value

    @field_validator(
        "output_file",
    )
    @classmethod
    def cast_output_file(cls, output_file: str | None) -> str | None:
        return filter_str_def(output_file)
