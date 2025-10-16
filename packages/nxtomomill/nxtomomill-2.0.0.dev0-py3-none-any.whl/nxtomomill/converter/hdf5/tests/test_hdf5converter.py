# coding: utf-8

import os
import sys
import tempfile

import h5py
import numpy
import pint

from tomoscan.esrf.scan.utils import cwd_context

from nxtomomill import converter
from nxtomomill.tests.datasets import GitlabDataset
from nxtomomill.converter.hdf5.acquisition.utils import (
    get_nx_detectors,
    guess_nx_detector,
)
from nxtomomill.io.config import TomoHDF5Config
from nxtomomill.tests.utils.bliss import _BlissSample
from nxtomomill.utils.hdf5 import DatasetReader, EntryReader
from nxtomomill.converter.hdf5.utils import (
    PROCESSED_DATA_DIR_NAME,
    RAW_DATA_DIR_NAME,
    get_default_output_file,
)
from nxtomomill.models.h52nx import H52nxModel

from tomoscan.io import HDF5File, get_swmr_mode

try:
    from tomoscan.esrf.scan.hdf5scan import NXtomoScan
except ImportError:
    from tomoscan.esrf.hdf5scan import NXtomoScan

import subprocess  # nosec B404
from glob import glob

import pytest
from silx.io.url import DataUrl
from silx.io.utils import get_data
from tomoscan.validator import is_valid_for_reconstruction

from nxtomo.application.nxtomo import NXtomo
from nxtomo.nxobject.nxdetector import ImageKey

from nxtomomill.models.h52nx.FrameGroup import FrameGroup
from nxtomomill.tests.utils.bliss import MockBlissAcquisition

_ureg = pint.get_application_registry()


def url_has_been_copied(file_path: str, url: DataUrl):
    """util function to parse the `duplicate_data` folder and
    insure the copy of the dataset has been done"""
    duplicate_data_url = DataUrl(
        file_path=file_path, data_path="/duplicate_data", scheme="silx"
    )
    url_path = url.path()
    with EntryReader(duplicate_data_url) as duplicate_data_node:
        for _, dataset in duplicate_data_node.items():
            if "original_url" in dataset.attrs:
                original_url = dataset.attrs["original_url"]
                # the full dataset is registered in the attributes.
                # Here we only check the scan entry name
                if original_url.startswith(url_path):
                    return True
    return False


def test_simple_converter_with_nx_detector_attr(tmp_path):
    """
    Test a simple conversion when NX_class is defined
    """
    folder = tmp_path / "output_test_simple_converter_with_nx_detector_attr"
    folder.mkdir()
    config = TomoHDF5Config()
    config.no_master_file = False

    bliss_mock = MockBlissAcquisition(
        n_sample=2,
        n_sequence=1,
        n_scan_per_sequence=10,
        n_darks=5,
        n_flats=5,
        with_nx_detector_attr=True,
        output_dir=folder,
        detector_name="pcolinux",
        create_tomo_config=False,
    )
    for sample in bliss_mock.samples:
        assert os.path.exists(sample.sample_file)
        config.output_file = sample.sample_file.replace(".h5", ".nx")
        config.input_file = sample.sample_file
        config.raises_error = True
        config.sample_x_keys = ("sx",)
        config.sample_y_keys = ("sy",)
        assert len(converter.get_bliss_tomo_entries(sample.sample_file, config)) == 1

        converter.from_h5_to_nx(
            configuration=config,
        )
        # insure only one file is generated
        assert os.path.exists(config.output_file)
        # insure data is here
        with HDF5File(config.output_file, mode="r", swmr=get_swmr_mode()) as h5s:
            for _, entry_node in h5s.items():
                assert "instrument/detector/data" in entry_node
                dataset = entry_node["instrument/detector/data"]
            # check virtual dataset are relative and valid
            assert dataset.is_virtual
            for vs in dataset.virtual_sources():
                assert not os.path.isabs(vs.file_name)
            # insure connection is valid. There is no
            # 'VirtualSource.is_valid' like function
            assert not (dataset[()].min() == 0 and dataset[()].max() == 0)
            instrument_grp = entry_node.require_group("instrument")
            assert "beam" in instrument_grp


def test_invalid_tomo_n(tmp_path):
    """Test translation fails if no detector can be found"""
    folder = tmp_path / "output_test_test_invalid_tomo_n"
    folder.mkdir()
    config = TomoHDF5Config()
    bliss_mock = MockBlissAcquisition(
        n_sample=1,
        n_sequence=1,
        n_scan_per_sequence=10,
        n_darks=5,
        n_flats=5,
        with_nx_detector_attr=True,
        output_dir=folder,
        create_tomo_config=False,
    )
    assert len(bliss_mock.samples) == 1
    sample = bliss_mock.samples[0]
    assert os.path.exists(sample.sample_file)
    output_file = sample.sample_file.replace(".h5", ".nx")

    # rewrite tomo_n
    with HDF5File(sample.sample_file, mode="a") as h5s:
        for _, entry_node in h5s.items():
            if "technique/scan/tomo_n" in entry_node:
                del entry_node["technique/scan/tomo_n"]
                entry_node["technique/scan/tomo_n"] = 9999

    with pytest.raises(ValueError):
        config.input_file = sample.sample_file
        config.output_file = output_file
        config.single_file = True
        config.no_input = True
        config.raises_error = True
        converter.from_h5_to_nx(configuration=config)


@pytest.mark.parametrize("create_tomo_config", (True, False))
def test_simple_converter_without_nx_detector_attr(tmp_path, create_tomo_config: bool):
    """
    Test a simple conversion when no NX_class is defined
    """
    folder = tmp_path / "output_test_simple_converter_without_nx_detector_attr"
    folder.mkdir()
    config = TomoHDF5Config()
    bliss_mock = MockBlissAcquisition(
        n_sample=1,
        n_sequence=3,
        n_scan_per_sequence=10,
        n_darks=5,
        n_flats=5,
        with_nx_detector_attr=True,
        output_dir=folder,
        detector_name="tata_detector",
        create_tomo_config=create_tomo_config,
    )
    assert len(bliss_mock.samples) == 1
    sample = bliss_mock.samples[0]
    assert os.path.exists(sample.sample_file)
    output_file = sample.sample_file.replace(".h5", ".nx")
    config.input_file = sample.sample_file
    config.output_file = output_file
    config.single_file = True
    config.no_input = True
    converter.from_h5_to_nx(configuration=config)
    # insure only one file is generated
    assert os.path.exists(output_file)
    # insure data is here
    with HDF5File(output_file, mode="r", swmr=get_swmr_mode()) as h5s:
        for _, entry_node in h5s.items():
            assert "instrument/detector/data" in entry_node
            dataset = entry_node["instrument/detector/data"]
        # check virtual dataset are relative and valid
        assert dataset.is_virtual
        for vs in dataset.virtual_sources():
            assert not os.path.isabs(vs.file_name)
        # insure connection is valid. There is no
        # 'VirtualSource.is_valid' like function
        assert not (dataset[()].min() == 0 and dataset[()].max() == 0)
        # check NXdata group
        assert "data/data" in entry_node
        assert not (
            entry_node["data/data"][()].min() == 0
            and entry_node["data/data"][()].max() == 0
        )
        assert "data/rotation_angle" in entry_node
        assert "data/image_key" in entry_node


