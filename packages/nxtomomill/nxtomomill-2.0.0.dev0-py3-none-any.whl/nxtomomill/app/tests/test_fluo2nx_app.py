# coding: utf-8

import os
import logging

import h5py

from tomoscan.tests.datasets import GitlabDataset
from nxtomomill.app.fluo2nx import main

logging.disable(logging.INFO)


def test_fluo2nx_application_all_dets(tmp_path):
    """test nxtomomill fluo2nx CLI with default parameters (handle all detectors found)"""
    scan_dir = GitlabDataset.get_dataset("fluo_datasets")
    output_file = os.path.join(tmp_path, "nexus_file.nx")

    assert not os.path.exists(output_file), "output_file exists already"
    main(["fluo2nx", scan_dir, output_file, "CP1_XRD_insitu_top_ft_100nm"])
    assert os.path.exists(output_file), "output_file doesn't exists"
    with h5py.File(output_file, "r") as f:
        assert (
            len(list(f.keys())) == 45
        ), f"Number of entries ({len(list(f.keys()))}) not as expected (45)."


def test_fluo2nx_application_single_det(tmp_path):
    """test nxtomomill fluo2nx CLI targetting a single existing detector"""
    scan_dir = GitlabDataset.get_dataset("fluo_datasets")
    output_file = os.path.join(tmp_path, "nexus_file.nx")

    assert not os.path.exists(output_file), "output_file exists already"
    main(
        [
            "fluo2nx",
            scan_dir,
            output_file,
            "CP1_XRD_insitu_top_ft_100nm",
            "--detectors",
            "xmap",
        ]
    )
    assert os.path.exists(output_file), "output_file doesn't exists"
    with h5py.File(output_file, "r") as f:
        assert (
            len(list(f.keys())) == 15
        ), f"Number of entries ({len(list(f.keys()))}) not as expected (15)."


def test_fluo2nx_application_two_dets(tmp_path):
    """test nxtomomill fluo2nx CLI targetting two existing detectors"""
    scan_dir = GitlabDataset.get_dataset("fluo_datasets")
    output_file = os.path.join(tmp_path, "nexus_file.nx")

    assert not os.path.exists(output_file), "output_file exists already"
    main(
        [
            "fluo2nx",
            scan_dir,
            output_file,
            "CP1_XRD_insitu_top_ft_100nm",
            "--detectors",
            "xmap",
            "falcon",
        ]
    )
    assert os.path.exists(output_file), "output_file doesn't exists"
    with h5py.File(output_file, "r") as f:
        assert (
            len(list(f.keys())) == 30
        ), f"Number of entries ({len(list(f.keys()))}) not as expected (30)."


def test_fluo2nx_application_2D(tmp_path):
    scan_dir = GitlabDataset.get_dataset("fluo_datasets2D")
    output_file = os.path.join(tmp_path, "nexus_file_2d.nx")

    assert not os.path.exists(output_file), "output_file exists already"
    main(
        [
            "fluo2nx",
            scan_dir,
            output_file,
            "CONT2_p2_600nm_FT02_slice_0",
            "--dimension",
            "2",
        ]
    )
    assert os.path.exists(output_file), "output_file doesn't exists"
    with h5py.File(output_file, "r") as f:
        assert (
            len(list(f.keys())) == 4
        ), f"Number of entries ({len(list(f.keys()))}) not as expected (4)."


def test_fluo2nx_application_2D_single_det(tmp_path):
    """test nxtomomill fluo2nx CLI targetting a single existing detector"""
    scan_dir = GitlabDataset.get_dataset("fluo_datasets2D")
    output_file = os.path.join(tmp_path, "nexus_file_2D_singledet.nx")

    assert not os.path.exists(output_file), "output_file exists already"
    main(
        [
            "fluo2nx",
            scan_dir,
            output_file,
            "CONT2_p2_600nm_FT02_slice_0",
            "--detectors",
            "corrweighted",
            "--dimension",
            "2",
        ]
    )
    assert os.path.exists(output_file), "output_file doesn't exists"
    with h5py.File(output_file, "r") as f:
        assert (
            len(list(f.keys())) == 2
        ), f"Number of entries ({len(list(f.keys()))}) not as expected (2)."
