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

"""Test case and runner for :class:`aglyph.component.Component`."""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import logging
import unittest
import warnings

from aglyph import AglyphError, __version__
from aglyph.component import Component

from test import assertRaisesWithMessage, dummy
from test.test_Template import TemplateTest

__all__ = [
    "ComponentTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_Component")


class ComponentTest(TemplateTest):

    def setUp(self):
        # for TemplateTest, DependencySupportTest
        self._support = Component("test-component-depsupport")

    def test_dotted_name_is_unique_id_by_default(self):
        self.assertEqual(
            "test-component-depsupport", self._support.dotted_name)

    def test_dotted_name_at_init_time(self):
        component = Component("test-class", dotted_name="test.dummy.Class")
        self.assertEqual("test.dummy.Class", component.dotted_name)

    def test_dotted_name_is_read_only(self):
        self.assertRaises(
            AttributeError, setattr, self._support, "dotted_name", "value")

    def test_factory_name_is_none_by_default(self):
        self.assertIsNone(self._support.factory_name)

    def test_factory_name_at_init_time(self):
        component = Component(
            "test-class", dotted_name="test.dummy", factory_name="ModuleClass")
        self.assertEqual("ModuleClass", component.factory_name)

    def test_factory_name_is_read_only(self):
        self.assertRaises(
            AttributeError, setattr, self._support, "factory_name", "value")

    def test_member_name_is_none_by_default(self):
        self.assertIsNone(self._support.member_name)

    def test_member_name_at_init_time(self):
        component = Component(
            "test-class", dotted_name="test.dummy", member_name="ModuleClass")
        self.assertEqual("ModuleClass", component.member_name)

    def test_member_name_is_read_only(self):
        self.assertRaises(
            AttributeError, setattr, self._support, "member_name", "value")

    def test_factory_name_and_member_name_are_mutually_exclusive(self):
        e_expected = AglyphError(
            "only one of factory_name or member_name may be specified")
        assertRaisesWithMessage(
            self, e_expected,
            Component, "test", factory_name="factory", member_name="member")

    def test_strategy_is_prototype_by_default(self):
        self.assertEqual("prototype", self._support.strategy)

    def test_strategy_is_imported_by_default_for_member_name(self):
        support = Component(
            "test.dummy.ModuleClass", member_name="NestedClass")
        self.assertEqual("_imported", support.strategy)

    def test_strategy_must_be_imported_for_member_name(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            component = Component(
                "test.dummy.ModuleClass",
                member_name="NestedClass", strategy="prototype")

            self.assertEqual(1, len(w))
            self.assertEqual(
                "ignoring strategy 'prototype' for component "
                    "'test.dummy.ModuleClass' -- strategy MUST be '_imported' "
                    "(implicit) if member_name is specified",
                str(w[0].message))

        self.assertEqual("_imported", component.strategy)

    def test_rejects_unrecognized_strategy(self):
        e_expected = ValueError(
            "unrecognized assembly strategy 'unrecognized'")
        assertRaisesWithMessage(
            self, e_expected, Component, "test", strategy="unrecognized")

    def test_strategy_explicit_prototype(self):
        component = Component("test", strategy="prototype")
        self.assertEqual("prototype", component.strategy)

    def test_strategy_singleton(self):
        component = Component("test", strategy="singleton")
        self.assertEqual("singleton", component.strategy)

    def test_strategy_borg(self):
        component = Component("test", strategy="borg")
        self.assertEqual("borg", component.strategy)

    def test_strategy_weakref(self):
        component = Component("test", strategy="weakref")
        self.assertEqual("weakref", component.strategy)

    # overrides TemplateTest.test_before_clear_at_init_time because
    # before_clear on a prototype component is set to None
    def test_before_clear_at_init_time(self):
        component = Component(
            "test", strategy="singleton", before_clear="before_clear")
        self.assertEqual("before_clear", component.before_clear)

    def test_before_clear_ignored_for_prototype(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            component = Component(
                "test", strategy="prototype", before_clear="before_clear")

            self.assertEqual(1, len(w))
            self.assertEqual(
                "ignoring before_clear='before_clear' for prototype component "
                "with ID 'test'",
                str(w[0].message))

        self.assertIsNone(component.before_clear)

    def test_singleton_accepts_before_clear(self):
        component = Component(
            "test", strategy="singleton", before_clear="before_clear")
        self.assertEqual("before_clear", component.before_clear)

    def test_borg_accepts_before_clear(self):
        component = Component(
            "test", strategy="borg", before_clear="before_clear")
        self.assertEqual("before_clear", component.before_clear)

    def test_weakref_accepts_before_clear(self):
        component = Component(
            "test", strategy="weakref", before_clear="before_clear")
        self.assertEqual("before_clear", component.before_clear)


def suite():
    return unittest.makeSuite(ComponentTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