def test_providing_existing_camera_name(tmp_path):
    """Test that detector can be provided to the h5_to_nx function and
    using linux wildcard"""
    folder = tmp_path / "output_test_providing_existing_camera_name"
    folder.mkdir()
    config = TomoHDF5Config()

    bliss_mock = MockBlissAcquisition(
        n_sample=1,
        n_sequence=3,
        n_scan_per_sequence=10,
        n_darks=5,
        n_flats=5,
        with_nx_detector_attr=True,
        output_dir=folder,
        detector_name="my_detector",
        create_tomo_config=False,
    )
    assert len(bliss_mock.samples) == 1
    sample = bliss_mock.samples[0]
    assert os.path.exists(sample.sample_file)
    config.output_file = sample.sample_file.replace(".h5", ".nx")
    config.valid_camera_names = ("my_detec*",)
    config.input_file = sample.sample_file
    config.single_file = True
    config.no_input = True
    config.raises_error = True
    config.rotation_angle_keys = ("hrsrot",)
    config.sample_x_keys = ("sx",)
    config.sample_y_keys = ("sy",)
    converter.from_h5_to_nx(configuration=config)
    # insure only one file is generated
    assert os.path.exists(config.output_file)
    # insure data is here
    with HDF5File(config.output_file, mode="r", swmr=get_swmr_mode()) as h5s:
        for _, entry_node in h5s.items():
            assert "instrument/detector/data" in entry_node
            dataset = entry_node["instrument/detector/data"]
        # check virtual dataset are relative and valid
        assert dataset.is_virtual
        for vs in dataset.virtual_sources():
            assert not os.path.isabs(vs.file_name)
        # insure connection is valid. There is no
        # 'VirtualSource.is_valid' like function
        assert not (dataset[()].min() == 0 and dataset[()].max() == 0)


def test_providing_non_existing_camera_name_no_tomo_config(tmp_path):
    """Test translation fails if no detector can be found"""
    folder = tmp_path / "output_test_providing_non_existing_camera_name_no_tomo_config"
    folder.mkdir()
    config = TomoHDF5Config()

    bliss_mock = MockBlissAcquisition(
        n_sample=1,
        n_sequence=3,
        n_scan_per_sequence=10,
        n_darks=5,
        n_flats=5,
        with_nx_detector_attr=True,
        output_dir=folder,
        detector_name="toto_detector",
        create_tomo_config=False,
        z_series_v_3_options={
            "dark_at_start": True,
            "flat_at_start": True,
            "dark_at_end": False,
            "flat_at_end": False,
        },
    )
    assert len(bliss_mock.samples) == 1
    sample = bliss_mock.samples[0]
    assert os.path.exists(sample.sample_file)
    config.input_file = sample.sample_file
    config.output_file = sample.sample_file.replace(".h5", ".nx")
    config.valid_camera_names = ("my_detec",)
    config.raises_error = True
    with pytest.raises(ValueError):
        converter.from_h5_to_nx(configuration=config)


@pytest.mark.parametrize("z_series_version", ("z-series-v1", "z-series-v3"))
def test_z_series_conversion_no_tomo_config(tmp_path, z_series_version: str):
    """Test conversion of a zseries bliss (mock) acquisition"""
    folder = tmp_path / "output_test_z_series_conversion_no_tomo_config"
    folder.mkdir()
    config = TomoHDF5Config()

    bliss_mock = MockBlissAcquisition(
        n_sample=1,
        n_sequence=1,
        n_scan_per_sequence=10,
        n_darks=5,
        n_flats=5,
        with_nx_detector_attr=True,
        output_dir=folder,
        detector_name="frelon1",
        acqui_type=z_series_version,
        z_values=(1, 2, 3),
        create_tomo_config=False,
        z_series_v_3_options={
            "dark_at_start": True,
            "flat_at_start": True,
            "dark_at_end": False,
            "flat_at_end": False,
        },
    )
    assert len(bliss_mock.samples) == 1
    sample = bliss_mock.samples[0]
    assert os.path.exists(sample.sample_file)
    config.input_file = sample.sample_file
    config.output_file = sample.sample_file.replace(".h5", ".nx")
    res = converter.from_h5_to_nx(configuration=config)
    # insure the 3 files are generated: one per z
    files = glob(os.path.dirname(sample.sample_file) + "/*.nx")
    assert len(files) == 3
    # try to create NXtomoScan from those to insure this is valid
    # and check z values for example
    for res_tuple in res:
        scan = NXtomoScan(scan=res_tuple[0], entry=res_tuple[1])
        if hasattr(scan, "translation_z"):
            assert scan.translation_z is not None
        assert is_valid_for_reconstruction(scan)


@pytest.mark.parametrize("z_series_version", ("z-series-v1", "z-series-v3"))
def test_z_series_conversion(tmp_path, z_series_version):
    """Test conversion of a zseries bliss (mock) acquisition"""
    folder = tmp_path / "output_test_z_series_conversion"
    folder.mkdir()
    config = TomoHDF5Config()

    bliss_mock = MockBlissAcquisition(
        n_sample=1,
        n_sequence=1,
        n_scan_per_sequence=10,
        n_darks=5,
        n_flats=5,
        with_nx_detector_attr=True,
        output_dir=folder,
        detector_name="frelon1",
        acqui_type=z_series_version,
        z_values=(1, 2, 3),
        create_tomo_config=True,
        ebs_tomo_version="2.1.0",
        z_series_v_3_options={
            "dark_at_start": True,
            "flat_at_start": True,
            "dark_at_end": False,
            "flat_at_end": False,
        },
    )
    assert len(bliss_mock.samples) == 1
    sample = bliss_mock.samples[0]
    assert os.path.exists(sample.sample_file)
    config.input_file = sample.sample_file
    config.output_file = sample.sample_file.replace(".h5", ".nx")
    res = converter.from_h5_to_nx(configuration=config)
    # insure the 3 files are generated: one per z
    files = glob(os.path.dirname(sample.sample_file) + "/*.nx")
    assert len(files) == 3
    # try to create NXtomoScan from those to insure this is valid
    # and check z values for example
    for res_tuple in res:
        scan = NXtomoScan(scan=res_tuple[0], entry=res_tuple[1])
        if hasattr(scan, "translation_z"):
            assert scan.translation_z is not None
        assert is_valid_for_reconstruction(scan)


