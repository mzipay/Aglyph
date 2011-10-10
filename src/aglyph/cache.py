# The MIT License (MIT)
#
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

"""The classes in this module define mapping types that use lock objects
for synchronization.

Atomic "check-then-act" operations can be performed by acquiring the
cache lock, performing the check-then-act sequence, and finally
releasing the cache lock.

"""

from __future__ import with_statement

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "1.0.0"

import logging
try:
    import threading
    threading_ = threading
except ImportError:
    import dummy_threading
    threading_ = dummy_threading

__all__ = ["MutexCache", "ReentrantMutexCache"]

_logger = logging.getLogger(__name__)
_logger.debug("using %r", threading_)


class _LockingCache(dict):
    """A mapping that uses a lock object for synchronization.

    Atomic "check-then-act" operations can be performed by
    acquiring the cache lock, performing the check-then-act sequence,
    and finally releasing the cache lock.

    This class should not be used directly; instead, a subclass should
    provide the desired type of lock (e.g. :func:`threading.Lock` or
    :func:`threading.RLock`).

    """

    _logger = logging.getLogger("%s._LockingCache" % __name__)

    def __init__(self, lock):
        """Initialize an empty cache that uses *lock* for
        synchronization.

        """
        super(_LockingCache, self).__init__()
        self.__lock = lock

    @property
    def lock(self):
        """a read-only property for the lock object"""
        return self.__lock

    def __repr__(self):
        return "%s:%s<%r>" % (self.__class__.__module__,
                              self.__class__.__name__, self.__lock)


class MutexCache(_LockingCache):
    """A mapping that uses a primitive lock to synchronize access.

    If the lock is held, any attempt to acquire it will block until the
    holding thread releases the lock.

    >>> cache = MutexCache()
    >>> cache.lock.locked()
    False
    >>> with cache.lock:
    ...     cache.lock.locked()
    ...
    True
    >>> cache.lock.locked()
    False

    """

    _logger = logging.getLogger("%s.MutexCache" % __name__)

    def __init__(self):
        super(MutexCache, self).__init__(threading_.Lock())


class ReentrantMutexCache(_LockingCache):
    """A mapping that uses a reentrant lock to synchronize access.

    If the lock is held, any attempt to acquire it by a thread OTHER
    than the holding thread will block until the holding thread releases
    the lock. (A reentrant mutex permits the same thread to acquire the
    same lock more than once, allowing nested access to a shared
    resource by a single thread.)

    >>> cache = ReentrantMutexCache()
    >>> cache.lock._count
    0
    >>> with cache.lock:
    ...     cache.lock._count
    ...     with cache.lock:
    ...         cache.lock._count
    ... 
    1
    2
    >>> cache.lock._count
    0

    """

    _logger = logging.getLogger("%s.ReentrantMutexCache" % __name__)

    def __init__(self):
        super(ReentrantMutexCache, self).__init__(threading_.RLock())
