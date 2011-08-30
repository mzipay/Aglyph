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

"""The classes in this module are used to define collections of related
components (:class:`aglyph.component.Component` instances), called
"contexts" in Aglyph.

A context can be created in pure Python. This approach involves use of
the following API classes:

* :class:`aglyph.context.Context` (required)
* :class:`aglyph.component.Component` (required)
* :class:`aglyph.component.Reference` (used to indicate that a component
  depends on another component)
* :class:`aglyph.component.Strategy` (defines component assembly
  strategies)
* :class:`aglyph.component.Evaluator` (used as a partial function to
  lazily evaluate component arguments/attributes)

Alternatively, a context can be defined using a declarative XML syntax
that conforms to the
:download:`aglyph-context-1.0.0 DTD <../../resources/aglyph-context-1.0.0.dtd>`
(included in the *resources/* directory of the distribution). This
approach requires only the :class:`aglyph.context.XMLContext` class,
which parses the XML document and then uses the API classes mentioned
above to populate the context.

.. note::

    An additional class is needed in *IronPython* applications that use XML
    contexts: :class:`aglyph.compat.ipyetree.XmlReaderTreeBuilder`.

"""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "1.0.0"

import functools
import logging
import sys
from xml.etree.ElementTree import ElementTree

from aglyph import AglyphError
from aglyph.compat import (DataType, is_python_2, RESTRICTED_BUILTINS,
                           TextType)
from aglyph.component import Component, Evaluator, Reference, Strategy

__all__ = ["Context", "XMLContext"]

_logger = logging.getLogger(__name__)


class Context(dict):
    """A mapping of component IDs to
    :class:`aglyph.componnent.Component` objects."""

    _logger = logging.getLogger("%s.Context" % __name__)

    def __init__(self, context_id):
        """*context_id* is a string that uniquely identifies this
        context.

        """
        super(Context, self).__init__()
        self._context_id = context_id
        self._logger.info("initialized %s", self)

    @property
    def context_id(self):
        return self._context_id

    def add(self, component):
        """Adds *component* to this context.

        *component* is an :class:`aglyph.component.Component`.

        :raises aglyph.AglyphError: if *component.component_id* is already
                             contained in this context

        """
        if (component.component_id in self):
            raise AglyphError("component with ID %r is already defined in %s" %
                              (component.component_id, self))
        self[component.component_id] = component

    def add_or_replace(self, component):
        """Adds *component* to this context, **replacing** any component
        with the same ``component_id`` that already exists.

        *component* is an :class:`aglyph.component.Component`.

        :returns: the component that was replaced
        :rtype: :class:`aglyph.component.Component` (or ``None`` if
                no replacement was made)

        """
        replaced_component = self.get(component.component_id)
        if ((replaced_component is not None) and
            self._logger.isEnabledFor(logging.WARNING)):
            self._logger.warning("%s is replacing %s in %s", component,
                                 replaced_component, self)
        self[component.component_id] = component
        return replaced_component

    def remove(self, component_id):
        """Removes a component from this context.

        *component* is an :class:`aglyph.component.Component`.

        :returns: the component that was removed
        :rtype: :class:`aglyph.component.Component` (or ``None`` if
                *component.component_id* was not in this context)

        """
        component = self.get(component_id)
        if (component is not None):
            del self[component_id]
        return component

    def __repr__(self):
        return "%s:%s<%r>" % (self.__class__.__module__,
                              self.__class__.__name__, self._context_id)


