# coding: utf-8

"""
Utils related to bliss-HDF5
"""

from collections import namedtuple
import os
from pathlib import Path

H5FileKeys = namedtuple(
    "H5FileKeys",
    [
        "acq_expo_time_keys",
        "rot_angle_keys",
        "valid_camera_names",
        "sample_x_keys",
        "sample_y_keys",
        "translation_z_keys",
        "translation_y_keys",
        "x_sample_pixel_size",
        "y_sample_pixel_size",
        "x_detector_pixel_size",
        "y_detector_pixel_size",
        "diode_keys",
    ],
)


H5ScanTitles = namedtuple(
    "H5ScanTitles",
    [
        "init_titles",
        "zseries_init_titles",
        "multitomo_init_titles",
        "back_and_forth_init_titles",
        "dark_titles",
        "flat_titles",
        "projection_titles",
        "align_titles",
    ],
)

PROCESSED_DATA_DIR_NAME = "PROCESSED_DATA"
RAW_DATA_DIR_NAME = "RAW_DATA"


def get_default_output_file(input_file: str, output_file_extension: str = ".nx") -> str:
    """
    Policy: look for any 'RAW_DATA' in file directory. If find any (before any 'PROCESSED_DATA' directory) replace it "RAW_DATA".
    Then replace input_file by the expected file_extension and make sure the output file is different than the input file. Else append _nxtomo to it.

    :param input_file: file to be converted from bliss to NXtomo
    :param output_file_extension:
    :return: default output file according to policy
    """
    if isinstance(input_file, Path):
        input_file = str(input_file)
    if not isinstance(input_file, str):
        raise TypeError(
            f"input_file is expected to be an instance of str. {type(input_file)} provided"
        )
    if not isinstance(output_file_extension, str):
        raise TypeError("output_file_extension is expected to be a str")
    if not output_file_extension.startswith("."):
        output_file_extension = "." + output_file_extension

    input_file = os.path.abspath(input_file)
    input_file_no_ext, _ = os.path.splitext(input_file)

    def from_raw_data_path_to_process_data_path(file_path: str):
        split_path = file_path.split(os.sep)
        # reverse it to find the lower level value of '_RAW_DATA_DIR_NAME' if by any 'chance' has several in the path
        # in this case this is most likely what we want
        split_path = split_path[::-1]
        # check if already contain in a "PROCESSED_DATA" directory
        try:
            index_processed_data = split_path.index(PROCESSED_DATA_DIR_NAME)
        except ValueError:
            index_processed_data = None

        try:
            index_raw_data = split_path.index(RAW_DATA_DIR_NAME)
        except ValueError:
            # if the value is not in the list
            pass
        else:
            if index_processed_data is None or index_raw_data < index_processed_data:
                # make sure we are not already in a 'PROCESSED_DATA' directory. Not sure it will never happen but safer
                split_path[index_raw_data] = PROCESSED_DATA_DIR_NAME

        # reorder path to original
        split_path = split_path[::-1]
        return os.sep.join(split_path)

    output_path = from_raw_data_path_to_process_data_path(input_file_no_ext)
    output_file = output_path + output_file_extension
    if output_file == input_file:
        # to be safer if the default output file is the same as the input file (if the input file has a .nx extension and not in any 'RAw_DATA' directory)
        return output_path + "_nxtomo" + output_file_extension
    else:
        return output_file
