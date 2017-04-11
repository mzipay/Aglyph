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

"""Test case and runner for :class:`aglyph.component.Reference`."""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import logging
import unittest

from aglyph import AglyphError, __version__
from aglyph._compat import is_string, name_of
from aglyph.component import Reference

from test import assertRaisesWithMessage, dummy

__all__ = [
    "ReferenceTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_Reference")


class ReferenceTest(unittest.TestCase):
    
    def test_initarg_is_required(self):
        self.assertRaises(TypeError, Reference)

    def test_string(self):
        ref = Reference("test-component-id")
        self.assertTrue(isinstance(ref, Reference))
        self.assertTrue(is_string(ref))
        self.assertEqual("test-component-id", ref)

    def test_user_class(self):
        ref = Reference(dummy.ModuleClass)
        self.assertTrue(isinstance(ref, Reference))
        self.assertTrue(is_string(ref))
        self.assertEqual("test.dummy.ModuleClass", ref)

    def test_builtin_class(self):
        ref = Reference(float)
        self.assertTrue(isinstance(ref, Reference))
        self.assertTrue(is_string(ref))
        self.assertEqual("%s.float" % float.__module__, ref)

    def test_user_function(self):
        ref = Reference(dummy.factory_function)
        self.assertTrue(isinstance(ref, Reference))
        self.assertTrue(is_string(ref))
        self.assertEqual("test.dummy.factory_function", ref)

    def test_builtin_function(self):
        ref = Reference(hex)
        self.assertTrue(isinstance(ref, Reference))
        self.assertTrue(is_string(ref))
        self.assertEqual("%s.hex" % hex.__module__, ref)

    def test_module(self):
        ref = Reference(dummy)
        self.assertTrue(isinstance(ref, Reference))
        self.assertTrue(is_string(ref))
        self.assertEqual("test.dummy", ref)

    def test_user_object(self):
        obj = dummy.ModuleClass(None)
        e_expected = AglyphError(
            "%r does not have an importable dotted name" % obj)
        assertRaisesWithMessage(self, e_expected, Reference, obj)

    def test_builtin_object(self):
        e_expected = AglyphError("79 does not have an importable dotted name")
        assertRaisesWithMessage(self, e_expected, Reference, 79)

    def test_staticmethod(self):
        e_expected = AglyphError(
            "%r does not have an importable dotted name" %
                dummy.ModuleClass.staticmethod_factory)
        assertRaisesWithMessage(
            self, e_expected, Reference,
            dummy.ModuleClass.staticmethod_factory)

    def test_classmethod(self):
        e_expected = AglyphError(
            "%r does not have an importable dotted name" %
                dummy.ModuleClass.classmethod_factory)
        assertRaisesWithMessage(
            self, e_expected, Reference, dummy.ModuleClass.classmethod_factory)

    def test_unbound_method(self):
        e_expected = AglyphError(
            "%r does not have an importable dotted name" %
                dummy.ModuleClass.method)
        assertRaisesWithMessage(
            self, e_expected, Reference, dummy.ModuleClass.method)

    def test_bound_method(self):
        bound_method = dummy.ModuleClass(None).method
        e_expected = AglyphError(
            "%r does not have an importable dotted name" % bound_method)
        assertRaisesWithMessage(self, e_expected, Reference, bound_method)

    def test_property(self):
        e_expected = AglyphError(
            "%r does not have an importable dotted name" %
                dummy.ModuleClass.prop)
        assertRaisesWithMessage(
            self, e_expected, Reference, dummy.ModuleClass.prop)

    def test_nonimportable_class(self):
        e_expected = AglyphError(
            "%r does not have an importable dotted name" %
                dummy.ModuleClass.NestedClass)
        assertRaisesWithMessage(
            self, e_expected, Reference, dummy.ModuleClass.NestedClass)

    def test_nonimportable_function(self):
        nested_function = dummy.outer_function()
        e_expected = AglyphError(
            "%r does not have an importable dotted name" % nested_function)
        assertRaisesWithMessage(self, e_expected, Reference, nested_function)


def suite():
    return unittest.makeSuite(ReferenceTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

