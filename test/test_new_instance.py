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

"""Test case and runner for :func:`aglyph._compat.new_instance`."""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import logging
import types
import unittest

from aglyph import __version__
from aglyph._compat import is_python_2, new_instance

from test.dummy import ModuleClass

__all__ = [
    "NewInstanceTest",
    "suite",
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_new_instance")


#PYVER: Under Python 3, this implicitly extends object anyway
class OldStyleClass:
    pass


class NewInstanceTest(unittest.TestCase):
    """Test the :func:`aglyph._compat.new_instance` function."""

    def test_derived_from_object(self):
        obj = new_instance(ModuleClass)
        self.assertTrue(type(obj) is ModuleClass)

    @unittest.skipUnless(
        is_python_2, "only test old-style classes under Python 2")
    def test_not_derived_from_object(self):
        obj = new_instance(OldStyleClass)
        #PYVER: types.InstanceType is not defined in Python 3
        self.assertTrue(type(obj) is types.InstanceType)


def suite():
    return unittest.makeSuite(NewInstanceTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

