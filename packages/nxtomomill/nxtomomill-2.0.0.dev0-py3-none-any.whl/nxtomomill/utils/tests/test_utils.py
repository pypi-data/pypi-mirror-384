# coding: utf-8

from __future__ import annotations

import os
import shutil
import tempfile
import unittest

import h5py
import numpy.random

from silx.io.url import DataUrl
from silx.io.utils import h5py_read_dataset

from tomoscan.io import HDF5File, get_swmr_mode
from tomoscan.esrf.mock import MockNXtomo as MockNXtomo
from tomoscan.esrf.scan.nxtomoscan import NXtomoScan

from nxtomo.nxobject.nxdetector import ImageKey

from nxtomomill.utils import add_dark_flat_nx_file, change_image_key_control


class MockNXtomoWithElecCurrent(MockNXtomo):
    def __init__(
        self,
        scan_path,
        ini_dark: numpy.array | None,
        ini_flats: numpy.array | None,
        final_flats: numpy.array | None,
        dim: int,
        n_proj: int,
        count_time: numpy.array | None = None,
        machine_current: numpy.array | None = None,
    ):
        assert ini_dark is None or ini_dark.ndim == 3, "ini_dark should be a 3d array"
        assert ini_flats is None or ini_flats.ndim == 3, "ini_dark should be a 3d array"
        assert (
            final_flats is None or final_flats.ndim == 3
        ), "ini_dark should be a 3d array"
        self._ini_darks = ini_dark
        self._ini_flats = ini_flats
        self._final_flats = final_flats
        self._count_time = count_time
        super().__init__(
            scan_path=scan_path,
            dim=dim,
            create_ini_dark=ini_dark is not None,
            create_ini_flat=ini_flats is not None,
            create_final_flat=final_flats is not None,
            n_ini_proj=n_proj,
            n_proj=n_proj,
        )

        # append count_time and machine_current to the HDF5 file
        with HDF5File(self.scan_master_file, "a") as h5_file:
            entry_one = h5_file.require_group(self.scan_entry)
            if machine_current is not None:
                monitor_grp = entry_one.require_group("control")
                monitor_grp["data"] = machine_current
            # rewrite count_time
            if count_time is not None:
                instrument_grp = entry_one.require_group("instrument")
                detector_grp = instrument_grp.require_group("detector")
                if "count_time" in detector_grp:
                    del detector_grp["count_time"]
                detector_grp["count_time"] = count_time

    def add_initial_dark(self):
        for frame in self._ini_darks:
            self._append_frame(
                data_=frame.reshape(1, frame.shape[0], frame.shape[1]),
                rotation_angle=self.rotation_angle[-1],
                image_key=ImageKey.DARK_FIELD.value,
                image_key_control=ImageKey.DARK_FIELD.value,
                diode_data=None,
            )

    def add_initial_flat(self):
        for frame in self._ini_flats:
            self._append_frame(
                data_=frame.reshape(1, frame.shape[0], frame.shape[1]),
                rotation_angle=self.rotation_angle[-1],
                image_key=ImageKey.FLAT_FIELD.value,
                image_key_control=ImageKey.FLAT_FIELD.value,
                diode_data=None,
            )

    def add_final_flat(self):
        for frame in self._final_flats:
            self._append_frame(
                data_=frame.reshape(1, frame.shape[0], frame.shape[1]),
                rotation_angle=self.rotation_angle[-1],
                image_key=ImageKey.FLAT_FIELD.value,
                image_key_control=ImageKey.FLAT_FIELD.value,
                diode_data=None,
            )


