# coding: utf-8

import logging

import pytest
import numpy

from nxtomomill.converter.fluo.fluoscan import FluoTomoScan2D
from nxtomomill.tests.datasets import GitlabDataset

logging.disable(logging.INFO)


@pytest.fixture(scope="class")
def fluodata2D(request):
    cls = request.cls
    cls.scan_dir = GitlabDataset.get_dataset("fluo_datasets2D")
    cls.dataset_basename = "CONT2_p2_600nm_FT02_slice_0"
    cls.scan = FluoTomoScan2D(
        scan=cls.scan_dir,
        dataset_basename=cls.dataset_basename,
        detectors=(),
    )


@pytest.mark.usefixtures("fluodata2D")
class TestFluo2D:
    def test_all_detectors(self):
        assert (
            len(self.scan.el_lines) == 2  # pylint: disable=E1101
        ), f"Number of elements found should be 2 and is {len(self.scan.el_lines)}."  # pylint: disable=E1101
        assert set(self.scan.detectors) == set(  # pylint: disable=E1101
            ["fluo1", "corrweighted"]
        ), f"There should be 2 'detectors' (fluo1 and corrweighted), {len(self.detectors)} were found."  # pylint: disable=E1101

    def test_one_detector(self):
        scan = FluoTomoScan2D(
            scan=self.scan_dir,  # pylint: disable=E1101
            dataset_basename=self.dataset_basename,  # pylint: disable=E1101
            detectors=("corrweighted",),
        )
        assert (
            len(scan.el_lines) == 2
        ), f"Number of elements found should be 2 and is {len(scan.el_lines)}."
        assert (
            len(scan.detectors) == 1
        ), f"There should be 1 detector (corrweighted), {len(scan.detectors)} were found."

        # One ghost detector (no corresponding files)
        # test general section setters
        with pytest.raises(ValueError):
            scan = FluoTomoScan2D(
                scan=self.scan_dir,  # pylint: disable=E1101
                dataset_basename=self.dataset_basename,  # pylint: disable=E1101
                detectors=("toto",),
            )

    def test_load_data(self):
        data = self.scan.load_data("corrweighted", "Ca", 0)  # pylint: disable=E1101
        assert data.shape == (1, 251, 1000)

    def test_load_energy_and_pixel_size(self):
        assert self.scan.energy == 17.1  # pylint: disable=E1101
        assert numpy.allclose(
            self.scan.pixel_size, 6e-10, atol=1e-4  # pylint: disable=E1101
        )  # Tolerance:0.1nm (since pixel_size is expected in um).
