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

"""The classes in this module are used to define components and their
dependencies.

"""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "2.1.0"

from collections import namedtuple
from functools import partial
import logging
import warnings

from aglyph import AglyphDeprecationWarning, AglyphError, _safe_repr
from aglyph.compat import is_callable, OrderedDict, StringTypes, TextType

__all__ = [
    "Component",
    "Evaluator",
    "LifecycleState",
    "Reference",
    "Strategy",
    "Template",
]

_logger = logging.getLogger(__name__)

Strategy = namedtuple("Strategy",
                      ("PROTOTYPE", "SINGLETON", "BORG", "WEAKREF"))(
                       "prototype", "singleton", "borg", "weakref")
"""Define the component assembly strategies implemented by Aglyph.

.. versionchanged:: 2.0.0
   ``Strategy`` is now a named tuple. In prior versions, it was a class.

.. rubric:: "prototype"

A new object is always created, initialized, wired, and returned.

.. note::
   "prototype" is the default assembly strategy for Aglyph components.

.. rubric:: "singleton"

The cached object is returned if it exists. Otherwise, the object is
created, initialized, wired, cached, and returned.

Singleton component objects are cached by :attr:`Component.unique_id`.

.. rubric:: "borg"

A new instance is always created. The shared-state is assigned to the
new instance's ``__dict__`` if it exists. Otherwise, the new instance is
initialized and wired, its instance ``__dict__`` is cached, and then the
instance is returned.

Borg component instance shared-states are cached by
:attr:`Component.component_id`.

.. warning::
   * The borg assembly strategy is **only** supported for
     components that are non-builtin classes.
   * The borg assembly strategy is **not** supported for
     classes that define or inherit a ``__slots__`` member.

.. rubric:: "weakref"

.. versionadded:: 2.1.0

In the simplest terms, this is a "prototype" that can exhibit
"singleton" behavior: as long as there is at least one "live" reference
to the assembled object in the application runtime, then requests to
assemble this component will return the same (cached) object.

When the only reference to the assembled object that remains is the
cached weak reference, the Python garbage collector is free to destroy
the object, at which point it is automatically removed from the Aglyph
cache.

Subsequent requests to assemble the same component will cause a new
object to be created, initialized, wired, cached (as a weak reference),
and returned.

.. note::
   Please refer to the :mod:`weakref` module for a detailed explanation
   of weak reference behavior.

"""

LifecycleState = namedtuple("LifecycleState",
                            ("AFTER_INJECT", "BEFORE_CLEAR"))(
                             "after_inject", "before_clear")
"""Define the lifecycle states for which Aglyph will call object methods
on your behalf.

.. _lifecycle-methods:

.. rubric:: Lifecycle methods

Lifecycle methods are called with **no arguments** (positional or
keyword).

If a called lifecycle method raises an exception, the exception is
caught, logged at :attr:`logging.ERROR` level (including a traceback) to
the "aglyph.assembler.Assembler" channel, and a :class:`RuntimeWarning`
is issued.

A method may be registered for a lifecycle state by specifying the
method name at the context (least specific), template, and/or component
(most specific) level.

.. note::
   Aglyph only calls **one** method on an object for any lifecycle
   state. Refer to **The lifecycle method lookup process** (below) for
   details.

Aglyph recognizes the following lifecycle states:

.. rubric:: "after_inject"

A component object is in this state after **all** dependencies (both
initialization arguments and attributes) have been injected into a
newly-created instance, but before the object is cached and/or returned
to the caller.

Aglyph will only call **one** "after_inject" method on any object, and
will determine which method to call by using the lookup process
described below.

.. rubric:: "before_clear"

A component object is in this state after is has been removed from an
internal cache (singleton, borg, or weakref), but before the object
itself is actually discarded.

Aglyph will only call **one** "before_clear" method on any object, and
will determine which method to call by using the lookup process
described below.

.. _lifecycle-method-lookup-process:

.. rubric:: The lifecycle method lookup process

Lifecyle methods may be specified at the context (least specific),
template, and component (most specific) levels.

In order to determine which named method is called for a particular
object, Aglyph looks up the appropriate lifecycle method name in the
following order, using the **first** one found that is not ``None``
*and* is actually defined on the object:

#. The method named by the object's ``Component.<lifecycle-state>``
   property.
#. If the object's :attr:`Component.parent_id` is not ``None``, the
   method named by the corresponding parent
   ``Template.<lifecycle-state>`` or ``Component.<lifecycle-state>``
   property.
   (If necessary, lookup continues by examining the
   parent-of-the-parent and so on.)
#. The method named by the ``Context.<lifecycle-state>`` property.

When Aglyph finds a named lifecycle method that applies to an object,
but the object itself does not define that method, a
:attr:`logging.WARNING` message is emitted.

.. note::
  Either a :class:`Component` or :attr:`Template` may serve as the
  parent identified by a ``parent_id``.

  However, only a :class:`Component` may actually be assembled into
  a usable object. (A :attr:`Template` is like an abstract class -
  it defines common dependencies and/or lifecycle methods, but it
  cannot be assembled.)

"""


