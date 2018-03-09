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
:class:`aglyph._compat.AglyphDefaultXMLParser`.

"""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import logging
import unittest
import xml.etree.ElementTree as ET

from aglyph import __version__
from aglyph._compat import (
    AglyphDefaultXMLParser,
    CLRXMLParser,
    is_ironpython,
    TextType,
)

from test.test_CLRXMLParser import (
    _cp1252_document,
    _utf8_document,
    _u_motleycrue,
)

__all__ = [
    "AglyphDefaultXMLParserTest",
    "suite",
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_AglyphDefaultXMLParser")


class AglyphDefaultXMLParserTest(unittest.TestCase):

    @unittest.skipUnless(
        is_ironpython,
        "aglyph._compat.CLRXMLParser is only the default Aglyph XML parser "
        "when running under IronPython, and in that case is already tested in "
        "test.test_CLRXMLParser")
    def test_default_is_CLRXMLParser(self):
        self.assertTrue(AglyphDefaultXMLParser is CLRXMLParser)

    @unittest.skipIf(
        is_ironpython,
        "under IronPython, the default Aglyph XML parser is "
        "aglyph._compat.CLRXMLParser, which is already tested in "
        "test.test_CLRXMLParser")
    def test_parses_cp1252_document_correctly(self):
        root = ET.XML(_cp1252_document, parser=AglyphDefaultXMLParser())
        self._assert_parsed_document(root)

    @unittest.skipIf(
        is_ironpython,
        "under IronPython, the default Aglyph XML parser is "
        "aglyph._compat.CLRXMLParser, which is already tested in "
        "test.test_CLRXMLParser")
    def test_parses_utf8_document_correctly(self):
        root = ET.XML(_utf8_document, parser=AglyphDefaultXMLParser())
        self._assert_parsed_document(root)

    def _assert_parsed_document(self, root):
        self.assertEqual("band", root.tag)
        self.assertEqual("hair/glam metal", root.attrib["genre"])
        self.assertTrue(type(root.text) is TextType)
        self.assertEqual(_u_motleycrue, root.text)


def suite():
    return unittest.makeSuite(AglyphDefaultXMLParserTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

