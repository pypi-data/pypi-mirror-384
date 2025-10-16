# coding: utf-8

import os

from nxtomomill.app.h52nx import main
from nxtomomill.tests.utils.bliss import MockBlissAcquisition


def test_h52nx_application(tmp_path):
    """test nxtomomill h52nx input_file output_file --single-file"""
    folder = tmp_path / "test_h52nx_application"
    folder.mkdir()
    nx_file_path = os.path.join(folder, "acquisition.nx")

    bliss_mock = MockBlissAcquisition(
        n_sample=1,
        n_sequence=1,
        n_scan_per_sequence=10,
        n_darks=5,
        n_flats=5,
        with_nx_detector_attr=True,
        output_dir=folder,
        detector_name="pcolinux",
    )

    h5_file_path = bliss_mock.samples[0].sample_file
    assert not os.path.exists(nx_file_path), "outputfile exists already"
    main(["h52nx", h5_file_path, nx_file_path, "--single-file"])
    assert os.path.exists(nx_file_path), "outputfile doesn't exists"
