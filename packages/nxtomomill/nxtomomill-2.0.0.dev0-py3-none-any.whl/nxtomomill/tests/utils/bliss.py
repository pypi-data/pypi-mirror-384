# coding: utf-8

from __future__ import annotations

import datetime
import os

import numpy
import h5py
from tomoscan.io import HDF5File


class MockBlissAcquisition:
    """

    :param n_sequence: number of sequence to create
    :param n_scan_per_sequence: number of scans (projection series) per sequence
    :param n_projections_per_scan: number of projection frame in a scan
    :param n_darks: number of dark frame in the series. Only one series at the
                    beginning
    :param n_flats: number of flats to create. In this case will only
                        create one series of n flats after dark if any
    :param output_dir: will contain the proposal file and one folder per
                           sequence.
    :param str acqui_type: acquisition type. Can be "basic", "multitomo", "zseries-v1", "zseries-v3
    :param Iterable z_values: if acqui_type is zseries then users should
                              provide the serie of values for z (one per stage)
    :param nb_loop: number of multitomo loop for v1 of bliss multitomo
    :param nb_tomo: number of tomo per loop for v1 of bliss multitomo
    :param nb_turns: number of turns for v2 of bliss multitomo ( <=> nb NXtomo to generate)
    :param file_name_prefix: bliss file prefix name
    :param file_name_z_fill: optional z fill for the file name index. If None then file index will not be 'z filled'
    :param create_tomo_config: if True create the 'tomo_config' group under instrument which contains
                                    metadata describing the acquisition (which dataset to read for rotation, translation ...)
    """

    def __init__(
        self,
        n_sample,
        n_sequence,
        n_scan_per_sequence,
        n_darks,
        n_flats,
        output_dir,
        with_nx_detector_attr=True,
        detector_name="pcolinux",
        acqui_type="basic",
        z_values=None,
        nb_loop=None,
        nb_tomo=None,
        nb_turns=None,
        with_rotation_motor_info=True,
        frame_data_type=numpy.uint16,
        file_name_prefix="sample",
        file_name_z_fill=None,
        create_tomo_config: bool = True,
        ebs_tomo_version: str | None = None,
        z_series_v_3_options=None,
        rotation_is_clockwise: bool = False,
    ):
        self._n_darks = n_darks
        self._n_flats = n_flats
        self._n_scan_per_sequence = n_scan_per_sequence
        self.__folder = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.__proposal_file = os.path.join(self.__folder, "ihproposal_file.h5")
        if acqui_type not in ("pcotomo", "multitomo"):
            if nb_loop is not None or nb_tomo is not None:
                raise ValueError(
                    "nb_loop and nb_tomo are only handled by acqui_type: `multitomo`"
                )
        else:
            if not (
                nb_turns is not None or (nb_loop is not None and nb_tomo is not None)
            ):
                raise ValueError(
                    "nb_turns should be provided or nb_loop and nb_tomo must be provided"
                )

        # create sample
        self.__samples = []
        for sample_i in range(n_sample):
            if file_name_z_fill is None:
                dir_name = f"{file_name_prefix}_{sample_i}"
            else:
                dir_name = f"{file_name_prefix}_{str(sample_i).zfill(file_name_z_fill)}"
            sample_dir = os.path.join(self.path, dir_name)
            os.mkdir(sample_dir)
            sample_file = os.path.join(sample_dir, dir_name + ".h5")
            if acqui_type == "basic":
                acqui_tomo = _BlissBasicTomo(
                    sample_dir=sample_dir,
                    sample_file=sample_file,
                    n_sequence=n_sequence,
                    n_scan_per_sequence=n_scan_per_sequence,
                    n_darks=n_darks,
                    n_flats=n_flats,
                    with_nx_detector_attr=with_nx_detector_attr,
                    detector_name=detector_name,
                    with_rotation_motor_info=with_rotation_motor_info,
                    frame_data_type=frame_data_type,
                    create_tomo_config=create_tomo_config,
                    ebs_tomo_version=ebs_tomo_version,
                    rotation_is_clockwise=rotation_is_clockwise,
                )
            elif acqui_type in ("pcotomo", "multitomo"):
                acqui_tomo = _BlissMultiTomo(
                    sample_dir=sample_dir,
                    sample_file=sample_file,
                    n_sequence=n_sequence,
                    n_scan_per_sequence=n_scan_per_sequence,
                    n_darks=n_darks,
                    n_flats=n_flats,
                    with_nx_detector_attr=with_nx_detector_attr,
                    detector_name=detector_name,
                    with_rotation_motor_info=with_rotation_motor_info,
                    nb_loop=nb_loop,
                    nb_tomo=nb_tomo,
                    nb_turns=nb_turns,
                    frame_data_type=frame_data_type,
                    create_tomo_config=create_tomo_config,
                    ebs_tomo_version=ebs_tomo_version,
                    rotation_is_clockwise=rotation_is_clockwise,
                )
            elif acqui_type in ("z-series-v1", "z-series-v3"):
                if z_values is None:
                    raise ValueError("for z-series z_values should be provided")
                acqui_tomo = _BlissZseriesTomo(
                    sample_dir=sample_dir,
                    sample_file=sample_file,
                    n_sequence=n_sequence,
                    n_scan_per_sequence=n_scan_per_sequence,
                    n_darks=n_darks,
                    n_flats=n_flats,
                    with_nx_detector_attr=with_nx_detector_attr,
                    detector_name=detector_name,
                    z_values=z_values,
                    with_rotation_motor_info=with_rotation_motor_info,
                    frame_data_type=frame_data_type,
                    create_tomo_config=create_tomo_config,
                    ebs_tomo_version=ebs_tomo_version,
                    z_series_version=acqui_type.split("-")[-1],
                    z_series_v_3_options=z_series_v_3_options,
                    rotation_is_clockwise=rotation_is_clockwise,
                )
            else:
                raise NotImplementedError("")
            self.__samples.append(acqui_tomo)

    @property
    def samples(self):
        return self.__samples

    @property
    def proposal_file(self):
        # for now a simple file
        return self.__proposal_file

    @property
    def path(self):
        return self.__folder


