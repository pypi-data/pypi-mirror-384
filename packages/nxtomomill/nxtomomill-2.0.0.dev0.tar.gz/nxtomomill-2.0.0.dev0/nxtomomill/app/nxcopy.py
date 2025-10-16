"""application to copy NXtomo(s) from one file to another"""

import argparse
import os
from nxtomo.application.nxtomo import copy_nxtomo_file as copy_nxtomo
from nxtomomill.models.utils import convert_str_to_tuple


def main(argv):
    """ """
    parser = argparse.ArgumentParser(
        description="copy one or several NXtomo to another location"
    )
    parser.add_argument(
        "nexus_file", help="file path to the nexus file containing NXtomo", nargs="?"
    )
    parser.add_argument("output_file", help="output nexus file", nargs="?")
    parser.add_argument(
        "--entry",
        "--entries",
        default=None,
        help="NXtomo path(s) to be copied. If none provided then all NXtomo entries will be copied",
        dest="entries",
    )
    parser.add_argument(
        "--overwrite",
        help="Do not ask for user permission to overwrite output files",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--debug",
        help="Set logs to debug mode",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--remove-vds",
        help="Remove any Virtual dataset to the resulting NXtomo (duplicate detector data - warning: all data will be load in memory before dumping it)",
        action="store_true",
        default=False,
    )

    options = parser.parse_args(argv[1:])
    copy_nxtomo(
        input_file=options.nexus_file,
        output_file=get_output_file(options.output_file, options.nexus_file),
        entries=(
            convert_str_to_tuple(options.entries)
            if options.entries is not None
            else None
        ),
        overwrite=options.overwrite,
        vds_resolution="remove" if options.remove_vds else "update",
    )


def get_output_file(output_file_or_folder, input_file) -> str:
    """compute output file for copying NXtomo from input file or folder"""

    def get_output_file_from_folder():
        return os.path.join(
            output_file_or_folder, os.path.basename(os.path.abspath(input_file))
        )

    if os.path.isdir(output_file_or_folder):
        output_file = get_output_file_from_folder()
    elif (
        os.path.isfile(output_file_or_folder)
        or os.path.splitext(output_file_or_folder)[-1] != ""
    ):
        output_file = output_file_or_folder
    else:
        output_file = get_output_file_from_folder()
    return os.path.abspath(output_file)
