# -*- coding: UTF-8 -*-

# Copyright (c) 2006, 2011, 2013-2016 Matthew Zipay.
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

__author__ = "Matthew Zipay <mattz@ninthtest.net>"

import logging
import unittest

from aglyph import AglyphError, __version__
from aglyph._compat import name_of
from aglyph.component import Component, Template
from aglyph.context import _ComponentBuilder, _TemplateBuilder, Context

from test import assertRaisesWithMessage, dummy

__all__ = [
    "ContextTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_Context")


class _BaseContextTest(unittest.TestCase):

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

    def test_component_returns_component_builder(self):
        builder = self._context.component("test")
        self.assertTrue(type(builder) is _ComponentBuilder)

    def test_component_registers_component(self):
        self._context.component("test")
        self.assertTrue(type(self._context["test"]) is Component)

    def test_component_registers_prototype_by_default(self):
        self._context.component("test")
        self.assertEqual("prototype", self._context["test"].strategy)

    def test_component_can_register_prototype(self):
        self._context.component("test", strategy="prototype")
        self.assertEqual("prototype", self._context["test"].strategy)

    def test_component_can_register_singleton(self):
        self._context.component("test", strategy="singleton")
        self.assertEqual("singleton", self._context["test"].strategy)

    def test_component_can_register_borg(self):
        self._context.component("test", strategy="borg")
        self.assertEqual("borg", self._context["test"].strategy)

    def test_component_can_register_weakref(self):
        self._context.component("test", strategy="weakref")
        self.assertEqual("weakref", self._context["test"].strategy)

    def test_component_fails_on_nonimportable_object(self):
        e_expected = AglyphError(
            "%r does not have an importable dotted name" %
                dummy.ModuleClass.NestedClass)
        assertRaisesWithMessage(
            self, e_expected, self._context.component,
            dummy.ModuleClass.NestedClass)

    def test_component_builds_dotted_name_from_object(self):
        self._context.component(dummy.ModuleClass)
        self.assertTrue("test.dummy.ModuleClass" in self._context)

    def test_prototype_returns_component_builder(self):
        builder = self._context.prototype("test")
        self.assertTrue(type(builder) is _ComponentBuilder)

    def test_prototype_registers_component(self):
        self._context.prototype("test")
        self.assertTrue(type(self._context["test"]) is Component)

    def test_prototype_builds_dotted_name_from_object(self):
        self._context.prototype(dummy.ModuleClass)
        self.assertTrue("test.dummy.ModuleClass" in self._context)

    def test_singleton_returns_component_builder(self):
        builder = self._context.singleton("test")
        self.assertTrue(type(builder) is _ComponentBuilder)

    def test_singleton_registers_component(self):
        self._context.singleton("test")
        self.assertTrue(type(self._context["test"]) is Component)

    def test_singleton_builds_dotted_name_from_object(self):
        self._context.singleton(dummy.ModuleClass)
        self.assertTrue("test.dummy.ModuleClass" in self._context)

    def test_borg_returns_component_builder(self):
        builder = self._context.borg("test")
        self.assertTrue(type(builder) is _ComponentBuilder)

    def test_borg_registers_component(self):
        self._context.borg("test")
        self.assertTrue(type(self._context["test"]) is Component)

    def test_borg_builds_dotted_name_from_object(self):
        component = self._context.borg(dummy.ModuleClass)
        self.assertTrue("test.dummy.ModuleClass" in self._context)

    def test_weakref_returns_component_builder(self):
        builder = self._context.weakref("test")
        self.assertTrue(type(builder) is _ComponentBuilder)

    def test_weakref_registers_component(self):
        self._context.weakref("test")
        self.assertTrue(type(self._context["test"]) is Component)

    def test_weakref_builds_dotted_name_from_object(self):
        component = self._context.weakref(dummy.ModuleClass)
        self.assertTrue("test.dummy.ModuleClass" in self._context)

    def test_template_returns_template_builder(self):
        builder = self._context.template("test")
        self.assertTrue(type(builder) is _TemplateBuilder)

    def test_template_registers_template(self):
        self._context.template("test")
        self.assertTrue(type(self._context["test"]) is Template)

    def test_template_fails_on_nonimportable_object(self):
        e_expected = AglyphError(
            "%r does not have an importable dotted name" %
                dummy.ModuleClass.NestedClass)
        assertRaisesWithMessage(
            self, e_expected, self._context.template,
            dummy.ModuleClass.NestedClass)

    def test_template_builds_dotted_name_from_object(self):
        self._context.template(dummy.ModuleClass)
        self.assertTrue("test.dummy.ModuleClass" in self._context)

    def test_register_fails_if_id_already_registered(self):
        test_component = Component("test")
        self._context.register(test_component)
        e_expected = AglyphError(
            "Component with ID %r already mapped in %s" %
                ("test", self._context))
        assertRaisesWithMessage(
            self, e_expected, self._context.register, test_component)

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