def test_ignore_sub_entries(tmp_path):
    """
    Test we can ignore some sub entries
    """
    folder = tmp_path / "output_test_ignore_sub_entries"
    folder.mkdir()
    config = TomoHDF5Config()

    from nxtomomill.tests.utils.bliss import MockBlissAcquisition

    bliss_mock = MockBlissAcquisition(
        n_sample=1,
        n_sequence=1,
        n_scan_per_sequence=10,
        n_darks=0,
        n_flats=0,
        with_nx_detector_attr=True,
        output_dir=folder,
        detector_name="pcolinux",
    )
    for sample in bliss_mock.samples:
        assert os.path.exists(sample.sample_file)
        config.output_file = sample.sample_file.replace(".h5", ".nx")
        config.input_file = sample.sample_file
        config.single_file = True
        config.sub_entries_to_ignore = ("6.1", "7.1")
        config.no_input = True
        converter.from_h5_to_nx(configuration=config)
        # insure only one file is generated
        assert os.path.exists(config.output_file)
        # insure data is here
        with HDF5File(config.output_file, mode="r", swmr=get_swmr_mode()) as h5s:
            for _, entry_node in h5s.items():
                assert "instrument/detector/data" in entry_node
                dataset = entry_node["instrument/detector/data"]
            # check virtual dataset are relative and valid
            assert dataset.is_virtual
            assert dataset.shape == (
                10 * (10 - len(config.sub_entries_to_ignore)),
                64,
                64,
            )
            for vs in dataset.virtual_sources():
                assert not os.path.isabs(vs.file_name)
            # insure connection is valid. There is no
            # 'VirtualSource.is_valid' like function
            assert not (dataset[()].min() == 0 and dataset[()].max() == 0)


def create_nx_detector(node: h5py.Group, name, with_nx_class):
    det_node = node.require_group(name)
    data = numpy.random.random(10 * 10 * 10).reshape(10, 10, 10)
    det_node["data"] = data
    if with_nx_class:
        if "NX_class" not in det_node.attrs:
            det_node.attrs["NX_class"] = "NXdetector"
    return


def test_get_nx_detectors(tmp_path):
    """test get_nx_detectors function"""
    folder = tmp_path / "output_test_get_nx_detectors"
    folder.mkdir()

    h5file = os.path.join(folder, "h5file.hdf5")
    with HDF5File(h5file, mode="w") as h5s:
        create_nx_detector(node=h5s, name="det1", with_nx_class=True)
        create_nx_detector(node=h5s, name="det2", with_nx_class=False)
    with HDF5File(h5file, mode="r", swmr=get_swmr_mode()) as h5s:
        dets = get_nx_detectors(h5s)
        assert len(dets) == 1
        assert dets[0].name == "/det1"
        assert len(guess_nx_detector(h5s)) == 2
    with HDF5File(h5file, mode="a") as h5s:
        create_nx_detector(node=h5s, name="det3", with_nx_class=True)
        create_nx_detector(node=h5s, name="det4", with_nx_class=True)
    with HDF5File(h5file, mode="r", swmr=get_swmr_mode()) as h5s:
        dets = get_nx_detectors(h5s)
        assert len(dets) == 3


def test_guess_nx_detector(tmp_path):
    """test guess_nx_detector function"""
    folder = tmp_path / "output_test_guess_nx_detector"
    folder.mkdir()

    h5file = os.path.join(folder, "h5file.hdf5")

    with HDF5File(h5file, mode="w") as h5s:
        create_nx_detector(node=h5s, name="det2", with_nx_class=False)
    with HDF5File(h5file, mode="r", swmr=get_swmr_mode()) as h5s:
        dets = get_nx_detectors(h5s)
        assert len(dets) == 0
        dets = guess_nx_detector(h5s)
        assert dets[0].name == "/det2"
    with HDF5File(h5file, mode="w") as h5s:
        create_nx_detector(node=h5s, name="det3", with_nx_class=False)
        create_nx_detector(node=h5s, name="det4", with_nx_class=True)
    with HDF5File(h5file, mode="a") as h5s:
        dets = guess_nx_detector(h5s)
        assert len(dets) == 2


def create_scan(n_projection_scans, n_flats, n_darks, output_dir, frame_data_type):
    """
    :param int n_projection_scans: number of scans beeing projections
    :param int n_flats: number of frame per flats
    :param int n_darks: number of frame per dark
    """
    bliss_mock = MockBlissAcquisition(
        n_sample=1,
        n_sequence=1,
        n_scan_per_sequence=n_projection_scans,
        n_darks=n_darks,
        n_flats=n_flats,
        with_nx_detector_attr=True,
        output_dir=output_dir,
        detector_name="pcolinux",
        frame_data_type=frame_data_type,
    )
    return bliss_mock.samples[0].sample_file


