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

"""This module defines a custom error type and several utility functions
used by Aglyph.

Aglyph is fully logged using the standard :mod:`logging` module, but by
default uses a no-op logging handler to suppress log messages. If you
want to enable Aglyph logging, define a logger for the *"aglyph"* log
channel in your application, **prior** to importing any Aglyph modules.

See :mod:`logging.config` for more information about configuring the
logging module.


"""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "1.0.0"

import logging
import platform

from aglyph.compat import (ClassAndFunctionTypes, log_23_compatibility,
                           NoOpLoggingHandler, python_implementation)

__all__ = ["AglyphError", "format_dotted_name", "has_importable_dotted_name",
           "resolve_dotted_name"]

# define a logger for the "aglyph" channel to enable logging
_logger = logging.getLogger(__name__)
if (not _logger.handlers):
    # suppress log messages by default
    _logger.addHandler(NoOpLoggingHandler())

# log the Aglyph/Python versions and the platform (useful for debugging), and
# then the _23compat details
_logger.info("Aglyph %s; %s %s; %s" % (__version__, python_implementation,
                                       platform.python_version(),
                                       platform.platform()))
log_23_compatibility()


class AglyphError(Exception):
    """Raised when Aglyph operations fail with a condition that is not
    sufficiently described by a built-in exception.

    """


def has_importable_dotted_name(obj):
    """Returns ``True`` if *obj* is an importable class or unbound
    function.

    """
    return (isinstance(obj, ClassAndFunctionTypes) and
            # need to look for __self__ because BuiltinFunctionType is the type
            # of both built-in functions AND built-in methods
            (getattr(obj, "__self__", None) is None))


def format_dotted_name(factory):
    """Returns the dotted-name string for *factory*.

    *factory* should be an importable class or unbound function.

    The returned dotted-name is a "relative_module.identifier" string
    for *factory* that represents a valid import statement according to
    the following production:

    .. productionlist::
        import_stmt: "from" relative_module "import" identifier

    This function is the inverse of :func:`resolve_dotted_name`.

    :raises TypeError: if *factory* is not a class or unbound function

    """
    _logger.debug("formatting dotted-name for %r", factory)
    if (not has_importable_dotted_name(factory)):
        raise TypeError("expected class or unbound function, not %s" %
                        type(factory).__name__)
    dotted_name = "%s.%s" % (factory.__module__, factory.__name__)
    return dotted_name


def resolve_dotted_name(dotted_name):
    """Returns the class or function identified by *dotted_name*.

    *dotted_name* must be a "relative_module.identifier" string such
    that the following production represents a valid import statement
    with respect to the application's ``sys.path``:

    .. productionlist::
        import_stmt: "from" relative_module "import" identifier

    This method is the inverse of :func:`format_dotted_name`.

    :raises ImportError: if importing *dotted_name* fails
    :raises ValueError: if *dotted_name* cannot be parsed into
                        "relative_module" and "identifier" parts

    """
    _logger.debug("resolving %r", dotted_name)
    try:
        (module_name, identifier) = dotted_name.rsplit('.', 1)
        module = __import__(module_name, globals(), locals(), [identifier])
        return getattr(module, identifier)
    except ImportError:
        raise
    except Exception:
        raise ValueError("%r is not a valid dotted-name" % dotted_name)
