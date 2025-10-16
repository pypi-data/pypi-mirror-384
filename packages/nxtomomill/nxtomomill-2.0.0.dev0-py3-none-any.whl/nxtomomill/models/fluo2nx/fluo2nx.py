# coding: utf-8

from __future__ import annotations

from configparser import ConfigParser

from pydantic import BaseModel, ConfigDict

from ..base.FrmFlatToNestedBase import FrmFlatToNestedBase
from ..base.NestedModelBase import NestedModelBase

from ..base.source_section import SourceSection as _SourceSection
from ..base.instrument_section import InstrumentSection
from .general_section import GeneralSection
from nxtomomill.utils.io import deprecated_warning


__all__ = ["Fluo2nxModel", "generate_default_fluo_config"]


class _LegacySourceSection(_SourceSection, InstrumentSection):
    """Historically the instrument name and section was melt with the source section"""

    pass


class Fluo2nxModel(FrmFlatToNestedBase, GeneralSection, _LegacySourceSection):
    """
    Configuration class to provide to the fluo->nx converter .
    """

    model_config = ConfigDict(validate_assignment=True)

    def to_nested_model(self) -> _NestedTomoFluoConfig:
        return _NestedTomoFluoConfig(
            general_section=GeneralSection(
                output_file=self.output_file,
                dataset_basename=self.dataset_basename,
                dataset_info_file=self.dataset_info_file,
                detector_names=self.detector_names,
                dimension=self.dimension,
                duplicate_data=self.duplicate_data,
                file_extension=self.file_extension,
                input_folder=self.input_folder,
                log_level=self.log_level,
                overwrite=self.overwrite,
                patterns_to_ignores=self.patterns_to_ignores,
            ),
            source_section=_LegacySourceSection(
                instrument_name=self.instrument_name,
                source_name=self.source_name,
                source_probe=self.source_probe,
                source_type=self.source_type,
            ),
        )

    @classmethod
    def from_cfg_file(cls, file_path: str) -> Fluo2nxModel:
        txt_parser = ConfigParser(allow_no_value=True)
        txt_parser.read(file_path)

        def get_section(name, default={}):
            if txt_parser.has_section(name):
                return txt_parser[name]
            else:
                return default

        return _NestedTomoFluoConfig(
            general_section=GeneralSection(**get_section("GENERAL_SECTION")),
            source_section=_LegacySourceSection(**get_section("SOURCE_SECTION")),
        ).to_flatten_config()

    @staticmethod
    def from_dict(dict_: dict) -> None:
        deprecated_warning(
            type_="function",
            name="from_dict",
            reason="replaced by pydantic 'model_dump' function",
            replacement="model_dump",
            since_version="2.0",
        )

        dict_ = {key.lower(): value for key, value in dict_.items()}
        config = _NestedTomoFluoConfig(**dict_)
        return config.to_flatten_config()


class _NestedTomoFluoConfig(BaseModel, NestedModelBase):

    model_config = ConfigDict(str_to_upper=True)

    general_section: GeneralSection = GeneralSection()
    source_section: _LegacySourceSection = _LegacySourceSection()

    def to_flatten_config(self) -> Fluo2nxModel:
        return Fluo2nxModel(
            **self.general_section.model_dump(),
            **self.source_section.model_dump(),
        )


def generate_default_fluo_config(level: str = "required") -> dict:
    """generate a default configuration to convert fluo-tomo data (after PyMCA fit) to NXtomo"""
    config = Fluo2nxModel().to_nested_model()
    return {key.upper(): value for key, value in config.model_dump().items()}
