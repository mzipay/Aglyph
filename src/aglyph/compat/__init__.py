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

"""This module defines constants, functions, and classes that are used
to enable Python 2/3 cross-compatibility.

There are two primary goals:

#. Make the differences between Python 2 ``str``/``unicode`` and
   Python 3 ``bytes``/``str`` as transparent as possible.
#. Hide Python API differences behind aliases that can be used in either
   version.

Keeping these constructs contained in a separate module makes them
easier to maintain (and easier to remove later).

"""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "1.0.0"

import logging
import platform
import sys
import types

__all__ = ["ClassAndFunctionTypes", "DataType", "is_python_2", "is_python_3",
           "log_23_compatibility", "new_instance", "NoOpLoggingHandler",
           "python_implementation", "RESTRICTED_BUILTINS", "TextType"]

_logger = logging.getLogger(__name__)

is_python_2 = (sys.version_info[0] == 2)
is_python_3 = (sys.version_info[0] == 3)

# identify the Python implementation (i.e. CPython, IronPython, Jython, or
# PyPy) - 'platform.python_implementation()' is not available in Python < 2.6
# (used in 'aglyph.__init__')
if (hasattr(platform, "python_implementation")):
    python_implementation = getattr(platform, "python_implementation")()
else:
    python_implementation = "Python"

# get a reference to the built-ins for use below; note that __builtins__ is not
# always available (and when it is, can be either a module or a dict), so
# explicitly import the appropriate module here
if (is_python_2):
    _py_builtins = __import__("__builtin__").__dict__
else: # assume is_python_3
    _py_builtins = __import__("builtins").__dict__

# normalize text (Unicode) and data (encoded bytes) types, as this is the most
# significant difference between Python 2 and 3:
#
# +----------+-------------------+-------------------+
# |          |    Unicode text   | Encoded byte data |
# +----------+-------------------+-------------------+
# | Python 2 |      unicode      |        str        |
# +----------+-------------------+-------------------+
# | Python 3 |        str        |       bytes       |
# +----------+-------------------+-------------------+
#
# Also:
# * u"..." is valid syntax in Python 2, but raises SyntaxError in Python 3
# * b"..." is valid syntax in Python 3, but raise SyntaxError in Python 2
if (is_python_2):
    # normalize the types for Unicode text and encoded byte data
    TextType = _py_builtins["unicode"]
    DataType = str
    StringTypes = (_py_builtins["basestring"],)
else: # assume is_python_3
    # normalize the types for Unicode text and encoded byte data
    TextType = str
    DataType = _py_builtins["bytes"]
    StringTypes = (DataType, str)

# define a no-op logging handler (logging.NullHandler is not available in
# Python < 2.7, or in Python 3.0)
# (used in aglyph.__init__)
if (hasattr(logging, "NullHandler")):
    NoOpLoggingHandler = getattr(logging, "NullHandler")
else:
    class NoOpLoggingHandler(logging.Handler):    
        def handle(self, record):
            pass
        def emit(self, record):
            pass    
        def createLock(self):
            self.lock = None

if (is_python_2):
    # take old-style classes into account when trying to determine whether or
    # not an object is a class or function
    # (used in aglyph.__init__.has_importable_dotted_name)
    ClassAndFunctionTypes = (type, types.ClassType, types.FunctionType,
                             types.BuiltinFunctionType)

    # the built-in function 'callable' is available in Python 2
    # (used in 'aglyph.assembler.Assembler._wire' and
    #  'aglyph.component.Evaluator.__init__')
    is_callable = _py_builtins["callable"]

    # a function that can create an (uninitialized) instance of an old-style or
    # new-style class
    # (used in 'aglyph.assembler.Assembler._create_borg' and
    #  'aglyph.assembler.Assembler._initialize')
    _instance_type = getattr(types, "InstanceType")
    def new_instance(cls):
        if (issubclass(cls, object)):
            return cls.__new__(cls)
        else:
            return _instance_type(cls)
