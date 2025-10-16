# coding: utf-8

"""
Application to create a default configuration file to be used by blissfluo2nx application.

.. program-output:: nxtomomill blissfluo-config --help

"""

import argparse
import logging

from nxtomomill.models.blissfluo2nx import BlissFluo2nxModel

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


def main(argv):
    """ """
    parser = argparse.ArgumentParser(description="Create a default configuration file")
    parser.add_argument("output_file", help="output .cfg file")
    parser.add_argument(
        "--level",
        "--option-level",
        help="Level of options to embed in the configuration file. Can be 'required' or 'advanced'.",
        default="required",
    )

    options = parser.parse_args(argv[1:])

    configuration = BlissFluo2nxModel()
    configuration.to_cfg_file(file_path=options.output_file)
