# -*- coding: utf-8 -*-

# Copyright (c) 2006-2013 Matthew Zipay <mattz@ninthtest.net>
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

"""Utility functions and classes for all unit test modules."""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "1.1.1"

from functools import wraps
import inspect
import logging
import os
import sys
import unittest

__all__ = [
    "additional_tests",
    "enable_debug_logging",
    "find_basename",
    "skip_if",
]

_logger = logging.getLogger(__name__)

try:
    skip_if = unittest.skipIf
except AttributeError:
    # PYVER: unittest.skipIf is not available in all versions of Python
    def skip_if(condition, reason):
        if (condition):
            def decorator(test_obj):
                @wraps(test_obj)
                def skip_wrapper(*args, **kwargs):
                    sys.stderr.write("\nSKIPPED %s (%s)\n" %
                                     (test_obj.__name__, reason))
                return skip_wrapper
            return decorator
        else:
            return lambda obj: obj


def enable_debug_logging(suite):
    """Log *DEBUG* and above to a file.

    The logging filename is determined by taking the source filename of
    the *suite* function and replacing the ".py" extension with a ".log"
    extension.

    The log file is always overwritten (i.e. it is opened in 'w' mode).

    """
    py_filename = os.path.abspath(inspect.getsourcefile(suite))
    log_filename = os.path.splitext(py_filename)[0] + ".log"
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s %(funcName)s %(message)s",
        filename=log_filename,
        filemode='w'
    )
    _logger.debug("RETURN %r", log_filename)
    return log_filename


def find_basename(basename):
    """Locate *basename* relative to the ``test`` package."""
    init_filename = inspect.getsourcefile(find_basename)
    return os.path.join(os.path.dirname(init_filename), basename)