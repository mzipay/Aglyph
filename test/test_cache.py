# -*- coding: UTF-8 -*-

# Copyright (c) 2006-2015 Matthew Zipay <mattz@ninthtest.net>
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

"""Test cases and runner for the :mod:`aglyph.cache` module."""

from __future__ import with_statement

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "2.1.0"

import logging
# do not use dummy_threading for testing! (let it fail)
import threading
import unittest

from aglyph.cache import MutexCache, ReentrantMutexCache

from test import enable_debug_logging

__all__ = [
    "MutexCacheTest",
    "ReentrantMutexCacheTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_logger = logging.getLogger("test.test_cache")


def _blocked(cache):
    with cache.lock:
        cache["test"] = "blocked"


class MutexCacheTest(unittest.TestCase):
    """Test the :class:`aglyph.cache.MutexCache` class."""

    def test_lock_is_blocking(self):
        cache = MutexCache()
        t = threading.Thread(target=_blocked, args=(cache,))
        with cache.lock:
            cache["test"] = "acquired"
            t.start()
            self.assertEqual("acquired", cache["test"])
        t.join(1)
        self.assertEqual("blocked", cache["test"])


class ReentrantMutexCacheTest(unittest.TestCase):
    """Test the :class:`aglyph.cache.ReentrantMutexCache` class."""

    def test_lock_is_nonblocking(self):
        cache = ReentrantMutexCache()
        t = threading.Thread(target=_blocked, args=(cache,))
        with cache.lock:
            t.start()
            cache["test"] = "acquired"
            # nested acquire
            with cache.lock:
                self.assertEqual("acquired", cache["test"])
                cache["test"] = "acquired again"
            self.assertEqual("acquired again", cache["test"])
        t.join(1)
        self.assertEqual("blocked", cache["test"])


def suite():
    """Build the test suite for the :mod:`aglyph.cache` module."""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MutexCacheTest))
    suite.addTest(unittest.makeSuite(ReentrantMutexCacheTest))
    _logger.debug("RETURN %r", suite)
    return suite


if (__name__ == "__main__"):
    enable_debug_logging(suite)
    unittest.TextTestRunner().run(suite())

