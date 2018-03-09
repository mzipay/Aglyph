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

"""Test case and runner for :class:`aglyph._compat.CLRXMLParser`."""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import codecs
import logging
import unittest
import xml.etree.ElementTree as ET

from aglyph import __version__
from aglyph._compat import CLRXMLParser, is_ironpython, TextType

from test import read_resource

__all__ = [
    "CLRXMLParserTest",
    "suite",
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_CLRXMLParser")

_cp1252_document = read_resource(
    "resources/cp1252_context.xml", to_encoding="windows-1252")
_utf8_document = read_resource(
    "resources/utf8_context.xml", to_encoding="utf-8")
_u_motleycrue = read_resource("resources/motleycrue.txt")


class CLRXMLParserTest(unittest.TestCase):

    @unittest.skipUnless(
        is_ironpython,
        "CRLXMLParser is only relevant when running under IronPython")
    def test_parses_cp1252_document_correctly(self):
        root = ET.XML(_cp1252_document, parser=CLRXMLParser())
        self._assert_parsed_document(root)

    @unittest.skipUnless(
        is_ironpython,
        "CRLXMLParser is only relevant when running under IronPython")
    def test_parses_utf8_document_correctly(self):
        root = ET.XML(_utf8_document, parser=CLRXMLParser())
        self._assert_parsed_document(root)

    def _assert_parsed_document(self, root):
        self.assertEqual("band", root.tag)
        self.assertEqual("hair/glam metal", root.attrib["genre"])
        self.assertTrue(type(root.text) is TextType)
        self.assertEqual(_u_motleycrue, root.text)

    @unittest.skipIf(
        is_ironpython,
        "CLRXMLParser is only a no-op when NOT running under IronPython")
    def test_not_usable_when_not_ironpython(self):
        self.assertRaises(RuntimeError, CLRXMLParser)


def suite():
    return unittest.makeSuite(CLRXMLParserTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

