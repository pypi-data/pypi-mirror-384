# coding: utf-8

import os
import pytest

from nxtomomill.io.config.confighandler import TomoHDF5ConfigHandler
from nxtomomill.io.config.hdf5config import TomoHDF5Config
from nxtomomill.models.h52nx.FrameGroup import FrameGroup


class _ARParseMock(object):
    def __init__(self):
        self.config_file = None
        self.input_file = None
        self.output_file = None
        self.set_params = None
        self.alignment_titles = None
        self.projection_titles = None
        self.flat_titles = None
        self.dark_titles = None
        self.zseries_init_titles = None
        self.multitomo_init_titles = None
        self.init_titles = None
        self.back_and_forth_init_titles = None
        self.sample_x_pixel_size_keys = None
        self.sample_y_pixel_size_keys = None
        self.exposure_time_keys = None
        self.rotation_angle_keys = None
        self.valid_camera_names = None
        self.translation_z_keys = None
        self.sample_y_keys = None
        self.sample_x_keys = None
        self.request_input = False
        self.raises_error = False
        self.default_data_copy = None
        self.sub_entries_to_ignore = None
        self.entries = None
        self.debug = False
        self.overwrite = False
        self.single_file = False
        self.no_master_file = False
        self.file_extension = None
        self.field_of_view = None
        self.sample_detector_distance_keys = None


def test_creation_from_config_file(tmp_path):
    options = _ARParseMock()
    with pytest.raises(ValueError):
        TomoHDF5ConfigHandler(argparse_options=options)

    input_file_path = os.path.join(tmp_path, "output_file.cfg")
    input_config = TomoHDF5Config()
    input_config.to_cfg_file(input_file_path)

    options.config_file = input_file_path

    # insure this is valid if we add an input file and an output file
    # from the command line
    options.input_file = "toto.h5"
    options.output_file = "toto.nx"
    TomoHDF5ConfigHandler(argparse_options=options)

    # or if we provide them from the configuration file
    options.input_file = None
    options.output_file = None
    input_config.input_file = "toto.h5"
    input_config.output_file = "toto.nx"
    input_config.to_cfg_file(input_file_path)
    TomoHDF5ConfigHandler(argparse_options=options)


def write_and_read_configuration(folder, data_urls):
    configuration = TomoHDF5Config()
    configuration.data_scans = data_urls
    configuration.input_file = "toto.h5"
    configuration.output_file = "toto.nx"

    file_path = os.path.join(folder, "h52nx.cfg")
    configuration.to_cfg_file(file_path=file_path)

    options = _ARParseMock()
    options.config_file = file_path
    config_handler = TomoHDF5ConfigHandler(options)
    return config_handler.configuration


def test_local_paths(tmp_path):
    res_config = write_and_read_configuration(
        folder=tmp_path,
        data_urls=(
            FrameGroup(url="/entry0000/data/flats", frame_type="flat"),
            FrameGroup(url="/entry0000/data/projection1", frame_type="projection"),
            FrameGroup(url="/entry0000/data/projection2", frame_type="projection"),
            FrameGroup(url="/entry0000/data/alignment1", frame_type="alignment"),
            FrameGroup(url="/entry0000/data/alignment2", frame_type="alignment"),
            FrameGroup(url="/entry0000/data/darks", frame_type="dark"),
        ),
    )
    assert res_config is not None
    assert len(res_config.data_scans) == 6
    # check flats
    flat_url = res_config.data_scans[0].url
    assert flat_url.file_path() in (None, "")
    assert flat_url.data_path() == "/entry0000/data/flats"
    assert flat_url.data_slice() in (None, "")
    # check projections
    projection_url_0 = res_config.data_scans[1].url
    projection_url_1 = res_config.data_scans[2].url
    assert projection_url_0.file_path() in (None, "")
    assert projection_url_0.data_path() == "/entry0000/data/projection1"
    assert projection_url_0.data_slice() is None
    assert projection_url_1.file_path() in (None, "")
    assert projection_url_1.data_path() == "/entry0000/data/projection2"
    assert projection_url_1.data_slice() is None

    # check darks
    dark_url = res_config.data_scans[-1].url
    assert dark_url.file_path() in (None, "")
    assert dark_url.data_path(), "/entry0000/data/darks"
    assert dark_url.data_slice() is None

    # check alignments
    alignment_url_0 = res_config.data_scans[3].url
    alignment_url_1 = res_config.data_scans[4].url
    assert alignment_url_0.file_path() in (None, "")
    assert alignment_url_0.data_path(), "/entry0000/data/alignment1"
    assert alignment_url_0.data_slice() is None
    assert alignment_url_1.data_path() == "/entry0000/data/alignment2"


def test_external_paths(tmp_path):
    """
    Check that DataUrl are handled.

    Warning: this also check data_slices but those are not handled.
    """
    res_config = write_and_read_configuration(
        folder=tmp_path,
        data_urls=(
            FrameGroup(
                frame_type="flat",
                url="silx:///myfile.h5?path=/entry0000/data/flats",
            ),
            FrameGroup(
                frame_type="dark",
                url="h5py:///data/file2.hdf5?path=/entry0000/data/darks",
            ),
            FrameGroup(frame_type="proj", url="h5py:///data/file3.hdf5?path=/data"),
            FrameGroup(
                frame_type="proj",
                url="silx:///data/file2.hdf5?path=/entry0000/data/projection2&slice=5:100",
            ),
            FrameGroup(
                frame_type="alignment",
                url="silx:///myfile.h5?path=/entry0000/data/alignment&slice=5",
            ),
        ),
    )
    assert res_config is not None
    assert len(res_config.data_scans) == 5
    # check flats
    flat_url = res_config.data_scans[0]
    assert flat_url.url.file_path() == "/myfile.h5"
    assert flat_url.url.data_path() == "/entry0000/data/flats"
    assert flat_url.url.data_slice() is None
    assert flat_url.url.scheme() == "silx"

    # check projections
    projection_url_0 = res_config.data_scans[2].url
    projection_url_1 = res_config.data_scans[3].url
    assert projection_url_0.file_path() == "/data/file3.hdf5"
    assert projection_url_0.data_path() == "/data"
    assert projection_url_0.data_slice() is None
    assert projection_url_0.scheme() == "h5py"
    assert projection_url_1.file_path() == "/data/file2.hdf5"
    assert projection_url_1.data_path() == "/entry0000/data/projection2"
    assert projection_url_1.data_slice() == (slice(5, 100),)
    assert projection_url_1.scheme() == "silx"

    # check darks
    dark_url = res_config.data_scans[1].url
    assert dark_url.file_path() == "/data/file2.hdf5"
    assert dark_url.data_path() == "/entry0000/data/darks"
    assert dark_url.data_slice() is None
    assert dark_url.scheme() == "h5py"

    # check alignments
    alignment_url_0 = res_config.data_scans[4].url
    assert alignment_url_0.file_path() == "/myfile.h5"
    assert alignment_url_0.data_path() == "/entry0000/data/alignment"
    assert alignment_url_0.data_slice() == (5,)
    assert alignment_url_0.scheme() == "silx"
