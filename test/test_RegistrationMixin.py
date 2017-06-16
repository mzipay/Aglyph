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
:class:`aglyph.context._RegistrationMixin`.

"""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

from collections import OrderedDict
import logging
import unittest

from aglyph import __version__
from aglyph.context import _RegistrationMixin

__all__ = [
    "RegistrationMixinTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_RegistrationMixin")


class _MockComponent(object):

    def __init__(self, unique_id):
        self.unique_id = unique_id


class _MockContext(dict):

    def register(self, definition):
        if definition.unique_id in self:
            raise RuntimeError("duplicate ID %r" % definition.unique_id)
        self[definition.unique_id] = definition


# Need to define the slots in order to test
class _MockRegistrationMixin(_RegistrationMixin):

    __slots__ = [
        "_context",
        "_unique_id_spec",
        "_args",
        "_keywords",
        "_attributes",
    ]

    def __init__(self, context):
        self._context = context
        self._unique_id_spec = None
        self._args = []
        self._keywords = {}
        self._attributes = OrderedDict()

    def _init_definition(self):
         return _MockComponent(self._unique_id_spec)


class RegistrationMixinTest(unittest.TestCase):

    def setUp(self):
        self._builder = _MockRegistrationMixin(_MockContext())

    def test_definition_is_registered_in_context(self):
        self._builder._unique_id_spec = "test"
        self._builder._args.append("test")
        self._builder._keywords["keyword"] = "test"
        self._builder._attributes["prop"] = "test"

        self._builder.register()

        definition = self._builder._context["test"]
        self.assertEqual(["test"], definition._args)
        self.assertEqual({"keyword": "test"}, definition._keywords)
        self.assertEqual({"prop": "test"}, definition._attributes)

    def test_register_terminates_fluent_call_sequence(self):
        self.assertIsNone(self._builder.register())


def suite():
    return unittest.makeSuite(RegistrationMixinTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

