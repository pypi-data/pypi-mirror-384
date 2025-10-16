# coding: utf-8

from __future__ import annotations

import logging
import os

import numpy
from tomoscan.esrf.scan.nxtomoscan import NXtomoScan
from tomoscan.esrf.scan.utils import cwd_context
from tomoscan.framereducer.method import ReduceMethod
from silx.io.utils import open as open_hdf5

from nxtomo.application.nxtomo import NXtomo
from nxtomo.nxobject.nxdetector import ImageKey

from ..utils.utils import strip_extension

logging.basicConfig(level=logging.INFO)

_logger = logging.getLogger(__name__)

__all__ = ["flat_reducer", "extract_darks_flats"]


def extract_darks_flats(
    dataset_file_name: str,
    entry_name: str,
    save_intermediated: bool = False,
    target_filename: str | None = None,
    target_entry_name: str | None = None,
    method: str = "median",
    reuse_intermediated: bool = False,
    use_projections_for_flats: bool = False,
    dark_default_value=None,
):
    dataset_file_name = os.path.abspath(dataset_file_name)
    target_entry_name = target_entry_name if target_entry_name else entry_name

    dirname = os.path.dirname(dataset_file_name)

    basename = os.path.basename(dataset_file_name)

    if not dirname:
        dirname = "./"

    if target_filename is not None:
        target_filename = os.path.abspath(target_filename)

    with cwd_context(dirname):
        if reuse_intermediated:
            scan = NXtomoScan(target_filename, target_entry_name)
            reduced_flats, metadata_flats = scan.load_reduced_flats(return_info=True)
            reduced_darks, metadata_darks = scan.load_reduced_darks(return_info=True)
        else:
            nxt = NXtomo()
            nxt.load(basename, data_path=entry_name)
            if use_projections_for_flats:
                where_proj = [k.value == 0 for k in nxt.instrument.detector.image_key]
                where_flat = [k.value == 1 for k in nxt.instrument.detector.image_key]

                nxt.instrument.detector.image_key_control[where_proj] = (
                    ImageKey.FLAT_FIELD
                )
                nxt.instrument.detector.image_key_control[where_flat] = ImageKey.INVALID

                file_path = f"{basename}_edited_keys_scan.nx"
                if os.path.isfile(file_path):
                    os.remove(file_path)
                nxt.save(file_path, entry_name)

                scan = NXtomoScan(file_path, entry_name)
                reduced_flats, metadata_flats = scan.compute_reduced_flats(
                    method, return_info=True
                )
                reduced_darks, metadata_darks = scan.compute_reduced_darks(
                    return_info=True
                )
                if len(reduced_darks) == 0:
                    assert len(reduced_flats), " We expect to find at least  some flats"
                    dim_2, dim_1 = reduced_flats[list(reduced_flats.keys())[0]].shape
                    _logger.warning(
                        f" patching with a default dark of size {dim_1} for horizontal , {dim_2} for vertical and default value {dark_default_value}"
                    )
                    assert (
                        dark_default_value is not None
                    ) > 0, f"No raw darks found in the dataset {scan} and 'dark_default_value' not provided. Unable to get any reduced darks."

                    reduced_darks[0] = numpy.full(
                        (dim_2, dim_1), dark_default_value, dtype="f"
                    )
                    metadata_darks = metadata_flats
            else:
                scan = NXtomoScan(basename, entry_name)
                reduced_flats, metadata_flats = scan.compute_reduced_flats(
                    method, return_info=True
                )
                reduced_darks, metadata_darks = scan.compute_reduced_darks(
                    return_info=True
                )
                reduced_flats, metadata_flats = scan.compute_reduced_flats(
                    method, return_info=True
                )

        if save_intermediated:
            scan = NXtomoScan(target_filename, target_entry_name)
            scan.save_reduced_flats(
                reduced_flats, flats_infos=metadata_flats, overwrite=True
            )
            scan.save_reduced_darks(
                reduced_darks, darks_infos=metadata_darks, overwrite=True
            )

    return_dict = {
        "flat": {"images": reduced_flats, "meta": metadata_flats},
        "dark": {"images": reduced_darks, "meta": metadata_darks},
    }

    return __RefsDarks(return_dict, entry_name), return_dict


class __RefsDarks:
    def __init__(self, dict_or_file_name, entry_name):
        self.dict_or_file_name = dict_or_file_name
        self.entry_name = entry_name
        self.flat_image, self.flat_current = self._take_image_and_meta("flat")
        self.dark_image, self.dark_current = self._take_image_and_meta("dark")

    def _take_image_and_meta(self, what) -> tuple:
        """
        :return: a tuple as (image, current:float|None)
        """
        if isinstance(self.dict_or_file_name, dict):
            group = self.dict_or_file_name[what]  # [self.entry_name]
            image = None
            for key in group["images"]:
                if (
                    isinstance(key, int)
                    or (isinstance(key, str) and key.isnumeric())
                    or (numpy.isdtype(numpy.dtype(key), "integral"))
                ):
                    if image is None:
                        image = group["images"][key]
                    else:
                        _logger.warning("More than one image found.")
            if len(group["meta"].machine_current) > 0:
                current = group["meta"].machine_current[0]
            else:
                current = None
        else:
            file_name_tmp = f"{strip_extension(self.dict_or_file_name)}_{what}.h5"
            with open_hdf5(file_name_tmp) as f:
                group = f[self.entry_name]
                group = f[what]
                image = None
                current = group["machine_current"][()][0]
                for key in group:
                    if (
                        isinstance(key, int)
                        or (isinstance(key, str) and key.isnumeric())
                        or (numpy.isdtype(numpy.dtype(key), "integral"))
                    ):
                        if image is None:
                            image = group[key][()]
                        else:
                            raise ValueError(
                                f"More than one image found in {file_name_tmp}"
                            )

        return image, current


