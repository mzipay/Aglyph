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

"""Test case and runner for :class:`aglyph.context.Context`."""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import logging
import unittest

from aglyph import AglyphError, __version__
from aglyph._compat import name_of
from aglyph.component import Component, Strategy, Template
from aglyph.context import _ComponentBuilder, _TemplateBuilder, Context

from test import assertRaisesWithMessage, dummy
from test.test_ContextBuilder import ContextBuilderTest

__all__ = [
    "ContextTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_Context")


class _BaseContextTest(ContextBuilderTest):

    def test_context_id_cannot_be_none(self):
        e_expected = AglyphError(
            "%s ID must not be None or empty" %
                name_of(self._context.__class__))
        assertRaisesWithMessage(
            self, e_expected, self._context.__class__, None)

    def test_context_id_cannot_be_empty(self):
        e_expected = AglyphError(
            "%s ID must not be None or empty" %
                name_of(self._context.__class__))
        assertRaisesWithMessage(self, e_expected, self._context.__class__, "")

    def test_register_rejects_duplicate_id(self):
        self._context["test"] = Component("test")
        self.assertRaises(
            AglyphError, self._context.register, Component("test"))

    def test_get_component_returns_component(self):
        test_component = Component("test")
        self._context["test"] = test_component
        self.assertTrue(self._context.get_component("test") is test_component)

    def test_get_component_does_not_return_noncomponent(self):
        test_template = Template("test")
        self._context["test"] = test_template
        self.assertIsNone(self._context.get_component("test"))

    def test_iter_components_yields_only_components(self):
        test_template = Template("test-template")
        self._context.register(test_template)
        test_component = Component("test-component")
        self._context.register(test_component)
        self.assertEqual(
            [test_component], list(self._context.iter_components()))

    def test_prototype_implicit_strategy(self):
        (self._context.component("myObject").
            create(dummy.ModuleClass).init(None).register())
        self.assertEqual("prototype", self._context["myObject"].strategy)

    def test_prototype_explicit_strategy(self):
        (self._context.component("myObject").
            create(dummy.ModuleClass, strategy="prototype").init(None).
            register())
        self.assertEqual("prototype", self._context["myObject"].strategy)

    def test_imported_implicit_strategy(self):
        (self._context.component("NestedClass").
            create(dummy.ModuleClass, member="NestedClass").
            init(None).register())
        self.assertEqual("_imported", self._context["NestedClass"].strategy)

    def test_imported_explicit_strategy(self):
        (self._context.component("NestedClass").
            create(
                dummy.ModuleClass, member="NestedClass", strategy="_imported").
            init(None).register())
        self.assertEqual("_imported", self._context["NestedClass"].strategy)


class ContextTest(_BaseContextTest):

    def setUp(self):
        self._context = Context("test")

    def test_context_id_required(self):
        self.assertRaises(TypeError, Context)

    def test_after_inject_at_init_time(self):
        context = Context("test", after_inject="after_inject")
        self.assertEqual("after_inject", context.after_inject)

    def test_before_clear_at_init_time(self):
        context = Context("test", before_clear="before_clear")
        self.assertEqual("before_clear", context.before_clear)


def suite():
    return unittest.makeSuite(ContextTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

