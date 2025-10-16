# coding: utf-8

import os
import pytest
import logging

from configparser import ConfigParser
import importlib.resources as importlib_resources

from nxtomo.nxobject.nxsource import ProbeType, SourceType

from nxtomomill.models.fluo2nx import Fluo2nxModel, generate_default_fluo_config
from nxtomomill.tests.resources import fluo2nx_config_files as _fluo2nx_config_files
from nxtomomill.utils import FileExtension


def test_moving_to_pydantic_default_config_file():
    """
    test that the default nxtomomill config generated before moving to pydantic is properly interpreted.
    This ignores comments.
    """
    resources = importlib_resources.files(_fluo2nx_config_files.__name__)
    ref_file = os.path.join(resources, "default_file_before_moving_to_pydantic.cfg")
    assert os.path.exists(ref_file)
    txt_parser = ConfigParser(allow_no_value=True)
    txt_parser.read(ref_file)

    old_config = Fluo2nxModel(
        general_section=txt_parser["GENERAL_SECTION"],
        source_section=txt_parser["SOURCE_SECTION"],
    ).to_nested_model()
    old_dict = {key.upper(): value for key, value in old_config.model_dump().items()}

    new_dict = generate_default_fluo_config()
    assert new_dict == old_dict


def test_TomoFluoConfig_default_config(tmp_path):
    """insure default configuration generation works"""
    file_path = os.path.join(tmp_path, "config.cfg")
    assert not os.path.exists(file_path)
    Fluo2nxModel().to_cfg_file(file_path=file_path)
    assert os.path.exists(file_path)


def test_moving_to_pydantic_modified_config_file():
    """
    test that an old nxtomomill fluo-config file generated before moving to pydantic is properly interpreted.
    This ignores any comments.
    """
    resources = importlib_resources.files(_fluo2nx_config_files.__name__)
    ref_file = os.path.join(resources, "fully_modified_file_before_moving.cfg")
    assert os.path.exists(ref_file)

    config = Fluo2nxModel.from_cfg_file(file_path=ref_file)
    assert config.input_folder == "my_folder"
    assert config.output_file == "output_file.nx"
    assert config.dimension == 2
    assert config.detector_names == ("my_detector",)
    assert config.overwrite is True
    assert config.file_extension == FileExtension.H5
    assert config.dataset_basename == "dataset_basename"
    assert config.dataset_info_file == "dataset_info_file.info"
    assert config.log_level == logging.ERROR
    # note: 'title' is part of the configuration file but was never used in the processing
    assert config.patterns_to_ignores == ("_ignore_",)
    assert config.duplicate_data is False
    # note: 'external_link_path is part of the configuration file but was never used in the processing
    assert config.instrument_name == "my_instrument"
    assert config.source_name == "my_source"
    assert config.source_type == SourceType.PULSED_REACTOR_NEUTRON_SOURCE
    assert config.source_probe == ProbeType.POSITRON


def test_TomoFluoConfig_setters():
    """test the different setters and getter of the Fluo2nxModel"""
    config = Fluo2nxModel()

    # try to test a new attribut (insure class is frozeen)
    with pytest.raises(ValueError):
        config.new_attrs = "toto"

    # test general section setters
    with pytest.raises(ValueError):
        config.input_folder = 12.0
    config.input_folder = "my_folder"
    with pytest.raises(ValueError):
        config.output_file = 12.0
    config.output_file = "my_nx.nx"

    config.file_extension = ".nx"

    with pytest.raises(ValueError):
        config.detectors = 12.0
    config.detector_names = ()
    config.detector_names = ("test_",)

    with pytest.raises(ValueError):
        config.dataset_basename = 12.0
    config.dataset_basename = None
    config.dataset_basename = "test_"

    config.overwrite = True

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

    config_dict = config.to_dict()
    general_section_dict = config_dict["GENERAL_SECTION"]
    assert general_section_dict["input_folder"] == "my_folder"
    assert general_section_dict["output_file"] == "my_nx.nx"
    assert general_section_dict["file_extension"] == ".nx"
    assert general_section_dict["overwrite"] is True
    assert general_section_dict["dataset_basename"] == "test_"

    source_section_dict = config_dict["SOURCE_SECTION"]
    assert source_section_dict["instrument_name"] == "BMXX"
    assert source_section_dict["source_name"] == "XFEL"
    assert source_section_dict["source_type"] == SourceType.FIXED_TUBE_X_RAY.value
