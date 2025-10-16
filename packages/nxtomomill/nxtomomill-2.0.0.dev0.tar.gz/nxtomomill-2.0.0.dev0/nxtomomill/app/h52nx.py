# coding: utf-8

"""
Application to convert a bliss-hdf5 tomography dataset to Nexus - NXtomo (hdf5) format

.. program-output:: nxtomomill h52nx --help

For a complete tutorial you can have a look at: :ref:`Tomoh52nx`

"""

import argparse
import logging
from typing import Iterable

from tqdm import tqdm

from nxtomomill import utils
from nxtomomill.converter import from_h5_to_nx
from nxtomomill.io.config.confighandler import (
    SETTABLE_PARAMETERS_UNITS,
    TomoHDF5ConfigHandler,
)

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


def _getPossibleInputParams():
    """

    :return: string with param1 (expected unit) ...
    """
    res = []
    for key, value in SETTABLE_PARAMETERS_UNITS.items():
        res.append(f"{key} ({value})")
    return ", ".join(res)


def _ask_for_selecting_detector(det_grps: Iterable):
    res = input(
        "Several detector found. Only one detector is managed at the "
        "time. Please enter the name of the detector you want to use "
        f"or 'Cancel' to stop translation ({det_grps})"
    )
    if res == "Cancel":
        return None
    elif res in det_grps:
        return res
    else:
        # warning: this is not a debug log !!!
        print("detector name not recognized.")
        return _ask_for_selecting_detector(det_grps)


