from __future__ import annotations

from pydantic import Field, field_serializer, field_validator, ConfigDict

from nxtomo.nxobject.nxdetector import FieldOfView

from nxtomomill.models.utils import filter_str_def, convert_str_to_bool
from ..base.general_section import GeneralSection as _GeneralSectionBase


class GeneralSection(_GeneralSectionBase):
    model_config = ConfigDict(validate_assignment=True, validate_by_name=True)

    input_file: str | None = Field(default=None, description="Input file path.")
    raises_error: bool = Field(
        default=False, description="Raise an error when encountered."
    )
    no_input: bool = Field(
        default=False, description="Ask for user inputs if missing information."
    )
    single_file: bool = Field(
        default=False, description="Create a single file for all sequences."
    )
    no_master_file: bool = Field(
        default=True, description="Avoid creating the master file."
    )
    ignore_bliss_tomo_config: bool = Field(
        default=False,
        description="Ignore Bliss tomography group. On recent bliss file (2023) a dedicated group specify datasets to be used for tomography. Defining for example translations, rotation, etc. If True then this group will be ignored and conversion will fallback on using path list provided in the KEYS section.",
    )
    field_of_view: FieldOfView | None = Field(
        default=None,
        description="Force output to be a 'Full' or 'Half' acquisition. Else determine from existing metadata",
    )
    create_control_data: bool = Field(
        default=True, description="Generate control/data - filled with machine current."
    )
    check_tomo_n: bool | None = Field(
        default=None,
        description="Check 'tomo_n' metadata once the conversion is done. By default will be done for all except scan build from 'scan_data'.",
    )
    rotation_is_clockwise: bool | None = Field(
        default=None,
        description="Force rotation clockwise or not. If not set will read the information from the bliss-tomo 'tomoconfig' group. Else consider rotation is counterclockwise.",
    )
    mechanical_lr_flip: bool = Field(
        default=False,
        description="Detector image is flipped **left-right** for mechanical reasons that are not propagated with bliss-tomo hdf5 metadata (mirror,..).",
    )
    mechanical_ud_flip: bool = Field(
        default=False,
        description="Detector image is flipped **up-down** for mechanical reasons that are not propagated with bliss-tomo hdf5 metadata (mirror,..).",
    )

    @property
    def request_input(self) -> bool:
        return not self.no_input

    @request_input.setter
    def request_input(self, request: bool):
        self.no_input = request

    @field_validator(
        "check_tomo_n",
        "rotation_is_clockwise",
        mode="before",
    )
    @classmethod
    def cast_to_bool_or_none(cls, value: str | None | bool) -> bool | None:
        if isinstance(value, str):
            value = filter_str_def(value)
        if value in (None, "None", ""):
            return None
        elif value in ("True", True, "1"):
            return True
        elif value in ("False", False, "0"):
            return False
        else:
            raise ValueError

    @field_serializer(
        "check_tomo_n",
        "rotation_is_clockwise",
        when_used="always",
    )
    @classmethod
    def serialize_check_tomo_n(cls, value: None | bool) -> str:
        if value is None:
            return None
        else:
            return value

    @field_validator(
        "field_of_view",
        mode="plain",
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

    @field_validator(
        "input_file",
        mode="before",
    )
    @classmethod
    def cast_to_str(cls, value: str | None) -> str | None:
        return filter_str_def(value)

    @field_validator(
        "no_input",
        "single_file",
        "no_master_file",
        "ignore_bliss_tomo_config",
        "create_control_data",
        "mechanical_lr_flip",
        "mechanical_ud_flip",
        mode="before",
    )
    @classmethod
    def cast_to_bool(cls, value: str | bool | None) -> bool:
        return convert_str_to_bool(value)
