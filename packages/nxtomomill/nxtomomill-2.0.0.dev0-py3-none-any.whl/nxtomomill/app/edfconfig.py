# coding: utf-8

"""
Application to create a default configuration file to be used by edf2nx application.

.. program-output:: nxtomomill edf-config --help

For a complete tutorial you can have a look at :ref:`edf2nxtutorial`
"""

import argparse
import logging

from nxtomomill.io import TomoEDFConfig

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
    if options.level != "required":
        _logger.warning("Level option has been removed. Will be ignored")

    configuration = TomoEDFConfig()
    configuration.to_cfg_file(file_path=options.output_file)
