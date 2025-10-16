# coding: utf-8

"""
module to convert from edf to (nexus tomo compliant) .nx
"""

from __future__ import annotations

import logging
import os
from collections import namedtuple
import fabio
import h5py
import numpy
import pint

from tqdm import tqdm

from silx.io.dictdump import dicttoh5
from silx.utils.deprecation import deprecated

from tomoscan.esrf.scan.edfscan import EDFTomoScan
from tomoscan.esrf.scan.nxtomoscan import NXtomoScan
from tomoscan.esrf.scan.utils import get_parameters_frm_par_or_info
from tomoscan.io import HDF5File

from nxtomo.paths.nxtomo import get_paths as get_nexus_paths
from nxtomo.nxobject.nxdetector import FieldOfView, ImageKey
from nxtomo.nxobject.nxsource import SourceType

from nxtomomill import utils
from nxtomomill.converter.version import LATEST_VERSION
from nxtomomill.converter.version import version as converter_version
from nxtomomill.models.utils import PathType
from nxtomomill.models.edf2nx import EDF2nxModel
from nxtomomill.utils.nexus import create_nx_data_group, link_nxbeam_to_root
from nxtomomill.settings import Tomo

__all__ = [
    "EDFFileKeys",
    "DEFAULT_EDF_KEYS",
    "edf_to_nx",
    "from_edf_to_nx",
    "post_processing_check",
    "get_byte_order",
]

EDF_MOTOR_POS = Tomo.EDF.MOTOR_POS
EDF_MOTOR_MNE = Tomo.EDF.MOTOR_MNE
EDF_REFS_NAMES = Tomo.EDF.REFS_NAMES
EDF_TO_IGNORE = Tomo.EDF.TO_IGNORE
EDF_ROT_ANGLE = Tomo.EDF.ROT_ANGLE
EDF_DARK_NAMES = Tomo.EDF.DARK_NAMES
EDF_X_TRANS = Tomo.EDF.X_TRANS
EDF_Y_TRANS = Tomo.EDF.Y_TRANS
EDF_Z_TRANS = Tomo.EDF.Z_TRANS
EDF_MACHINE_CURRENT = Tomo.EDF.MACHINE_CURRENT

_ureg = pint.get_application_registry()
_logger = logging.getLogger(__name__)


EDFFileKeys = namedtuple(
    "EDFFileKeys",
    [
        "motor_pos_keys",
        "motor_mne_keys",
        "rotation_angle_keys",
        "x_translation_keys",
        "y_translation_keys",
        "z_translation_keys",
        "to_ignore",
        "dark_names",
        "flat_names",
        "machine_current_keys",
    ],
)

DEFAULT_EDF_KEYS = EDFFileKeys(
    EDF_MOTOR_POS,
    EDF_MOTOR_MNE,
    EDF_ROT_ANGLE,
    EDF_X_TRANS,
    EDF_Y_TRANS,
    EDF_Z_TRANS,
    EDF_TO_IGNORE,
    EDF_DARK_NAMES,
    EDF_REFS_NAMES,
    EDF_MACHINE_CURRENT,
)

_ESTIMATED_PERCENTAGE_TIME_TO_READ_METADATA = 20
# as at the moment we cannot provide a good estimation of how much it takes to read metadata let's estimate it from experience


@deprecated(replacement="from_edf_to_nx", since_version="0.9.0")
def edf_to_nx(
    scan: EDFTomoScan,
    output_file: str,
    file_extension: str,
    file_keys: EDFFileKeys = DEFAULT_EDF_KEYS,
    progress=None,
    sample_name: str | None = None,
    title: str | None = None,
    instrument_name: str | None = None,
    source_name: str | None = None,
    source_type: SourceType | None = None,
) -> tuple:
    """
    Convert an edf file to a nexus file.
    For now duplicate data.

    :param scan:
    :param output_file:
    :param file_extension:
    :param file_keys:
    :param progress:
    :param sample_name: name of the sample
    :param title: dataset title
    :param instrument_name: name of the instrument used
    :param source_name: name of the source (most likely ESRF)
    :param source_type: type of the source (most likely "Synchrotron X-ray Source")
    :return: (nexus_file, entry)
    """
    if not isinstance(scan, EDFTomoScan):
        raise TypeError("scan is expected to be an instance of EDFTomoScan")

    config = EDF2nxModel(
        input_folder=scan.path,
        dataset_basename=scan.dataset_basename,
        output_file=output_file,
        file_extension=file_extension,
        sample_name=sample_name,
        title=title,
        instrument_name=instrument_name,
        source_name=source_name,
        source_type=source_type,
        # handle file_keys
        motor_position_keys=file_keys.motor_pos_keys,
        motor_mne_keys=file_keys.motor_mne_keys,
        rotation_angle_keys=file_keys.rotation_angle_keys,
        x_translation_keys=file_keys.x_translation_keys,
        y_translation_keys=file_keys.y_translation_keys,
        z_translation_keys=file_keys.z_translation_keys,
        machine_current_keys=file_keys.machine_current_keys,
        patterns_to_ignores=file_keys.to_ignore,
        dark_names_prefix=file_keys.dark_names,
        flat_names_prefix=file_keys.flat_names,
    )

    return from_edf_to_nx(config, progress=progress)


