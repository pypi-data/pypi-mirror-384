from __future__ import annotations

import os
import pytest
import logging
import importlib.resources as importlib_resources

from silx.io.url import DataUrl

from nxtomo.nxobject.nxdetector import FieldOfView

from nxtomomill import settings
from nxtomomill.utils import FileExtension
from nxtomomill.models.h52nx import H52nxModel, generate_default_h5_config
from nxtomomill.models.h52nx.general_section import GeneralSection
from nxtomomill.models.h52nx.keys_section import KeysSection
from nxtomomill.models.h52nx.entries_and_title_section import (
    EntriesAndTitlesSection,
)
from nxtomomill.models.h52nx.frame_type_section import (
    FrameTypeSection,
    FrameGroup,
)
from nxtomomill.models.h52nx.multitomo_section import MultiTomoSection
from nxtomomill.models.h52nx.extra_params_section import (
    ExtraParamsSection,
)

from nxtomomill.tests.resources import h52nx_config_files as _h52nx_config_files
from configparser import ConfigParser


def test_moving_to_pydantic_default_config_file():
    """
    test that the default nxtomomill config generated before moving to pydantic is properly interpreted.
    This ignores comments.
    """
    resources = importlib_resources.files(_h52nx_config_files.__name__)
    ref_file = os.path.join(resources, "default_file_before_moving_to_pydantic.cfg")
    assert os.path.exists(ref_file)
    txt_parser = ConfigParser(allow_no_value=True)
    txt_parser.read(ref_file)

    old_config = H52nxModel(
        general_section=txt_parser["GENERAL_SECTION"],
        keys_section=txt_parser["KEYS_SECTION"],
        entries_and_titles_section=txt_parser["ENTRIES_AND_TITLES_SECTION"],
        frame_type_section=txt_parser["FRAME_TYPE_SECTION"],
        multitomo_section=txt_parser["MULTITOMO_SECTION"],
        extra_params_section=txt_parser["EXTRA_PARAMS_SECTION"],
    ).to_nested_model()
    old_dict = {key.upper(): value for key, value in old_config.model_dump().items()}

    new_dict = generate_default_h5_config()
    assert new_dict == old_dict


def test_moving_to_pydantic_modified_config_file():
    """
    test that an old nxtomomill h5-config file generated before moving to pydantic is properly interpreted.
    This ignores any comments.
    """
    resources = importlib_resources.files(_h52nx_config_files.__name__)
    ref_file = os.path.join(resources, "fully_modified_file_before_moving.cfg")
    assert os.path.exists(ref_file)

    config = H52nxModel.from_cfg_file(ref_file)
    # general section
    assert config.input_file == "input_file.h5"
    assert config.output_file == "output_file.nx"
    assert config.overwrite is True
    assert config.file_extension is FileExtension.H5
    assert config.log_level is logging.DEBUG
    assert config.raises_error is True
    assert config.no_input is True
    assert config.single_file is True
    assert config.no_master_file is False
    assert config.ignore_bliss_tomo_config is True
    assert config.field_of_view is FieldOfView.FULL
    assert config.create_control_data is False
    # keys section
    assert config.valid_camera_names == ("my_camera",)
    assert config.rotation_angle_keys == ("rotm",)
    assert config.sample_x_keys == ("samx",)
    assert config.sample_y_keys == ("samy",)
    assert config.translation_y_keys == ("yrot",)
    assert config.translation_z_keys == ("zrot",)
    assert config.diode_keys == ("fpico",)
    assert config.exposure_time_keys == ("exposure_time",)
    assert config.sample_x_pixel_size_keys == ("technique/optic/my_sample_pixel_size",)
    assert config.sample_y_pixel_size_keys == ("technique/optic/my_sample_pixel_size2",)
    assert config.detector_x_pixel_size_keys == ("technique/scan/detector_pixel_size",)
    assert config.detector_y_pixel_size_keys == ("technique/scan/detector_pixel_size2",)
    assert config.sample_detector_distance_keys == (
        "technique/scan/my_sample_detector_distance",
    )
    assert config.source_sample_distance_keys == (
        "technique/scan/source_my_sample_distance",
    )
    # entries and titles section
    assert {url.path() for url in config.entries} == {
        DataUrl(data_path="/1.1", scheme="silx").path(),
        DataUrl(data_path="/3.1", scheme="silx").path(),
    }
    assert {url.path() for url in config.sub_entries_to_ignore} == {
        DataUrl(data_path="/2.1", scheme="silx").path()
    }
    assert config.init_titles == ("my_tomo:basic",)
    assert config.zseries_init_titles == ("my_tomo:zseries",)
    assert config.multitomo_init_titles == ("my_tomo:pcotomo",)
    assert config.dark_titles == ("my dark images",)
    assert config.flat_titles == ("my flat",)
    assert config.projection_titles == ("my projections",)
    assert config.alignment_titles == ("my static images",)
    # frame type section
    assert config.data_scans == ()
    assert config.default_data_copy is True
    # multitomo section
    assert config.start_angle_offset_in_degree == 24.2
    assert config.n_nxtomo == 100
    assert config.angle_interval_in_degree == 180
    assert config.shift_angles is True
    # extra params
    assert config.energy_kev == 12.5
    assert config.y_detector_pixel_size_m == 2.3e-6