def flat_reducer(
    scan_filename: str,
    ref_start_filename: str,
    ref_end_filename: str,
    mixing_factor: float,
    entry_name: str = "entry0000",
    median_or_mean: str = ReduceMethod.MEAN.value,
    save_intermediated: bool = False,
    reuse_intermediated: bool = False,
    overwrite: bool = True,
    dark_default_value=300,
):
    """
    this method extracts first a flatfield and dark from  two  reference scans. After flats and darks extraction, an interpolation is done
    according to the mixing_factor parameter. The obtained flats and dark are then saved associating them for a given target scan_filename

    :param scan_filename: The target scan. A nexus filename for which we want to create reduced scan from the scans
        given by ref_start and ref_end parameters ( a scan at the beginning, another at the end)
    :param ref_start_filename: The scan with projections to be used as reference for the beginning of the measures.
    :param ref_end_filename: The scan with projections to be used as reference at the end  of the measures.
    :param mixing_factor: The mixing factor giving the averaged flats as
        (ref_start-darkB+darkS)*(1-mixing_factor)+(ref_end-darkE+darkS)*mixing_factor
    :param entry_name: The entry name, it defaults to entry0000
    :param median_or_mean: Either "mean" or "median". Default is "mean"
    :param save_intermediated: Save intermediated flats and darks corresponding to extremal
        reference scans (ref_start_filename, refa_filename) for later usage. Defaults to False
    :param use_intermediated: Save  intermediated flats and darks and if already presente reuse them for mixing
    :param overwrite: enforce overwriting of the reduced flats/darks
    """

    if reuse_intermediated:
        required_files = [
            f"{strip_extension(ref_start_filename, _logger)}_darks.hdf5",
            f"{strip_extension(ref_start_filename, _logger)}_flats.hdf5",
            f"{strip_extension(ref_end_filename, _logger)}_darks.hdf5",
            f"{strip_extension(ref_end_filename, _logger)}_flats.hdf5",
        ]
        intermediated_are_reusable = True
        for fn in required_files:
            if not os.path.exists(fn):
                intermediated_are_reusable = False
    else:
        intermediated_are_reusable = False

    # saving the intermediae if enforced if there is a plan to use them
    # and they are not available yet
    save_intermediated = save_intermediated or (
        reuse_intermediated and not intermediated_are_reusable
    )

    if median_or_mean not in [ReduceMethod.MEAN.value, ReduceMethod.MEDIAN.value]:
        message = f""" the "median_or_mean" parameter must be one of {[ReduceMethod.MEAN.value, ReduceMethod.MEDIAN.value]}.
        It was {median_or_mean}
        """
        raise ValueError(message)

    fd_start, fd_start_as_dict = extract_darks_flats(
        ref_start_filename,
        entry_name,
        target_filename=ref_start_filename,
        save_intermediated=save_intermediated,
        method=median_or_mean,
        reuse_intermediated=intermediated_are_reusable,
        use_projections_for_flats=True,
        dark_default_value=dark_default_value,
    )

    fd_end, _ = extract_darks_flats(
        ref_end_filename,
        entry_name,
        target_filename=ref_end_filename,
        save_intermediated=save_intermediated,
        method=median_or_mean,
        reuse_intermediated=intermediated_are_reusable,
        use_projections_for_flats=True,
        dark_default_value=dark_default_value,
    )
    fd_sample, fd_as_dict = extract_darks_flats(
        scan_filename,
        entry_name,
        method=median_or_mean,
        use_projections_for_flats=False,
    )
    reduced_infos = fd_as_dict["flat"]["meta"]

    scan = NXtomoScan(scan_filename, entry_name)
    current = fd_sample.flat_current
    if current is None:
        # handle the case the fd_sample does not contains any flat frames. In this case get the first
        # current we find from the NXtomo
        currents = scan.machine_current
        if currents is not None and len(currents) > 0:
            current = currents[0]  # pylint: disable=E1136

    if current is None:
        raise ValueError(
            f"Unable to find any machine current from {scan_filename}. Unable to compute reduced darks and flats"
        )

    # compute reduced flats and dark
    flat0 = (
        fd_start.flat_image - fd_start.dark_image
    ) * current / fd_start.flat_current + fd_start.dark_image
    flat1 = (
        fd_end.flat_image - fd_start.dark_image
    ) * current / fd_end.flat_current + fd_start.dark_image

    flat = (1 - mixing_factor) * flat0 + mixing_factor * flat1

    reduced_flats = {0: flat}

    # save reduced flats and dark
    reduced_infos.machine_current = numpy.array([current])
    reduced_infos.count_time = reduced_infos.count_time[:1]
    if current != reduced_infos.machine_current[0]:
        raise RuntimeError(
            " Coherence check failed. Total non sense: the code is broken."
        )

    scan.save_reduced_flats(
        reduced_flats, flats_infos=reduced_infos, overwrite=overwrite
    )

    reduced_darks = fd_start_as_dict["dark"]["images"]
    reduced_infos = fd_start_as_dict["dark"]["meta"]
    scan.save_reduced_darks(
        reduced_darks, darks_infos=reduced_infos, overwrite=overwrite
    )