def from_edf_to_nx(configuration: EDF2nxModel, progress: tqdm | None = None) -> tuple:
    """
    Convert an edf file to a nexus file.
    For now duplicate data.

    :param configuration: configuration to use to process the data
    :param progress: if provided then will be updated with conversion progress
    :return: (nexus_file, entry)
    """
    if configuration.input_folder is None:
        raise ValueError("input_folder should be provided")
    if not os.path.isdir(configuration.input_folder):
        raise OSError(f"{configuration.input_folder} is not a valid folder path")

    if configuration.output_file is None:
        raise ValueError("output_file should be provided")

    # if we don't duplicate data then we can't delete sources EDF files
    if not configuration.duplicate_data and configuration.delete_edf_source_files:
        raise ValueError(
            "You asked for avoiding data duplication and to delete edf source files. "
            "Those two options are not compatible. Avoiding data duplication will "
            "lead to create HDF5Virtual dataset pointing to the edf source files"
        )

    fileout_h5 = utils.get_file_name(
        file_name=configuration.output_file,
        extension=configuration.file_extension,
        check=True,
    )

    with HDF5File(fileout_h5, "w") as h5d:
        return __process(
            configuration=configuration,
            output_grp=h5d,
            fileout_h5=fileout_h5,
            progress=progress,
        )


def post_processing_check(configuration: EDF2nxModel):
    """
    check that conversion made contains the same information as a folder and optionnaly delete edf files

    """
    if configuration.input_folder is None:
        raise ValueError("input_folder should be provided")
    if not os.path.isdir(configuration.input_folder):
        raise OSError(f"{configuration.input_folder} is not a valid folder path")

    if configuration.output_file is None:
        raise ValueError("output_file should be provided")
    if (
        configuration.delete_edf_source_files is True
        and len(configuration.output_checks) == 0
    ):
        raise ValueError(
            "requested to remove edf files without righting an NXtomo and not doing any check on an existing NXtomo. This is a non sense."
        )

    # if we don't duplicate data then we can't delete sources EDF files
    if not configuration.duplicate_data and configuration.delete_edf_source_files:
        raise ValueError(
            "You asked for avoiding data duplication and to delete edf source files. "
            "Those two options are not compatible. Avoiding data duplication will "
            "lead to create HDF5Virtual dataset pointing to the edf source files"
        )

    fileout_h5 = utils.get_file_name(
        file_name=configuration.output_file,
        extension=configuration.file_extension,
        check=True,
    )

    return __process(
        configuration=configuration,
        fileout_h5=fileout_h5,
        output_grp=None,
        progress=None,
    )


