# coding: utf-8

import os
import pint
from tempfile import TemporaryDirectory

import pytest
import logging

# from pydantic import ValidateError
import importlib.resources as importlib_resources
from configparser import ConfigParser

from nxtomo.nxobject.nxdetector import FieldOfView
from nxtomo.nxobject.nxsource import ProbeType, SourceType

from nxtomomill import settings
from nxtomomill.models.edf2nx import EDF2nxModel, generate_default_edf_config
from nxtomomill.tests.resources import edf2nx_config_files as _edf2nx_config_files
from nxtomomill.utils import FileExtension
from nxtomomill.models.utils import PathType


_ureg = pint.get_application_registry()


def test_moving_to_pydantic_default_config_file():
    """
    test that the default nxtomomill config generated before moving to pydantic is properly interpreted.
    This ignores any comments.
    """
    resources = importlib_resources.files(_edf2nx_config_files.__name__)
    ref_file = os.path.join(resources, "default_file_before_moving_to_pydantic.cfg")
    assert os.path.exists(ref_file)
    txt_parser = ConfigParser(allow_no_value=True)
    txt_parser.read(ref_file)

    old_config = EDF2nxModel(
        general_section=txt_parser["GENERAL_SECTION"],
        edf_keys_section=txt_parser["EDF_KEYS_SECTION"],
        dark_and_flat_section=txt_parser["DARK_AND_FLAT_SECTION"],
        sample_section=txt_parser["SAMPLE_SECTION"],
        unit_section=txt_parser["UNIT_SECTION"],
        source_section=txt_parser["SOURCE_SECTION"],
        detector_section=txt_parser["DETECTOR_SECTION"],
    )
    old_dict = {key.upper(): value for key, value in old_config.model_dump().items()}

    new_dict = generate_default_edf_config()
    assert new_dict == old_dict


def test_TomoEDFConfig_default_config():
    """insure default configuration generation works"""
    with TemporaryDirectory() as folder:
        file_path = os.path.join(folder, "config.cfg")
        assert not os.path.exists(file_path)
        config = generate_default_edf_config()
        assert isinstance(config, dict)
        EDF2nxModel().to_cfg_file(file_path=file_path)
        assert os.path.exists(file_path)


def test_moving_to_pydantic_modified_config_file():
    """
    test that an old nxtomomill edf-config file generated before moving to pydantic is properly interpreted.
    This ignores any comments.
    """
    resources = importlib_resources.files(_edf2nx_config_files.__name__)
    ref_file = os.path.join(resources, "fully_modified_file_before_moving.cfg")
    assert os.path.exists(ref_file)

    config: EDF2nxModel = EDF2nxModel.from_cfg_file(ref_file)
    assert config.input_folder == "my_folder"
    assert config.output_file == "my_file.nx"
    assert config.overwrite is True
    assert config.delete_edf_source_files is True
    assert config.output_checks == ("check_1",)
    assert config.file_extension == FileExtension.NXS
    assert config.dataset_basename == "dataset_basename"
    assert config.dataset_info_file == "dataset_info_file.info"
    assert config.log_level == logging.INFO
    assert config.title == "my_title"
    assert config.patterns_to_ignores == ("_slice_", "_pattern_")
    assert config.duplicate_data is False
    assert config.external_link_type is PathType.ABSOLUTE

    assert config.motor_position_keys == ("motor_pos_key",)
    assert config.motor_mne_keys == ("motor_mne_key",)
    assert config.rotation_angle_keys == ("srotatation",)
    assert config.x_translation_keys == ("stx",)
    assert config.y_translation_keys == ("sty",)
    assert config.z_translation_keys == ("stz",)

    assert config.dark_names_prefix == ("prefix_1", "prefix_2")
    assert config.flat_names_prefix == ("prefix_3", "prefix_4")

    assert config.pixel_size_unit == _ureg.meter
    assert config.sample_detector_distance_unit == _ureg.meter
    assert config.energy_unit == _ureg.GeV
    assert config.x_translation_unit == _ureg.meter
    assert config.y_translation_unit == _ureg.meter
    assert config.z_translation_unit == _ureg.meter
    assert config.machine_current_unit == _ureg.kA

    assert config.sample_name == "my_sample"
    assert config.force_angle_calculation is False
    assert config.angle_calculation_endpoint is True
    assert config.angle_calculation_rev_neg_scan_range is False

    assert config.instrument_name == "my_instrument"
    assert config.source_name == "my_source"
    assert config.source_type == SourceType.SPALLATION_NEUTRON
    assert config.source_probe == ProbeType.NEUTRON

    assert config.field_of_view == FieldOfView.HALF


