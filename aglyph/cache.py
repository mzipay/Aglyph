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

"""The classes in this module define mapping types that use lock objects
for synchronization.

Atomic "check-then-act" operations can be performed by acquiring the
cache lock, performing the check-then-act sequence, and finally
releasing the cache lock.

"""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "2.1.0"

import logging
import warnings

from aglyph import AglyphDeprecationWarning

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

    .. versionadded:: 2.1.0
       This class now acts as a `context manager
       <https://docs.python.org/3/library/stdtypes.html#typecontextmanager>`_
       using `the with statement
       <https://docs.python.org/3/reference/compound_stmts.html#with>`_

    """

    __logger = logging.getLogger("%s._LockingCache" % __name__)

    def __init__(self, lock):
        """Initialize an empty cache that uses *lock* for
        synchronization.

        """
        self.__logger.debug("TRACE %r", lock)
        super(_LockingCache, self).__init__()
        self.__lock = lock

    def __enter__(self):
        """Acquire the cache lock."""
        self.__lock.acquire()
        return self

    def __exit__(self, e_type, e_obj, tb):
        """Release the cache lock.

        :arg e_type: the exception class if an exception occurred while\
                     executing the body of the ``with`` statement, else\
                     ``None``
        :arg Exception e_value: the exception object if an exception\
                                occurred while executing the body of\
                                the ``with`` statement, else ``None``
        :arg tb: the traceback if an exception occurred while executing\
                 the body of the ``with`` statement, else ``None``

        .. note::
           If an exception occurred, it will be logged but allowed to
           propagate.

        """
        self.__lock.release()
        if (e_obj is not None):
            self.__logger.error(
                "exception occurred while cache lock was held: %s", str(e_obj))

    @property
    def lock(self):
        """a read-only property for the lock object

        .. deprecated:: 2.1.0::
           use ``with cache`` instead of ``with cache.lock``

        """
        warnings.warn(AglyphDeprecationWarning("_LockingCache.lock",
                                               replacement="'with cache:'"))
        return self.__lock

    def __repr__(self):
        return "%s.%s(%r)" % (self.__class__.__module__,
                              self.__class__.__name__, self.__lock)


class MutexCache(_LockingCache):
    """A mapping that uses a primitive lock to synchronize access.

    If the lock is held, any attempt to acquire it will block until the
    holding thread releases the lock.

    To use a mutex cache::

        cache = MutexCache()
        ...
        with cache:
            # check-then-act

    """

    __logger = logging.getLogger("%s.MutexCache" % __name__)

    def __init__(self):
        super(MutexCache, self).__init__(threading_.Lock())


class ReentrantMutexCache(_LockingCache):
    """A mapping that uses a reentrant lock to synchronize access.

    If the lock is held, any attempt to acquire it by a thread OTHER
    than the holding thread will block until the holding thread releases
    the lock. (A reentrant mutex permits the same thread to acquire the
    same lock more than once, allowing nested access to a shared
    resource by a single thread.)

    To use a re-entrant mutex cache::

        cache = ReentrantMutexCache()
        ...
        with cache:
            # check-then-act

    """

    __logger = logging.getLogger("%s.ReentrantMutexCache" % __name__)

    def __init__(self):
        super(ReentrantMutexCache, self).__init__(threading_.RLock())

