# coding: utf-8


import unittest

from silx.io.url import DataUrl

from nxtomomill.models.h52nx._acquisitionstep import AcquisitionStep
from nxtomomill.models.h52nx.FrameGroup import (
    FrameGroup,
    filter_acqui_frame_type,
)


class TestFrameGroupCreator(unittest.TestCase):
    """Test FrameGroup class"""

    def setUp(self) -> None:
        self.url1 = DataUrl(
            file_path="/path/to/file/my_file", data_path="/path/to/data", scheme="silx"
        )
        self.url2 = DataUrl(file_path="my_file", data_path="/path/to/data")

    def test_default_constructor(self):
        """Test FrameGroup constructor"""
        frame_grp = FrameGroup(url=self.url1, frame_type="projection")
        self.assertEqual(frame_grp.url.path(), self.url1.path())
        self.assertEqual(frame_grp.frame_type, AcquisitionStep.PROJECTION)

        frame_grp = FrameGroup(url=self.url2, frame_type=AcquisitionStep.ALIGNMENT)
        self.assertEqual(frame_grp.url.path(), self.url2.path())
        self.assertEqual(frame_grp.frame_type, AcquisitionStep.ALIGNMENT)

        with self.assertRaises(ValueError):
            FrameGroup(url=self.url1, frame_type="toto")

        with self.assertRaises(ValueError):
            FrameGroup(url=self.url1, frame_type="projection", copy_data="tata")

    def test_constructor_frm_str(self):
        """Test FrameGroup.frm_str function"""
        grp_prefix = FrameGroup.frm_str(
            "frame_type=projections, "
            "entry=silx:///path/to/file/my_file?/path/to/data, "
            "copy_data=True"
        )
        self.assertTrue(isinstance(grp_prefix, FrameGroup))
        self.assertEqual(grp_prefix.copy_data, True)

        grp_no_prefix = FrameGroup.frm_str(
            "projections, silx:///path/to/file/my_file?/path/to/data, True"
        )
        self.assertEqual(str(grp_no_prefix), str(grp_prefix))

        with self.assertRaises(ValueError):
            FrameGroup.frm_str(
                "frame_type=projections, "
                "entry=silx:///path/to/file/my_file?/path/to/data, "
                "copy_data=12"
            )

        with self.assertRaises(ValueError):
            FrameGroup.frm_str("frame_type=projections")


class TestFilterCurrentAcquiFrameType(unittest.TestCase):
    """test filter_acqui_frame_type function"""

    def setUp(self) -> None:
        self.init_1 = FrameGroup(frame_type="init", url=None)
        self.sequence1 = (
            self.init_1,
            FrameGroup(frame_type="dark", url="data/to/dark/1"),
            FrameGroup(frame_type="flat", url="data/to/flat/1"),
            FrameGroup(frame_type="proj", url="data/to/proj/1"),
            FrameGroup(frame_type="proj", url="data/to/proj/2"),
        )

        self.init_2 = FrameGroup(frame_type="init", url="/path/to/init")
        self.sequence2 = (
            self.init_2,
            FrameGroup(frame_type="dark", url="data/to/dark/2"),
            FrameGroup(frame_type="proj", url="data/to/proj/3"),
            FrameGroup(frame_type="proj", url="data/to/proj/4"),
            FrameGroup(frame_type="proj", url="data/to/proj/5"),
            FrameGroup(frame_type="proj", url="data/to/proj/6"),
            FrameGroup(frame_type="flat", url="data/to/flat/2"),
            FrameGroup(frame_type="alignment", url="data/to/alignment/1"),
        )

    def test_search_init(self):
        """test filter_acqui_frame_type with init frame group"""
        with self.assertRaises(ValueError):
            filter_acqui_frame_type(
                init=self.init_1,
                sequences=self.sequence1,
                frame_type=AcquisitionStep.INITIALIZATION,
            )

    def test_search_flat(self):
        """test filter_acqui_frame_type with flat frame group"""
        flat_url = filter_acqui_frame_type(
            init=self.init_1,
            sequences=self.sequence1,
            frame_type=AcquisitionStep.FLAT,
        )
        self.assertEqual(len(flat_url), 1)
        self.assertEqual(flat_url[0].url.path(), self.sequence1[2].url.path())

        with self.assertRaises(ValueError):
            filter_acqui_frame_type(
                init=self.init_1,
                sequences=self.sequence2,
                frame_type=AcquisitionStep.FLAT,
            )

    def test_search_dark(self):
        """test filter_acqui_frame_type with dark frame group"""
        seq_sum = list(self.sequence1)
        seq_sum.extend(self.sequence2)
        dark_1 = filter_acqui_frame_type(
            init=self.init_1, sequences=tuple(seq_sum), frame_type=AcquisitionStep.DARK
        )
        self.assertEqual(len(dark_1), 1)
        self.assertEqual(dark_1[0].url.path(), self.sequence1[1].url.path())
        dark_2 = filter_acqui_frame_type(
            init=self.init_2, sequences=tuple(seq_sum), frame_type=AcquisitionStep.DARK
        )
        self.assertEqual(len(dark_2), 1)
        self.assertEqual(dark_2[0].url.path(), self.sequence2[1].url.path())

    def test_search_proj(self):
        """test filter_acqui_frame_type with projection frame group"""
        projs_1 = filter_acqui_frame_type(
            init=self.init_2,
            sequences=self.sequence2,
            frame_type=AcquisitionStep.PROJECTION,
        )
        self.assertEqual(len(projs_1), 4)
        self.assertEqual(projs_1[2].url.path(), self.sequence2[4].url.path())

        seq_sum = list(self.sequence1)
        seq_sum.extend(self.sequence2)
        projs_2 = filter_acqui_frame_type(
            init=self.init_2,
            sequences=tuple(seq_sum),
            frame_type=AcquisitionStep.PROJECTION,
        )
        self.assertEqual(len(projs_2), 4)
        self.assertEqual(projs_1[1].url.path(), projs_2[1].url.path())
