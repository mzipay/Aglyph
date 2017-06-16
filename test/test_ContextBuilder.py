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

"""Test case and runner for :class:`aglyph.context._ContextBuilder`."""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import logging
import unittest

from aglyph import __version__
from aglyph.context import _ComponentBuilder, _ContextBuilder, _TemplateBuilder

__all__ = [
    "ContextBuilderTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_ContextBuilder")


# Need to have register method for testing.
class _MockContextBuilder(dict, _ContextBuilder):

    def register(self, definition):
        if definition.unique_id in self:
            raise RuntimeError("duplicate ID %r" % definition.unique_id)
        self[definition.unique_id] = definition


class ContextBuilderTest(unittest.TestCase):

    def setUp(self):
        # use member name "_context"
        # (tests are inherited by test.test_Context._BaseContextTest)
        self._context = _MockContextBuilder()

    def test_component_returns_component_builder(self):
        builder = self._context.component("test")
        self.assertTrue(type(builder) is _ComponentBuilder)

    def test_prototype_returns_component_builder(self):
        builder = self._context.prototype("test")
        self.assertTrue(type(builder) is _ComponentBuilder)

    def test_singleton_returns_component_builder(self):
        builder = self._context.singleton("test")
        self.assertTrue(type(builder) is _ComponentBuilder)

    def test_borg_returns_component_builder(self):
        builder = self._context.borg("test")
        self.assertTrue(type(builder) is _ComponentBuilder)

    def test_weakref_returns_component_builder(self):
        builder = self._context.weakref("test")
        self.assertTrue(type(builder) is _ComponentBuilder)

    def test_template_returns_template_builder(self):
        builder = self._context.template("test")
        self.assertTrue(type(builder) is _TemplateBuilder)


def suite():
    return unittest.makeSuite(ContextBuilderTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

