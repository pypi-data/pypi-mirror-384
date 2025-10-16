from __future__ import annotations

from pydantic import Field, field_validator, ConfigDict
from collections import OrderedDict


from nxtomomill.models.utils import convert_str_to_tuple, filter_str_def
from ..base.general_section import GeneralSection as _GeneralSectionBase


class GeneralSection(_GeneralSectionBase):
    model_config = ConfigDict(validate_assignment=True, validate_by_name=True)

    ewoksfluo_filename: str | None = Field(
        default=None,
        description="Path to the ewoksfluo-generated h5 file that contains fitted XRF data. If not provided from the configuration file must be provided from the command line.",
    )

    dimension: int = Field(
        default=3,
        description="Dimension of the experiment. 2 for 2D XRFCT, 3 for 3D XRFCT. Default is 3.",
    )

    detector_names: tuple[str, ...] = Field(
        default=tuple(),
        description="Define a list of (real or virtual) detector names used for the exp (space separated values - no comma). E.g. 'falcon xmap'. If not specified, all detectors are processed.",
    )

    @field_validator(
        "detector_names",
        mode="before",
    )
    @classmethod
    def cast_to_tuple(cls, value: str | None) -> tuple[str]:
        return convert_str_to_tuple(value) or ()

    @field_validator(
        "ewoksfluo_filename",
        mode="before",
    )
    @classmethod
    def cast_to_str(cls, value: str | None) -> str | None:
        return filter_str_def(value)

    def model_dump(self, *args, **kwargs) -> dict:
        unordered_result = super().model_dump(*args, **kwargs)
        ordered_result = OrderedDict(
            {
                "ewoksfluo_filename": unordered_result.pop("ewoksfluo_filename"),
                "output_file": unordered_result.pop("output_file"),
                "detector_names": unordered_result.pop("detector_names"),
                "dimension": unordered_result.pop("dimension"),
            }
        )
        ordered_result.update(unordered_result)
        return ordered_result