def test_dataset_1(tmp_path):
    """test a conversion where projections are contained in the
    input_file. Dark and flats are on a different file"""

    frame_data_type = numpy.uint16
    folder = tmp_path / "output_test_dataset_1"
    folder.mkdir()
    config = TomoHDF5Config()
    config.no_master_file = False
    config.output_file = os.path.join(folder, "output.nx")
    config.rotation_angle_keys = ("hrsrot",)
    config.sample_x_keys = ("sx",)
    config.sample_y_keys = ("sy",)

    folder_1 = os.path.join(folder, "acqui_1")
    input_file = create_scan(
        n_projection_scans=6,
        n_flats=0,
        n_darks=0,
        output_dir=folder_1,
        frame_data_type=frame_data_type,
    )
    folder_2 = os.path.join(folder, "acqui_2")
    dark_flat_file = create_scan(
        n_projection_scans=0,
        n_flats=1,
        n_darks=1,
        output_dir=folder_2,
        frame_data_type=frame_data_type,
    )
    config.input_file = input_file

    # we want to take two scan of projections from the input file: 5.1
    # and 6.1. As the input file is provided we don't need to
    # specify it
    config.data_scans = (
        FrameGroup(frame_type="proj", url=DataUrl(data_path="/5.1", scheme="silx")),
        FrameGroup(frame_type="proj", url=DataUrl(data_path="/6.1", scheme="silx")),
        FrameGroup(
            frame_type="flat",
            url=DataUrl(file_path=dark_flat_file, data_path="/2.1", scheme="silx"),
        ),
        FrameGroup(
            frame_type="dark",
            url=DataUrl(file_path=dark_flat_file, data_path="/3.1", scheme="silx"),
        ),
    )
    converter.from_h5_to_nx(
        configuration=config,
    )

    assert os.path.exists(config.output_file), "output file does not exists"

    with HDF5File(config.output_file, mode="r", swmr=get_swmr_mode()) as h5s:
        assert len(h5s.items()) == 1
        assert "entry0000" in h5s

    scan = NXtomoScan(scan=config.output_file, entry="entry0000")
    assert is_valid_for_reconstruction(scan)

    # check the `data`has been created
    assert len(scan.projections) == 20
    assert len(scan.darks) == 10
    # check data is a virtual dataset
    with HDF5File(config.output_file, mode="r", swmr=get_swmr_mode()) as h5f:
        dataset = h5f["entry0000/instrument/detector/data"]
        assert dataset.is_virtual
        assert dataset.dtype == frame_data_type
    # check the `data` virtual dataset is valid
    # if the link fail then all values are zeros
    url = tuple(scan.projections.values())[0]
    proj_data = get_data(url)
    assert proj_data.min() != proj_data.max()

    url = tuple(scan.darks.values())[0]
    dark_data = get_data(url)
    assert dark_data.min() != dark_data.max()

    assert len(scan.flats) == 10
    url = tuple(scan.flats.values())[0]
    flat_data = get_data(url)
    assert flat_data.min() != flat_data.max()


def test_dataset_2(tmp_path):
    """test a conversion where no input file is provided and
    where we have 2 projections in a file, 3 in an other.
    Flat and darks are also in another file. No flat provided.
    """
    folder = tmp_path / "output_test_dataset_2"
    folder.mkdir()
    frame_data_type = numpy.uint16
    config = TomoHDF5Config()
    config.no_master_file = False
    config.output_file = os.path.join(folder, "output.nx")
    config.rotation_angle_keys = ("hrsrot",)
    config.sample_x_keys = ("sx",)
    config.sample_y_keys = ("sy",)

    folder_1 = os.path.join(folder, "acqui_1")
    file_1 = create_scan(
        n_projection_scans=6,
        n_flats=0,
        n_darks=0,
        output_dir=folder_1,
        frame_data_type=frame_data_type,
    )
    folder_2 = os.path.join(folder, "acqui_2")
    file_2 = create_scan(
        n_projection_scans=6,
        n_flats=0,
        n_darks=0,
        output_dir=folder_2,
        frame_data_type=frame_data_type,
    )
    folder_3 = os.path.join(folder, "acqui_3")
    file_3 = create_scan(
        n_projection_scans=0,
        n_flats=0,
        n_darks=1,
        output_dir=folder_3,
        frame_data_type=frame_data_type,
    )
    folder_4 = os.path.join(folder, "acqui_4")
    file_4 = create_scan(
        n_projection_scans=0,
        n_flats=1,
        n_darks=0,
        output_dir=folder_4,
        frame_data_type=frame_data_type,
    )

    # we want to take two scan of projections from the input file: 5.1
    # and 6.1. As the input file is provided we don't need to
    # specify it
    dark_url_1 = DataUrl(file_path=file_3, data_path="/2.1", scheme="silx")
    flat_url_1 = DataUrl(file_path=file_4, data_path="/2.1", scheme="silx")
    proj_url_1 = DataUrl(file_path=file_1, data_path="/5.1", scheme="silx")
    proj_url_2 = DataUrl(file_path=file_1, data_path="/6.1", scheme="silx")
    proj_url_3 = DataUrl(file_path=file_2, data_path="/4.1", scheme="silx")
    proj_url_4 = DataUrl(file_path=file_2, data_path="/2.1", scheme="silx")

    config.default_data_copy = True
    config.data_scans = (
        FrameGroup(frame_type="dark", url=dark_url_1),
        FrameGroup(frame_type="flat", url=flat_url_1),
        FrameGroup(frame_type="proj", url=proj_url_1, copy_data=False),
        FrameGroup(frame_type="proj", url=proj_url_2, copy_data=False),
        FrameGroup(frame_type="proj", url=proj_url_3),
        FrameGroup(frame_type="proj", url=proj_url_4),
    )

    urls_copied = (dark_url_1, flat_url_1, proj_url_3, proj_url_4)
    urls_not_copied = (proj_url_1, proj_url_2)

    config.raises_error = True
    converter.from_h5_to_nx(
        configuration=config,
    )

    assert os.path.exists(config.output_file)

    with HDF5File(config.output_file, mode="r", swmr=get_swmr_mode()) as h5s:
        assert "entry0000" in h5s
        assert len(h5s.items()) == 1

    with HDF5File(
        config.output_file.replace(".nx", "_0000.nx"),
        mode="r",
        swmr=get_swmr_mode(),
    ) as h5s:
        assert "entry0000" in h5s
        assert "duplicate_data" in h5s
        assert len(h5s.items()) == 2

    detector_url = DataUrl(
        file_path=config.output_file,
        data_path="/entry0000/instrument/detector/data",
        scheme="silx",
    )
    with DatasetReader(detector_url) as detector_dataset:
        assert detector_dataset.is_virtual
        for i_vs, vs in enumerate(detector_dataset.virtual_sources()):
            assert not os.path.isabs(vs.file_name)
            if i_vs in (0, 1, 4, 5):
                assert vs.file_name == "."
            else:
                assert vs.file_name == "./acqui_1/sample_0/sample_0.h5"
    # FIXME: avoid keeping some file open. not clear why this is needed
    detector_dataset = None

    scan = NXtomoScan(scan=config.output_file, entry="entry0000")
    assert is_valid_for_reconstruction(scan)

    # check the `data`has been created
    assert len(scan.projections) == 40
    assert len(scan.darks) == 10

    # check the `data` virtual dataset is valid
    # if the link fail then all values are zeros
    url = tuple(scan.projections.values())[0]
    proj_data = get_data(url)
    assert proj_data.min() != proj_data.max()

    url = tuple(scan.darks.values())[0]
    dark_data = get_data(url)
    assert dark_data.min() != dark_data.max()

    assert len(scan.flats) == 10
    url = tuple(scan.flats.values())[0]
    flat_data = get_data(url)
    assert flat_data.min() != flat_data.max()

    with HDF5File(config.output_file, mode="r", swmr=get_swmr_mode()) as h5f:
        dataset = h5f["entry0000/instrument/detector/data"][()]
        assert dataset.shape[0] == 60
    with EntryReader(dark_url_1) as dark_entry:
        numpy.testing.assert_array_equal(
            dark_entry["instrument/pcolinux/data"], dataset[0:10]
        )
    with EntryReader(flat_url_1) as flat_entry:
        numpy.testing.assert_array_equal(
            flat_entry["instrument/pcolinux/data"], dataset[10:20]
        )
    with EntryReader(proj_url_1) as proj_entry_1:
        numpy.testing.assert_array_equal(
            proj_entry_1["instrument/pcolinux/data"], dataset[20:30]
        )
    with EntryReader(proj_url_2) as proj_entry_2:
        numpy.testing.assert_array_equal(
            proj_entry_2["instrument/pcolinux/data"], dataset[30:40]
        )
    with EntryReader(proj_url_3) as proj_entry_3:
        numpy.testing.assert_array_equal(
            proj_entry_3["instrument/pcolinux/data"], dataset[40:50]
        )
    with EntryReader(proj_url_4) as proj_entry_4:
        numpy.testing.assert_array_equal(
            proj_entry_4["instrument/pcolinux/data"], dataset[50:60]
        )

    for url in urls_copied:
        assert url_has_been_copied(
            file_path=config.output_file.replace(".nx", "_0000.nx"),
            url=url,
        )

    for url in urls_not_copied:
        assert not url_has_been_copied(
            file_path=config.output_file.replace(".nx", "_0000.nx"),
            url=url,
        )

    # test with some extra parameters
    config.energy_kev = 12.2
    config.x_sample_pixel_size_m = 2.6 * 10e-6
    config.y_sample_pixel_size_m = 2.7 * 10e-6

    config.overwrite = True
    config.field_of_view = "Half"

    init_url_1 = DataUrl(file_path=file_1, data_path="/1.1", scheme="silx")

    config.default_data_copy = True
    config.data_scans = (
        FrameGroup(frame_type="init", url=init_url_1),
        FrameGroup(frame_type="dark", url=dark_url_1),
        FrameGroup(frame_type="flat", url=flat_url_1),
        FrameGroup(frame_type="proj", url=proj_url_1, copy=False),
        FrameGroup(frame_type="proj", url=proj_url_2, copy=False),
        FrameGroup(frame_type="proj", url=proj_url_3),
        FrameGroup(frame_type="proj", url=proj_url_4),
    )

    converter.from_h5_to_nx(
        configuration=config,
    )
    scan.clear_cache()
    energy = scan.energy
    assert numpy.isclose(energy, 12.2)
    assert scan.sample_x_pixel_size is not None
    assert numpy.isclose(scan.sample_x_pixel_size, 2.6 * 10e-6)
    assert scan.sample_y_pixel_size is not None
    assert numpy.isclose(scan.sample_y_pixel_size, 2.7 * 10e-6)
    with EntryReader(
        DataUrl(file_path=scan.master_file, data_path=scan.entry, scheme="h5py")
    ) as entry:
        assert "instrument/detector" in entry
        assert "instrument/diode" not in entry


