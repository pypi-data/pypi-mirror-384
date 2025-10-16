# coding: utf-8

"""
Application to create a default configuration file to be used by h52nx application.

.. program-output:: nxtomomill h5-config --help

For a complete tutorial you can have a look at: :ref:`Tomoh52nx`
"""

import argparse
import logging

from nxtomomill.io import TomoHDF5Config

logging.basicConfig(level=logging.INFO)


def main(argv):
    """ """
    parser = argparse.ArgumentParser(description="Create a default configuration file")
    parser.add_argument("output_file", help="output .cfg file")
    parser.add_argument(
        "--from-title-names",
        help="Provide minimalistic configuration to make a conversion from "
        "titles names. (FRAME TYPE section is ignored). \n"
        "Exclusive with `from-scan-urls` option",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--from-scan-urls",
        help="Provide minimalistic configuration to make a conversion from "
        "scan urls. (ENTRIES and TITLES section is ignored).\n"
        "Exclusive with `from-title-names` option",
        action="store_true",
        default=False,
    )

    options = parser.parse_args(argv[1:])
    if options.from_title_names:
        filter_sections = ("frame_type_section",)
    elif options.from_scan_urls:
        filter_sections = ("entries_and_titles_section",)
    else:
        filter_sections = ()

    configuration = TomoHDF5Config()
    configuration.to_cfg_file(
        file_path=options.output_file, filter_sections=filter_sections
    )
