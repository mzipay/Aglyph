# -*- coding: UTF-8 -*-

# Copyright (c) 2006, 2011, 2013-2016 Matthew Zipay.
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

"""The classes in this module are used to define collections
("contexts") of related components and templates.

A context can be created in pure Python using the following API classes:

* :class:`aglyph.component.Template`
* :class:`aglyph.component.Component`
* :class:`aglyph.component.Reference` (used to indicate that one
  component depends on another component)
* :class:`aglyph.component.Evaluator` (used like a partial function to
  lazily evaluate component initialization arguments and attributes)
* :class:`aglyph.context.Context` or a subclass

Alternatively, a context can be defined using a declarative XML syntax
that conforms to the :download:`Aglyph context DTD
<../../resources/aglyph-context.dtd>` (included in the *resources/*
directory of the distribution). This approach requires only the
:class:`aglyph.context.XMLContext` class, which parses the XML document
and then uses the API classes mentioned above to populate the context.

"""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"

import logging
import sys
import xml.etree.ElementTree as ET

from autologging import logged, traced

from aglyph import AglyphError, _identify, __version__
from aglyph._compat import (
    AglyphDefaultXMLParser,
    DataType,
    DoctypeTreeBuilder,
    is_python_3,
    name_of,
    TextType,
)
from aglyph.component import (
    Component,
    Evaluator as evaluate,
    Reference as ref,
    Strategy,
    Template,
)

__all__ = ["Context", "evaluate", "ref", "XMLContext"]

_log = logging.getLogger(__name__)


@traced
@logged
class _ContextBuilder(object):

    def component(self,
            component_spec, parent_spec=None, strategy="prototype"):
        """Create, :meth:`register`, and return a :class:`Component`
        builder for *component_spec*.

        :arg component_spec:
           a context-unique identifier for this component; or the object
           whose dotted name will identify this component
        :keyword parent_spec:
           the context-unique identifier for this component's parent
           template or component definition; or the object whose dotted
           name identifies this component's parent definition
        :keyword str strategy:
           specifies the component assembly strategy

        .. note::
           This method is part of the Aglyph "fluent configuration" API.
           Callers should prefer calling one of the :meth:`prototype`,
           :meth:`singleton`, :meth:`borg`, or :meth:`weakref` methods
           directly; this method is exposed primarily as a convenience
           for scripted configuration.

        """
        component = Component(
            component_spec, parent_spec=parent_spec, strategy=strategy)
        self.register(component)
        return _ComponentBuilder(component)

    def prototype(self, component_spec, parent_spec=None):
        """Create, :meth:`register`, and return a
        :data:`prototype <aglyph.component.Strategy>` :class:`Component`
        builder for *component_spec*.

        :arg component_spec:
           a context-unique identifier for this component; or the object
           whose dotted name will identify this component
        :keyword parent_spec:
           the context-unique identifier for this component's parent
           template or component definition; or the object whose dotted
           name identifies this component's parent definition

        .. note::
           This method is part of the Aglyph "fluent configuration" API.

        """
        return self.component(
            component_spec, parent_spec=parent_spec, strategy="prototype")

    def singleton(self, component_spec, parent_spec=None):
        """Create, :meth:`register`, and return a
        :data:`singleton <aglyph.component.Strategy>` :class:`Component`
        builder for *component_spec*.

        :arg component_spec:
           a context-unique identifier for this component; or the object
           whose dotted name will identify this component
        :keyword parent_spec:
           the context-unique identifier for this component's parent
           template or component definition; or the object whose dotted
           name identifies this component's parent definition

        .. note::
           This method is part of the Aglyph "fluent configuration" API.

        """
        return self.component(
            component_spec, parent_spec=parent_spec, strategy="singleton")

    def borg(self, component_spec, parent_spec=None):
        """Create, :meth:`register`, and return a
        :data:`borg <aglyph.component.Strategy>` :class:`Component`
        builder for *component_spec*.

        :arg component_spec:
           a context-unique identifier for this component; or the object
           whose dotted name will identify this component
        :keyword parent_spec:
           the context-unique identifier for this component's parent
           template or component definition; or the object whose dotted
           name identifies this component's parent definition

        .. note::
           This method is part of the Aglyph "fluent configuration" API.

        """
        return self.component(
            component_spec, parent_spec=parent_spec, strategy="borg")

    def weakref(self, component_spec, parent_spec=None):
        """Create, :meth:`register`, and return a
        :data:`weakref <aglyph.component.Strategy>` :class:`Component`
        builder for *component_spec*.

        :arg component_spec:
           a context-unique identifier for this component; or the object
           whose dotted name will identify this component
        :keyword parent_spec:
           the context-unique identifier for this component's parent
           template or component definition; or the object whose dotted
           name identifies this component's parent definition

        .. note::
           This method is part of the Aglyph "fluent configuration" API.

        """
        return self.component(
            component_spec, parent_spec=parent_spec, strategy="weakref")

    def template(self, template_spec, parent_spec=None):
        """Create, :meth:`register`, and return a :class:`Template`
        builder for a template identified by *template_spec*.

        :arg template_spec:
           a context-unique identifier for this template; or the object
           whose dotted name will identify this template
        :keyword parent_spec:
           the context-unique identifier for this template's parent
           template or component definition; or the object whose dotted
           name identifies this template's parent definition

        .. note::
           This method is part of the Aglyph "fluent configuration" API.

        """
        template = Template(template_spec, parent_spec=parent_spec)
        self.register(template)
        return _TemplateBuilder(template)


