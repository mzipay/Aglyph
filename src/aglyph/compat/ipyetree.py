# -*- coding: utf-8 -*-

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

"""This module defines an :mod:`xml.etree.ElementTree` "tree builder"
that uses the .NET
`System.Xml.XmlReader <http://msdn.microsoft.com/en-us/library/system.xml.xmlreader>`_
XML parser to parse an Aglyph XML context document.

`IronPython <http://ironpython.net/>`_ is not able to load CPython's
:mod:`xml.parsers.expat` module, and so the default parser (used by
ElementTree) simply does not exist. This means that, by default,
Aglyph XML contexts cannot be loaded in *IronPython* applications.

*IronPython* developers who wish to use XML configuration have several
options to work around this limitation:

#. Use an instance of the
   :class:`aglyph.compat.ipyetree.XmlReaderTreeBuilder` class as the
   ``parser`` keyword argument to :class:`aglyph.context.XMLContext`.
#. Install an *expat* or *expat*-like library as a site package. A
   search engine query for "IronPython expat" is a good start. **This
   has not been tested with Aglyph.**
#. Write your own subclass of :class:`aglyph.context.Context` to parse
   a custom XML format using a .NET XML parser (e.g.
   ``System.Xml.XmlReader``).

.. note::

    Programmatic configuration using :class:`aglyph.context.Context`
    is fully supported in *IronPython*.

"""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "1.0.0"

import platform
from xml.etree.ElementTree import TreeBuilder

try:
    import clr
except ImportError:
    class XmlReaderTreeBuilder(object):
        def __init__(self, *args, **keywords):
            raise NotImplementedError("CLR is not available!")
else:
    clr.AddReference("System.Xml")

    from System.IO import StringReader
    from System.Text.RegularExpressions import Regex, RegexOptions
    from System.Xml import (DtdProcessing, ValidationType, XmlNodeType,
                            XmlReader, XmlReaderSettings)

    CRE_ENCODING = Regex("encoding=['\"](?<enc_name>.*?)['\"]",
                         RegexOptions.Compiled)


    class XmlReaderTreeBuilder(object):
        """Builds an
        `ElementTree <http://effbot.org/zone/element-index.htm>`_ using
        the .NET
        `System.Xml.XmlReader <http://msdn.microsoft.com/en-us/library/system.xml.xmlreader>`_
        XML parser.

        """

        def __init__(self, validating=False):
            """Set *validating* to ``True`` to use a validating parser.

            """
            super(XmlReaderTreeBuilder, self).__init__()
            settings = XmlReaderSettings()
            settings.IgnoreComments = True
            settings.IgnoreProcessingInstructions = True
            settings.IgnoreWhitespace = True
            if (not validating):
                settings.DtdProcessing = DtdProcessing.Ignore
                settings.ValidationType = ValidationType.None
            else:
                settings.DtdProcessing = DtdProcessing.Parse
                settings.ValidationType = ValidationType.DTD
            self.settings = settings
            self._target = TreeBuilder()
            self.version = "%s %s" % (platform.platform(),
                                          platform.python_compiler())
            self._buffer = []
            self._document_encoding = "utf-8" # default

        def feed(self, data):
            """Adds more XML data to be parsed.

            *data* is raw XML read from a stream or passed in as a
            string.

            .. note::

                All *data* across calls to this method are buffered
                internally; the parser itself is not actually created
                until the :func:`close` method is called.

            """
            self._buffer.append(data)

        def close(self):
            """Parses the XML from the internal buffer to build an
            element tree.

            :returns: the root element of the XML document
            :rtype: :class:`xml.etree.ElementTree.ElementTree`

            """
            reader = XmlReader.Create(StringReader("".join(self._buffer)),
                                      self.settings)
            self._buffer = None
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

        def _parse_xml_declaration(self, xml_decl):
            """Parses the document encoding from *xml_decl*.

            *xml_decl* is the content of the XML declaration as reported
            by
            `System.Xml.XmlReader <http://msdn.microsoft.com/en-us/library/system.xml.xmlreader>`_
            (node type
            `XmlNodeType.XmlDeclaration <http://msdn.microsoft.com/en-us/library/system.xml.xmlnodetype>`_).

            """
            enc_name = CRE_ENCODING.Match(xml_decl).Groups["enc_name"].Value
            if (enc_name):
                self._document_encoding = enc_name

        def _start_element(self, reader):
            """Notifies the tree builder that a start element has been
            encountered.

            *reader* is a reference to a .NET
            `System.Xml.XmlReader <http://msdn.microsoft.com/en-us/library/system.xml.xmlreader>`_.

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
