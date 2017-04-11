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

"""Test case and runner for :func:`aglyph._importable`."""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import logging
import unittest

from aglyph import _importable, __version__

from test import assertRaisesWithMessage, dummy

__all__ = [
    "ImportableTest",
    "suite",
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_importable")


class ImportableTest(unittest.TestCase):
    """Test the :func:`aglyph._importable` function."""

    def test_module_is_importable(self):
        self.assertTrue(_importable(dummy))

    def test_module_level_function_is_importable(self):
        self.assertTrue(_importable(dummy.factory_function))

    def test_nested_function_is_not_importable(self):
        nested_function = dummy.factory_function(None)
        self.assertFalse(_importable(nested_function))

    def test_module_level_class_is_importable(self):
        self.assertTrue(_importable(dummy.ModuleClass))

    def test_nested_class_is_not_importable(self):
        self.assertFalse(_importable(dummy.ModuleClass.NestedClass))

    def test_instance_is_not_importable(self):
        self.assertFalse(_importable(dummy.ModuleClass(None)))

    def test_method_is_not_importable(self):
        self.assertFalse(_importable(dummy.ModuleClass.method))

    def test_literal_is_not_importable(self):
        self.assertFalse(_importable(79))

    def test_None_is_not_importable(self):
        self.assertFalse(_importable(None))


def suite():
    return unittest.makeSuite(ImportableTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

