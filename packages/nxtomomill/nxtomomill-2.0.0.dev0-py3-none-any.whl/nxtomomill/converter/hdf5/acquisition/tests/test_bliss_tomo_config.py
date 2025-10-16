import pytest
import os
import numpy
from tomoscan.io import HDF5File, get_swmr_mode
from nxtomomill.converter.hdf5.acquisition.blisstomoconfig import TomoConfig


def test_tomo_config(tmp_path):
    """
    test a configuration from bliss can be read from nxtomomill
    """
    file_path = os.path.join(tmp_path, "test_bliss_tomo_config.hdf5")
    with HDF5File(file_path, mode="w") as h5s:
        tomo_config_group = h5s.create_group("/0/test/instrument/tomoconfig")
        tomo_config_group["rotation"] = ("my_rot", "rot")
        tomo_config_group["sample_u"] = numpy.array(
            [
                "alias",
                "motor_name",
            ],
            dtype=object,
        )
        tomo_config_group["sample_v"] = numpy.array(
            [
                "sample_v_motor",
            ],
            dtype=object,
        )
        tomo_config_group["sample_x"] = [
            "sample_x_motor",
        ]
        tomo_config_group["sample_y"] = numpy.array(
            [
                "sample_y_motor",
            ],
            dtype=object,
        )
        tomo_config_group["detector"] = ["alias", "frelon"]
        tomo_config_group["translation_y"] = numpy.array(
            [
                "ty",
            ],
            dtype=object,
        )
        tomo_config_group["translation_z"] = numpy.array(
            [
                "tz",
            ],
            dtype=object,
        )
        tomo_config_group["rotation_is_clockwise"] = True

    with pytest.raises(TypeError):
        TomoConfig.from_technique_group(file_path)

    with pytest.raises(KeyError):
        TomoConfig.from_technique_group(h5s)

    with HDF5File(file_path, mode="r", swmr=get_swmr_mode()) as h5s:
        tomo_config = TomoConfig.from_technique_group(h5s["/0/test/instrument"])

    numpy.testing.assert_array_equal(
        tomo_config.rotation, numpy.array(["my_rot", "rot"], dtype=object)
    )
    numpy.testing.assert_array_equal(
        tomo_config.sample_u, numpy.array(["alias", "motor_name"], dtype=object)
    )
    numpy.testing.assert_array_equal(
        tomo_config.sample_v,
        numpy.array(
            [
                "sample_v_motor",
            ],
            dtype=object,
        ),
    )
    numpy.testing.assert_array_equal(
        tomo_config.sample_x,
        numpy.array(
            [
                "sample_x_motor",
            ],
            dtype=object,
        ),
    )
    numpy.testing.assert_array_equal(
        tomo_config.sample_y,
        numpy.array(
            [
                "sample_y_motor",
            ],
            dtype=object,
        ),
    )
    numpy.testing.assert_array_equal(
        tomo_config.tomo_detector,
        numpy.array(
            [
                "alias",
                "frelon",
            ],
            dtype=object,
        ),
    )
    numpy.testing.assert_array_equal(
        tomo_config.translation_y,
        numpy.array(
            [
                "ty",
            ],
            dtype=object,
        ),
    )
    numpy.testing.assert_array_equal(
        tomo_config.translation_z,
        numpy.array(
            [
                "tz",
            ],
            dtype=object,
        ),
    )

    assert tomo_config.rotation_is_clockwise is True
