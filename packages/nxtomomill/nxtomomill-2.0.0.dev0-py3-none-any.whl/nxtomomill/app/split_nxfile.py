"""
Application to split a file containing several NXtomo entries into several files containing each a single NXtomo

.. program-output:: split-nxfile --help

"""

import os
import argparse
import logging
import string

from nxtomo.application.nxtomo import NXtomo
from tomoscan.esrf.scan.nxtomoscan import NXtomoScan
from silx.io.utils import open as open_hdf5

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


def main(argv):
    """ """
    parser = argparse.ArgumentParser(
        description="split a file containing several NXtomo (at root level) into multiple files containing each a single NXtomo"
    )
    parser.add_argument(
        "input_file",
        help="File containing NXtomo to be split into several files",
        nargs="?",
    )
    parser.add_argument(
        "output_file_pattern",
        help="output file pattern. Must contain `{entry_name}` or `{index}` pattern to make sure it is unique",
        default="{input_file_name}_{entry_name}.nx",
        nargs="?",
    )

    parser.add_argument(
        "--overwrite",
        help="Do not ask for user permission to overwrite output files",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--duplicate-data",
        help="Make all NXtomo free of any external link. As a result this will duplicate data",
        nargs="?",
    )

    options = parser.parse_args(argv[1:])
    output_file_pattern = options.output_file_pattern
    if "{input_file_name}" in output_file_pattern:
        output_file_pattern = output_file_pattern.format(
            {
                "output_file_pattern": os.path.splitext(options.input_file),
            }
        )

    split(
        input_file=options.input_file,
        output_file_pattern=output_file_pattern,
        overwrite=options.overwrite,
    )


def split(
    input_file: str,
    output_file_pattern: str,
    overwrite: bool = False,
    duplicate_data: bool = False,
) -> tuple:
    """
    :param input_file: path to the file to be splitted
    :param output_file_pattern: pattern of the file to create. Must contain either `{entry_name}` or `{index}`
    :param overwrite: can we overwrite output file if alread exists

    :return: tuple of identifier of all the NXtomo generated
    """

    def get_output_file(index: int, entry_name: str, pattern: str) -> str:
        """
        treat 'pattern' to create the expected output file
        """
        keywords = {
            "entry_name": entry_name,
            "index": index,
        }

        # filter necessary keywords
        def get_necessary_keywords():
            formatter = string.Formatter()
            return [field for _, field, _, _ in formatter.parse(pattern) if field]

        requested_keywords = get_necessary_keywords()

        def keyword_needed(pair):
            keyword, _ = pair
            return keyword in requested_keywords

        keywords = dict(filter(keyword_needed, keywords.items()))
        if len(keywords) == 0:
            raise ValueError(
                "pattern should at least contains keywords '{index}' or '{entry_name}' to be format. Else unable to create a unique file per NXtomo"
            )
        return os.path.abspath(pattern.format(**keywords))

    if duplicate_data:
        detector_data_as = "as_numpy_array"
    else:
        detector_data_as = "as_data_url"
    result = []
    with open_hdf5(input_file) as h5f:
        for i_entry, entry in enumerate(h5f.keys()):
            try:
                nx_tomo = NXtomo().load(
                    input_file, entry, detector_data_as=detector_data_as
                )
            except Exception as e:
                _logger.error(
                    f"Fail to treat entry {entry}. Error is {e}. Is this a valid Nxtomo ?"
                )
            else:
                output_file = get_output_file(
                    index=i_entry, entry_name=entry, pattern=output_file_pattern
                )
                dirname = os.path.dirname(output_file)
                if dirname and not os.path.exists(dirname):
                    os.makedirs(dirname)
                nx_tomo.save(
                    file_path=output_file, data_path=entry, overwrite=overwrite
                )
                result.append(NXtomoScan(output_file, entry))

    return tuple(result)