def test_moving_to_pydantic_file_with_data_scans():
    resources = importlib_resources.files(_h52nx_config_files.__name__)
    ref_file = os.path.join(resources, "config_file_with_data_scans.cfg")
    assert os.path.exists(ref_file)
    txt_parser = ConfigParser(allow_no_value=True)
    txt_parser.read(ref_file)

    old_config = H52nxModel(
        general_section=txt_parser["GENERAL_SECTION"],
        keys_section=txt_parser["KEYS_SECTION"],
        entries_and_titles_section=txt_parser["ENTRIES_AND_TITLES_SECTION"],
        frame_type_section=txt_parser["FRAME_TYPE_SECTION"],
        multitomo_section=txt_parser["MULTITOMO_SECTION"],
        extra_params_section=txt_parser["EXTRA_PARAMS_SECTION"],
    )
    old_dict = {key.upper(): value for key, value in old_config.model_dump().items()}

    config = H52nxModel(
        general_section=GeneralSection(),
        keys_section=KeysSection(),
        entries_and_titles_section=EntriesAndTitlesSection(),
        frame_type_section=FrameTypeSection(
            data_scans=(
                FrameGroup(
                    url="silx:///path/to/file?/path/to/scan/node",
                    frame_type="projections",
                ),
                FrameGroup(
                    url="/path_relative_to_file",
                    frame_type="darks",
                    copy_data=True,
                ),
            )
        ),
        multitomo_section=MultiTomoSection(),
        extra_params_section=ExtraParamsSection(),
    )
    new_dict = {key.upper(): value for key, value in config.model_dump().items()}
    assert new_dict == old_dict


def test_generate_default_hdf5_config():
    """
    Insure we can generate a default configuration
    """
    config = H52nxModel()
    config.input_file = "toto.h5"
    config.output_file = "toto.nx"
    output = config.to_dict()

    assert isinstance(output, dict)
    # check titles values
    titles_dict = output["ENTRIES_AND_TITLES_SECTION"]
    assert titles_dict["init_titles"] == settings.Tomo.H5.INIT_TITLES
    assert titles_dict["zseries_init_titles"] == settings.Tomo.H5.ZSERIE_INIT_TITLES
    assert titles_dict["projection_titles"] == settings.Tomo.H5.PROJ_TITLES
    assert titles_dict["flat_titles"] == settings.Tomo.H5.FLAT_TITLES
    assert titles_dict["dark_titles"] == settings.Tomo.H5.DARK_TITLES
    assert titles_dict["alignment_titles"] == settings.Tomo.H5.ALIGNMENT_TITLES
    # check sample pixel size
    keys_dict = output["KEYS_SECTION"]
    assert (
        keys_dict["sample_x_pixel_size_keys"]
        == settings.Tomo.H5.SAMPLE_X_PIXEL_SIZE_KEYS
    )
    assert (
        keys_dict["sample_y_pixel_size_keys"]
        == settings.Tomo.H5.SAMPLE_Y_PIXEL_SIZE_KEYS
    )
    assert (
        keys_dict["detector_x_pixel_size_keys"]
        == settings.Tomo.H5.DETECTOR_X_PIXEL_SIZE_KEYS
    )
    assert (
        keys_dict["detector_y_pixel_size_keys"]
        == settings.Tomo.H5.DETECTOR_Y_PIXEL_SIZE_KEYS
    )
    # check translation
    assert keys_dict["sample_x_keys"] == settings.Tomo.H5.SAMPLE_X_KEYS
    assert keys_dict["sample_y_keys"] == settings.Tomo.H5.SAMPLE_Y_KEYS
    assert keys_dict["translation_z_keys"] == settings.Tomo.H5.TRANSLATION_Z_KEYS
    # others
    if len(settings.Tomo.H5.VALID_CAMERA_NAMES) == 0:
        assert keys_dict["valid_camera_names"] == ()
    else:
        assert keys_dict["valid_camera_names"] == settings.Tomo.H5.VALID_CAMERA_NAMES
    assert keys_dict["rotation_angle_keys"] == settings.Tomo.H5.ROT_ANGLE_KEYS
    assert keys_dict["diode_keys"] == settings.Tomo.H5.DIODE_KEYS
    assert keys_dict["translation_y_keys"] == settings.Tomo.H5.TRANSLATION_Y_KEYS
    assert keys_dict["exposure_time_keys"] == settings.Tomo.H5.ACQ_EXPO_TIME_KEYS

    # check input and output file
    general_information = output["GENERAL_SECTION"]
    assert general_information["input_file"] == "toto.h5"
    assert general_information["output_file"] == "toto.nx"


