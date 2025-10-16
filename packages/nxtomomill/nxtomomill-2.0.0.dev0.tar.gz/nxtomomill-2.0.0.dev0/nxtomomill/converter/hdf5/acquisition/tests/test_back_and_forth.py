from __future__ import annotations

import os
import pint
import numpy

from nxtomo.application.nxtomo import NXtomo
from nxtomo.nxobject.nxdetector import ImageKey

from nxtomomill.tests.datasets import GitlabDataset
from nxtomomill import converter
from nxtomomill.io.config import TomoHDF5Config

_ureg = pint.get_application_registry()


def test_back_and_forth_conversion(tmp_path):
    """test nxtomomill fluo2nx CLI with default parameters (handle all detectors found)"""
    scan_dir = GitlabDataset.get_dataset("h5_datasets")
    assert scan_dir is not None
    input_file = os.path.join(scan_dir, "back_and_forth/bliss_tomo_2025_06_17.h5")

    output_file = os.path.join(tmp_path, "nexus_file.nx")

    assert not os.path.exists(output_file), "output_file exists already"
    configuration = TomoHDF5Config()

    configuration.output_file = output_file
    configuration.input_file = input_file
    configuration.no_input = True
    configuration.raises_error = False
    configuration.no_master_file = False

    # Step 1: make sure conversion is not done if we mess with tiles (and make sure this is back-and-forth which is recognized and not another like multi-tomo)
    tmp_back_and_forth_titles = configuration.back_and_forth_init_titles
    configuration.back_and_forth_init_titles = tuple()

    result = converter.from_h5_to_nx(configuration=configuration)
    assert not os.path.exists(output_file)

    # Step 2: test the real conversion using default inputs
    configuration.back_and_forth_init_titles = tmp_back_and_forth_titles
    result = converter.from_h5_to_nx(configuration=configuration)
    assert os.path.exists(output_file)
    # check we have our 3 NXtomo are converted with each 101 projections, a flat and a dark at the beginning and a flat at the end.
    assert len(result) == 3
    nx_tomos = [NXtomo().load(file_path, entry) for (file_path, entry) in result]
    n_proj_per_nx_tomo = 101
    for i_nx_tomo, nx_tomo in enumerate(nx_tomos):
        # check instrument
        assert len(nx_tomo.instrument.detector.image_key) == n_proj_per_nx_tomo + 40 * 2
        # image key
        numpy.testing.assert_array_equal(
            nx_tomo.instrument.detector.image_key,
            numpy.concatenate(
                (
                    [ImageKey.DARK_FIELD] * 20,
                    [ImageKey.FLAT_FIELD] * 20,
                    [ImageKey.PROJECTION] * n_proj_per_nx_tomo,
                    [ImageKey.FLAT_FIELD] * 20,
                    [ImageKey.DARK_FIELD] * 20,
                )
            ),
        )
        # sequence number
        proj_seq_start = n_proj_per_nx_tomo * i_nx_tomo + 40
        second_flat_start_index = 40 + 3 * n_proj_per_nx_tomo
        numpy.testing.assert_array_equal(
            nx_tomo.instrument.detector.sequence_number,
            numpy.concatenate(
                (
                    numpy.arange(0, 20, dtype=numpy.uint32),  # dark
                    numpy.arange(20, 40, dtype=numpy.uint32),  # flat
                    numpy.arange(
                        proj_seq_start,
                        proj_seq_start + n_proj_per_nx_tomo,
                        dtype=numpy.uint32,
                    ),  # projections
                    numpy.arange(
                        second_flat_start_index,
                        second_flat_start_index + 20,
                        dtype=numpy.uint32,
                    ),  # flat
                    numpy.arange(
                        second_flat_start_index + 20,
                        second_flat_start_index + 40,
                        dtype=numpy.uint32,
                    ),  # dark
                )
            ),
        )
        # detector pixel size
        numpy.testing.assert_almost_equal(
            nx_tomo.instrument.detector.x_pixel_size.magnitude,
            (2.55135 * _ureg.micrometer).magnitude,
            decimal=5,
        )
        numpy.testing.assert_almost_equal(
            nx_tomo.instrument.detector.y_pixel_size.magnitude,
            (2.55135 * _ureg.micrometer).magnitude,
            decimal=5,
        )

        assert nx_tomo.instrument.detector.distance == 3500 * _ureg.millimeter
        # check energy
        assert nx_tomo.energy == 10.0 * _ureg.keV
        # check sample
        assert nx_tomo.sample.x_pixel_size == 2.4 * _ureg.micrometer
        assert nx_tomo.sample.y_pixel_size == 2.4 * _ureg.micrometer
        # check source
        assert nx_tomo.instrument.source.distance == -55500 * _ureg.millimeter
