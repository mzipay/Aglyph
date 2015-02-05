# -*- coding: UTF-8 -*-

# Copyright (c) 2006-2015 Matthew Zipay <mattz@ninthtest.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Test cases and runner for the :mod:`aglyph.binder` module."""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "2.1.0"

import functools
import logging
import struct
import unittest
import zipfile

from aglyph import AglyphError
from aglyph.binder import Binder, _DependencySupportProxy
from aglyph.component import Component, Reference, Strategy, Template

from test import enable_debug_logging
from test.bindertest_bindings import lifecycle_methods_binder
import test.dummy

__all__ = [
    "BinderTest",
    "BindingTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_logger = logging.getLogger("test.test_binder")

# PYVER: unittest.TestCase.assertIsNone is missing in Jython 2.5.3
if (not hasattr(unittest.TestCase, "assertIsNone")):
    def _assert_is_none(self, obj, msg=None):
        if (obj is not None):
            self.fail(msg if (msg is not None) else "%r is not None" % obj)
    unittest.TestCase.assertIsNone = _assert_is_none


class DependencySupportProxyTest(unittest.TestCase):
    """Test the :class:`aglyph.binder._DependencySupportProxy` class."""

    def setUp(self):
        if ("_binding_" in str(self)):
            self.depsupport = Component("test.dummy.Alpha")
        else:
            self.depsupport = Template("test-template")
        self.proxy = _DependencySupportProxy(self.depsupport)

    def tearDown(self):
        self.depsupport = None
        self.proxy = None

    def _test_init_chaining(self):
        self.assertTrue(self.proxy is self.proxy.init())

    test_binding_init_chaining = _test_init_chaining
    test_description_init_chaining = _test_init_chaining

    def _test_init_empty(self):
        self.assertEqual([], self.depsupport.args)
        self.assertEqual({}, self.depsupport.keywords)
        self.proxy.init()
        self.assertEqual([], self.depsupport.args)
        self.assertEqual({}, self.depsupport.keywords)

    test_binding_init_empty = _test_init_empty
    test_description_init_empty = _test_init_empty

    def _test_init_arg_class(self):
        # new-style class, old-style class
        self.proxy.init(test.dummy.Alpha, test.dummy.Gamma)
        self.assertTrue(self.depsupport.args[0].__class__ is Reference)
        self.assertEqual("test.dummy.Alpha", self.depsupport.args[0])
        self.assertTrue(self.depsupport.args[1].__class__ is Reference)
        self.assertEqual("test.dummy.Gamma", self.depsupport.args[1])

    test_binding_init_arg_class = _test_init_arg_class
    test_description_init_arg_class = _test_init_arg_class

    def _test_init_arg_func(self):
        self.proxy.init(test.dummy.create_alpha)
        self.assertTrue(self.depsupport.args[0].__class__ is Reference)
        self.assertEqual("test.dummy.create_alpha", self.depsupport.args[0])

    test_binding_init_arg_func = _test_init_arg_func
    test_description_init_arg_func = _test_init_arg_func

    def _test_init_arg_module(self):
        self.proxy.init(test.dummy)
        self.assertTrue(self.depsupport.args[0].__class__ is Reference)
        self.assertEqual("test.dummy", self.depsupport.args[0])

    test_binding_init_arg_module = _test_init_arg_module
    test_description_init_arg_module = _test_init_arg_module

    def _test_init_arg_value(self):
        self.proxy.init((2, 3, 5, 7))
        self.assertTrue(type(self.depsupport.args[0]) is tuple)
        self.assertEqual((2, 3, 5, 7), self.depsupport.args[0])

    test_binding_init_arg_value = _test_init_arg_value
    test_description_init_arg_value = _test_init_arg_value

    def _test_init_keyword_class(self):
        self.proxy.init(new_style=test.dummy.Alpha, old_style=test.dummy.Gamma)
        self.assertTrue(
            self.depsupport.keywords["new_style"].__class__ is Reference)
        self.assertEqual("test.dummy.Alpha",
                         self.depsupport.keywords["new_style"])
        self.assertTrue(
            self.depsupport.keywords["old_style"].__class__ is Reference)
        self.assertEqual("test.dummy.Gamma",
                         self.depsupport.keywords["old_style"])

    test_binding_init_keyword_class = _test_init_keyword_class
    test_description_init_keyword_class = _test_init_keyword_class

    def _test_init_keyword_func(self):
        self.proxy.init(function=test.dummy.create_alpha)
        self.assertTrue(
            self.depsupport.keywords["function"].__class__ is Reference)
        self.assertEqual("test.dummy.create_alpha",
                         self.depsupport.keywords["function"])

    test_binding_init_keyword_func = _test_init_keyword_func
    test_description_init_keyword_func = _test_init_keyword_func

    def _test_init_keyword_module(self):
        self.proxy.init(module=test.dummy)
        self.assertTrue(
            self.depsupport.keywords["module"].__class__ is Reference)
        self.assertEqual("test.dummy", self.depsupport.keywords["module"])

    test_binding_init_keyword_module = _test_init_keyword_module
    test_description_init_keyword_module = _test_init_keyword_module

    def _test_init_keyword_value(self):
        self.proxy.init(test=(2, 3, 5, 7))
        self.assertTrue(type(self.depsupport.keywords["test"]) is tuple)
        self.assertEqual((2, 3, 5, 7), self.depsupport.keywords["test"])

    test_binding_init_keyword_value = _test_init_keyword_value
    test_description_init_keyword_value = _test_init_keyword_value

    def _test_attributes_empty(self):
        self.assertEqual({}, self.depsupport.attributes)
        self.proxy.attributes()
        self.assertEqual({}, self.depsupport.attributes)

    test_binding_attributes_empty = _test_attributes_empty
    test_description_attributes_empty = _test_attributes_empty

    def _test_attributes_class(self):
        self.proxy.attributes(new_style=test.dummy.Alpha,
                              old_style=test.dummy.Gamma)
        self.assertTrue(
            self.depsupport.attributes["new_style"].__class__ is Reference)
        self.assertEqual("test.dummy.Alpha",
                         self.depsupport.attributes["new_style"])
        self.assertTrue(
            self.depsupport.attributes["old_style"].__class__ is Reference)
        self.assertEqual("test.dummy.Gamma",
                         self.depsupport.attributes["old_style"])

    test_binding_attributes_class = _test_attributes_class
    test_description_attributes_class = _test_attributes_class

    def _test_attributes_func(self):
        self.proxy.attributes(function=test.dummy.create_alpha)
        self.assertTrue(
            self.depsupport.attributes["function"].__class__ is Reference)
        self.assertEqual("test.dummy.create_alpha",
                         self.depsupport.attributes["function"])

    test_binding_attributes_func = _test_attributes_func
    test_description_attributes_func = _test_attributes_func

    def _test_attributes_module(self):
        self.proxy.attributes(module=test.dummy)
        self.assertTrue(
            self.depsupport.attributes["module"].__class__ is Reference)
        self.assertEqual("test.dummy", self.depsupport.attributes["module"])

    test_binding_attributes_module = _test_attributes_module
    test_description_attributes_module = _test_attributes_module

    def _test_attributes_value(self):
        self.proxy.attributes(test=(2, 3, 5, 7))
        self.assertTrue(type(self.depsupport.attributes["test"]) is tuple)
        self.assertEqual((2, 3, 5, 7), self.depsupport.attributes["test"])

    test_binding_attributes_value = _test_attributes_value
    test_description_attributes_value = _test_attributes_value

    def _test_attributes_nvpairs(self):
        self.proxy.attributes(("field", "FIELD"), ("set_value", "VALUE"))
        self.assertEqual(2, len(self.depsupport.attributes))
        self.assertEqual("FIELD", self.depsupport.attributes["field"])
        self.assertEqual("VALUE", self.depsupport.attributes["set_value"])

    test_binding_attributes_nvpairs = _test_attributes_nvpairs
    test_description_attributes_nvpairs = _test_attributes_nvpairs

    def _test_attributes_nvpairs_and_keywords(self):
        self.proxy.attributes(("field", "FIELD"), set_value="VALUE")
        self.assertEqual(2, len(self.depsupport.attributes))
        self.assertEqual("FIELD", self.depsupport.attributes["field"])
        self.assertEqual("VALUE", self.depsupport.attributes["set_value"])

    test_binding_attributes_nvpairs_and_keywords = \
        _test_attributes_nvpairs_and_keywords
    test_description_attributes_nvpairs_and_keywords = \
        _test_attributes_nvpairs_and_keywords


class BinderTest(unittest.TestCase):
    """Test the :class:`aglyph.binder.Binder` class."""

    def setUp(self):
        binder_id = str(self).split()[0]
        self.binder = Binder(binder_id)

    def tearDown(self):
        self.binder = None

    def test_init_after_inject(self):
        eta = lifecycle_methods_binder.lookup("context-after-inject")
        self.assertFalse(eta.called_after_inject_raise)
        self.assertTrue(eta.called_context_after_inject)
        self.assertFalse(eta.called_template_after_inject)
        self.assertFalse(eta.called_component_after_inject)

    def test_init_before_clear(self):
        eta = lifecycle_methods_binder.lookup("context-before-clear")
        self.assertFalse(eta.called_before_clear_raise)
        self.assertFalse(eta.called_context_before_clear)
        self.assertFalse(eta.called_template_before_clear)
        self.assertFalse(eta.called_component_before_clear)
        self.assertEqual(["context-before-clear"],
                         lifecycle_methods_binder.clear_singletons())
        self.assertFalse(eta.called_before_clear_raise)
        self.assertTrue(eta.called_context_before_clear)
        self.assertFalse(eta.called_template_before_clear)
        self.assertFalse(eta.called_component_before_clear)

    def test_bind_defaults(self):
        binding = self.binder.bind("test.dummy.Alpha")
        component = binding._depsupport
        self.assertEqual("test.dummy.Alpha", component.unique_id)
        self.assertEqual("test.dummy.Alpha", component.dotted_name)
        self.assertIsNone(component.factory_name)
        self.assertIsNone(component.member_name)
        self.assertEqual(Strategy.PROTOTYPE, component.strategy)
        self.assertIsNone(component.parent_id)
        self.assertIsNone(component.after_inject)
        self.assertIsNone(component.before_clear)
        self.assertEqual([], component.args)
        self.assertEqual({}, component.keywords)
        self.assertEqual({}, component.attributes)

    def test_bind_reference(self):
        binding = self.binder.bind(test.dummy.Alpha)
        component = binding._depsupport
        self.assertEqual("test.dummy.Alpha", component.unique_id)
        self.assertEqual("test.dummy.Alpha", component.dotted_name)

    def test_bind_to(self):
        binding = self.binder.bind("alpha", to="test.dummy.Alpha")
        component = binding._depsupport
        self.assertEqual("alpha", component.unique_id)
        self.assertEqual("test.dummy.Alpha", component.dotted_name)

    def test_bind_to_reference(self):
        binding = self.binder.bind("alpha", to=test.dummy.Alpha)
        component = binding._depsupport
        self.assertEqual("alpha", component.unique_id)
        self.assertEqual("test.dummy.Alpha", component.dotted_name)

    def test_bind_factory_member_mutually_exclusive(self):
        self.assertRaises(AglyphError, self.binder.bind, "test.dummy",
                          factory="Epsilon.Zeta", member="Epsilon.ATTRIBUTE")

    def test_bind_factory(self):
        binding = self.binder.bind("test.dummy", factory="Epsilon.Zeta")
        self.assertEqual("Epsilon.Zeta", binding._depsupport.factory_name)

    def test_bind_member(self):
        binding = self.binder.bind("test.dummy", member="Epsilon.ATTRIBUTE")
        self.assertEqual("Epsilon.ATTRIBUTE", binding._depsupport.member_name)

    def test_bind_bad_strategy(self):
        self.assertRaises(ValueError, self.binder.bind, "test.dummy.Alpha",
                          strategy="spam")

    def test_bind_explicit_prototype(self):
        binding = self.binder.bind("test.dummy.Alpha", strategy="prototype")
        self.assertEqual("prototype", binding._depsupport.strategy)

    def test_bind_strategy_singleton(self):
        binding = self.binder.bind("test.dummy.Alpha", strategy="singleton")
        self.assertEqual("singleton", binding._depsupport.strategy)

    def test_bind_strategy_borg(self):
        binding = self.binder.bind("test.dummy.Alpha", strategy="borg")
        self.assertEqual("borg", binding._depsupport.strategy)

    def test_bind_strategy_weakref(self):
        binding = self.binder.bind("test.dummy.Alpha", strategy="weakref")
        self.assertEqual("weakref", binding._depsupport.strategy)

    def test_bind_parent(self):
        binding = self.binder.bind("test.dummy.Alpha", parent="alpha-parent")
        self.assertEqual("alpha-parent", binding._depsupport.parent_id)

    def test_bind_parent_reference(self):
        binding = self.binder.bind("test.dummy.Gamma", parent=test.dummy.Alpha)
        self.assertEqual("test.dummy.Alpha", binding._depsupport.parent_id)

    def test_bind_after_inject(self):
        binding = self.binder.bind("test.dummy.Alpha",
                                   after_inject="component_after_inject")
        self.assertEqual("component_after_inject",
                         binding._depsupport.after_inject)

    def test_bind_prototype_rejects_before_clear(self):
        binding = self.binder.bind("test.dummy.Alpha",
                                   before_clear="component_before_clear")
        self.assertIsNone(binding._depsupport.before_clear)

    def test_bind_singleton_before_clear(self):
        binding = self.binder.bind("test.dummy.Alpha", strategy="singleton",
                                   before_clear="component_before_clear")
        self.assertEqual("component_before_clear",
                         binding._depsupport.before_clear)

    def test_bind_borg_before_clear(self):
        binding = self.binder.bind("test.dummy.Alpha", strategy="borg",
                                   before_clear="component_before_clear")
        self.assertEqual("component_before_clear",
                         binding._depsupport.before_clear)

    def test_bind_weakref_before_clear(self):
        binding = self.binder.bind("test.dummy.Alpha", strategy="weakref",
                                   before_clear="component_before_clear")
        self.assertEqual("component_before_clear",
                         binding._depsupport.before_clear)

    def test_describe_defaults(self):
        description = self.binder.describe("test")
        template = description._depsupport
        self.assertEqual("test", template.unique_id)
        self.assertIsNone(template.parent_id)
        self.assertIsNone(template.after_inject)
        self.assertIsNone(template.before_clear)
        self.assertEqual([], template.args)
        self.assertEqual({}, template.keywords)
        self.assertEqual({}, template.attributes)

    def test_describe_parent(self):
        description = self.binder.describe("test", parent="test-parent")
        self.assertEqual("test-parent", description._depsupport.parent_id)

    def test_describe_parent_reference(self):
        description = self.binder.describe("test", parent=test.dummy.Alpha)
        self.assertEqual("test.dummy.Alpha", description._depsupport.parent_id)

    def test_describe_after_inject(self):
        description = self.binder.describe(
            "test", after_inject="template_after_inject")
        self.assertEqual("template_after_inject",
                         description._depsupport.after_inject)

    def test_describe_before_clear(self):
        description = self.binder.describe(
            "test", before_clear="template_before_clear")
        self.assertEqual("template_before_clear",
                         description._depsupport.before_clear)


def suite():
    """Build the test suite for the :mod:`aglyph.binder` module."""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DependencySupportProxyTest))
    suite.addTest(unittest.makeSuite(BinderTest))
    _logger.debug("RETURN %r", suite)
    return suite


if (__name__ == "__main__"):
    enable_debug_logging(suite)
    unittest.TextTestRunner().run(suite())

