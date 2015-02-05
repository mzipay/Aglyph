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

"""The Aglyph binder provides a concise programmatic-configuration
option for Aglyph.

.. versionadded:: 1.1.0

The Aglyph binder provides a much simpler and more compact alternative
to :class:`aglyph.assembler.Assembler`, :class:`aglyph.context.Context`,
and :class:`aglyph.component.Component` for programmatic configuration
of Aglyph.

"Binding" usually results in less configuration code. A :class:`Binder`
also offers the same functionality as an
:class:`aglyph.assembler.Assembler`, so the same object used to
*configure* injection can be used to *perform* injection, further
reducing the amount of "bootstrap" code needed.

For example, the following two blocks exhibit identical behavior:

Using ``Context``, ``Component``, and ``Assembler`` directly::

   context = Context("context-id")
   component = Component("my-class", dotted_name="my.package.MyClass")
   component.init_args.append("value")
   component.init_keywords["foo"] = "bar"
   component.attributes["set_spam"] = "eggs"
   context.add(component)
   assembler = Assembler(context)
   ...
   my_object = assembler.assemble("my-class")

Using ``Binder``::

   binder = Binder()
   (binder.bind("my-class", to="my.package.MyClass").
       init("value", foo="bar").
       attributes(set_spam="eggs"))
   ...
   my_object = binder.lookup("my-class")

"""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "2.1.0"

from inspect import isclass, ismodule
import logging
import types
import uuid
import warnings

from aglyph import (
    AglyphDeprecationWarning,
    format_dotted_name,
    _is_unbound_function,
    _safe_repr,
)
from aglyph.assembler import Assembler
from aglyph.component import Component, Reference, Strategy, Template
from aglyph.context import Context

__all__ = ["Binder"]

_logger = logging.getLogger(__name__)


