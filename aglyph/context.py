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

"""The classes in this module are used to define collections
("contexts") of related components and templates.

A context can be created in pure Python. This approach involves use of
the following API classes:

* :class:`aglyph.component.Template`
* :class:`aglyph.component.Component`
* :class:`aglyph.component.Reference` (used to indicate that one
  component depends on another component)
* :class:`aglyph.component.Evaluator` (used as a partial function to
  lazily evaluate component initialization arguments and attributes)
* :class:`aglyph.context.Context`

.. versionadded:: 1.1.0
   :class:`aglyph.binder.Binder` offers an alternative approach to
   programmatic configuration, which is more succinct than using the
   API classes noted above.

Alternatively, a context can be defined using a declarative XML syntax
that conforms to the :download:`Aglyph context DTD
<../../resources/aglyph-context.dtd>` (included in the *resources/*
directory of the distribution). This approach requires only the
:class:`aglyph.context.XMLContext` class, which parses the XML document
and then uses the API classes mentioned above to populate the context.

.. versionchanged:: 2.0.0
   IronPython applications that use XML contexts are **no longer**\
   required to pass an\
   :class:`aglyph.compat.ipyetree.XmlReaderTreeBuilder` instance to\
   :meth:`XMLContext.__init__`. Aglyph now uses an appropriate default\
   parser based on the current Python implementation.

"""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "2.1.0"

import functools
import logging
import sys
import warnings
import xml.etree.ElementTree as ET

from aglyph import AglyphDeprecationWarning, AglyphError
from aglyph.compat import (
    DataType,
    DoctypeTreeBuilder,
    etree_iter,
    is_ironpython,
    is_python_2,
    RESTRICTED_BUILTINS,  # deprecated
    TextType,
)
from aglyph.component import (
    Component,
    Evaluator,
    Reference,
    Strategy,
    Template,
)

__all__ = ["Context", "XMLContext"]

_logger = logging.getLogger(__name__)