def __process(
    configuration: EDF2nxModel,
    output_grp: h5py.Group | None,
    fileout_h5: str,
    progress: tqdm | None,
):
    """
    This function is used to insure processing is exactly the same:
     * if we want to convert edf to .nx
     * if we want to check a conversion from edf to edf (and optionally remove edf afterwards)

    Not very nice but the simpler for making evolve some legacy code...
    """

    if progress is not None:
        progress.set_postfix_str(
            "preprocessing - retrieve all metadata (can take a few seconds - cannot display real advancement)"
        )
        progress.total = 100
        progress.n = _ESTIMATED_PERCENTAGE_TIME_TO_READ_METADATA
        progress.refresh()

    if configuration.dataset_info_file is not None:
        if not os.path.isfile(configuration.dataset_info_file):
            raise ValueError(f"{configuration.dataset_info_file} is not a file")
        else:
            scan_info = get_parameters_frm_par_or_info(configuration.dataset_info_file)
    else:
        scan_info = None
    scan = EDFTomoScan(
        scan=configuration.input_folder,
        dataset_basename=configuration.dataset_basename,
        scan_info=scan_info,
        # TODO: add n frames ?
    )

    _logger.info(f"Output file will be {fileout_h5}")
    if scan.dim_2 is None or scan.dim_1 is None:
        if scan_info is not None:
            raise ValueError("Please provide scan 'dim_1' and 'dim_2' with scan info")
        else:
            info_file = os.path.join(
                configuration.input_folder, f"{configuration.dataset_basename}.info"
            )
            raise ValueError(
                f"Unable to deduce scan dimension from scan metadata (used file for metadata: {info_file})"
            )

    default_current = scan.retrieve_information(
        scan=scan.path,
        dataset_basename=scan.dataset_basename,
        ref_file=None,
        key="SrCurrent",
        key_aliases=["SRCUR", "machineCurrentStart"],
        type_=float,
        scan_info=scan.scan_info,
    )
    if default_current is None:
        _logger.warning("Unable to find machine current default current. Take 0.0")
        default_current = 0.0

    output_data_path = "entry"

    # with today design we can simply remove the files of the url. We don't expect those files
    # to contain other type of data
    edf_source_files = dict()
    # for each file register a tuple (existing_frame, set(url)) so at the end we can make sure all the frame have been used before
    # removing the file
    detector_data_urls = []
    # store the url in the order they are used and if it has been modified or not (for output checks).

    def update_edf_source_files(url, n_frames):
        if configuration.delete_edf_source_files:
            # edf_source files is only used for deleting edf files
            edf_file_path = url.file_path()
            file_source_info = edf_source_files.get(edf_file_path, (n_frames, set()))
            urls_used = file_source_info[1]
            urls_used.add(url.path())
            edf_source_files[edf_file_path] = (
                file_source_info[0],
                urls_used,
            )

    DARK_ACCUM_FACT = True

    metadata = []
    proj_urls = scan.get_proj_urls(
        scan=scan.path, dataset_basename=scan.dataset_basename
    )

    for dark_to_find in configuration.dark_names_prefix:
        dk_urls = scan.get_darks_url(scan_path=scan.path, prefix=dark_to_find)
        if len(dk_urls) > 0:
            if dark_to_find == "dark":
                DARK_ACCUM_FACT = False
            break

    _edf_to_ignore = list(configuration.patterns_to_ignores)

    for refs_to_find in configuration.flat_names_prefix:
        if refs_to_find == "ref":
            _edf_to_ignore.append("HST")
        elif "HST" in _edf_to_ignore:
            _edf_to_ignore.remove("HST")

        refs_urls = scan.get_flats_url(
            scan_path=scan.path,
            prefix=refs_to_find,
            ignore=_edf_to_ignore,
            dataset_basename=scan.dataset_basename,
        )
        if len(refs_urls) > 0:
            break

    n_frames = len(proj_urls) + len(refs_urls) + len(dk_urls)
    n_darks = len(dk_urls)

    (
        frame_type,
        rot_angle_index,
        x_trans_index,
        y_trans_index,
        z_trans_index,
        srcur_index,
    ) = _getExtraInfo(scan=scan, configuration=configuration)

    if rot_angle_index == -1 and configuration.force_angle_calculation is False:
        _logger.warning(
            f"Unable to find one of the defined key for rotation in header ({configuration.rotation_angle_keys}). Will force angle calculation"
        )
        configuration.force_angle_calculation = True

    if not output_grp:
        # in the case we don't intend to write the NXtomo but only check it
        output_grp = None
        ext_datasets_grp = None
        dark_dataset = None
        data_dataset = None
        keys_dataset = None
        keys_control_dataset = None
        x_dataset = y_dataset = z_dataset = None
        rotation_dataset = None
        machine_current_dataset = None
    else:
        if configuration.duplicate_data is True:
            data_dataset = output_grp.create_dataset(
                "/entry/instrument/detector/data",
                shape=(n_frames, scan.dim_2, scan.dim_1),
                dtype=frame_type,
            )
            ext_datasets_grp = None
            dark_dataset = None
        else:
            _logger.warning(
                "No data duplication requested. Will fail if your dataset contains compressed data"
            )
            # if necessary create external datasets groups
            # note: for now we are force to create one dataset per frame because
            # the byte order can be modified from one frame to the other.
            ext_datasets_grp = output_grp.create_group("external_datasets")
            data_dataset = None
            # we must duplicate darks not matter what because exposure time is not handled
            # at nabu side for the moment
            dark_dataset = ext_datasets_grp.create_dataset(
                "darks",
                shape=(n_darks, scan.dim_2, scan.dim_1),
                dtype=frame_type,
            )

        keys_dataset = output_grp.create_dataset(
            "/entry/instrument/detector/image_key", shape=(n_frames,), dtype=numpy.int32
        )

        keys_control_dataset = output_grp.create_dataset(
            "/entry/instrument/detector/image_key_control",
            shape=(n_frames,),
            dtype=numpy.int32,
        )

        title = configuration.title
        if title is None:
            title = os.path.basename(scan.path)
        output_grp["/entry/title"] = title

        sample_name = configuration.sample_name
        if configuration.sample_name is None:
            # try to deduce sample name from scan path.
            try:
                sample_name = os.path.abspath(scan.path).split(os.sep)[-3:]
                sample_name = os.sep.join(sample_name)
            except Exception:
                sample_name = "unknow"
        output_grp["/entry/sample/name"] = sample_name
        if configuration.instrument_name is not None:
            instrument_grp = output_grp["/entry"].require_group("instrument")
            instrument_grp["name"] = configuration.instrument_name

        if configuration.source_name is not None:
            source_grp = output_grp["/entry/instrument"].require_group("source")
            source_grp["name"] = configuration.source_name
        if configuration.source_type is not None:
            source_grp = output_grp["/entry/instrument"].require_group("source")
            source_grp["type"] = configuration.source_type.value
        if configuration.source_probe is not None:
            source_grp = output_grp["/entry/instrument"].require_group("source")
            source_grp["probe"] = configuration.source_probe.value

        if scan.scan_range is None or scan.tomo_n is None:
            raise ValueError(
                f"Cannot find scan_range ({scan.scan_range}) and / or tomo_n ({scan.tomo_n}). Is the .info file here and / or valid ?"
            )

        distance = scan.retrieve_information(
            scan=os.path.abspath(scan.path),
            dataset_basename=scan.dataset_basename,
            ref_file=None,
            key="Distance",
            type_=float,
            key_aliases=["distance"],
            scan_info=scan.scan_info,
        )
        if distance is not None:
            output_grp["/entry/instrument/detector/distance"] = (
                (distance * configuration.sample_detector_distance_unit)
                .to(_ureg.meter)
                .magnitude
            )
            output_grp["/entry/instrument/detector/distance"].attrs["units"] = str(
                (_ureg.meter)
            )

        pixel_size = scan.retrieve_information(
            scan=os.path.abspath(scan.path),
            dataset_basename=scan.dataset_basename,
            ref_file=None,
            key="PixelSize",
            type_=float,
            key_aliases=["pixelSize"],
            scan_info=scan.scan_info,
        )
        output_grp["/entry/instrument/detector/x_pixel_size"] = (
            (pixel_size * configuration.pixel_size_unit).to(_ureg.meter).magnitude
        )
        output_grp["/entry/instrument/detector/x_pixel_size"].attrs["units"] = str(
            str(_ureg.meter)
        )
        output_grp["/entry/instrument/detector/y_pixel_size"] = (
            (pixel_size * configuration.pixel_size_unit).to(_ureg.meter).magnitude
        )
        output_grp["/entry/instrument/detector/y_pixel_size"].attrs["units"] = str(
            str(_ureg.meter)
        )

        energy = scan.retrieve_information(
            scan=os.path.abspath(scan.path),
            dataset_basename=scan.dataset_basename,
            ref_file=None,
            key="Energy",
            type_=float,
            key_aliases=["energy"],
            scan_info=scan.scan_info,
        )
        if energy is not None:
            energy = energy * configuration.energy_unit
            output_grp["/entry/instrument/beam/incident_energy"] = energy.to(
                _ureg.keV
            ).magnitude
            output_grp["/entry/instrument/beam/incident_energy"].attrs["units"] = str(
                _ureg.keV
            )

        # rotations values
        rotation_dataset = output_grp.create_dataset(
            "/entry/sample/rotation_angle", shape=(n_frames,), dtype=numpy.float32
        )
        output_grp["/entry/sample/rotation_angle"].attrs["units"] = str(_ureg.degree)

        # machine current
        nexus_paths = get_nexus_paths(LATEST_VERSION)
        machine_current_path = "/".join(["entry", nexus_paths.ELECTRIC_CURRENT_PATH])
        machine_current_dataset = output_grp.create_dataset(
            machine_current_path,
            shape=(n_frames,),
            dtype=numpy.float32,
        )
        output_grp[machine_current_path].attrs["units"] = str(_ureg.ampere)

        # provision for centering motors
        # warning: x_dataset, y_dataset and z_dataset are from the esrf reference.
        # from NXtomo reference this is z_translation, x_translation and y_translation
        x_dataset = output_grp.create_dataset(
            "/entry/sample/z_translation", shape=(n_frames,), dtype=numpy.float32
        )
        output_grp["/entry/sample/z_translation"].attrs["units"] = str(_ureg.meter)

        y_dataset = output_grp.create_dataset(
            "/entry/sample/x_translation", shape=(n_frames,), dtype=numpy.float32
        )
        output_grp["/entry/sample/x_translation"].attrs["units"] = str(_ureg.meter)

        z_dataset = output_grp.create_dataset(
            "/entry/sample/y_translation", shape=(n_frames,), dtype=numpy.float32
        )
        output_grp["/entry/sample/y_translation"].attrs["units"] = str(_ureg.meter)

    #  --------->  and now fill all datasets!

    nf = 0

    external_datasets = []  # collect all urls created
    progress_v = 0
    if progress is not None:
        progress.set_postfix_str("write dark")

    def ignore(file_name):
        for forbid in _edf_to_ignore:
            if forbid in file_name:
                return True
        return False

    # darks

    # dark in acumulation mode?
    norm_dark = 1.0
    if scan.dark_n > 0 and DARK_ACCUM_FACT is True:
        norm_dark = len(dk_urls) / scan.dark_n
    dk_indexes = sorted(dk_urls.keys())

    for dk_index in dk_indexes:
        dk_url = dk_urls[dk_index]
        if ignore(os.path.basename(dk_url.file_path())):
            _logger.info("ignore " + dk_url.file_path())
            continue
        data, header, external_dataset, n_frames_in_file = _read_url(
            url=dk_url,
            i_frame=dk_index,
            h5group_to_dump=None,  # never create external dataset for dark
            frame_prefix="dark",
            configuration=configuration,
        )
        assert header is not None
        metadata.append(header)

        update_edf_source_files(url=dk_url, n_frames=n_frames_in_file)
        detector_data_urls.append((dk_url, True))
        if output_grp:
            if configuration.duplicate_data:
                data_dataset[nf, :, :] = data * norm_dark
            else:
                dark_dataset[nf, :, :] = data * norm_dark
            keys_dataset[nf] = ImageKey.DARK_FIELD.value
            keys_control_dataset[nf] = ImageKey.DARK_FIELD.value

            motor_pos_key = _get_valid_key(header, configuration.motor_position_keys)
            if motor_pos_key:
                str_mot_val = header[motor_pos_key].split(" ")
                if rot_angle_index == -1 or configuration.force_angle_calculation:
                    rotation_dataset[nf] = 0.0
                else:
                    rotation_dataset[nf] = float(str_mot_val[rot_angle_index])
                if x_trans_index == -1:
                    x_dataset[nf] = 0.0
                else:
                    x_dataset[nf] = (
                        (
                            float(str_mot_val[x_trans_index])
                            * configuration.x_translation_unit
                        )
                        .to(_ureg.meter)
                        .magnitude
                    )
                if y_trans_index == -1:
                    y_dataset[nf] = 0.0
                else:
                    y_dataset[nf] = (
                        (
                            float(str_mot_val[y_trans_index])
                            * configuration.y_translation_unit
                        )
                        .to(_ureg.meter)
                        .magnitude
                    )
                if z_trans_index == -1:
                    z_dataset[nf] = 0.0
                else:
                    z_dataset[nf] = (
                        (
                            float(str_mot_val[z_trans_index])
                            * configuration.z_translation_unit
                        )
                        .to(_ureg.meter)
                        .magnitude
                    )

            if srcur_index == -1:
                machine_current_dataset[nf] = (
                    (default_current * configuration.machine_current_unit)
                    .to(_ureg.ampere)
                    .magnitude
                )
            else:
                try:
                    str_counter_val = header.get("counter_pos", "").split(" ")
                    machine_current_dataset[nf] = (
                        (
                            float(str_counter_val[srcur_index])
                            * configuration.machine_current_unit
                        )
                        .to(_ureg.ampere)
                        .magnitude
                    )
                except IndexError:
                    machine_current_dataset[nf] = (
                        (default_current * configuration.machine_current_unit)
                        .to(_ureg.ampere)
                        .magnitude
                    )

            nf += 1
            if progress is not None:
                progress_v += 1 / (n_frames - 1)
                progress.n = (
                    _ESTIMATED_PERCENTAGE_TIME_TO_READ_METADATA
                    + progress_v * (100 - _ESTIMATED_PERCENTAGE_TIME_TO_READ_METADATA)
                )
                progress.refresh()

    ref_indexes = sorted(refs_urls.keys())

    ref_projs = []
    for irf in ref_indexes:
        pjnum = int(irf)
        if pjnum not in ref_projs:
            ref_projs.append(pjnum)

    # refs
    def store_refs(
        refIndexes,
        projnum,
        refUrls,
        nF,
        dataDataset,
        keysDataset,
        keysCDataset,
        xDataset,
        yDataset,
        zDataset,
        rotationDataset,
        raix,
        xtix,
        ytix,
        ztix,
    ):
        nfr = nF
        for ref_index in refIndexes:
            int_rf = int(ref_index)
            if int_rf == projnum:
                refUrl = refUrls[ref_index]
                if ignore(os.path.basename(refUrl.file_path())):
                    _logger.info("ignore " + refUrl.file_path())
                    continue
                data, header, external_data, n_frames_in_file = _read_url(
                    url=refUrl,
                    i_frame=ref_index,
                    h5group_to_dump=ext_datasets_grp,
                    frame_prefix="flat",
                    configuration=configuration,
                )
                update_edf_source_files(url=refUrl, n_frames=n_frames_in_file)
                if external_data is not None:
                    external_datasets.append(external_data)
                metadata.append(header)
                detector_data_urls.append((refUrl, False))

                if output_grp is None:
                    continue

                if configuration.duplicate_data and dataDataset:
                    dataDataset[nfr, :, :] = data
                keysDataset[nfr] = ImageKey.FLAT_FIELD.value
                keysCDataset[nfr] = ImageKey.FLAT_FIELD.value
                motor_pos_key = _get_valid_key(
                    header, configuration.motor_position_keys
                )

                if motor_pos_key in header:
                    str_mot_val = header[motor_pos_key].split(" ")
                    if raix == -1 or configuration.force_angle_calculation:
                        rotationDataset[nfr] = 0.0
                    else:
                        rotationDataset[nfr] = float(str_mot_val[raix])
                    if xtix == -1:
                        xDataset[nfr] = 0.0
                    else:
                        xDataset[nfr] = (
                            (
                                float(str_mot_val[xtix])
                                * configuration.x_translation_unit
                            )
                            .to(_ureg.meter)
                            .magnitude
                        )
                    if ytix == -1:
                        yDataset[nfr] = 0.0
                    else:
                        yDataset[nfr] = (
                            (
                                float(str_mot_val[ytix])
                                * configuration.y_translation_unit
                            )
                            .to(_ureg.meter)
                            .magnitude
                        )
                    if ztix == -1:
                        zDataset[nfr] = 0.0
                    else:
                        zDataset[nfr] = (
                            (
                                float(str_mot_val[ztix])
                                * configuration.z_translation_unit
                            )
                            .to(_ureg.meter)
                            .magnitude
                        )
                if srcur_index == -1:
                    machine_current_dataset[nfr] = (
                        (default_current * configuration.machine_current_unit)
                        .to(_ureg.ampere)
                        .magnitude
                    )
                else:
                    str_counter_val = header.get("counter_pos", "").split(" ")
                    try:
                        machine_current_dataset[nfr] = (
                            (
                                float(str_counter_val[srcur_index])
                                * configuration.machine_current_unit
                            )
                            .to(_ureg.ampere)
                            .magnitude
                        )
                    except IndexError:
                        machine_current_dataset[nfr] = (
                            (default_current * configuration.machine_current_unit)
                            .to(_ureg.ampere)
                            .magnitude
                        )

                nfr += 1

        return nfr

    # projections
    proj_indexes = sorted(proj_urls.keys())
    if progress is not None:
        progress.set_postfix_str("write projections and flats")
    nproj = 0
    iref_pj = 0

    if configuration.force_angle_calculation:
        if configuration.angle_calculation_rev_neg_scan_range and scan.scan_range < 0:
            proj_angles = numpy.linspace(
                0,
                scan.scan_range,
                scan.tomo_n,
                endpoint=configuration.angle_calculation_endpoint,
            )
        else:
            proj_angles = numpy.linspace(
                min(0, scan.scan_range),
                max(0, scan.scan_range),
                scan.tomo_n,
                endpoint=configuration.angle_calculation_endpoint,
            )
            revert_angles_in_nx = (
                configuration.angle_calculation_rev_neg_scan_range
                and (scan.scan_range < 0)
            )
            if revert_angles_in_nx:
                proj_angles = proj_angles[::-1]

    alignment_indices = []
    for i_proj, proj_index in enumerate(proj_indexes):
        proj_url = proj_urls[proj_index]
        if ignore(os.path.basename(proj_url.file_path())):
            _logger.info("ignore " + proj_url.file_path())
            continue

        # store refs if the ref serial number is = projection number
        if iref_pj < len(ref_projs) and ref_projs[iref_pj] == nproj:
            nf = store_refs(
                ref_indexes,
                ref_projs[iref_pj],
                refs_urls,
                nf,
                data_dataset,
                keys_dataset,
                keys_control_dataset,
                x_dataset,
                y_dataset,
                z_dataset,
                rotation_dataset,
                rot_angle_index,
                x_trans_index,
                y_trans_index,
                z_trans_index,
            )
            iref_pj += 1
        data, header, external_data, n_frames_in_file = _read_url(
            proj_url,
            i_frame=proj_index,
            h5group_to_dump=ext_datasets_grp,
            frame_prefix="proj",
            configuration=configuration,
        )
        update_edf_source_files(url=proj_url, n_frames=n_frames_in_file)
        detector_data_urls.append((proj_url, False))

        if output_grp:
            if external_data is not None:
                external_datasets.append(external_data)
            metadata.append(header)

            if configuration.duplicate_data:
                data_dataset[nf, :, :] = data
            keys_dataset[nf] = ImageKey.PROJECTION.value
            keys_control_dataset[nf] = ImageKey.PROJECTION.value
            if nproj >= scan.tomo_n:
                keys_control_dataset[nf] = ImageKey.ALIGNMENT.value

            motor_pos_key = _get_valid_key(header, configuration.motor_position_keys)

            if configuration.force_angle_calculation:
                if i_proj < len(proj_angles):
                    rotation_dataset[nf] = proj_angles[i_proj]
                else:
                    # case of return / control projection
                    rotation_dataset[nf] = 0.0

            if motor_pos_key in header:
                str_mot_val = header[motor_pos_key].split(" ")

                # continuous scan - rot angle is unknown. Compute it
                if not configuration.force_angle_calculation:
                    rotation_dataset[nf] = float(str_mot_val[rot_angle_index])

                if x_trans_index == -1:
                    x_dataset[nf] = 0.0
                else:
                    x_dataset[nf] = (
                        (
                            float(str_mot_val[x_trans_index])
                            * configuration.x_translation_unit
                        )
                        .to(_ureg.meter)
                        .magnitude
                    )
                if y_trans_index == -1:
                    y_dataset[nf] = 0.0
                else:
                    y_dataset[nf] = (
                        (
                            float(str_mot_val[y_trans_index])
                            * configuration.y_translation_unit
                        )
                        .to(_ureg.meter)
                        .magnitude
                    )
                if z_trans_index == -1:
                    z_dataset[nf] = 0.0
                else:
                    z_dataset[nf] = (
                        (
                            float(str_mot_val[z_trans_index])
                            * configuration.z_translation_unit
                        )
                        .to(_ureg.meter)
                        .magnitude
                    )
            if srcur_index == -1:
                machine_current_dataset[nf] = (
                    (default_current * configuration.machine_current_unit)
                    .to(_ureg.ampere)
                    .magnitude
                )
            else:
                try:
                    str_counter_val = header.get("counter_pos", "").split(" ")
                    machine_current_dataset[nf] = (
                        (
                            float(str_counter_val[srcur_index])
                            * configuration.machine_current_unit
                        )
                        .to(_ureg.ampere)
                        .magnitude
                    )
                except IndexError:
                    machine_current_dataset[nf] = (
                        (default_current * configuration.machine_current_unit)
                        .to(_ureg.ampere)
                        .magnitude
                    )
        nf += 1
        nproj += 1

        if progress is not None:
            progress_v += 1 / (n_frames - 1)
            progress.n = _ESTIMATED_PERCENTAGE_TIME_TO_READ_METADATA + progress_v * (
                100 - _ESTIMATED_PERCENTAGE_TIME_TO_READ_METADATA
            )
            progress.refresh()

    # we need to update alignement angles values. I wanted to avoid to redo all the previous existing processing.
    n_alignment_angles = len(alignment_indices)
    if n_alignment_angles == 3:
        alignments_angles = numpy.linspace(
            scan.scan_range,
            0,
            n_alignment_angles,
            endpoint=(n_alignment_angles % 2) == 0,
        )
        for index, angle in zip(alignment_indices, alignments_angles):
            rotation_dataset[index] = angle

    # store last flat if any remaining in the list
    if iref_pj < len(ref_projs) and output_grp:
        nf = store_refs(
            ref_indexes,
            ref_projs[iref_pj],
            refs_urls,
            nf,
            data_dataset,
            keys_dataset,
            keys_control_dataset,
            x_dataset,
            y_dataset,
            z_dataset,
            rotation_dataset,
            rot_angle_index,
            x_trans_index,
            y_trans_index,
            z_trans_index,
        )

    if output_grp:
        # if we avoided data duplication: create the virtual dataset on top of the external datasets
        if not configuration.duplicate_data:
            virtual_layout = h5py.VirtualLayout(
                shape=(n_frames, scan.dim_2, scan.dim_1),
                dtype=frame_type,
            )
            virtual_layout[0:n_darks] = h5py.VirtualSource(dark_dataset)
            for i_ext, external_dataset in enumerate(external_datasets):
                assert isinstance(external_dataset, h5py.Dataset)
                virtual_layout[i_ext + n_darks] = h5py.VirtualSource(external_dataset)
            output_grp.create_virtual_dataset(
                "/entry/instrument/detector/data",
                virtual_layout,
            )

        # we can add some more NeXus look and feel
        output_grp["/entry"].attrs["NX_class"] = "NXentry"
        output_grp["/entry"].attrs["definition"] = "NXtomo"
        output_grp["/entry"].attrs["version"] = converter_version()
        output_grp["/entry/instrument"].attrs["NX_class"] = "NXinstrument"
        output_grp["/entry/instrument/detector"].attrs["NX_class"] = "NXdetector"
        output_grp["/entry/instrument/detector/data"].attrs["interpretation"] = "image"
        if configuration.field_of_view is not None:
            field_of_view = configuration.field_of_view
        elif abs(scan.scan_range) == 180:
            field_of_view = "Full"
        elif abs(scan.scan_range) == 360:
            field_of_view = "Half"

        if field_of_view is not None:
            field_of_view = FieldOfView(field_of_view)
            output_grp["/entry/instrument/detector/field_of_view"] = field_of_view.value

        output_grp["/entry/sample"].attrs["NX_class"] = "NXsample"
        output_grp["/entry/definition"] = "NXtomo"
        source_grp = output_grp["/entry/instrument"].get("source", None)
        if source_grp is not None and "NX_class" not in source_grp.attrs:
            source_grp.attrs["NX_class"] = "NXsource"

        output_grp.flush()

        for i_meta, meta in enumerate(metadata):
            # save metadata
            dicttoh5(
                meta,
                fileout_h5,
                h5path=f"/entry/instrument/positioners/{i_meta}",
                update_mode="replace",
                mode="a",
            )

        try:
            create_nx_data_group(
                file_path=fileout_h5,
                entry_path=output_data_path,
                axis_scale=["linear", "linear"],
            )
        except Exception as e:
            _logger.error(f"Fail to create NXdata group. Reason is {e}")

        # create beam group at root for compatibility
        try:
            link_nxbeam_to_root(file_path=fileout_h5, entry_path=output_data_path)
        except Exception as e:
            _logger.error(f"Fail to link nx beam. Error is {e}")
        if progress is not None:
            print("\nconversion finished\n")

    if output_grp is not None:
        # if the output group is provided then close it so we can safely read it back
        # it should be done outside this function but this is legacy code that won't evolve
        output_grp.close()
    # do some check on the conversion
    issues_discovered = []
    for output_check in configuration.output_checks:
        print("\nstart output checks\n")
        from nxtomomill.converter.edf import checks as _checks_utils

        output_check = _checks_utils.OUPUT_CHECK(output_check)
        if output_check is _checks_utils.OUPUT_CHECK.COMPARE_VOLUME:
            issues = _checks_utils.compare_volumes(
                edf_volume_as_urls=detector_data_urls,
                hdf5_scan=NXtomoScan(fileout_h5, output_data_path),
            )
        else:
            raise ValueError(f"{output_check} is not handled")
        issues_discovered.extend(issues)
    if len(issues_discovered) > 0:
        raise ValueError("Seems the conversion failed. Detected issues are {errs}")
    elif len(configuration.output_checks) > 0:
        print("\noutput checks done, no issues detected\n")

    if configuration.delete_edf_source_files:
        print("start edf source files removal")
        assert (
            configuration.duplicate_data
        ), "if data is not duplicated this make no sense to remove the edf files"
        for file_path, (n_frames, used_urls) in edf_source_files.items():
            if n_frames > len(used_urls):
                _logger.warning(
                    f"Will not delete {file_path}. Only {len(used_urls)} used on the {n_frames} contained"
                )
            else:
                try:
                    os.remove(file_path)
                except OSError as e:
                    _logger.error(f"Issue when removing {file_path}. Error is {e}")

    return fileout_h5, output_data_path


