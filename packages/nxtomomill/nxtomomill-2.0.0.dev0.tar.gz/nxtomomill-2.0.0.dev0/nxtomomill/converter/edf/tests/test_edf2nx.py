# coding: utf-8

import os
import shutil
import tempfile
from glob import glob

import numpy
import pytest

from tqdm import tqdm

from tomoscan import version
from tomoscan.esrf.mock import MockEDF
from tomoscan.esrf.scan.edfscan import EDFTomoScan
from tomoscan.esrf.scan.nxtomoscan import NXtomoScan
from tomoscan.esrf.scan.utils import cwd_context, dump_info_file
from tomoscan.validator import is_valid_for_reconstruction
from tomoscan.io import HDF5File, get_swmr_mode

from nxtomomill import converter
from nxtomomill.converter.edf.checks import OUPUT_CHECK
from nxtomomill.models.edf2nx import EDF2nxModel


@pytest.mark.parametrize(
    "duplicate_data, external_link_type",
    ((False, "absolute"), (False, "relative"), (True, "absolute")),
)
@pytest.mark.parametrize("progress", (None, tqdm(desc="conversion from edf")))
@pytest.mark.skipif(
    condition=(version.MINOR < 7 and version.MAJOR == 0),
    reason="dark_n and ref_n from EDFTomoScan where not existing",
)
def test_edf_to_nx_converter(tmp_path, progress, duplicate_data, external_link_type):
    folder = tmp_path

    scan_path = os.path.join(folder, "myscan")
    n_proj = 120
    n_alignment_proj = 5
    dim = 100
    MockEDF(
        scan_path=scan_path,
        n_radio=n_proj,
        n_ini_radio=n_proj,
        n_extra_radio=n_alignment_proj,
        dim=dim,
        dark_n=1,
        flat_n=1,
        distance=2.3,
    )
    scan = EDFTomoScan(scan_path)
    assert scan.dark_n == 1
    output_file = os.path.join(folder, "nexus_file.nx")

    config = EDF2nxModel()
    config.input_folder = scan_path
    config.output_file = output_file
    config.duplicate_data = duplicate_data
    config.external_link_type = external_link_type
    config.x_translation_unit = "cm"
    config.y_translation_unit = "cm"
    config.z_translation_unit = "m"
    config.sample_detector_distance_unit = "cm"
    nx_file, nx_entry = converter.from_edf_to_nx(
        configuration=config,
        progress=progress,
    )

    hdf5_scan = NXtomoScan(scan=nx_file, entry=nx_entry)
    assert len(hdf5_scan.projections) == n_proj
    assert len(hdf5_scan.alignment_projections) == n_alignment_proj
    assert hdf5_scan.dim_1 == dim
    assert hdf5_scan.dim_2 == dim
    assert is_valid_for_reconstruction(hdf5_scan)
    # insure links are valid in case of external
    # for relative links it looks we still need to be on the file working directory to solve links
    # see policy details here: https://docs.hdfgroup.org/hdf5/v1_12/group___h5_l.html#title5
    # this will work with the tomotools suite as tomoscan will automatically create a working dircetory context when reading the file.
    # but this can be an issue when sharing data or reading data outside the tomotools suite
    with cwd_context(output_file):
        with HDF5File(output_file, mode="r", swmr=get_swmr_mode()) as h5f:
            detector_data_path = f"/{nx_entry}/instrument/detector/data"
            assert (
                f"/{nx_entry}/instrument/detector/data" in h5f
            ), f"/{nx_entry}/instrument/detector/data  doesn't exists"
            assert h5f[detector_data_path].is_virtual == (not duplicate_data)
            assert (
                h5f[detector_data_path][()].min() != h5f[detector_data_path][()].max()
            )
            numpy.testing.assert_almost_equal(
                h5f[f"/{nx_entry}/sample/z_translation"][0], 0.0
            )
            numpy.testing.assert_almost_equal(
                h5f[f"/{nx_entry}/sample/x_translation"][0], 1.0 / 100.0
            )
            numpy.testing.assert_almost_equal(
                h5f[f"/{nx_entry}/sample/y_translation"][0], 2.0
            )

    # x, y and z are set manually on MockEDF.
    n_frames = 120 + 5 + 1 + 1
    numpy.testing.assert_array_almost_equal(
        hdf5_scan.x_translation,
        numpy.array([1.0 / 100.0] * n_frames),
    )
    numpy.testing.assert_array_almost_equal(
        hdf5_scan.y_translation, numpy.array([2.0] * n_frames)
    )
    numpy.testing.assert_almost_equal(hdf5_scan.distance, 2.3 / 100.0)


