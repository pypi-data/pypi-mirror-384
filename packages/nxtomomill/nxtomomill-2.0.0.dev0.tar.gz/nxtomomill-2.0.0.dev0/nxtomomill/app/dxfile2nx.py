# coding: utf-8

"""
Application to convert from dx file (HDF5) to NXTomo (HDF5) file

.. program-output:: nxtomomill dxfile2nx --help

For a complete tutorial you can have a look at :ref:`dxfile2nxtutorial`

"""

import argparse
import logging
import pint

from nxtomomill import utils
from nxtomomill.converter.dxfile.dxfileconverter import from_dx_to_nx

_logger = logging.getLogger(__name__)
_ureg = pint.get_application_registry()


def convert_2elmts__tuple_to_float(input_str) -> tuple:
    if input_str == (None, None):
        return input_str

    try:
        tmp_str = input_str.replace(" ", "")
        tmp_str = tmp_str.replace(";", ",")
        if tmp_str.startswith("("):
            tmp_str = tmp_str[1:]
        if tmp_str.startswith(")"):
            tmp_str = tmp_str[:-1]
        v1, v2 = tmp_str.split(",")
    except Exception as e:
        raise ValueError(
            f"Unable to convert {input_str} to a tuple of two float. Reason is {e}"
        )
    else:
        return float(v1), float(v2)


def _get_pixel_size(input_str) -> tuple:
    try:
        values = convert_2elmts__tuple_to_float(input_str)
    except ValueError:
        try:
            value = float(input_str)
        except Exception:
            raise ValueError(
                f"Unable to convert {input_str} to pixel size."
                f"Should be provided as a tuple (sample x_pixel_size, sample y_pixel_size) "
                f"or as a single value pixel_size"
            )
        else:
            return value, value
    else:
        return values


def main(argv):
    """ """
    parser = argparse.ArgumentParser(
        description="convert acquisition contained in provided dx file to "
        "NXTomo entry"
    )
    parser.add_argument("input_file", help="master file of the " "acquisition")
    parser.add_argument("output_file", help="output .nx or .h5 file", default=None)
    # usually it looks like the dxfile contains only one acquisition at the
    # root level
    parser.add_argument(
        "--input_entry",
        help="h5py group path to be converted",
        default="/",
    )
    parser.add_argument(
        "--output_entry",
        help="h5py group path to store the NXTomo",
        default="entry0000",
    )
    parser.add_argument(
        "--file_extension",
        default=".nx",
        help="extension of the output file. Valid values are "
        "" + "/".join([item.value for item in utils.FileExtension]),
    )
    # as scan range or rotation angle are not stored in dxfile we
    # provide the default value which is the "standard" case
    parser.add_argument(
        "--scan-range",
        default="0,180",
        help="scan range of the projections. Dark and flat will always be "
        "considered with rotation angle == scan_range[0]",
    )
    # as pixel sizes are not stored in the dxfile and requested for paganin
    # we provide some default value
    parser.add_argument(
        "--pixel-size",
        default=(None, None),
        help="pixel size in meter as (x pixel size, y pixel size) or as a single value",
    )
    parser.add_argument(
        "--fov",
        "--field-of-view",
        default=None,
        help="field of view. Can be Full or Half",
        dest="field_of_view",
    )
    # as distance is not stored in the dxfile and requested for paganin
    # we provide some default value
    parser.add_argument(
        "--distance",
        "--detector-sample-distance",
        default=None,
        help="sample to detector distance (in meter)",
        dest="distance",
    )
    parser.add_argument(
        "--energy",
        "--incident-beam-energy",
        default=None,
        help="incident beam energy in keV",
        dest="energy",
    )
    parser.add_argument(
        "--overwrite",
        help="Do not ask for user permission to overwrite output files",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--data-copy",
        help="Force data duplication of frames. This will permit to have an "
        "'all-embed' file. Otherwise we will have link between the dxfile "
        "and the NXTomo.",
        action="store_true",
        dest="duplicate_data",
        default=False,
    )
    options = parser.parse_args(argv[1:])

    distance = options.distance
    if distance is not None:
        distance = float(options.distance)
    energy = options.energy
    if energy is not None:
        energy = float(options.energy) * _ureg.keV
    if options.duplicate_data is False:
        _logger.warning(
            "Generated file will contain relative links to the "
            "(dxfile) source file. You should insure the "
            "relative position of the input file and the output "
            "stay constant to protect links. (use --copy-data) "
            "option to avoid links"
        )

    from_dx_to_nx(
        input_file=options.input_file,
        output_file=options.output_file,
        file_extension=options.file_extension,
        input_entry=options.input_entry,
        output_entry=options.output_entry,
        scan_range=convert_2elmts__tuple_to_float(options.scan_range),
        pixel_size=_get_pixel_size(options.pixel_size),
        field_of_view=options.field_of_view,
        distance=distance,
        overwrite=options.overwrite,
        duplicate_data=options.duplicate_data,
        energy=energy,
    )
