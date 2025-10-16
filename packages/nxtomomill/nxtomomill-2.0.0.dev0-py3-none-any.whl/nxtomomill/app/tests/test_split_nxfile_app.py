import os
import numpy
import pytest
import pint
from tomoscan.io import HDF5File, get_swmr_mode
from nxtomo.application.nxtomo import NXtomo
from nxtomomill.app.split_nxfile import split

_ureg = pint.get_application_registry()


@pytest.mark.parametrize("duplicate_data", (True, False))
def test_split_nxfile(tmp_path, duplicate_data):
    """
    test execution of split_nxfile
    One file contains
    """
    nx_tomo = NXtomo()
    n_frames = 20
    nx_tomo.instrument.detector.data = numpy.random.random(
        100 * 100 * n_frames
    ).reshape([n_frames, 100, 100])
    nx_tomo.sample.rotation_angle = [0, 12] * _ureg.degree

    output_dir = tmp_path / "test_split_nx_file"
    output_dir.mkdir()
    output_dir = str(output_dir)
    output_file = os.path.join(output_dir, "input_file.nx")
    nx_tomo.save(output_file, "entry0000")
    nx_tomo.save(output_file, "entry0001")
    nx_tomo.save(output_file, "entry0002")

    # test split
    with pytest.raises(ValueError):
        # make sure if no '{index}' or '{entry_name}' are provided this raises an error
        split(
            output_file,
            output_file_pattern=os.sep.join([output_dir, "output_dir_1", "part_.nx"]),
        )

    split(
        output_file,
        output_file_pattern=os.sep.join(
            [output_dir, "output_dir_1", "part_{index}.nx"]
        ),
        duplicate_data=duplicate_data,
    )
    for i_file in range(3):
        assert os.path.exists(
            tmp_path / f"test_split_nx_file/output_dir_1/part_{i_file}.nx"
        )

    split(
        output_file,
        output_file_pattern=os.sep.join(
            [output_dir, "output_dir_2", "{entry_name}.nx"]
        ),
        duplicate_data=duplicate_data,
    )
    for output in ("entry0000", "entry0001", "entry0002"):
        assert os.path.exists(tmp_path / f"test_split_nx_file/output_dir_2/{output}.nx")

    # test overwrite
    with pytest.raises(KeyError):
        split(
            output_file,
            output_file_pattern=os.sep.join(
                [output_dir, "output_dir_2", "{entry_name}.nx"]
            ),
            duplicate_data=duplicate_data,
        )

    with HDF5File(
        tmp_path / "test_split_nx_file/output_dir_2/entry0002.nx",
        mode="r",
        swmr=get_swmr_mode(),
    ) as h5f:
        assert "entry0002" in h5f.keys()
        assert "entry0000" not in h5f.keys()