class Context(dict):
    """A mapping of unique IDs to :class:`Component` and
    :class:`Template` objects.

    """

    __logger = logging.getLogger("%s.Context" % __name__)

    def __init__(self, context_id, after_inject=None, before_clear=None):
        """
        :arg str context_id: a unique ID for this context
        :keyword str after_inject: specifies the name of the method\
                                   that will be called (if it exists)\
                                   on **all** component objects after\
                                   all of their dependencies have been\
                                   injected
        :keyword str before_clear: specifies the name of the method\
                                   that will be called (if it exists)\
                                   on **all** singleton, borg, and\
                                   weakref objects immediately before\
                                   they are cleared from cache

        """
        self.__logger.debug("TRACE %r, after_inject=%r, before_clear=%r",
                            context_id, after_inject, before_clear)
        super(Context, self).__init__()
        self._context_id = context_id
        self._after_inject = after_inject
        self._before_clear = before_clear

    @property
    def context_id(self):
        """The unique context ID *(read-only)*."""
        return self._context_id

    @property
    def after_inject(self):
        """The name of the component object method that will be called
        after **all** dependencies have been injected into that
        component object.

        """
        return self._after_inject

    @property
    def before_clear(self):
        """The name of the component object method that will be called
        immediately before the object is cleared from cache.

        .. warning::
           This property is not applicable to "prototype" component
           objects, and is **not** guaranteed to be called for "weakref"
           component objects.

        """
        return self._before_clear

    def get_component(self, component_id):
        """Return the :class:`Component` identified by *component_id*.

        :arg str component_id: a unique ID that identifies a\
                               :class:`Component`
        :return: the :class:`Component` identified by *component_id*
        :rtype: :class:`Component` if *component_id* is mapped in this\
                context, else ``None``

        """
        obj = self.get(component_id)
        return obj if isinstance(obj, Component) else None

    def iter_components(self):
        """Yield all definitions in this context that are instances of
        :class:`Component`.

        :return: a :class:`Component` generator

        """
        for obj in self.values():
            if isinstance(obj, Component):
                yield obj

    def add(self, obj):
        """Add *obj*, which must be a component or template, to this
        context.

        :arg obj: the :class:`Component` or :class:`Template` to add to\
                  this context
        :raise AglyphError: if *obj.unique_id* is already mapped

        .. deprecated:: 2.1.0
           use the :meth:`dict.__contains__` and
           :meth:`dict.__setitem__` protocols instead.

        """
        self.__logger.debug("TRACE %r", obj)
        warnings.warn(
            AglyphDeprecationWarning("Context.add",
                replacement="the dict.__contains__ and dict.__setitem__ "
                            "protocols"))
        if (obj.unique_id in self):
            raise AglyphError(
                "component or template with ID %r already mapped in %s" %
                (obj.unique_id, self))
        self[obj.unique_id] = obj

    def add_or_replace(self, obj):
        """Add *obj* (which must be a component or template) to this
        context, replacing any component or template with the same ID
        that is already mapped.

        :arg obj: the :class:`Component` or :class:`Template` to add to\
                  this context
        :return: the component or template that was replaced, or\
                 ``None`` if *obj.unique_id* is not already mapped
        :rtype: :class:`Component` or :class:`Template`

        .. note::
           This method will **not** replace a component with a template
           or vice-versa; if the object that would be replaced is not
           the same type as the replacement, :class:`TypeError` is
           raised.

        .. deprecated:: 2.1.0
           use the standard :meth:`dict.__setitem__` protocol instead.

        """
        self.__logger.debug("TRACE %r", obj)
        warnings.warn(
            AglyphDeprecationWarning("Context.add_or_replace",
                replacement="the dict.__setitem__ protocol"))
        replaced_obj = self.get(obj.unique_id)
        if (replaced_obj is not None):
            self.__logger.info("%r is replacing %r in %r",
                               obj, replaced_obj, self)
        self[obj.unique_id] = obj
        self.__logger.debug("RETURN %r", replaced_obj)
        return replaced_obj

    def remove(self, unique_id):
        """Remove the component or template identified by *id_* from
        this context.

        :arg str unique_id: identifies the component or template to\
                            remove
        :return: the component or template that was removed, or\
                 ``None`` if *unique_id* is not mapped
        :rtype: :class:`Component` or :class:`Template`

        .. deprecated:: 2.1.0
           use the :meth:`dict.__contains__` and
           :meth:`dict.__delitem__` protocols instead.

        """
        self.__logger.debug("TRACE %r", unique_id)
        warnings.warn(
            AglyphDeprecationWarning("Context.remove",
                replacement="the dict.__contains__ and dict.__delitem__ "
                            "protocols"))
        obj = self.pop(unique_id) if (unique_id in self) else None
        self.__logger.debug("RETURN %r", obj)
        return obj

    def __repr__(self):
        return "%s.%s(%r, after_inject=%r, before_clear=%r)" % (
            self.__class__.__module__, self.__class__.__name__,
            self._context_id, self._after_inject, self._before_clear)