def _get_valid_key(header: dict, keys: tuple) -> str | None:
    """Return the first existing key in header"""
    for key in keys:
        if key in header:
            return key
    else:
        return None


def _get_valid_key_index(motors: list, keys: tuple) -> int | None:
    for key in keys:
        if key in motors:
            return motors.index(key)
    else:
        return -1


def _read_url(
    url,
    h5group_to_dump: h5py.Group,
    i_frame: int,
    frame_prefix: str,
    configuration: EDF2nxModel,
) -> tuple:
    """
    if h5group_to_dump is provided then it will create a dataset with external data to
    the EDF file under the name `frame_{i}`
    This way we will be able to create a virtual
    """
    data_slice = url.data_slice()
    if data_slice is None:
        data_slice = (0,)
    if data_slice is None or len(data_slice) != 1:
        raise ValueError(f"Fabio slice expect a single frame but {data_slice} found")
    index = data_slice[0]
    if not isinstance(index, int):
        raise ValueError(f"Fabio slice expect a single integer but {data_slice} found")

    try:
        fabio_file = fabio.open(url.file_path())
    except Exception:
        _logger.debug(
            f"Error while opening {url.file_path()} with fabio", exc_info=True
        )
        raise IOError(
            f"Error while opening {url.path()} with fabio (use debug for more information)"
        )

    try:
        n_frames_in_file = fabio_file.nframes
        if n_frames_in_file == 1:
            if index != 0:
                raise ValueError(
                    f"Only a single frame available. Slice {index} out of range"
                )
            it = fabio.edfimage.EdfImage.lazy_iterator(url.file_path())
            frame = next(it)
        else:
            frame = fabio_file.getframe(index)
        data = frame.data
        header = frame.header
        frame_start_offset = frame.start
        blobsize = frame.blobsize
        byte_order = get_byte_order(frame.header)
    except Exception as e:
        _logger.error(e)
        data = None
        header = None
        frame_start_offset = None
        blobsize = None
        byte_order = None
    finally:
        fabio_file.close()
        fabio_file = None

    if data is not None and byte_order is None:
        raise ValueError("Unable to get ByteOrder for file_path")

    if h5group_to_dump is not None and data is not None:
        frame_start = frame_start_offset + blobsize - (data.size * data.dtype.itemsize)
        frame_end = frame_start + blobsize
        dataset_name = f"{frame_prefix}_{i_frame}"
        data_type = numpy.dtype(byte_order + data.dtype.char)
        if configuration.external_link_type is PathType.ABSOLUTE:
            file_path = os.path.abspath(url.file_path())
        elif configuration.external_link_type is PathType.RELATIVE:
            file_path = os.path.abspath(url.file_path())
            file_path = os.path.relpath(
                os.path.abspath(file_path),
                os.path.abspath(os.path.dirname(configuration.output_file)),
            )
            file_path = "./" + file_path
        else:
            raise NotImplementedError
        external_dataset = h5group_to_dump.create_dataset(
            name=dataset_name,
            shape=data.shape,
            dtype=data_type,
            external=[
                (file_path, frame_start, frame_end),
            ],
        )
    else:
        external_dataset = None
    return data, header, external_dataset, n_frames_in_file


