# -*- coding: UTF-8 -*-

# Copyright (c) 2006-2014 Matthew Zipay <mattz@ninthtest.net>
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
__version__ = "2.0.0"

import logging
import types
import uuid

from aglyph import format_dotted_name
from aglyph.assembler import Assembler
from aglyph.compat import ClassAndFunctionTypes, StringTypes
from aglyph.component import Component, Reference, Strategy
from aglyph.context import Context

__all__ = ["Binder"]

_logger = logging.getLogger(__name__)


class Binder(Assembler):
    """Configure and assemble application components."""

    __logger = logging.getLogger("%s.Binder" % __name__)

    def __init__(self, binder_id=None):
        """
        :keyword str binder_id: a unique identifier for this binder

        If *binder_id* is not provided, a random identifier is
        generated.

        """
        self.__logger.debug("TRACE binder_id=%r", binder_id)
        if (binder_id is None):
            binder_id = uuid.uuid4()
        super(Binder, self).__init__(Context(binder_id))
        self._binder_id = binder_id
        self.__logger.info("initialized %s", self)
        self.__logger.debug("RETURN")

    @property
    def binder_id(self):
        """The unique binder identifier *(read-only)*."""
        return self._binder_id

    def bind(self, component_spec, to=None, factory=None, member=None,
             strategy=Strategy.PROTOTYPE):
        """Define a component by associating the unique identifier for
        *component_spec* with the importable dotted-name for *to*.

        :param component_spec: used to determine the value that will\
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
        :return: a proxy object that allows the component dependencies\
                 to be defined in chained-call fashion
        :rtype: :class:`aglyph.binding._Binding`

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

        """
        self.__logger.debug("TRACE %r, to=%r, strategy=%r", component_spec, to,
                           strategy)
        component_id = self._identify(component_spec)
        if (to is None):
            dotted_name = component_id
        else:
            dotted_name = self._identify(to)
        component = Component(component_id, dotted_name=dotted_name,
                              factory_name=factory, member_name=member,
                              strategy=strategy)
        self._context.add(component)
        self.__logger.info("bound %r to %r (%r)", component_spec, to,
                           dotted_name)
        binding = _Binding(component)
        self.__logger.debug("RETURN %r", binding)
        return binding

    def _identify(self, component_spec):
        """Generate a unique identifier for *component_spec*.

        :param component_spec: an **importable** class, function, or\
                               module; or a :obj:`str`
        :return: *component_spec* unchanged (if it is a :obj:`str`),\
                 else *component_spec*'s importable dotted name
        :rtype: :obj:`str`

        If *component_spec* is a string, it is assumed to already
        represent a unique identifier and is returned unchanged.
        Otherwise, *component_spec* is assumed to be an **importable**
        class, function, or module, and its dotted name is returned (see
        :func:`aglyph.format_dotted_name`).

        """
        return (component_spec if (type(component_spec) in StringTypes)
                else format_dotted_name(component_spec))

    def lookup(self, component_spec):
        """Return an instance of the component specified by
        *component_spec* with all of its dependencies provided.

        *component_spec* must be an importable class or unbound
        function, or a user-defined unique identifier, that was
        previously bound by a call to :func:`bind`.

        """
        self.__logger.debug("TRACE %r", component_spec)
        component_id = self._identify(component_spec)
        obj = self.assemble(component_id)
        self.__logger.debug("RETURN %r", type(obj))
        return obj


