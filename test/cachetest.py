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

"""Test cases and runner for the :mod:`aglyph.cache` module."""

from __future__ import with_statement

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "1.0.0"

# do not use dummy_threading for testing! (let it fail)
import threading
import unittest

from aglyph.cache import MutexCache, ReentrantMutexCache

__all__ = ["get_suite", "PrimitiveCacheTest", "ReentrantCacheTest"]


def _blocked(cache):
    with cache.lock:
        cache["test"] = "blocked"


class PrimitiveCacheTest(unittest.TestCase):

    def test_lock_is_blocking(self):
        cache = MutexCache()
        t = threading.Thread(target=_blocked, args=(cache,))
        with cache.lock:
            cache["test"] = "acquired"
            t.start()
            self.assertEquals("acquired", cache["test"])
        t.join(1)
        self.assertEquals("blocked", cache["test"])


class ReentrantCacheTest(unittest.TestCase):

    def test_lock_is_nonblocking(self):
        cache = ReentrantMutexCache()
        t = threading.Thread(target=_blocked, args=(cache,))
        with cache.lock:
            t.start()
            cache["test"] = "acquired"
            # nested acquire
            with cache.lock:
                self.assertEquals("acquired", cache["test"])
                cache["test"] = "acquired again"
            self.assertEquals("acquired again", cache["test"])
        t.join(1)
        self.assertEquals("blocked", cache["test"])


def get_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PrimitiveCacheTest))
    suite.addTest(unittest.makeSuite(ReentrantCacheTest))
    return suite


if (__name__ == "__main__"):
    unittest.TextTestRunner().run(get_suite())