def main(argv):
    """ """
    parser = argparse.ArgumentParser(
        description="convert data acquired as "
        "hdf5 from bliss to nexus "
        "`NXtomo` classes. For `zseries` it will create one entry per `z`"
    )
    parser.add_argument(
        "input_file", help="master file of the " "acquisition", default=None, nargs="?"
    )
    parser.add_argument(
        "output_file", help="output .nx or .h5 file", default=None, nargs="?"
    )
    parser.add_argument(
        "--file-extension",
        "--file_extension",
        default=None,
        help="extension of the output file. Valid values are "
        "" + "/".join([item.value for item in utils.FileExtension]),
    )
    parser.add_argument(
        "--single-file",
        help="merge all scan sequence to the same output file. "
        "By default create one file per sequence and "
        "group all sequence in the output file",
        dest="single_file",
        action="store_true",
        default=None,  # default is None and not False for the ConfigHandler so it can knows when set by the user or not
    )
    parser.add_argument(
        "--with-master-file",
        help="Creates a master file linking all .nx files",
        dest="no_master_file",
        action="store_false",
        default=None,
    )
    parser.add_argument(
        "--overwrite",
        help="Do not ask for user permission to overwrite output files",
        action="store_true",
        default=None,  # default is None and not False for the ConfigHandler so it can knows when set by the user or not
    )
    parser.add_argument(
        "--debug",
        help="Set logs to debug mode",
        action="store_true",
        default=None,  # default is None and not False for the ConfigHandler so it can knows when set by the user or not
    )
    parser.add_argument(
        "--entries",
        help="Specify (root) entries to be converted. By default it will try "
        "to convert all existing entries.",
        default=None,
    )
    parser.add_argument(
        "--sub-entries-to-ignore",
        "--ignore-sub-entries",
        help="Specify (none-root) sub entries to ignore.",
        default=None,
    )
    parser.add_argument(
        "--raises-error",
        help="Raise errors if some data are not met instead of providing some"
        " default values",
        action="store_true",
        default=None,  # default is None and not False for the ConfigHandler so it can knows when set by the user or not
    )
    parser.add_argument(
        "--field-of-view",
        help="Force the output to be `Half`  or `Full` acquisition. Otherwise "
        "parse raw data to find this information.",
        default=None,
    )
    parser.add_argument(
        "--no-input",
        "--no-input-for-missing-information",
        help="The user won't be ask for any inputs",
        dest="request_input",
        action="store_false",
        default=None,  # default is None and not False for the ConfigHandler so it can knows when set by the user or not
    )
    parser.add_argument(
        "--data-copy",
        "--copy-data",
        help="Force data duplication of frames. This will permit to have an "
        "'all-embed' file. Otherwise the detector/data dataset will haves "
        "links to other files.",
        action="store_true",
        dest="default_data_copy",
        default=None,  # default is None and not False for the ConfigHandler so it can knows when set by the user or not
    )
    parser.add_argument(
        "--sample_x_keys",
        "--sample-x-keys",
        default=None,
        help="x translation key in bliss HDF5 file",
    )
    parser.add_argument(
        "--sample_y_keys",
        "--sample-y-keys",
        default=None,
        help="y translation key in bliss HDF5 file",
    )
    parser.add_argument(
        "--translation_z_keys",
        "--translation-z-keys",
        default=None,
        help="z translation key in bliss HDF5 file",
    )
    parser.add_argument(
        "--sample-detector-distance-keys",
        "--sample-detector-distance-paths",
        "--distance-paths",
        default=None,
        help="sample detector distance paths",
    )
    parser.add_argument(
        "--valid_camera_names",
        "--valid-camera-names",
        default=None,
        help="Valid NXDetector dataset name to be considered. Otherwise will"
        "try to deduce them from NX_class attibute (value should be"
        "NXdetector) or from instrument group child structure.",
    )
    parser.add_argument(
        "--rotation_angle_keys",
        "--rotation-angle-keys",
        "--rot-angle-keys",
        "--rot_angle_keys",
        default=None,
        help="Valid dataset name for rotation angle",
    )
    parser.add_argument(
        "--exposure_time_keys",
        "--exposure-time-keys",
        "--acq_expo_time_keys",
        "--acq-expo-time-keys",
        default=None,
        help="Valid dataset name for acquisition exposure time",
    )
    parser.add_argument(
        "--sample-x-pixel-size_keys",
        "--sample_x_pixel_size_keys",
        default=None,
        help="X pixel size key to read",
    )
    parser.add_argument(
        "--sample-y-pixel-size_keys",
        "--sample_y_pixel_size_keys",
        default=None,
        help="Y pixel size key to read",
    )

    # scan titles
    parser.add_argument(
        "--init_titles",
        "--init-titles",
        default=None,
        help="Titles corresponding to init scans",
    )
    parser.add_argument(
        "--zseries-init-titles",
        "--zseries_init_titles",
        "--z_series_init_titles",
        "--z-series_init_titles",
        "--init_zserie_titles",
        "--init-zserie-titles",
        default=None,
        help="Titles corresponding to zserie init scans",
    )
    parser.add_argument(
        "--multitomo-init-titles",
        "--multitomo_init_titles",
        "--multi-tomo-init-titles",
        "--multi_tomo_init_titles",
        "--init-multi-tomo-titles",
        "--init-pcotomo-titles",
        default=None,
        help="Titles corresponding to multi-tomo init scans",
    )
    parser.add_argument(
        "--back-and-forth-init-titles",
        "--back_and_forth_init_titles",
        "--init-back-and-forth-titles",
        "--init_back_and_forth_titles",
        default=None,
        help="Titles corresponding to back-and-forth init scans",
    )
    parser.add_argument(
        "--dark-titles",
        "--dark_titles",
        default=None,
        help="Titles corresponding to dark scans",
    )
    parser.add_argument(
        "--flat-titles",
        "--flat_titles",
        "--ref_titles",
        "--ref-titles",
        default=None,
        help="Titles corresponding to ref scans",
        dest="flat_titles",
    )
    parser.add_argument(
        "--projection_titles",
        "--proj_titles",
        "--proj-titles",
        default=None,
        help="Titles corresponding to projection scans",
    )
    parser.add_argument(
        "--alignment-titles",
        "--alignment_titles",
        "--align_titles",
        "--align-titles",
        default=None,
        help="Titles corresponding to alignment scans",
    )
    parser.add_argument(
        "--set-params",
        default=None,
        nargs="*",
        help="Allow manual definition of some parameters. "
        "Valid parameters (and expected input unit) "
        f"are: {_getPossibleInputParams()}. Should be added at the end of the command line because "
        "will try to cover all text set after this option.",
    )

    # config file
    parser.add_argument(
        "--config-file",
        "--config",
        "--configuration",
        "--configuration-file",
        default=None,
        help="file containing the full configuration to convert from h5 "
        "bliss to nexus",
    )

    options = parser.parse_args(argv[1:])
    if options.request_input:
        callback_det_sel = _ask_for_selecting_detector
    else:
        callback_det_sel = None
    try:
        configuration_handler = TomoHDF5ConfigHandler(options)
    except Exception:
        _logger.error("Fail to initiate the configuration.", exc_info=True)
        return
    else:
        for title in configuration_handler.configuration.init_titles:
            assert title != ""
        logging.getLogger("nxtomomill").setLevel(
            configuration_handler.configuration.log_level
        )
        from_h5_to_nx(
            configuration=configuration_handler.configuration,
            progress=tqdm(desc="h52nx", delay=1, bar_format="{l_bar}{bar}"),
            input_callback=None,
            detector_sel_callback=callback_det_sel,
        )
