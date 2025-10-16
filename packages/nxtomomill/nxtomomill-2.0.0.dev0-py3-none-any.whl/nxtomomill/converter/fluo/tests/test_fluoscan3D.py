# coding: utf-8

import logging

import pytest

from nxtomomill.converter.fluo.fluoscan import FluoTomoScan3D
from nxtomomill.tests.datasets import GitlabDataset

logging.disable(logging.INFO)


@pytest.fixture(scope="class")
def fluodata3D(request):
    cls = request.cls
    cls.scan_dir = GitlabDataset.get_dataset("fluo_datasets")
    cls.dataset_basename = "CP1_XRD_insitu_top_ft_100nm"
    cls.scan = FluoTomoScan3D(
        scan=cls.scan_dir,
        dataset_basename=cls.dataset_basename,
        detectors=(),
    )


@pytest.mark.usefixtures("fluodata3D")
class TestFluo3D:
    def test_all_detectors(self):
        assert (
            len(self.scan.el_lines) == 14  # pylint: disable=E1101
        ), f"Number of elements found should be 14 and is {len(self.scan.el_lines)}."  # pylint: disable=E1101
        assert set(self.scan.detectors) == set(  # pylint: disable=E1101
            ["falcon", "weighted", "xmap"]
        ), f"There should be 3 'detectors' (xmap, falcon and weighted), {len(self.detectors)} were found."  # pylint: disable=E1101

    def test_one_detector(self):
        scan = FluoTomoScan3D(
            scan=self.scan_dir,  # pylint: disable=E1101
            dataset_basename=self.dataset_basename,  # pylint: disable=E1101
            detectors=("xmap",),
        )
        assert (
            len(scan.el_lines) == 14
        ), f"Number of elements found should be 14 and is {len(scan.el_lines)}."
        assert (
            len(scan.detectors) == 1
        ), f"There should be 1 detector (xmap), {len(scan.detectors)} were found."

        # One ghost detector (no corresponding files)
        # test general section setters
        with pytest.raises(ValueError):
            scan = FluoTomoScan3D(
                scan=self.scan_dir,  # pylint: disable=E1101
                dataset_basename=self.dataset_basename,  # pylint: disable=E1101
                detectors=("toto",),
            )

    def test_load_data(self):
        data = self.scan.load_data("xmap", "Ti", 0)  # pylint: disable=E1101
        assert data.shape == (2, 51, 280)

    def test_load_energy_and_pixel_size(self):
        assert self.scan.pixel_size == 1.3e-6  # pylint: disable=E1101
        assert self.scan.energy == 17.1  # pylint: disable=E1101
