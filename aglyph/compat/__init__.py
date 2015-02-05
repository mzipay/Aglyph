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

"""This module defines constants, functions, and classes that are used
to enable Python version and variant cross-compatibility.

There are two primary goals:

#. Make the differences between Python 2 ``str``/``unicode`` and
   Python 3 ``bytes``/``str`` as transparent as possible.
#. Hide Python API differences behind aliases that can be used in any
   version or variant.

Keeping these constructs contained in a separate module makes them
easier to maintain (and easier to remove later).

"""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "2.1.0"

import logging
import os
import platform
import sys
import types
import xml.etree.ElementTree as ET

# TODO: Need a custom OrderedDict (Jython 2.5.3 collections module doesn't have it)

__all__ = [
    "ClassAndFunctionTypes",
    "DataType",
    "DoctypeTreeBuilder",
    "etree_iter",
    "is_callable",
    "is_gae",
    "is_ironpython",
    "is_jython",
    "is_pypy",
    "is_python_2",
    "is_python_3",
    "is_stackless",
    "log_compatibility",
    "new_instance",
    "NoOpLoggingHandler",   # deprecated; remove in 3.0.0
    "NULL_LOGGING_HANDLER",
    "OrderedDict",
    "platform_detail",
    "python_implementation",    # deprecated; remove in 3.0.0
    "RESTRICTED_BUILTINS",
    "StringTypes",
    "TextType",
]

_logger = logging.getLogger(__name__)

#: True if the Python MAJOR version is 2.
is_python_2 = (sys.version_info[0] == 2)

#: True if the Python MAJOR version is 3.
is_python_3 = (sys.version_info[0] == 3)

#: The name of the runtime Python implementation (e.g. "CPython", "Jython").
_py_impl = getattr(platform, "python_implementation", lambda: "Python")()

# platform.python_implementation() has proven to be somewhat unreliable
if (hasattr(sys, "JYTHON_JAR")):
    _py_impl = "Jython"
elif (hasattr(sys, "pypy_version_info")):
    _py_impl = "PyPy"

try:
    import clr
except ImportError:
    _has_clr = False
else:
    _has_clr = True

#: True if the runtime Python implementation is IronPython.
is_ironpython = ("ironpython" in _py_impl.lower()) and _has_clr

#: True if the runtime Python implementation is Jython.
is_jython = ("jython" in _py_impl.lower())

#: True if the runtime Python implementation is PyPy.
is_pypy = ("pypy" in _py_impl.lower())

# PYVER: PyPy includes support for stackless, but as of the 3.2.5-compatible
# PyPy 2.4.0 release, importing the "stackless" module causes an AttributeError
# (see https://github.com/eventlet/eventlet/issues/83)
try:
    import stackless
except:
    _has_stackless = False
else:
    _py_impl = "Stackless Python"
    _has_stackless = True

#: True if the runtime Python implementation is Stackless Python.
is_stackless = (not is_pypy) and _has_stackless

#: True if running on the Google App Engine
is_gae = "APPENGINE_RUNTIME" in os.environ

python_implementation = _py_impl
"""The name of the runtime Python implementation.

.. deprecated:: 2.1.0
   Superceded by :attr:`platform_detail` and will be **removed** in\
   release 3.0.0.

"""

_py_ver = "%d.%d.%d" % sys.version_info[:3]
if (sys.version_info[3] != "final"):
    _py_ver = "%s%s%d" % (_py_ver, sys.version_info[3][0], sys.version_info[4])

_py_system = None
if (not is_gae):
    _py_system = getattr(platform, "platform", lambda: None)()
if (_py_system is None):
    _py_system = getattr(platform, "system", lambda: "Unknown")()

#: The python implementation, version, and platform information.
platform_detail = "%s %s (%s)" % (_py_impl, _py_ver, _py_system)
if (is_gae):
    platform_detail = "%s [GAE]" % platform_detail

# get a reference to the built-ins for use below; note that __builtins__ is not
# always available (and when it is, can be either a module or a dict), so
# explicitly import the appropriate module here
if (is_python_2):
    _py_builtins = __import__("__builtin__").__dict__
else: # assume is_python_3
    _py_builtins = __import__("builtins").__dict__

# normalize text (Unicode) and data (encoded bytes) types, as this is the most
# significant difference between Python 2 and 3
#
# Also:
# * u"..." is valid syntax in Python 2, but raises SyntaxError in Python 3
# * b"..." is valid syntax in Python 3, but raise SyntaxError in Python 2
if (is_python_2):
    _text_type = _py_builtins["unicode"]
    _data_type = str
else:  # assume is_python_3
    _text_type = str
    _data_type = _py_builtins["bytes"]

TextType = _text_type
"""The type of Unicode text.

.. note::
   The Python 2 Unicode text type is :obj:`unicode`, while the Python 3
   Unicode text type is :obj:`str`.

"""

