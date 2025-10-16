"""
Application to concatenate several scans; each corresponding to a z-stage, into one nexus scan for nabu-helical
"""

import argparse
import os
import re
import json
import pint

import numpy as np
from silx.io.url import DataUrl
from tomoscan.esrf.scan.nxtomoscan import NXtomoScan
from tomoscan.scanbase import ReducedFramesInfos
from tomoscan.io import HDF5File, get_swmr_mode

from nxtomo.application.nxtomo import NXtomo
from nxtomo.nxobject.utils import concatenate as nx_concatenate
from nxtomo.nxobject.nxdetector import ImageKey
from nxtomomill.utils.hdf5 import DatasetReader

_ureg = pint.get_application_registry()


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def get_arguments(argv):
    parser = argparse.ArgumentParser(description="")
    parser.add_argument(
        "--filename_template",
        required=True,
        help="""The filename template. It must contain a segment equal to "X"*ndigits   which will be replaced by the stage number """,
    )
    parser.add_argument(
        "--target_file",
        required=True,
        help="The new nexus filename that we are going to create ",
    )
    parser.add_argument(
        "--entry_name",
        required=False,
        help="Optional.Output data path aka entry_name. Its default is entry0000",
        default="entry0000",
    )
    parser.add_argument(
        "--total_nstages", type=int, required=True, help="The total number of stages"
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
        "--cors_file",
        required=False,
        type=str,
        help="Optional. If given, it is a txt file with a column of centers of rotation. We expect one COR per stage. They are use to set the x_translation.\n"
        "This file can be either a one column text file, or a json file. In this case the key rotation_axis_position_list must be present and give a list",
    )
    parser.add_argument(
        "--pixel_size_m",
        required=False,
        default=None,
        help="Optional. The pixel size in meters. If given it will overwrite the nexus one, in the final nexus file",
    )
    parser.add_argument(
        "--neutral_flat",
        type=str2bool,
        required=False,
        default=False,
        help="Optional. Its default is False. If true then it will set flats to arrays filled with ones and darks with zeroes",
    )
    parser.add_argument(
        "--flats_from_reduced",
        type=str2bool,
        required=False,
        default=False,
        help="Optional. Its default is False. If true then the flats will be set from the reduced flats of the original scans",
    )
    parser.add_argument(
        "--flats_from_before_after",
        type=str2bool,
        required=False,
        default=False,
        help="""Optional. Its default is False. If true set flats from the reduced flats of  "before and after" scans.\n"
        "If given then you have to provide also the names these two scans, using parameters '--scan_before' and '--scan_after'""",
    )
    parser.add_argument(
        "--scan_before",
        required=False,
        type=str,
        help="""Optional. To be used with "flats_from_before_after selected". The name of the scan before all the scans. From this the flat/dark has been extracted""",
    )
    parser.add_argument(
        "--scan_after",
        required=False,
        type=str,
        help="""Optional. To be used with "flats_from_before_after selected".  The name of the scan after all the scans. From this the flat/dark has been extracted""",
    )

    args = parser.parse_args(argv)

    sum_bool = (
        args.neutral_flat + args.flats_from_reduced + args.flats_from_before_after
    )

    if (sum_bool) not in [0, 1]:
        message = f""" Only one or none of neutral_flat, flats_from_reduced, flats_from_before_after
        options can be selected. You selected {sum_bool} of them
        """
        raise ValueError(message)

    if args.last_stage == -1:
        args.last_stage = args.total_nstages - 1

    args.nstages = args.last_stage + 1 - args.first_stage

    if args.cors_file is None:
        args.cors = np.zeros([args.nstages], "f")
    else:
        try:  # check if it is json
            with open(args.cors_file, "r") as fj:
                json_dict = json.load(fj)
        except ValueError:
            args.cors = np.loadtxt(args.cors_file)
        else:
            args.cors = json_dict["rotation_axis_position_list"]

    pattern = re.compile("[X]+")
    # X represent the variable part of the 'template'
    # for example if we want to treat scans HA_2000_sample_0000.nx, ..., HA_2000_sample_9999.nx then
    # we expect the template to be HA_2000_sample_XXXX.nx
    # warning: If the dataset base names contains several X substrings the longest ones will be taken.
    ps = pattern.findall(args.filename_template)
    ls = list(map(len, ps))
    if len(ls) < 1:
        args.name_template = args.filename_template

        if args.first_stage != args.last_stage:
            message = f" The argument for filename_template , which was '{args.filename_template}'  does not seem to contain a pattern with multiple X for the numerical part"
            raise ValueError(message)
    else:
        idx = np.argmax(ls)
        if len(ps[idx]) < 2:
            message = f""" The argument filename_template should contain  a substring  formed by at least two 'X'
            The filename_template was {args.filename_template}
            """
            raise ValueError(message)
        args.name_template = args.filename_template.replace(
            ps[idx], "{i_stage:" + "0" + str(ls[idx]) + "d}"
        )

    args.file_list = []
    for i_stage in range(args.first_stage, args.last_stage + 1):
        args.file_list.append(args.name_template.format(i_stage=i_stage))
    args.used_current = None

    if args.pixel_size_m is not None:
        args.overwrite_pixel_size = True
        args.pixel_size_m = float(args.pixel_size_m)
    else:
        args.overwrite_pixel_size = False
        with HDF5File(args.file_list[0], "r", swmr=get_swmr_mode()) as h5f:
            args.pixel_size_m = h5f[
                os.path.join(args.entry_name, "instrument", "detector", "x_pixel_size")
            ][()]
    return args