class _BlissSample:
    """
    Simple mock of a bliss sample. For now we only create the hierarchy of
    files.
    """

    def __init__(
        self,
        sample_dir,
        sample_file,
        n_sequence,
        n_scan_per_sequence,
        n_darks,
        n_flats,
        detector_name,
        with_nx_detector_attr=True,
        with_rotation_motor_info=True,
        frame_data_type=numpy.uint16,
        create_tomo_config: bool = True,
        ebs_tomo_version: str | None = None,
        rotation_is_clockwise: bool = False,
    ):
        self._with_nx_detector_attr = with_nx_detector_attr
        self._sample_dir = sample_dir
        self._sample_file = sample_file
        self._n_sequence = n_sequence
        self._n_scan_per_seq = n_scan_per_sequence
        self._n_darks = n_darks
        self._n_flats = n_flats
        self._scan_folders = []
        self._index = 1
        self._detector_name = detector_name
        self._det_width = 64
        self._det_height = 64
        self._tomo_n = 10
        self._energy = 19.0
        self._sample_detector_distance = 100.0  # in mm
        self._source_sample_distance = 52000.0  # in mm
        self._sample_pixel_size = (0.0065, 0.0066)
        self._detector_pixel_size = (0.00022, 0.00022)
        self._with_rotation_motor_info = with_rotation_motor_info
        self._frame_data_type = frame_data_type
        self._create_tomo_config = create_tomo_config
        self._ebs_tomo_version = ebs_tomo_version
        assert isinstance(rotation_is_clockwise, bool)
        self._rotation_is_clockwise = rotation_is_clockwise
        for _ in range(n_sequence):
            self.add_sequence()

    @property
    def frame_data_type(self):
        return self._frame_data_type

    def get_next_free_index(self):
        idx = self._index
        self._index += 1
        return idx

    @property
    def current_scan_index(self) -> int:
        return self._index - 1

    def get_main_entry_title(self):
        raise NotImplementedError("Base class")

    @staticmethod
    def get_title(scan_type):
        if scan_type == "dark":
            return "dark images"
        elif scan_type == "flat":
            return "reference images 1"
        elif scan_type == "projection":
            return "projections 1 - 2000"
        else:
            raise ValueError("Not implemented")

    def create_entry_and_technique(self, seq_ini_index):
        # add sequence init information
        with HDF5File(self.sample_file, mode="a") as h5f:
            seq_node = h5f.require_group(str(seq_ini_index) + ".1")
            seq_node.attrs["NX_class"] = "NXentry"
            seq_node["title"] = self.get_main_entry_title()
            seq_node.require_group("instrument/positioners")
            # write energy
            seq_node["technique/scan/energy"] = self._energy
            seq_node["technique/scan/tomo_n"] = self._tomo_n * self._n_scan_per_seq
            seq_node["technique/scan/sample_detector_distance"] = (
                self._sample_detector_distance
            )
            seq_node["technique/scan/sample_detector_distance"].attrs["units"] = "mm"
            seq_node["technique/scan/source_sample_distance"] = (
                self._source_sample_distance
            )
            seq_node["technique/scan/source_sample_distance"].attrs["units"] = "mm"
            seq_node["technique/optic/sample_pixel_size"] = numpy.asarray(
                self._sample_pixel_size
            )
            seq_node["technique/detector/pixel_size"] = numpy.asarray(
                self._detector_pixel_size
            )
            seq_node["start_time"] = str(datetime.datetime.now())
            seq_node["end_time"] = str(
                datetime.datetime.now() + datetime.timedelta(minutes=10)
            )
            if self._create_tomo_config:
                self._add_tomo_config(seq_node)

    @staticmethod
    def get_next_group_name(seq_ini_index, scan_idx):
        return str(scan_idx) + ".1"

    def add_scan(
        self,
        scan_type,
        seq_ini_index,
        z_value,
        skip_title=False,
        nb_loop=None,
        nb_tomo=None,
        nb_turns=1,
    ):
        """
        :param nb_loop: number of loop in multitomo use case. Else must be 1
        :param nb_tomo: number of tomography done in multitomo 'per iteration' use case. Else must be 1
        """
        scan_idx = self.get_next_free_index()
        scan_name = str(scan_idx).zfill(4)
        scan_path = os.path.join(self.path, scan_name)
        self._scan_folders.append(_BlissScan(folder=scan_path, scan_type=scan_type))
        if nb_turns is not None:
            nb_nxtomo = nb_turns
            if nb_tomo is not None or nb_loop is not None:
                raise ValueError(
                    "nb_tomo and nb_loop should be provided or nb_turns. Not both"
                )
        elif nb_loop is not None and nb_tomo is not None:
            nb_nxtomo = nb_loop * nb_tomo
            if nb_turns is not None:
                raise ValueError(
                    "nb_tomo and nb_loop should be provided or nb_turns. Not both"
                )
        else:
            raise ValueError(
                "nb_tomo and nb_loop should be provided or nb_turns. None provided"
            )
        # register the scan information
        with HDF5File(self.sample_file, mode="a") as h5f:
            seq_node = h5f.require_group(str(scan_idx) + ".1")
            if "start_time" not in seq_node:
                seq_node["start_time"] = str(datetime.datetime.now())
            # write title
            title = self.get_title(scan_type=scan_type)
            if not skip_title:
                seq_node["title"] = title
            # write data
            data = (
                numpy.random.random(
                    self._det_height * self._det_width * self._tomo_n * nb_nxtomo
                )
                * 256
            )
            n_frames = self._tomo_n * nb_nxtomo
            data = data.reshape(n_frames, self._det_height, self._det_width)
            data = data.astype(self.frame_data_type)
            det_path_1 = "/".join(("instrument", self._detector_name))
            det_grp = seq_node.require_group(det_path_1)
            det_grp["data"] = data
            if self._with_nx_detector_attr:
                det_grp.attrs["NX_class"] = "NXdetector"
            acq_grp = det_grp.require_group("acq_parameters")
            acq_grp["acq_expo_time"] = 4
            det_path_2 = "/".join(("technique", "scan", self._detector_name))
            seq_node[det_path_2] = data
            seq_node.attrs["NX_class"] = "NXentry"

            # write rotation angle value and translations
            instrument_group = seq_node.require_group("instrument")
            positioners_grp = instrument_group.require_group("positioners")
            positioners_grp["hrsrot"] = numpy.linspace(
                start=0.0, stop=360, num=n_frames
            )
            positioners_grp["sx"] = numpy.array(numpy.random.random(size=n_frames))
            positioners_grp["sy"] = numpy.random.random(size=n_frames)
            positioners_grp["sz"] = numpy.asarray([z_value] * n_frames)
            positioners_grp["yrot"] = numpy.random.random(size=n_frames)
            if self._with_rotation_motor_info:
                scan_node = seq_node.require_group("technique/scan")
                scan_node["motor"] = ("rotation", "hrsrot", "srot")

            if self._ebs_tomo_version is not None:
                technique_group = seq_node.require_group("technique")
                technique_group.attrs["tomo_version"] = self._ebs_tomo_version

    def _add_tomo_config(self, group: h5py.Group):
        technique_group = group.require_group("technique")
        tomo_config_group = technique_group.require_group("tomoconfig")
        tomo_config_group["rotation"] = ["hrsrot"]
        tomo_config_group["detector"] = [
            self._detector_name,
        ]
        tomo_config_group["sample_x"] = ["sx"]
        tomo_config_group["sample_y"] = ["sy"]
        tomo_config_group["translation_z"] = ["sz"]
        tomo_config_group["translation_y"] = ["yrot"]
        tomo_config_group["rotation_is_clockwise"] = self._rotation_is_clockwise

    def add_sequence(self):
        """Add a sequence to the bliss file"""
        raise NotImplementedError("Base class")

    @property
    def path(self):
        return self._sample_dir

    @property
    def sample_directory(self):
        return self._sample_dir

    @property
    def sample_file(self):
        return self._sample_file

    def scans_folders(self):
        return self._scan_folders

    @property
    def n_darks(self):
        return self._n_darks

    @property
    def with_rotation_motor_info(self):
        return self._with_rotation_motor_info