class BaseTestAddDarkAndFlats(unittest.TestCase):
    """
    Unit test on nxtomomill.utils.add_dark_flat_nx_file function
    """

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        simple_nx_path = os.path.join(self.tmpdir, "simple_case")
        self.dim = 55
        self.nproj = 20
        self._simple_nx = MockNXtomoWithElecCurrent(
            scan_path=simple_nx_path,
            n_proj=self.nproj,
            ini_dark=None,
            ini_flats=None,
            final_flats=None,
            dim=self.dim,
            machine_current=numpy.zeros(self.nproj),
        ).scan
        with HDF5File(
            self._simple_nx.master_file, mode="r", swmr=get_swmr_mode()
        ) as h5s:
            data_path = "/".join(
                (self._simple_nx.entry, "instrument", "detector", "data")
            )
            self._raw_data = h5py_read_dataset(h5s[data_path])
        nx_with_vds_path = os.path.join(self.tmpdir, "case_with_vds")
        self._nx_with_virtual_dataset = MockNXtomoWithElecCurrent(
            scan_path=nx_with_vds_path,
            n_proj=0,
            ini_dark=None,
            ini_flats=None,
            final_flats=None,
            dim=self.dim,
            machine_current=numpy.zeros(self.nproj),
        ).scan
        self._create_vds(
            source_file=self._simple_nx.master_file,
            source_data_path=self._simple_nx.entry,
            target_file=self._nx_with_virtual_dataset.master_file,
            target_data_path=self._nx_with_virtual_dataset.entry,
            copy_other_data=True,
        )
        self._patch_nxtomo_flags(self._nx_with_virtual_dataset)

        nx_with_vds_path_and_links = os.path.join(
            self.tmpdir, "case_with_vds_and_links"
        )
        self._nx_with_virtual_dataset_with_link = MockNXtomoWithElecCurrent(
            scan_path=nx_with_vds_path_and_links,
            n_proj=0,
            ini_dark=None,
            ini_flats=None,
            final_flats=None,
            dim=self.dim,
            machine_current=numpy.zeros(self.nproj),
        ).scan
        self._create_vds(
            source_file=self._simple_nx.master_file,
            source_data_path=self._simple_nx.entry,
            target_file=self._nx_with_virtual_dataset_with_link.master_file,
            target_data_path=self._nx_with_virtual_dataset_with_link.entry,
            copy_other_data=True,
        )
        self._patch_nxtomo_flags(self._nx_with_virtual_dataset_with_link)

        # create dark
        self.start_dark = (
            numpy.random.random((self.dim * self.dim))
            .reshape(1, self.dim, self.dim)
            .astype("f")
        )
        self.start_dark_file = os.path.join(self.tmpdir, "dark.hdf5")
        self.start_dark_entry = "data"
        self.start_dark_url = self._save_raw(
            data=self.start_dark,
            entry=self.start_dark_entry,
            file_path=self.start_dark_file,
        )

        self.end_dark = (
            numpy.random.random((self.dim * self.dim * 2))
            .reshape(2, self.dim, self.dim)
            .astype("f")
        )
        self.end_dark_file = os.path.join(self.tmpdir, "dark.hdf5")
        self.end_dark_entry = "data2"
        self.end_dark_url = self._save_raw(
            data=self.end_dark, entry=self.end_dark_entry, file_path=self.end_dark_file
        )

        # create flats
        self.start_flat = (
            numpy.random.random((self.dim * self.dim * 3))
            .reshape(3, self.dim, self.dim)
            .astype("f")
        )
        self.start_flat_file = os.path.join(self.tmpdir, "start_flat.hdf5")
        self.start_flat_entry = "/root/flat"
        self.start_flat_url = self._save_raw(
            data=self.start_flat,
            entry=self.start_flat_entry,
            file_path=self.start_flat_file,
        )

        self.end_flat = (
            numpy.random.random((self.dim * self.dim))
            .reshape(1, self.dim, self.dim)
            .astype("f")
        )
        # save the end flat in the simple case file to insure all cases are
        # consider
        self.end_flat_file = self._simple_nx.master_file
        self.end_flat_entry = "flat"
        self.end_flat_url = self._save_raw(
            data=self.end_flat, entry=self.end_flat_entry, file_path=self.end_flat_file
        )

    def _save_raw(self, data, entry, file_path) -> DataUrl:
        with HDF5File(file_path, mode="a") as h5s:
            h5s[entry] = data
        return DataUrl(file_path=file_path, data_path=entry, scheme="silx")

    def _create_vds(
        self,
        source_file: str,
        source_data_path: str,
        target_file: str,
        target_data_path: str,
        copy_other_data: bool,
    ):
        """Create virtual dataset and links from source to target

        :param source_file:
        :param source_data_path:
        :param target_file:
        :param target_data_path:
        :param copy_other_data: we want to create two cases: one copying
                                     datasets 'image_key'... and the other
                                     one linking them. Might have a difference
                                     of behavior when overwriting for example
        """
        assert source_file != target_file, "file should be different"
        # link data
        n_frames = 0
        # for now we only consider the original data
        with HDF5File(source_file, mode="r", swmr=get_swmr_mode()) as o_h5s:
            old_path = os.path.join(source_data_path, "instrument", "detector", "data")
            n_frames += o_h5s[old_path].shape[0]
            shape = o_h5s[old_path].shape
            data_type = o_h5s[old_path].dtype

            layout = h5py.VirtualLayout(shape=shape, dtype=data_type)
            assert os.path.exists(source_file)
            with HDF5File(source_file, mode="r", swmr=get_swmr_mode()) as ppp:
                assert source_data_path in ppp
            layout[:] = h5py.VirtualSource(path_or_dataset=o_h5s[old_path])

            det_path = os.path.join(target_data_path, "instrument", "detector")
            with HDF5File(target_file, mode="a") as h5s:
                detector_node = h5s.require_group(det_path)
                detector_node.create_virtual_dataset("data", layout, fillvalue=-5)

        for path in (
            os.path.join("instrument", "detector", "image_key"),
            os.path.join("instrument", "detector", "image_key_control"),
            os.path.join("instrument", "detector", "count_time"),
            os.path.join("sample", "rotation_angle"),
        ):
            old_path = os.path.join(source_data_path, path)
            new_path = os.path.join(target_data_path, path)
            with HDF5File(target_file, mode="a") as h5s:
                if copy_other_data:
                    with HDF5File(source_file, mode="r", swmr=get_swmr_mode()) as o_h5s:
                        if new_path in h5s:
                            del h5s[new_path]
                        h5s[new_path] = h5py_read_dataset(o_h5s[old_path])
                elif source_file == target_file:
                    h5s[new_path] = h5py.SoftLink(old_path)
                else:
                    relpath = os.path.relpath(source_file, os.path.dirname(target_file))
                    h5s[new_path] = h5py.ExternalLink(relpath, old_path)

    def _patch_nxtomo_flags(self, scan):
        """Insure necessary flags are here"""
        with HDF5File(scan.master_file, mode="a") as h5s:
            instrument_path = os.path.join(scan.entry, "instrument")
            instrument_node = h5s.require_group(instrument_path)
            if "NX_class" not in instrument_node.attrs:
                instrument_node.attrs["NX_class"] = "NXinstrument"
            detector_node = instrument_node.require_group("detector")
            if "NX_class" not in detector_node.attrs:
                detector_node.attrs["NX_class"] = "NXdetector"
            if "data" in instrument_node:
                if "interpretation" not in instrument_node.attrs:
                    instrument_node["data"].attrs["interpretation"] = "image"

            sample_path = os.path.join(scan.entry, "sample")
            sample_node = h5s.require_group(sample_path)
            if "NX_class" not in sample_node:
                sample_node.attrs["NX_class"] = "NXsample"

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir)


