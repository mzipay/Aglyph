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

"""Test case and runner for :class:`aglyph._compat.DoctypeTreeBuilder`."""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import logging
import unittest
import xml.etree.ElementTree as ET

from aglyph import __version__
from aglyph._compat import (
    AglyphDefaultXMLParser,
    DoctypeTreeBuilder,
    is_ironpython,
    is_jython,
)

__all__ = [
    "DoctypeTreeBuilderTest",
    "suite",
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_DoctypeTreeBuilder")

_no_doctype_document = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n'
    '<test />\n'
)

_public_doctype_document = (
    '<?xml version="1.0" encoding="UTF-8" ?>\n'
    '<!DOCTYPE context PUBLIC \n'
        '"-//NinthTest.info//Aglyph context DTD//EN" \n'
        '"http://ninthtest.info/aglyph-python-dependency-injection/_downloads/aglyph-context.dtd">\n'
    '<context id="test" />\n'
)

_system_doctype_document = (
    '<?xml version="1.0" encoding="UTF-8" ?>\n'
    '<!DOCTYPE context SYSTEM "../resources/aglyph-context.dtd">\n'
    '<context id="test" />\n'
)


class DoctypeTreeBuilderTest(unittest.TestCase):

    def setUp(self):
        self._tree_builder = DoctypeTreeBuilder()
        self._parser = AglyphDefaultXMLParser(target=self._tree_builder)

    def test_doctype_name_is_read_only(self):
        self.assertRaises(
            AttributeError, setattr, self._tree_builder,
            "doctype_name", "test")

    def test_doctype_pubid_is_read_only(self):
        self.assertRaises(
            AttributeError, setattr, self._tree_builder,
            "doctype_pubid", "test")

    def test_doctype_system_is_read_only(self):
        self.assertRaises(
            AttributeError, setattr, self._tree_builder,
            "doctype_system", "test")

    def test_with_no_doctype(self):
        ET.XML(_no_doctype_document, parser=self._parser)
        self.assertIsNone(self._tree_builder.doctype_name)
        self.assertIsNone(self._tree_builder.doctype_pubid)
        self.assertIsNone(self._tree_builder.doctype_system)

    @unittest.skipIf(
        is_jython or is_ironpython,
        "the doctype() method is not called in the ET impl in Jython")
    def test_with_public_doctype(self):
        ET.XML(_public_doctype_document, parser=self._parser)
        self.assertEqual("context", self._tree_builder.doctype_name)
        self.assertEqual(
            "-//NinthTest.info//Aglyph context DTD//EN",
            self._tree_builder.doctype_pubid)
        self.assertEqual(
            "http://ninthtest.info/aglyph-python-dependency-injection/_downloads/aglyph-context.dtd",
            self._tree_builder.doctype_system)

    @unittest.skipIf(
        is_jython or is_ironpython,
        "the doctype() method is not called in the ET impl in Jython")
    def test_with_system_doctype(self):
        ET.XML(_system_doctype_document, parser=self._parser)
        self.assertEqual("context", self._tree_builder.doctype_name)
        self.assertIsNone(self._tree_builder.doctype_pubid)
        self.assertEqual(
            "../resources/aglyph-context.dtd",
            self._tree_builder.doctype_system)


def suite():
    return unittest.makeSuite(DoctypeTreeBuilderTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