def test_TomoEDFConfig_setters():
    """test the different setters and getter of the EDFTomoConfig"""
    config = EDF2nxModel()

    # try to test a new attribut (insure class is frozeen)
    with pytest.raises(ValueError):
        config.new_attrs = "toto"

    # test general section setters
    config.input_folder = "my_folder"
    config.output_file = "my_nx.nx"

    config.file_extension = ".nx"

    with pytest.raises(ValueError):
        config.dataset_basename = 12.0
    config.dataset_basename = None
    config.dataset_basename = "test_"

    with pytest.raises(ValueError):
        config.dataset_info_file = 12.3
    config.dataset_info_file = None
    config.dataset_info_file = "my_info_file.info"

    config.overwrite = True

    with pytest.raises(ValueError):
        config.title = 12.0
    config.title = None
    config.title = "my title"

    with pytest.raises(ValueError):
        config.patterns_to_ignores = 12.0
    config.patterns_to_ignores = ("toto",)

    # test header keys + dark and flat setters
    attributes_value = {
        "motor_position_keys": settings.Tomo.EDF.MOTOR_POS,
        "motor_mne_keys": settings.Tomo.EDF.MOTOR_MNE,
        "rotation_angle_keys": settings.Tomo.EDF.ROT_ANGLE,
        "dark_names": settings.Tomo.EDF.DARK_NAMES,
        "flat_names": settings.Tomo.EDF.REFS_NAMES,
    }
    for attr, key in attributes_value.items():
        setattr(config, attr, key)
        with pytest.raises((TypeError, ValueError)):
            setattr(config, attr, "toto")
        with pytest.raises((TypeError, ValueError)):
            setattr(config, attr, 12.20)
        with pytest.raises((TypeError, ValueError)):
            setattr(config, attr, (12.20,))

    # test units setters
    attributes_value = {
        "pixel_size_unit": _ureg.micrometer,
        "distance_unit": _ureg.meter,
        "energy_unit": _ureg.keV,
        "x_translation_unit": _ureg.meter,
        "y_translation_unit": _ureg.meter,
        "z_translation_unit": _ureg.meter,
    }
    for attr, key in attributes_value.items():
        # test providing an instance of a unit
        setattr(config, attr, key)
        # test providing a sting if of a unit
        setattr(config, attr, str(key))
        with pytest.raises(TypeError):
            setattr(config, attr, None)
        with pytest.raises(TypeError):
            setattr(config, attr, 12.0)

    # test sample setters
    config.sample_name = None
    with pytest.raises(ValueError):
        config.sample_name = (12,)
    with pytest.raises(ValueError):
        config.sample_name = 12.0
    config.sample_name = "my sample"

    with pytest.raises(ValueError):
        config.force_angle_calculation = "toto"
    config.force_angle_calculation = True

    with pytest.raises(ValueError):
        config.angle_calculation_endpoint = "toto"
    config.angle_calculation_endpoint = True

    with pytest.raises(ValueError):
        config.angle_calculation_rev_neg_scan_range = "toto"
    config.angle_calculation_rev_neg_scan_range = False

    # test source setters
    config.instrument_name = None
    config.instrument_name = "BMXX"
    with pytest.raises(ValueError):
        config.instrument_name = 12.3

    config.source_name = None
    config.source_name = "ESRF"
    with pytest.raises(ValueError):
        config.source_name = 12.2
    config.source_name = "XFEL"

    config.source_type = None
    config.source_type = SourceType.FIXED_TUBE_X_RAY.value
    config.source_type = SourceType.FIXED_TUBE_X_RAY
    with pytest.raises(ValueError):
        config.source_type = "trsts"
    with pytest.raises(ValueError):
        config.source_type = 123

    config.source_probe = None
    config.source_probe = ProbeType.ELECTRON
    config.source_probe = "positron"
    with pytest.raises(ValueError):
        config.source_probe = 123

    # test detector setters
    config.field_of_view = None
    with pytest.raises(ValueError):
        config.field_of_view = 12
    with pytest.raises(ValueError):
        config.field_of_view = "toto"
    config.field_of_view = FieldOfView.FULL.value
    config.field_of_view = FieldOfView.HALF

    config_dict = config.to_dict()
    general_section_dict = config_dict["GENERAL_SECTION"]
    assert general_section_dict["input_folder"] == "my_folder"
    assert general_section_dict["output_file"] == "my_nx.nx"
    assert general_section_dict["file_extension"] == ".nx"
    assert general_section_dict["overwrite"] is True
    assert general_section_dict["dataset_basename"] == "test_"
    assert general_section_dict["dataset_info_file"] == "my_info_file.info"
    assert general_section_dict["title"] == "my title"
    assert general_section_dict["patterns_to_ignores"] == ("toto",)

    edf_headers_section_dict = config_dict["EDF_KEYS_SECTION"]
    assert (
        edf_headers_section_dict["motor_position_keys"] == settings.Tomo.EDF.MOTOR_POS
    )
    assert edf_headers_section_dict["motor_mne_keys"] == settings.Tomo.EDF.MOTOR_MNE
    assert edf_headers_section_dict["x_translation_keys"] == settings.Tomo.EDF.X_TRANS
    assert edf_headers_section_dict["y_translation_keys"] == settings.Tomo.EDF.Y_TRANS
    assert edf_headers_section_dict["z_translation_keys"] == settings.Tomo.EDF.Z_TRANS
    assert (
        edf_headers_section_dict["rotation_angle_keys"] == settings.Tomo.EDF.ROT_ANGLE
    )

    dark_flat_section_dict = config_dict["DARK_AND_FLAT_SECTION"]
    assert dark_flat_section_dict["dark_names_prefix"] == settings.Tomo.EDF.DARK_NAMES
    assert dark_flat_section_dict["flat_names_prefix"] == settings.Tomo.EDF.REFS_NAMES

    units_section_dict = config_dict["UNIT_SECTION"]
    assert units_section_dict["pixel_size_unit"] == str(_ureg.micrometer)
    assert units_section_dict["sample_detector_distance_unit"] == str(_ureg.meter)
    assert units_section_dict["energy_unit"] == str(_ureg.keV)
    assert units_section_dict["x_translation_unit"] == str(_ureg.meter)
    assert units_section_dict["y_translation_unit"] == str(_ureg.meter)
    assert units_section_dict["z_translation_unit"] == str(_ureg.meter)

    sample_section_dict = config_dict["SAMPLE_SECTION"]
    assert sample_section_dict["sample_name"] == "my sample"
    assert sample_section_dict["force_angle_calculation"] is True
    assert sample_section_dict["angle_calculation_endpoint"] is True
    assert sample_section_dict["angle_calculation_rev_neg_scan_range"] is False

    source_section_dict = config_dict["SOURCE_SECTION"]
    assert source_section_dict["instrument_name"] == "BMXX"
    assert source_section_dict["source_name"] == "XFEL"
    assert source_section_dict["source_type"] == SourceType.FIXED_TUBE_X_RAY.value

    detector_section_dict = config_dict["DETECTOR_SECTION"]
    assert detector_section_dict["field_of_view"] == FieldOfView.HALF.value
