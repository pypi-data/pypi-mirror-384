# coding: utf-8

import os
import pytest
import numpy

from nxtomomill import converter
from nxtomomill.tests.utils.dxfile import MockDxFile

from tomoscan.esrf.scan.nxtomoscan import NXtomoScan
from tomoscan.validator import is_valid_for_reconstruction

from silx.io.utils import get_data


@pytest.mark.parametrize("duplicate_data", (True, False))
def test_dx_file_conversion(tmp_path, duplicate_data):

    folder = tmp_path / "test_dx_file_conversion"
    folder.mkdir()
    dxfile_path = os.path.join(folder, "dxfile.h5")

    n_projections = 50
    n_darks = 2
    n_flats = 4
    mock = MockDxFile(
        file_path=dxfile_path,
        n_projection=n_projections,
        n_darks=n_darks,
        n_flats=n_flats,
    )

    output_file = os.path.join(folder, "dxfile.nx")

    results = converter.from_dx_to_nx(
        input_file=dxfile_path,
        output_file=output_file,
        duplicate_data=duplicate_data,
    )
    assert len(results) == 1
    assert os.path.exists(output_file)
    _, entry = results[0]
    scan = NXtomoScan(output_file, entry)
    assert len(scan.projections) == n_projections
    assert len(scan.darks) == n_darks
    assert len(scan.flats) == n_flats
    assert numpy.array(scan.rotation_angle).min() == 0
    assert numpy.array(scan.rotation_angle).max() == 180
    assert is_valid_for_reconstruction(scan)

    # check arrays are correctly copied from mock
    numpy.testing.assert_array_equal(mock.data_dark[0], get_data(scan.darks[0]))
    numpy.testing.assert_array_equal(mock.data_flat[1], get_data(scan.flats[3]))
    idx_last_proj = n_projections + n_flats + n_darks - 1
    numpy.testing.assert_array_equal(
        mock.data_proj[-1], get_data(scan.projections[idx_last_proj])
    )
    assert scan.rotation_angle[0] == 0  # pylint: disable=E1136
    assert scan.rotation_angle[5] == 0  # pylint: disable=E1136
    assert scan.rotation_angle[6] == 0  # pylint: disable=E1136
    assert scan.rotation_angle[-1] == 180  # pylint: disable=E1136

    # if overwrite not requested should fail on reprocessing
    with pytest.raises(OSError):
        converter.from_dx_to_nx(
            input_file=dxfile_path,
            output_file=output_file,
            duplicate_data=duplicate_data,
            overwrite=False,
        )

    # if overwrite requested should succeed
    converter.from_dx_to_nx(
        input_file=dxfile_path,
        output_file=output_file,
        overwrite=True,
        duplicate_data=duplicate_data,
    )