class _Binding(object):
    """Instances of ``_Binding`` are returned as proxy objects from the
    :meth:`Binder.bind` method.

    A ``_Binding`` allows component dependencies to be defined in
    chained-call fashion::

        Binder().bind(...).init(*args, **keywords).attributes(**keywords)

    .. note::
       This class should not be imported or otherwise directly
       referenced.

    """

    __slots__ = ["_component"]

    __logger = logging.getLogger("%s._Binding" % __name__)

    def __init__(self, component):
        """
        :param aglyph.component.Component component:\
           the object that was created by a call to :meth:`Binder.bind`

        """
        self.__logger.debug("TRACE %r", component)
        self._component = component

    def init(self, *args, **keywords):
        """Define the initialization dependencies (i.e. positional
        and/or keyword arguments) for the component.

        :param tuple args: the positional argument dependencies
        :param dict keywords: the keyword argument dependencies
        :return: a reference to ``self`` (enables chained calls)

        If any argument value is a class, unbound function, or module
        type, it is automatically turned into an
        :class:`aglyph.component.Reference`. This allows for a kind of
        "shorthand" in the binding of components and dependencies, but
        requires that such a component/dependency be identified by its
        dotted name. For example::

           binder.bind("thing", to="module.Thing").init(SomeClass)
           binder.bind(SomeClass).init(...).attributes(...)

        In the above case, ``SomeClass`` will be automatically turned
        into a ``Reference``. Assuming ``SomeClass`` is defined in a
        module named "my.package", this means that the "thing" component
        will have an initialization dependency on a component with the
        identifier and dotted name "my.package.SomeClass".

        If more flexibility is needed, simply create and pass in an
        :class:`aglyph.component.Reference` by hand.

        .. versionchanged:: 2.0.0
           Successive calls to this method on the same instance have a
           cumulative effect.

        """
        self.__logger.debug("TRACE *%r, **%r", args, keywords)
        reference = self._reference
        self._component.init_args.extend([reference(arg) for arg in args])
        self._component.init_keywords.update(
            dict([(keyword, reference(arg))
                  for (keyword, arg) in keywords.items()]))
        self.__logger.debug("RETURN %r", self)
        return self

    def attributes(self, **keywords):
        """Define the setter dependencies (i.e. attributes, setter
        methods, and/or properties) for the component.

        :param dict keywords: the attribute, setter method, and/or\
                              property dependencies
        :return: a reference to ``self`` (enables chained calls)

        Each key in *keywords* corresponds to the name of a simple
        attribute, setter method, or property.

        If any value in *keywords* is a class, unbound function, or
        module type, it is automatically turned into an
        :class:`aglyph.component.Reference`. This allows for a kind of
        "shorthand" in the binding of components and dependencies, but
        requires that such a component/dependency be identified by its
        dotted name. For example::

           (binder.bind("thing", to="module.Thing").
               attributes(set_something=SomeClass))
           binder.bind(SomeClass).init(...).attributes(...)

        In the above case, ``SomeClass`` will be automatically turned
        into a ``Reference``. Assuming ``SomeClass`` is defined in a
        module named "my.package", this means that the "thing" component
        will have a setter dependency (``set_something``) on a component
        with the identifier and dotted name "my.package.SomeClass".

        If more flexibility is needed, simply create and pass in an
        :class:`aglyph.component.Reference` by hand.

        .. versionchanged:: 2.0.0
           Successive calls to this method on the same instance have a
           cumulative effect.

        """
        if (self.__logger.isEnabledFor(logging.DEBUG)):
            # do not log possibly sensitive data
            self.__logger.debug("TRACE **%r",
                dict([(k, type(v)) for (k, v) in keywords.items()]))
        reference = self._reference
        self._component.attributes.update(
            dict([(name, reference(value))
                  for (name, value) in keywords.items()]))
        self.__logger.debug("RETURN self")
        return self

    def _reference(self, obj):
        """Convert *obj* into a component reference, if applicable.

        :param obj: an object representing a component dependency

        If *obj* is a class, unbound function, or module, then an
        :class:`aglyph.component.Reference` to *obj* is returned.
        Otherwise, *obj* itself is returned.

        """
        obj_type = type(obj)
        if ((obj_type in ClassAndFunctionTypes) or
                (obj_type is types.ModuleType)):
            return Reference(format_dotted_name(obj))
        else:
            return obj

    def __repr__(self):
        return "%s.%s(%r)" % (self.__class__.__module__,
                              self.__class__.__name__, self._component)