def _getExtraInfo(scan, configuration):
    assert isinstance(scan, EDFTomoScan)
    projections_urls = scan.projections
    if len(projections_urls) == 0:
        raise ValueError(
            f"No projections found in {scan.path} with dataset basename: {configuration.dataset_basename if configuration.dataset_basename is not None else 'Default'} and dataset info file: {configuration.dataset_info_file if configuration.dataset_info_file is not None else 'Default'}. "
        )
    indexes = sorted(projections_urls.keys())
    first_proj_file = projections_urls[indexes[0]]
    fid = fabio.open(first_proj_file.file_path())

    rotangle_index = -1
    xtrans_index = -1
    ytrans_index = -1
    ztrans_index = -1
    srcur_index = -1
    frame_type = None

    try:
        if hasattr(fid, "header"):
            hd = fid.header
        else:
            hd = fid.getHeader()
        motor_mne_key = _get_valid_key(hd, configuration.motor_mne_keys)
        motors = hd.get(motor_mne_key, "").split(" ")
        counters = hd.get("counter_mne", "").split(" ")
        rotangle_index = _get_valid_key_index(motors, configuration.rotation_angle_keys)
        xtrans_index = _get_valid_key_index(motors, configuration.x_translation_keys)
        ytrans_index = _get_valid_key_index(motors, configuration.y_translation_keys)
        ztrans_index = _get_valid_key_index(motors, configuration.z_translation_keys)
        srcur_index = _get_valid_key_index(counters, configuration.machine_current_keys)

        if hasattr(fid, "bytecode"):
            frame_type = fid.bytecode
        else:
            frame_type = fid.getByteCode()
    finally:
        fid.close()
        fid = None

    return (
        frame_type,
        rotangle_index,
        xtrans_index,
        ytrans_index,
        ztrans_index,
        srcur_index,
    )


def get_byte_order(header):
    """
    byte_order (as a str compatible with numpy data types)
    """
    byte_order = header.get("ByteOrder", None)
    if byte_order is None:
        pass
    elif byte_order.lower() == "highbytefirst":
        byte_order = ">"
    elif byte_order.lower() == "lowbytefirst":
        byte_order = "<"
    return byte_order
