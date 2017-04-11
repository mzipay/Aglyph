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

"""Test case and runner for :mod:`aglyph._compat`."""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import logging
import sys
import unittest

from aglyph import _compat, __version__

__all__ = [
    "CompatibilityTest",
    "suite",
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_compat")


class CompatibilityTest(unittest.TestCase):

    def test_python_version_flags(self):
        if sys.version_info[0] == 3:
            self.assertTrue(_compat.is_python_3)
            self.assertFalse(_compat.is_python_2)
        else:
            self.assertFalse(_compat.is_python_3)
            self.assertTrue(_compat.is_python_2)

    def test_ironpython_flag(self):
        try:
            import clr
            has_clr = True
        except:
            has_clr = False
        if "IronPython" in sys.version and has_clr:
            self.assertTrue(_compat.is_ironpython)
        else:
            self.assertFalse(_compat.is_ironpython)

    def test_platform_detail_is_not_empty(self):
        self.assertTrue(_compat.platform_detail.strip() != "")

    def test_text_type_encodes_to_data_type(self):
        self.assertTrue(type(_compat.TextType().encode()) is _compat.DataType)

    def test_data_type_decodes_to_text_type(self):
        self.assertTrue(type(_compat.DataType().decode()) is _compat.TextType)


def suite():
    return unittest.makeSuite(CompatibilityTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