DataType = _data_type
"""The type of encoded byte data.

.. note::
   The Python 2 encoded byte data type is ``str``, while the Python 3
   encoded byte data type is ``bytes``.

"""

StringTypes = (TextType, DataType)
"""The types recognized generically as "strings."

.. note::
   ``StringTypes`` is always the 2-tuple
   ``(`` :data:`TextType` ``,`` :data:`DataType` ``)``.

"""

# define a null (no-op) logging handler
# (used in aglyph.__init__)
if (hasattr(logging, "NullHandler")):
    NoOpLoggingHandler = getattr(logging, "NullHandler")
else:
    class NoOpLoggingHandler(logging.Handler):
        """The null (no-op) logging handler.

        This handler is (should be) used by library code to avoid "No
        handlers could be found" warnings when no handlers are
        configured for the library's logging channel.

        .. note::
           :py:class:`logging.NullHandler` is not available in
           Python < 2.7 or in Python 3.0.

        .. deprecated:: 2.1.0
           Aglyph is no longer supported on Python < 2.7 or
           Python == 3.0, so :class:`logging.NullHandler` will used
           moving forward.
           This class will be **removed** in release 3.0.0.

        """
        def handle(self, record):
            pass
        def emit(self, record):
            pass    
        def createLock(self):
            self.lock = None

#: The null (no-op) logging handler instance.
NULL_LOGGING_HANDLER = NoOpLoggingHandler()

_class_and_func_types = [type, types.FunctionType, types.BuiltinFunctionType]
if (is_python_2):
    # take old-style classes into account when trying to determine whether or
    # not an object is a class or function
    # (used in aglyph.__init__.format_dotted_name)
    _class_and_func_types.insert(1, getattr(types, "ClassType"))

    # the built-in function 'callable' is available in Python 2
    # (used in 'aglyph.assembler.Assembler._wire' and
    #  'aglyph.component.Evaluator.__init__')
    _callable = _py_builtins["callable"]

    # a function that can create an (uninitialized) instance of an old-style or
    # new-style class
    # (used in 'aglyph.assembler.Assembler._create_borg' and
    #  'aglyph.assembler.Assembler._initialize')
    _instance_type = getattr(types, "InstanceType")
    def _new_instance(cls):
        if (issubclass(cls, object)):
            return cls.__new__(cls)
        else:
            return _instance_type(cls)
else: # assume is_python_3
    # the built-in function 'callable' is not available in Python 3.0 and 3.1
    # (used in 'aglyph.assembler.Assembler._wire' and
    #  'aglyph.component.Evaluator.__init__')
    _callable = _py_builtins.get("callable",
                                 lambda o: hasattr(o, "__call__"))

    # a function that can create an (uninitialized) instance of a class
    # (used in 'aglyph.assembler.Assembler._create_borg' and
    #  'aglyph.assembler.Assembler._initialize')
    _new_instance = lambda cls: cls.__new__(cls)

try:
    from collections import OrderedDict
except:
    from aglyph.compat.ordereddict import OrderedDict

ClassAndFunctionTypes = tuple(_class_and_func_types)
"""The types of classes and functions.

.. note::

   Old-style classes need to be taken into account in Python 2, but do
   not exist in Python 3.

"""

is_callable = _callable
"""Return ``True`` if the argument is a callable object.

.. note::

   The builtin ``callable`` function is not available in Python 3.0 or
   Python 3.1.

"""

new_instance = _new_instance
"""Create an **uninitialized** instance of the class object argument.

.. note::

   Old-style classes need to be taken into account in Python 2, but do
   not exist in Python 3.

"""


# create a module that contains a "safe" subset of built-ins (for use as
# builtins in the globals passed to 'eval()')
# (used in 'aglyph.context.XMLContext._parse_eval')
_restricted_builtins = types.ModuleType.__new__(types.ModuleType)
_restricted_builtins.__init__("%s.RESTRICTED_BUILTINS" % __name__,
                              "Aglyph restricted builtins for :py:func:`eval`")
