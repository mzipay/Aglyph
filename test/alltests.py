# Copyright (c) 2006-2011 Matthew Zipay <mattz@ninthtest.net>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Test case runner for Aglyph."""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "1.0.0"

import sys
import unittest

__all__ = ["enable_debug_logging", "get_suite"]


def enable_debug_logging():
    import logging
    import os
    import tempfile
    filename = os.path.join(tempfile.gettempdir(), "aglyph-unittest.log")
    formatter = logging.Formatter("%(asctime)s %(levelname)s "
                                  "[%(name)s %(funcName)s] %(message)s")
    handler = logging.FileHandler(filename, 'w')
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    logger = logging.getLogger("aglyph")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return filename


def get_suite():
    import assemblertest
    import cachetest
    import componenttest
    import contexttest
    import functionstest
    suite = unittest.TestSuite()
    suite.addTest(functionstest.get_suite())
    suite.addTest(cachetest.get_suite())
    suite.addTest(componenttest.get_suite())
    suite.addTest(contexttest.get_suite())
    suite.addTest(assemblertest.get_suite())
    return suite


if (__name__ == "__main__"):
    if ("+logging" == sys.argv[-1]):
        sys.stderr.write("Logging to %s\n" % enable_debug_logging())
    unittest.TextTestRunner().run(get_suite())
