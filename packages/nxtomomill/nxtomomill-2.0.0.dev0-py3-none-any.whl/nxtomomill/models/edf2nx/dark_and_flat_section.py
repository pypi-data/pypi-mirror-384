from __future__ import annotations

from nxtomomill.settings import Tomo
from nxtomomill.models.utils import convert_str_to_tuple
from nxtomomill.utils.io import deprecated
from nxtomomill.models.utils import filter_str_def

from pydantic import BaseModel, Field, field_validator, ConfigDict


class DarkAndFlatSection(BaseModel):

    model_config = ConfigDict(validate_assignment=True, validate_by_name=True)

    dark_names_prefix: tuple[str, ...] = Field(
        default=Tomo.EDF.DARK_NAMES, description="Prefixes of dark field file(s)"
    )
    flat_names_prefix: tuple[str, ...] = Field(
        default=Tomo.EDF.REFS_NAMES, description="Prefixes of flat field file(s)"
    )

    @field_validator(
        "dark_names_prefix",
        "flat_names_prefix",
        mode="plain",
    )
    @classmethod
    def cast_to_tuple(cls, value: str | tuple[str, ...]) -> tuple[str,]:
        if isinstance(value, str):
            value = filter_str_def(value)
        return convert_str_to_tuple(value) or ()

    @property
    @deprecated(since_version="2.0", reason="renamed", replacement="dark_names_prefix")
    def dark_names(self):
        return self.dark_names_prefix

    @dark_names.setter
    @deprecated(since_version="2.0", reason="renamed", replacement="dark_names_prefix")
    def dark_names(self, value):
        self.dark_names_prefix = value

    @property
    @deprecated(since_version="2.0", reason="renamed", replacement="flat_names_prefix")
    def flat_names(self):
        return self.flat_names_prefix

    @flat_names.setter
    @deprecated(since_version="2.0", reason="renamed", replacement="flat_names_prefix")
    def flat_names(self, value):
        self.flat_names_prefix = value