def main(argv):
    args = get_arguments(argv[1:])
    output_file = args.target_file

    dummy_frame = None
    """the dummy frame is a frame fill with ones. It will be insert between two stages to ensure series from the twos stages will be
    perceived as 'uncontiguous'. Separates flats at the end of a stage and at the beginning.
    """
    nxt_z_list = []
    npoints_list = []
    for i_stage in range(args.first_stage, args.last_stage + 1):
        filename = args.file_list[i_stage - args.first_stage]
        # step 1: load the stage
        nxt = NXtomo()
        nxt.load(filename, data_path=args.entry_name, detector_data_as="as_data_url")
        nxt_z_list.append(nxt)

        scan = NXtomoScan(filename, args.entry_name)

        npoints_list.append(len(scan.image_key_control))

        if dummy_frame is None:
            if len(nxt.instrument.detector.data) > 0:
                # create empty frame to give it to the 'invalid_nxt' NXtomo later
                with DatasetReader(nxt.instrument.detector.data[0]) as raw_data:
                    data_type = raw_data.dtype
                # FIXME: avoid keeping some file open. not clear why this is needed
                raw_data = None
                args.img_shape = (scan.dim_2, scan.dim_1)
                with HDF5File(output_file, mode="w") as h5s:
                    h5s["empty_frame"] = np.ones(
                        (1, scan.dim_2, scan.dim_1), dtype=data_type
                    )
                    dummy_frame = DataUrl(
                        file_path=output_file, data_path="empty_frame"
                    )
            else:
                message = """The first nx file must have some data"""
                raise ValueError(message)

        # step 2: insert single 'empty' frame between the two stages (aka dummy frame)
        invalid_nxt = NXtomo(args.entry_name)
        invalid_nxt.instrument.detector.image_key_control = [ImageKey.INVALID]
        invalid_nxt.energy = nxt.energy.value
        invalid_nxt.control.data = np.ones(1, "f")
        invalid_nxt.sample.rotation_angle = [0.0] * _ureg.degree
        invalid_nxt.instrument.detector.field_of_view = (
            nxt.instrument.detector.field_of_view.value
        )
        invalid_nxt.instrument.detector.x_pixel_size = (
            nxt.instrument.detector.x_pixel_size.value
        )
        invalid_nxt.instrument.detector.y_pixel_size = (
            nxt.instrument.detector.y_pixel_size.value
        )

        invalid_nxt.instrument.detector.distance = (
            nxt.instrument.detector.distance.value
        )
        invalid_nxt.sample.x_translation = np.zeros([1], "f")
        invalid_nxt.sample.y_translation = np.zeros([1], "f")
        invalid_nxt.sample.z_translation = np.zeros([1], "f")
        invalid_nxt.instrument.detector.data = (dummy_frame,)

        nxt_z_list.append(invalid_nxt)

    nx_concatenated = nx_concatenate(nxt_z_list)
    nx_concatenated.save(
        file_path=output_file, data_path=args.entry_name, overwrite=True
    )

    with HDF5File(output_file, "r+") as output_target:
        N_total = output_target[
            os.path.join(args.entry_name, "sample", "x_translation")
        ].shape[0]

        if args.neutral_flat:
            # will set flats to arrays filled with ones and darks with zeroes
            original_currents = output_target[
                os.path.join(args.entry_name, "control", "data")
            ][()]
            original_currents[:] = 1
            del output_target[os.path.join(args.entry_name, "control", "data")]
            output_target[os.path.join(args.entry_name, "control", "data")] = (
                original_currents
            )

        do_flat = (
            args.flats_from_reduced or args.flats_from_before_after or args.neutral_flat
        )

        if do_flat or (args.cors_file is not None):
            one_for_invalid = 1
            actual_pos = 0
            old_pos = actual_pos

            i_stage = args.first_stage

            if do_flat:
                darks_dictionary = {}
                flats_dictionary = {}
                darks_infos_dictionary = {"count_time": []}
                flats_infos_dictionary = {"machine_current": [], "count_time": []}
                add_dark_to_dict(
                    args, darks_dictionary, darks_infos_dictionary, i_stage, actual_pos
                )

            for i_stage in range(args.first_stage, args.last_stage + 1):
                if do_flat:
                    add_flat_to_dict(
                        args,
                        flats_dictionary,
                        flats_infos_dictionary,
                        i_stage,
                        actual_pos,
                    )

                actual_pos += npoints_list[i_stage - args.first_stage]

                if do_flat:
                    add_flat_to_dict(
                        args,
                        flats_dictionary,
                        flats_infos_dictionary,
                        i_stage,
                        actual_pos,
                        position_in_list=1,
                    )

                # if i_stage != args.last_stage:
                actual_pos += one_for_invalid

                if args.cors_file is not None:
                    output_target[
                        os.path.join(args.entry_name, "sample", "x_translation")
                    ][old_pos:actual_pos] = (
                        -args.cors[i_stage - args.first_stage] + args.cors[0]
                    ) * args.pixel_size_m

                old_pos = actual_pos

            assert actual_pos == N_total

            if args.overwrite_pixel_size:
                g = output_target[
                    os.path.join(args.entry_name, "instrument", "detector")
                ]
                g["x_pixel_size"][()] = args.pixel_size_m
                g["y_pixel_size"][()] = args.pixel_size_m

            if do_flat:
                # darks metadata
                meta_darks = ReducedFramesInfos()
                meta_darks.count_time.extend(darks_infos_dictionary["count_time"][:1])

                # flats metadata
                meta_flats = ReducedFramesInfos()
                meta_flats.machine_current.extend(
                    flats_infos_dictionary["machine_current"]
                )
                meta_flats.count_time.extend(flats_infos_dictionary["count_time"])

                # save metadata
                scan = NXtomoScan(output_file, args.entry_name)
                scan.save_reduced_flats(
                    flats_dictionary, flats_infos=meta_flats, overwrite=True
                )
                scan.save_reduced_darks(
                    darks_dictionary, darks_infos=meta_darks, overwrite=True
                )


