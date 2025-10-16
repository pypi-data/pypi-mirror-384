# coding: utf-8

import os
import tempfile

from nxtomomill.app.dxfile2nx import main
from nxtomomill.tests.utils.dxfile import MockDxFile


def test_dxfile2nx_application():
    """test nxtomomill dxfile2nx input_file output_file"""
    with tempfile.TemporaryDirectory() as folder:
        dx_file_path = os.path.join(folder, "dxfile.dx")
        nx_file_path = os.path.join(folder, "dxfile.nx")
        n_projections = 50
        n_darks = 2
        n_flats = 4

        MockDxFile(
            file_path=dx_file_path,
            n_projection=n_projections,
            n_darks=n_darks,
            n_flats=n_flats,
        )
        assert not os.path.exists(nx_file_path), "outputfile exists already"
        main(["dxfile2nx", dx_file_path, nx_file_path])
        assert os.path.exists(nx_file_path), "outputfile doesn't exists"
