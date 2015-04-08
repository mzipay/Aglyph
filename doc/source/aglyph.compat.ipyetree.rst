==========================================================================
:mod:`aglyph.compat.ipyetree` --- an *ElementTree* parser for *IronPython*
==========================================================================

:Release: |release|

.. automodule:: aglyph.compat.ipyetree

.. class:: CLRXMLParser(target=None, validating=False)

   Bases: :class:`xml.etree.ElementTree.XMLParser`

   An :class:`xml.etree.ElementTree.XMLParser` that delegates
   parsing to the .NET `System.Xml.XmlReader
   <http://msdn.microsoft.com/en-us/library/system.xml.xmlreader>`_
   parser.

   If *target* is omitted, a standard ``TreeBuilder`` instance is used.

   If *validating* is ``True``, the ``System.Xml.XmlReader`` parser will
   be configured for DTD validation.

   .. method:: feed(data)

      Add more XML data to be parsed.

      :param str data: raw XML read from a stream

      .. note::
         All *data* across calls to this method are buffered
         internally; the parser itself is not actually created
         until the :meth:`close` method is called.

   .. method:: close()

      Parse the XML from the internal buffer to build an
      element tree.

      :return: the root element of the XML document
      :rtype: :class:`xml.etree.ElementTree.ElementTree`

.. autoclass:: XmlReaderTreeBuilder(validating=False)
   :members:

A note on *IronPython* Unicode issues
=====================================

*IronPython* does not have an encoded-bytes ``str`` type; rather, the
``str`` and ``unicode`` types are one and the same:

>>> str is unicode
True

Unfortunately, this means that *IronPython* **cannot not properly decode byte
streams/sequences to Unicode strings** using Python language facilities.
Consider the simple example of a UTF-8-encoded XML file *test.xml*::

   <?xml version="1.0" encoding="utf-8"?>
   <test>façade</test>

.. rubric:: CPython

>>> open("test.xml", "rb").read()
'<?xml version="1.0" encoding="utf-8"?>\n<test>fa\xc3\xa7ade</test>\n'

.. rubric:: IronPython

>>> open("test.xml", "rb").read()
u'<?xml version="1.0" encoding="utf-8"?>\n<test>fa\xc3\xa7ade</test>\n'

The byte sequence ``C3 A7`` in UTF-8-encoded byte string represents a single
Unicode code point (U+00E7 LATIN SMALL LETTER C WITH CEDILLA), while the
*character* sequence ``C3 A7`` in a *Unicode* string are the Unicode code
points U+00C3 LATIN CAPITAL LETTER A WITH TILDE followed by
U+00A7 SECTION SIGN. Clearly the latter is incorrect.

In many cases, this difference between *CPython* and *IronPython* will be
transparent. For example:

.. rubric:: CPython

>>> "fa\xc3\xa7ade".decode("utf-8")
u'fa\xe7ade'

.. rubric:: IronPython

>>> u"fa\xc3\xa7ade".decode("utf-8")
u'fa\xe7ade'

However, *IronPython*'s behavior poses a problem for Aglyph XML context
parsing because the :class:`xml.etree.ElementTree.ElementTree` class uses
``open(source, "rb")`` (as in the first comparison) to access the file contents
when the *source* argument to :func:`xml.etree.ElementTree.ElementTree.parse`
is a string (filename). This would cause the XML parser to return the Unicode
string ``u"fa\xc3\xa7ade"`` as the value of the text node under ``<test>``.
If, for example, this was in an Aglyph ``<str>`` or ``<bytes>`` element (e.g.
``<str encoding="iso-8859-1">façade</str>``), Aglyph would attempt (correctly)
to encode the Unicode string using ISO-8859-1, which would result in an
**incorrect** ISO-8859-1 string under *IronPython*:

>>> u"fa\xc3\xa7ade".encode("iso-8859-1")
u'fa\xc3\xa7ade'

This happens because both ``'\xc3'`` and ``'\xa7'`` represent valid ISO-8859-1
characters (LATIN SMALL LETTER C WITH CEDILLA and SECTION SIGN, respectively).

One workaround is to use the .NET ``System.IO.StreamReader`` class instead of
the Python built-in function :func:`open`:

>>> from System.IO import StreamReader
>>> from System.Text import Encoding
>>> sr = StreamReader("test.xml", Encoding.UTF8)
>>> sr.ReadToEnd()
u'<?xml version="1.0" encoding="utf-8"?>\n<test>fa\xe7ade</test>\n'

Unfortunately, this requires knowledge of the file encoding prior to reading,
which isn't always possible when parsing XML. (Arguably, it should *not* need
to be known in advance for XML parsing, since the XML declaration should
convey this piece of metadata to the XML parser.)

Aglyph's :class:`aglyph.compat.ipyetree.XmlReaderTreeBuilder` takes a two-step
approach to work around *IronPython*'s Unicode issues when parsing an Aglyph
XML context document:

#. Save the document encoding from the XML declaration.
#. Use the document encoding to *decode* data before handing it off to
   :class:`aglyph.context.XMLContext`.

Step #1 is possible because, luckily, the
`System.Xml.XmlReader <http://msdn.microsoft.com/en-us/library/system.xml.xmlreader>`_
class reports
`XmlNodeType.XmlDeclaration <http://msdn.microsoft.com/en-us/library/system.xml.xmlnodetype>`_.

.. note::
   If the XML document does *not* specify an explicit encoding in the XML
   declaration, ``XmlReaderTreeBuilder`` assumes UTF-8.

Step #2 works because the same "glitch" that causes *IronPython*'s Unicode
issues can be exploited to work around it:

>>> str is unicode
True
>>> u"fa\xc3\xa7ade".decode("utf-8")
u'fa\xe7ade'
>>> "no non-ascii bytes".decode("utf-8")
'no non-ascii bytes'

Because of this, the text node string ``u"fa\xc3\xa7ade"`` can actually be
*decoded* to ``u"fa\xe7ade"`` before being handed off to
:class:`aglyph.context.XMLContext`, allowing ``XMLContext`` to remain ignorant
of *IronPython*'s Unicode issues.