class TestAddDarkAtStart(BaseTestAddDarkAndFlats):
    """
    Make sure adding dark works
    """

    def testAddDarkAsNumpyArray(self) -> None:
        """Insure adding a dark works from a numpy array"""
        for scan in (self._simple_nx,):
            with self.subTest(scan=scan):
                add_dark_flat_nx_file(
                    file_path=scan.master_file,
                    entry=scan.entry,
                    darks_start=self.start_dark,
                )

                # test `data` dataset
                with HDF5File(scan.master_file, mode="r", swmr=get_swmr_mode()) as h5s:
                    data_path = os.path.join(
                        scan.entry, "instrument", "detector", "data"
                    )
                    self.assertEqual(
                        h5s[data_path].shape, (self.nproj + 1, self.dim, self.dim)
                    )
                    numpy.testing.assert_array_almost_equal(
                        h5s[data_path][0], self.start_dark[0]
                    )
                    numpy.testing.assert_array_almost_equal(
                        h5s[data_path][1], self._raw_data[0]
                    )
                    # insure we can still make a HDF5Scan out of it
                    NXtomoScan(scan=scan.master_file, entry=scan.entry)

        # test some exception are raised if we try to add directly a numpy
        # array within a virtual dataset
        for scan in (
            self._nx_with_virtual_dataset,
            self._nx_with_virtual_dataset_with_link,
        ):
            with self.assertRaises(TypeError):
                add_dark_flat_nx_file(
                    file_path=scan.master_file,
                    entry=scan.entry,
                    darks_start=self.start_dark,
                )

    def testAddDarkAsDataUrl(self) -> None:
        """Insure adding a dark works from a DataUrl"""
        for scan in (self._nx_with_virtual_dataset_with_link,):
            with self.subTest(scan=scan):
                add_dark_flat_nx_file(
                    file_path=scan.master_file,
                    entry=scan.entry,
                    darks_start=self.start_dark_url,
                )

                # test `data` dataset
                with HDF5File(scan.master_file, mode="r", swmr=get_swmr_mode()) as h5s:
                    data_path = os.path.join(
                        scan.entry, "instrument", "detector", "data"
                    )
                    self.assertEqual(
                        h5s[data_path].shape, (self.nproj + 1, self.dim, self.dim)
                    )
                    numpy.testing.assert_array_almost_equal(
                        h5s[data_path][0], self.start_dark[0]
                    )
                    numpy.testing.assert_array_almost_equal(
                        h5s[data_path][1], self._raw_data[0]
                    )
                    # insure we can still make a HDF5Scan out of it
                    NXtomoScan(scan=scan.master_file, entry=scan.entry)
                    # test rotation angle and count_time
                    count_time_path = os.path.join(
                        scan.entry, "instrument", "detector", "count_time"
                    )
                    numpy.testing.assert_array_equal(
                        h5py_read_dataset(h5s[count_time_path][-1]), 1
                    )
                    self.assertEqual(
                        len(h5s[count_time_path]), self.nproj + self.start_dark.shape[0]
                    )
                    rotation_angle_path = os.path.join(
                        scan.entry, "sample", "rotation_angle"
                    )
                    numpy.testing.assert_array_equal(
                        h5s[rotation_angle_path][0], h5s[rotation_angle_path][1]
                    )
                    self.assertEqual(
                        len(h5s[rotation_angle_path]),
                        self.nproj + self.start_dark.shape[0],
                    )
                    control_data_path = os.path.join(scan.entry, "control", "data")
                    numpy.testing.assert_array_equal(
                        h5s[control_data_path][0], h5s[control_data_path][1]
                    )
                    self.assertEqual(
                        len(h5s[control_data_path]),
                        self.nproj + self.start_dark.shape[0],
                    )


class TestAddFlatAtStart(BaseTestAddDarkAndFlats):
    """
    Make sure adding initial flat works
    """

    def testAddFlatStartAsNumpyArray(self) -> None:
        """Insure adding a dark works from a numpy array"""
        for scan in (self._simple_nx,):
            with self.subTest(scan=scan):
                add_dark_flat_nx_file(
                    file_path=scan.master_file,
                    entry=scan.entry,
                    flats_start=self.start_flat,
                )

                # test `data` dataset
                with HDF5File(scan.master_file, mode="r", swmr=get_swmr_mode()) as h5s:
                    data_path = os.path.join(
                        scan.entry, "instrument", "detector", "data"
                    )
                    self.assertEqual(
                        h5s[data_path].shape,
                        (self.nproj + self.start_flat.shape[0], self.dim, self.dim),
                    )
                    numpy.testing.assert_array_almost_equal(
                        h5s[data_path][0], self.start_flat[0]
                    )
                    numpy.testing.assert_array_almost_equal(
                        h5s[data_path][2], self.start_flat[2]
                    )
                    numpy.testing.assert_array_almost_equal(
                        h5s[data_path][3], self._raw_data[0]
                    )
                    # insure we can still make a HDF5Scan out of it
                    NXtomoScan(scan=scan.master_file, entry=scan.entry)

        # test some exception are raised if we try to add directly a numpy
        # array within a virtual dataset
        for scan in (
            self._nx_with_virtual_dataset,
            self._nx_with_virtual_dataset_with_link,
        ):
            with self.assertRaises(TypeError):
                add_dark_flat_nx_file(
                    file_path=scan.master_file,
                    entry=scan.entry,
                    flats_start=self.start_flat,
                )

    def testAddFlatStartAsDataUrl(self) -> None:
        """Insure adding a dark works from a DataUrl"""
        for scan in (self._nx_with_virtual_dataset_with_link,):
            with self.subTest(scan=scan):
                add_dark_flat_nx_file(
                    file_path=scan.master_file,
                    entry=scan.entry,
                    flats_start=self.start_flat_url,
                )

                # test `data` dataset
                with HDF5File(scan.master_file, mode="r", swmr=get_swmr_mode()) as h5s:
                    data_path = os.path.join(
                        scan.entry, "instrument", "detector", "data"
                    )
                    self.assertEqual(
                        h5s[data_path].shape,
                        (self.nproj + self.start_flat.shape[0], self.dim, self.dim),
                    )
                    numpy.testing.assert_array_almost_equal(
                        h5s[data_path][0], self.start_flat[0]
                    )
                    numpy.testing.assert_array_almost_equal(
                        h5s[data_path][2], self.start_flat[2]
                    )
                    numpy.testing.assert_array_almost_equal(
                        h5s[data_path][3], self._raw_data[0]
                    )
                    # test rotation angle and count_time
                    count_time_path = os.path.join(
                        scan.entry, "instrument", "detector", "count_time"
                    )
                    numpy.testing.assert_array_equal(
                        h5py_read_dataset(h5s[count_time_path][-1]), 1
                    )
                    self.assertEqual(
                        len(h5s[count_time_path]), self.nproj + self.start_flat.shape[0]
                    )
                    rotation_angle_path = os.path.join(
                        scan.entry, "sample", "rotation_angle"
                    )
                    numpy.testing.assert_array_equal(
                        h5s[rotation_angle_path][0], h5s[rotation_angle_path][1]
                    )
                    self.assertEqual(
                        len(h5s[rotation_angle_path]),
                        self.nproj + self.start_flat.shape[0],
                    )
                    # insure we can still make a HDF5Scan out of it
                    NXtomoScan(scan=scan.master_file, entry=scan.entry)