@pytest.mark.parametrize("z_series_version", ("z-series-v1",))
def test_z_series_conversion_with_external_urls(tmp_path, z_series_version: str):
    """
    test conversion of a z-series using configuration
    """

    folder = tmp_path / "test_z_series_conversion_with_external_urls"
    folder = tempfile.mkdtemp()
    frame_data_type = numpy.uint64

    config = TomoHDF5Config()
    config.output_file = os.path.join(folder, "output.nx")

    # dataset init
    camera_name = "frelon"
    bliss_mock = MockBlissAcquisition(
        n_sample=1,
        n_sequence=1,
        n_scan_per_sequence=2,
        n_darks=1,
        n_flats=0,
        with_nx_detector_attr=True,
        output_dir=os.path.join(folder, "seq_1"),
        detector_name=camera_name,
        acqui_type=z_series_version,
        z_values=(1, 2, 3),
        frame_data_type=frame_data_type,
    )
    zseries_1_file = bliss_mock.samples[0].sample_file

    bliss_mock = MockBlissAcquisition(
        n_sample=1,
        n_sequence=1,
        n_scan_per_sequence=2,
        n_darks=0,
        n_flats=1,
        with_nx_detector_attr=True,
        output_dir=os.path.join(folder, "seq_2"),
        detector_name=camera_name,
        acqui_type=z_series_version,
        z_values=(4, 5, 6),
        frame_data_type=frame_data_type,
    )
    zseries_2_file = bliss_mock.samples[0].sample_file

    dark_url_1 = DataUrl(file_path=zseries_1_file, data_path="/5.1", scheme="silx")
    proj_url_1 = DataUrl(file_path=zseries_1_file, data_path="/6.1", scheme="silx")
    proj_url_2 = DataUrl(file_path=zseries_1_file, data_path="/7.1", scheme="silx")
    proj_url_3 = DataUrl(file_path=zseries_1_file, data_path="/9.1", scheme="silx")
    proj_url_4 = DataUrl(file_path=zseries_1_file, data_path="/10.1", scheme="silx")
    proj_url_5 = DataUrl(file_path=zseries_2_file, data_path="/3.1", scheme="silx")
    proj_url_6 = DataUrl(file_path=zseries_2_file, data_path="/4.1", scheme="silx")
    flat_url_1 = DataUrl(file_path=zseries_2_file, data_path="/2.1", scheme="silx")
    config.default_data_copy = True
    config.single_file = True
    config.data_scans = (
        FrameGroup(frame_type="dark", url=dark_url_1, copy_data=False),
        FrameGroup(frame_type="flat", url=flat_url_1, copy_data=False),
        FrameGroup(frame_type="proj", url=proj_url_1),
        FrameGroup(frame_type="proj", url=proj_url_2),
        FrameGroup(frame_type="proj", url=proj_url_3),
        FrameGroup(frame_type="proj", url=proj_url_4),
        FrameGroup(frame_type="proj", url=proj_url_5),
        FrameGroup(frame_type="proj", url=proj_url_6),
    )
    urls_copied = (
        proj_url_1,
        proj_url_2,
        proj_url_3,
        proj_url_4,
        proj_url_5,
        proj_url_6,
    )
    urls_not_copied = (flat_url_1, dark_url_1)
    # do conversion
    new_scans = converter.from_h5_to_nx(
        configuration=config,
    )
    assert len(new_scans) == 3
    assert os.path.exists(config.output_file)
    with HDF5File(config.output_file, mode="r", swmr=get_swmr_mode()) as h5f:
        assert "entry0000" in h5f
        assert "entry0001" in h5f
        assert "entry0002" in h5f

    scan_z0 = NXtomoScan(scan=config.output_file, entry="entry0000")
    scan_z1 = NXtomoScan(scan=config.output_file, entry="entry0001")
    scan_z2 = NXtomoScan(scan=config.output_file, entry="entry0002")

    # check the `data`has been created
    assert len(scan_z0.projections) == 20
    assert len(scan_z1.projections) == 20
    assert len(scan_z2.projections) == 20

    for url in urls_copied:
        assert url_has_been_copied(file_path=config.output_file, url=url)

    for url in urls_not_copied:
        assert not url_has_been_copied(file_path=config.output_file, url=url)

    # test a few slices
    with HDF5File(config.output_file, mode="r", swmr=get_swmr_mode()) as h5f:
        dataset = h5f["entry0000/instrument/detector/data"]
        assert dataset.shape[0] == 30

        with EntryReader(proj_url_1) as proj_entry_1:
            numpy.testing.assert_array_equal(
                proj_entry_1["instrument/frelon/data"], dataset[10:20]
            )
        with EntryReader(proj_url_2) as proj_entry_2:
            numpy.testing.assert_array_equal(
                proj_entry_2["instrument/frelon/data"], dataset[20:30]
            )
        assert dataset.dtype == frame_data_type