class Binder(Assembler):
    """Configure and assemble application components."""

    __logger = logging.getLogger("%s.Binder" % __name__)

    def __init__(self, binder_id=None, after_inject=None, before_clear=None):
        """
        :keyword str binder_id: a unique identifier for this binder
        :keyword str after_inject: specifies the name of the method\
                                   that will be called on assembled\
                                   objects after all of their\
                                   dependencies have been injected
        :keyword str before_clear: specifies the name of the method\
                                   that will be called on assembled\
                                   objects immediately before they are\
                                   cleared from cache

        If *binder_id* is not provided, a random identifier is
        generated.

        .. versionadded:: 2.1.0
           the *after_inject* and *before_clear* keyword arguments

        """
        self.__logger.debug("TRACE binder_id=%r", binder_id)
        if (binder_id is None):
            binder_id = uuid.uuid4()
        context = Context(binder_id, after_inject=after_inject,
                          before_clear=before_clear)
        super(Binder, self).__init__(context)
        self._binder_id = binder_id
        self.__logger.info("initialized %s", self)

    @property
    def binder_id(self):
        """The unique binder identifier *(read-only)*."""
        return self._binder_id

    def bind(self, component_spec, to=None, factory=None, member=None,
             strategy=Strategy.PROTOTYPE, parent=None, after_inject=None,
             before_clear=None):
        """Define a component by associating the unique identifier for
        *component_spec* with the importable dotted-name for *to*.

        :arg component_spec: used to determine the value that will\
                               serve as the :meth:`lookup` key for\
                               objects of the component
        :keyword to: used to identify the class or function that will\
                     be called to initialize objects of the component
        :keyword str factory: names a **callable** member of the object\
                              identified by the *component_spec*\
                              argument or *to* keyword
        :keyword str member: names **any** member of the object\
                             identified by the *component_spec*\
                             argument or *to* keyword
        :keyword str strategy: specifies the component assembly strategy
        :keyword str parent: specifies the ID of a template or\
                             component that describes the default\
                             dependencies and/or lifecyle methods for\
                             this component
        :keyword str after_inject: specifies the name of the method\
                                   that will be called on objects of\
                                   this component after all of its\
                                   dependencies have been injected
        :keyword str before_clear: specifies the name of the method\
                                   that will be called on objects of\
                                   this component immediately before\
                                   they are cleared from cache
        :return: a proxy object that allows the component dependencies\
                 to be defined in chained-call fashion
        :rtype: :class:`aglyph.binder._DependencySupportProxy`

        If *component_spec* is a :obj:`str`, it is used as the unique
        identifier for the component. In this case, the *to* keyword is
        **required**.

        Otherwise, *component_spec* must be an importable class, unbound
        function, or module. Its dotted name will be used as the
        component identifier.

        If *to* is not provided, the component identifier will be used
        as *both* the component's identifier *and* dotted name. In such
        cases, *component_spec* must be **either** an importable class,
        unbound function, or module, **or** a dotted name.

        .. versionadded:: 2.0.0
           the *factory* keyword argument

        *factory* is the name of a **callable** member of the importable
        object (i.e. *factory* is a function, class, staticmethod, or
        classmethod). When provided, this member is called to assemble
        the component.

        *factory* enables Aglyph to inject dependencies into objects
        that can only be initialized via nested classes,
        ``staticmethod``, or ``classmethod``. For example::

           # in module 'module.py'
           class Outer:
               class Nested:
                   pass

           # elsewhere...
           binder.bind("nested-instance", to="module.Outer",
                       factory="Nested")

        When assembled, the "nested-instance" component will be an
        instance of the ``module.Outer.Nested`` class.

        .. versionadded:: 2.0.0
           the *member* keyword argument

        *member* is the name of **any** member of the importable object
        (including a callable member, such as a nested class).

        *member* differs from *factory* in two ways:

        1. *member* is not restricted to callable members; it may name
           an attribute or property, as well as a callable.
        2. When the binder looks up a component with a defined *member*,
           initialization is *bypassed* (i.e. no initialization
           dependencies are injected).

        *member* enables Aglyph to reference classes, functions,
        staticmethods, classmethods, and attributes as dependencies.
        For example::

           # in module 'module.py'
           class Outer:
               class Nested:
                   pass

           # elsewhere...
           binder.bind("nested-class", to="module.Outer",
                       member="Nested")

        When assembled, the "nested-class" component will be the
        module.Outer.Nested ``class`` object itself.

        .. note::
           Both *factory* and *member* can be dot-separated names to
           reference nested members.

        .. warning::
           The *factory* and *member* arguments are mutually exclusive.
           An exception is raised if both are provided.

        *strategy* must be a recognized component assembly strategy, and
        defaults to :attr:`aglyph.component.Strategy.PROTOTYPE`
        (*"prototype"*) if not specified.

        Please see :class:`aglyph.component.Strategy` for a description
        of the component assembly strategies supported by Aglyph.

        .. warning::
           The :attr:`aglyph.component.Strategy.BORG` (*"borg"*)
           component assembly strategy is only supported for classes
           that do not define or inherit ``__slots__``!

        .. versionadded:: 2.1.0
           the *parent* keyword argument

        If *parent* is a :obj:`str`, it is used as the unique identifier
        for the component's parent template or component.

        If *parent* is not a string, then it must be an importable
        class, unbound function, or module. Its dotted name will be used
        as the :attr:`Component.parent_id`.

        .. versionadded:: 2.1.0
           the *after_inject* keyword argument

        *after_inject* is the name of a method *of objects of this
        component* that will be called after **all** dependencies have
        been injected, but before the object is returned to the caller.
        This method will be called with **no** arguments (positional or
        keyword). Exceptions raised by this method are not caught.

        .. note::
           ``Component.after_inject``, if specified, **replaces** either
           :attr:`Template.after_inject` (if this component also
           specifies :attr:`parent_id`) or
           :attr:`aglyph.context.Context.after_inject`.

        .. versionadded:: 2.1.0
           the *before_clear* keyword argument

        *before_clear* is the name of a method *of objects of this
        component* that will be called immediately before the object is
        cleared from cache via
        :meth:`aglyph.assembler.Assembler.clear_singletons()`,
        :meth:`aglyph.assembler.Assembler.clear_borgs()`, or
        :meth:`aglyph.assembler.Assembler.clear_weakrefs()`.

        .. note::
           ``Component.before_clear``, if specified, **replaces** either
           :attr:`Template.before_clear` (if this component also
           specifies :attr:`parent_id`) or
           :attr:`aglyph.context.Context.before_clear`.

        .. warning::
           The *before_clear* keyword argument has no meaning for and is
           ignored by "prototype" components. If *before_clear* is
           specified for a prototype, a :class:`RuntimeWarning` will be
           issued.

           For "weakref" components, there is a possibility that the
           object no longer exists at the moment when the *before_clear*
           method would be called. In such cases, the *before_clear*
           method is **not** called. No warning is issued, but a
           :attr:`logging.WARNING` message is emitted.

        """
        self.__logger.debug(
            "TRACE %r, to=%r, factory=%r, member=%r, strategy=%r, parent=%r, "
            "after_inject=%r, before_clear=%r",
            component_spec, to, factory, member, strategy, parent,
            after_inject, before_clear)
        component_id = self._identify(component_spec)
        if (to is None):
            dotted_name = component_id
        else:
            dotted_name = self._identify(to)
        parent_id = self._identify(parent) if (parent is not None) else None
        component = Component(component_id, dotted_name=dotted_name,
                              factory_name=factory, member_name=member,
                              strategy=strategy, parent_id=parent_id,
                              after_inject=after_inject,
                              before_clear=before_clear)
        self._context[component.unique_id] = component
        self.__logger.info("bound %r to %r (%r)", component_spec, to,
                           dotted_name)
        proxy = _DependencySupportProxy(component)
        self.__logger.debug("RETURN %r", proxy)
        return proxy

    def describe(self, template_spec, parent=None, after_inject=None,
                 before_clear=None):
        """Define a template using the unique identifier derived from
        *template_spec*.

        :arg template_spec: used to determine the value that will serve\
                            as the unique identifier for the template
        :keyword str parent: specifies the ID of a template or\
                             component that describes the default\
                             dependencies and/or lifecyle methods for\
                             this template
        :keyword str after_inject: specifies the name of the method\
                                   that will be called on objects of\
                                   components that refer to this\
                                   template's ID as the\
                                   :attr:`Component.parent_id`\
                                   immediately after all component\
                                   dependencies have been injected
        :keyword str before_clear: specifies the name of the method\
                                   that will be called on objects of\
                                   components that refer to this\
                                   template's ID as the\
                                   :attr:`Component.parent_id`\
                                   when the objects are removed from\
                                   any internal cache
        :return: a proxy object that allows the template dependencies\
                 to be defined in chained-call fashion
        :rtype: :class:`aglyph.binder._DependencySupportProxy`

        If *template_spec* is a :obj:`str`, it is used as the unique
        identifier for the template. Otherwise, *template_spec* must be
        an importable class, unbound function, or module. Its dotted
        name will be used as the template identifier.

        If *parent* is a :obj:`str`, it is used as the unique identifier
        for the component's parent template or component.

        If *parent* is not a string, then it must be an importable
        class, unbound function, or module. Its dotted name will be used
        as the :attr:`Component.parent_id`.

        *after_inject* is the name of a method (of objects of components
        that reference this template) that will be called after **all**
        dependencies have been injected, but before the object is
        returned to the caller.

        The method named by *after_inject* will be called with **no**
        arguments (positional or keyword). Exceptions raised by this
        method are ignored (though a :class:`RuntimeWarning` will be
        issued).

        .. note::
           ``Template.after_inject``, if specified, **replaces** any
           after-inject method named by its parent or by
           :attr:`aglyph.context.Context.after_inject`.

        *before_clear* is the name of a method (of objects of components
        that reference this template) that will be called when the
        object is cleared from cache via
        :meth:`Assembler.clear_singletons()`,
        :meth:`Assembler.clear_borgs()`, or
        :meth:`Assembler.clear_weakrefs()`.

        .. note::
           ``Template.before_clear``, if specified, **replaces** any
           before-clear method named by its parent or by
           :attr:`aglyph.context.Context.before_clear`.

        .. warning::
           The *before_clear* keyword argument has no meaning for and is
           ignored by "prototype" components. If *before_clear* is
           specified for a prototype, a :class:`RuntimeWarning` will be
           issued.

           For "weakref" components, there is a possibility that the
           object no longer exists at the moment when the *before_clear*
           method would be called. In such cases, the *before_clear*
           method is **not** called. No warning is issued, but a
           :attr:`logging.WARNING` message is emitted.

        """
        self.__logger.debug(
            "TRACE %r, parent=%r, after_inject=%r, before_clear=%r",
            template_spec, parent, after_inject, before_clear)
        template_id = self._identify(template_spec)
        parent_id = self._identify(parent) if (parent is not None) else None
        template = Template(template_id, parent_id=parent_id,
                            after_inject=after_inject,
                            before_clear=before_clear)
        self._context[template.unique_id] = template
        self.__logger.info("described template %r with ID %r)",
                           template_spec, template_id)
        proxy = _DependencySupportProxy(template)
        self.__logger.debug("RETURN %r", proxy)
        return proxy

    def lookup(self, component_spec):
        """Return an instance of the component specified by
        *component_spec* with all of its dependencies provided.

        *component_spec* must be an importable class or unbound
        function, or a user-defined unique identifier, that was
        previously bound by a call to :func:`bind`.

        .. deprecated:: 2.1.0
           use :meth:`assemble` instead.

        """
        self.__logger.debug("TRACE %r", component_spec)
        warnings.warn(AglyphDeprecationWarning("Binder.lookup",
                                               replacement="Binder.assemble"))
        obj = self.assemble(component_spec)
        # do not log str/repr of assembled objects; may contain sensitive data
        self.__logger.debug("RETURN %s", _safe_repr(obj))
        return obj


