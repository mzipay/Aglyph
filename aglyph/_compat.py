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

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

from inspect import getmodule
import logging
import os
import platform
import sys
import types
import xml.etree.ElementTree as ET

from aglyph import __version__

from autologging import logged, traced

__all__ = [
    "is_python_2",
    "is_python_3",
    "is_pypy",
    "is_stackless",
    "is_jython",
    "has_clr",
    "is_ironpython",
    "platform_detail",
    "TextType",
    "DataType",
    "is_string",
    "new_instance",
    "name_of",
    "DoctypeTreeBuilder",
    "CLRXMLParser",
    "AglyphDefaultXMLParser",
]

_log = logging.getLogger(__name__)

#: True if the Python MAJOR version is 2.
is_python_2 = (sys.version_info[0] == 2)

#: True if the Python MAJOR version is 3.
is_python_3 = (sys.version_info[0] == 3)

_sys_version = ' '.join(sys.version.split())

try:
    _py_impl = platform.python_implementation()
except:
    _py_impl = "Python"

#: True if the runtime Python implementation is PyPy.
is_pypy = \
    _py_impl == "PyPy" and getattr(sys, "pypy_version_info", None) is not None

try:
    import stackless
except:
    _has_stackless = False
else:
    _py_impl = "Stackless Python"
    _has_stackless = True

#: True if the runtime Python implementation is Stackless Python.
is_stackless = \
    (not is_pypy) and _has_stackless and ("Stackless" in sys.version)

#: True if the runtime Python implementation is Jython.
is_jython = \
    _py_impl == "Jython" and getattr(sys, "JYTHON_JAR", None) is not None

try:
    import clr
    clr.AddReference("System")
    has_clr = True
except:
    has_clr = False

#: True if the runtime Python implementation is IronPython.
is_ironpython = _py_impl == "IronPython" and has_clr

_platform = None
try:
    # preferred (most detail, but not universally available/supported)
    _platform = platform.platform()
except:
    _platform = getattr(os, "name", "unknown")

if hasattr(sys, "getwindowsversion"):
    try:
        _platform = "%s %s" % (_platform, sys.getwindowsversion())
    except:
        pass

#: The python implementation, version, and platform information.
platform_detail = "%s %s %s" % (_py_impl, _sys_version, _platform)
if "APPENGINE_RUNTIME" in os.environ:
    platform_detail = "%s [GAE]" % platform_detail

_builtins = getmodule(hex).__dict__

#: The type of Unicode text strings.
TextType = _builtins["str"] if is_python_3 else _builtins["unicode"]

#: The type of encoded byte data strings.
DataType = _builtins["bytes"] if is_python_3 else _builtins["str"]

_StringTypes = (TextType, DataType)


def is_string(obj):
    """Return ``True`` if *obj* is Unicode text or encoded bytes data.

    :param obj: an object
    :rtype: bool

    """
    return isinstance(obj, _StringTypes)


_instance_type = getattr(types, "InstanceType", None)


def new_instance(cls):
    """Create an **uninitialized** instance of the class *cls*.

    :param cls: a class object

    .. note::
       This function can create uninitialized instances of both
       "new-style" (Python 3, Python 2 derived from :class:`object`) and
       "old-style" (Python 2 **not** derived from :class:`object`)
       classes.

    """
    return object.__new__(cls) if type(cls) is type else _instance_type(cls)


def name_of(obj):
    """Return the name of *obj*.

    :param obj: any object

    .. note::
       This function will return ``obj.__qualname__`` if :pep:`3155` is
       supported in the runtime Python implementation; otherwise
       ``obj.__name__`` is returned.

    """
    return getattr(obj, "__qualname__", obj.__name__)


class DoctypeTreeBuilder(ET.TreeBuilder):
    """An :mod:`xml.etree.ElementTree.TreeBuilder` that avoids
    deprecation warnings for
    :meth:`xml.etree.ElementTree.XMLParser.doctype`.

    .. seealso::
       `Issue14007 <http://bugs.python.org/issue14007>`_
          xml.etree.ElementTree - XMLParser and TreeBuilder's doctype()
          method missing

    """

    def __init__(self, *args, **keywords):
        """
        :arg tuple *args: the positional initialization arguments
        :arg dict **keywords: the keyword initialization arguments

        """
        #PYVER: arguments to super() are implicit under Python 3
        super(DoctypeTreeBuilder, self).__init__(*args, **keywords)
        self._doctype_name = None
        self._doctype_pubid = None
        self._doctype_system = None

    @property
    def doctype_name(self):
        """The document type name *(read-only)*."""
        return self._doctype_name

    @property
    def doctype_pubid(self):
        """The document type public identifier *(read-only)*."""
        return self._doctype_pubid

    @property
    def doctype_system(self):
        """The document type system identifier *(read-only)*."""
        return self._doctype_system

    def doctype(self, name, pubid, system):
        """Report the parsed DOCTYPE declaration.

        :arg str name: the document type name
        :arg str pubid: the document type public identifier
        :arg str system: the document type system identifier

        """
        self._doctype_name = name
        self._doctype_pubid = pubid
        self._doctype_system = system


