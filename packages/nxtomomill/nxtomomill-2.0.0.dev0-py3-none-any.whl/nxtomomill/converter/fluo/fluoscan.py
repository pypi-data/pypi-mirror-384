"""Scan dedicated for bliss format - based on EDF files"""

from __future__ import annotations

import logging
import os
import glob
import pint

import numpy

from tomoscan.identifier import ScanIdentifier
from tomoscan.scanbase import TomoScanBase
from tomoscan.utils import docstring


from dataclasses import dataclass, field
import numpy as np
from numpy.typing import NDArray, DTypeLike
from silx.io.utils import h5py_read_dataset

try:
    from tqdm.auto import tqdm
except ImportError:
    has_tqdm = False
else:
    has_tqdm = True
import h5py

_ureg = pint.get_application_registry()
_logger = logging.getLogger(__name__)

try:
    import tifffile  # noqa #F401 needed for later possible lazy loading
except ImportError:
    has_tifffile = False
else:
    has_tifffile = True

__all__ = ["FluoTomoScanBase", "FluoTomoScan3D", "FluoTomoScan2D"]


@dataclass
class FluoTomoScanBase:
    """Dataset manipulation class."""

    scan: str
    dataset_basename: str
    detectors: tuple = ()

    dtype: DTypeLike = numpy.float32
    verbose: bool = False

    angles: float | None = None
    """rotation angles in degree"""
    el_lines: dict[str, list[str]] = field(default_factory=dict)
    pixel_size: float | None = None
    """pixel size in meter"""
    energy: float | None = None
    """energy in keV"""
    detected_folders: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.detected_folders = self.detect_folders()
        self.detected_detectors = tuple(self.detect_detectors())
        self.get_metadata_from_h5_file()
        _logger.info(f"Detectors: {self.detected_detectors}")
        if len(self.detectors) == 0:
            self.detectors = self.detected_detectors
        for det in self.detectors:
            if det not in self.detected_detectors:
                raise ValueError(
                    f"The detector should be in {self.detected_detectors} and is {self.detectors}"
                )
        self.detect_elements()

        if self.angles is None:
            self.angles = self.detect_rot_angles()

    def detect_folders(self) -> list[str]:
        """List all folders to process."""
        raise NotImplementedError("Base class")

    @property
    def rot_angles_deg(self) -> NDArray:
        if self.angles is None:
            raise ValueError("Rotation angles not initialized")

        return self.angles * _ureg.deg

    @property
    def rot_angles_rad(self) -> NDArray:
        return self.rot_angles_deg.to(_ureg.rad)

    def detect_rot_angles(self) -> NDArray:
        """Build rotation angles list."""
        raise NotImplementedError("Base class")

    def _check_ready_to_load_data(self, det):
        if not has_tifffile:
            raise RuntimeError("tiffile not install. Cannot load data.")
        if det not in self.detectors:
            raise RuntimeError(
                f"The detector {det} is invalid. Valid ones are {self.detectors}"
            )
        if self.angles is None:
            raise RuntimeError("Rotation angles not initialized")

        if self.detectors is None:
            raise RuntimeError("Detectors not initialized")

    def get_metadata_from_h5_file(self):
        if len(self.detected_folders) == 0:
            raise ValueError("No folder found, unable to load metadata")
        h5_path = os.path.join(self.scan, self.detected_folders[0])
        h5_files = glob.glob1(h5_path, "*.h5")
        if len(h5_files) > 1:
            raise ValueError(
                "More than one hdf5 file in scan directory. Expect only ONE to pick pixel size."
            )
        elif len(h5_files) == 0:
            pattern = os.path.join(h5_path, "*.h5")
            raise ValueError(
                f"Unable to find the hdf5 file in scan directory to pick pixel size. RegExp used is {pattern}"
            )
        else:
            with h5py.File(os.path.join(h5_path, h5_files[0]), "r") as f:
                if len(list(f.keys())) != 1:
                    raise ValueError(
                        f"H5 file should contain only one entry, found {len(list(f.keys()))}"
                    )
                else:
                    entry_name = list(f.keys())[0]
                    self.pixel_size = (
                        (
                            h5py_read_dataset(f[entry_name]["FLUO"]["pixelSize"])
                            * _ureg.micrometer
                        )
                        .to(_ureg.meter)
                        .magnitude
                    )
                    self.energy = float(
                        h5py_read_dataset(
                            f[entry_name]["instrument"]["monochromator"]["energy"]
                        )
                    )

    def detect_detectors(self):
        if len(self.detected_folders) == 0:
            raise ValueError("No folder found, unable to detect detectors")
        proj_1_dir = os.path.join(self.scan, "fluofit", self.detected_folders[0])
        detected_detectors = []
        file_names = glob.glob1(proj_1_dir, "IMG_*area_density_ngmm2.tif")
        for file in file_names:
            det = file.split("_")[1]
            if det not in detected_detectors:
                detected_detectors.append(det)
        if "" in detected_detectors:
            raise ValueError(
                f"Suspicious detector! Detected detectors are {detected_detectors}. Please use --detectors <det1>... where det1 are valid detector name."
            )

        return detected_detectors

    def detect_elements(self):
        if len(self.detected_folders) == 0:
            raise ValueError("No folder found, unable to detect elements")
        proj_1_dir = os.path.join(self.scan, "fluofit", self.detected_folders[0])
        detector = self.detectors[0]
        file_names = glob.glob1(proj_1_dir, f"IMG_{detector}*area_density_ngmm2.tif")
        for file in file_names:
            el_str = file.split("_")[2]
            element, line = el_str.split("-")
            try:
                if line not in self.el_lines[element]:
                    self.el_lines[element].append(line)
                    self.el_lines[element] = sorted(self.el_lines[element])
            except KeyError:
                self.el_lines[element] = [line]

    def load_data(self, det: str, element: str, line_ind: int = 0) -> NDArray:
        """Main function of class to load data."""
        raise NotImplementedError("Base class")

    @staticmethod
    def from_identifier(identifier):
        """Return the Dataset from a identifier"""
        raise NotImplementedError("Not implemented for fluo-tomo yet.")

    @docstring(TomoScanBase)
    def get_identifier(self) -> ScanIdentifier:
        raise NotImplementedError("Not implemented for fluo-tomo yet.")