class TestAddFlatAtEnd(BaseTestAddDarkAndFlats):
    """
    Make sure adding final flat works
    """

    def testAddFlatEndAsNumpyArray(self) -> None:
        """Insure adding a dark works from a numpy array"""
        for scan in (self._simple_nx,):
            with self.subTest(scan=scan):
                add_dark_flat_nx_file(
                    file_path=scan.master_file,
                    entry=scan.entry,
                    flats_end=self.end_flat,
                )

                # test `data` dataset
                with HDF5File(scan.master_file, mode="r", swmr=get_swmr_mode()) as h5s:
                    data_path = os.path.join(
                        scan.entry, "instrument", "detector", "data"
                    )
                    self.assertEqual(
                        h5s[data_path].shape,
                        (self.nproj + self.end_flat.shape[0], self.dim, self.dim),
                    )
                    numpy.testing.assert_array_almost_equal(
                        h5s[data_path][-1], self.end_flat[-1]
                    )
                    numpy.testing.assert_array_almost_equal(
                        h5s[data_path][0], self._raw_data[0]
                    )
                    # insure we can still make a HDF5Scan out of it
                    NXtomoScan(scan=scan.master_file, entry=scan.entry)

                    # test the 'image_key' and image_key_control dataset
                    img_key_control_path = os.path.join(
                        scan.entry, "instrument", "detector", "image_key_control"
                    )
                    numpy.testing.assert_array_equal(
                        h5py_read_dataset(h5s[img_key_control_path][-2:]), [0, 1]
                    )
                    img_key_path = os.path.join(
                        scan.entry, "instrument", "detector", "image_key"
                    )
                    numpy.testing.assert_array_equal(
                        h5py_read_dataset(h5s[img_key_path][-2:]), [0, 1]
                    )
                    # test rotation angle and count_time
                    count_time_path = os.path.join(
                        scan.entry, "instrument", "detector", "count_time"
                    )
                    numpy.testing.assert_array_equal(
                        h5py_read_dataset(h5s[count_time_path][-1]), 1
                    )
                    self.assertEqual(
                        len(h5s[count_time_path]), self.nproj + self.end_flat.shape[0]
                    )
                    rotation_angle_path = os.path.join(
                        scan.entry, "sample", "rotation_angle"
                    )
                    numpy.testing.assert_array_equal(
                        h5s[rotation_angle_path][-1], h5s[rotation_angle_path][-2]
                    )
                    self.assertEqual(
                        len(h5s[rotation_angle_path]),
                        self.nproj + self.end_flat.shape[0],
                    )

        # test some exception are raised if we try to add directly a numpy
        # array within a virtual dataset
        for scan in (
            self._nx_with_virtual_dataset,
            self._nx_with_virtual_dataset_with_link,
        ):
            with self.assertRaises(TypeError):
                add_dark_flat_nx_file(
                    file_path=scan.master_file,
                    entry=scan.entry,
                    flats_end=self.end_flat,
                )

    def testAddFlatStartAsDataUrl(self) -> None:
        """Insure adding a dark works from a DataUrl"""
        for scan in (self._nx_with_virtual_dataset_with_link,):
            with self.subTest(scan=scan):
                add_dark_flat_nx_file(
                    file_path=scan.master_file,
                    entry=scan.entry,
                    flats_end=self.end_flat_url,
                )

                # test data is correctly store
                with HDF5File(scan.master_file, mode="r", swmr=get_swmr_mode()) as h5s:
                    # test the 'data' dataset
                    data_path = os.path.join(
                        scan.entry, "instrument", "detector", "data"
                    )
                    self.assertEqual(
                        h5s[data_path].shape,
                        (self.nproj + self.end_flat.shape[0], self.dim, self.dim),
                    )
                    numpy.testing.assert_array_almost_equal(
                        h5s[data_path][-1], self.end_flat[-1]
                    )
                    numpy.testing.assert_array_almost_equal(
                        h5s[data_path][0], self._raw_data[0]
                    )
                    NXtomoScan(scan=scan.master_file, entry=scan.entry)
                    # test the 'image_key' and image_key_control dataset
                    img_key_control_path = os.path.join(
                        scan.entry, "instrument", "detector", "image_key_control"
                    )
                    numpy.testing.assert_array_equal(
                        h5py_read_dataset(h5s[img_key_control_path][-2:]), [0, 1]
                    )
                    img_key_path = os.path.join(
                        scan.entry, "instrument", "detector", "image_key"
                    )
                    numpy.testing.assert_array_equal(
                        h5py_read_dataset(h5s[img_key_path][-2:]), [0, 1]
                    )
                    # test rotation angle and count_time
                    count_time_path = os.path.join(
                        scan.entry, "instrument", "detector", "count_time"
                    )
                    numpy.testing.assert_array_equal(
                        h5py_read_dataset(h5s[count_time_path][-1]), 1
                    )
                    self.assertEqual(
                        len(h5s[count_time_path]), self.nproj + self.end_flat.shape[0]
                    )
                    rotation_angle_path = os.path.join(
                        scan.entry, "sample", "rotation_angle"
                    )
                    numpy.testing.assert_array_equal(
                        h5s[rotation_angle_path][-1], h5s[rotation_angle_path][-2]
                    )
                    self.assertEqual(
                        len(h5s[rotation_angle_path]),
                        self.nproj + self.end_flat.shape[0],
                    )
                    # insure we can still make a HDF5Scan out of it
                    NXtomoScan(scan=scan.master_file, entry=scan.entry)