class _BlissScan:
    """
    mock of a bliss scan
    """

    def __init__(self, folder, scan_type: str):
        assert scan_type in ("dark", "flat", "projection")
        self.__path = folder

    def path(self):
        return self.__path


class _BlissBasicTomo(_BlissSample):
    def get_main_entry_title(self):
        return "tomo:fullturn"

    def add_sequence(self):
        # reserve the index for the 'initialization' sequence. No scan folder
        # will be created for this one.
        seq_ini_index = self.get_next_free_index()

        self.create_entry_and_technique(seq_ini_index=seq_ini_index)

        if self.n_darks > 0:
            self.add_scan(scan_type="dark", seq_ini_index=seq_ini_index, z_value=1)

        if self._n_flats > 0:
            self.add_scan(scan_type="flat", seq_ini_index=seq_ini_index, z_value=1)

        for _ in range(self._n_scan_per_seq):
            self.add_scan(
                scan_type="projection", seq_ini_index=seq_ini_index, z_value=1
            )


class _BlissMultiTomo(_BlissSample):
    def __init__(
        self,
        sample_dir,
        sample_file,
        n_sequence,
        n_scan_per_sequence,
        n_darks,
        n_flats,
        detector_name,
        with_nx_detector_attr=True,
        with_rotation_motor_info=True,
        nb_loop=None,
        nb_tomo=None,
        nb_turns=1,
        frame_data_type=numpy.uint16,
        create_tomo_config: bool = True,
        ebs_tomo_version=None,
        rotation_is_clockwise: bool = False,
    ):
        self.nb_loop = nb_loop
        self.nb_tomo = nb_tomo
        self.nb_turns = nb_turns
        super().__init__(
            sample_dir,
            sample_file,
            n_sequence,
            n_scan_per_sequence,
            n_darks,
            n_flats,
            detector_name,
            with_nx_detector_attr,
            with_rotation_motor_info=with_rotation_motor_info,
            frame_data_type=frame_data_type,
            create_tomo_config=create_tomo_config,
            ebs_tomo_version=ebs_tomo_version,
            rotation_is_clockwise=rotation_is_clockwise,
        )
        if nb_loop is not None and nb_tomo is not None:
            if nb_turns is not None:
                raise ValueError(
                    "All of nb_loop, nb_tomo and nb_turns provided. Unable to deduce the pcotomo version"
                )
            multitomo_version = 1
        elif nb_turns is not None:
            multitomo_version = 2
        else:
            multitomo_version = None
        if multitomo_version is not None:
            # write Bliss version in attrs
            with HDF5File(self.sample_file, mode="a") as h5f:
                if "creator_version" not in h5f.attrs:
                    if multitomo_version == 1:
                        h5f.attrs["creator_version"] = "1.2.3"
                    if multitomo_version == 2:
                        h5f.attrs["creator_version"] = "1.10.0"

    def get_main_entry_title(self):
        return "tomo:multitomo"

    def add_sequence(self):
        # reserve the index for the 'initialization' sequence. No scan folder
        # will be created for this one.
        seq_ini_index = self.get_next_free_index()

        self.create_entry_and_technique(seq_ini_index=seq_ini_index)

        # start dark
        if self.n_darks > 0:
            self.add_scan(scan_type="dark", seq_ini_index=seq_ini_index, z_value=1)

        # start flat
        if self._n_flats > 0:
            self.add_scan(scan_type="flat", seq_ini_index=seq_ini_index, z_value=1)

        for _ in range(self._n_scan_per_seq):
            self.add_scan(
                scan_type="projection",
                seq_ini_index=seq_ini_index,
                z_value=1,
                nb_loop=self.nb_loop,
                nb_tomo=self.nb_tomo,
                nb_turns=self.nb_turns,
            )

        # end flat
        if self._n_flats > 0:
            self.add_scan(scan_type="flat", seq_ini_index=seq_ini_index, z_value=1)

    def add_scan(
        self,
        scan_type,
        seq_ini_index,
        z_value,
        skip_title=False,
        nb_loop=None,
        nb_tomo=None,
        nb_turns=1,
    ):
        super().add_scan(
            scan_type, seq_ini_index, z_value, skip_title, nb_loop, nb_tomo, nb_turns
        )
        if scan_type == "projection":
            # register multi-tomo specific informations (only for projections)
            with HDF5File(self.sample_file, mode="a") as h5f:
                seq_node = h5f.require_group(str(self._index - 1) + ".1")

                scan_grp = seq_node.require_group("technique/proj")
                if nb_loop is not None and "nb_loop" not in scan_grp:
                    scan_grp["nb_loop"] = nb_loop
                if nb_tomo is not None and "nb_tomo" not in scan_grp:
                    scan_grp["nb_tomo"] = nb_tomo
                if nb_turns is not None and "nb_turns" not in scan_grp:
                    scan_grp["nb_turns"] = nb_turns
                if "tomo_n" not in scan_grp:
                    scan_grp["tomo_n"] = self._tomo_n