class Reference(TextType):
    """A place-holder used to refer to another :class:`Component`.

    A ``Reference`` is used as an alias to identify a component that is a
    dependency of another component. The value of a ``Reference`` can be
    either a dotted-name or a user-provided unique ID.

    A ``Reference`` value MUST correspond to a component ID in the same
    context.

    A ``Reference`` can be used as an argument for an
    :class:`Evaluator`, and can be assembled directly by an
    :class:`aglyph.assembler.Assembler`.

    .. note::
        In Python versions < 3.0, a ``Reference`` representing a
        dotted-name *must* consist only of characters in the ASCII
        subset of the source encoding (see :pep:`0263`).

        But in Python versions >= 3.0, a ``Reference`` representing a
        dotted-name *may* contain non-ASCII characters
        (see :pep:`3131`).

        However, a ``Reference`` may also represent a user-defined
        identifier. To accommodate all cases, the super class of
        ``Reference`` is "dynamic" with respect to the version of Python
        under which Aglyph is running (:class:`unicode` under Python 2,
        :class:`str` under Python 3). This documentation shows the base
        class as ``str`` because the `Sphinx <http://sphinx-doc.org/>`_
        documentation generator runs under CPython 3.

    """

    def __new__(cls, value):
        return TextType.__new__(cls, value)


_logger.debug("Reference extends %r", TextType)


class _InitializationSupport(object):

    __slots__ = ["_args", "_keywords"]

    def __init__(self):
        super(_InitializationSupport, self).__init__()
        self._args = []
        self._keywords = {}

    @property
    def args(self):
        return self._args

    @property
    def keywords(self):
        return self._keywords


