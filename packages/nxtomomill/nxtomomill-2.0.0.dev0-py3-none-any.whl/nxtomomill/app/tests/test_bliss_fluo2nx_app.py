# coding: utf-8

import os
import logging
import numpy as np

import h5py

try:
    from nxtomomill.tests.datasets import GitlabDataset
except ImportError:
    raise ImportError("Unable to import GitlabDataset")

from nxtomomill.app.blissfluo2nx import main

logging.disable(logging.INFO)


def test_blissfluo2nx_application_all_dets():
    """test nxtomomill fluo2nx CLI with default parameters (handle all detectors found)"""
    scan_dir = GitlabDataset.get_dataset("blissfluo_datasets3D")
    output_file = os.path.join(scan_dir, "test_Siemens.nx")
    truth_file = os.path.join(scan_dir, "Siemens.nx")
    input_file = os.path.join(scan_dir, "Siemens_raw.h5")

    main(
        [
            "blissfluo2nx",
            "--ewoksfluo_filename",
            input_file,
            "--output_file",
            output_file,
            "--overwrite",
        ]
    )
    assert os.path.exists(output_file), "output_file doesn't exists"
    with h5py.File(output_file, "r") as f_test, h5py.File(truth_file, "r") as f_true:
        assert len(list(f_test.keys())) == len(
            list(f_true.keys())
        ), f"Number of entries ({len(list(f_test.keys()))}) not as expected ({len(list(f_true.keys()))})."
        assert np.allclose(
            f_test["/grid_Ardesia_ng_mm2_Al_K/data/data"][()],
            f_true["/grid_Ardesia_ng_mm2_Al_K/data/data"][()],
        ), "Discrepancy in grid_Ardesia_Al_K projection data."
        assert np.allclose(
            f_test["/grid_Ardesia_ng_mm2_Al_K/data/rotation_angle"][()],
            f_true["/grid_Ardesia_ng_mm2_Al_K/data/rotation_angle"][()],
        ), "Discrepancy in grid_Ardesia_Al_K rotation angles."


def test_blissfluo2nx_application_single_det():
    """test nxtomomill fluo2nx CLI targetting a single existing detector"""
    scan_dir = GitlabDataset.get_dataset("blissfluo_datasets3D")
    input_file = os.path.join(scan_dir, "Siemens_raw.h5")
    truth_file = os.path.join(scan_dir, "Siemens_1det_2.nx")
    output_file = os.path.join(scan_dir, "test_Siemens_1det.nx")

    main(
        [
            "blissfluo2nx",
            "--ewoksfluo_filename",
            input_file,
            "--output_file",
            output_file,
            "--detectors",
            "grid_Ardesia_ng_mm2",
            "--overwrite",
        ]
    )
    assert os.path.exists(output_file), "output_file doesn't exists"
    with h5py.File(output_file, "r") as f_test, h5py.File(truth_file, "r") as f_true:
        assert len(list(f_test.keys())) == len(
            list(f_true.keys())
        ), f"Number of entries ({len(list(f_test.keys()))}) not as expected ({len(list(f_true.keys()))})."
        assert np.allclose(
            f_test["/grid_Ardesia_ng_mm2_Al_K/data/data"][()],
            f_true["/grid_Ardesia_ng_mm2_Al_K/data/data"][()],
        ), "Discrepancy in grid_Ardesia_Al_K projection data."
        assert np.allclose(
            f_test["/grid_Ardesia_ng_mm2_Al_K/data/rotation_angle"][()],
            f_true["/grid_Ardesia_ng_mm2_Al_K/data/rotation_angle"][()],
        ), "Discrepancy in grid_Ardesia_Al_K rotation angles."


def test_blissfluo2nx_application_two_det():
    """test nxtomomill fluo2nx CLI targetting two existing detector"""
    scan_dir = GitlabDataset.get_dataset("blissfluo_datasets3D")
    input_file = os.path.join(scan_dir, "Siemens_raw.h5")
    truth_file = os.path.join(scan_dir, "Siemens_2det_2.nx")
    output_file = os.path.join(scan_dir, "test_Siemens_2det.nx")

    main(
        [
            "blissfluo2nx",
            "--ewoksfluo_filename",
            input_file,
            "--output_file",
            output_file,
            "--detectors",
            "grid_Ardesia_ng_mm2",
            "grid_weighted_ng_mm2",
            "--overwrite",
        ]
    )
    assert os.path.exists(output_file), "output_file doesn't exists"
    with h5py.File(output_file, "r") as f_test, h5py.File(truth_file, "r") as f_true:
        assert len(list(f_test.keys())) == len(
            list(f_true.keys())
        ), f"Number of entries ({len(list(f_test.keys()))}) not as expected ({len(list(f_true.keys()))})."
        assert np.allclose(
            f_test["/grid_Ardesia_ng_mm2_Al_K/data/data"][()],
            f_true["/grid_Ardesia_ng_mm2_Al_K/data/data"][()],
        ), "Discrepancy in grid_Ardesia_Al_K projection data."
        assert np.allclose(
            f_test["/grid_Ardesia_ng_mm2_Al_K/data/rotation_angle"][()],
            f_true["/grid_Ardesia_ng_mm2_Al_K/data/rotation_angle"][()],
        ), "Discrepancy in grid_Ardesia_Al_K rotation angles."