class XMLContext(Context):
    """Populates a new context by parsing an XML document.

    The XML document must conform to the
    :download:`aglyph-context-1.0.0 DTD <../../resources/aglyph-context-1.0.0.dtd>`
    (included in the *resources/* directory of the distribution).

    """

    _logger = logging.getLogger("%s.XMLContext" % __name__)

    def __init__(self, source, parser=None,
                 default_encoding=sys.getdefaultencoding()):
        """*source* is a filename or stream from which XML data is read.

        *parser*, if specified, is an *ElementTree* parser; it is passed
        as the second argument to
        :func:`xml.etree.ElementTree.ElementTree.parse`. In most
        cases it is unnecessary to specify a value for *parser* (as the
        default works fine on **most** Python implementations - see the
        warning below).

        *default_encoding* is the character set used to encode
        ``<bytes>`` or ``<str>`` (under Python 2) element content when
        an **@encoding** attribute is *not* specified on those elements.
        It defaults to ``sys.getdefaultencoding()``. **This is not
        related to the document encoding!**

        .. warning::

            *IronPython* developers **must** specify a *parser* because
            the default Python XML parser (expat) is not available in
            *IronPython*. Please see :doc:`aglyph.compat.ipyetree`.

        .. note::

            Aglyph uses a non-validating XML parser by default, so DTD
            conformance is not enforced at runtime. It is recommended
            that XML contexts be validated at least once (manually)
            during testing.

        """
        self._logger.info("parsing context from %r", source)
        # alias the correct _parse_str method based on Python version
        if (is_python_2):
            self._parse_str = self.__parse_str_as_data
        else: # assume 3
            self._parse_str = self.__parse_str_as_text
        self._logger.info("default encoding is %r", default_encoding)
        self._default_encoding = default_encoding
        root = ElementTree().parse(source, parser)
        if (root.tag != "context"):
            raise AglyphError("expected root <context>, not <%s>" % root.tag)
        super(XMLContext, self).__init__(root.attrib["id"])
        # Element.iter is not available in Python 2.5, 2.6, and 3.1, but IS
        # available in 2.7 and 3.2 (!?) - just use getiterator
        for component_element in root.getiterator("component"):
            component = self._parse_component(component_element)
            self._process_component(component, component_element)
            # this will raise AglyphError if the component.component_id has
            # already been added
            self.add(component)

    @property
    def default_encoding(self):
        return self._default_encoding

    def _parse_component(self, component_element):
        """Creates an :class:`aglyph.component.Component` from
        *component_element*.

        *component_element* is an
        :class:`xml.etree.ElementTree.Element` representing a
        ``<component>`` element.

        """
        component_id = component_element.attrib["id"]
        self._logger.debug("parsing component[@id=%r]", component_id)
        # if the dotted-name is not specified explicitly, then the component ID
        # is assumed to represent a dotted-name
        dotted_name = component_element.get("dotted-name", component_id)
        strategy = component_element.get("strategy", Strategy.PROTOTYPE)
        # Component will reject unrecognized strategy
        return Component(component_id, dotted_name, strategy)

    def _process_component(self, component, component_element):
        """Parses the child elements of *component_element* to populate
        the *component* initialization arguments and attributes.

        *component* is an :class:`aglyph.component.Component`.
        *component_element* is an
        :class:`xml.etree.ElementTree.Element` representing a
        ``<component>`` element.

        """
        init_element = component_element.find("init")
        if (init_element is not None):
            for (keyword, value) in self._parse_init(init_element):
                if (keyword is None):
                    component.init_args.append(value)
                else:
                    component.init_keywords[keyword] = value
        attributes_element = component_element.find("attributes")
        if (attributes_element is not None):
            for (name, value) in self._parse_attributes(attributes_element):
                component.attributes[name] = value
        if (self._logger.isEnabledFor(logging.DEBUG)):
            self._logger.debug("%d args, %r keywords, %r attributes for %s" %
                               (len(component.init_args),
                                list(component.init_keywords.keys()),
                                list(component.attributes.keys()), component))

    def _parse_init(self, init_element):
        """Yields initialization arguments (positional and keyword)
        parsed from *init_element*.

        *init_element* is an :class:`xml.etree.ElementTree.Element`
        representing an ``<init>`` element.

        """
        # Element.iter is not available in Python 2.5, 2.6, and 3.1, but IS
        # available in 2.7 and 3.2 (!?) - just use getiterator
        for arg_element in init_element.getiterator("arg"):
            value = self._unserialize_element_value(arg_element)
            if ("keyword" not in arg_element.attrib):
                yield (None, value)
            else:
                keyword = arg_element.attrib["keyword"]
                yield (keyword, value)

    def _parse_attributes(self, attributes_element):
        """Yields attributes (fields, setter methods, or properties)
        parsed from *attributes_element*.

        *attributes_element* is an
        :class:`xml.etree.ElementTree.Element` representing an
        ``<attributes>`` element.

        """
        # Element.iter is not available in Python 2.5, 2.6, and 3.1, but IS
        # available in 2.7 and 3.2 (!?) - just use getiterator
        for attribute_element in attributes_element.getiterator("attribute"):
            name = attribute_element.attrib["name"]
            value = self._unserialize_element_value(attribute_element)
            yield (name, value)

    def _unserialize_element_value(self, element):
        """Returns the value, :class:`aglyph.component.Reference`,
        :class:`aglpyh.component.Evaluator`, or
        :func:`functools.partial` object that is the result of
        processing *element*.

        *element* is an :class:`xml.etree.ElementTree.Element`
        representing a "value container" element (i.e. ``<arg>``,
        ``<attribute>``, ``<key>``, or ``<value>``).

        """
        if ("reference" in element.attrib):
            return Reference(element.attrib["reference"])
        if (len(element) != 1):
            raise AglyphError("<%s> must contain exactly one child element!!" %
                              element.tag)
        return self._process_element(list(element)[0])

    def _process_element(self, element):
        """Creates a usable Python object from *element*.

        *element* is an :class:`xml.etree.ElementTree.Element`
        representing a "value" element (e.g. ``<int>``,
        ``<reference>``).

        This method will return one of the following types:

        * a built-in object (e.g. an ``int``, a ``str``)
        * a built-in constant (e.g. ``True``, ``False``, ``None``)
        * an :class:`aglyph.component.Reference`
        * an :class:`aglyph.component.Evaluator`
        * a :func:`functools.partial`

        """
        parse = getattr(self, "_parse_%s" % element.tag)
        return parse(element)

    def _parse_true(self, true_element):
        """Returns the built-in constant ``True``.

        *true_element* is an :class:`xml.etree.ElementTree.Element`
        representing a ``<true/>`` element.

        """
        return True

    def _parse_false(self, false_element):
        """Returns the built-in constant ``False``.

        *false_element* is an :class:`xml.etree.ElementTree.Element`
        representing a ``<false/>`` element.

        """
        return False

    def _parse_none(self, none_element):
        """Returns the built-in constant ``None``.

        *none_element* is an :class:`xml.etree.ElementTree.Element`
        representing a ``<none/>`` element.

        """
        return None

    def _parse_bytes(self, bytes_element):
        """Returns a built-in :func:`str` (Python 2) or :class:`bytes`
        (Python 3) object.

        *bytes_element* is an :class:`xml.etree.ElementTree.Element`
        representing a ``<bytes>`` element.

        If the **bytes/@encoding** attribute has been set, the text of
        the ``<bytes>`` element is encoded using the specified character
        set; otherwise, the text of the ``<bytes>`` element is encoded
        using the XML document's encoding (defaulting to UTF-8).

        .. note::
            Whitespace in the ``<bytes>`` element's text is preserved.

        If *bytes_element* is an empty element, ``str()`` (Python 2) or
        ``bytes()`` (Python 3) is returned.

        :raises UnicodeEncodeError: if the text cannot be encoded
                                    according to the specified character
                                    set

        """
        if (bytes_element.text is not None):
            encoding = bytes_element.get("encoding", self._default_encoding)
            # .encode() will return the appropriate type
            return bytes_element.text.encode(encoding)
        else:
            return DataType()

    def __parse_str_as_data(self, str_element):
        """Returns a built-in ``str`` (Python 2 encoded byte data)
        object.

        .. note::

            This method is aliased as ``_parse_str(self, str_element)``
            when Aglyph is running under Python 2.

        *str_element* is an :class:`xml.etree.ElementTree.Element`
        representing a ``<str>`` element.

        If the **str/@encoding** attribute has been set, the text of the
        ``<str>`` element is encoded using the specified character set;
        otherwise, the text of the ``<str>`` element is encoded using
        the XML document's encoding (defaulting to UTF-8).

        .. note::

            Whitespace in the ``<str>`` element's text is preserved.

        If *str_element* is an empty element, ``str()`` is returned.

        :raises UnicodeEncodeError: if the text cannot be encoded
                                    according to the specified character
                                    set

        """
        if (str_element.text is not None):
            encoding = str_element.get("encoding", self._default_encoding)
            return str_element.text.encode(encoding)
        else:
            return str()

    def __parse_str_as_text(self, str_element):
        """Returns a built-in ``str`` (Python 3 Unicode text) object.

        .. note::

            This method is aliased as ``_parse_str(self, str_element)``
            when Aglyph is running under Python 3.

        *str_element* is an :class:`xml.etree.ElementTree.Element`
        representing a ``<str>`` element.

        The text of the ``<str>`` element (which is already a Unicode
        string) is returned unchanged.

        .. note::
            Whitespace in the ``<str>`` element's text is preserved.

        If *str_element* is an empty element, ``str()`` is returned.

        """
        if (str_element.text is not None):
            encoding = str_element.get("encoding")
            if (encoding is not None):
                self._logger.warning("ignoring str/@encoding attribute (%r)",
                                     encoding)
            return str_element.text
        else:
            return str()

    def _parse_unicode(self, unicode_element):
        """Returns a built-in ``unicode`` (Python 2) or ``str``
        (Python 3) object.

        *unicode_element* is an :class:`xml.etree.ElementTree.Element`
        representing a ``<unicode>`` element.

        The text of the ``<unicode>`` element (which is already a
        Unicode string) is returned unchanged.

        .. note::
            Whitespace in the ``<unicode>`` element's text is preserved.

        If *unicode_element* is an empty element, ``unicode()``
        (Python 2) or ``str()`` (Python 3) is returned.

        """
        if (unicode_element.text is not None):
            return unicode_element.text
        else:
            return TextType()

    def _parse_int(self, int_element):
        """Returns a built-in :func:`int` object.

        *int_element* is an :class:`xml.etree.ElementTree.Element`
        representing an ``<int>`` element.

        The text of the ``<int>`` element is passed as the first
        argument to the built-in function :func:`int`.

        The **int/@base** attribute, if specified, is passed as the
        second argument to the built-in function :func:`int`.

        If *int_element* is an empty element, ``int()`` is returned.

        """
        if (int_element.text is not None):
            base = int(int_element.get("base", "10"))
            return int(int_element.text, base)
        else:
            return int()

    def _parse_float(self, float_element):
        """Returns a built-in :func:`float` object.

        *float_element* is an :class:`xml.etree.ElementTree.Element`
        representing a ``<float>`` element.

        The text of the ``<float>`` element is passed as the argument to
        the built-in function :func:`float`.

        If *float_element* is an empty element, ``float()`` is returned.

        """
        if (float_element.text is not None):
            return float(float_element.text)
        else:
            return float()

    def _parse_list(self, list_element):
        """Returns an :class:`aglyph.component.Evaluator` that produces
        a built-in :func:`list` object when called.

        *list_element* is an :class:`xml.etree.ElementTree.Element`
        representing a ``<list>`` element.

        """
        items = [self._process_element(child_element)
                 for child_element in list_element]
        return Evaluator(list, items)

    def _parse_tuple(self, tuple_element):
        """Returns either an :class:`aglyph.component.Evaluator` that
        produces a built-in :func:`tuple` object when called, or an
        empty :func:`tuple` object.

        *tuple_element* is an :class:`xml.etree.ElementTree.Element`
        representing a ``<tuple>`` element.

        If *tuple_element* is an empty element, ``tuple()`` is returned.

        """
        children = list(tuple_element)
        if (len(children)):
            items = [self._process_element(child_element)
                     for child_element in children]
            return Evaluator(tuple, items)
        else:
            # a tuple is immutable, so there's no sense in paying the overhead
            # of evaluation for an empty tuple
            return tuple()

    def _parse_dict(self, dict_element):
        """Returns an :class:`aglyph.component.Evaluator` that produces
        a built-in :func:`dict` object when called.

        *dict_element* is an :class:`xml.etree.ElementTree.Element`
        representing a ``<dict>`` element.

        """
        # a list of 2-tuples, (key, value), used to initialize a dictionary
        items = []
        # Element.iter is not available in Python 2.5, 2.6, and 3.1, but IS
        # available in 2.7 and 3.2 (!?) - just use getiterator
        for item_element in dict_element.getiterator("item"):
            key_element = item_element.find("key")
            if (key_element is None):
                raise AglyphError("item/key is required")
            value_element = item_element.find("value")
            if (value_element is None):
                raise AglyphError("item/value is required")
            items.append((self._unserialize_element_value(key_element),
                          self._unserialize_element_value(value_element)))
        return Evaluator(dict, items)

    def _parse_reference(self, reference_element):
        """Returns an :class:`aglyph.component.Reference`.

        *reference_element* is an :class:`xml.etree.ElementTree.Element`
        representing a ``<reference>`` element.

        The **reference/@id** attribute is required, and will be used as
        the value to create an :class:`aglyph.component.Reference`.

        """
        component_id = reference_element.attrib["id"]
        return Reference(component_id)

    def _parse_eval(self, eval_element):
        """Returns a :func:`functools.partial` that will evaluate an
        expression when called, using the built-in :func:`eval`
        function.

        *eval_element* is an :class:`xml.etree.ElementTree.Element`
        representing an ``<eval>`` element.

        The environment for :func:`eval` is a restricted subset of
        :mod:`builtins`, providing access to the following built-ins
        **only** (and subject to availability based on Python version):

        .. hlist::
            :columns: 5

            * ``ArithmeticError``
            * ``AssertionError``
            * ``AttributeError``
            * ``BaseException``
            * ``BufferError``
            * ``BytesWarning``
            * ``DeprecationWarning``
            * ``EOFError``
            * ``Ellipsis``
            * ``EnvironmentError``
            * ``Exception``
            * ``False``
            * ``FloatingPointError``
            * ``FutureWarning``
            * ``GeneratorExit``
            * ``IOError``
            * ``ImportError``
            * ``ImportWarning``
            * ``IndentationError``
            * ``IndexError``
            * ``KeyError``
            * ``KeyboardInterrupt``
            * ``LookupError``
            * ``MemoryError``
            * ``NameError``
            * ``None``
            * ``NotImplemented``
            * ``NotImplementedError``
            * ``OSError``
            * ``OverflowError``
            * ``PendingDeprecationWarning``
            * ``ReferenceError``
            * ``ResourceWarning``
            * ``RuntimeError``
            * ``RuntimeWarning``
            * ``StandardError``
            * ``StopIteration``
            * ``SyntaxError``
            * ``SyntaxWarning``
            * ``SystemError``
            * ``TabError``
            * ``True``
            * ``TypeError``
            * ``UnboundLocalError``
            * ``UnicodeDecodeError``
            * ``UnicodeEncodeError``
            * ``UnicodeError``
            * ``UnicodeTranslateError``
            * ``UnicodeWarning``
            * ``UserWarning``
            * ``ValueError``
            * ``Warning``
            * ``ZeroDivisionError``
            * ``__debug__``
            * ``abs``
            * ``all``
            * ``any``
            * ``apply``
            * ``ascii``
            * ``basestring``
            * ``bin``
            * ``bool``
            * ``buffer``
            * ``bytearray``
            * ``bytes``
            * ``callable``
            * ``chr``
            * ``cmp``
            * ``coerce``
            * ``complex``
            * ``dict``
            * ``dir``
            * ``divmod``
            * ``enumerate``
            * ``filter``
            * ``float``
            * ``format``
            * ``frozenset``
            * ``getattr``
            * ``hasattr``
            * ``hash``
            * ``hex``
            * ``id``
            * ``int``
            * ``intern``
            * ``isinstance``
            * ``issubclass``
            * ``iter``
            * ``len``
            * ``list``
            * ``long``
            * ``map``
            * ``max``
            * ``memoryview``
            * ``min``
            * ``next``
            * ``object``
            * ``oct``
            * ``ord``
            * ``pow``
            * ``range``
            * ``reduce``
            * ``repr``
            * ``reversed``
            * ``round``
            * ``set``
            * ``slice``
            * ``sorted``
            * ``str``
            * ``sum``
            * ``tuple``
            * ``type``
            * ``unichr``
            * ``unicode``
            * ``xrange``
            * ``zip``

        """
        if (eval_element.text is None):
            raise AglyphError("<eval> cannot be an empty element")
        # the environment for an eval expression is a restricted subset of
        # __builtins__.
        return functools.partial(eval, eval_element.text,
                                 {"__builtins__": RESTRICTED_BUILTINS})
