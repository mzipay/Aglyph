# -*- coding: utf-8 -*-

# Copyright (c) 2006-2013 Matthew Zipay <mattz@ninthtest.net>
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

""".. versionadded:: 1.1.0

The Aglyph binder provides a much simpler and more compact alternative
to :class:`aglyph.assembler.Assembler`, :class:`aglyph.context.Context`,
and :class:`aglyph.component.Component` for programmatic configuration
of Aglyph.

"Binding" usually results in much less configuration code. An
:class:`aglyph.binder.Binder` also offers the same functionality as an
:class:`aglyph.assembler.Assembler`, so the same object used to
configure injection can be used to *perform* injection, further reducing
the amount of "bootstrap" code needed.

For example, the following two blocks exhibit identical behavior:

Using ``Assembler`` / ``Context`` / ``Component``::

    context = Context("context-id")
    assembler = Assembler(context)
    component = Component("my.package.MyClass")
    component.init_args.append("arg")
    component.init_keywords["kw"] = "value"
    component.attributes["set_spam"] = "eggs"
    context.add(component)
    my = assembler.assemble("my.package.MyClass")

Using ``Binder``::

    binder = Binder()
    binder.bind(MyClass).init("arg", kw="value").attributes(set_spam="eggs")
    my = binder.lookup(MyClass)

"""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "1.1.1"

import logging
from uuid import uuid4

from aglyph import format_dotted_name, identify_by_spec
from aglyph.assembler import Assembler
from aglyph.compat import ClassAndFunctionTypes
from aglyph.component import Component, Reference, Strategy
from aglyph.context import Context

__all__ = [
    "Binder",
]

_logger = logging.getLogger(__name__)


class Binder(Assembler):
    """Configure application components *and* provide assembly services
    (see :func:`lookup`) for those components.

    """

    _logger = logging.getLogger("%s.Binder" % __name__)

    def __init__(self, binder_id=None):
        """*binder_id* is a unique identifier for this instance. If it
        is not provided, a random ID is generated.

        """
        self._logger.debug("TRACE")
        if (binder_id is None):
            binder_id = uuid4()
        super(Binder, self).__init__(Context("binder:%s" % binder_id))
        self._binder_id = binder_id
        self._logger.info("initialized %s", self)
        self._logger.debug("RETURN")

    @property
    def binder_id(self):
        """a read-only property for the binder ID"""
        return self._binder_id

    def bind(self, component_spec, to=None, strategy=Strategy.PROTOTYPE):
        """Define a component by associating the unique ID for
        *component_spec* with the dotted-name for *to*.

        *component_spec* any importable class or unbound function, or
        a user-defined identifier, that will serve as the :func:`lookup`
        key for objects of the component.

        *to* is the importable class or unbound function, or the
        dotted-name for the same, that will be called to product objects
        of the component.

        If *to* is not provided, the component ID and dotted-name will
        be identical. In this case *component_spec* **must** be a class,
        a function, or a dotted-name.

        *strategy* must be a recognized component assembly strategy, and
        defaults to :attr:`aglyph.component.Strategy.PROTOTYPE`
        (*"prototype"*) if not specified.

        Please see :class:`aglyph.component.Strategy` for a description
        of the component assembly strategies supported by Aglyph.

        .. warning::
            The :attr:`aglyph.component.Strategy.BORG` (*"borg"*)
            component assembly strategy is only supported for classes
            that **do not** define or inherit ``__slots__``!

        :returns: a :class:`_Binding` object that allows the component
                  dependencies to be defined in chained-call fashion.

        """
        self._logger.debug("TRACE %r, to=%r, strategy=%r", component_spec, to,
                           strategy)
        component_id = identify_by_spec(component_spec)
        if (to is None):
            dotted_name = component_id
        else:
            dotted_name = identify_by_spec(to)
        component = Component(component_id, dotted_name, strategy)
        self._context.add(component)
        self._logger.info("bound %r to %r (%r)", component_spec, to,
                           dotted_name)
        binding = _Binding(component)
        self._logger.debug("RETURN %r", binding)
        return binding

    def lookup(self, component_spec):
        """Return an instance of the component specified by
        *component_spec* with all of its dependencies provided.

        *component_spec* must be an importable class or unbound
        function, or a user-defined unique identifier, that was
        previously bound by a call to :func:`bind`.

        """ 
        self._logger.debug("TRACE %r", component_spec)
        component_id = identify_by_spec(component_spec)
        obj = self.assemble(component_id)
        self._logger.debug("RETURN %r", type(obj))
        return obj


class _Binding(object):
    """.. note::

        This class is not intended to be imported or created directly;
        instances are returned automatically from the
        :meth:`Binder.bind` method.

    A ``_Binding`` allows component dependencies to be defined in
    chained-call fashion::

        Binder().bind(...).init(*args, **keywords).attributes(**keywords)

    Or, if you don't prefer chained calls::

        binding = Binder().bind(...)
        binding.init(*args, **keywords)
        binding.attributes(**keywords)

    """

    __slots__ = ["_component"]

    _logger = logging.getLogger("%s._Binding" % __name__)

    def __init__(self, component):
        """*component* is an :class:`aglyph.component.Component` that
        was created by a call to :meth:`Binder.bind`.

        """
        self._logger.debug("TRACE %r", component)
        self._component = component

    def init(self, *args, **keywords):
        """Define the initialization dependencies (i.e. position and/or
        keyword arguments) for a component.

        *args* are the positional argument dependencies, and *keywords*
        are the keyword argument dependencies.

        .. warning::

            Multiple calls to this method on the same instance are *not*
            cumulative; each call will **replace** the
            :attr:`aglyph.component.Component.init_args` list and the
            :attr:`aglyph.component.Component.init_keywords` map.

        """
        if (self._logger.isEnabledFor(logging.DEBUG)):
            # do not log possibly sensitive data
            self._logger.debug("TRACE *%r, **%r", [type(arg) for arg in args],
                               dict([(k, type(v))
                                     for (k, v) in keywords.items()]))
        resolve = self._resolve
        self._component.init_args = [resolve(arg) for arg in args]
        self._component.init_keywords = dict(
            [(keyword, resolve(arg)) for (keyword, arg) in keywords.items()])
        self._logger.debug("RETURN self")
        return self

    def attributes(self, **keywords):
        """Define the attribute dependencies (i.e. fields, setter
        methods, and/or properties) for a component.

        *keywords* are the field, setter method, and/or property
        dependencies. Each keyword name corresponds to the name of a
        simple attribute (field), setter method, or property.

        .. warning::

            Multiple calls to this method on the same instance are *not*
            cumulative; each call will **replace** the
            :attr:`aglyph.component.Component.attributes` map.

        """
        if (self._logger.isEnabledFor(logging.DEBUG)):
            # do not log possibly sensitive data
            self._logger.debug("TRACE **%r",
                dict([(k, type(v)) for (k, v) in keywords.items()]))
        resolve = self._resolve
        self._component.attributes = dict(
                [(name, resolve(value)) for (name, value) in keywords.items()])
        self._logger.debug("RETURN self")
        return self

    def _resolve(self, obj):
        """Return an :class:`aglyph.component.Reference` if *obj* is a
        class or function; otherwise, return *obj* itself.

        """
        if (isinstance(obj, ClassAndFunctionTypes)):
            return Reference(format_dotted_name(obj))
        else:
            return obj

    def __repr__(self):
        return "%s:%s<%s>" % (self.__class__.__module__,
                              self.__class__.__name__, self._component)