@pytest.mark.parametrize("z_series_version", ("z-series-v1", "z-series-v3"))
@pytest.mark.parametrize(
    "dark_flat_config",
    (
        {
            "dark_at_start": True,
            "flat_at_start": True,
            "dark_at_end": False,
            "flat_at_end": False,
        },
        {
            "dark_at_start": False,
            "flat_at_start": False,
            "dark_at_end": True,
            "flat_at_end": True,
        },
    ),
)
def test_z_series_dark_flat_copy(tmp_path, z_series_version: str, dark_flat_config):
    """In z-series version 3"""

    folder = tmp_path / "h52nx_from_command_line"
    folder.mkdir()

    bliss_mock = MockBlissAcquisition(
        n_sample=1,
        n_sequence=1,
        n_scan_per_sequence=2,
        n_darks=1,
        n_flats=1,
        acqui_type=z_series_version,
        with_nx_detector_attr=True,
        output_dir=folder,
        detector_name="pcolinux",
        frame_data_type=numpy.uint32,
        z_values=(0.0, 1.0, 2.0),
        z_series_v_3_options=dark_flat_config,
    )

    # launch conversion
    sample = bliss_mock.samples[0]
    input_file = sample.sample_file
    assert os.path.exists(input_file)

    config = TomoHDF5Config()
    config.output_file = get_default_output_file(sample.sample_file)
    config.valid_camera_names = ("pcolinux",)
    config.input_file = sample.sample_file
    config.single_file = True
    config.no_input = True
    config.raises_error = True
    config.rotation_angle_keys = ("hrsrot",)

    new_entries = converter.from_h5_to_nx(configuration=config)
    # insure only one file is generated
    assert os.path.exists(config.output_file)
    # insure data is here
    for i_nx_tomo, (file_path, data_path) in enumerate(new_entries):
        nx_tomo = NXtomo().load(file_path=file_path, data_path=data_path)
        assert (
            len(
                numpy.where(
                    nx_tomo.instrument.detector.image_key_control == ImageKey.DARK_FIELD
                )[0]
            )
            == 10
        ), f"NXtomo {i_nx_tomo} doesn't have the expected number of dark"
        assert (
            len(
                numpy.where(
                    nx_tomo.instrument.detector.image_key_control == ImageKey.FLAT_FIELD
                )[0]
            )
            == 10
        ), f"NXtomo {i_nx_tomo} doesn't have the expected number of flat"
        assert (
            len(
                numpy.where(
                    nx_tomo.instrument.detector.image_key_control == ImageKey.PROJECTION
                )[0]
            )
            == 20
        ), f"NXtomo {i_nx_tomo} doesn't have the expected number of projection"


def test_h52nx_from_command_line(tmp_path):

    folder = tmp_path / "h52nx_from_command_line"
    folder.mkdir()

    bliss_mock = MockBlissAcquisition(
        n_sample=1,
        n_sequence=1,
        n_scan_per_sequence=2,
        n_darks=1,
        n_flats=1,
        with_nx_detector_attr=True,
        output_dir=folder,
        detector_name="pcolinux",
        frame_data_type=numpy.uint32,
    )
    sample = bliss_mock.samples[0]
    output_file = sample.sample_file.replace(".h5", ".nx")
    assert os.path.exists(sample.sample_file)

    with cwd_context(os.path.dirname(sample.sample_file)):

        input_file = os.path.basename(sample.sample_file)
        assert os.path.exists(input_file)
        output_file = os.path.basename(output_file)
        assert not os.path.exists(output_file)
        cmd = (
            sys.executable,
            "-m",
            "nxtomomill",
            "h52nx",
            input_file,
            output_file,
            "--copy-data",
            "--raises-error",
            "--single-file",
        )
        subprocess.call(cmd, cwd=os.path.dirname(sample.sample_file))  # nosec B603

        assert os.path.exists(output_file)

        # insure all link are connected to one file: the internal one
        frame_dataset_url = DataUrl(
            file_path=output_file,
            data_path="/entry0000/instrument/detector/data",
            scheme="silx",
        )
        with DatasetReader(frame_dataset_url) as dataset:
            assert dataset.is_virtual

            for vs_info in dataset.virtual_sources():
                assert dataset.is_virtual
                assert vs_info.file_name == "."
                assert dataset.dtype == numpy.uint32
        # FIXME: avoid keeping some file open. not clear why this is needed
        dataset = None
        with HDF5File(output_file, "r", swmr=get_swmr_mode()) as h5f:
            assert "/entry0000/instrument/diode" not in h5f

        # insure an nxtomo can be created from it
        nx_tomo = NXtomo().load(output_file, "entry0000")
        assert nx_tomo.energy is not None
        z1 = -52.0 * _ureg.meter
        z2 = 0.1 * _ureg.meter
        assert nx_tomo.instrument.detector.distance == z2
        assert nx_tomo.instrument.source.distance == z1
        propa_dist_read = nx_tomo.sample.propagation_distance.to_base_units().magnitude
        propa_dist_expected = ((-z1 * z2) / (-z1 + z2)).to_base_units().magnitude
        assert numpy.isclose(
            propa_dist_read,
            propa_dist_expected,
        )
        numpy.testing.assert_array_equal(
            nx_tomo.instrument.detector.sequence_number,
            numpy.linspace(0, 40, 40, endpoint=False, dtype=numpy.uint32),
        )


