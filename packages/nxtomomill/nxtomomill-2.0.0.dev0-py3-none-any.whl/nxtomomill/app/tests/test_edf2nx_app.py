# coding: utf-8

import os
import tempfile

from tomoscan.esrf.mock import MockEDF

from nxtomomill.app.edf2nx import main


def test_edf2nx_application():
    """test nxtomomill edf2nx input_file output_file"""
    with tempfile.TemporaryDirectory() as folder:
        edf_acq_path = os.path.join(folder, "acquisition")
        n_proj = 10
        MockEDF(
            scan_path=edf_acq_path,
            n_radio=n_proj,
            n_ini_radio=n_proj,
        )
        output_file = os.path.join(edf_acq_path, "nexus_file.nx")

        assert not os.path.exists(output_file), "output_file exists already"
        main(["edf2nx", edf_acq_path, output_file])
        assert os.path.exists(output_file), "output_file doesn't exists"
