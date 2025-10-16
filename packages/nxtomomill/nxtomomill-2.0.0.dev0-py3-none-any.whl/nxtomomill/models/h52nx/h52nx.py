# coding: utf-8

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from configparser import ConfigParser

from ..base.NestedModelBase import NestedModelBase
from ..base.FrmFlatToNestedBase import FrmFlatToNestedBase
from ..base.instrument_section import InstrumentSection
from .general_section import GeneralSection
from .keys_section import KeysSection
from .entries_and_title_section import EntriesAndTitlesSection
from .frame_type_section import FrameTypeSection
from .multitomo_section import MultiTomoSection
from .extra_params_section import ExtraParamsSection
from nxtomomill.utils.io import deprecated_warning, deprecated


__all__ = [
    "H52nxModel",
    "generate_default_h5_config",
]


class H52nxModel(
    FrmFlatToNestedBase,
    GeneralSection,
    KeysSection,
    EntriesAndTitlesSection,
    FrameTypeSection,
    MultiTomoSection,
    ExtraParamsSection,
    InstrumentSection,
):
    """Configuration file to run a conversion from bliss-hdf5 file to NXtomo format"""

    model_config: ConfigDict = ConfigDict(validate_assignment=True)

    def to_nested_model(self) -> _NestedTomoHDF5Config:
        return _NestedTomoHDF5Config(
            general_section=GeneralSection(
                output_file=self.output_file,
                overwrite=self.overwrite,
                log_level=self.log_level,
                input_file=self.input_file,
                file_extension=self.file_extension,
                raises_error=self.raises_error,
                no_input=self.no_input,
                single_file=self.single_file,
                no_master_file=self.no_master_file,
                ignore_bliss_tomo_config=self.ignore_bliss_tomo_config,
                field_of_view=self.field_of_view,
                rotation_is_clockwise=self.rotation_is_clockwise,
                create_control_data=self.create_control_data,
                check_tomo_n=self.check_tomo_n,
                mechanical_lr_flip=self.mechanical_lr_flip,
                mechanical_ud_flip=self.mechanical_ud_flip,
            ),
            keys_section=KeysSection(
                valid_camera_names=self.valid_camera_names,
                rotation_angle_keys=self.rotation_angle_keys,
                sample_x_keys=self.sample_x_keys,
                sample_y_keys=self.sample_y_keys,
                translation_y_keys=self.translation_y_keys,
                translation_z_keys=self.translation_z_keys,
                diode_keys=self.diode_keys,
                exposure_time_keys=self.exposure_time_keys,
                sample_x_pixel_size_keys=self.sample_x_pixel_size_keys,
                sample_y_pixel_size_keys=self.sample_y_pixel_size_keys,
                detector_x_pixel_size_keys=self.detector_x_pixel_size_keys,
                detector_y_pixel_size_keys=self.detector_y_pixel_size_keys,
                sample_detector_distance_keys=self.sample_detector_distance_keys,
                source_sample_distance_keys=self.source_sample_distance_keys,
                machine_current_keys=self.machine_current_keys,
            ),
            entries_and_titles_section=EntriesAndTitlesSection(
                entries=self.entries,
                sub_entries_to_ignore=self.sub_entries_to_ignore,
                init_titles=self.init_titles,
                zseries_init_titles=self.zseries_init_titles,
                multitomo_init_titles=self.multitomo_init_titles,
                dark_titles=self.dark_titles,
                flat_titles=self.flat_titles,
                projection_titles=self.projection_titles,
                alignment_titles=self.alignment_titles,
                back_and_forth_init_titles=self.back_and_forth_init_titles,
            ),
            frame_type_section=FrameTypeSection(
                data_scans=self.data_scans,
                default_data_copy=self.default_data_copy,
            ),
            multitomo_section=MultiTomoSection(
                start_angle_offset_in_degree=self.start_angle_offset_in_degree,
                n_nxtomo=self.n_nxtomo,
                angle_interval_in_degree=self.angle_interval_in_degree,
                shift_angles=self.shift_angles,
            ),
            extra_params_section=ExtraParamsSection(
                energy_kev=self.energy_kev,
                x_sample_pixel_size_m=self.x_sample_pixel_size_m,
                y_sample_pixel_size_m=self.y_sample_pixel_size_m,
                x_detector_pixel_size_m=self.x_detector_pixel_size_m,
                y_detector_pixel_size_m=self.y_detector_pixel_size_m,
                detector_sample_distance_m=self.detector_sample_distance_m,
                source_sample_distance_m=self.source_sample_distance_m,
            ),
        )

    @property
    def is_using_titles(self) -> bool:
        return len(self.data_scans) == 0

    @property
    def is_using_urls(self) -> bool:
        """
        Return true if we want to use urls for darks, flats, projections
        instead of titles
        """
        return len(self.data_scans) > 0

    def clear_entries_and_subentries(self):
        self.entries = ()
        self.sub_entries_to_ignore = ()

    @classmethod
    def from_cfg_file(cls, file_path: str) -> H52nxModel:
        txt_parser = ConfigParser(allow_no_value=True)
        txt_parser.read(file_path)

        def get_section(name, default={}):
            if txt_parser.has_section(name):
                return txt_parser[name]
            else:
                return default

        return _NestedTomoHDF5Config(
            general_section=GeneralSection(**get_section("GENERAL_SECTION")),
            entries_and_titles_section=EntriesAndTitlesSection(
                **get_section("ENTRIES_AND_TITLES_SECTION")
            ),
            extra_params_section=ExtraParamsSection(
                **get_section("EXTRA_PARAMS_SECTION")
            ),
            frame_type_section=FrameTypeSection(**get_section("FRAME_TYPE_SECTION")),
            multitomo_section=MultiTomoSection(**get_section("MULTITOMO_SECTION")),
            keys_section=KeysSection(**get_section("KEYS_SECTION")),
        ).to_flatten_config()

    # deprecated function / properties from version 1

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
        config = _NestedTomoHDF5Config(**dict_)
        return config.to_flatten_config()

    @property
    @deprecated(since_version="2.0", reason="removed", replacement="")
    def bam_single_file(self):
        """This option has been removed. Usage of 'single_file' should be enough"""
        pass

    @bam_single_file.setter
    @deprecated(since_version="2.0", reason="removed", replacement="")
    def bam_single_file(self, bam: bool):
        """This option has been removed. Usage of 'single_file' should be enough"""
        pass


class _NestedTomoHDF5Config(BaseModel, NestedModelBase):
    """
    Nested model to dump the model to .cfg.
    It has historically sections when the model (config class is flat). But the parameters are the same
    """

    model_config = ConfigDict(str_to_upper=True)

    general_section: GeneralSection = GeneralSection()
    keys_section: KeysSection = KeysSection()
    entries_and_titles_section: EntriesAndTitlesSection = EntriesAndTitlesSection()
    frame_type_section: FrameTypeSection = FrameTypeSection()
    multitomo_section: MultiTomoSection = MultiTomoSection()
    extra_params_section: ExtraParamsSection = ExtraParamsSection()

    def to_flatten_config(self) -> H52nxModel:
        return H52nxModel(
            **self.general_section.model_dump(),
            **self.keys_section.model_dump(),
            **self.entries_and_titles_section.model_dump(),
            **self.frame_type_section.model_dump(),
            **self.multitomo_section.model_dump(),
            **self.extra_params_section.model_dump(),
        )


def generate_default_h5_config() -> dict:
    """generate a default configuration for converting hdf5 to nx"""
    config = H52nxModel().to_nested_model()
    return {key.upper(): value for key, value in config.model_dump().items()}
