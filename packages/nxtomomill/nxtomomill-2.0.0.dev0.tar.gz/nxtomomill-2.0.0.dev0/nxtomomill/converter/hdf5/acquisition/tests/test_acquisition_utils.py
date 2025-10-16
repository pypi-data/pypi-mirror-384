# coding: utf-8

import os
import numpy
import pytest
import h5py

from silx.io.url import DataUrl
from tomoscan.io import HDF5File
from nxtomo.nxobject.nxdetector import ImageKey

from nxtomomill.io.config import TomoHDF5Config
from nxtomomill.models.h52nx._acquisitionstep import AcquisitionStep
from nxtomomill.converter.hdf5.acquisition.utils import (
    deduce_machine_current,
    split_timestamps,
    get_entry_type,
    group_series,
)
from nxtomomill.converter.hdf5.acquisition.zseriesacquisition import (
    ZSeriesBaseAcquisition,
)
from nxtomomill.utils.utils import str_datetime_to_numpy_datetime64


def test_deduce_machine_current():
    """
    Test `deduce_current` function. Base function to compute current for each frame according to it's timestamp
    """

    current_datetimes = {
        "2022-01-15T21:07:58.360095+02:00": 1.1,
        "2022-04-15T21:07:58.360095+02:00": 121.1,
        "2022-04-15T21:09:58.360095+02:00": 123.3,
        "2022-04-15T21:11:58.360095+02:00": 523.3,
        "2022-12-15T21:07:58.360095+02:00": 1000.3,
    }
    with pytest.raises(ValueError):
        deduce_machine_current(tuple(), {})
    with pytest.raises(TypeError):
        deduce_machine_current(12, 2)
    with pytest.raises(TypeError):
        deduce_machine_current(
            [
                12,
            ],
            2,
        )
    with pytest.raises(TypeError):
        deduce_machine_current(
            [
                2,
            ],
            current_datetimes,
        )

    converted_currents = {}
    for elec_cur_datetime_str, elect_cur in current_datetimes.items():
        datetime_as_datetime = str_datetime_to_numpy_datetime64(elec_cur_datetime_str)
        converted_currents[datetime_as_datetime] = elect_cur

    # check exacts values, left and right bounds
    assert deduce_machine_current(
        (str_datetime_to_numpy_datetime64("2022-01-15T21:07:58.360095+02:00"),),
        converted_currents,
    ) == (1.1,)
    assert deduce_machine_current(
        (str_datetime_to_numpy_datetime64("2022-01-14T21:07:58.360095+02:00"),),
        converted_currents,
    ) == (1.1,)
    assert deduce_machine_current(
        (str_datetime_to_numpy_datetime64("2022-12-15T21:07:58.360095+02:00"),),
        converted_currents,
    ) == (1000.3,)
    assert deduce_machine_current(
        (str_datetime_to_numpy_datetime64("2022-12-16T21:07:58.360095+02:00"),),
        converted_currents,
    ) == (1000.3,)
    # check interpolated values
    numpy.testing.assert_almost_equal(
        deduce_machine_current(
            (str_datetime_to_numpy_datetime64("2022-04-15T21:08:58.360095+02:00"),),
            converted_currents,
        )[0],
        (122.2,),
    )
    numpy.testing.assert_almost_equal(
        deduce_machine_current(
            (str_datetime_to_numpy_datetime64("2022-04-15T21:10:28.360095+02:00"),),
            converted_currents,
        )[0],
        (223.3,),
    )

    # test several call and insure keep order
    numpy.testing.assert_almost_equal(
        deduce_machine_current(
            (
                str_datetime_to_numpy_datetime64("2022-01-15T21:07:58.360095+02:00"),
                str_datetime_to_numpy_datetime64("2022-04-15T21:10:28.360095+02:00"),
                str_datetime_to_numpy_datetime64("2022-04-15T21:08:58.360095+02:00"),
            ),
            converted_currents,
        ),
        (1.1, 223.3, 122.2),
    )


