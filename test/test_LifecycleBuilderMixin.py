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
:class:`aglyph.context._LifecycleBuilderMixin`.

"""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import logging
import unittest

from aglyph import __version__
from aglyph.context import _LifecycleBuilderMixin

__all__ = [
    "LifecycleBuilderMixinTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_LifecycleBuilderMixin")


# Need to define the slots in order to test
class _MockLifecycleBuilderMixin(_LifecycleBuilderMixin):

    __slots__ = [
        "_after_inject",
        "_before_clear",
    ]

    def __init__(self):
        self._after_inject = None
        self._before_clear = None


class _BaseLifecycleBuilderMixinTest(unittest.TestCase):

    def test_can_set_attributes_with_one_call(self):
        self._builder.call(
            after_inject="after_inject", before_clear="before_clear")
        self.assertEqual("after_inject", self._builder._after_inject)
        self.assertEqual("before_clear", self._builder._before_clear)

    def test_can_set_attributes_with_chained_calls(self):
        # NOTE: this also indirectly asserts that None default values do not
        # "overwrite" previously-specified, non-None values in chained calls
        (self._builder.
            call(after_inject="after_inject").
            call(before_clear="before_clear"))
        self.assertEqual("after_inject", self._builder._after_inject)
        self.assertEqual("before_clear", self._builder._before_clear)


class LifecycleBuilderMixinTest(_BaseLifecycleBuilderMixinTest):

    def setUp(self):
        self._builder = _MockLifecycleBuilderMixin()


def suite():
    return unittest.makeSuite(LifecycleBuilderMixinTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

