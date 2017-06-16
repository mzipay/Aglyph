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

"""Test case and runner for
:class:`aglyph.context._InjectionBuilderMixin`.

"""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

from collections import OrderedDict
import logging
import unittest

from aglyph import __version__
from aglyph.context import _InjectionBuilderMixin

__all__ = [
    "InjectionBuilderMixinTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_InjectionBuilderMixin")


# Need to define the slots in order to test
class _MockInjectionBuilderMixin(_InjectionBuilderMixin):

    __slots__ = [
        "_args",
        "_keywords",
        "_attributes",
    ]

    def __init__(self):
        self._args = []
        self._keywords = {}
        self._attributes = OrderedDict()


class InjectionBuilderMixinTest(unittest.TestCase):

    def setUp(self):
        self._builder = _MockInjectionBuilderMixin()

    def test_can_set_init_attributes_with_one_call(self):
        self._builder.init("arg", keyword="keyword")
        self.assertEqual(["arg"], self._builder._args)
        self.assertEqual({"keyword": "keyword"}, self._builder._keywords)
        self.assertEqual({}, self._builder._attributes)

    def test_can_set_init_attributes_with_chained_calls(self):
        (self._builder.
            init("arg").
            init(keyword="keyword"))
        self.assertEqual(["arg"], self._builder._args)
        self.assertEqual({"keyword": "keyword"}, self._builder._keywords)
        self.assertEqual({}, self._builder._attributes)

    def test_init_args_are_cumulative(self):
        (self._builder.
            init("arg1", "arg2").
            init("arg3"))
        self.assertEqual(["arg1", "arg2", "arg3"], self._builder._args)
        self.assertEqual({}, self._builder._keywords)
        self.assertEqual({}, self._builder._attributes)

    def test_init_keywords_are_cumulative(self):
        (self._builder.
            init(keyword1="kw1", keyword2="kw2").
            init(keyword3="kw3"))
        self.assertEqual([], self._builder._args)
        self.assertEqual(
            {"keyword1": "kw1", "keyword2": "kw2", "keyword3": "kw3"},
            self._builder._keywords)
        self.assertEqual({}, self._builder._attributes)

    def test_init_keywords_are_replaceable(self):
        (self._builder.
            init(keyword="original").
            init(keyword="replaced"))
        self.assertEqual([], self._builder._args)
        self.assertEqual({"keyword": "replaced"}, self._builder._keywords)
        self.assertEqual({}, self._builder._attributes)

    def test_can_set_attributes_with_one_call(self):
        self._builder.set(prop="value1", attr="value2")
        self.assertEqual([], self._builder._args)
        self.assertEqual({}, self._builder._keywords)
        self.assertEqual(
            {"prop": "value1", "attr": "value2"}, self._builder._attributes)

    def test_can_set_attributes_with_chained_calls(self):
        (self._builder.
            set(prop="value1").
            set(attr="value2"))
        self.assertEqual([], self._builder._args)
        self.assertEqual({}, self._builder._keywords)
        self.assertEqual(
            {"prop": "value1", "attr": "value2"}, self._builder._attributes)

    def test_can_set_attributes_as_pairs_or_keywords(self):
        self._builder.set(
            ("prop", "value1"), ("attr", "value2"), set_value="value3")
        self.assertEqual([], self._builder._args)
        self.assertEqual({}, self._builder._keywords)
        self.assertEqual(
            {"prop": "value1", "attr": "value2", "set_value": "value3"},
            self._builder._attributes)

    def test_attributes_are_replaceable(self):
        self._builder.set(prop="value1", attr="value2").set(prop="value3")
        self.assertEqual([], self._builder._args)
        self.assertEqual({}, self._builder._keywords)
        self.assertEqual(
            {"prop": "value3", "attr": "value2"}, self._builder._attributes)


def suite():
    return unittest.makeSuite(InjectionBuilderMixinTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