for allowed in [
            "ArithmeticError",
            "AssertionError",
            "AttributeError",
            "BaseException",
            "BufferError",
            "BytesWarning",
            "DeprecationWarning",
            "EOFError",
            "Ellipsis",
            "EnvironmentError",
            "Exception",
            "False",
            "FloatingPointError",
            "FutureWarning",
            "GeneratorExit",
            "IOError",
            "ImportError",
            "ImportWarning",
            "IndentationError",
            "IndexError",
            "KeyError",
            "KeyboardInterrupt",
            "LookupError",
            "MemoryError",
            "NameError",
            "None",
            "NotImplemented",
            "NotImplementedError",
            "OSError",
            "OverflowError",
            "PendingDeprecationWarning",
            "ReferenceError",
            "ResourceWarning",
            "RuntimeError",
            "RuntimeWarning",
            "StandardError",
            "StopIteration",
            "SyntaxError",
            "SyntaxWarning",
            "SystemError",
            "TabError",
            "True",
            "TypeError",
            "UnboundLocalError",
            "UnicodeDecodeError",
            "UnicodeEncodeError",
            "UnicodeError",
            "UnicodeTranslateError",
            "UnicodeWarning",
            "UserWarning",
            "ValueError",
            "Warning",
            "ZeroDivisionError",
            "__debug__",
            "abs",
            "all",
            "any",
            "apply",
            "ascii",
            "basestring",
            "bin",
            "bool",
            "buffer",
            "bytearray",
            "bytes",
            "callable",
            "chr",
            "cmp",
            "coerce",
            "complex",
            "dict",
            "dir",
            "divmod",
            "enumerate",
            "filter",
            "float",
            "format",
            "frozenset",
            "getattr",
            "hasattr",
            "hash",
            "hex",
            "id",
            "int",
            "intern",
            "isinstance",
            "issubclass",
            "iter",
            "len",
            "list",
            "long",
            "map",
            "max",
            "memoryview",
            "min",
            "next",
            "object",
            "oct",
            "ord",
            "pow",
            "range",
            "reduce",
            "repr",
            "reversed",
            "round",
            "set",
            "slice",
            "sorted",
            "str",
            "sum",
            "tuple",
            "type",
            "unichr",
            "unicode",
            "xrange",
            "zip"
        ]:
    if (allowed in _py_builtins):
        _restricted_builtins.__dict__[allowed] = _py_builtins[allowed]
del allowed

RESTRICTED_BUILTINS = _restricted_builtins
"""A module object that defines a "safe" subset of Python builtins.

These builtins are passed in the globals to the builtin :obj:`eval`
function.

.. deprecated:: 2.0.0
   Use a top-level ``<component>`` instead of a nested ``<eval>``. This
   member will be **removed** in release 3.0.0.

.. seealso::

   `Eval really is dangerous <http://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html>`_
      Ned Batchelder's insanely thorough discussion of :obj:`eval`

"""


class DoctypeTreeBuilder(ET.TreeBuilder):
    """An :mod:`xml.etree.ElementTree.TreeBuilder` that avoids
    deprecation warnings for
    :meth:`xml.etree.ElementTree.XMLParser.doctype`.

    .. seealso::
       `Issue14007 <http://bugs.python.org/issue14007>`_
          xml.etree.ElementTree - XMLParser and TreeBuilder's doctype()\
          method missing

    """

    def doctype(self, name, pubid, system):
        pass


def etree_iter(root, tag=None):
    """Return an iterator over elements named *tag* rooted at *root*.

    :param root: an :class:`xml.etree.ElementTree.ElementTree` or\
                 :class:`xml.etree.ElementTree.Element`

    .. note::
       Refer to :meth:`xml.etree.ElementTree.Element.iter` for an
       explanation of the *tag* keyword and the return value/type.

    :meth:`xml.etree.ElementTree.Element.iter` is not available in
    Python 2.6 and 3.1, but **is** available in 2.7, 3.2, and 3.3.

    :meth:`xml.etree.ElementTree.Element.getiterator` is deprecated,
    but **only** in 2.7 and 3.2.

    As a work-around, this function will use ``root.iter`` if it is
    defined, or will fall back to using ``root.getiterator``.

    """
    iter_method = getattr(root, "iter", None)
    if (iter_method is None):
        # allow AttributeError here
        iter_method = getattr(root, "getiterator")
    return iter_method(tag)


def log_compatibility():
    """Log the runtime compatibility details.

    """
    if (_logger.isEnabledFor(logging.DEBUG)):
        _logger.debug("is_python_2? %r; is_python_3? %r",
                      is_python_2, is_python_3)
        _logger.debug(
            "is_ironpython? %r, is_jython? %r, is_pypy? %r, is_stackless? %r, "
            "is_gae? %r",
            is_ironpython, is_jython, is_pypy, is_stackless, is_gae)
        _logger.debug("TextType is %r; DataType is %r; StringTypes is %r",
                      TextType, DataType, StringTypes)
        _logger.debug("NoOpLoggingHandler is %r", NoOpLoggingHandler)
        _logger.debug("OrderedDict is %r", OrderedDict)
        _logger.debug("ClassAndFunctionTypes is %r", ClassAndFunctionTypes)
        _logger.debug("is_callable is %r", is_callable)
        _logger.debug("new_instance is %r", new_instance)
        _logger.debug("RESTRICTED_BUILTINS (deprecated) contains %r",
                      sorted(RESTRICTED_BUILTINS.__dict__.keys()))


del _py_builtins