@pytest.mark.parametrize("scan_range", (-180, 180, 360))
@pytest.mark.parametrize("endpoint", (True, False))
@pytest.mark.parametrize("revert", (True, False))
@pytest.mark.parametrize("force_angles", (True, False))
def test_rotation_angle_infos(scan_range, endpoint, revert, force_angles):
    """test conversion fits EDF2nxModel parameters regarding the rotation angle calculation options"""
    with tempfile.TemporaryDirectory() as data_folder:
        scan_path = os.path.join(data_folder, "myscan")
        n_proj = 12
        n_alignment_proj = 5
        dim = 4

        MockEDF(
            scan_path=scan_path,
            n_radio=n_proj,
            n_ini_radio=n_proj,
            n_extra_radio=n_alignment_proj,
            dim=dim,
            dark_n=1,
            ref_n=1,
            scan_range=scan_range,
            rotation_angle_endpoint=endpoint,
        )

        output_file = os.path.join(data_folder, "nexus_file.nx")

        config = EDF2nxModel()
        config.input_folder = scan_path
        config.output_file = output_file
        config.force_angle_calculation = force_angles
        config.angle_calculation_endpoint = endpoint
        config.angle_calculation_rev_neg_scan_range = revert

        nx_file, nx_entry = converter.from_edf_to_nx(
            configuration=config,
        )
        hdf5_scan = NXtomoScan(scan=nx_file, entry=nx_entry)

        # compute expected rotation angles
        raw_rotation_angles = numpy.asarray(hdf5_scan.rotation_angle)
        converted_rotation_angles = raw_rotation_angles[
            hdf5_scan.image_key_control == 0
        ]

        if force_angles and revert and scan_range < 0 and not endpoint:
            expected_angles = numpy.linspace(0, scan_range, n_proj, endpoint=endpoint)
        else:
            expected_angles = numpy.linspace(
                min(0, scan_range), max(0, scan_range), n_proj, endpoint=endpoint
            )
            revert_angles_in_nx = force_angles and revert and (scan_range < 0)
            if revert_angles_in_nx:
                expected_angles = expected_angles[::-1]

        numpy.testing.assert_almost_equal(
            converted_rotation_angles, expected_angles, decimal=3
        )
        # test alignment projection and flat are contained in the projections range
        dark_angles = raw_rotation_angles[hdf5_scan.image_key_control == 2]
        for angle in dark_angles:
            assert angle == 0 or min(converted_rotation_angles) <= angle <= max(
                converted_rotation_angles
            )

        flat_angles = raw_rotation_angles[hdf5_scan.image_key_control == 1]

        for angle in flat_angles:
            assert angle == 0 or min(converted_rotation_angles) <= angle <= max(
                converted_rotation_angles
            )

        alignment_angles = raw_rotation_angles[hdf5_scan.image_key_control == -1]
        for angle in alignment_angles:
            assert angle == 0 or min(converted_rotation_angles) <= angle <= max(
                converted_rotation_angles
            )


