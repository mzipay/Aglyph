# -*- coding: UTF-8 -*-

# Copyright (c) 2006, 2011, 2013-2017 Matthew Zipay.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

"""Test case and runner for :func:`aglyph._compat.is_string`."""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import logging
import unittest

from aglyph import __version__
from aglyph._compat import DataType, is_string, TextType
from aglyph.component import Reference

__all__ = [
    "IsStringTest",
    "suite",
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_is_string")


class IsStringTest(unittest.TestCase):

    def test_text_type_is_string_type(self):
        self.assertTrue(is_string(TextType()))

    def test_data_type_is_string_type(self):
        self.assertTrue(is_string(DataType()))

    def test_literal_string_is_string_type(self):
        # this is redundant w/r/t one of the previous two tests, depending on
        # the runtime Python version
        self.assertTrue(is_string(""))

    def test_none_is_not_string(self):
        self.assertFalse(is_string(None))

    def test_number_is_not_string(self):
        self.assertFalse(is_string(79))

    def test_reference_is_string(self):
        self.assertTrue(is_string(Reference("test")))


def suite():
    return unittest.makeSuite(IsStringTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