class Evaluator(_InitializationSupport):
    """Perform lazy creation of objects."""

    __slots__ = ["_func"]

    __logger = logging.getLogger("%s.Evaluator" % __name__)

    def __init__(self, func, *args, **keywords):
        """
        :param callable func: any callable that returns an object
        :param tuple args: the positional arguments to *func*
        :param dict keywords: the keyword arguments to *func*

        An ``Evaluator`` is similar to a :func:`functools.partial` in
        that they both collect a function and related arguments into a
        :obj:`callable` object with a simplified signature that can be
        called repeatedly to produce a new object.

        *Unlike* a partial function, an ``Evaluator`` may have arguments
        that are not truly "frozen," in the sense that any argument may
        be defined as a :class:`Reference`, a :func:`functools.partial`,
        or even another ``Evaluator``, which needs to be resolved (i.e.
        assembled/called) before calling *func*.

        When an ``Evaluator`` is called, its arguments (positional and
        keyword) are each resolve in one of the following ways:

        * If the argument value is a :class:`Reference`, it is assembled
          (by an :class:`aglyph.assembler.Assembler` or
          :class:`aglyph.binder.Binder` reference passed to
          :meth:`__call__`)
        * If the argument value is an ``Evaluator`` or a
          :func:`functools.partial`, it is called to produce its value.
        * If the argument is a dictionary or a sequence other than a
          string type, each item is resolved according to these rules.
        * If none of the above cases apply, the argument value is used
          as-is.

        .. note::
           An ``Evaluator`` can handle any level of nesting (e.g. a
           :func:`functools.partial` within an ``Evaluator`` within
           *another* ``Evaluator``).

        """
        self.__logger.debug("TRACE %r, *%r, **%r", func, args, keywords)
        super(Evaluator, self).__init__()
        if (not is_callable(func)):
            raise TypeError("%s is not callable" % type(func).__name__)
        self._func = func
        self._args = args
        self._keywords = keywords

    @property
    def func(self):
        """The :obj:`callable` that creates new objects *(read-only)*."""
        return self._func

    def __call__(self, assembler):
        """Call ``func(*args, **keywords)`` and return the new object.

        :param assembler: a reference to an\
                          :class:`aglyph.assembly.Assembler` or\
                          :class:`aglyph.binder.Binder`

        *assembler* is used to assemble any :class:`Reference` that is
        encountered in the function arguments.

        """
        self.__logger.debug("TRACE %r", assembler)
        args = self._args
        keywords = self._keywords
        resolve = self._resolve
        resolved_args = tuple([resolve(arg, assembler) for arg in args])
        # keywords MUST be strings!
        resolved_keywords = dict([(keyword, resolve(arg, assembler))
                                  for (keyword, arg) in keywords.items()])
        obj = self._func(*resolved_args, **resolved_keywords)
        # do not log str/repr of assembled objects; may contain sensitive data
        self.__logger.debug("RETURN %s", _safe_repr(obj))
        return obj

    def _resolve(self, arg, assembler):
        """Return the resolved *arg*.

        :param arg: represents an argument (positional or keyword) to\
                    :attr:`func`.
        :param assembler: a reference to an\
                          :class:`aglyph.assembly.Assembler` or\
                          :class:`aglyph.binder.Binder`
        :return: the resolved argument value that will actually be\
                 passed to :attr:`func`

        """
        if (isinstance(arg, Reference)):
            return assembler.assemble(arg)
        elif (isinstance(arg, Evaluator)):
            return arg(assembler)
        elif (isinstance(arg, partial)):
            return arg()
        elif (isinstance(arg, dict)):
            # either keys or values may themselves be References, partials, or
            # Evaluators
            resolve = self._resolve
            return dict([(resolve(key, assembler), resolve(value, assembler))
                         for (key, value) in arg.items()])
        elif (hasattr(arg, "__iter__") and (not isinstance(arg, StringTypes))):
            resolve = self._resolve
            # assumption: the iterable class supports initialization with
            # __init__(iterable)
            return arg.__class__([resolve(value, assembler) for value in arg])
        else:
            return arg

    def __repr__(self):
        return "%s.%s(%r, *%r **%r)" % (self.__class__.__module__,
                                        self.__class__.__name__,
                                        self._func, self._args, self._keywords)


class _DependencySupport(_InitializationSupport):

    __slots__ = ["_attributes"]

    def __init__(self):
        super(_DependencySupport, self).__init__()
        self._attributes = OrderedDict()

    @property
    def attributes(self):
        return self._attributes


class Template(_DependencySupport):

    __slots__ = [
        "_after_inject",
        "_before_clear",
        "_parent_id",
        "_unique_id",
    ]

    __logger = logging.getLogger("%s.Template" % __name__)

    def __init__(self, template_id, parent_id=None, after_inject=None,
                 before_clear=None):
        """
        :arg str template_id: context-unique identifier for this\
                              template
        :keyword str parent_id: specifies the ID of a template or\
                                component that describes the default\
                                dependencies and/or lifecyle methods\
                                for this template
        :keyword str after_inject: specifies the name of the method\
                                   that will be called on objects of\
                                   components that reference this\
                                   template after all component\
                                   dependencies have been injected
        :keyword str before_clear: specifies the name of the method\
                                   that will be called on objects of\
                                   components that reference this\
                                   template immediately before they are\
                                   cleared from cache

        .. note::
           A ``Template`` cannot be assembled (it is equivalent to an
           abstract class).

           However, a :class:`Component` can also serve as a template,
           so if you need the ability to assemble an object *and* use
           its definition as the basis for other components, then define
           the default dependencies and/or lifecycle methods in a
           :class:`Component` and use that component's ID as the
           :attr:`Component.parent_id` in other components.

        *unique_id* must be a user-provided identifier that is unique
        within the context to which this template is added. A component
        may then be instructed to use a template by specifying the same
        value for :attr:`Component.parent_id`.

        *parent_id* is **another** :attr:`Component.unique_id` or
        :attr:`Template.unique_id` in the same context that descibes
        **this** template's default dependencies and/or lifecycle
        methods.

        *after_inject* is the name of a method *of objects of this
        component* that will be called after **all** dependencies have
        been injected, but before the object is returned to the caller.
        This method will be called with **no** arguments (positional or
        keyword). Exceptions raised by this method are not caught.

        .. note::
           ``Template.after_inject``, if specified, **replaces**
           :attr:`aglyph.context.Context.after_inject` for any component
           that uses the template.

        *before_clear* is the name of a method *of objects of this
        component* that will be called immediately before the object is
        cleared from cache via
        :meth:`aglyph.assembler.Assembler.clear_singletons()`,
        :meth:`aglyph.assembler.Assembler.clear_borgs()`, or
        :meth:`aglyph.assembler.Assembler.clear_weakrefs()`.

        .. note::
           ``Template.before_clear``, if specified, **replaces**
           :attr:`aglyph.context.Context.before_clear` for any component
           that uses the template.

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
            "TRACE %r, parent_id=%r, after_inject=%r, before_clear=%r",
            template_id, parent_id, after_inject, before_clear)
        super(Template, self).__init__()
        self._unique_id = template_id
        self._parent_id = parent_id
        self._after_inject = after_inject
        self._before_clear = before_clear

    @property
    def unique_id(self):
        """Uniquely identifies this template in a context *(read-only)*.

        """
        return self._unique_id

    @property
    def parent_id(self):
        """Identifies this template's parent template or component
        *(read-only)*.

        """
        return self._parent_id

    @property
    def after_inject(self):
        """The name of the component object method that will be called
        after **all** dependencies have been injected.

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

    def __repr__(self):
        return "%s.%s(%r, parent_id=%r, after_inject=%r, before_clear=%r)" % (
            self.__class__.__module__, self.__class__.__name__,
            self._unique_id, self._parent_id, self._after_inject,
            self._before_clear)


