import os
import pytest
from glob import glob
from tomoscan.esrf.mock import MockEDF
from tomoscan.esrf.scan.edfscan import EDFTomoScan
from nxtomomill.converter.edf.checks import OUPUT_CHECK
from nxtomomill.models.edf2nx import EDF2nxModel
from nxtomomill.converter.edf.edfconverter import from_edf_to_nx, post_processing_check


def test_edf2nx_check(tmp_path):
    """
    make sure checking an conversion in post processing works
    """

    folder = tmp_path / "test_edf2nx_check"
    folder.mkdir()
    scans = []
    for scan_name, n_proj in zip(["scanA", "scanB"], [10, 11]):
        scan_path = os.path.join(folder, scan_name)
        MockEDF(
            scan_path=scan_path,
            n_radio=n_proj,
            n_ini_radio=n_proj,
            n_extra_radio=0,
            dim=20,
            dark_n=1,
            flat_n=1,
            distance=2.3,
        )
        scans.append(EDFTomoScan(scan_path))

    # do the conversion of the two files
    config_1 = EDF2nxModel()
    config_1.input_folder = scans[0].path
    config_1.output_file = scans[0].path + ".nx"
    from_edf_to_nx(config_1)
    assert os.path.exists(config_1.output_file)

    config_2 = EDF2nxModel()
    config_2.input_folder = scans[1].path
    config_2.output_file = scans[1].path + ".nx"
    from_edf_to_nx(config_2)
    assert os.path.exists(config_2.output_file)

    # check
    post_processing_check(configuration=config_1)
    post_processing_check(configuration=config_2)

    assert os.path.exists(scans[0].path)

    config_test = EDF2nxModel()
    config_test.output_checks = (OUPUT_CHECK.COMPARE_VOLUME,)
    config_test.delete_edf_source_files = True
    config_test.input_folder = scans[0].path
    config_test.output_file = scans[1].path + ".nx"
    assert _get_nb_edf_files(scans[0].path) == 12
    assert _get_nb_edf_files(scans[1].path) == 13

    with pytest.raises(ValueError):
        post_processing_check(configuration=config_test)

    # make sure no edf file have been removed
    assert _get_nb_edf_files(scans[0].path) == 12
    assert _get_nb_edf_files(scans[1].path) == 13

    config_test.input_folder = scans[0].path
    config_test.output_file = scans[0].path + ".nx"

    post_processing_check(configuration=config_test)
    assert _get_nb_edf_files(scans[0].path) == 0
    assert _get_nb_edf_files(scans[1].path) == 13

    config_test.input_folder = scans[1].path
    config_test.output_file = scans[1].path + ".nx"
    post_processing_check(configuration=config_test)
    assert _get_nb_edf_files(scans[1].path) == 0


def _get_nb_edf_files(folder):
    return len(glob(os.path.join(folder, "*.edf")))
