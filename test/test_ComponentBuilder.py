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

"""Test case and runner for :class:`aglyph.context._ComponentBuilder`.

"""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import logging
import unittest

from aglyph import __version__
from aglyph.component import Component
from aglyph.context import _ComponentBuilder

from test import dummy
from test.test_RegistrationMixin import _MockContext
from test.test_TemplateBuilder import TemplateBuilderTest

__all__ = [
    "ComponentBuilderTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_ComponentBuilder")


class ComponentBuilderTest(TemplateBuilderTest):

    @classmethod
    def setUpClass(cls):
        cls._builder_type = _ComponentBuilder
        cls._definition_type = Component

    def test_register_dotted_name_from_object(self):
        self._builder.create(dotted_name=dummy.factory_function).register()
        self.assertEqual(
            "test.dummy.factory_function",
            self._builder._context["test.dummy.ModuleClass"].dotted_name)

    def test_register_prototype_by_default(self):
        self._builder.register()
        self.assertEqual(
            "prototype",
            self._builder._context["test.dummy.ModuleClass"].strategy)

    def test_register_prototype_explicit(self):
        self._builder.create(strategy="prototype").register()
        self.assertEqual(
            "prototype",
            self._builder._context["test.dummy.ModuleClass"].strategy)

    def test_register_singleton(self):
        self._builder.create(strategy="singleton").register()
        self.assertEqual(
            "singleton",
            self._builder._context["test.dummy.ModuleClass"].strategy)

    def test_register_borg(self):
        self._builder.create(strategy="borg").register()
        self.assertEqual(
            "borg", self._builder._context["test.dummy.ModuleClass"].strategy)

    def test_register_weakref(self):
        self._builder.create(strategy="weakref").register()
        self.assertEqual(
            "weakref",
            self._builder._context["test.dummy.ModuleClass"].strategy)


def suite():
    return unittest.makeSuite(ComponentBuilderTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

