# coding: utf-8

from __future__ import annotations

from configparser import ConfigParser
from pydantic import BaseModel, ConfigDict

from ..base.FrmFlatToNestedBase import FrmFlatToNestedBase
from ..base.NestedModelBase import NestedModelBase
from .dark_and_flat_section import DarkAndFlatSection
from .general_section import GeneralSection
from .keys_section import KeysSection
from .sample_section import SampleSection
from .unit_section import UnitSection
from .detector_section import DetectorSection
from ..base.source_section import SourceSection as _SourceSection
from ..base.instrument_section import InstrumentSection
from nxtomomill.utils.io import deprecated_warning


__all__ = ["EDF2nxModel", "generate_default_edf_config"]


class _LegacySourceSection(_SourceSection, InstrumentSection):
    """Historically the instrument name and section was melt with the source section"""

    pass


class EDF2nxModel(
    FrmFlatToNestedBase,
    GeneralSection,
    KeysSection,
    DarkAndFlatSection,
    SampleSection,
    _LegacySourceSection,
    DetectorSection,
    UnitSection,
):
    """Configuration file to run a conversion from spec-edf to NXtomo format"""

    model_config: ConfigDict = ConfigDict(validate_assignment=True)

    def to_nested_model(self) -> _NestedTomoEDFConfig:
        return _NestedTomoEDFConfig(
            general_section=GeneralSection(
                output_file=self.output_file,
                overwrite=self.overwrite,
                log_level=self.log_level,
                input_folder=self.input_folder,
                file_extension=self.file_extension,
                delete_edf_source_files=self.delete_edf_source_files,
                output_checks=self.output_checks,
                dataset_basename=self.dataset_basename,
                dataset_info_file=self.dataset_info_file,
                title=self.title,
                patterns_to_ignores=self.patterns_to_ignores,
                duplicate_data=self.duplicate_data,
                external_link_type=self.external_link_type,
            ),
            edf_keys_section=KeysSection(
                motor_position_keys=self.motor_position_keys,
                motor_mne_keys=self.motor_mne_keys,
                rotation_angle_keys=self.rotation_angle_keys,
                x_translation_keys=self.x_translation_keys,
                y_translation_keys=self.y_translation_keys,
                z_translation_keys=self.z_translation_keys,
                machine_current_keys=self.machine_current_keys,
            ),
            sample_section=SampleSection(
                angle_calculation_endpoint=self.angle_calculation_endpoint,
                force_angle_calculation=self.force_angle_calculation,
                angle_calculation_rev_neg_scan_range=self.angle_calculation_rev_neg_scan_range,
                sample_name=self.sample_name,
            ),
            source_section=_LegacySourceSection(
                instrument_name=self.instrument_name,
                source_name=self.source_name,
                source_type=self.source_type,
                source_probe=self.source_probe,
            ),
            detector_section=DetectorSection(
                field_of_view=self.field_of_view,
            ),
            unit_section=UnitSection(
                pixel_size_unit=self.pixel_size_unit,
                sample_detector_distance_unit=self.sample_detector_distance_unit,
                energy_unit=self.energy_unit,
                machine_current_unit=self.machine_current_unit,
                x_translation_unit=self.x_translation_unit,
                y_translation_unit=self.y_translation_unit,
                z_translation_unit=self.z_translation_unit,
            ),
            dark_and_flat_section=DarkAndFlatSection(
                dark_names_prefix=self.dark_names_prefix,
                flat_names_prefix=self.flat_names_prefix,
            ),
        )

    @classmethod
    def from_cfg_file(cls, file_path: str) -> EDF2nxModel:
        txt_parser = ConfigParser(allow_no_value=True)
        txt_parser.read(file_path)

        def get_section(name, default={}):
            if txt_parser.has_section(name):
                return txt_parser[name]
            else:
                return default

        return _NestedTomoEDFConfig(
            general_section=GeneralSection(**get_section("GENERAL_SECTION")),
            edf_keys_section=KeysSection(**get_section("EDF_KEYS_SECTION")),
            dark_and_flat_section=DarkAndFlatSection(
                **get_section("DARK_AND_FLAT_SECTION")
            ),
            sample_section=SampleSection(**get_section("SAMPLE_SECTION")),
            unit_section=UnitSection(**get_section("UNIT_SECTION")),
            source_section=_LegacySourceSection(**get_section("SOURCE_SECTION")),
            detector_section=DetectorSection(**get_section("DETECTOR_SECTION")),
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
        config = _NestedTomoEDFConfig(**dict_)
        return config.to_flatten_config()


class _NestedTomoEDFConfig(
    BaseModel,
    NestedModelBase,
):
    """
    Configuration class to provide to the convert from edf to nx
    """

    model_config = ConfigDict(str_to_upper=True)

    general_section: GeneralSection = GeneralSection()
    edf_keys_section: KeysSection = KeysSection()
    dark_and_flat_section: DarkAndFlatSection = DarkAndFlatSection()
    sample_section: SampleSection = SampleSection()
    source_section: _LegacySourceSection = _LegacySourceSection()
    detector_section: DetectorSection = DetectorSection()
    unit_section: UnitSection = UnitSection()

    def to_flatten_config(self) -> EDF2nxModel:
        return EDF2nxModel(
            **self.general_section.model_dump(),
            **self.edf_keys_section.model_dump(),
            **self.dark_and_flat_section.model_dump(),
            **self.sample_section.model_dump(),
            **self.source_section.model_dump(),
            **self.detector_section.model_dump(),
            **self.unit_section.model_dump(),
        )


def generate_default_edf_config() -> dict:
    """generate a default configuration for converting spec-edf to NXtomo"""
    config = EDF2nxModel()
    return {key.upper(): value for key, value in config.model_dump().items()}