@traced
@logged
class _CreationBuilder(object):

    def create(
            self, dotted_name_spec=None, factory_name=None, member_name=None):
        # do not overwrite the dotted_name if one was not specified explicitly
        if dotted_name_spec is not None:
            self._depsupport._dotted_name = _identify(dotted_name_spec)

        # factory_name and member_name are mutually exclusive
        if factory_name is not None and member_name is not None:
            raise AglyphError(
                "only one of factory_name or member_name may be specified")
        self._depsupport._factory_name = factory_name
        self._depsupport._member_name = member_name

        return self


@traced
@logged
class _InjectionBuilder(object):

    def init(self, *args, **keywords):
        """Configure the base initialization arguments (positional and
        keyword) for templates and/or components that will extend this
        template.

        :arg tuple args:
           the positional initialization arguments
        :arg dict keywords:
           the keyword initialization arguments

        .. note::
           Successive calls to this method on the same instance have a
           cumulative effect; the list of positional arguments is
           extended, and the dictionary of keyword arguments is updated.

        """
        self._depsupport.args.extend(args)
        self._depsupport.keywords.update(keywords)
        return self

    def set(self, **attributes):
        self._depsupport.attributes.update(attributes)
        return self


@traced
@logged
class _LifecycleBuilder(object):

    def call(self, after_inject=None, before_clear=None):
        self._depsupport._after_inject = after_inject
        self._depsupport._before_clear = before_clear
        # terminator


@traced
@logged
class _TemplateBuilder(_InjectionBuilder, _LifecycleBuilder):

    def __init__(self, template):
        """
        :arg aglyph.component.Template template:
           the template being defined

        Instances of ``_TemplateBuilder`` are returned by
        :meth:`Context.template`.

        """
        self._depsupport = template


@traced
@logged
class _ComponentBuilder(
        _CreationBuilder, _InjectionBuilder, _LifecycleBuilder):

    def __init__(self, component):
        """
        :arg aglyph.component.Component component:
           the component being defined

        Instances of ``_ComponentBuilder`` are returned by
        :meth:`Context.component`.

        """
        self._depsupport = component