class TestAddDarkAndFlatWithFancySelection(BaseTestAddDarkAndFlats):
    """Insure we can do some fancy selection with virtual dataset and data url"""

    def testValid(self):
        """
        Insure virtual dataset are still correctly recreate even if
        using slices
        """
        scan = self._nx_with_virtual_dataset_with_link

        start_flat_url = DataUrl(
            file_path=self.start_flat_file,
            data_path=self.start_flat_entry,
            data_slice=slice(0, 4),
            scheme="silx",
        )
        end_dark_url = DataUrl(
            file_path=self.end_dark_file,
            data_path=self.end_dark_entry,
            data_slice=[
                1,
            ],
            scheme="silx",
        )

        add_dark_flat_nx_file(
            file_path=scan.master_file,
            entry=scan.entry,
            flats_start=start_flat_url,
            darks_end=end_dark_url,
            embed_data=False,
        )

        # test data is correctly store
        with HDF5File(scan.master_file, mode="r", swmr=get_swmr_mode()) as h5s:
            # test the 'data' dataset
            data_path = os.path.join(scan.entry, "instrument", "detector", "data")
            self.assertEqual(
                h5s[data_path].shape,
                (self.nproj + 3 + 1, self.dim, self.dim),
            )
            numpy.testing.assert_array_almost_equal(
                h5s[data_path][0:3], self.start_flat[0:3]
            )
            numpy.testing.assert_array_almost_equal(
                h5s[data_path][-1], self.end_dark[1]
            )
            NXtomoScan(scan=scan.master_file, entry=scan.entry)
            # test the 'image_key' and image_key_control dataset
            img_key_control_path = os.path.join(
                scan.entry, "instrument", "detector", "image_key_control"
            )
            numpy.testing.assert_array_equal(
                h5py_read_dataset(h5s[img_key_control_path][0:3]), [1, 1, 1]
            )
            numpy.testing.assert_array_equal(
                h5py_read_dataset(h5s[img_key_control_path][-2:]), [0, 2]
            )
            # insure we can still make a HDF5Scan out of it
            NXtomoScan(scan=scan.master_file, entry=scan.entry)

    def testInValidSlice(self):
        """Insure an error is raise if user try to
        provide a slice with step !=1. This case is not handled
        """
        scan = self._nx_with_virtual_dataset_with_link

        start_flat_url = DataUrl(
            file_path=self.start_flat_file,
            data_path=self.start_flat_entry,
            data_slice=slice(0, 4, 2),
            scheme="silx",
        )
        end_dark_url = DataUrl(
            file_path=self.end_dark_file,
            data_path=self.end_dark_entry,
            data_slice=[
                1,
            ],
            scheme="silx",
        )
        with self.assertRaises(ValueError):
            add_dark_flat_nx_file(
                file_path=scan.master_file,
                entry=scan.entry,
                flats_start=start_flat_url,
                darks_end=end_dark_url,
                embed_data=False,
            )


