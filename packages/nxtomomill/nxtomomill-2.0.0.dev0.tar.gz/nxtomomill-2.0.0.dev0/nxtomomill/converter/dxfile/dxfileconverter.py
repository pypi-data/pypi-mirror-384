# coding: utf-8

"""
module to convert from dx file (hdf5) to nexus tomo compliant .nx (hdf5)
"""

from __future__ import annotations

import logging
import os
import pint

import h5py
import numpy
from silx.io.url import DataUrl
from silx.io.utils import get_data, h5py_read_dataset
from tomoscan.io import HDF5File
from nxtomo.nxobject.nxdetector import FieldOfView, ImageKey
from nxtomo.utils.frameappender import FrameAppender

from nxtomomill.converter.baseconverter import BaseConverter
from nxtomomill.converter.version import version as converter_version
from nxtomomill.models.dx2nx import DX2nxModel

from nxtomomill.utils.hdf5 import DatasetReader, EntryReader
from silx.utils.deprecation import deprecated

_ureg = pint.get_application_registry()
_logger = logging.getLogger(__name__)


__all__ = ["from_dx_to_nx", "from_dx_config_to_nx"]


# dev note: to ensure backward compatibility we needed to keep from_dx_to_nx. And we created from_dx_config_to_nx to handle the configuration file.
# but with time we expect to remove `from_dx_to_nx` and them rename from_dx_config_to_nx to `from_dx_to_nx` in order to get something coherent.
@deprecated(
    replacement="from_dx_config_to_nx",
    since_version="0.13",
    reason="Some configuration dedicated classes exists for tuning the configuration directly instead of provided n parameter to the function.",
)
def from_dx_to_nx(
    input_file: str,
    output_file: str | None = None,
    file_extension: str = ".nx",
    duplicate_data: bool = True,
    input_entry: str = "/",
    output_entry: str = "entry0000",
    scan_range: tuple = (0.0, 180.0),
    pixel_size=(None, None),
    field_of_view: FieldOfView | str | None = None,
    distance: float | None = None,
    overwrite: bool = True,
    energy: float | None = None,
) -> tuple:
    """

    :param input_file: dxfile to convert
    :param output_file: output file to save
    :param file_extension: file extension to give if the output file is
        not provided.
    :param duplicate_data: if True frames will be duplicated. Otherwise
        we will create (relative) link to the input file.
    :param input_entry: path to the HDF5 group to convert. For now it looks
        each file can only contain one dataset. Just to ensure any future
        compatibility if it evolve with time.
    :param output_entry: path to store the NxTomo created.
    :param scan_range: tuple of two elements with the minimum scan range.
        Projections are expected to be taken with equal angular spaces.
    :param pixel_size: pixel size can be provided (in meter and as
        x_pizel_size, y_pixel_size)
    :param field_of_view: field of view
    :param distance: sample / detector distance in meter
    :param overwrite: if True and if the entry already exists in the
        output file then will overwrite it.
    :return: tuple of (output_file, entry) created. For now the list should
        contain at most one of those tuple
    """
    configuration = DX2nxModel(input_file=input_file, output_file=output_file)
    configuration.file_extension = file_extension
    configuration.copy_data = duplicate_data
    configuration.input_entry = input_entry
    configuration.output_entry = output_entry
    configuration.scan_range = scan_range
    configuration.pixel_size = pixel_size
    configuration.field_of_view = field_of_view
    configuration.sample_detector_distance = distance
    configuration.overwrite = overwrite
    configuration.energy = energy
    return from_dx_config_to_nx(configuration=configuration)


def from_dx_config_to_nx(
    configuration: DX2nxModel,
):
    """
    Convert from dxfile to NXtomo.
    Dark and flats will be store at the beginning and we consider they are
    take at start so rotation angle will set to scan_range[0].
    Projection rotation angle will be interpolated from scan_range and
    with equality space distribution.
    We do not expect any alignment projection.
    """
    converter = _DxFileToNxConverter(configuration=configuration)
    return converter.convert()


class _PathDoesNotExistsInExchange(Exception):
    pass