def test_rot_angle_key_does_not_exists():
    """test conversion fits EDF2nxModel parameters regarding the rotation angle calculation options"""
    with tempfile.TemporaryDirectory() as data_folder:
        scan_path = os.path.join(data_folder, "myscan")
        n_proj = 12
        n_alignment_proj = 5
        dim = 4

        MockEDF(
            scan_path=scan_path,
            n_radio=n_proj,
            n_ini_radio=n_proj,
            n_extra_radio=n_alignment_proj,
            dim=dim,
            dark_n=1,
            ref_n=1,
            scan_range=180,
        )

        output_file = os.path.join(data_folder, "nexus_file.nx")

        config = EDF2nxModel()
        config.input_folder = scan_path
        config.output_file = output_file
        config.force_angle_calculation = False
        config.rotation_angle_keys = tuple()

        nx_file, nx_entry = converter.from_edf_to_nx(
            configuration=config,
        )
        hdf5_scan = NXtomoScan(scan=nx_file, entry=nx_entry)

        # compute expected rotation angles
        raw_rotation_angles = numpy.asarray(hdf5_scan.rotation_angle)
        converted_rotation_angles = raw_rotation_angles[
            hdf5_scan.image_key_control == 0
        ]

        expected_angles = numpy.linspace(
            0, 180, n_proj, endpoint=config.angle_calculation_endpoint
        )
        numpy.testing.assert_almost_equal(
            converted_rotation_angles, expected_angles, decimal=3
        )


def test_different_info_file():
    """insure providing a different spec info file will be taken into account"""
    with tempfile.TemporaryDirectory() as data_folder:
        scan_path = os.path.join(data_folder, "myscan")
        n_proj = 12
        n_alignment_proj = 0
        dim = 4
        flat_n = 1
        dark_n = 1

        original_scan_range = 180
        original_energy = 2.3
        original_pixel_size = 0.03
        original_distance = 0.36

        new_scan_range = -180
        new_energy = 6.6
        new_pixel_size = 0.002
        new_distance = 0.458
        new_n_proj = n_proj - 2

        other_info_file = os.path.join(data_folder, "new_info_file.info")
        dump_info_file(
            file_path=other_info_file,
            tomo_n=new_n_proj,
            scan_range=new_scan_range,
            flat_n=flat_n,
            flat_on=new_n_proj,
            dark_n=dark_n,
            dim_1=dim,
            dim_2=dim,
            col_beg=0,
            col_end=dim,
            row_beg=0,
            row_end=dim,
            pixel_size=new_pixel_size,
            distance=new_distance,
            energy=new_energy,
        )
        assert os.path.exists(other_info_file)

        MockEDF(
            scan_path=scan_path,
            n_radio=n_proj,
            n_ini_radio=n_proj,
            n_extra_radio=n_alignment_proj,
            dim=dim,
            dark_n=dark_n,
            flat_n=flat_n,
            scan_range=original_scan_range,
            energy=original_energy,
            pixel_size=original_pixel_size,
            distance=original_distance,
        )

        output_file = os.path.join(data_folder, "nexus_file.nx")
        config = EDF2nxModel()
        config.input_folder = scan_path
        config.output_file = output_file
        config.force_angle_calculation = True
        config.pixel_size_unit = "m"
        config.distance_unit = "m"
        config.energy_unit = "keV"

        # test step 1: check scan info is correctly read from the original parameters
        nx_file, nx_entry = converter.from_edf_to_nx(
            configuration=config,
        )
        hdf5_scan_original_info_file = NXtomoScan(scan=nx_file, entry=nx_entry)
        assert numpy.isclose(hdf5_scan_original_info_file.energy, original_energy)
        assert hdf5_scan_original_info_file.scan_range == original_scan_range
        assert hdf5_scan_original_info_file.pixel_size == original_pixel_size
        assert hdf5_scan_original_info_file.distance == original_distance
        assert len(hdf5_scan_original_info_file.projections) == n_proj

        # test step 2: check scan info is correctly read from new parameters
        config.dataset_info_file = other_info_file
        config.overwrite = True
        nx_file, nx_entry = converter.from_edf_to_nx(
            configuration=config,
        )
        hdf5_scan_new_info_file = NXtomoScan(scan=nx_file, entry=nx_entry)
        assert numpy.isclose(hdf5_scan_new_info_file.energy, new_energy)
        # for now NXtomoScan expect range to be 180 or 360. There is no such -180 as in EDF
        assert abs(hdf5_scan_new_info_file.scan_range) == abs(new_scan_range)
        assert hdf5_scan_new_info_file.pixel_size == new_pixel_size
        assert hdf5_scan_new_info_file.distance == new_distance
        assert len(hdf5_scan_new_info_file.projections) == new_n_proj


