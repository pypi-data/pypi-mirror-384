# coding: utf-8

"""
Application to convert a fluo-tomo dataset, after PyMCA (https://www.silx.org/doc/PyMca/dev/index.html) fit, into an hdf5/nexus file.

.. program-output:: nxtomomill fluo2nx --help

"""

import argparse
import logging

from nxtomomill import converter
from nxtomomill.models.blissfluo2nx import BlissFluo2nxModel

from tqdm import tqdm

logging.basicConfig(level=logging.INFO)


def main(argv):
    """ """
    parser = argparse.ArgumentParser(
        description="Converts Bliss fluo-tomo data (after PyMca fit) "
        "to hdf5 - nexus compliant file format."
    )
    parser.add_argument(
        "--ewoksfluo_filename",
        help="Path to the ewoksfluo-generated (h5) filename taht contains fitted XRF data.",
    )
    parser.add_argument(
        "--output_file",
        help="File produced by the converter. '.nx' extension recommended.",
    )
    parser.add_argument(
        "--detectors",
        nargs="*",
        default=list(),
        help="Define a list of (real or virtual) detector names used for the exp (space separated values - no comma). E.g. 'falcon xmap'. If not specified, all detectors are processed.",
    )
    parser.add_argument(
        "--dimension",
        help="2 for 2D XRFCT, 3 for 3D XRFCT. Default is 3.",
        default=3,
    )
    parser.add_argument(
        "--config",
        "--configuration-file",
        "--configuration",
        default=None,
        help="file containing the full configuration to convert from (PyMCA-computed) fluo projections to nexus. "
        "Default configuration file can be created from `nxtomomill fluo-config` command",
    )

    parser.add_argument(
        "--overwrite",
        default=False,
        action="store_true",
        help="If the output file exists then overwrite.",
    )

    options = parser.parse_args(argv[1:])
    config = BlissFluo2nxModel()
    if options.config is not None:
        config = config.from_cfg_file(options.config)

    check_input = {
        "ewoksfluo_filename": (
            options.ewoksfluo_filename,
            config.general_section.ewoksfluo_filename,
        ),
        "output file": (options.output_file, config.general_section.output_file),
    }
    for input_name, (opt_value, config_value) in check_input.items():
        if (
            opt_value is not None
            and config_value is not None
            and opt_value != config_value
        ):
            raise ValueError(
                f"two values for {input_name} are provided from arguments and configuration file ({opt_value, config_value})"
            )

    if options.ewoksfluo_filename is not None:
        config.general_section.ewoksfluo_filename = options.ewoksfluo_filename
    if options.output_file is not None:
        config.general_section.output_file = options.output_file
    if options.detectors is not None:
        config.general_section.detector_names = options.detectors
    config.general_section.dimension = options.dimension
    config.general_section.overwrite = options.overwrite

    converter.from_blissfluo_to_nx(
        configuration=config,
        progress=tqdm("blissfluo2nx"),
    )