class _DxFileToNxConverter(BaseConverter):
    """
    Convert from dxfile to NXtomo.
    Dark and flats will be store at the beginning and we consider they are
    take at start so rotation angle will set to scan_range[0].
    Projection rotation angle will be interpolated from scan_range and
    with equality space distribution.
    We do not expect any alignment projection.
    """

    DEFAULT_SAMPLE_DETECTOR_DISTANCE_VALUE: float = 1.0

    DEFAULT_PIXEL_VALUE: float = 1.0

    DEFAULT_BEAM_ENERGY: float = 1.0

    def __init__(
        self,
        configuration: DX2nxModel,
    ):
        self._configuration = configuration
        if not len(self.scan_range) == 2:
            raise ValueError("scan_range expects to be a tuple with two elements")

        input_file = os.path.abspath(self.input_file)
        if self.output_file is None:
            input_file_basename, _ = os.path.splitext(input_file)
            if not self._configuration.file_extension.startswith("."):
                self._configuration.file_extension = (
                    "." + self._configuration.file_extension
                )
            output_file = os.path.join(
                os.path.dirname(input_file),
                os.path.basename(input_file_basename)
                + self._configuration.file_extension,
            )
        else:
            output_file = os.path.abspath(self.output_file)
        self._configuration.output_file = output_file
        if self.input_entry == "/":
            self._configuration._input_entry = ""
        else:
            self._configuration._input_entry = self.input_entry
        if self.field_of_view is not None:
            fov = self.field_of_view
            if isinstance(fov, str):
                fov = fov.title()
            self._configuration.field_of_view = FieldOfView(fov)

        self._n_frames = 0
        self._data_proj_url = None
        self._data_darks_url = None
        self._data_flats_url = None
        self._input_root_url = DataUrl(
            file_path=self.input_file,
            data_path=self.input_entry,
            scheme="silx",
        )

    @property
    def input_file(self):
        return self._configuration.input_file

    @property
    def input_entry(self):
        return self._configuration.input_entry

    @property
    def output_file(self):
        return self._configuration.output_file

    @property
    def output_entry(self):
        return self._configuration.output_entry

    @property
    def scan_range(self):
        return self._configuration.scan_range

    @property
    def copy_data(self):
        return self._configuration.copy_data

    @property
    def overwrite(self):
        return self._configuration.overwrite

    @property
    def field_of_view(self) -> FieldOfView | None:
        return self._configuration.field_of_view

    @property
    def energy(self) -> float | None:
        return self._configuration.energy

    @property
    def input_root_url(self):
        return self._input_root_url

    def convert(self):
        """
        do conversion from dxfile to NXtomo

        :return: tuple of (output_file, entry) created. For now the list should
                 contain at most one of those tuple
        """
        with HDF5File(self.output_file, mode="a") as h5f:
            if self.output_entry in h5f:
                if self.overwrite:
                    del h5f[self.output_entry]
                else:
                    raise OSError(
                        "{} already exists cannot create requested NXtomo entry. Won't overwrite it as not requested"
                    )

        self._n_frames = 0
        self._data_proj_url = DataUrl(
            file_path=self.input_file,
            data_path="/".join((self.input_entry, "exchange", "data")),
            scheme="silx",
        )
        self._data_darks_url = DataUrl(
            file_path=self.input_file,
            data_path="/".join((self.input_entry, "exchange", "data_dark")),
            scheme="silx",
        )
        self._data_flats_url = DataUrl(
            file_path=self.input_file,
            data_path="/".join((self.input_entry, "exchange", "data_white")),
            scheme="silx",
        )

        # convert frames
        if self.copy_data:
            self._convert_frames_with_duplication()
        else:
            self._convert_frames_without_duplication()

        # convert detector extra information
        #  x pixel size
        x_pixel_size, y_pixel_size = self._configuration.pixel_size
        if x_pixel_size is None:
            try:
                x_pixel_size = self._read_x_pixel_size().to_base_units().magnitude
            except Exception:
                x_pixel_size = self.DEFAULT_PIXEL_VALUE
                _logger.warning(
                    "No x pixel size found or provided. Set the it to the default value"
                )
        with HDF5File(self.output_file, mode="a") as h5f:
            root_grp = h5f.require_group(self.output_entry)
            instrument_grp = root_grp.require_group("instrument")
            detector_grp = instrument_grp.require_group("detector")
            detector_grp["x_pixel_size"] = x_pixel_size
            detector_grp["x_pixel_size"].attrs["units"] = "m"
        #  y pixel size
        if y_pixel_size is None:
            try:
                y_pixel_size = self._read_y_pixel_size().to_base_units().magnitude
            except Exception:
                y_pixel_size = self.DEFAULT_PIXEL_VALUE
                _logger.warning(
                    "No y pixel size found or provided. Set the it to the default value"
                )

        with HDF5File(self.output_file, mode="a") as h5f:
            root_grp = h5f.require_group(self.output_entry)
            instrument_grp = root_grp.require_group("instrument")
            detector_grp = instrument_grp.require_group("detector")
            detector_grp["y_pixel_size"] = y_pixel_size
            detector_grp["y_pixel_size"].attrs["units"] = "m"
        #  field of view
        if self.field_of_view is not None:
            with HDF5File(self.output_file, mode="a") as h5f:
                root_grp = h5f.require_group(self.output_entry)
                instrument_grp = root_grp.require_group("instrument")
                detector_grp = instrument_grp.require_group("detector")
                detector_grp["field_of_view"] = self.field_of_view.value
        #  distance
        if self._configuration.sample_detector_distance is None:
            # if value not set by the user let read it
            try:
                self._configuration.sample_detector_distance = (
                    self._read_sample_detector_distance().to_base_units().magnitude
                )
            except Exception:
                self._configuration.sample_detector_distance = (
                    self.DEFAULT_SAMPLE_DETECTOR_DISTANCE_VALUE
                )
                _logger.warning(
                    "No detector / sample distance found or provided. "
                    "Set the it  the default value"
                )

        with HDF5File(self.output_file, mode="a") as h5f:
            root_grp = h5f.require_group(self.output_entry)
            instrument_grp = root_grp.require_group("instrument")
            detector_grp = instrument_grp.require_group("detector")
            detector_grp["distance"] = self._configuration.sample_detector_distance
            detector_grp["distance"].attrs["units"] = str(_ureg.meter)
        # energy
        if self.energy is None:
            try:
                self._configuration.energy = self._read_energy().to(_ureg.keV).magnitude
            except Exception:
                self._configuration.energy = self.DEFAULT_BEAM_ENERGY
                _logger.warning(
                    "No energy found or provided. " "Set the it to the default value"
                )

        with HDF5File(self.output_file, mode="a") as h5f:
            root_grp = h5f.require_group(self.output_entry)
            beam_grp = root_grp.require_group("beam")
            beam_grp["incident_energy"] = self._configuration.energy
            beam_grp["incident_energy"].attrs["units"] = str(_ureg.keV)

        #  count_time
        self._copy_count_time()

        # start time
        with EntryReader(self.input_root_url) as input_entry:
            if "file_creation_datetime" in input_entry:
                with HDF5File(self.output_file, mode="a") as h5f:
                    root_grp = h5f.require_group(self.output_entry)
                    root_grp["start_time"] = h5py_read_dataset(
                        input_entry["file_creation_datetime"]
                    )

        return ((self.output_file, self.output_entry),)

    def _copy_count_time(self):
        """Try to read and copy count_time / exposure_period"""

        def read_and_write_count_time(dataset: h5py.Dataset):
            count_time = h5py_read_dataset(dataset)
            if count_time == "Error: Unknown Attribute":
                _logger.info(
                    f"Count time not stored on {self.input_entry}@{self.input_file}"
                )
            else:
                try:
                    if len(count_time) == self._n_frames:
                        with HDF5File(self.output_file, mode="a") as h5f:
                            root_grp = h5f.require_group(self.input_entry)
                            instrument_grp = root_grp.require_group("instrument")
                            detector_grp = instrument_grp.require_group("detector")
                            detector_grp["count_time"] = count_time
                    else:
                        _logger.warning(
                            f"exposure period and data frame have an incoherent size ({len(count_time)} vs {self._n_frames})"
                        )
                except Exception as e:
                    _logger.error(
                        f"Failed to get 'count_time' / 'exposure_period'. reason is {e}"
                    )

        with EntryReader(self.input_root_url) as input_entry:
            if "measurement" in input_entry:
                measurement_grp = input_entry["measurement"]
                if "detector" in measurement_grp:
                    detector_grp = measurement_grp["detector"]
                    if "exposure_period" in detector_grp:
                        read_and_write_count_time(detector_grp["exposure_period"])

    def _convert_frames_with_duplication(self):
        image_key = []
        image_key_control = []
        rotation_angle = []
        data = None

        # handle darks
        try:
            data_dark = get_data(self._data_darks_url)
        except _PathDoesNotExistsInExchange:
            _logger.warning(f"No darks found in {self.input_entry}@{self.input_file}")
        else:
            image_key.extend([ImageKey.DARK_FIELD.value] * len(data_dark))
            image_key_control.extend([ImageKey.DARK_FIELD.value] * len(data_dark))
            rotation_angle.extend([self.scan_range[0]] * len(data_dark))
            if data is None:
                data = data_dark
            else:
                data = numpy.concatenate((data, data_dark), axis=0)
        # handle flats
        try:
            data_flat = get_data(self._data_flats_url)
        except _PathDoesNotExistsInExchange:
            _logger.warning(f"No flats found in {self.input_entry}@{self.input_file}")
        else:
            image_key.extend([ImageKey.FLAT_FIELD.value] * len(data_flat))
            image_key_control.extend([ImageKey.FLAT_FIELD.value] * len(data_flat))
            rotation_angle.extend([self.scan_range[0]] * len(data_flat))
            if data is None:
                data = data_flat
            else:
                data = numpy.concatenate((data, data_flat), axis=0)
        # handle projections
        data_proj = get_data(self._data_proj_url)
        image_key.extend([ImageKey.PROJECTION.value] * len(data_proj))
        image_key_control.extend([ImageKey.PROJECTION.value] * len(data_proj))
        assert (
            self.scan_range[0] is not None
        ), "scan range is expected to be a tuple of float"
        assert (
            self.scan_range[1] is not None
        ), "scan range is expected to be a tuple of float"
        rotation_angle.extend(
            numpy.linspace(
                self.scan_range[0],
                self.scan_range[1],
                num=len(data_proj),
                endpoint=True,
            )
        )
        if data is None:
            data = data_proj
        else:
            data = numpy.concatenate((data, data_proj), axis=0)
        self._n_frames = len(data)

        with HDF5File(self.output_file, mode="a") as h5f:
            root_grp = h5f.require_group(self.output_entry)
            instrument_grp = root_grp.require_group("instrument")
            detector_grp = instrument_grp.require_group("detector")
            detector_grp["data"] = data
            detector_grp["image_key"] = image_key
            detector_grp["image_key_control"] = image_key_control
            sample_grp = root_grp.require_group("sample")
            sample_grp["rotation_angle"] = rotation_angle
            sample_grp["rotation_angle"].attrs["units"] = str(_ureg.degree)
            self._path_nxtomo_attrs(root_grp)

    def _path_nxtomo_attrs(self, root_grp):
        root_grp.attrs["NX_class"] = "NXentry"
        root_grp.attrs["definition"] = "NXtomo"
        root_grp.attrs["version"] = converter_version()
        root_grp.attrs["default"] = "instrument/detector"
        instrument_grp = root_grp.require_group("instrument")
        instrument_grp.attrs["NX_class"] = "NXinstrument"
        instrument_grp.attrs["default"] = "detector"
        detector_grp = instrument_grp.require_group("detector")
        detector_grp.attrs["NX_class"] = "NXdetector"
        detector_grp.attrs["NX_class"] = "NXdata"
        detector_grp.attrs["signal"] = "data"
        detector_grp.attrs["SILX_style/axis_scale_types"] = ["linear", "linear"]
        if "data" in detector_grp:
            detector_grp["data"].attrs["interpretation"] = "image"
        sample_node = root_grp.require_group("sample")
        sample_node.attrs["NX_class"] = "NXsample"

    def _convert_frames_without_duplication(self):
        image_key = []
        image_key_control = []
        rotation_angle = []
        dataset_path = "/".join((self.output_entry, "instrument", "detector", "data"))
        n_dark = 0
        n_flat = 0
        n_proj = 0
        # handle darks
        try:
            with DatasetReader(self._data_darks_url) as dark_dataset:
                n_dark = dark_dataset.shape[0]
            # FIXME: avoid keeping some file open. not clear why this is needed
            dark_dataset = None
            FrameAppender(
                self._data_darks_url,
                self.output_file,
                data_path=dataset_path,
                where="end",
                logger=_logger,
            ).process()
        except Exception:
            _logger.error(
                f"No darks found in {self._data_darks_url.path()} or unable to add them to the dataset"
            )
        else:
            image_key.extend([ImageKey.DARK_FIELD.value] * n_dark)
            image_key_control.extend([ImageKey.DARK_FIELD.value] * n_dark)
            rotation_angle.extend([self.scan_range[0]] * n_dark)

        # handle flats
        try:
            with DatasetReader(self._data_flats_url) as flat_dataset:
                n_flat = flat_dataset.shape[0]
            # FIXME: avoid keeping some file open. not clear why this is needed
            flat_dataset = None
            FrameAppender(
                self._data_flats_url,
                self.output_file,
                data_path=dataset_path,
                where="end",
                logger=_logger,
            ).process()
        except Exception:
            _logger.warning(
                f"No flats found in {self._data_flats_url.path()} or unable to add them to the dataset"
            )
        else:
            image_key.extend([ImageKey.FLAT_FIELD.value] * n_flat)
            image_key_control.extend([ImageKey.FLAT_FIELD.value] * n_flat)
            rotation_angle.extend([self.scan_range[0]] * n_flat)

        # handle projections
        try:
            with DatasetReader(self._data_proj_url) as proj_dataset:
                n_proj = proj_dataset.shape[0]
            # FIXME: avoid keeping some file open. not clear why this is needed
            proj_dataset = None
            FrameAppender(
                self._data_proj_url,
                self.output_file,
                data_path=dataset_path,
                where="end",
                logger=_logger,
            ).process()
        except Exception:
            _logger.warning(
                f"No projections found in {self._data_proj_url.path()} or unable to add them to the dataset"
            )
        else:
            image_key.extend([ImageKey.PROJECTION.value] * n_proj)
            image_key_control.extend([ImageKey.PROJECTION.value] * n_proj)
            rotation_angle.extend(
                numpy.linspace(
                    self.scan_range[0],
                    self.scan_range[1],
                    num=n_proj,
                    endpoint=True,
                )
            )

        self._n_frames = n_flat + n_dark + n_proj

        with HDF5File(self.output_file, mode="a") as h5f:
            root_grp = h5f.require_group(self.output_entry)
            instrument_grp = root_grp.require_group("instrument")
            detector_grp = instrument_grp.require_group("detector")
            detector_grp["image_key"] = image_key
            detector_grp["image_key_control"] = image_key_control
            sample_grp = root_grp.require_group("sample")
            sample_grp["rotation_angle"] = rotation_angle
            sample_grp["rotation_angle"].attrs["unit"] = "degree"
            self._path_nxtomo_attrs(root_grp)

    def _read_sample_detector_distance(self):
        with EntryReader(self.input_root_url) as input_entry:
            path = "/".join(
                ("measurement", "instrument", "sample", "setup", "detector_distance")
            )
            dataset = input_entry[path]
            distance = h5py_read_dataset(dataset)
            try:
                if "units" in dataset.attrs:
                    unit = dataset.attrs["units"]
                else:
                    unit = dataset.attrs["unit"]
                unit = _ureg(unit)
            except Exception:
                unit = _ureg.meter
            return distance * unit

    def _read_energy(self):
        with EntryReader(self.input_root_url) as input_entry:
            path = "/".join(("measurement", "instrument", "source", "energy"))
            dataset = input_entry[path]
            energy = float(h5py_read_dataset(dataset))
            try:
                if "units" in dataset.attrs:
                    unit = dataset.attrs["units"]
                else:
                    unit = dataset.attrs["unit"]
                # patch until next tomoscan is released
                if unit.lower() in ("mev", "megaelectronvolt"):
                    unit = _ureg.keV * 1e3
                elif unit.lower() in ("gev", "gigaelectronvolt"):
                    unit = _ureg.keV * 1e6
                else:
                    unit = _ureg(unit)
            except Exception:
                unit = _ureg.keV
            return energy * unit

    def _read_x_pixel_size(self):
        with EntryReader(self.input_root_url) as input_entry:
            path = "/".join(
                ("measurement", "instrument", "detector", "actual_pixel_size_x")
            )
            dataset = input_entry[path]
            pixel_size = float(h5py_read_dataset(dataset))
            try:
                if "units" in dataset.attrs:
                    unit = dataset.attrs["units"]
                else:
                    unit = dataset.attrs["unit"]
                # patch until next tomoscan is released
                if unit == "microns":
                    unit = "um"
                unit = _ureg(unit)
            except Exception:
                unit = _ureg.meter
            return pixel_size * unit

    def _read_y_pixel_size(self):
        with EntryReader(self.input_root_url) as input_entry:
            path = "/".join(
                ("measurement", "instrument", "detector", "actual_pixel_size_y")
            )
            dataset = input_entry[path]
            pixel_size = float(h5py_read_dataset(dataset))
            try:
                if "units" in dataset.attrs:
                    unit = dataset.attrs["units"]
                else:
                    unit = dataset.attrs["unit"]
                # patch until next tomoscan is released
                if unit == "microns":
                    unit = "um"
                unit = _ureg(unit)
            except Exception:
                unit = _ureg.meter
            return pixel_size * unit
