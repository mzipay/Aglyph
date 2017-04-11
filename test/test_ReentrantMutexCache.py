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
:class:`aglyph.assembler._ReentrantMutexCache`.

"""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

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

from aglyph import __version__
from aglyph.assembler import _ReentrantMutexCache

__all__ = [
    "ReentrantMutexCacheTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_ReentrantMutexCache")
_log.info("has threading? %r (using %r)", _has_threading, threading_)


def _blocked(cache):
    with cache:
        cache["test"] = "blocked"


class ReentrantMutexCacheTest(unittest.TestCase):

    def setUp(self):
        self._cache = _ReentrantMutexCache()

    def test_lock_can_be_acquired(self):
        with self._cache as cache:
            cache["test"] = "acquired"

        self.assertEqual("acquired", self._cache["test"])

    def test_does_not_block_same_thread(self):
        with self._cache as cache:
            cache["test"] = "acquired"
            # acquire again, same thread
            with cache:
                cache["test"] = "acquired again"

        self.assertEqual("acquired again", self._cache["test"])

    @unittest.skipUnless(_has_threading, "threading module is not available!")
    def test_blocks_other_thread(self):
        cache = self._cache
        t = threading_.Thread(target=_blocked, args=(cache,))
        with cache:
            cache["test"] = "acquired"
            t.start()
            self.assertEqual("acquired", cache["test"])
            # acquire again, same thread
            with cache:
                cache["test"] = "acquired again"
                self.assertEqual("acquired again", cache["test"])
        t.join(1)
        self.assertEqual("blocked", cache["test"])


def suite():
    return unittest.makeSuite(ReentrantMutexCacheTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