@dataclass
class FluoTomoScan3D(FluoTomoScanBase):
    """Dataset manipulation class."""

    def detect_folders(self):
        fit_folders = glob.glob1(
            os.path.join(self.scan, "fluofit"), rf"{self.dataset_basename}_projection*"
        )
        fit_folders.sort()
        proj_indices = [int(f[-3:]) for f in fit_folders]

        if len(fit_folders) < proj_indices[-1]:
            _logger.debug(
                f"The number of projections ({len(fit_folders)}) is lower than the largest projection index {proj_indices[-1]}. Some projections are probably missing."
            )

        if len(fit_folders) == 0:
            raise FileNotFoundError(
                "No projection was found in the fluofit folder. The searched for pattern is <scan_dir>/fluofit/<dataset_basename>_projection*'."
            )
        elif not os.path.isdir(os.path.join(self.scan, fit_folders[0])):
            raise FileNotFoundError(
                "Found fitted data folders but not the corresponding raw data folder."
            )
        else:
            return fit_folders

    def detect_rot_angles(self) -> NDArray:
        tmp_angles = []
        for f in self.detected_folders:
            prj_dir = os.path.join(self.scan, "fluofit", f)
            info_file = os.path.join(prj_dir, "info.txt")
            try:
                with open(info_file, "r") as f:
                    info_str = f.read()
                    tmp_angles.append(float(info_str.split(" ")[2]))
            except FileNotFoundError:
                _logger.debug(
                    f"{info_file} doesn't exist, while expected to be present in each projection folder."
                )
                raise FileNotFoundError(
                    f"{info_file} doesn't exist, while expected to be present in each projection folder."
                )
            _logger.info(f"Correctly found all {len(tmp_angles)} rotation angles.")
        return numpy.array(tmp_angles, ndmin=1, dtype=numpy.float32)

    def load_data(self, det: str, element: str, line_ind: int = 0) -> NDArray:

        self._check_ready_to_load_data(det)

        line = self.el_lines[element][line_ind]

        data_det = []

        description = f"Loading images of {element}-{line} ({det}): "

        if has_tqdm:
            proj_iterator = tqdm(
                range(len(self.detected_folders)),
                disable=self.verbose,
                desc=description,
            )
        else:
            proj_iterator = range(len(self.detected_folders))

        for ii_i in proj_iterator:
            proj_dir = os.path.join(
                self.scan,
                "fluofit",
                self.detected_folders[ii_i],
            )
            img_path = os.path.join(
                proj_dir, f"IMG_{det}_{element}-{line}_area_density_ngmm2.tif"
            )

            if self.verbose:
                _logger.info(f"Loading {ii_i + 1} / {len(self.angles)}: {img_path}")

            img = tifffile.imread(img_path)
            data_det.append(numpy.nan_to_num(numpy.array(img, dtype=self.dtype)))

        data = numpy.array(data_det)
        return numpy.ascontiguousarray(data)


