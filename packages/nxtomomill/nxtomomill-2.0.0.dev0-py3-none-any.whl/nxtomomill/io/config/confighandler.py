# coding: utf-8

"""
contains the HDF5ConfigHandler
"""

from __future__ import annotations

import logging
import os

from nxtomomill.converter.hdf5.utils import get_default_output_file

from .hdf5config import TomoHDF5Config

_logger = logging.getLogger(__name__)

__all__ = [
    "SETTABLE_PARAMETERS_UNITS",
    "SETTABLE_PARAMETERS_TYPE",
    "SETTABLE_PARAMETERS",
    "TomoHDF5ConfigHandler",
]

SETTABLE_PARAMETERS_UNITS = {
    "energy": "kev",
    "x_pixel_size": "m",
    "y_pixel_size": "m",
    "detector_sample_distance": "m",
}

SETTABLE_PARAMETERS_TYPE = {
    "energy": float,
    "x_pixel_size": float,
    "y_pixel_size": float,
    "detector_sample_distance": float,
}

SETTABLE_PARAMETERS = SETTABLE_PARAMETERS_UNITS.keys()


def _extract_param_value(key_values):
    """extract all the key / values elements from the str_list. Expected
    format is `param_1_name param_1_value param_2_name param_2_value ...`

    :param str_list: raw input string as `param_1_name param_1_value
                         param_2_name param_2_value ...`
    :return: dict of tuple (param_name, param_value)
    """
    if len(key_values) % 2 != 0:
        raise ValueError(
            "Expect a pair `param_name, param_value` for each " "parameters"
        )

    def pairwise(it):
        it = iter(it)
        while True:
            try:
                yield next(it), next(it)
            except StopIteration:
                # no more elements in the iterator
                return

    res = {}
    for name, value in pairwise(key_values):
        if name not in SETTABLE_PARAMETERS:
            raise ValueError(f"parameters {name} is not managed")
        if name in SETTABLE_PARAMETERS_TYPE:
            type_ = SETTABLE_PARAMETERS_TYPE[name]
            if type_ is not None:
                res[name] = type_(value)
                continue
        res[name] = value
    return res


class TomoHDF5ConfigHandler:
    """
    Create a TomoHDF5Config from argparse option provided from the CLI.

    ..warning:: If a configuration file (--config_file) is given then other argparse options will be ignored.
    """

    def __init__(self, argparse_options):
        self._argparse_options = argparse_options
        self._config = None
        self.build_configuration()

    @property
    def configuration(self) -> TomoHDF5Config | None:
        return self._config

    @property
    def argparse_options(self):
        return self._argparse_options

    def build_configuration(self):
        if self.argparse_options.config_file is not None:
            assert isinstance(
                self.argparse_options.config_file, str
            ), f"{self.argparse_options.config_file}, {type(self.argparse_options.config_file)}"
            # from the configuration file
            _logger.warning(
                "A configuration has been given. All other options at the exception of the input and output file will be ignored"
            )
            config = TomoHDF5Config.from_cfg_file(self.argparse_options.config_file)
            if self.argparse_options.input_file is not None:
                config.input_file = self.argparse_options.input_file
            if self.argparse_options.output_file is not None:
                config.output_file = self.argparse_options.output_file
        else:
            # from argparse
            config = TomoHDF5Config()

        options = self.argparse_options
        # check input and output file

        # propagate options defined by the user to the config file.
        # policy: all options when not defined have a default value set to None
        # So we don't have to set twice the default value from the source code (class and argparse)
        for opt_name in (
            "input_file",
            "output_file",
            "file_extension",
            "single_file",
            "no_master_file",
            "overwrite",
            "entries",
            "sub_entries_to_ignore",
            "raises_error",
            "field_of_view",
            "request_input",
            "default_data_copy",
            "sample_x_keys",
            "sample_y_keys",
            "translation_z_keys",
            "sample_detector_distance_keys",
            "valid_camera_names",
            "rotation_angle_keys",
            "exposure_time_keys",
            "sample_x_pixel_size_keys",
            "sample_y_pixel_size_keys",
            "init_titles",
            "zseries_init_titles",
            "multitomo_init_titles",
            "back_and_forth_init_titles",
            "dark_titles",
            "flat_titles",
            "projection_titles",
            "alignment_titles",
        ):
            opt_value = getattr(options, opt_name)
            if opt_value is not None:
                setattr(config, opt_name, opt_value)

        # handle specific use cases
        if options.debug is not None:
            config.log_level = logging.DEBUG

        if options.set_params is not None:
            extra_params = _extract_param_value(options.set_params)
            for param, param_value in extra_params.items():
                setattr(config, param, param_value)

        if config.input_file is None:
            raise ValueError("No input file provided")

        if config.output_file is None:
            if config.file_extension is None:
                err = "If no output file provided you should provide the extension"
                raise ValueError(err)

            config.output_file = get_default_output_file(
                input_file=config.input_file,
                output_file_extension=config.file_extension.value,  # pylint: disable=E1101
            )
        elif os.path.isdir(config.output_file):
            # if the output file is only a directory: consider we want the same file basename with default extension
            # in this directory
            input_file, _ = os.path.splitext(config.input_file)
            config.output_file = os.path.join(
                os.path.abspath(config.output_file),
                os.path.basename(input_file)
                + config.file_extension.value,  # pylint: disable=E1101
            )

        self._config = config
