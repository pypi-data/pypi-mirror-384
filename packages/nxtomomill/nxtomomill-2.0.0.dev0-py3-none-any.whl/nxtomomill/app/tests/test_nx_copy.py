import os
from nxtomo.application.nxtomo import NXtomo
from nxtomomill.app.nxcopy import get_output_file
from nxtomomill.app.nxcopy import main


def test_nxcopy_get_output_file():
    """dummy test for 'get_output_file'"""
    assert get_output_file("output.nx", "input.nx") == os.path.abspath("output.nx")
    assert (
        get_output_file("/file1/to/", "/file2/to/input/input.nx")
        == "/file1/to/input.nx"
    )


def test_copy(tmp_path):
    """test 'copy' application"""
    input_folder = tmp_path / "input"
    input_folder.mkdir()
    input_nx_tomo_file = os.path.join(input_folder, "nexus.nx")

    output_folder = tmp_path / "output"
    output_folder.mkdir()
    output_folder = str(output_folder)

    nx_tomo = NXtomo()
    nx_tomo.save(input_nx_tomo_file, "/entry0000")
    nx_tomo.save(input_nx_tomo_file, "/entry0002")
    nx_tomo.save(input_nx_tomo_file, "/entry0004")

    main(["nx-copy", input_nx_tomo_file, output_folder, "--entry", "entry0002"])
    output_file = os.path.join(output_folder, "nexus.nx")
    assert os.path.exists(output_file)
    assert len(NXtomo.get_valid_entries(output_file)) == 1
    main(["nx-copy", input_nx_tomo_file, output_folder, "--overwrite"])
    assert len(NXtomo.get_valid_entries(output_file)) == 3
    main(["nx-copy", input_nx_tomo_file, output_folder, "--overwrite", "--remove-vds"])
    assert len(NXtomo.get_valid_entries(output_file)) == 3