@pytest.mark.parametrize("n_part", (1, 3, 4, 7, 9, 12))
@pytest.mark.parametrize(
    "array_to_test",
    (numpy.arange(-15, 23, dtype=numpy.float32), numpy.ones(57, dtype=numpy.uint8)),
)
def test_split_timestamps(n_part, array_to_test):
    split_arrays = tuple(
        split_timestamps(
            my_array=array_to_test,
            n_part=n_part,
        )
    )
    assert len(split_arrays) == n_part
    assert split_arrays[0].dtype == array_to_test.dtype
    numpy.testing.assert_array_equal(
        numpy.concatenate([numpy.array(part) for part in split_arrays]),
        numpy.array(array_to_test),
    )


def test_get_entry_type(tmp_path):
    """test the get_entry_type function"""
    test_folder = tmp_path / "test_get_entry_type"
    test_folder.mkdir()
    test_file = os.path.join(test_folder, "test.hdf5")

    default_configuration = TomoHDF5Config()

    with HDF5File(test_file, mode="w") as h5f:
        h5f["group1/title"] = "darks"
        url_case1_darks = DataUrl(file_path=test_file, data_path="group1")

        h5f["group2/title"] = "flats"
        url_case1_flats = DataUrl(file_path=test_file, data_path="group2")

        h5f["group3/title"] = "darks"
        h5f["group3/technique/image_key"] = ImageKey.PROJECTION.value
        url_case2_proj = DataUrl(file_path=test_file, data_path="group3")

        h5f["group4/title"] = "darks"
        h5f["group4/technique/image_key"] = ImageKey.ALIGNMENT.value
        url_case2_alignment = DataUrl(file_path=test_file, data_path="group4")

        h5f["group5/technique/image_key"] = ImageKey.INVALID.value
        url_case3_invalid = DataUrl(file_path=test_file, data_path="group5")
        h5f["group6/technique/image_key"] = ImageKey.PROJECTION.value
        url_case3_proj = DataUrl(file_path=test_file, data_path="group6")

    # make sure if title is provided this is still working
    assert (
        get_entry_type(url_case1_darks, default_configuration) == AcquisitionStep.DARK
    )
    assert (
        get_entry_type(url_case1_flats, default_configuration) == AcquisitionStep.FLAT
    )

    # make sure the 'technique/image_key' get priority other the 'title'
    assert (
        get_entry_type(url_case2_proj, default_configuration)
        == AcquisitionStep.PROJECTION
    )
    assert (
        get_entry_type(url_case2_alignment, default_configuration)
        == AcquisitionStep.ALIGNMENT
    )

    # make sure if title is no more present then 'image_key' will be picked anyway
    assert get_entry_type(url_case3_invalid, default_configuration) is None
    assert (
        get_entry_type(url_case3_proj, default_configuration)
        == AcquisitionStep.PROJECTION
    )


def test_group_z_series(tmp_path):
    input_file = os.path.join(tmp_path, "test_z_series.h5")
    z_acquisitions = []
    n_series = 3
    n_scan_per_series = 4
    with h5py.File(input_file, mode="w") as h5f:
        i_scan = 0
        for i_series in range(n_series):
            for _ in range(n_scan_per_series):
                h5f[f"{i_scan}.1/sample/name"] = (
                    f"my_serie_{str(i_series).zfill(4)}_{str(i_scan).zfill(4)}"
                )
                z_acquisitions.append(
                    ZSeriesBaseAcquisition(
                        root_url=DataUrl(
                            file_path=input_file,
                            data_path=f"{i_scan}.1",
                            scheme="silx",
                        ),
                        configuration={},
                        detector_sel_callback=None,
                        start_index=i_scan,
                    )
                )
                i_scan += 1

    series_grouped = []
    for acquisition in z_acquisitions:
        series_grouped = group_series(
            acquisition=acquisition, list_of_series=series_grouped
        )

    assert len(series_grouped) == n_series
    for i in range(n_series):
        assert series_grouped[i] == list(
            [
                z_acquisitions[i * n_scan_per_series + i_scan]
                for i_scan in range(n_scan_per_series)
            ]
        )
