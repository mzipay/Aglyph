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
:class:`aglyph.component._DependencySupport`.

"""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

from collections import OrderedDict
import logging
import unittest

from aglyph import __version__
from aglyph.component import _DependencySupport

from test.test_InitializationSupport import InitializationSupportTest

__all__ = [
    "DependencySupportTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_DependencySupport")


class DependencySupportTest(InitializationSupportTest):

    def setUp(self):
        # for InitializationSupportTest
        self._support = _DependencySupport()

    def test_attributes_initialized_empty(self):
        self.assertEqual({}, self._support.attributes)

    def test_attributes_is_read_only(self):
        self.assertRaises(
            AttributeError, setattr, self._support, "attributes", None)

    def test_can_modify_attributes_by_reference(self):
        self._support.attributes["test"] = "value"
        self._support.attributes.update(
            {"test": "value2", "number": 79, "key": None})
        del self._support.attributes["key"]

        self.assertEqual(
            {"test": "value2", "number": 79}, self._support.attributes)

    def test_dependency_attribute_order_is_maintained(self):
        for key in "abcxyz":
            self._support.attributes[key] = None

        #PYVER: use list(keys()) since keys() returns a view in Python 3
        self.assertEqual(
            ['a', 'b', 'c', 'x', 'y', 'z'],
            list(self._support.attributes.keys()))


def suite():
    return unittest.makeSuite(DependencySupportTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