class Component(Template):
    """Define a component and the dependencies needed to create a new
    object of that component at runtime.

    """

    __slots__ = [
        "_dotted_name",
        "_factory_name",
        "_member_name",
        "_strategy",
    ]

    __logger = logging.getLogger("%s.Component" % __name__)

    def __init__(self, component_id, dotted_name=None, factory_name=None,
                 member_name=None, strategy=Strategy.PROTOTYPE,
                 parent_id=None, after_inject=None, before_clear=None):
        """
        :arg str component_id: context-unique identifier for this\
                               component
        :keyword str dotted_name: an **importable** dotted name
        :keyword str factory_name: names a :obj:`callable` member of\
                                   the object identified by\
                                   *component_id* or *dotted_name*
        :keyword str member_name: names **any** member of the object\
                                  identified by *component_id* or\
                                  *dotted_name*
        :keyword str strategy: specifies the component assembly strategy
        :keyword str parent_id: specifies the ID of a template or\
                                component that describes the default\
                                dependencies and/or lifecyle methods\
                                for this component
        :keyword str after_inject: specifies the name of the method\
                                   that will be called on objects of\
                                   this component after all of its\
                                   dependencies have been injected
        :keyword str before_clear: specifies the name of the method\
                                   that will be called on objects of\
                                   this component immediately before\
                                   they are cleared from cache
        :raise aglyph.AglyphError: if both *factory_name* and\
                                   *member_name* are specified
        :raise ValueError: if *strategy* is not a recognized assembly\
                           strategy

        *component_id* must be a user-provided identifier that is unique
        within the context to which this component is added. An
        **importable** dotted name may be used (see
        :func:`aglyph.resolve_dotted_name`).

        *dotted_name*, if provided, must be an **importable** dotted
        name (see :func:`aglyph.resolve_dotted_name`).

        .. note::
           If *dotted_name* is not specified, then *component_id*
           will be used as the component's dotted name. In this case,
           *component_id* **must** be an importable dotted name.

        .. versionadded:: 2.0.0
           the *factory_name* keyword argument

        *factory_name* is the name of a :obj:`callable` member of
        *dotted-name* (i.e. a function, class, staticmethod, or
        classmethod). When provided, the assembler will call this member
        to create an object of this component.

        *factory_name* enables Aglyph to inject dependencies into
        objects that can only be initialized via nested classes,
        :obj:`staticmethod`, or :obj:`classmethod`. See
        :attr:`factory_name` for details.

        .. versionadded:: 2.0.0
           the *member_name* keyword argument

        *member_name* is the name of a member of *dotted-name*, which
        **may or may not** be callable.

        *member_name* differs from *factory_name* in two ways:

        1. *member_name* is not restricted to callable members; it may
           identify attributes and/or properties as well.
        2. When an assembler assembles a component with a
           *member_name*, initialization of the object is *bypassed*
           (i.e. the assembler will not call the member, and any
           initialization arguments defined for the component will be
           **ignored**).

        *member_name* enables Aglyph to reference class, function,
        :obj:`staticmethod`, and :obj:`classmethod` obejcts, as well as
        simple attributes or properties, as components and dependencies.
        See :attr:`member_name` for details.

        .. note::

           Both *factory_name* and *member_name* can be dot-separated
           names to reference nested members.

        .. warning::
           The *factory_name* and *member_name* arguments are mutually
           exclusive. An exception is raised if both are provided.

        *strategy* must be a recognized component assembly strategy, and
        defaults to ``Strategy.PROTOTYPE`` (*"prototype"*) if not
        specified.

        Please see :data:`Strategy` for a description of the component
        assembly strategies supported by Aglyph.

        .. warning::
           The ``Strategy.BORG`` (*"borg"*) component assembly strategy
           is only supported for classes that **do not** define or
           inherit ``__slots__``!

        .. versionadded:: 2.1.0
           the *parent_id* keyword argument

        *parent_id* is the context-unique ID of a :class:`Template` (or
        another ``Component``) that defines default dependencies and/or
        lifecycle methods for this component.

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

        Once a ``Component`` instance is initialized, the ``args``
        (:obj:`list`), ``keywords`` (:obj:`dict`), and ``attributes``
        (:class:`collections.OrderedDict`) members can be modified
        in-place to define the dependencies that must be injected into
        objects of this component at assembly time. For example::

           component = Component("http.client.HTTPConnection")
           component.args.append("www.ninthtest.net")
           component.args.append(80)
           component.keywords["strict"] = True
           component.attributes["set_debuglevel"] = 1

        In Aglyph, a component may:

        * be assembled directly by an
          :class:`aglyph.assembler.Assembler` or
          :class:`aglyph.binder.Binder`
        * identify other components as dependencies (using a
          :class:`Reference`)
        * be used by other components as a dependency
        * use common dependencies and behaviors (*after_inject*,
          *before_clear*) defined in a
          :class:`aglyph.component.Template`
        * use any combination of the above behaviors

        """
        self.__logger.debug(
            "TRACE %r, dotted_name=%r, factory_name=%r, member_name=%r, "
            "strategy=%r, parent_id=%r, after_inject=%r, before_clear=%r",
            component_id, dotted_name, factory_name, member_name, strategy,
            parent_id, after_inject, before_clear)
        if ((factory_name is not None) and (member_name is not None)):
            raise AglyphError(
                "only one of factory_name or member_name may be specified")
        super(Component, self).__init__(component_id, parent_id=parent_id,
                                        after_inject=after_inject,
                                        before_clear=before_clear)
        if (dotted_name is not None):
            self._dotted_name = dotted_name
        else:
            self._dotted_name = component_id
        self._factory_name = factory_name
        self._member_name = member_name
        if (strategy in Strategy):
            self._strategy = strategy
        else:
            raise ValueError("unrecognized assembly strategy %r" % strategy)
        if ((strategy == Strategy.PROTOTYPE) and (before_clear is not None)):
            self._before_clear = None
            warning_msg = (
                "ignoring before_clear=%r for prototype component %r" %
                (before_clear, component_id))
            self.__logger.warning(warning_msg)
            warnings.warn(RuntimeWarning(warning_msg))

    @property
    def component_id(self):
        """The unique component identifier *(read-only)*.

        .. deprecated:: 2.1.0
           use :attr:`unique_id` instead.

        """
        warnings.warn(
            AglyphDeprecationWarning("Component.component_id",
                                     replacement="Component.unique_id"))
        return self._unique_id

    @property
    def dotted_name(self):
        """The importable dotted name for objects of this component
        *(read-only)*.

        """
        return self._dotted_name

    @property
    def factory_name(self):
        """The name of a :obj:`callable` member of :attr:`dotted_name`
        *(read-only)*.

        ``factory_name`` can be used to initialize objects of the
        component when a class is not directly importable (e.g. the
        component class is a nested class), or when component objects
        need to be initialized via :obj:`staticmethod` or
        :obj:`classmethod`.

        Consider the following::

           # module.py
           class Example:
               class Nested:
                   pass

        The following examples show how to define a component that will
        produce an *instance* of the ``module.Example.Nested`` class
        when assembled.

        Programmatic configuration using :class:`Component`::

           component = Component("nested-object",
                                 dotted_name="module.Example",
                                 factory_name="Nested")

        Programmatic configuration using :class:`aglyph.binder.Binder`::

           from aglyph.binder import Binder
           from module import Example

           binder = Binder()
           binder.bind("nested-object", to=Example, factory="Nested")

        Declarative XML configuration::

           <component id="nested-object" dotted-name="module.Example"
               factory-name="Nested" />

        ``factory_name`` may also be a dot-separated name to specify an
        arbitrarily-nested callable:

        Programmatic configuration using :class:`Component`::

           component = Component("nested-object", dotted_name="module",
                                 factory_name="Example.Nested")

        Programmatic configuration using :class:`aglyph.binder.Binder`::

           from aglyph.binder import Binder
           import module

           binder = Binder()
           binder.bind("nested-object", to=module,
                       factory="Example.Nested")

        Declarative XML configuration::

           <component id="nested-object" dotted-name="module"
               factory-name="Example.Nested" />

        .. note::
           The important thing to remember is that :attr:`dotted_name`
           must be **importable**, and ``factory_name`` must be
           accessible from the imported class or module via attribute
           access.

        """
        return self._factory_name

    @property
    def member_name(self):
        """The name of any member of :attr:`dotted_name` *(read-only)*.

        ``member_name`` can be used to obtain an object *directly* from
        an importable module or class. The named member is simply
        accessed and returned (it is **not** called, even if it is
        callable).

        Consider the following::

           # module.py
           class Example:
               class Nested:
                   pass

        The following examples show how to define a component that will
        produce the ``module.Example.Nested`` class *itself* when
        assembled.

        Programmatic configuration using :class:`Component`::

           component = Component("nested-class",
                                 dotted_name="module.Example",
                                 member_name="Nested")

        Programmatic configuration using :class:`aglyph.binder.Binder`::

           from aglyph.binder import Binder
           from module import Example

           binder = Binder()
           binder.bind("nested-class", to=Example, member="Nested")

        Declarative XML configuration::

           <component id="nested-class" dotted-name="module.Example"
               member-name="Nested" />

        ``member_name`` may also be a dot-separated name to specify an
        arbitrarily-nested member:

        Programmatic configuration using :class:`Component`::

           component = Component("nested-class", dotted_name="module",
                                 member_name="Example.Nested")

        Programmatic configuration using :class:`aglyph.binder.Binder`::

           from aglyph.binder import Binder
           import module

           binder = Binder()
           binder.bind("nested-class", to=module,
                       member="Example.Nested")

        Declarative XML configuration::

           <component id="nested-class" dotted-name="module"
               member-name="Example.Nested" />

        .. note::
           The important thing to remember is that :attr:`dotted_name`
           must be **importable**, and ``member_name`` must be
           accessible from the imported class or module via attribute
           access.

        .. warning::
           When a component specifies ``member_name``, initialization is
           assumed. In other words, Aglyph **will not** attempt to
           initialize the member, and will **ignore** any
           :attr:`init_args` or :attr:`init_keywords`.

           On assembly, if any initialization arguments and/or keyword
           arguments have been defined for such a component, they are
           discarded and a WARN-level log record is emitted to the
           "aglyph.assembler.Assembler" channel.

           Any :attr:`attributes` that have been specified for the
           component will still be processed as setter injection
           dependencies, however.

        """
        return self._member_name

    @property
    def strategy(self):
        """The component assembly strategy *(read-only)*."""
        return self._strategy

    @property
    def init_args(self):
        """The positional arguments for constructor injection of
        component object dependencies.

        .. deprecated:: 2.1.0
           use :attr:`args` instead.

        .. note::
           This property may not be set; it must be modified by
           reference.

        """
        warnings.warn(AglyphDeprecationWarning("Component.init_args",
                                               replacement="Component.args"))
        return self.args

    @property
    def init_keywords(self):
        """The keyword arguments for constructor injection of component
        object dependencies.

        .. deprecated:: 2.1.0
           use :attr:`keywords` instead.

        .. note::
           This property may not be set; it must be modified by
           reference.

        """
        warnings.warn(
            AglyphDeprecationWarning("Component.init_keywords",
                                     replacement="Component.keywords"))
        return self.keywords

    def __repr__(self):
        return ("%s.%s(%r, dotted_name=%r, factory_name=%r, member_name=%r, "
                "strategy=%r, parent_id=%r, after_inject=%r, "
                "before_clear=%r)") % (
                    self.__class__.__module__, self.__class__.__name__,
                    self._unique_id, self._dotted_name, self._factory_name,
                    self._member_name, self._strategy, self._parent_id,
                    self._after_inject, self._before_clear)