if is_ironpython:
    clr.AddReference("System.IO")
    clr.AddReference("System.Xml")

    _log.info("loaded System.IO and System.Xml CLR namespaces")

    from System.IO import StringReader
    from System.Xml import (
        DtdProcessing,
        ValidationType,
        XmlNodeType,
        XmlReader,
        XmlReaderSettings
    )


    @traced
    @logged
    class CLRXMLParser(ET.XMLParser):
        """An :class:`xml.etree.ElementTree.XMLParser` that delegates
        parsing to the .NET CLR `System.Xml.XmlReader
        <http://msdn.microsoft.com/en-us/library/system.xml.xmlreader>`_
        parser.

        .. note::
           `IronPython <http://ironpython.net/>`_ is not able to load
           CPython's :mod:`xml.parsers.expat` module by default, and so
           the default parser used by ElementTree does not exist.

        """

        def __init__(self, target=DoctypeTreeBuilder(), validating=False):
            """
            :keyword xml.etree.ElementTree.TreeBuilder target:
               the target object (optional; defaults to
               :class:`aglyph._compat.DoctypeTreeBuilder`)
            :keyword bool validating:
               specify ``True`` to use a validating parser

            """
            settings = XmlReaderSettings()
            settings.IgnoreComments = True
            settings.IgnoreProcessingInstructions = True
            settings.IgnoreWhitespace = True
            if not validating:
                settings.DtdProcessing = DtdProcessing.Ignore
                settings.ValidationType = getattr(ValidationType, "None")
            else:
                settings.DtdProcessing = DtdProcessing.Parse
                settings.ValidationType = ValidationType.DTD
            self.settings = settings
            self.version = platform.python_compiler()
            self.__log.debug("ET parser version is %s", self.version)
            self._target = target
            self._buffer = []

        def feed(self, data):
            """Add more XML data to be parsed.

            :arg str data: raw XML read from a stream

            .. note::
               All *data* across calls to this method are buffered
               internally; the parser itself is not actually created
               until the :meth:`close` method is called.

            """
            self._buffer.append(data)

        def close(self):
            """Parse the XML from the internal buffer to build an
            element tree.

            :return:
                the root element of the XML document
            :rtype:
                :class:`xml.etree.ElementTree.ElementTree`

            """
            xml_string = "".join(self._buffer)
            self._buffer = None

            reader = XmlReader.Create(StringReader(xml_string), self.settings)

            # figure out which encoding to use
            next = reader.Read()
            document_encoding = (
                reader.GetAttribute("encoding")
                if next and reader.NodeType == XmlNodeType.XmlDeclaration
                else None)
            if document_encoding:
                self.__log.info(
                    "parsed document encoding %r from XML declaration",
                    document_encoding)
            else:
                document_encoding = "UTF-8"
                self.__log.warn(
                    "document encoding is missing! assuming default %r",
                    document_encoding)

            while next:
                if reader.IsStartElement():
                    self._start_element(reader)
                elif reader.NodeType in [XmlNodeType.Text, XmlNodeType.CDATA]:
                    # decode the value first to work around IronPython quirk
                    self._target.data(reader.Value.decode(document_encoding))
                elif reader.NodeType == XmlNodeType.EndElement:
                    self._target.end(reader.LocalName)

                next = reader.Read()

            return self._target.close()

        def _start_element(self, reader):
            """Notify the tree builder that a start element has been
            encountered.

            :arg reader:
               a .NET `System.Xml.XmlReader
               <http://msdn.microsoft.com/en-us/library/system.xml.xmlreader>`_

            If the element is an empty element (e.g. ``<name />``), the
            tree builder is also notified that the element has been
            closed.

            """
            name = reader.LocalName
            attributes = {}
            while reader.MoveToNextAttribute():
                attributes[reader.Name] = reader.Value
            reader.MoveToElement()
            self._target.start(name, attributes)
            if reader.IsEmptyElement:
                self._target.end(name)


else:
    class CLRXMLParser(ET.XMLParser):
        """A dummy class that will raise :class:`RuntimeError` if
        instantiated.

        """

        def __new__(self, *args, **keywords):
            raise RuntimeError(".NET CLR is not available")


#: The default XML parser used by :class:`aglyph.context.XMLContext`.
AglyphDefaultXMLParser = ET.XMLParser if not is_ironpython else CLRXMLParser


# log compatibility details
_log.debug(
    "compatibility details:\n"
        "  is_python_2? %r\n"
        "  is_python_3? %r\n"
        "  is_pypy? %r\n"
        "  is_stackless? %r\n"
        "  is_jython? %r\n"
        "  is_ironpython? %r (has_clr? %r)\n"
        "  TextType is %r\n"
        "  DataType is %r\n"
        "  _instance_type is %r\n"
        "  __qualname__ supported? %r\n"
        "  AglyphDefaultXMLParser is %r",
    is_python_2,
    is_python_3,
    is_pypy,
    is_stackless,
    is_jython,
    is_ironpython, has_clr,
    TextType,
    DataType,
    _instance_type,
    hasattr(DoctypeTreeBuilder, "__qualname__"),
    AglyphDefaultXMLParser
)

del _sys_version, _py_impl, _has_stackless, _platform, _builtins