class TestCompleteAddFlatAndDark(BaseTestAddDarkAndFlats):
    """
    Complete test on adding dark and flats on a complete case
    """

    def testWithoutExtras(self):
        """Insure a complete case can be handle without defining any extras
        parameters"""
        scan = self._nx_with_virtual_dataset_with_link

        add_dark_flat_nx_file(
            file_path=scan.master_file,
            entry=scan.entry,
            flats_start=self.start_flat_url,
            flats_end=self.end_flat_url,
            darks_start=self.start_dark_url,
            extras={},
        )
        with HDF5File(scan.master_file, mode="r", swmr=get_swmr_mode()) as h5s:
            # test the 'data' dataset
            data_path = os.path.join(scan.entry, "instrument", "detector", "data")
            th_shape = (
                self.nproj
                + self.end_flat.shape[0]
                + self.start_flat.shape[0]
                + self.start_dark.shape[0],
                self.dim,
                self.dim,
            )
            self.assertEqual(h5s[data_path].shape, th_shape)

            # test the 'image_key' and image_key_control dataset
            numpy.testing.assert_array_almost_equal(
                h5s[data_path][0], self.start_dark[0]
            )
            numpy.testing.assert_array_almost_equal(
                h5s[data_path][1], self.start_flat[0]
            )
            numpy.testing.assert_array_almost_equal(
                h5s[data_path][-1], self.end_flat[0]
            )
            numpy.testing.assert_array_almost_equal(
                h5s[data_path][-self.end_flat.shape[0] - 1], self._raw_data[-1]
            )

            # test image_key
            img_key_path = os.path.join(
                scan.entry, "instrument", "detector", "image_key"
            )
            th_img_keys = [0] * self.nproj
            [th_img_keys.insert(0, 1) for _ in range(self.start_flat.shape[0])]
            [th_img_keys.insert(0, 2) for _ in range(self.start_dark.shape[0])]
            [th_img_keys.append(1) for _ in range(self.end_flat.shape[0])]

            numpy.testing.assert_array_equal(h5s[img_key_path], th_img_keys)
            # test rotation_angle dataset
            rotation_angle_dataset = os.path.join(
                scan.entry, "sample", "rotation_angle"
            )
            numpy.testing.assert_array_almost_equal(
                h5s[rotation_angle_dataset][0], h5s[rotation_angle_dataset][1]
            )
            numpy.testing.assert_array_almost_equal(
                h5s[rotation_angle_dataset][0], h5s[rotation_angle_dataset][2]
            )
            numpy.testing.assert_array_almost_equal(
                h5s[rotation_angle_dataset][-2], h5s[rotation_angle_dataset][-1]
            )

    def testWithExtras(self):
        """Insure a complete case can be handle providing some extras
        parameters"""
        scan = self._nx_with_virtual_dataset
        dark_extras = {"rotation_angle": 10.2}
        start_flat_extras = {"rotation_angle": [10, 11, 12]}
        end_flat_extras = {"count_time": 0.3}
        end_dark_extras = {"count_time": [0.1, 0.2], "rotation_angle": [89, 88]}

        extras = {
            "darks_start": dark_extras,
            "darks_end": end_dark_extras,
            "flats_start": start_flat_extras,
            "flats_end": end_flat_extras,
        }
        add_dark_flat_nx_file(
            file_path=scan.master_file,
            entry=scan.entry,
            flats_start=self.start_flat_url,
            flats_end=self.end_flat_url,
            darks_start=self.start_dark_url,
            darks_end=self.end_dark_url,
            extras=extras,
        )
        with HDF5File(scan.master_file, mode="r", swmr=get_swmr_mode()) as h5s:
            # test the 'data' dataset
            data_path = os.path.join(scan.entry, "instrument", "detector", "data")
            th_shape = (
                self.nproj
                + self.end_flat.shape[0]
                + self.start_flat.shape[0]
                + self.start_dark.shape[0]
                + self.end_dark.shape[0],
                self.dim,
                self.dim,
            )
            self.assertEqual(h5s[data_path].shape, th_shape)

            # test the 'image_key' and image_key_control dataset
            numpy.testing.assert_array_almost_equal(
                h5s[data_path][0], self.start_dark[0]
            )
            numpy.testing.assert_array_almost_equal(
                h5s[data_path][1], self.start_flat[0]
            )
            numpy.testing.assert_array_almost_equal(
                h5s[data_path][-1], self.end_flat[0]
            )
            numpy.testing.assert_array_almost_equal(
                h5s[data_path][-self.end_flat.shape[0] - self.end_dark.shape[0] - 1],
                self._raw_data[-1],
            )
            numpy.testing.assert_array_almost_equal(
                h5s[data_path][-3], self.end_dark[-2]
            )

            # test image_key
            img_key_path = os.path.join(
                scan.entry, "instrument", "detector", "image_key"
            )
            th_img_keys = [0] * self.nproj
            [th_img_keys.insert(0, 1) for _ in range(self.start_flat.shape[0])]
            [th_img_keys.insert(0, 2) for _ in range(self.start_dark.shape[0])]
            [th_img_keys.append(2) for _ in range(self.end_dark.shape[0])]
            [th_img_keys.append(1) for _ in range(self.end_flat.shape[0])]

            numpy.testing.assert_array_equal(h5s[img_key_path], th_img_keys)
            # test rotation_angle dataset
            rotation_angle_dataset = os.path.join(
                scan.entry, "sample", "rotation_angle"
            )
            numpy.testing.assert_array_almost_equal(
                h5s[rotation_angle_dataset][0], 10.2
            )
            numpy.testing.assert_array_almost_equal(h5s[rotation_angle_dataset][-3], 89)
            numpy.testing.assert_array_almost_equal(
                h5py_read_dataset(h5s[rotation_angle_dataset][1:4]),
                numpy.array([10, 11, 12]),
            )
            numpy.testing.assert_array_almost_equal(
                h5s[rotation_angle_dataset][-2], h5s[rotation_angle_dataset][-1]
            )
            count_time_dataset = os.path.join(
                scan.entry, "instrument", "detector", "count_time"
            )
            self.assertEqual(h5s[count_time_dataset][-1], 0.3)
            self.assertEqual(h5s[count_time_dataset][-2], 0.2)
            self.assertEqual(h5s[count_time_dataset][0], 1)