@dataclass
class FluoTomoScan2D(FluoTomoScanBase):
    """Dataset manipulation class."""

    def get_metadata_from_h5_file(self):
        super().get_metadata_from_h5_file()
        h5_path = os.path.join(self.scan, self.detected_folders[0])
        h5_files = glob.glob1(h5_path, "*.h5")
        if len(h5_files) > 1:
            raise ValueError(
                "More than one hdf5 file in scan directory. Expect only ONE to pick pixel size."
            )
        elif len(h5_files) == 0:
            pattern = os.path.join(h5_path, "*.h5")
            raise ValueError(
                f"Unable to find the hdf5 file in scan directory to pick pixel size. RegExp used is {pattern}"
            )
        else:
            with h5py.File(os.path.join(h5_path, h5_files[0]), "r") as f:
                if len(list(f.keys())) != 1:
                    raise ValueError(
                        f"H5 file should contain only one entry, found {len(list(f.keys()))}"
                    )
                else:
                    entry_name = list(f.keys())[0]
                    self.scanRange_2 = float(
                        h5py_read_dataset(f[entry_name]["FLUO"]["scanRange_2"])
                    )
                    self.scanDim_2 = int(
                        h5py_read_dataset(f[entry_name]["FLUO"]["scanDim_2"])
                    )

    def detect_rot_angles(self) -> NDArray:
        nb_projs = self.scanDim_2
        angular_coverage = self.scanRange_2
        return np.linspace(0, angular_coverage, nb_projs, endpoint=True)

    def detect_folders(self):
        fit_folder = os.path.join(self.scan, "fluofit", self.dataset_basename)

        if not os.path.isdir(fit_folder):
            raise FileNotFoundError(
                f"No folder {fit_folder} was found in the fluofit folder. The searched for pattern is <scan_dir>/fluofit/<dataset_basename>'."
            )
        elif not os.path.isdir(os.path.join(self.scan, self.dataset_basename)):
            raise FileNotFoundError(
                "Found fitted data folders but not the corresponding raw data folder."
            )
        else:
            return [
                self.dataset_basename,
            ]

    def load_data(self, det: str, element: str, line_ind: int = 0) -> NDArray:
        self._check_ready_to_load_data(det)

        line = self.el_lines[element][line_ind]

        data_det = []

        description = f"Loading images of {element}-{line} ({det}): "

        if has_tqdm:
            slice_iterator = tqdm(
                range(len(self.detected_folders)),
                disable=self.verbose,
                desc=description,
            )
        else:
            slice_iterator = range(len(self.detected_folders))

        for ii_i in slice_iterator:

            proj_dir = os.path.join(
                self.scan,
                "fluofit",
                self.dataset_basename,  # WARNING: dataset_basename is ONE SINGLE sinogram.
            )
            img_path = os.path.join(
                proj_dir, f"IMG_{det}_{element}-{line}_area_density_ngmm2.tif"
            )

            if self.verbose:
                _logger.info(f"Loading {ii_i + 1} / {len(self.angles)}: {img_path}")

            img = tifffile.imread(img_path)
            data_det.append(numpy.nan_to_num(numpy.array(img, dtype=self.dtype)))

        data = numpy.array(data_det)
        return numpy.ascontiguousarray(data)