def test_hdf5config_to_dict():
    """test the `to_dict` function"""
    output_dict = H52nxModel().to_nested_model().model_dump()
    # check sections
    for section in (
        "general_section",
        "keys_section",
        "extra_params_section",
        "frame_type_section",
        "entries_and_titles_section",
    ):
        assert section in output_dict
    # check titles keys
    for key in (
        "alignment_titles",
        "projection_titles",
        "zseries_init_titles",
        "init_titles",
        "flat_titles",
        "dark_titles",
    ):
        assert key in output_dict["entries_and_titles_section"]
    # check sample pixel size
    for key in (
        "sample_x_pixel_size_keys",
        "sample_y_pixel_size_keys",
        "detector_x_pixel_size_keys",
        "detector_y_pixel_size_keys",
    ):
        assert key in output_dict["keys_section"]
    # translation keys
    for key in (
        "sample_x_keys",
        "sample_y_keys",
        "translation_z_keys",
    ):
        assert key in output_dict["keys_section"]
    # others
    for key in (
        "valid_camera_names",
        "rotation_angle_keys",
        "translation_y_keys",
        "diode_keys",
        "exposure_time_keys",
    ):
        assert key in output_dict["keys_section"]


def test_hdf5config_from_dict():
    """test the `from_dict` function"""
    valid_camera_names = ("frelon", "totocam")
    alignment_titles = ("this is an alignment",)
    sample_x_keys = ("tx", "x")
    config = H52nxModel.from_dict(
        {
            "KEYS_SECTION": {
                "valid_camera_names": valid_camera_names,
                "sample_x_keys": sample_x_keys,
            },
            "ENTRIES_AND_TITLES_SECTION": {"alignment_titles": alignment_titles},
        }
    )
    assert config.valid_camera_names == valid_camera_names
    assert config.alignment_titles == alignment_titles
    assert config.sample_x_keys == sample_x_keys


def test_hdf5config_from_dict_lowercase():
    """Test `from_dict` method with lower case sections"""
    ref_dict = H52nxModel().to_dict()
    lower_dict = {k.lower(): v for k, v in ref_dict.items()}

    config = H52nxModel.from_dict(lower_dict)
    assert config.to_dict() == ref_dict


def test_hdf5config_raises_errors():
    """
    Insure a type error is raised if an invalid type is passed to the
    HDF5Config class
    :return:
    """
    with pytest.raises(TypeError):
        H52nxModel.from_dict({"ENTRIES_AND_TITLES_SECTION": {"dark_titles": 1213}})


def test_hdf5config_to_and_from_cfg_file(tmp_path):
    """
    Insure we can dump the configuration to a .cfg file and that we
    can read it back
    """
    file_path = os.path.join(tmp_path, "output_file.cfg")
    input_config = H52nxModel()
    input_config.to_cfg_file(file_path)
    assert os.path.exists(file_path)
    loaded_config = H52nxModel.from_cfg_file(file_path=file_path)
    assert isinstance(loaded_config, H52nxModel)
