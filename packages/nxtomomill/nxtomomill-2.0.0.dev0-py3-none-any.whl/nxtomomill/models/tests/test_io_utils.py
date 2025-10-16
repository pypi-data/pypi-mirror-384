# coding: utf-8

import unittest

from nxtomomill.models import utils


class TestConvertStrToTuple(unittest.TestCase):
    """
    test convert_str_to_tuple function
    """

    def testStr1(self):
        self.assertEqual(utils.convert_str_to_tuple("toto, tata"), ("toto", "tata"))

    def testStr2(self):
        self.assertEqual(
            utils.convert_str_to_tuple("'toto', \"tata\""), ("toto", "tata")
        )

    def testStr3(self):
        self.assertEqual(utils.convert_str_to_tuple("test"), ("test",))

    def testStr4(self):
        self.assertEqual(
            utils.convert_str_to_tuple("(this is a test)"), ("this is a test",)
        )

    def testStr5(self):
        self.assertEqual(
            utils.convert_str_to_tuple("(this is a test, 'and another one')"),
            ("this is a test", "and another one"),
        )


class TestIsUrlPath(unittest.TestCase):
    """test the is_url function"""

    def test_invalid_url_1(self):
        self.assertFalse(utils.is_url_path("/toto/tata"))

    def test_invalid_url_2(self):
        self.assertFalse(utils.is_url_path("tata"))

    def test_valid_url_1(self):
        self.assertTrue(utils.is_url_path("silx:///data/image.h5?path=/scan_0/data"))

    def test_valid_url_2(self):
        self.assertTrue(utils.is_url_path("silx:///data/image.edf"))

    def test_valid_url_3(self):
        self.assertTrue(utils.is_url_path("silx://image.h5"))

    def test_valid_url_4(self):
        self.assertTrue(
            utils.is_url_path("silx:///data/image.h5?path=/scan_0/data&slice=1,5")
        )
