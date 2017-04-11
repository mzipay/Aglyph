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
:class:`aglyph.component._InitializationSupport`.

"""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import logging
import unittest

from aglyph import __version__
from aglyph.component import _InitializationSupport

__all__ = [
    "InitializationSupportTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_InitializationSupport")


class InitializationSupportTest(unittest.TestCase):

    def setUp(self):
        self._support = _InitializationSupport()

    def test_args_initialized_empty(self):
        self.assertEqual([], self._support.args)

    def test_args_is_read_only(self):
        self.assertRaises(AttributeError, setattr, self._support, "args", None)

    def test_can_modify_args_by_reference(self):
        self._support.args.append("test")
        self._support.args.extend([None, "value"])
        self._support.args.insert(2, 79)
        del self._support.args[1]
        self.assertEqual(["test", 79, "value"], self._support.args)

    def test_keywords_initialized_empty(self):
        self.assertEqual({}, self._support.keywords)

    def test_keywords_is_read_only(self):
        self.assertRaises(
            AttributeError, setattr, self._support, "keywords", None)

    def test_can_modify_keywords_by_reference(self):
        self._support.keywords["test"] = "value"
        self._support.keywords.update(
            {"test": "value2", "number": 79, "key": None})
        del self._support.keywords["key"]

        self.assertEqual(
            {"test": "value2", "number": 79}, self._support.keywords)


def suite():
    return unittest.makeSuite(InitializationSupportTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

