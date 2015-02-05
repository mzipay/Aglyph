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

"""This module defines a custom error type and several utility functions
used by Aglyph.

Aglyph is fully logged using the standard :mod:`logging` module, but by
default uses a no-op logging handler to suppress log messages. If you
want to enable Aglyph logging, define a logger for the *"aglyph"* log
channel in your application's logging configuration (see
:mod:`logging.config` for more information).

"""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"

# always the current version of Aglyph
MAJOR = 2
MINOR = 1
PATCH = 0
VERSION = (MAJOR, MINOR, PATCH)
__version__ = "%d.%d.%d" % VERSION

from inspect import isclass, ismethod, ismodule, isroutine
import logging
import warnings

from aglyph.compat import (
    ClassAndFunctionTypes,  # deprecated
    log_compatibility,
    NULL_LOGGING_HANDLER,
    platform_detail,
    StringTypes,
)

__all__ = [
    "AglyphDeprecationWarning",
    "AglyphError",
    "format_dotted_name",
    "has_importable_dotted_name",  # deprecated
    "identify_by_spec",  # deprecated
    "resolve_dotted_name",
]

# define a logger for the "aglyph" channel to enable logging
_logger = logging.getLogger(__name__)
if (not _logger.handlers):
    # suppress log messages by default
    _logger.addHandler(NULL_LOGGING_HANDLER)

# log the Aglyph version and Python platform, then the compatibility details
_logger.info("Aglyph %s on %s" % (__version__, platform_detail))
log_compatibility()


class AglyphDeprecationWarning(DeprecationWarning):
    """Issued when deprecated Aglyph functions, classes, or methods are
    used.

    """

    def __init__(self, name, replacement=None):
        """
        :arg str name: the name of the deprecated function, class, or\
                       method
        :keyword str replacement: the name of the replacement function,\
                                  class, or method (if applicable)

        """
        message = (
            "%s is deprecated and will be removed in release %d.0.0." %
            (name, MAJOR + 1))
        if (replacement is not None):
            message = "%s Use %s instead." % (message, replacement)
        super(AglyphDeprecationWarning, self).__init__(message)


class AglyphError(Exception):
    """Raised when Aglyph operations fail with a condition that is not
    sufficiently described by a built-in exception.

    """


def has_importable_dotted_name(obj):
    """Tell whether or not *obj* can be represented as an importable
    dotted-name string.

    :param obj: any object
    :return:\
       ``True`` if *obj* is an importable class or unbound function,\
       else ``False``

    .. deprecated:: 2.0.0
       This function has no replacement and will be **removed** in\
       release 3.0.0.

    """
    warnings.warn(
        AglyphDeprecationWarning("aglyph.has_importable_dotted_name"))
    return (isinstance(obj, ClassAndFunctionTypes) and
            # need to look for __self__ because BuiltinFunctionType is the type
            # of both built-in functions AND built-in methods
            (getattr(obj, "__self__", None) is None))


def _is_unbound_function(obj):
    """Tell whether or not *obj* is an unbound function.

    :param obj: 
    :return: ``True`` if *obj* is an unbound function, else ``False``

    .. versionadded:: 2.0.0

    """
    return (isroutine(obj) and (not ismethod(obj)) and
            # need to look for __self__ because BuiltinFunctionType is the type
            # of both built-in functions AND built-in methods
            (getattr(obj, "__self__", None) is None))


def format_dotted_name(obj):
    """Return the importable dotted-name string for *obj*.

    :param obj: an **importable** class, function, or module
    :return: a dotted name representing *obj*
    :rtype: :obj:`str`
    :raise TypeError: if *obj* is not a class, unbound function, or\
                      module
    :raise ValueError: if the dotted name for *obj* is not importable

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

       As a result, using this function to format the dotted name of a
       nested class, class method, or static method will **fail** if not
       running on Python 3.3+.

       .. seealso::
          `PEP 3155 -- Qualified name for classes and functions
          <http://www.python.org/dev/peps/pep-3155/>`_

    """
    _logger.debug("TRACE %r", obj)
    if (isclass(obj) or _is_unbound_function(obj)):
        dotted_name = "%s.%s" % (obj.__module__,
                                 getattr(obj, "__qualname__", obj.__name__))
    elif (ismodule(obj)):
        dotted_name = obj.__name__
    else:
        raise TypeError("expected class, unbound function, or module; not %s" %
                        type(obj).__name__)

    # a dotted-name MUST be importable
    # (the optimistic case here should be very fast - obj or its module is
    # already in sys.modules, otherwise NameError or AttributeError would have
    # been raised when trying to call this function)
    try:
        resolve_dotted_name(dotted_name)
    except ImportError:
        raise ValueError("%r for %r is not importable" % (dotted_name, obj))

    _logger.debug("RETURN %r", dotted_name)
    return dotted_name


def identify_by_spec(spec):
    """Generate a unique identifier for *spec*.

    :param spec: an **importable** class, function, or module; or a\
                 :obj:`str`
    :return: *spec* unchanged (if it is a :obj:`str`), else *spec*'s\
             importable dotted name
    :rtype: :obj:`str`

    If *spec* is a string, it is assumed to already represent a unique
    identifier and is returned unchanged. Otherwise, *spec* is assumed
    to be an **importable** class, function, or module, and its dotted
    name is returned (see :func:`format_dotted_name`).

    .. deprecated:: 2.0.0
       This function has no replacement and will be **removed** in\
       release 3.0.0.

    """
    warnings.warn(AglyphDeprecationWarning("aglyph.identify_by_spec"))
    return (spec if (isinstance(spec, StringTypes))
            else format_dotted_name(spec))


def resolve_dotted_name(dotted_name):
    """Return the class, function, or module identified by
    *dotted_name*.

    :param str dotted_name: a string representing an **importable**\
                            class, function, or module
    :return: a class, function, or module

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
    _logger.debug("TRACE %r", dotted_name)
    if ('.' in dotted_name):
        (module_name, name) = dotted_name.rsplit('.', 1)
        module = __import__(module_name, fromlist=[name], level=0)
        obj = getattr(module, name)
    else:
        obj = __import__(dotted_name, level=0)
    _logger.debug("RETURN %r", obj)
    return obj


def _safe_repr(obj):
    """Return a safe representation of *obj*.

    :arg obj: any object assembled by Aglyph

    .. note::
       A "safe" representation means that no internal details of *obj*
       are exposed. This is used to log assembled objects, which may
       contain sensitive data that should not be emitted to logs.

    """
    type_name = type(obj).__name__
    obj_name = getattr(obj, "__name__", None)
    if (obj_name is None):
        obj_name = obj.__class__.__name__
    if (type_name != obj_name):
        return "<%s %s @ %x>" % (obj_name, type_name, id(obj))
    else:
        return "<%s object @ %x>" % (type_name, id(obj))