input_types = (
    numpy.uint8,
    numpy.uint16,
    numpy.uint32,
    numpy.uint64,
    numpy.float16,
    numpy.float32,
    numpy.int16,
    numpy.int32,
    numpy.int64,
)


@pytest.mark.parametrize("rotation_is_clockwise", (True, False))
@pytest.mark.parametrize("input_type", input_types)
def test_simple_conversion(input_type, tmp_path, rotation_is_clockwise: bool):
    """test simple conversion from different frame data type and handling of RAW_DATA with PROCESSED_DATA"""

    input_path = tmp_path / "test" / RAW_DATA_DIR_NAME / "dataset"
    os.makedirs(input_path)

    bliss_mock = MockBlissAcquisition(
        n_sample=1,
        n_sequence=1,
        n_scan_per_sequence=10,
        n_darks=5,
        n_flats=5,
        with_nx_detector_attr=True,
        output_dir=input_path,
        detector_name="my_detector",
        frame_data_type=input_type,
        rotation_is_clockwise=rotation_is_clockwise,
        create_tomo_config=True,
    )
    sample = bliss_mock.samples[0]
    assert os.path.exists(sample.sample_file)

    config = TomoHDF5Config()
    config.output_file = get_default_output_file(sample.sample_file)
    assert PROCESSED_DATA_DIR_NAME in config.output_file
    config.valid_camera_names = ("my_detec*",)
    config.input_file = sample.sample_file
    config.single_file = True
    config.no_input = True
    config.raises_error = True
    config.rotation_angle_keys = ("hrsrot",)

    converter.from_h5_to_nx(configuration=config)
    # insure only one file is generated
    assert os.path.exists(config.output_file)
    # insure data is here
    with HDF5File(config.output_file, mode="r", swmr=get_swmr_mode()) as h5s:
        for _, entry_node in h5s.items():
            assert "instrument/detector/data" in entry_node
            dataset = entry_node["instrument/detector/data"]
            assert dataset.dtype == input_type
            assert "control" not in entry_node
            if rotation_is_clockwise:
                assert numpy.all(
                    entry_node["data/rotation_angle"][()] <= 0.0
                ), "tomoconfig 'rotation_is_clockwise' doesn't seems to be properly read"
            else:
                assert numpy.all(
                    entry_node["data/rotation_angle"][()] >= 0.0
                ), "tomoconfig 'rotation_is_clockwise' doesn't seems to be properly read"


def test_machine_current():
    """Test machine current is handle by the convertor"""
    with tempfile.TemporaryDirectory() as root_dir:
        bliss_mock = MockBlissAcquisition(
            n_sample=1,
            n_sequence=1,
            n_scan_per_sequence=2,
            n_darks=5,
            n_flats=5,
            with_nx_detector_attr=True,
            output_dir=root_dir,
            detector_name="my_detector",
        )
        sample = bliss_mock.samples[0]
        assert os.path.exists(sample.sample_file)
        # append current to the bliss file
        # from the example file I had it looks like this information can be saved at different location
        # and can be either a number (for dark and flat for example) or a list (for projections)
        with HDF5File(sample.sample_file, mode="a") as h5f:
            # overwrite start_time to made ordering work
            del h5f["1.1"]["start_time"]
            h5f["1.1"]["start_time"] = "2022-01-15T21:05:58.360095+02:00"

        with HDF5File(sample.sample_file, mode="a") as h5f:
            node_names = ("2.1", "3.1")
            machine_current = (602, 589)  # those are in ma
            start_times = (
                "2022-01-15T21:07:58.360095+02:00",
                "2022-01-15T21:07:59.360095+02:00",
            )
            for node_name, machine_current_ma, st in zip(
                node_names, machine_current, start_times
            ):
                h5f[f"{node_name}/instrument/machine/current"] = machine_current_ma
                h5f[f"{node_name}/instrument/machine/current"].attrs["units"] = str(
                    _ureg.milliampere
                )
                del h5f[node_name]["start_time"]
                h5f[node_name]["start_time"] = st

            assert "4.1" in h5f
            assert "5.1" in h5f
            assert (
                "6.1" not in h5f
            )  # this is because n_scan_per_sequence == 2 in MockBlissAcquisition

            # create some X.2 for machine current as this is done in Bliss
            for node_name in ("4.2", "5.2"):
                h5f.require_group(node_name)["title"] = _BlissSample.get_title(
                    "projection"
                )

                current_monitor_dataset = h5f.require_dataset(
                    f"{node_name}/measurement/current", shape=(5), dtype=numpy.float32
                )
                current_monitor_dataset[:] = numpy.linspace(
                    0.9, 0.96, 5, dtype=numpy.float32, endpoint=True
                )
                # add a nan to make sure this is properly handled
                current_monitor_dataset[1] = numpy.nan
                current_monitor_dataset.attrs["units"] = str(_ureg.ampere)

            # define start_time and end_time to insure conversion is correct
            # start_time and end_time is required for both:
            #    * from X.1 to create frame time stamp
            #    * from X.2 to get machine current time stamp
            start_times = (
                "2022-01-15T21:08:58.360095+02:00",
                "2022-01-15T21:10:58.360095+02:00",
            )
            end_times = (
                "2022-01-15T21:09:58.360095+02:00",
                "2022-01-15T21:11:58.360095+02:00",
            )
            tuple_node_names = (["4.1", "4.2"], ["5.1", "5.2"])

            for node_names, st, et in zip(tuple_node_names, start_times, end_times):
                for node_name in node_names:
                    if "start_time" in h5f[node_name]:
                        del h5f[node_name]["start_time"]
                    h5f[node_name]["start_time"] = st
                    h5f[node_name]["end_time"] = et
                    h5f[node_name].require_group("instrument")

        # convert the file
        config = TomoHDF5Config()
        config.output_file = sample.sample_file.replace(".h5", ".nx")
        config.single_file = True
        config.no_input = True
        config.raises_error = True
        with pytest.raises(ValueError):
            converter.from_h5_to_nx(configuration=config)
        config.input_file = sample.sample_file
        converter.from_h5_to_nx(configuration=config)
        # insure only one file is generated
        assert os.path.exists(config.output_file)
        # insure data is here
        nx_tomo = NXtomo().load(config.output_file, "entry0000")
        expected_results = numpy.concatenate(
            [
                [602 / 1000] * 10,
                [589 / 1000] * 10,
                numpy.linspace(0.9, 0.96, 10, dtype=numpy.float32),
                numpy.linspace(0.9, 0.96, 10, dtype=numpy.float32),
            ]
        )
        n_frames = (
            10 * 4
        )  # there is 10 frames per scan. One dark, one flat and two projections scans
        assert len(nx_tomo.control.data) == n_frames
        numpy.testing.assert_allclose(
            nx_tomo.control.data, expected_results, rtol=0.001
        )

        # test also from tomoscan
        scan = NXtomoScan(scan=config.output_file, entry="entry0000")
        # check getting the projections machine current
        assert (
            len(
                scan.machine_current[
                    scan.image_key_control == ImageKey.PROJECTION.value
                ]
            )
            == 20
        )
        assert (
            len(
                scan.machine_current[
                    scan.image_key_control == ImageKey.DARK_FIELD.value
                ]
            )
            == 10
        )
        assert (
            len(
                scan.machine_current[
                    scan.image_key_control == ImageKey.FLAT_FIELD.value
                ]
            )
            == 10
        )