class TestChangeImageKeyControl(unittest.TestCase):
    """
    Test the `change_image_key_control` function
    """

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        simple_nx_path = os.path.join(self.tmpdir, "simple_case")
        self.dim = 55
        self.nproj = 20
        # this can will have one dark, then 4 flats then 20 projections
        # then 4 flats and 5 alignment projections at the end
        mock = MockNXtomo(
            scan_path=simple_nx_path,
            n_proj=self.nproj,
            n_ini_proj=self.nproj,
            create_ini_dark=True,
            create_ini_flat=True,
            create_final_flat=True,
            dim=self.dim,
            n_refs=4,
        )
        n_alignment = 5
        for i in range(n_alignment):
            mock.add_alignment_radio(i, angle=0)
        self.scan = mock.scan

    def tearDown(self) -> None:
        if os.path.exists(self.tmpdir):
            shutil.rmtree(self.tmpdir)

    def testInputType(self):
        """Check a TypeError is raised if input of `frames_indexes` is
        invalid"""
        with self.assertRaises(TypeError):
            change_image_key_control(
                file_path=self.scan.master_file,
                entry=self.scan.entry,
                frames_indexes=1,
                image_key_control_value=ImageKey.PROJECTION,
            )

    def testUpdateToProjections(self):
        """Insure we can correctly set some frame as `projection`"""
        change_image_key_control(
            file_path=self.scan.master_file,
            entry=self.scan.entry,
            frames_indexes=slice(0, 3, 2),
            image_key_control_value=ImageKey.PROJECTION,
        )
        with HDF5File(self.scan.master_file, mode="r", swmr=get_swmr_mode()) as h5s:
            image_keys_path = "/".join(
                (self.scan.entry, "instrument", "detector", "image_key")
            )
            image_keys = h5s[image_keys_path]
            image_keys_control_path = "/".join(
                (self.scan.entry, "instrument", "detector", "image_key_control")
            )
            self.assertEqual(image_keys[0], ImageKey.PROJECTION.value)
            self.assertEqual(image_keys[1], ImageKey.FLAT_FIELD.value)
            self.assertEqual(image_keys[2], ImageKey.PROJECTION.value)

            image_keys_control = h5s[image_keys_control_path]
            self.assertEqual(image_keys_control[0], ImageKey.PROJECTION.value)
            self.assertEqual(image_keys_control[1], ImageKey.FLAT_FIELD.value)
            self.assertEqual(image_keys_control[2], ImageKey.PROJECTION.value)

    def testUpdateToDark(self):
        """Insure we can correctly set some frame as `dark`"""
        change_image_key_control(
            file_path=self.scan.master_file,
            entry=self.scan.entry,
            frames_indexes=[1],
            image_key_control_value=ImageKey.DARK_FIELD,
        )
        with HDF5File(self.scan.master_file, mode="r", swmr=get_swmr_mode()) as h5s:
            image_keys_path = "/".join(
                (self.scan.entry, "instrument", "detector", "image_key")
            )
            image_keys = h5s[image_keys_path]
            image_keys_control_path = "/".join(
                (self.scan.entry, "instrument", "detector", "image_key_control")
            )
            self.assertEqual(image_keys[0], ImageKey.DARK_FIELD.value)
            self.assertEqual(image_keys[1], ImageKey.DARK_FIELD.value)
            self.assertEqual(image_keys[2], ImageKey.FLAT_FIELD.value)

            image_keys_control = h5s[image_keys_control_path]
            self.assertEqual(image_keys_control[0], ImageKey.DARK_FIELD.value)
            self.assertEqual(image_keys_control[1], ImageKey.DARK_FIELD.value)
            self.assertEqual(image_keys_control[2], ImageKey.FLAT_FIELD.value)

    def testUpdateToFlat(self):
        """Insure we can correctly set some frame as `flatfield`"""
        change_image_key_control(
            file_path=self.scan.master_file,
            entry=self.scan.entry,
            frames_indexes=[0],
            image_key_control_value=ImageKey.FLAT_FIELD,
        )
        with HDF5File(self.scan.master_file, mode="r", swmr=get_swmr_mode()) as h5s:
            image_keys_path = "/".join(
                (self.scan.entry, "instrument", "detector", "image_key")
            )
            image_keys = h5s[image_keys_path]
            image_keys_control_path = "/".join(
                (self.scan.entry, "instrument", "detector", "image_key_control")
            )
            self.assertEqual(image_keys[0], ImageKey.FLAT_FIELD.value)
            self.assertEqual(image_keys[1], ImageKey.FLAT_FIELD.value)

            image_keys_control = h5s[image_keys_control_path]
            self.assertEqual(image_keys_control[0], ImageKey.FLAT_FIELD.value)
            self.assertEqual(image_keys_control[1], ImageKey.FLAT_FIELD.value)

    def testUpdateToAlignment(self):
        """Insure we can correctly set some frame as `alignment`"""
        change_image_key_control(
            file_path=self.scan.master_file,
            entry=self.scan.entry,
            frames_indexes=slice(10, 20, None),
            image_key_control_value=ImageKey.ALIGNMENT,
        )
        with HDF5File(self.scan.master_file, mode="r", swmr=get_swmr_mode()) as h5s:
            image_keys_path = "/".join(
                (self.scan.entry, "instrument", "detector", "image_key")
            )
            image_keys = h5s[image_keys_path]
            image_keys_control_path = "/".join(
                (self.scan.entry, "instrument", "detector", "image_key_control")
            )
            self.assertEqual(image_keys[10], ImageKey.PROJECTION.value)
            self.assertEqual(image_keys[11], ImageKey.PROJECTION.value)
            self.assertEqual(image_keys[20], ImageKey.PROJECTION.value)

            image_keys_control = h5s[image_keys_control_path]
            self.assertEqual(image_keys_control[9], ImageKey.PROJECTION.value)
            self.assertEqual(image_keys_control[10], ImageKey.ALIGNMENT.value)
            self.assertEqual(image_keys_control[11], ImageKey.ALIGNMENT.value)
            self.assertEqual(image_keys_control[21], ImageKey.PROJECTION.value)

    def testUpdateToInvalid(self):
        """Insure we can correctly set some frame as `invalid`"""
        change_image_key_control(
            file_path=self.scan.master_file,
            entry=self.scan.entry,
            frames_indexes=slice(0, 16, 5),
            image_key_control_value=ImageKey.INVALID,
        )
        with HDF5File(self.scan.master_file, mode="r", swmr=get_swmr_mode()) as h5s:
            image_keys_path = "/".join(
                (self.scan.entry, "instrument", "detector", "image_key")
            )
            image_keys = h5s[image_keys_path]
            image_keys_control_path = "/".join(
                (self.scan.entry, "instrument", "detector", "image_key_control")
            )
            self.assertEqual(image_keys[9], ImageKey.PROJECTION.value)
            self.assertEqual(image_keys[10], ImageKey.INVALID.value)
            self.assertEqual(image_keys[11], ImageKey.PROJECTION.value)
            self.assertEqual(image_keys[15], ImageKey.INVALID.value)

            image_keys_control = h5s[image_keys_control_path]
            self.assertEqual(image_keys_control[9], ImageKey.PROJECTION.value)
            self.assertEqual(image_keys_control[10], ImageKey.INVALID.value)
            self.assertEqual(image_keys_control[11], ImageKey.PROJECTION.value)
            self.assertEqual(image_keys_control[15], ImageKey.INVALID.value)


