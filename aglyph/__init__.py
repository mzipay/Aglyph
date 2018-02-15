# -*- coding: UTF-8 -*-

# Copyright (c) 2006, 2011, 2013-2018 Matthew Zipay.
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

"""This module defines a custom error type and several utility functions
used by Aglyph.

.. note::
   Aglyph uses the standard :mod:`logging` module, but by default
   registers a :class:`logging.NullHandler` to suppress messages.

   To enable Aglyph logging, configure a logger and handler for the
   *"aglyph"* log channel (see :mod:`logging.config`).


.. note::
   .. versionadded:: 3.0.0

   Aglyph framework functions and methods are fully traced using
   `Autologging <http://ninthtest.info/python-autologging/>`_. However,
   all tracing is **deactivated** by default.

   To activate tracing:

   1. Configure a logger and handler for the *"aglyph"* log channel and
      set the logging level to :attr:`autologging.TRACE`.
   2. Run Aglyph with the *AGLYPH_TRACED* environment variable set to a
      **non-empty** value.

"""

from collections import namedtuple

# see https://semver.org/
version_info = namedtuple(
    "version_info", ["major", "minor", "patch", "pre_release", "metadata"])(
        3, 0, 0, "", "")

__author__ = "Matthew Zipay <mattz@ninthtest.info>"
__version__ = "%d.%d.%d%s%s" % version_info

from inspect import ismodule
import logging
import os
import sys

import autologging
if not os.getenv("AGLYPH_TRACED"):
    autologging.install_traced_noop()

from autologging import traced

__all__ = [
    "version_info",
    "AglyphError",
    "format_dotted_name",
    "resolve_dotted_name",
]

# configure a logging for the "aglyph" channel to see log output
_log = logging.getLogger(__name__)

# prevent messages to the console when there's no logging configuration
# (see https://docs.python.org/3/howto/logging.html#library-config)
if not _log.handlers:
    _log.addHandler(logging.NullHandler())

# log the Aglyph and Python versions, the platform, and compatibility details
from aglyph._compat import is_string, name_of, platform_detail
_log.info("Aglyph %s on %s", __version__, platform_detail)


class AglyphDeprecationWarning(DeprecationWarning):
    """Issued when deprecated Aglyph functions, classes, or methods are
    used.

    """

    def __init__(self, name, replacement=None):
        """
        :arg str name:
           the name of the deprecated function, class, or method
        :keyword str replacement:
           the name of the replacement function, class, or method

        """
        message = (
            "%s is deprecated and will be removed in release %d.0.0." %
                (name, MAJOR + 1))
        if replacement is not None:
            message = "%s Use %s instead." % (message, replacement)
        #PYVER: arguments to super() are implicit under Python 3
        super(AglyphDeprecationWarning, self).__init__(message)


class AglyphError(Exception):
    """Raised when Aglyph operations fail with a condition that is not
    sufficiently described by a built-in exception.

    """

    def __init__(self, message, cause=None):
        #PYVER: arguments to super() are implicit under Python 3
        super(AglyphError, self).__init__(message)
        self.cause = cause


@traced
def format_dotted_name(obj):
    """Return the importable dotted-name string for *obj*.

    :param obj:
       an **importable** class, function, or module
    :return:
       a dotted name representing *obj*
    :rtype:
       :obj:`str`
    :raise AglyphError:
       if *obj* does not have a resolvable (importable) dotted name

    The dotted name returned by this function is a *"dotted_name.NAME"*
    or *"dotted_name"* string for *obj* that represents a valid absolute
    import statement according to the following productions:

    .. productionlist::
       absolute_import_stmt: "from" dotted_name "import" NAME
                           : | "import" dotted_name
       dotted_name: NAME ('.' NAME)*

    .. note::
       This function is the inverse of :func:`resolve_dotted_name`.

    .. warning::
       This function will attempt to use the ``__qualname__`` attribute,
       which is only available in Python 3.3+. When ``__qualname__`` is
       **not** available, ``__name__`` is used instead.

       .. seealso:: :pep:`3155`, :func:`aglyph._compat.name_of`

    """
    if not _importable(obj):
        raise AglyphError("%r does not have an importable dotted name" % obj)

    if not ismodule(obj):
        return "%s.%s" % (obj.__module__, name_of(obj))
    else:
        return obj.__name__


@traced
def _importable(obj):
    """Tell whether or not *obj* is directly importable.

    :arg obj:
       any object
    :rtype:
       :obj:`bool`

    If *obj* is importable, then:

    >>> resolve_dotted_name(format_dotted_name(obj)) is obj
    True

    """
    if ismodule(obj):
        return True
    elif hasattr(obj, "__module__") and hasattr(obj, "__name__"):
        return obj.__name__ in sys.modules[obj.__module__].__dict__
    else:
        return False


@traced
def resolve_dotted_name(dotted_name):
    """Return the class, function, or module identified by
    *dotted_name*.

    :param str dotted_name:
       a string representing an **importable** class, function, or
       module
    :return:
       a class, function, or module

    *dotted_name* must be a "dotted_name.NAME" or "dotted_name"
    string that represents a valid absolute import statement according
    to the following productions:

    .. productionlist::
       absolute_import_stmt: "from" dotted_name "import" NAME
                           : | "import" dotted_name
       dotted_name: NAME ('.' NAME)*

    .. note::
       This function is the inverse of :func:`format_dotted_name`.

    """
    if '.' in dotted_name:
        (module_name, name) = dotted_name.rsplit('.', 1)
        module = __import__(module_name, fromlist=[name], level=0)
        obj = getattr(module, name)
    else:
        obj = __import__(dotted_name, level=0)

    return obj


@traced
def _identify(spec):
    """Determine the unique ID for *spec*.

    :arg spec:
       an **importable** class, function, or module; or a :obj:`str`
    :return:
       *spec* unchanged (if it is a :obj:`str`), else *spec*'s
       importable dotted name
    :rtype:
       :obj:`str`

    If *spec* is a string, it is assumed to already represent a unique
    ID and is returned unchanged. Otherwise, *spec* is assumed to be an
    **importable** class, function, or module, and its dotted name is
    returned (see :func:`format_dotted_name`).

    """
    return spec if is_string(spec) else format_dotted_name(spec)