files_to_expected_result: dict[str, tuple[str]] = {
    "h5_datasets/multitomo/id19/20250713/034_oak_1__0001.h5": (
        [f"034_oak_1__0001_{str(i).zfill(4)}.nx" for i in range(140)]
    ),
    "h5_datasets/holotomo/id16b/20250711/B3P7_sponge_pco2_ht_25nm.h5": (
        "B3P7_sponge_pco2_ht_25nm_0000.nx",
        "B3P7_sponge_pco2_ht_25nm_0001.nx",
        "B3P7_sponge_pco2_ht_25nm_0002.nx",
        "B3P7_sponge_pco2_ht_25nm_0003.nx",
    ),
    "h5_datasets/holotomo/id16b/20250325/needle_test_alu_17p4_daiquiri_50nm_ht_0004.h5": (
        "needle_test_alu_17p4_daiquiri_50nm_ht_0004_0000.nx",
        "needle_test_alu_17p4_daiquiri_50nm_ht_0004_0001.nx",
        "needle_test_alu_17p4_daiquiri_50nm_ht_0004_0002.nx",
        "needle_test_alu_17p4_daiquiri_50nm_ht_0004_0003.nx",
    ),
}


@pytest.mark.parametrize(
    "input_file,expected_result_file_names", files_to_expected_result.items()
)
def test_output_file_indexing(
    input_file: str, expected_result_file_names: tuple[tuple[str, str]], tmp_path
):
    """test nxtomo indexing policy"""
    scan_dir = GitlabDataset.get_dataset(os.path.dirname(input_file))
    bliss_file = os.path.join(scan_dir, os.path.basename(input_file))

    output_file = (
        tmp_path / "output" / os.path.basename(input_file).replace(".h5", ".nx")
    )
    config = TomoHDF5Config()
    config.input_file = bliss_file
    config.output_file = str(output_file)

    converter.from_h5_to_nx(
        configuration=config,
    )
    assert tuple(sorted(os.listdir(tmp_path / "output"))) == tuple(
        sorted(expected_result_file_names)
    )


def test_id16a_use_case(tmp_path):
    """
    Dummy test to match the ID16a use case: providing the input and output file.
    Check that the rotation_is_clockwise works. Check the sample and detector pixel size.
    """
    output_file = tmp_path / "output.nx"
    config = H52nxModel()
    config.single_file = True
    # add noise to the input and output file to make sure they are overwritten
    config.input_file = "toto"
    config.output_file = "tata"

    input_file = GitlabDataset.get_dataset(
        "h5_datasets/holotomo/id16a/Atomium_S2_holo4_HT_010nm_0001.h5"
    )

    config_file = tmp_path / "config.cfg"
    config.to_cfg_file(file_path=str(config_file))

    cmd = (
        sys.executable,
        "-m",
        "nxtomomill",
        "h52nx",
        input_file,
        output_file,
        "--config",
        config_file,
    )
    subprocess.call(cmd, cwd=tmp_path)  # nosec B603

    assert os.path.exists(output_file)

    # check 4 NXtomo exists
    nxtomos = [
        NXtomo().load(
            file_path=output_file,
            data_path=f"entry000{i}",
        )
        for i in range(4)
    ]
    assert len(nxtomos) == 4

    nxtomo_d0 = nxtomos[0]
    assert len(nxtomo_d0.sample.rotation_angle) == 2064

    # check rotation_is_clockwise
    raw_rot_angles = numpy.concatenate(
        [
            [0.0] * 20,  # dark
            [0.0] * 20,  # flat
            numpy.linspace(0.0, 180.0, 2001, endpoint=True),  # proj
            [180.0, 90.0, 0.0],  # alignment proj
            [0.0] * 20,  # flat
        ]
    )

    numpy.testing.assert_almost_equal(
        nxtomo_d0.sample.rotation_angle.to("degree").magnitude,
        raw_rot_angles,
        decimal=2,
    )

    # check detector pixel size
    numpy.testing.assert_almost_equal(
        nxtomo_d0.instrument.detector.x_pixel_size.to(_ureg.micrometer).magnitude,
        2.95203,
        decimal=4,
    )
    numpy.testing.assert_almost_equal(
        nxtomo_d0.instrument.detector.y_pixel_size.to(_ureg.micrometer).magnitude,
        2.95203,
        decimal=4,
    )

    # check sample pixel size
    numpy.testing.assert_almost_equal(
        nxtomo_d0.sample.x_pixel_size.to(_ureg.micrometer).magnitude,
        0.00999999,
        decimal=4,
    )
    numpy.testing.assert_almost_equal(
        nxtomo_d0.sample.y_pixel_size.to(_ureg.micrometer).magnitude,
        0.00999999,
        decimal=4,
    )

    # check detector flips
    transformations = {
        t.axis_name: t
        for t in nxtomo_d0.instrument.detector.transformations.transformations
    }
    for transformation_name in ("rx", "ry"):
        transformation = transformations[transformation_name]
        transformation.transformation_values.magnitude == numpy.array([0.0])
