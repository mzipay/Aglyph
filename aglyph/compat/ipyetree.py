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

"""This module defines an :class:`xml.etree.ElementTree.XMLParser` that
delegates to the .NET
`System.Xml.XmlReader
<http://msdn.microsoft.com/en-us/library/system.xml.xmlreader>`_ XML
parser to parse an Aglyph XML context document.

`IronPython <http://ironpython.net/>`_ is not able to load CPython's
:mod:`xml.parsers.expat` module, and so the default parser used by
ElementTree does not exist.

.. versionadded:: 2.0.0
   To address the missing :mod:`xml.parsers.expat` module, this module\
   now defines the :class:`CLRXMLParser` class, which replaces\
   :class:`XmlReaderTreeBuilder` and is used by\
   :class:`aglyph.context.XMLContext` as the default parser when\
   running under IronPython.

Alternatively, IronPython developers may wish to install ``expat`` or an
``expat``-compatible library as a site package. **However, this has not
been tested with Aglyph.**

"""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "2.1.0"

import logging
import platform
import warnings
import xml.etree.ElementTree as ET

from aglyph import AglyphDeprecationWarning, AglyphError
from aglyph.compat import DoctypeTreeBuilder, is_ironpython

__all__ = ["CLRXMLParser", "XmlReaderTreeBuilder"]

_logger = logging.getLogger(__name__)

if (is_ironpython):
    import clr

    clr.AddReference("System.Xml")

    from System.IO import StringReader
    from System.Text.RegularExpressions import Regex, RegexOptions
    from System.Xml import (
        DtdProcessing,
        ValidationType,
        XmlNodeType,
        XmlReader,
        XmlReaderSettings
    )

    _logger.info(
        "loaded System.Xml, System.IO, and System.Text CLR namespaces")

    CRE_ENCODING = Regex("encoding=['\"](?<enc_name>.*?)['\"]",
                         RegexOptions.Compiled)

    class CLRXMLParser(ET.XMLParser):
        """An :class:`xml.etree.ElementTree.XMLParser` that delegates
        parsing to the .NET `System.Xml.XmlReader
        <http://msdn.microsoft.com/en-us/library/system.xml.xmlreader>`_
        parser.

        """

        __logger = logging.getLogger("%s.CLRXMLParser" % __name__)

        def __init__(self, target=None, validating=False):
            """
            :param xml.etree.ElementTree.TreeBuilder target:\
               the target object (if omitted, a standard\
               ``TreeBuilder`` instance is used)
            :param bool validating:\
               specify ``True`` to use a validating parser

            """
            self.__logger.debug("TRACE target=%r, validating=%r",
                                target, validating)
            settings = XmlReaderSettings()
            settings.IgnoreComments = True
            settings.IgnoreProcessingInstructions = True
            settings.IgnoreWhitespace = True
            if (not validating):
                settings.DtdProcessing = DtdProcessing.Ignore
                settings.ValidationType = getattr(ValidationType, "None")
            else:
                settings.DtdProcessing = DtdProcessing.Parse
                settings.ValidationType = ValidationType.DTD
            self.settings = settings
            self.version = "%s %s" % (platform.platform(),
                                      platform.python_compiler())
            self.__logger.debug("ET parser version is %r", self.version)
            self._target = (target if (target is not None)
                            else DoctypeTreeBuilder())
            self._buffer = []
            self._document_encoding = "UTF-8"  # default
            self.__logger.debug("RETURN")

        def feed(self, data):
            """Add more XML data to be parsed.

            :param str data: raw XML read from a stream

            .. note::
               All *data* across calls to this method are buffered
               internally; the parser itself is not actually created
               until the :meth:`close` method is called.

            """
            self._buffer.append(data)

        def close(self):
            """Parse the XML from the internal buffer to build an
            element tree.

            :return: the root element of the XML document
            :rtype: :class:`xml.etree.ElementTree.ElementTree`

            """
            self.__logger.debug("TRACE")
            xml_string = "".join(self._buffer)
            self._buffer = None
            reader = XmlReader.Create(StringReader(xml_string), self.settings)
            while (reader.Read()):
                if (reader.IsStartElement()):
                    self._start_element(reader)
                elif (reader.NodeType in [XmlNodeType.Text,
                                          XmlNodeType.CDATA]):
                    # decode the value first (see the comment for
                    # 'self._document_encoding' and the docstring for
                    # '_parse_xml_declaration(xml_decl)'
                    self._target.data(
                                reader.Value.decode(self._document_encoding))
                elif (reader.NodeType == XmlNodeType.EndElement):
                    self._target.end(reader.LocalName)
                elif (reader.NodeType == XmlNodeType.XmlDeclaration):
                    self._parse_xml_declaration(reader.Value)
            return self._target.close()
            self.__logger.debug("RETURN")

        def _parse_xml_declaration(self, xml_decl):
            """Parse the document encoding from *xml_decl*.

            :param str xml_decl: the document XML declaration

            *xml_decl* is reported by `System.Xml.XmlReader
            <http://msdn.microsoft.com/en-us/library/system.xml.xmlreader>`_
            as a node of the type
            `XmlNodeType.XmlDeclaration
            <http://msdn.microsoft.com/en-us/library/system.xml.xmlnodetype>`_.

            """
            self.__logger.debug("TRACE %r", xml_decl)
            enc_name = CRE_ENCODING.Match(xml_decl).Groups["enc_name"].Value
            if (enc_name):
                self.__logger.info("document encoding is %r", enc_name)
                self._document_encoding = enc_name
            self.__logger.debug("RETURN")

        def _start_element(self, reader):
            """Notify the tree builder that a start element has been
            encountered.

            *reader* is a reference to a .NET
            `System.Xml.XmlReader
            <http://msdn.microsoft.com/en-us/library/system.xml.xmlreader>`_.

            If the element is an empty element (e.g. ``<name/>``), the
            tree builder is also notified that the element has been
            closed.

            """
            name = reader.LocalName
            attributes = {}
            while (reader.MoveToNextAttribute()):
                attributes[reader.Name] = reader.Value
            reader.MoveToElement()
            self._target.start(name, attributes)
            if (reader.IsEmptyElement):
                self._target.end(name)


else:
    _logger.warn("not running under IronPython; .NET CLR is not available")

    class CLRXMLParser(ET.XMLParser):
        """A dummy class that will throw :class:`aglyph.AglyphError` if
        instantiated.

        """

        def __new__(self, *args, **keywords):
            raise AglyphError(".NET CLR is not available")


class XmlReaderTreeBuilder(CLRXMLParser):
    """Build an `ElementTree
    <http://effbot.org/zone/element-index.htm>`_ using the .NET
    `System.Xml.XmlReader
    <http://msdn.microsoft.com/en-us/library/system.xml.xmlreader>`_
    XML parser.

    .. versionchanged:: 2.0.0
       It is no longer necessary for IronPython applications to use\
       this class explicitly. :class:`aglyph.context.XMLContext` now\
       uses :class:`CLRXMLParser` by default if running under\
       IronPython.

    .. deprecated:: 2.0.0
       This class has been renamed to :class:`CLRXMLParser`.\
       ``XmlReaderTreeBuilder`` will be **removed** in release 3.0.0.

    """

    def __init__(self, validating=False):
        warnings.warn(
            AglyphDeprecationWarning(
                "aglyph.compat.ipyetree.XmlReaderTreeBuilder",
                replacement="aglyph.compat.ipyetree.CLRXMLParser"))
        super(XmlReaderTreeBuilder, self).__init__(validating=validating)

