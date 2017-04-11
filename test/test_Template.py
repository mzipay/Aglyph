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

"""Test case and runner for :class:`aglyph.component.Template`."""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import logging
import unittest

from aglyph import AglyphError, __version__
from aglyph._compat import name_of
from aglyph.component import Template

from test import assertRaisesWithMessage, dummy
from test.test_DependencySupport import DependencySupportTest

__all__ = [
    "TemplateTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_Template")


class TemplateTest(DependencySupportTest):

    def setUp(self):
        # for DependencySupportTest
        self._support = Template("test-template-depsupport")

    def test_unique_id_is_required(self):
        # use __class__ so test is reusable for Template & Component
        self.assertRaises(TypeError, self._support.__class__)

    def test_unique_id_cannot_be_None(self):
        # use __class__ so test is reusable for Template & Component
        e_expected = ValueError(
            "%s unique ID must not be None or empty" %
                name_of(self._support.__class__))
        assertRaisesWithMessage(
            self, e_expected, self._support.__class__, None)

    def test_unique_id_cannot_be_empty(self):
        # use __class__ so test is reusable for Template & Component
        e_expected = ValueError(
            "%s unique ID must not be None or empty" %
                name_of(self._support.__class__))
        assertRaisesWithMessage(
            self, e_expected, self._support.__class__, "")

    def test_unique_id_from_string(self):
        # use __class__ so test is reusable for Template & Component
        support = self._support.__class__("test")
        self.assertEqual("test", support.unique_id)

    def test_parent_id_is_none_by_default(self):
        self.assertIsNone(self._support.parent_id)

    def test_parent_id_from_string(self):
        # use __class__ so test is reusable for Template & Component
        support = self._support.__class__("test", parent_id="parent")
        self.assertEqual("parent", support.parent_id)

    def test_after_inject_is_none_by_default(self):
        self.assertIsNone(self._support.after_inject)

    def test_after_inject_at_init_time(self):
        # use __class__ so test is reusable for Template & Component
        support = self._support.__class__("test", after_inject="after_inject")
        self.assertEqual("after_inject", support.after_inject)

    def test_after_inject_is_read_only(self):
        self.assertRaises(
            AttributeError, setattr, self._support, "after_inject", "value")

    def test_before_clear_is_none_by_default(self):
        self.assertIsNone(self._support.before_clear)

    def test_before_clear_at_init_time(self):
        # use __class__ so test is reusable for Template & Component
        support = self._support.__class__("test", before_clear="before_clear")
        self.assertEqual("before_clear", support.before_clear)

    def test_before_clear_is_read_only(self):
        self.assertRaises(
            AttributeError, setattr, self._support, "before_clear", "value")


def suite():
    return unittest.makeSuite(TemplateTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