@traced
@logged
class Context(dict, _ContextBuilder):
    """A mapping of unique IDs to :class:`Component` and
    :class:`Template` objects.

    """

    def __init__(self, context_id, after_inject=None, before_clear=None):
        """
        :arg str context_id:
           an identifier for this context
        :keyword str after_inject:
           specifies the name of the method that will be called (if it
           exists) on **all** component objects after all of their
           dependencies have been injected
        :keyword str before_clear:
           specifies the name of the method that will be called (if it
           exists) on **all** singleton, borg, and weakref objects
           immediately before they are cleared from cache

        """
        #PYVER: arguments to super() are implicit under Python 3
        super(Context, self).__init__()

        if not context_id:
            raise AglyphError(
                "%s ID must not be None or empty" % name_of(self.__class__))

        self._context_id = context_id
        self._after_inject = after_inject
        self._before_clear = before_clear

    @property
    def context_id(self):
        """The context identifier *(read-only)*."""
        return self._context_id

    @property
    def after_inject(self):
        """The name of the component object method that will be called
        after **all** dependencies have been injected into that
        component object *(read-only)*.

        """
        return self._after_inject

    @property
    def before_clear(self):
        """The name of the component object method that will be called
        immediately before the object is cleared from cache
        *(read-only)*.

        .. warning::
           This property is not applicable to "prototype" component
           objects, and is **not guaranteed** to be called for "weakref"
           component objects.

        """
        return self._before_clear

    def register(self, definition):
        """Add a component or template *definition* to this context.

        :arg definition:
           a :class:`Component` or :class:`Template` object
        :raise AglyphError:
           if a component or template with the same unique ID is already
           registered in this context

        .. note::
           To **replace** an already-registered component or template
           with the same unique ID, use :meth:`dict.__setitem__`
           directly.

        """
        if definition.unique_id in self:
            raise AglyphError(
                "%s with ID %r already mapped in %s" % (
                    name_of(definition.__class__), definition.unique_id, self))
        self[definition.unique_id] = definition

    def get_component(self, component_id):
        """Return the :class:`Component` identified by *component_id*.

        :arg str component_id:
           a unique ID that identifies a :class:`Component`
        :return:
           the :class:`Component` identified by *component_id*
        :rtype:
           :class:`Component` if *component_id* is mapped, else ``None``

        """
        obj = self.get(component_id)
        return obj if isinstance(obj, Component) else None

    def iter_components(self, strategy=None):
        """Yield all definitions in this context that are instances of
        :class:`Component`, optionally filtered by *strategy*.

        :keyword str strategy:
           only yield component definitions that use this assembly
           strategy (by default, **all** component definitions are
           yielded)
        :return:
           a :class:`Component` generator

        """
        for obj in self.values():
            if (isinstance(obj, Component) and
                    (strategy in [None, obj.strategy])):
                yield obj

    def __str__(self):
        return "<%s %r @%08x>" % (
            name_of(self.__class__), self._context_id, id(self))

    def __repr__(self):
        return "%s.%s(%r, after_inject=%r, before_clear=%r)" % (
            self.__class__.__module__, name_of(self.__class__),
            self._context_id, self._after_inject, self._before_clear)


