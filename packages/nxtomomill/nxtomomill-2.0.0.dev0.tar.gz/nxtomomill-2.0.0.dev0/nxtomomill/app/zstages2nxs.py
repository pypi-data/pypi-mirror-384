"""Application to concatenate a serie of scan with different z to a single NXtomo"""

import argparse
import logging
import os
import re

import numpy as np
from tomoscan.framereducer.method import ReduceMethod

from nxtomomill.converter import from_h5_to_nx
from nxtomomill.io.config import TomoHDF5Config

from ..utils.flat_reducer import flat_reducer
from ..utils.utils import strip_extension

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def get_arguments(user_args):
    parser = argparse.ArgumentParser(
        description="""
        creates all the target nxs for all the stages.
        If the postfixes for reference scans are give (the one before and another after the measurements) the reduced flats dark are also created.
        The references scans are expected to contains projections to be 'interpreted' as flats
        """
    )
    parser.add_argument(
        "--filename_template",
        required=False,
        default=None,
        help="""The filename template. To be used for multiples  zstages it must  contain one or more  segments equal to "X"*ndigits  which will be replaced by the stage number, for the scans, and, for the reference scans, by the begin/end prefixes""",
    )

    parser.add_argument(
        "--filename",
        required=False,
        default=None,
        help="""The filename. To be used for a single scan""",
    )
    parser.add_argument(
        "--output_filename_template",
        required=False,
        default=None,
        help="""Optional, default to a name deduced from filename_template. The output filename template. It must  contain one or more  segments equal to "X"*ndigits  which will be replaced by the stage number""",
    )
    parser.add_argument(
        "--entry_name", required=False, help="entry_name", default="entry0000"
    )

    parser.add_argument(
        "--total_nstages",
        type=int,
        default=None,
        required=True,
        help="How many stages. Example: from 0 to 43 -> --total_nstages  44. ",
    )
    parser.add_argument(
        "--first_stage",
        type=int,
        default=0,
        required=False,
        help="Optional. Defaults to zero. The number of the first considered stage. Use this to do a smaller sequence",
    )
    parser.add_argument(
        "--last_stage",
        type=int,
        default=-1,
        required=False,
        help="Optional. Defaults to total_nstages-1. The number of the last considered stage. Use this to do a smaller sequence",
    )

    parser.add_argument(
        "--do_references",
        type=str2bool,
        default=False,
        required=False,
        help="Optional. If given the reference scans are used for the extraction of the flats/dark. The reference scans are obtained using the ref postfixes",
    )
    parser.add_argument(
        "--extracted_reference_target_dir",
        type=str,
        default=None,
        required=None,
        help="Optional. By default the extracted reference will be written in the same directory as the nexus scan. As the extraction procedure is time consuming they can be written instead to a common directory",
    )
    parser.add_argument(
        "--ref_scan_begin",
        type=str,
        default=None,
        required=False,
        help="""used when "do_reference" is True. It is optional. It is the reference scan. """,
    )

    parser.add_argument(
        "--ref_scan_end",
        type=str,
        default=None,
        required=False,
        help="""used when "do_reference" is True. It is optional. It is the end for the reference scan . """,
    )

    parser.add_argument(
        "--target_directory",
        type=str,
        default="./",
        required=False,
        help="""Where files are written. Optional, defaults to current directory""",
    )
    parser.add_argument(
        "--median_or_mean",
        type=str,
        choices=[ReduceMethod.MEAN.value, ReduceMethod.MEDIAN.value],
        default=ReduceMethod.MEAN.value,
        required=False,
        help="""Choose betwen median or mean. Optional. Default is mean""",
    )
    parser.add_argument(
        "--voxel_size",
        type=float,
        default=None,
        required=False,
        help="""Defaults to zero. If set to a different value the bliss generated nexus files will be corrected. Units are micron""",
    )
    parser.add_argument(
        "--dark_default_value",
        type=float,
        default=300,
        required=False,
        help="""The dark value that is used for scans without dark""",
    )

    args = parser.parse_args(user_args)

    if args.last_stage == -1:
        args.last_stage = args.total_nstages - 1

    return args


