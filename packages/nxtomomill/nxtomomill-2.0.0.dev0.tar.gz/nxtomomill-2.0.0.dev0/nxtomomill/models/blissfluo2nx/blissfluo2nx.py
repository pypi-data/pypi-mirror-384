# coding: utf-8

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .general_section import GeneralSection
from ..base.source_section import SourceSection
from ..base.instrument_section import InstrumentSection
from ..base.NestedModelBase import NestedModelBase


__all__ = [
    "BlissFluo2nxModel",
]


class BlissFluo2nxModel(
    BaseModel,
    NestedModelBase,
):
    model_config = ConfigDict(str_to_upper=True, validate_assignment=True)

    general_section: GeneralSection = GeneralSection()
    source_section: SourceSection = SourceSection()
    instrument_section: InstrumentSection = InstrumentSection()

    def model_dump(self, *args, **kwargs) -> dict:
        unordered_result = super().model_dump(*args, **kwargs)
        orderdered_result = {
            "ewoksfluo_filename": unordered_result.pop("ewoksfluo_filename"),
            "output_file": unordered_result.pop("output_file"),
            "detector_names": unordered_result.pop("detector_names"),
            "dimension": unordered_result.pop("dimension"),
        }
        orderdered_result.update(unordered_result)
        return orderdered_result
