# coding: utf-8

import os
import tempfile

import pytest
from silx.io.url import DataUrl

from tomoscan.io import HDF5File
from nxtomomill.converter.hdf5.acquisition.baseacquisition import (
    BaseAcquisition,
    get_dataset_name_from_motor,
)
from nxtomomill.io.config import TomoHDF5Config


def test_BaseAquisition():
    """simple test of the BaseAcquisition class"""

    with tempfile.TemporaryDirectory() as folder:
        file_path = os.path.join(folder, "test.h5")
        with HDF5File(file_path, mode="w") as h5f:
            h5f["/data/toto/dataset"] = 12

        url = DataUrl(file_path=file_path, data_path="/data/toto", scheme="silx")
        std_acq = BaseAcquisition(
            root_url=url,
            configuration=TomoHDF5Config(),
            detector_sel_callback=None,
            start_index=0,
        )
        with std_acq.read_entry() as entry:
            assert "dataset" in entry


def test_get_dataset_name_from_motor():
    """test get_dataset_name_from_motor function"""
    set_1 = ["rotation", "test1", "alias"]
    assert get_dataset_name_from_motor(set_1, "rotation") == "test1"
    assert get_dataset_name_from_motor(set_1, "my motor") is None

    set_2 = ["rotation", "test1", "alias", "x translation", "m2", "test1"]
    assert get_dataset_name_from_motor(set_2, "rotation") == "test1"
    assert get_dataset_name_from_motor(set_2, "x translation") == "m2"

    set_3 = ["rotation"]
    with pytest.raises(ValueError):
        get_dataset_name_from_motor(set_3, "rotation")