else: # assume is_python_3
    # old-style classes no longer exist in Python >= 3.0, so only need to
    # consider new-style classes and functions  when trying to determine
    # whether or not an object is a class o function
    # (used in aglyph.__init__.has_importable_dotted_name)
    ClassAndFunctionTypes = (type, types.FunctionType,
                             types.BuiltinFunctionType)

    # the built-in function 'callable' is not available in Python 3.0 and 3.1
    # (used in 'aglyph.assembler.Assembler._wire' and
    #  'aglyph.component.Evaluator.__init__')
    is_callable = _py_builtins.get("callable",
                                   lambda o: hasattr(o, "__call__"))

    # a function that can create an (uninitialized) instance of a class
    # (used in 'aglyph.assembler.Assembler._create_borg' and
    #  'aglyph.assembler.Assembler._initialize')
    new_instance = lambda cls: cls.__new__(cls)

# create a module that contains a "safe" subset of built-ins (for use as
# "__builtins__" in the globals passed to 'eval()')
# (used in 'aglyph.context.XMLContext._parse_eval')
RESTRICTED_BUILTINS = types.ModuleType.__new__(types.ModuleType)
RESTRICTED_BUILTINS.__init__("%s.RESTRICTED_BUILTINS" % __name__,
                             "Aglyph restricted ``__builtins__`` for "
                             ":func:`eval`")
for allowed in ["ArithmeticError", "AssertionError", "AttributeError",
                "BaseException", "BufferError", "BytesWarning",
                "DeprecationWarning", "EOFError", "Ellipsis",
                "EnvironmentError", "Exception", "False", "FloatingPointError",
                "FutureWarning", "GeneratorExit", "IOError", "ImportError",
                "ImportWarning", "IndentationError", "IndexError", "KeyError",
                "KeyboardInterrupt", "LookupError", "MemoryError", "NameError",
                "None", "NotImplemented", "NotImplementedError", "OSError",
                "OverflowError", "PendingDeprecationWarning", "ReferenceError",
                "ResourceWarning", "RuntimeError", "RuntimeWarning",
                "StandardError", "StopIteration", "SyntaxError",
                "SyntaxWarning", "SystemError", "TabError", "True",
                "TypeError", "UnboundLocalError", "UnicodeDecodeError",
                "UnicodeEncodeError", "UnicodeError", "UnicodeTranslateError",
                "UnicodeWarning", "UserWarning", "ValueError", "Warning",
                "ZeroDivisionError", "__debug__", "abs", "all", "any", "apply",
                "ascii", "basestring", "bin", "bool", "buffer", "bytearray",
                "bytes", "callable", "chr", "cmp", "coerce", "complex", "dict",
                "dir", "divmod", "enumerate", "filter", "float", "format",
                "frozenset", "getattr", "hasattr", "hash", "hex", "id", "int",
                "intern", "isinstance", "issubclass", "iter", "len", "list",
                "long", "map", "max", "memoryview", "min", "next", "object",
                "oct", "ord", "pow", "range", "reduce", "repr", "reversed",
                "round", "set", "slice", "sorted", "str", "sum", "tuple",
                "type", "unichr", "unicode", "xrange", "zip"]:
    if (allowed in _py_builtins):
        RESTRICTED_BUILTINS.__dict__[allowed] = _py_builtins[allowed]
del allowed


def log_23_compatibility():
    if (_logger.isEnabledFor(logging.DEBUG)):
        _logger.debug("is_python_2? %r; is_python_3? %r", is_python_2, is_python_3)
        _logger.debug("python_implementation is %r", python_implementation)
        _logger.debug("TextType is %r; DataType is %r; StringTypes is %r",
                      TextType, DataType, StringTypes)
        _logger.debug("NoOpLoggingHandler is %r", NoOpLoggingHandler)
        _logger.debug("ClassAndFunctionTypes is %r", ClassAndFunctionTypes)
        _logger.debug("is_callable is %r", is_callable)
        _logger.debug("new_instance is %r", new_instance)
        _logger.debug("RESTRICTED_BUILTINS contains %r",
                      sorted(RESTRICTED_BUILTINS.__dict__.keys()))


del _py_builtins