@traced
@logged
class XMLContext(Context):
    """A mapping of unique IDs to :class:`Component` and
    :class:`Template` objects.

    Components and templates are declared in an XML document that
    conforms to the :download:`Aglyph context DTD
    <../../resources/aglyph-context.dtd>` (included in the *resources/*
    directory of the distribution).

    """

    def __init__(
            self, source, parser=None,
            default_encoding=sys.getdefaultencoding()):
        """
        :arg source:
           a filename or stream from which XML data is read
        :keyword xml.etree.ElementTree.XMLParser parser:
           the ElementTree parser to use (instead of Aglyph's default)
        :keyword str default_encoding:
           the default character set used to encode certain element
           content
        :raise AglyphError:
           if unexpected elements are encountered, or if expected
           elements are *not* encountered, in the document structure

        In most cases, *parser* should be left unspecified. Aglyph's
        default parser will be sufficient for all but extreme edge
        cases.

        *default_encoding* is the character set used to encode
        ``<bytes>`` (or ``<str>`` under Python 2) element content when
        an **@encoding** attribute is *not* specified on those elements.
        It defaults to the system-dependent value of
        :func:`sys.getdefaultencoding`. **This is not related to the
        document encoding!**

        .. note::
           Aglyph uses a non-validating XML parser by default, so DTD
           conformance is **not** enforced at runtime. It is recommended
           that XML contexts be validated at least once (manually)
           during testing.

           An :class:`AglyphError` *will* be raised under certain
           conditions (an unexpected element is encounted, or an
           expected element is *not* encountered), but Aglyph does not
           "reinvent the wheel" by implementing strict validation in
           the parsing logic.

        .. warning::
           Although Aglyph contexts are :class:`dict` types,
           ``XMLContext`` does not permit the same unique ID to be
           (re-)mapped multiple times.

           Attempting to define more than one ``<component>`` or
           ``<template>`` with the same ID will raise
           :class:`AglyphError` when the document is parsed.

           **After** an Aglyph ``<context>`` document has been
           successfully parsed, a unique component or template ID can be
           re-mapped using standard :class:`dict` protocols.

           .. seealso::
              Validity constraint: ID
                 https://www.w3.org/TR/REC-xml/#id

        """
        if parser is None:
            parser = AglyphDefaultXMLParser(target=DoctypeTreeBuilder())
        tree = ET.parse(source, parser=parser)
        root = tree.getroot()
        if root.tag != "context":
            raise AglyphError("expected root <context>, not <%s>" % root.tag)

        #PYVER: arguments to super() are implicit under Python 3
        super(XMLContext, self).__init__(
            root.get("id"), after_inject=root.get("after-inject"),
            before_clear=root.get("before-clear"))

        # alias the correct _parse_str method based on Python version
        if is_python_3:
            self._parse_str = self.__parse_str_as_text
        else:
            self._parse_str = self.__parse_str_as_data

        self._default_encoding = default_encoding

        for element in list(root):
            if element.tag == "component":
                depsupport = self._create_component(element)
            elif element.tag == "template":
                depsupport = self._create_template(element)
            else:
                raise AglyphError(
                    "unexpected element: /context/%s" % element.tag)
            self.register(depsupport)
            self._process_dependencies(depsupport, element)

        self.__repr = "%s.%s(%r, parser=%r, default_encoding=%r)" % (
            self.__class__.__module__, name_of(self.__class__),
            source, parser, default_encoding)

    @property
    def default_encoding(self):
        """The default encoding of ``<bytes>`` (or ``<str>`` under
        Python 2) element content when an **@encoding** attribute is
        *not* specified.

        .. note::
           This is **unrelated** to the document encoding!

        """
        return self._default_encoding

    def _create_template(self, template_element):
        """Create a template object from a ``<template>`` element.

        :arg xml.etree.ElementTree.Element template_element:
           a ``<template>`` element
        :return:
           an Aglyph template object
        :rtype:
           :class:`aglyph.component.Template`

        """
        return Template(
            template_element.get("id"),
            parent_spec=template_element.get("parent-id"),
            after_inject=template_element.get("after-inject"),
            before_clear=template_element.get("before-clear")
        )

    def _create_component(self, component_element):
        """Create a component object from a ``<component>`` element.

        :arg xml.etree.ElementTree.Element component_element:
           a ``<component>`` element
        :return:
           an Aglyph component object
        :rtype:
           :class:`aglyph.component.Component`

        """
        return Component(
            component_element.get("id"),
            dotted_name=component_element.get("dotted-name"),
            factory_name=component_element.get("factory-name"),
            member_name=component_element.get("member-name"),
            strategy=component_element.get("strategy", "prototype"),
            parent_spec=component_element.get("parent-id"),
            after_inject=component_element.get("after-inject"),
            before_clear=component_element.get("before-clear")
        )

    def _process_dependencies(self, depsupport, depsupport_element):
        """Parse the child elements of *depsupport_element* to populate
        the *depsupport* initialization arguments and attributess.

        :arg depsupport:
           a :class:`Template` or :class:`Component`
        :arg xml.etree.ElementTree.Element depsupport_element:
           the ``<template>`` or ``<component>`` that was parsed to
           create *depsupport*

        """
        children = list(depsupport_element)
        child_tags = [elem.tag for elem in children]
        if child_tags == ["init"]:
            init_element = children[0]
            attributes_element = None
        elif child_tags == ["init", "attributes"]:
            init_element, attributes_element = children
        elif child_tags == ["attributes"]:
            init_element = None
            attributes_element = children[0]
        elif not child_tags:
            init_element = None
            attributes_element = None
        else:
            dtag = depsupport_element.tag
            raise AglyphError(
                "unexpected element: %s/%s" %
                    (depsupport_element.tag, child_tags[0]))

        if init_element is not None:
            for (keyword, value) in self._process_init(init_element):
                if keyword is None:
                    depsupport.args.append(value)
                else:
                    depsupport.keywords[keyword] = value

        if attributes_element is not None:
            for (name, value) in self._process_attributes(attributes_element):
                depsupport.attributes[name] = value

        self.__log.debug(
            "%r has args=%r, keywords=%r, attributess=%r",
            depsupport, depsupport.args, depsupport.keywords,
            depsupport.attributes)

    def _process_init(self, init_element):
        """Yield initialization arguments (positional and keyword)
        parsed from *init_element*.

        :arg xml.etree.ElementTree.Element init_element:
           an ``<init>`` element
        :return:
           an iterator that yields the 2-tuple ``(keyword, value)``

        .. note::
           Both positional and keyword arguments are yielded by this
           method as a 2-tuple ``(keyword, value)``. For positional
           arguments, ``keyword`` will be ``None``.

        """
        for element in list(init_element):
            if element.tag != "arg":
                raise AglyphError("unexpected element: init/%s" % element.tag)
            keyword = element.get("keyword")
            if keyword == "":
                raise AglyphError("arg/@keyword cannot be empty")
            value = self._unserialize_element_value(element)
            yield (keyword, value)

    def _process_attributes(self, attributes_element):
        """Yield attributes (fields, setter methods, or properties)
        parsed from *attributes_element*.

        :arg xml.etree.ElementTree.Element attributes_element:
           an ``<attributes>`` element
        :return:
           an iterator that yields the 2-tuple ``(name, value)``

        """
        for element in list(attributes_element):
            if element.tag != "attribute":
                raise AglyphError(
                    "unexpected element: attributes/%s" % element.tag)
            name = element.get("name")
            if not name:
                raise AglyphError(
                    "attribute/@name is required and cannot be empty")
            value = self._unserialize_element_value(element)
            yield (name, value)

    def _unserialize_element_value(self, valuecontainer_element):
        """Return the appropriate object, value, Aglyph reference, or
        Aglyph evaluator for *element*.

        :arg xml.etree.ElementTree.Element valuecontainer_element:
           an element with a single child element that describes a value
        :return:
           the runtime object that is the result of processing
           *valuecontainer_element*
        :rtype:
           an object of a Python built-in type, a Python built-in
           constant, a :class:`Reference`, or an :class:`Evaluator`

        *valuecontainer_element* must be an ``<arg>``, ``<attribute>``,
        ``<key>``, or ``<value>`` element.

        """
        component_id = valuecontainer_element.get("reference")
        if component_id is not None:
            return ref(component_id)

        children = list(valuecontainer_element)
        if len(children) != 1:
            vtag = valuecontainer_element.tag
            raise AglyphError(
                "<%s> must contain exactly one child element; found %s" % (
                    vtag,
                    ", ".join("%s/%s" % (vtag, c.tag) for c in children)
                        if children else "no children"))

        return self._process_value_element(
            children[0], valuecontainer_element.tag)

    def _process_value_element(self, value_element, parent_tag):
        """Create a usable Python object from *value_element*.

        :arg xml.etree.ElementTree.Element value_element:
           an element that describes a value
        :arg str parent_tag:
           the name of the *value_element* parent element
        :return:
           a Python object that is the value of *value_element*

        *value_element* must be a ``<False />``, ``<True />``,
        ``<None />``, ``<bytes>``, ``<str>``, ``<unicode>``, ``<int>``,
        ``<float>``, ``<tuple>``, ``<list>``, ``<dict>``, or ``<set>``
        element.

        This method will return one of the following types, dependent
        upon the element:

        * an object of a Python built-in type
        * a Python built-in constant
        * an Aglyph :class:`Reference`
        * an Aglyph :class:`Evaluator`

        """
        parse_value = getattr(self, "_parse_%s" % value_element.tag, None)
        if parse_value is None:
            raise AglyphError(
                "unexpected element: %s/%s" % (parent_tag, value_element.tag))
        return parse_value(value_element)

    def _parse_False(self, false_element):
        """Return the builtin constant ``False``.

        :arg xml.etree.ElementTree.Element false_element:
           a ``<False />`` element

        """
        return False

    def _parse_True(self, true_element):
        """Return the builtin constant ``True``.

        :arg xml.etree.ElementTree.Element true_element:
           a ``<True />`` element

        """
        return True

    def _parse_None(self, none_element):
        """Return the builtin constant ``None``.

        :arg xml.etree.ElementTree.Element none_element:
           a ``<None />`` element

        """
        return None

    def _parse_bytes(self, bytes_element):
        """Return an encoded bytes object parsed from *bytes_element*.

        :arg xml.etree.ElementTree.Element bytes_element:
           a ``<bytes>`` element
        :rtype:
           :obj:`bytes` (Python 3) or :obj:`str` (Python 2)

        If the **bytes/@encoding** attribute is set, the text of the
        ``<bytes>`` element is encoded using the specified character
        set; otherwise, the text of the ``<bytes>`` element is encoded
        using :attr:`default_encoding`.

        Whitespace in the ``<bytes>`` element content is preserved.

        If *bytes_element* represents the empty element ``<bytes />``,
        ``bytes()`` (Python 3) or ``str()`` (Python 2) is returned.

        """
        if bytes_element.text is not None:
            encoding = bytes_element.get("encoding", self._default_encoding)
            # .encode() will return the appropriate type
            return bytes_element.text.encode(encoding)
        else:
            return DataType()

    def __parse_str_as_data(self, str_element):
        """Return an encoded bytes object parsed from *str_element*.

        :arg xml.etree.ElementTree.Element str_element:
           a ``<str>`` element
        :rtype:
           :obj:`str` (Python 2)

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
        if str_element.text is not None:
            encoding = str_element.get("encoding", self._default_encoding)
            return str_element.text.encode(encoding)
        else:
            return str()

    def __parse_str_as_text(self, str_element):
        """Return a Unicode text object parsed from *str_element*.

        :arg xml.etree.ElementTree.Element str_element:
           a ``<str>`` element
        :rtype:
           :obj:`str` (Python 3)

        .. note::
           This method is aliased as ``_parse_str`` when Aglyph is
           running under Python 3.

        The text of the ``<str>`` element (which is already a Unicode
        string) is returned unchanged.

        Whitespace in the ``<str>`` element content is preserved.

        If *str_element* represents the empty element ``<str />``,
        ``str()`` is returned.

        """
        if str_element.text is not None:
            encoding = str_element.get("encoding")
            if encoding is not None:
                self.__log.warning(
                    "ignoring str/@encoding attribute %r (Python 3)", encoding)
            return str_element.text
        else:
            return str()

    def _parse_unicode(self, unicode_element):
        """Return a Unicode text object parsed from *unicode_element*.

        :arg xml.etree.ElementTree.Element unicode_element:
           a ``<unicode>`` element
        :rtype:
           :obj:`str` (Python 3) or :obj:`unicode` (Python 2)

        The text of the ``<unicode>`` element (which is already a
        Unicode string) is returned unchanged.

        Whitespace in the ``<unicode>`` element content is preserved.

        If *unicode_element* represents the empty element
        ``<unicode />``, ``str()`` (Python 3) or ``unicode()``
        (Python 2) is returned.

        """
        if unicode_element.text is not None:
            return unicode_element.text
        else:
            return TextType()

    def _parse_int(self, int_element):
        """Return a builtin integer object parsed from *int_element*.

        :arg xml.etree.ElementTree.Element int_element:
           an ``<int>`` element
        :rtype:
           :obj:`int`

        The **int/@base** attribute, if specified, is used as the number
        base to interpret the content of *int_element*.

        If *int_element* represents the empty element ``<int />``,
        ``int()`` is returned.

        .. warning::
           This method **may** return :obj:`long` in Python 2!

        """
        if int_element.text is not None:
            base = int(int_element.get("base", "10"))
            #PYVER: IronPython 2.7 does not accept a 'base=' keyword argument
            return int(int_element.text, base)
        else:
            return int()

    def _parse_float(self, float_element):
        """Return a builtin floating-point object parsed from
        *float_element*.

        :arg xml.etree.ElementTree.Element float_element:
           a ``<float>`` element
        :rtype:
           :obj:`float`

        If *float_element* represents the empty element ``<float />``,
        ``float()`` is returned.

        """
        if float_element.text is not None:
            return float(float_element.text)
        else:
            return float()

    def _parse_list(self, list_element):
        """Return a :obj:`list` evaluator object parsed from
        *list_element*.

        :arg xml.etree.ElementTree.Element list_element:
           a ``<list>`` element
        :rtype:
           :class:`aglyph.component.Evaluator`

        .. note::
           The evaluator returned by this method produces a new
           :obj:`list` object each time it is called.

        """
        process_value_element = self._process_value_element
        items = [
            process_value_element(child_element, "list")
            for child_element in list_element]
        return evaluate(list, items)

    def _parse_tuple(self, tuple_element):
        """Return a :obj:`tuple` evaluator object parsed from
        *tuple_element*.

        :arg xml.etree.ElementTree.Element tuple_element:
           a ``<tuple>`` element
        :rtype:
           :class:`aglyph.component.Evaluator` (or :obj:`tuple` if
           the ``<tuple>`` element is empty)

        .. note::
           The evaluator returned by this method produces a new
           :obj:`tuple` object each time it is called.

        """
        children = list(tuple_element)
        if children:
            process_value_element = self._process_value_element
            items = [
                process_value_element(child_element, "tuple")
                for child_element in children]
            return evaluate(tuple, items)
        else:
            # a tuple is immutable, so there's no sense in paying the overhead
            # of evaluation for an empty tuple
            return tuple()

    def _parse_set(self, set_element):
        """Return a :obj:`set` evaluator object parsed from
        *set_element*.

        :arg xml.etree.ElementTree.Element set_element:
           a ``<set>`` element
        :rtype:
           :class:`aglyph.component.Evaluator`

        .. note::
           The evaluator returned by this method produces a new
           :obj:`set` object each time it is called.

        """
        process_value_element = self._process_value_element
        items = [
            process_value_element(child_element, "set")
            for child_element in set_element]
        return evaluate(set, items)

    def _parse_dict(self, dict_element):
        """Return a :obj:`dict` evaluator object parsed from
        *dict_element*.

        :arg xml.etree.ElementTree.Element dict_element:
           a ``<dict>`` element
        :rtype:
           :class:`aglyph.component.Evaluator`

        .. note::
           The evaluator returned by this method produces a new
           :obj:`dict` object each time it is called.

        """
        # a list of 2-tuples, (key, value), used to initialize a dictionary
        items = []
        for element in list(dict_element):
            if element.tag != "item":
                raise AglyphError("unexpected element: dict/%s" % element.tag)

            children = list(element)
            child_tags = [child.tag for child in children]
            if child_tags == ["key", "value"]:
                key_element, value_element = children
            else:
                raise AglyphError(
                    "expected item/key, item/value; found %s" %
                        ", ".join("item/%s" % ctag for ctag in child_tags))

            items.append((
                self._unserialize_element_value(key_element),
                self._unserialize_element_value(value_element)
            ))

        return evaluate(dict, items)

    def _parse_reference(self, reference_element):
        """Return a reference to another component in this context.

        :arg xml.etree.ElementTree.Element reference_element:
           a ``<reference>`` element
        :rtype:
           an Aglyph :class:`Reference`

        The **reference/@id** attribute is required, and will be used as
        the value to create an :class:`aglyph.component.Reference`.

        """
        component_id = reference_element.attrib["id"]
        return ref(component_id)

    def __repr__(self):
        return self.__repr

