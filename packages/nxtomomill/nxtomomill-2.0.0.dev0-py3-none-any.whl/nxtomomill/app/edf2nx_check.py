"""
Application to check the conversion done of an EDF folder to a .nx file.

.. program-output:: nxtomomill edf2nx-check --help

"""

import argparse
import logging

from nxtomomill.converter.edf.edfconverter import post_processing_check
from nxtomomill.models.utils import convert_str_to_tuple
from nxtomomill.io.config.edfconfig import TomoEDFConfig
from nxtomomill.converter.edf.checks import OUPUT_CHECK

logging.basicConfig(level=logging.INFO)


def main(argv):
    """
    check a conversion made.
    To keep it coherent and safe we must keep the same inputs as for the EDF to NXtomo conversion.
    The only difference is that this one has some output check defined by default
    """
    parser = argparse.ArgumentParser(
        description="check a conversion from edf to NXtomo went's well"
    )
    parser.add_argument("scan_path", help="folder containing the edf files", nargs="?")
    parser.add_argument("output_file", help="foutput .h5 file", nargs="?")
    parser.add_argument(
        "--dataset-basename",
        "--file-prefix",
        default=None,
        help="file prefix to be used to deduce projections",
    )
    parser.add_argument(
        "--info-file",
        default=None,
        help=".info file containing acquisition information (ScanRange, Energy, TOMO_N...)",
    )
    parser.add_argument(
        "--config",
        "--configuration-file",
        "--configuration",
        default=None,
        help="file containing the full configuration to convert from SPEC-EDF to bliss to nexus. "
        "Default configuration file can be created from `nxtomomill edf-config` command",
    )
    parser.add_argument(
        "--delete-edf",
        "--delete-edf-source",
        "--delete-edf-source-files",
        default=False,
        action="store_true",
        help="if you are duplicating data (default behavior) you can ask to delete used edf files to free space",
    )
    parser.add_argument(
        "--output-checks",
        default=(OUPUT_CHECK.COMPARE_VOLUME,),
        help="Define list of check to be run once the conversion is finished (raise an error if check fails). This is done before removing edf if asked. So if check fails source edf files won't be removed",
    )
    options = parser.parse_args(argv[1:])
    config = TomoEDFConfig()
    if options.config is not None:
        config = config.from_cfg_file(options.config)

    check_input = {
        "dataset basename": (options.dataset_basename, config.dataset_basename),
        "scan path": (options.scan_path, config.input_folder),
        "output file": (options.output_file, config.output_file),
        "info file": (options.info_file, config.dataset_info_file),
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

    if options.dataset_basename is not None:
        config.dataset_basename = options.dataset_basename
    if options.info_file is not None:
        config.dataset_info_file = options.info_file
    if options.scan_path is not None:
        config.input_folder = options.scan_path
    if options.output_file is not None:
        config.output_file = options.output_file
    config.delete_edf_source_files = options.delete_edf
    config.output_checks = convert_str_to_tuple(options.output_checks)
    if not len(config.output_checks) > 0:
        raise ValueError("not check on conversion selected")

    assert isinstance(
        config.output_checks, tuple
    ), f"config.output_checks is expected to be a tuple. Gets {type(config.output_checks)}"
    post_processing_check(
        configuration=config,
    )
