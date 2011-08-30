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

"""The classes in this module are used to define components and their
dependencies.

"""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "1.0.0"

import functools
import logging

from aglyph.compat import is_callable, StringTypes, TextType

__all__ = ["Component", "Evaluator", "Reference", "Strategy"]

_logger = logging.getLogger(__name__)


class Strategy(object):
    """Defines the component assembly strategies recognized by Aglyph.

    The default component assembly strategy for Aglyph is
    ``Strategy.PROTOTYPE`` (*"prototype"*).

    """

    PROTOTYPE = "prototype"
    """a new instance of the component is always created, initialized,
    wired, and returned

    """

    SINGLETON = "singleton"
    """only one instance is created, initialized, and wired; the
    instance is cached the first time the component is assembled, and
    subsequent assembly requests return the cached instance

    """

    BORG = "borg"
    """a new instance is always created; the internal state is cached
    the first time the component is assembled, and thereafter all new
    instances share this same state

    """

    _STRATEGIES = set([PROTOTYPE, SINGLETON, BORG])


class Reference(TextType):
    """A place-holder used to refer to another
    :class:`aglyph.component.Component`.

    A ``Reference`` is used as an alias to identify a component that is a
    dependency of another component. The value of a ``Reference`` can be
    either a dotted-name or a user-provided unique ID.

    A ``Reference`` value MUST correspond to a component ID in the same
    context.

    A ``Reference`` can be used as an argument for an
    :class:`aglyph.component.Evaluator`, and can be assembled directly
    by an :class:`aglyph.assembler.Assembler`.

    .. warning::
        In Python versions < 3.0, a ``Reference`` representing a
        dotted-name *must* consist only of characters in the ASCII
        subset of the source encoding (see :pep:`0263`).

        But in Python versions >= 3.0, a ``Reference`` representing a
        dotted-name *may* contain non-ASCII characters
        (see :pep:`3131`).

        Because of this difference, the super class of ``Reference``
        is "dynamic" with respect to the version of Python under which
        Aglyph is running (:class:`unicode` under Python 2.5 - 2.7,
        :class:`str` under Python >= 3.0).

    """

    def __new__(cls, value):
        return TextType.__new__(cls, value)


class Evaluator(object):
    """Enables lazy creation of objects.

    An ``Evaluator`` is similar to a :func:`functools.partial` in that
    they both collect a function and related arguments into a callable
    object with a simplified signature that can be called repeatedly to
    produce a new object.

    *Unlike* a partial function, an ``Evaluator`` may have arguments
    that are not truly "frozen," in the sense that any argument may be
    defined as an :class:`aglyph.component.Reference`, a
    :func:`functools.partial`, or even another ``Evaluator``, which
    needs to be resolved (i.e. assembled/called) before calling *func*.

    """

    __slots__ = ["_func", "_args", "_keywords"]

    _logger = logging.getLogger("%s.Evaluator" % __name__)

    def __init__(self, func, *args, **keywords):
        """An ``Evaluator`` is initialized similar to a
        :func:`functools.partial`:

        *func* must be a callable object that returns new objects,
        *args* is a tuple of positional arguments, and *keywords*
        is a mapping of keyword arguments.

        """
        super(Evaluator, self).__init__()
        if (not is_callable(func)):
            raise TypeError("%s is not callable" % type(func).__name__)
        self._func = func
        self._args = args
        self._keywords = keywords
        self._logger.debug("initialized %s", self)

    @property
    def func(self):
        return self._func

    @property
    def args(self):
        return self._args

    @property
    def keywords(self):
        return self._keywords

    def __call__(self, assembler):
        """Calls ``func(*args, **keywords)`` and returns the new object.

        *assembler* must be a reference to an
        :class:`aglyph.assembly.Assembler`, which is used to assemble
        any :class:`aglyph.component.Reference` encountered in the
        function arguments.

        """
        self._logger.info("evaluating %s", self)
        args = self._args
        keywords = self._keywords
        resolve = self._resolve
        resolved_args = tuple([resolve(arg, assembler) for arg in args])
        # keywords MUST be strings!
        resolved_keywords = dict([(keyword, resolve(arg, assembler))
                                  for (keyword, arg) in keywords.items()])
        return self._func(*resolved_args, **resolved_keywords)

    def _resolve(self, arg, assembler):
        """Returns the resolved argument value.

        *arg* is a positional or keyword argument to the function.
        *assembler* is an :class:`aglyph.assembly.Assembler` used to
        assemble an object if *arg* is an
        :class:`aglyph.component.Reference`.

        """
        self._logger.debug("resolving %r", arg)
        if (isinstance(arg, Reference)):
            return assembler.assemble(arg)
        elif (isinstance(arg, Evaluator)):
            return arg(assembler)
        elif (isinstance(arg, functools.partial)):
            return arg()
        elif (isinstance(arg, dict)):
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
        return "%s:%s<%r %r %r>" % (self.__class__.__module__,
                                    self.__class__.__name__, self._func,
                                    self._args, self._keywords)


