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

"""Test case and runner for :func:`aglyph.format_dotted_name`."""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import logging
import unittest

from aglyph import AglyphError, format_dotted_name, __version__
from aglyph._compat import is_python_2, name_of

from test import assertRaisesWithMessage, dummy

__all__ = [
    "FormatDottedNameTest",
    "suite",
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_format_dotted_name")


class FormatDottedNameTest(unittest.TestCase):

    def test_formats_module_name(self):
        self.assertEqual("test.dummy", format_dotted_name(dummy))

    def test_formats_class_name(self):
        self.assertEqual(
            "test.dummy.ModuleClass", format_dotted_name(dummy.ModuleClass))

    def test_fails_to_format_nested_class_name(self):
        e_expected = AglyphError(
            "%r does not have an importable dotted name" %
                dummy.ModuleClass.NestedClass)
        assertRaisesWithMessage(
            self, e_expected, format_dotted_name,
            dummy.ModuleClass.NestedClass)

    def test_fails_to_format_staticmethod_name(self):
        e_expected = AglyphError(
            "%r does not have an importable dotted name" %
                dummy.ModuleClass.staticmethod_factory)
        assertRaisesWithMessage(
            self, e_expected, format_dotted_name,
            dummy.ModuleClass.staticmethod_factory)

    def test_fails_to_format_classmethod_name(self):
        e_expected = AglyphError(
            "%r does not have an importable dotted name" %
                dummy.ModuleClass.classmethod_factory)
        assertRaisesWithMessage(
            self, e_expected, format_dotted_name,
            dummy.ModuleClass.classmethod_factory)

    def test_formats_function_name(self):
        self.assertEqual(
            "test.dummy.factory_function",
            format_dotted_name(dummy.factory_function))

    def test_fails_to_format_nested_function_name(self):
        nested_function = dummy.outer_function()
        e_expected = AglyphError(
            "%r does not have an importable dotted name" % nested_function)
        assertRaisesWithMessage(
            self, e_expected, format_dotted_name, nested_function)

    def test_formats_builtin_type_name(self):
        self.assertEqual("%s.dict" % dict.__module__, format_dotted_name(dict))

    def test_formats_builtin_function_name(self):
        self.assertEqual("%s.hex" % hex.__module__, format_dotted_name(hex))

    def test_fails_to_format_instance_name(self):
        # instance doesn't have __qualname__ or __name__
        instance = dummy.ModuleClass(None)
        e_expected = AglyphError(
            "%r does not have an importable dotted name" % instance)
        assertRaisesWithMessage(self, e_expected, format_dotted_name, instance)

    def test_fails_to_format_bound_function_name(self):
        bound_function = dummy.MODULE_MEMBER.method
        e_expected = AglyphError(
            "%r does not have an importable dotted name" % bound_function)
        assertRaisesWithMessage(
            self, e_expected, format_dotted_name, bound_function)

    def test_fails_to_format_property_name(self):
        # property doesn't have __module__, __qualname__, or __name__
        e_expected = AglyphError(
            "%r does not have an importable dotted name" %
                dummy.ModuleClass.prop)
        assertRaisesWithMessage(
            self, e_expected, format_dotted_name, dummy.ModuleClass.prop)

    def test_fails_to_format_name_for_none(self):
        # None doesn't have __module__, __qualname__, or __name__
        e_expected = AglyphError(
            "%r does not have an importable dotted name" % None)
        assertRaisesWithMessage(self, e_expected, format_dotted_name, None)


def suite():
    return unittest.makeSuite(FormatDottedNameTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