def _convert_bliss2nx(bliss_ref_name, nexus_name, corrections_dict={}):
    config = TomoHDF5Config()
    config.overwrite = True
    config.no_master_file = False
    config.input_file = bliss_ref_name
    config.output_file = nexus_name

    for corr_name, corr_value in corrections_dict.items():
        setattr(config, corr_name, corr_value)

    from_h5_to_nx(config)


def main(argv):
    args = get_arguments(argv[1:])

    if args.filename_template is not None:
        name_template_for_numeric = template_to_format_string(args.filename_template)
    else:
        name_template_for_numeric = args.filename

    if name_template_for_numeric is None:
        raise ValueError(
            " Either filename_template of filename must be given as arguments"
        )

    if args.output_filename_template is not None:
        args.output_refname_template = None
        if args.filename is None:
            if args.extracted_reference_target_dir is None:
                args.output_refname_template = template_to_format_string(
                    args.output_filename_template, literal=True
                )
            else:
                args.output_refname_template = None
            args.output_filename_template = template_to_format_string(
                args.output_filename_template, literal=False
            )
    else:
        # will be deduced at output time
        args.output_refname_template = None

    extra_dict = {}
    if args.voxel_size:
        extra_dict.update(
            {
                "x_pixel_size": args.voxel_size * 1.0e-6,
                "y_pixel_size": args.voxel_size * 1.0e-6,
            }
        )

    if args.do_references:
        refs_nexus_names = []
        for bliss_ref_name, what in (
            (args.ref_scan_begin, "begin"),
            (args.ref_scan_end, "end"),
        ):
            if args.output_refname_template is None:
                if args.extracted_reference_target_dir is None:
                    extraction_target_dir = args.target_directory
                else:
                    extraction_target_dir = args.extracted_reference_target_dir

                nexus_name = os.path.join(
                    extraction_target_dir,
                    strip_extension(os.path.basename(bliss_ref_name), _logger) + ".nx",
                )
            else:
                nexus_name = args.output_refname_template.format(what=what)

            _convert_bliss2nx(bliss_ref_name, nexus_name, extra_dict)

            refs_nexus_names.append(nexus_name)

    for iz in range(args.first_stage, args.last_stage + 1):
        bliss_name = name_template_for_numeric.format(i_stage=iz)
        if args.output_filename_template is None:
            nexus_name = os.path.join(
                args.target_directory,
                strip_extension(os.path.basename(bliss_name), _logger) + ".nx",
            )
        else:
            nexus_name = args.output_filename_template.format(i_stage=iz)

        _convert_bliss2nx(bliss_name, nexus_name, extra_dict)

        if args.do_references:
            factor = (iz + 1) / (args.total_nstages)
            flat_reducer(
                nexus_name,
                ref_start_filename=refs_nexus_names[0],
                ref_end_filename=refs_nexus_names[1],
                mixing_factor=factor,
                entry_name=args.entry_name,
                median_or_mean=args.median_or_mean,
                save_intermediated=False,
                reuse_intermediated=True,
                dark_default_value=args.dark_default_value,
            )
    return 0


def template_to_format_string(template, literal=False):
    pattern = re.compile("[X]+")
    # X represent the variable part of the 'template'
    # for example if we want to treat scans HA_2000_sample_0000.nx, ..., HA_2000_sample_9999.nx then
    # we expect the template to be HA_2000_sample_XXXX.nx
    # warning: If the dataset base names contains several X substrings the longest ones will be taken.
    ps = pattern.findall(template)
    ls = list(map(len, ps))
    if len(ls) == 0:
        raise ValueError("The template argument does not contain XX.. segments")
    idx = np.argmax(ls)
    if len(ps[idx]) < 2:
        message = f""" The argument template should contain  a substring  formed by at least two 'X'
        The template was {template}
        """
        raise ValueError(message)
    if not literal:
        template = template.replace(ps[idx], "{i_stage:" + "0" + str(ls[idx]) + "d}")
    else:
        template = template.replace(ps[idx], "{what}")

    return template
