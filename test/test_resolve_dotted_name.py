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

"""Test case and runner for :func:`aglyph.resolve_dotted_name`."""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import logging
import unittest

from aglyph import resolve_dotted_name, __version__
from aglyph._compat import is_python_2

from test import dummy

__all__ = [
    "ResolveDottedNameTest",
    "suite",
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_resolve_dotted_name")


class ResolveDottedNameTest(unittest.TestCase):

    def test_resolves_module_name(self):
        self.assertTrue(dummy is resolve_dotted_name("test.dummy"))

    def test_resolves_class_name(self):
        self.assertTrue(
            dummy.ModuleClass is resolve_dotted_name("test.dummy.ModuleClass"))

    def test_fails_to_resolve_nested_class(self):
        self.assertRaises(
            ImportError, resolve_dotted_name,
            "test.dummy.ModuleClass.NestedClass")

    def test_resolves_function_name(self):
        self.assertTrue(
            dummy.factory_function is
                resolve_dotted_name("test.dummy.factory_function"))

    def test_resolves_builtin_type_name(self):
        self.assertTrue(
            dict is resolve_dotted_name("%s.dict" % dict.__module__))

    def test_resolves_builtin_function_name(self):
        self.assertTrue(hex is resolve_dotted_name("%s.hex" % hex.__module__))

    def test_fails_to_resolve_when_name_is_not_defined(self):
        self.assertRaises(
            AttributeError, resolve_dotted_name, "test.dummy.NotDefined")


def suite():
    return unittest.makeSuite(ResolveDottedNameTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