class TestAddDarkAndFlatFromADifferentFolderWithVDS(unittest.TestCase):
    """
    Test adding dark and flat to vds pointing to vds pointing on files at
    at different level of the file system.
                               root_folder
            _______________________|_____________
           |                                    |
       folder_1                              folder_2
           |                                    |
      file created      _________________________|___________________
                       |               |                            |
                  subfolder_21     subfolder_22                 file with
                       |               |                    original start dark
               File containing     ____|___________
              VDS pointing to     |               |
              original flat    File with     subsubfolder_221
              and dark         original              |
                               start flat   File with original
                                               end flat
    """

    def setUp(self) -> None:
        unittest.TestCase.setUp(self)
        self.dim = 20
        # create folder
        self.root_folder = tempfile.mkdtemp()
        self.mv_folder = tempfile.mkdtemp()
        self.folder_1 = os.path.join(self.root_folder, "folder_1")
        self.folder_2 = os.path.join(self.root_folder, "folder_2")
        self.subfolder_21 = os.path.join(self.root_folder, "subfolder_21")
        self.subfolder_22 = os.path.join(self.root_folder, "subfolder_22")
        self.subsubfolder_221 = os.path.join(self.root_folder, "subsubfolder_221")
        for folder in (
            self.folder_1,
            self.folder_2,
            self.subfolder_21,
            self.subfolder_22,
            self.subsubfolder_221,
        ):
            os.makedirs(folder)

        # create original dark
        self.start_dark = (
            numpy.random.random((5 * self.dim * self.dim))
            .reshape(5, self.dim, self.dim)
            .astype("f")
        )
        self.start_dark_file = os.path.join(self.folder_2, "original_start_dark.hdf5")
        with HDF5File(self.start_dark_file, mode="w") as h5s:
            h5s["dark"] = self.start_dark
        self.start_dark_url = DataUrl(
            file_path=self.start_dark_file, data_path="dark", scheme="silx"
        )

        # create original flats
        self.start_flat = (
            numpy.random.random((5 * self.dim * self.dim))
            .reshape(5, self.dim, self.dim)
            .astype("f")
        )
        self.start_flat_file = os.path.join(self.subfolder_22, "original_start_flat.h5")
        with HDF5File(self.start_flat_file, mode="w") as h5s:
            h5s["flat1"] = self.start_flat
        self.start_flat_url = DataUrl(
            file_path=self.start_flat_file, data_path="flat1", scheme="silx"
        )

        self.end_flat = (
            numpy.random.random((5 * self.dim * self.dim))
            .reshape(5, self.dim, self.dim)
            .astype("f")
        )
        self.end_flat_file = os.path.join(self.subsubfolder_221, "original_end_flat.h5")
        with HDF5File(self.end_flat_file, mode="w") as h5s:
            h5s["flat2"] = self.end_flat
        self.end_flat_url = DataUrl(
            file_path=self.end_flat_file, data_path="flat2", scheme="silx"
        )

    def tearDown(self) -> None:
        for folder in (self.root_folder, self.mv_folder):
            if os.path.exists(folder):
                shutil.rmtree(folder)
        unittest.TestCase.tearDown(self)

    def test(self):
        # create a scan contained in subfolder21
        scan_subfolder_21 = self._simple_nx = MockNXtomo(
            scan_path=self.subfolder_21,
            n_proj=10,
            n_ini_proj=2,
            create_ini_dark=False,
            create_ini_flat=False,
            create_final_flat=False,
            dim=self.dim,
        ).scan
        # 1. add first level of indirection for dark and flat and check the VDS
        add_dark_flat_nx_file(
            file_path=scan_subfolder_21.master_file,
            entry=scan_subfolder_21.entry,
            flats_start=self.start_flat_url,
            flats_end=self.end_flat_url,
            darks_start=self.start_dark_url,
            extras={
                "darks_start": {"count_time": 0.3, "rotation_angle": 0.0},
                "flats_start": {"count_time": 0.3, "rotation_angle": 0.0},
                "flats_end": {"count_time": 0.3, "rotation_angle": 0.0},
            },
        )
        self.check_vds_from_file(
            file_=scan_subfolder_21.master_file, nx_entry=scan_subfolder_21.entry
        )

        # create a scan contained in subfolder221
        scan_subfolder_221 = self._simple_nx = MockNXtomo(
            scan_path=self.subsubfolder_221,
            n_proj=10,
            n_ini_proj=2,
            create_ini_dark=False,
            create_ini_flat=False,
            create_final_flat=False,
            dim=self.dim,
        ).scan
        # 2. create a second level of indirection for dark and flat and check
        # the VDS
        det_data_path = "/".join(
            (scan_subfolder_21.entry, "instrument", "detector", "data")
        )
        new_dark_url = DataUrl(
            file_path=scan_subfolder_21.master_file,
            data_path=det_data_path,
            data_slice=slice(0, 5),
            scheme="silx",
        )
        new_start_flat_url = DataUrl(
            file_path=scan_subfolder_21.master_file,
            data_path=det_data_path,
            data_slice=slice(5, 10),
            scheme="silx",
        )
        new_end_flat_url = DataUrl(
            file_path=scan_subfolder_21.master_file,
            data_path=det_data_path,
            data_slice=slice(12, 17),
            scheme="silx",
        )

        add_dark_flat_nx_file(
            file_path=scan_subfolder_221.master_file,
            entry=scan_subfolder_221.entry,
            flats_start=new_start_flat_url,
            flats_end=new_end_flat_url,
            darks_start=new_dark_url,
            extras={
                "darks_start": {"count_time": 0.3, "rotation_angle": 0.0},
                "flats_start": {"count_time": 0.3, "rotation_angle": 0.0},
                "flats_end": {"count_time": 0.3, "rotation_angle": 0.0},
            },
        )
        self.check_vds_from_file(
            file_=scan_subfolder_221.master_file, nx_entry=scan_subfolder_221.entry
        )

        # 3. move root folder and remove it to insure links are style valid
        shutil.move(src=self.folder_1, dst=self.mv_folder)
        shutil.move(src=self.folder_2, dst=self.mv_folder)
        new_scan_subfolder_221_m = scan_subfolder_221.master_file.replace(
            self.mv_folder, self.root_folder
        )

        self.check_vds_from_file(
            file_=new_scan_subfolder_221_m, nx_entry=scan_subfolder_221.entry
        )

    def check_vds_from_file(self, file_, nx_entry):
        with HDF5File(file_, mode="r", swmr=get_swmr_mode()) as h5s:
            entry_node = h5s[nx_entry]
            det_group = entry_node["instrument/detector"]
            det_data = det_group["data"]
            det_image_key = det_group["image_key"]

            # test dark
            numpy.testing.assert_array_equal(
                det_image_key[:5], [ImageKey.DARK_FIELD.value] * 5
            )
            numpy.testing.assert_array_equal(det_data[:5], self.start_dark)
            # test start flat
            numpy.testing.assert_array_equal(
                det_image_key[5:10], [ImageKey.FLAT_FIELD.value] * 5
            )
            numpy.testing.assert_array_equal(det_data[5:10], self.start_flat)
            # test end flat
            numpy.testing.assert_array_equal(
                det_image_key[-5:], [ImageKey.FLAT_FIELD.value] * 5
            )
            numpy.testing.assert_array_equal(det_data[-5:], self.end_flat)