class _DependencySupportProxy(object):
    """Instances of ``__DependencySupportProxy`` are returned as proxy
    objects from the :meth:`Binder.bind` and :meth:`Binder.describe`
    methods.

    A ``_DependencySupportProxy`` allows component dependencies to be
    defined in chained-call fashion::

       binder = Binder()
       binder.bind(...).init(*args, **keywords).attributes(**keywords)
       # - or -
       (binder.describe(...).
           init(*args, **keywords).
           attributes(**keywords))

    .. note::
       This class should not be imported or otherwise directly
       referenced.

    """

    __slots__ = ["_depsupport"]

    __logger = logging.getLogger("%s._DependencySupportProxy" % __name__)

    def __init__(self, depsupport):
        """
        :arg depsupport: a :class:`Component` or :class:`Template` that\
                         was created by :meth:`Binder.bind` or\
                         :meth:`Binder.describe`, respectively

        """
        self.__logger.debug("TRACE %r", depsupport)
        self._depsupport = depsupport

    def init(self, *args, **keywords):
        """Define the initialization dependencies (i.e. positional
        and/or keyword arguments) for the component or template.

        :arg tuple args: the positional argument dependencies
        :arg dict keywords: the keyword argument dependencies
        :return: a reference to ``self`` (enables chained calls)

        If any argument value is a class, unbound function, or module
        type, it is automatically turned into a :class:`Reference`::

           # SomeClass becomes
           # ``Reference(format_dotted_name(SomeClass))``
           binder.bind("thing", to="module.Thing").init(SomeClass)

        .. warning::
           In the above example, there **must** exist a component that
           has the ID "package.module.SomeClass"::

              binder.bind(SomeClass).init(...).attributes(...)
              # - or -
              (binder.bind("package.module.SomeClass").
                  init(...).attributes(...))

           If more flexibility is needed, simply create and pass in an
           explicit :class:`Reference`::

              (binder.bind("something", to=SomeClass).
                  init(...).attributes(...))
              ...
              (binder.bind("thing", to="module.Thing").
                  init(Reference("something")))

        .. versionchanged:: 2.0.0
           Successive calls to this method on the same instance have a
           cumulative effect.

        """
        self.__logger.debug("TRACE *%r, **%r", args, keywords)
        reference = self._reference
        self._depsupport.args.extend([reference(arg) for arg in args])
        self._depsupport.keywords.update(
            dict([(keyword, reference(arg))
                  for (keyword, arg) in keywords.items()]))
        return self

    def attributes(self, *nvpairs, **keywords):
        """Define the setter dependencies (i.e. attributes, setter
        methods, and/or properties) for the component.

        :arg tuple nvpairs: an **ordered** N-tuple of ``(name, value)``\
                            2-tuples that describe the attribute,\
                            setter method, and/or property dependencies
        :arg dict keywords: the attribute, setter method, and/or\
                            property dependencies
        :return: a reference to ``self`` (enables chained calls)

        .. versionadded:: 2.1.0::
           the *nvpairs* parameter.

        If the order in which attribute/setter/property dependencies are
        injected is significant, use *nvpairs* to control the order;
        otherwise, if order of injection doesn't matter, it is simpler
        to use *keywords*.

        In each ``(name, value)`` 2-tuple of *nvpairs*, ``name``
        corresponds to the name of a simple attribute, setter method, or
        property::

           (binder.bind("thing", to="module.Thing").
               attributes(("id", 1), ("set_name", "First thing")))

        Each key in *keywords* corresponds to the name of a simple
        attribute, setter method, or property::

           (binder.bind("thing", to="module.Thing").
               attributes(id=1, set_name="First thing"))

        If any value in *nvpairs* or *keywords* is a class, unbound
        function, or module type, it is automatically turned into a
        :class:`Reference`::

           # SomeClass becomes
           # ``Reference(format_dotted_name(SomeClass))``
           (binder.bind("thing", to="module.Thing").
               attributes(id=1, set_class=SomeClass))

        .. warning::
           In the above example, there **must** exist a component that
           has the ID "package.module.SomeClass"::

              binder.bind(SomeClass).init(...).attributes(...)
              # - or -
              (binder.bind("package.module.SomeClass").
                  init(...).attributes(...))

           If more flexibility is needed, simply create and pass in an
           explicit :class:`Reference`::

              (binder.bind("something", to=SomeClass).
                  init(...).attributes(...))
              ...
              (binder.bind("thing", to="module.Thing").
                  attributes(id=1, set_class=Reference("something")))

        .. versionchanged:: 2.0.0
           Successive calls to this method on the same instance have a
           cumulative effect.

        """
        self.__logger.debug("TRACE *%r, **%r", nvpairs, keywords)
        reference = self._reference
        for (name, value) in nvpairs:
            self._depsupport.attributes[name] = reference(value)
        self._depsupport.attributes.update(
            dict([(name, reference(value))
                  for (name, value) in keywords.items()]))
        return self

    def _reference(self, obj):
        """Convert *obj* into a component reference, if applicable.

        :arg obj: an object representing a component dependency

        If *obj* is a class, unbound function, or module, then an
        :class:`aglyph.component.Reference` to *obj* is returned.
        Otherwise, *obj* itself is returned.

        """
        if (isclass(obj) or _is_unbound_function(obj) or ismodule(obj)):
            return Reference(format_dotted_name(obj))
        else:
            return obj

    def __repr__(self):
        return "%s.%s(%r)" % (self.__class__.__module__,
                              self.__class__.__name__, self._depsupport)