class Component(object):
    """Defines a component and the dependencies needed to create a new
    object of the component at runtime.

    """

    __slots__ = ["attributes", "_component_id", "_dotted_name", "init_args",
                 "init_keywords", "_strategy"]

    _logger = logging.getLogger("%s.Component" % __name__)

    def __init__(self, component_id, dotted_name=None,
                 strategy=Strategy.PROTOTYPE):
        """Only a component ID is strictly required to define a
        component.

        *component_id* must be a valid "relative_module.identifier"
        dotted-name string or a user-provided unique component
        identifier.

        *dotted_name*, if provided, must be a valid
        "relative_module.identifier" dotted-name string. If it is not
        provided, *component_id* is assumed to be a dotted-name.

        *strategy* must be a recognized component assembly strategy, and
        defaults to ``Strategy.PROTOTYPE`` (*"prototype"*) if not
        specified.

        Please see :class:`aglyph.component.Strategy` for a description
        of the component assembly strategies supported by Aglyph.
    
        .. warning::
            The ``Strategy.BORG`` (*"borg"*) component assembly strategy
            is only supported for classes that **do not** define or
            inherit ``__slots__``!

        Once a ``Component`` instance is initialized, the ``init_args``
        (list), ``init_keywords`` (dict), and ``attributes`` (dict)
        members can be modified in-place to define the dependencies that
        must be injected into objects of this component at assembly
        time. For example::

            component = Component("http.client.HTTPConnection")
            component.init_args.append("www.ninthtest.net")
            component.init_args.append(80)
            component.init_keywords["strict"] = True
            component.attributes["set_debuglevel"] = 1

        In Aglyph, a component may:

        * be assembled directly by an
          :class:`aglyph.assembler.Assembler`
        * identify other components as dependencies (using
          :class:`aglyph.component.Reference`)
        * be used by other components as a dependency
        * use any combination of the above behaviors

        """
        super(Component, self).__init__()
        self._component_id = component_id
        if (dotted_name is not None):
            self._dotted_name = dotted_name
        else:
            self._dotted_name = component_id
        if (strategy in Strategy._STRATEGIES):
            self._strategy = strategy
        else:
            raise ValueError("unrecognized assembly strategy %r" % strategy)
        self.init_args = []
        self.init_keywords = {}
        self.attributes = {}
        self._logger.debug("initialized %s", self)

    @property
    def component_id(self):
        return self._component_id

    @property
    def dotted_name(self):
        return self._dotted_name

    @property
    def strategy(self):
        return self._strategy

    def __repr__(self):
        return "%s:%s<%r %r %r>" % (self.__class__.__module__,
                                    self.__class__.__name__,
                                    self._component_id, self._dotted_name,
                                    self._strategy)