class _BlissZseriesTomo(_BlissSample):
    def __init__(
        self,
        sample_dir,
        sample_file,
        n_sequence,
        n_scan_per_sequence,
        n_darks,
        n_flats,
        detector_name,
        z_values,
        z_series_version: str,
        with_nx_detector_attr=True,
        with_rotation_motor_info=True,
        frame_data_type=numpy.uint16,
        create_tomo_config: bool = True,
        ebs_tomo_version: str = None,
        z_series_v_3_options=None,
        rotation_is_clockwise: bool = False,
    ):
        assert z_series_version in ("v1", "v3")
        self.z_series_version = z_series_version
        self._z_values = z_values
        self._z_series_v_3_options = z_series_v_3_options
        super().__init__(
            sample_dir=sample_dir,
            sample_file=sample_file,
            n_sequence=n_sequence,
            n_scan_per_sequence=n_scan_per_sequence,
            n_darks=n_darks,
            n_flats=n_flats,
            detector_name=detector_name,
            with_nx_detector_attr=with_nx_detector_attr,
            with_rotation_motor_info=with_rotation_motor_info,
            frame_data_type=frame_data_type,
            create_tomo_config=create_tomo_config,
            ebs_tomo_version=ebs_tomo_version,
            rotation_is_clockwise=rotation_is_clockwise,
        )

    def get_main_entry_title(self):
        return "tomo:zseries"

    def create_dark_at_start(self) -> bool:
        if self.z_series_version == "v1":
            return True
        else:
            return self._z_series_v_3_options["dark_at_start"]

    def create_flat_at_start(self) -> bool:
        if self.z_series_version == "v1":
            return True
        else:
            return self._z_series_v_3_options["flat_at_start"]

    def create_dark_at_end(self) -> bool:
        if self.z_series_version == "v1":
            return True
        else:
            return self._z_series_v_3_options["dark_at_end"]

    def create_flat_at_end(self) -> bool:
        if self.z_series_version == "v1":
            return True
        else:
            return self._z_series_v_3_options["flat_at_end"]

    def create_intermediary_flat(self) -> bool:
        return self.z_series_version == "v1"

    def create_intermediary_dark(self) -> bool:
        return self.z_series_version == "v1"

    def add_sequence(self):
        # reserve the index for the 'initialization' sequence. No scan folder
        # will be created for this one.

        if self.z_series_version == "v1":
            seq_ini_index = self.get_next_free_index()
            self.create_entry_and_technique(seq_ini_index=seq_ini_index)

        for z_value in self._z_values:
            if self.z_series_version == "v3":
                seq_ini_index = self.get_next_free_index()
                self.create_entry_and_technique(seq_ini_index=seq_ini_index)

            if z_value == self._z_values[0]:
                create_dark = self.create_dark_at_start()
                create_flat = self.create_flat_at_start()
            elif z_value == self._z_values[-1]:
                create_dark = self.create_dark_at_end()
                create_flat = self.create_flat_at_end()
            else:
                create_dark = self.create_intermediary_dark()
                create_flat = self.create_intermediary_flat()

            if create_dark and self.n_darks > 0:
                self.add_scan(
                    scan_type="dark", seq_ini_index=seq_ini_index, z_value=z_value
                )

            if create_flat and self._n_flats > 0:
                self.add_scan(
                    scan_type="flat", seq_ini_index=seq_ini_index, z_value=z_value
                )

            for _ in range(self._n_scan_per_seq):
                self.add_scan(
                    scan_type="projection", seq_ini_index=seq_ini_index, z_value=z_value
                )

    def create_entry_and_technique(self, seq_ini_index):
        super().create_entry_and_technique(seq_ini_index=seq_ini_index)
        # add sequence init information
        if self.z_series_version == "v3":
            with HDF5File(self.sample_file, mode="a") as h5f:
                seq_node = h5f.require_group(str(seq_ini_index) + ".1")
                seq_node.attrs["NX_class"] = "NXentry"
                # write scab flags
                seq_node["technique/scan_flags/dark_images_at_start"] = (
                    self._z_series_v_3_options["dark_at_start"]
                )
                seq_node["technique/scan_flags/dark_images_at_end"] = (
                    self._z_series_v_3_options["dark_at_end"]
                )
                seq_node["technique/scan_flags/ref_images_at_start"] = (
                    self._z_series_v_3_options["flat_at_start"]
                )
                seq_node["technique/scan_flags/ref_images_at_end"] = (
                    self._z_series_v_3_options["flat_at_end"]
                )

    def add_scan(
        self,
        scan_type,
        seq_ini_index,
        z_value,
        skip_title=False,
        nb_loop=None,
        nb_tomo=None,
        nb_turns=1,
    ):
        super().add_scan(
            scan_type, seq_ini_index, z_value, skip_title, nb_loop, nb_tomo, nb_turns
        )
        with HDF5File(self.sample_file, mode="a") as h5f:
            seq_node = h5f.require_group(str(self.current_scan_index) + ".1")
            seq_node["sample/name"] = "mysample_0000"
