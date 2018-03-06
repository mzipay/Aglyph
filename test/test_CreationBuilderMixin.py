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
:class:`aglyph.context._CreationBuilderMixin`.

"""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import logging
import unittest

from aglyph import __version__
from aglyph.context import _CreationBuilderMixin

__all__ = [
    "CreationBuilderMixinTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_CreationBuilderMixin")


# Need to define the slots in order to test
class _MockCreationBuilderMixin(_CreationBuilderMixin):

    __slots__ = [
        "_dotted_name_spec",
        "_factory_name",
        "_member_name",
        "_strategy",
    ]

    def __init__(self):
        self._dotted_name_spec = None
        self._factory_name = None
        self._member_name = None
        self._strategy = None


class CreationBuilderMixinTest(unittest.TestCase):

    def setUp(self):
        self._builder = _MockCreationBuilderMixin()

    def test_can_set_attributes_in_one_call(self):
        self._builder.create(
            dotted_name="dummy.ModuleClass", strategy="prototype")
        self.assertEqual("dummy.ModuleClass", self._builder._dotted_name_spec)
        self.assertIsNone(self._builder._factory_name)
        self.assertIsNone(self._builder._member_name)
        self.assertEqual("prototype", self._builder._strategy)

    def test_can_set_attributes_in_one_call_with_factory(self):
        # NOTE: specifying both factory AND member_name is not a valid
        # case, as this would be raised later as an error by
        # aglyph.component.Component
        self._builder.create(
            dotted_name="dummy", factory="factory_function",
            strategy="prototype")
        self.assertEqual("dummy", self._builder._dotted_name_spec)
        self.assertEqual("factory_function", self._builder._factory_name)
        self.assertIsNone(self._builder._member_name)
        self.assertEqual("prototype", self._builder._strategy)

    def test_can_set_attributes_in_one_call_with_member(self):
        # NOTE: specifying both factory AND member_name is not a valid
        # case, as this would be raised later as an error by
        # aglyph.component.Component; also, the strategy when member_name is
        # specified will ALWAYS be "_imported" (also enforced by
        # aglyph.component.Component)
        self._builder.create(dotted_name="dummy", member="MODULE_MEMBER")
        self.assertEqual("dummy", self._builder._dotted_name_spec)
        self.assertEqual("MODULE_MEMBER", self._builder._member_name)
        self.assertIsNone(self._builder._factory_name)
        self.assertIsNone(self._builder._strategy)

    def test_can_set_attributes_with_chained_calls(self):
        # NOTE: this also indirectly asserts that None default values do not
        # "overwrite" previously-specified, non-None values in chained calls
        (self._builder.
            create(dotted_name="dummy").
            create(strategy="prototype").
            create(factory="factory_function"))
        self.assertEqual("dummy", self._builder._dotted_name_spec)
        self.assertEqual("factory_function", self._builder._factory_name)
        self.assertIsNone(self._builder._member_name)
        self.assertEqual("prototype", self._builder._strategy)


def suite():
    return unittest.makeSuite(CreationBuilderMixinTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

