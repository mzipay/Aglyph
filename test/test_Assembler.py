# -*- coding: UTF-8 -*-

# Copyright (c) 2006, 2011, 2013-2016 Matthew Zipay.
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

"""Test case and runner for :class:`aglyph.assembler.Assembler`."""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"

import logging
import unittest

try:
    import threading
    threading_ = threading
    _has_threading = True
except:
    import dummy_threading
    threading_ = dummy_threading
    _has_threading = False

from aglyph import __version__, AglyphError
from aglyph.assembler import Assembler
from aglyph._compat import is_python_2
from aglyph.context import Context, XMLContext

from test import assertRaisesWithMessage, dummy, find_basename

__all__ = [
    "AssemblerTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_Assembler")
_log.info("has threading? %r (using %r)", _has_threading, threading_)


class AssemblerTest(unittest.TestCase):

    def setUp(self):
        self._assembler = Assembler(
            XMLContext(find_basename("test_Assembler-context.xml")))

    def test_detects_circular_dependency(self):
        e = AglyphError(
            "circular dependency detected: "
            "circular-2 > circular-3 > circular-1 > circular-2")
        assertRaisesWithMessage(
            self, e, self._assembler.assemble, "circular-2")

    # https://github.com/mzipay/Aglyph/issues/3
    @unittest.skipUnless(
        _has_threading, "can't test thread safety without _thread")
    def test_circular_dependency_check_is_threadsafe(self):
        assemble = self._assembler.assemble
        class AssemblyThread(threading_.Thread):
            def run(self):
                try:
                    assemble("not-circular-1")
                except AglyphError as e:
                    self.e = e
                else:
                    self.e = None
        threads = [AssemblyThread() for i in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(0, len([t for t in threads if t.e is not None]))


def suite():
    return unittest.makeSuite(AssemblerTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