def test_different_dataset_basename():
    """test conversion succeed if we provide a dataset with a different basename"""
    with tempfile.TemporaryDirectory() as data_folder:
        original_scan_path = os.path.join(data_folder, "myscan")
        new_scan_path = os.path.join(data_folder, "myscan_435")

        n_proj = 12
        n_alignment_proj = 5
        dim = 4
        energy = 12.35
        n_darks = 2
        n_flats = 1

        MockEDF(
            scan_path=original_scan_path,
            n_radio=n_proj,
            n_ini_radio=n_proj,
            n_extra_radio=n_alignment_proj,
            dim=dim,
            dark_n=n_darks,
            flat_n=n_flats,
            energy=energy,
        )

        shutil.move(
            original_scan_path,
            new_scan_path,
        )

        output_file = os.path.join(data_folder, "nexus_file.nx")

        config = EDF2nxModel()
        config.input_folder = new_scan_path
        config.output_file = output_file
        config.dataset_basename = "myscan"
        nx_file, nx_entry = converter.from_edf_to_nx(
            configuration=config,
        )
        hdf5_scan = NXtomoScan(scan=nx_file, entry=nx_entry)
        assert len(hdf5_scan.projections) == n_proj
        assert len(hdf5_scan.alignment_projections) == n_alignment_proj
        assert len(hdf5_scan.darks) == n_darks
        assert len(hdf5_scan.flats) == n_flats
        assert hdf5_scan.energy == energy


def test_delete_edf_input_files():
    """
    test `delete_edf_source_files` option
    """

    def get_n_edf_file(path):
        return len(glob(os.path.join(path, "*.edf")))

    with tempfile.TemporaryDirectory() as data_folder:
        input_scan_path = os.path.join(data_folder, "input_scan")

        MockEDF(
            scan_path=input_scan_path,
            n_radio=10,
            n_ini_radio=10,
            n_extra_radio=2,
            dim=25,
            dark_n=2,
            flat_n=2,
        )
        assert get_n_edf_file(input_scan_path) == 16
        info_file = os.path.join(input_scan_path, "input_scan.info")
        assert os.path.exists(info_file)

        config = EDF2nxModel()

        nx_tomo_path = os.path.join(data_folder, "nxtomo.nx")
        config.input_folder = input_scan_path
        config.output_file = nx_tomo_path
        config.delete_edf_source_files = True
        config.duplicate_data = False
        # make sure if we ask for no data duplication and removing source files we raise an error (incoherent settings)
        with pytest.raises(ValueError):
            converter.from_edf_to_nx(
                configuration=config,
            )

        config.duplicate_data = True
        nx_file, _ = converter.from_edf_to_nx(
            configuration=config,
        )
        # check conversion went well
        assert os.path.exists(nx_file)
        # make sure there is no edf left
        assert get_n_edf_file(input_scan_path) == 0
        # make sure the .info file is still there to
        assert os.path.exists(info_file)


def test_output_checks():
    """
    test some conversion calling some check at the end of the conversion
    """
    with tempfile.TemporaryDirectory() as data_folder:
        input_scan_path = os.path.join(data_folder, "input_scan")

        MockEDF(
            scan_path=input_scan_path,
            n_radio=10,
            n_ini_radio=10,
            n_extra_radio=2,
            dim=25,
            dark_n=2,
            flat_n=2,
        )

        config = EDF2nxModel()
        nx_tomo_path = os.path.join(data_folder, "nxtomo.nx")
        config.input_folder = input_scan_path
        config.output_file = nx_tomo_path
        config._output_checks = (OUPUT_CHECK.COMPARE_VOLUME,)
        converter.from_edf_to_nx(
            configuration=config,
        )
