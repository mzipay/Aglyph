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

"""Test case and runner for :class:`aglyph.context._TemplateBuilder`."""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import logging
import unittest

from aglyph import __version__, AglyphError
from aglyph.component import Template
from aglyph.context import _TemplateBuilder

from test import assertRaisesWithMessage, dummy
from test.test_InjectionBuilderMixin import InjectionBuilderMixinTest
from test.test_LifecycleBuilderMixin import LifecycleBuilderMixinTest
from test.test_RegistrationMixin import _MockContext, RegistrationMixinTest

__all__ = [
    "TemplateBuilderTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_TemplateBuilder")


class TemplateBuilderTest(
        InjectionBuilderMixinTest, LifecycleBuilderMixinTest,
        RegistrationMixinTest):

    @classmethod
    def setUpClass(cls):
        cls._builder_type = _TemplateBuilder
        cls._definition_type = Template

    def setUp(self):
        self._builder = self._builder_type(
            _MockContext(), "test.dummy.ModuleClass")

    def test_registers_expected_definition_type(self):
        self._builder.register()
        self.assertTrue(
            type(self._builder._context["test.dummy.ModuleClass"])
                is self._definition_type)

    def test_register_fails_on_nonimportable_object(self):
        builder = self._builder_type(
            _MockContext(), dummy.ModuleClass.NestedClass)
        e_expected = AglyphError(
            "%r does not have an importable dotted name" %
                dummy.ModuleClass.NestedClass)
        assertRaisesWithMessage(self, e_expected, builder.register)

    def test_register_unique_id_from_object(self):
        context = _MockContext()
        self._builder_type(context, dummy.ModuleClass).register()
        self.assertTrue("test.dummy.ModuleClass" in context)

    def test_register_parent_id_from_object(self):
        context = _MockContext()
        self._builder_type(
            context, "test", parent=dummy.ModuleClass).register()
        self.assertEqual("test.dummy.ModuleClass", context["test"].parent_id)


def suite():
    return unittest.makeSuite(TemplateBuilderTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