def add_flat_to_dict(
    args,
    flats_dictionary,
    flats_infos_dictionary,
    i_stage,
    actual_pos,
    position_in_list=0,
):
    if args.flats_from_reduced:
        filename = args.file_list[i_stage - args.first_stage]
        scan = NXtomoScan(filename, args.entry_name)
        reduced_flats, metadata_flats = scan.load_reduced_flats(return_info=True)
        position_in_list = min(position_in_list, len(list(reduced_flats.keys())) - 1)
        my_flat = reduced_flats[list(reduced_flats.keys())[position_in_list]]
        my_current = metadata_flats.machine_current[position_in_list]
        my_count_time = metadata_flats.count_time[position_in_list]
    elif args.neutral_flat:
        my_flat = np.ones(args.img_shape, "f")
        my_current = 1.0
        my_count_time = 1.0
    elif args.flats_from_before_after:
        scan = NXtomoScan(args.scan_before, args.entry_name)
        reduced_flats_b, metadata_flats_b = scan.load_reduced_flats(return_info=True)
        reduced_darks_b, _ = scan.load_reduced_darks(return_info=True)
        scan = NXtomoScan(args.scan_after, args.entry_name)
        reduced_flats_e, metadata_flats_e = scan.load_reduced_flats(return_info=True)
        reduced_darks_e, _ = scan.load_reduced_darks(return_info=True)

        flat_b = reduced_flats_b[list(reduced_flats_b.keys())[0]]
        flat_e = reduced_flats_e[list(reduced_flats_e.keys())[0]]
        dark_b = reduced_darks_b[list(reduced_darks_b.keys())[0]]
        dark_e = reduced_darks_b[list(reduced_darks_e.keys())[0]]

        current_b = metadata_flats_b.machine_current[0]
        current_e = metadata_flats_e.machine_current[0]

        if args.used_current is None:
            args.used_current = current_b

        factor = (i_stage) / (args.total_nstages)
        my_flat = args.used_dark + (
            (flat_b - dark_b) * (args.used_current / current_b) * (1 - factor)
            + (flat_e - dark_e) * (args.used_current / current_e) * factor
        )
        my_current = args.used_current
        my_count_time = args.used_count_time
    else:
        raise ValueError(
            "one of the option must be activated in[neutral_flat, flats_from_reduced, flats_from_before_after]"
        )

    flats_dictionary[actual_pos] = my_flat
    flats_infos_dictionary["machine_current"].append(my_current)
    flats_infos_dictionary["count_time"].append(my_count_time)


def add_dark_to_dict(
    args, darks_dictionary, darks_infos_dictionary, i_stage, actual_pos
):
    if args.flats_from_reduced:
        filename = args.file_list[i_stage - args.first_stage]
    elif args.flats_from_before_after:
        filename = args.scan_before
    else:
        assert args.neutral_flat
        filename = None

    if filename is not None:
        scan = NXtomoScan(filename, args.entry_name)
        reduced_darks, metadata_darks = scan.load_reduced_darks(return_info=True)
        my_dark = reduced_darks[list(reduced_darks.keys())[0]]
        my_count_time = metadata_darks.count_time[0]
    else:
        my_dark = np.zeros(args.img_shape, "f")
        my_count_time = 1.0

    darks_dictionary[actual_pos] = my_dark
    darks_infos_dictionary["count_time"].append(my_count_time)
    args.used_count_time = my_count_time

    args.used_dark = darks_dictionary[actual_pos]