class XMLContext(Context):
    """A mapping of unique IDs to :class:`Component` and
    :class:`Template` objects.

    Components and templates are declared in an XML document that
    conforms to the :download:`Aglyph context DTD
    <../../resources/aglyph-context.dtd>` (included in the *resources/*
    directory of the distribution).

    """

    __logger = logging.getLogger("%s.XMLContext" % __name__)

    def __init__(self, source, parser=None,
                 default_encoding=sys.getdefaultencoding()):
        """
        :arg source: a filename or stream from which XML data is read
        :keyword xml.etree.ElementTree.XMLParser parser:\
           the ElementTree parser to use (instead of Aglyph's default)
        :keyword str default_encoding: the default character set used\
                                       to encode certain element content

        In most cases, *parser* should be left unspecified. Aglyph's
        default parser will be sufficient for all but extreme edge
        cases.

        *default_encoding* is the character set used to encode
        ``<bytes>`` or ``<str>`` (under Python 2) element content when
        an **@encoding** attribute is *not* specified on those elements.
        It defaults to the system-dependent value of
        :func:`sys.getdefaultencoding`. **This is not related to the
        document encoding!**

        .. versionchanged:: 2.0.0
           IronPython applications are no longer required to specify a\
           *parser*. See :doc:`aglyph.compat.ipyetree` for more
           information.

        .. note::
           Aglyph uses a non-validating XML parser by default, so DTD
           conformance is not enforced at runtime. It is recommended
           that XML contexts be validated at least once (manually)
           during testing.

        """
        self.__logger.debug("TRACE %r parser=%r, default_encoding=%r",
                            source, parser, default_encoding)
        # alias the correct _parse_str method based on Python version
        if (is_python_2):
            self._parse_str = self.__parse_str_as_data
        else: # assume 3
            self._parse_str = self.__parse_str_as_text
        self._default_encoding = default_encoding
        if (parser is None):
            tree_builder = DoctypeTreeBuilder()
            if (not is_ironpython):
                et_parser = ET.XMLParser(target=tree_builder)
            else:
                from aglyph.compat.ipyetree import CLRXMLParser
                et_parser = CLRXMLParser(target=tree_builder)
        else:
            et_parser = parser
        tree = ET.parse(source, parser=et_parser)
        root = tree.getroot()
        if (root.tag != "context"):
            raise AglyphError("expected root <context>, not <%s>" % root.tag)
        super(XMLContext, self).__init__(root.attrib["id"],
            after_inject=root.attrib.get("after-inject"),
            before_clear=root.attrib.get("before-clear"))
        for template_element in etree_iter(root, "template"):
            template_id = template_element.attrib["id"]
            if (template_id in self):
                raise AglyphError("template with ID %r already mapped in %s" %
                                  (template_id, self))
            template = self._parse_template(template_element)
            self._process_dependencies(template, template_element)
            self[template_id] = template
        for component_element in etree_iter(root, "component"):
            component_id = component_element.attrib["id"]
            if (component_id in self):
                raise AglyphError(
                    "component or template with ID %r already mapped in %s" %
                    (component_id, self))
            component = self._parse_component(component_element)
            self._process_dependencies(component, component_element)
            self[component_id] = component

    @property
    def default_encoding(self):
        """The default encoding of ``<bytes>`` or ``<str>`` (under
        Python 2) element content when an **@encoding** attribute is
        *not* specified.

        .. note::
           This is **unrelated** to the document encoding!

        """
        return self._default_encoding

    def _parse_template(self, template_element):
        """Create a template object from a ``<template>`` element.

        :arg xml.etree.ElementTree.Element template_element:\
           a ``<template>`` element
        :return: an Aglyph template object
        :rtype: :class:`aglyph.component.Template`

        """
        self.__logger.debug("TRACE %r", template_element)
        unique_id = template_element.attrib["id"]
        self.__logger.debug("parsing template[@id=%r]", unique_id)
        template = Template(unique_id,
            parent_id=template_element.get("parent-id"),
            after_inject=template_element.get("after-inject"),
            before_clear=template_element.get("before-clear"))
        self.__logger.debug("RETURN %r", template)
        return template

    def _parse_component(self, component_element):
        """Create a component object from a ``<component>`` element.

        :arg xml.etree.ElementTree.Element component_element:\
           a ``<component>`` element
        :return: an Aglyph component object
        :rtype: :class:`aglyph.component.Component`

        """
        self.__logger.debug("TRACE %r", component_element)
        unique_id = component_element.attrib["id"]
        self.__logger.debug("parsing component[@id=%r]", unique_id)
        # Component will reject unrecognized strategy
        component = Component(unique_id,
            # if the dotted-name is not specified explicitly, then the
            # component ID is assumed to represent a dotted-name
            dotted_name=component_element.get("dotted-name", unique_id),
            factory_name=component_element.get("factory-name"),
            member_name=component_element.get("member-name"),
            strategy=component_element.get("strategy", "prototype"),
            parent_id=component_element.get("parent-id"),
            after_inject=component_element.get("after-inject"),
            before_clear=component_element.get("before-clear"))
        self.__logger.debug("RETURN %r", component)
        return component

    def _process_component(self, component, component_element):
        """Parse the child elements of *component_element* to populate
        the *component* initialization arguments and attributes.

        :arg aglyph.component.Component component: an Aglyph component
        :arg xml.etree.ElementTree.Element component_element:\
           the element from which *component* was created

        .. deprecated:: 2.1.0
           use :meth:`_process_dependencies` instead.

        """
        warnings.warn(
            AglyphDeprecationWarning("XMLContext._process_component",
                replacement="XMLContext._process_dependencies"))
        self._process_dependencies(component, component_element)

    def _process_dependencies(self, depsupport, depsupport_element):
        """Parse the child elements of *depsupport_element* to populate
        the *depsupport* initialization arguments and attributes.

        :arg depsupport: a :class:`Template` or :class:`Component`
        :arg xml.etree.ElementTree.Element depsupport_element:\
           the ``<template>`` or ``<component>`` that was parsed to\
           create *depsupport*

        """
        self.__logger.debug("TRACE %r, %r", depsupport, depsupport_element)
        init_element = depsupport_element.find("init")
        if (init_element is not None):
            for (keyword, value) in self._parse_init(init_element):
                if (keyword is None):
                    depsupport.args.append(value)
                else:
                    depsupport.keywords[keyword] = value
        attributes_element = depsupport_element.find("attributes")
        if (attributes_element is not None):
            for (name, value) in self._parse_attributes(attributes_element):
                depsupport.attributes[name] = value
        self.__logger.debug(
            "%r has init_args=%r, init_keywords=%r, attributes=%r",
            depsupport, depsupport.args, depsupport.keywords,
            depsupport.attributes)

    def _parse_init(self, init_element):
        """Yield initialization arguments (positional and keyword)
        parsed from *init_element*.

        :arg xml.etree.ElementTree.Element init_element:\
           an ``<init>`` element
        :return: an iterator that yields the 2-tuple\
                 ``(keyword, value)``

        .. note::
           Both positional and keyword arguments are yielded by this
           method as a 2-tuple ``(keyword, value)``. For positional
           arguments, ``keyword`` will be ``None``.

        """
        self.__logger.debug("TRACE %r", init_element)
        for arg_element in etree_iter(init_element, "arg"):
            value = self._unserialize_element_value(arg_element)
            if ("keyword" not in arg_element.attrib):
                yield (None, value)
            else:
                keyword = arg_element.attrib["keyword"]
                yield (keyword, value)

    def _parse_attributes(self, attributes_element):
        """Yield attributes (fields, setter methods, or properties)
        parsed from *attributes_element*.

        :arg xml.etree.ElementTree.Element attributes_element:\
           an ``<attributes>`` element
        :return: an iterator that yields the 2-tuple ``(name, value)``

        """
        self.__logger.debug("TRACE %r", attributes_element)
        for attribute_element in etree_iter(attributes_element, "attribute"):
            name = attribute_element.attrib["name"]
            value = self._unserialize_element_value(attribute_element)
            yield (name, value)

    def _unserialize_element_value(self, element):
        """Return the appropriate Aglyph reference, Aglyph evaluator,
        partial object, or value for *element*.

        :arg xml.etree.ElementTree.Element element:\
           a "value container" element
        :return: the runtime object that is the result of processing\
                 *element*
        :rtype: :class:`aglyph.component.Reference`,\
                :class:`aglpyh.component.Evaluator`,\
                :obj:`functools.partial`, or Python builtin type

        *element* represents an ``<arg>``, ``<attribute>``, ``<key>``,
        or ``<value>`` element.

        """
        if ("reference" in element.attrib):
            return Reference(element.attrib["reference"])
        if (len(element) != 1):
            raise AglyphError("<%s> must contain exactly one child element" %
                              element.tag)
        return self._process_element(list(element)[0])

    def _process_element(self, element):
        """Create a usable Python object from *element*.

        :arg xml.etree.ElementTree.Element element:\
           a "value" element
        :return: a Python object representing the value of *element*

        *element* represents a ``<none>``, ``<true>``, ``<false>``,
        ``<bytes>``, ``<str>``, ``<unicode>``, ``<int>``, ``<float>``,
        ``<tuple>``, ``<list>``, or ``<dict>`` element.

        This method will return one of the following types, dependent
        upon the element:

        * a Python builtin object
        * a Python builtin constant
        * an :class:`aglyph.component.Reference`
        * an :class:`aglyph.component.Evaluator`
        * a :obj:`functools.partial`

        """
        self.__logger.debug("TRACE %r", element)
        parse = getattr(self, "_parse_%s" % element.tag)
        return parse(element)

    def _parse_true(self, true_element):
        """Return the builtin constant ``True``.

        :arg xml.etree.ElementTree.Element true_element:\
           a ``<true />`` element

        """
        return True

    def _parse_false(self, false_element):
        """Return the builtin constant ``False``.

        :arg xml.etree.ElementTree.Element false_element:\
           a ``<false />`` element

        """
        return False

    def _parse_none(self, none_element):
        """Return the builtin constant ``None``.

        :arg xml.etree.ElementTree.Element none_element:\
           a ``<none />`` element

        """
        return None

    def _parse_bytes(self, bytes_element):
        """Return an encoded bytes object parsed from *bytes_element*.

        :arg xml.etree.ElementTree.Element bytes_element:\
           a ``<bytes>`` element
        :rtype: :obj:`str` (Python 2) or :obj:`bytes` (Python 3)

        If the **bytes/@encoding** attribute is set, the text of the
        ``<bytes>`` element is encoded using the specified character
        set; otherwise, the text of the ``<bytes>`` element is encoded
        using :attr:`default_encoding`.

        Whitespace in the ``<bytes>`` element content is preserved.

        If *bytes_element* represents the empty element ``<bytes />``,
        ``str()`` (Python 2) or ``bytes()`` (Python 3) is returned.

        """
        if (bytes_element.text is not None):
            encoding = bytes_element.get("encoding", self._default_encoding)
            # .encode() will return the appropriate type
            return bytes_element.text.encode(encoding)
        else:
            return DataType()

    def __parse_str_as_data(self, str_element):
        """Return an encoded bytes object parsed from *str_element*.

        :arg xml.etree.ElementTree.Element str_element:\
           a ``<str>`` element
        :rtype: :obj:`str` (Python 2)

        .. note::
           This method is aliased as ``_parse_str`` when Aglyph is
           running under Python 2.

        If the **str/@encoding** attribute has been set, the text of the
        ``<str>`` element is encoded using the specified character set;
        otherwise, the text of the ``<str>`` element is encoded using
        :attr:`default_encoding`.

        Whitespace in the ``<str>`` element content is preserved.

        If *str_element* represents the empty element ``<str />``,
        ``str()`` is returned.

        """
        if (str_element.text is not None):
            encoding = str_element.get("encoding", self._default_encoding)
            return str_element.text.encode(encoding)
        else:
            return str()

    def __parse_str_as_text(self, str_element):
        """Return a Unicode text object parsed from *str_element*.

        :arg xml.etree.ElementTree.Element str_element:\
           a ``<str>`` element
        :rtype: :obj:`str` (Python 3)

        .. note::
           This method is aliased as ``_parse_str`` when Aglyph is
           running under Python 3.

        The text of the ``<str>`` element (which is already a Unicode
        string) is returned unchanged.

        Whitespace in the ``<str>`` element content is preserved.

        If *str_element* represents the empty element ``<str />``,
        ``str()`` is returned.

        """
        if (str_element.text is not None):
            encoding = str_element.get("encoding")
            if (encoding is not None):
                self.__logger.warning("ignoring str/@encoding attribute (%r)",
                                      encoding)
            return str_element.text
        else:
            return str()

    def _parse_unicode(self, unicode_element):
        """Return a Unicode text object parsed from *unicode_element*.

        :arg xml.etree.ElementTree.Element unicode_element:\
           a ``<unicode>`` element
        :rtype: :obj:`unicode` (Python 2) or :obj:`str` (Python 3)

        The text of the ``<unicode>`` element (which is already a
        Unicode string) is returned unchanged.

        Whitespace in the ``<unicode>`` element content is preserved.

        If *unicode_element* represents the empty element
        ``<unicode />``, ``unicode()`` (Python 2) or ``str()`` (Python
        3) is returned.

        """
        if (unicode_element.text is not None):
            return unicode_element.text
        else:
            return TextType()

    def _parse_int(self, int_element):
        """Return a builtin integer object parsed from *int_element*.

        :arg xml.etree.ElementTree.Element int_element:\
           am ``<int>`` element
        :rtype: :obj:`int`

        The **int/@base** attribute, if specified, is used as the number
        base to interpret the content of *int_element*.

        If *int_element* represents the empty element ``<int />``,
        ``int()`` is returned.

        .. warning::
           This method **may** return :obj:`long` in Python 2!

        """
        if (int_element.text is not None):
            base = int(int_element.get("base", "10"))
            # PYVER: IronPython 2.7 does not accept a 'base=' keyword argument
            return int(int_element.text, base)
        else:
            return int()

    def _parse_float(self, float_element):
        """Return a builtin floating-point object parsed from
        *float_element*.

        :arg xml.etree.ElementTree.Element float_element:\
           a ``<float>`` element
        :rtype: :obj:`float`

        If *float_element* represents the empty element ``<float />``,
        ``float()`` is returned.

        """
        if (float_element.text is not None):
            return float(float_element.text)
        else:
            return float()

    def _parse_list(self, list_element):
        """Return a :obj:`list` evaluator object parsed from
        *list_element*.

        :arg xml.etree.ElementTree.Element list_element:\
           a ``<list>`` element
        :rtype: :class:`aglyph.component.Evaluator`

        .. note::
           The evaluator returned by this method produces a new
           :obj:`list` object each time it is called.

        """
        items = [self._process_element(child_element)
                 for child_element in list_element]
        return Evaluator(list, items)

    def _parse_tuple(self, tuple_element):
        """Return a :obj:`tuple` evaluator object parsed from
        *tuple_element*.

        :arg xml.etree.ElementTree.Element tuple_element:\
           a ``<tuple>`` element
        :rtype: :class:`aglyph.component.Evaluator`

        .. note::
           The evaluator returned by this method produces a new
           :obj:`tuple` object each time it is called.

        .. note::
           If *tuple_element* is an empty element, ``tuple()`` is
           returned instead of an :class:`aglyph.component.Evaluator`.

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
        """Return a :obj:`dict` evaluator object parsed from
        *dict_element*.

        :arg xml.etree.ElementTree.Element dict_element:\
           a ``<dict>`` element
        :rtype: :class:`aglyph.component.Evaluator`

        .. note::
           The evaluator returned by this method produces a new
           :obj:`dict` object each time it is called.

        """
        # a list of 2-tuples, (key, value), used to initialize a dictionary
        items = []
        for item_element in etree_iter(dict_element, "item"):
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
        """Return a reference to another component in this context.

        :arg xml.etree.ElementTree.Element reference_element:\
           a ``<reference>`` element
        :rtype: :class:`aglyph.component.Reference`

        The **reference/@id** attribute is required, and will be used as
        the value to create an :class:`aglyph.component.Reference`.

        """
        component_id = reference_element.attrib["id"]
        return Reference(component_id)

    def _parse_eval(self, eval_element):
        """Return a partial object that will evaluate an expression
        parsed from *eval_element*.

        .. deprecated:: 2.0.0
           Use a top-level ``<component>`` instead of a nested
           ``<eval>``.

        :arg xml.etree.ElementTree.Element eval_element:\
           an ``<eval>`` element
        :rtype: :obj:`functools.partial`

        The partial object will use Python's :obj:`eval` to evaluate the
        expression when it is called.

        The environment for :obj:`eval` is a restricted subset of
        :mod:`builtins`, providing access to the following builtins
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

        .. seealso::
           `Eval really is dangerous <http://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html>`_
              Ned Batchelder's insanely thorough discussion of :py:func:`eval`

        """
        warnings.warn(
            AglyphDeprecationWarning("Support for the <eval> element",
                                     replacement="a <component> element"))
        if (eval_element.text is None):
            raise AglyphError("<eval> cannot be an empty element")
        # the environment for an eval expression is a restricted subset of
        # __builtins__.
        return functools.partial(eval, eval_element.text,
                                 {"__builtins__": RESTRICTED_BUILTINS})

