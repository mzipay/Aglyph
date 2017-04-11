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

"""Test case and runner for :func:`aglyph._compat.name_of`."""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import logging
import unittest

from aglyph import __version__
from aglyph._compat import is_python_3, name_of

from test.dummy import ModuleClass, outer_function

__all__ = [
    "NameOfTest",
    "suite",
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_name_of")


class NameOfTest(unittest.TestCase):

    def test_name_of_module_level_class(self):
        self.assertEqual("ModuleClass", name_of(ModuleClass))

    def test_name_of_module_level_function(self):
        self.assertEqual("outer_function", name_of(outer_function))

    def test_name_of_nested_class(self):
        # PEP-3155 - __qualname__ is only available in Python 3.3+
        self.assertEqual(
            "ModuleClass.NestedClass" if is_python_3 else "NestedClass",
            name_of(ModuleClass.NestedClass))

    def test_name_of_nested_function(self):
        self.assertEqual(
            "outer_function.<locals>.nested_function" if is_python_3
                else "nested_function",
            name_of(outer_function()))


def suite():
    return unittest.makeSuite(NameOfTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

