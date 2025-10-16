import os
import numpy
from fabio.edfimage import EdfImage
from silx.io.url import DataUrl
from nxtomomill.converter.edf.checks import compare_volumes
from tomoscan.esrf.scan.nxtomoscan import NXtomoScan
from tomoscan.io import HDF5File


def test_compare_volumes(tmp_path):
    """test the compare_volumes function"""

    input_folder = tmp_path / "input"
    input_folder.mkdir()
    output_folder = tmp_path / "output"
    output_folder.mkdir()

    frame_1 = (
        numpy.arange(10, 110, dtype=numpy.float32)
        .reshape(1, 10, 10)
        .astype(numpy.float32)
    )
    frame_2 = (
        numpy.arange(30, 130, dtype=numpy.float32)
        .reshape(1, 10, 10)
        .astype(numpy.float32)
    )
    frame_3 = (
        numpy.arange(100, 200, dtype=numpy.float32)
        .reshape(1, 10, 10)
        .astype(numpy.float32)
    )

    edf_frame_files = []
    edf_frame_urls = []
    for i_frame, frame in enumerate((frame_1, frame_2, frame_3)):
        edf_writer = EdfImage(
            data=frame[0],  # [0]: easy way to concatenate the frame later
            header={},
        )
        edf_frame_file = os.path.join(input_folder, f"frame_{i_frame}.edf")
        edf_writer.write(edf_frame_file)
        edf_frame_files.append(edf_frame_file)
        edf_frame_urls.append(
            [
                DataUrl(file_path=edf_frame_file, scheme="fabio"),
                False,
            ]
        )

    scan_0_file = os.path.join(output_folder, "nx_tomo.nx")
    with HDF5File(scan_0_file, mode="w") as h5f:
        h5f["entry/instrument/detector/data"] = numpy.vstack(
            [frame_1, frame_2, frame_3]
        )

    assert len(compare_volumes(edf_frame_urls, NXtomoScan(scan_0_file, "entry"))) == 0

    # test inverting a frame
    scan_1_file = os.path.join(output_folder, "toto_tomo.nx")
    with HDF5File(scan_1_file, mode="w") as h5f:
        h5f["entry/instrument/detector/data"] = numpy.vstack(
            [frame_1, frame_1, frame_3]
        )

    assert len(compare_volumes(edf_frame_urls, NXtomoScan(scan_1_file, "entry"))) == 1
    # then ignore second frame
    edf_frame_urls[1][1] = True
    assert len(compare_volumes(edf_frame_urls, NXtomoScan(scan_1_file, "entry"))) == 0

    # test modifying the type
    scan_2_file = os.path.join(output_folder, "nx_tomo32.nx")
    with HDF5File(scan_2_file, mode="w") as h5f:
        h5f["entry/instrument/detector/data"] = numpy.vstack(
            [frame_1, frame_2, frame_3]
        ).astype(numpy.uint16)

    assert len(compare_volumes(edf_frame_urls, NXtomoScan(scan_2_file, "entry"))) == 1
