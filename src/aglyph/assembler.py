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

"""The Aglyph assembler injects dependencies into application components.

Application components and their dependencies are defined in an
:class:`aglyph.context.Context`, which is used to initialize an
assembler.

An assembler provides thread-safe caching of **singleton** component
instances and **borg** component shared-states (i.e. instance
``__dict__`` references).

"""

from __future__ import with_statement

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "1.0.0"

import functools
from inspect import isclass
import logging

from aglyph import AglyphError, resolve_dotted_name
from aglyph.compat import is_callable, new_instance
from aglyph.cache import ReentrantMutexCache
from aglyph.component import Evaluator, Reference, Strategy

__all__ = ["Assembler"]

_logger = logging.getLogger(__name__)


class Assembler(object):
    """Creates application objects using type 2 (setter) and type 3
    (constructor) dependency injection.

    """

    _logger = logging.getLogger("%s.Assembler" % __name__)

    def __init__(self, context):
        """*context* should be an :class:`aglyph.context.Context`."""
        super(Assembler, self).__init__()
        self._context = context
        self._singleton_cache = ReentrantMutexCache()
        self._borg_cache = ReentrantMutexCache()
        self._assembly_stack = []
        self._logger.info("initialized %s", self)

    def assemble(self, component_id):
        """Returns an instance of the component specified by
        *component_id* with all of its dependencies provided.

        *component_id* must be a valid "relative_module.identifier"
        dotted-name string or a user-provided unique component
        identifier.

        """
        self._logger.info("assembling %r", component_id)
        # check for circular dependency
        if (component_id in self._assembly_stack):
            raise AglyphError("circular dependency detected: %s" %
                              " => ".join(self._assembly_stack +
                                          [component_id]))
        self._assembly_stack.append(component_id)
        self._logger.debug("current assembly stack: %s", self._assembly_stack)
        try:
            component = self._context[component_id]
            instance = self._create(component)
            if (component.strategy == Strategy.PROTOTYPE):
                self._wire(instance, component)
            return instance
        finally:
            self._assembly_stack.pop()

    def _create(self, component):
        """Returns an instance of *component*.

        *component* is an :class:`aglyph.component.Component`.

        """
        create = getattr(self, "_create_%s" % component.strategy, None)
        if (create is None):
            raise AglyphError("don't know how to create a %r component" %
                              component.strategy)
        return create(component)

    def _create_prototype(self, component):
        """Returns an instance of the prototype *component*.

        *component* is an :class:`aglyph.component.Component` having
        ``strategy="prototype"``.

        A new instance is always created and initialized.

        """
        self._logger.info("creating %s", component)
        instance = self._initialize(component)
        return instance

    def _create_singleton(self, component):
        """Returns an instance of the singleton *component*.

        *component* is an :class:`aglyph.component.Component` having
        ``strategy="singleton"``.

        If *component* has previously been assembled, the cached
        instance is returned. Otherwise, a new instance is created,
        initialized, wired, cached, and then returned.

        """
        self._logger.info("creating %s", component)
        with self._singleton_cache.lock:
            instance = self._singleton_cache.get(component.component_id)
            self._logger.debug("cached instance for %s is %s", component,
                               type(instance))
            if (instance is None):
                # singletons are initialized and wired once, then cached
                instance = self._initialize(component)
                self._wire(instance, component)
                self._singleton_cache[component.component_id] = instance
            return instance

    def _create_borg(self, component):
        """Returns an instance of the borg *component*.

        *component* is an :class:`aglyph.component.Component` having
        ``strategy="borg"``.

        A new instance is always created. If *component* has previously
        been assembled, the cached shared-state is assigned to the new
        instance's ``__dict__`` and the instance is returned. Otherwise,
        the new instance is initialized and wired, it's ``__dict__`` is
        cached, and then the instance is returned.

        """
        self._logger.info("creating %s", component)
        with self._borg_cache.lock:
            shared_state = self._borg_cache.get(component.component_id)
            self._logger.debug("cached shared-state for %s is %s", component,
                               type(shared_state))
            if (shared_state is None):
                # borgs are initialized and wired, then the state is cached
                instance = self._initialize(component)
                self._wire(instance, component)
                self._borg_cache[component.component_id] = instance.__dict__
                return instance
            else:
                # TODO: test fixtures for TypeError and AglyphError
                # always create a new instance of borg
                cls = resolve_dotted_name(component.dotted_name)
                if (not isclass(cls)):
                    raise TypeError("expected class, not %s"
                                    % type(cls).__name__)
                elif (hasattr(cls, "__slots__")):
                    # old-style classes do not enforce __slots__, but if
                    # __slots__ is defined for an old-style class, assume the
                    # intent is clear and reject anyway
                    raise AglyphError("borg is not supoprted for classes that "
                                      "define or inherit __slots__")
                instance = new_instance(cls)
                instance.__dict__ = shared_state
                return instance

    def _initialize(self, component):
        """Returns a new instance of *component* initialized with its
        dependencies.

        *component* is an :class:`aglyph.component.Component`.

        This method performs type 3 (constructor) injection.

        """
        self._logger.info("initializing %s", component)
        initializer = resolve_dotted_name(component.dotted_name)
        (args, kwargs) = self._resolve_args_and_keywords(component)
        if (isclass(initializer)):
            instance = new_instance(initializer)
            instance.__init__(*args, **kwargs)
            return instance
        else:
            # use the __call__ protocol
            return initializer(*args, **kwargs)

    def _resolve_args_and_keywords(self, component):
        """Returns the fully assembled/evaluated positional and keyword
        arguments for *component*.

        *component* is an :class:`aglyph.component.Component`.

        The arguments returned from this method are ready to be passed
        directly to an initializer.

        """
        self._logger.debug("resolving args and keywords for %s", component)
        args = tuple([self._resolve(arg) for arg in component.init_args])
        keywords = dict([(n, self._resolve(v))
                       for (n, v) in component.init_keywords.items()])
        return (args, keywords)

    def _wire(self, instance, component):
        """Injects dependencies into *instance*.

        *instance* is an initialized object of the type defined by
        *component* (which is an :class:`aglyph.component.Component`).

        This method performs type 2 (setter) injection for *instance*,
        based on the attributes defined in *component*.

        """
        self._logger.info("wiring %s", component)
        for (attr_name, raw_attr_value) in component.attributes.items():
            instance_attr = getattr(instance, attr_name)
            attr_value = self._resolve(raw_attr_value)
            if (is_callable(instance_attr)):
                # this is a setter method
                instance_attr(attr_value)
            else:
                # this is a simple attribute or property
                setattr(instance, attr_name, attr_value)

    def _resolve(self, value_spec):
        """Returns the actual value of an initialization or attribute
        value specification.

        If *value_spec* is an :class:`aglyph.component.Reference`, the
        :func:`assemble` method is called recursively to
        assemble the specified component, which is then returned.

        If *value_spec* is an :class:`aglyph.component.Evaluator`, it is
        evaluated (which may also result in nested references being
        assembled, as described above). The resulting value is returned.

        If *value_spec* is a :func:`functools.partial`, it is called,
        and the resulting value is returned.

        In any other case, *value_spec* is returned **unchanged**.

        """
        if (isinstance(value_spec, Reference)):
            return self.assemble(value_spec)
        elif (isinstance(value_spec, Evaluator)):
            # need to pass a reference to the assembler since the
            # evaluation may require further component assembly
            return value_spec(self)
        elif (isinstance(value_spec, functools.partial)):
            return value_spec()
        else:
            return value_spec

    def clear_singletons(self):
        """Evicts all cached singleton component instances.

        A list of evicted component IDs is returned.

        """
        with self._singleton_cache.lock:
            singleton_ids = list(self._singleton_cache.keys())
            self._logger.info("evicting cached singletons %s", singleton_ids)
            self._singleton_cache.clear()
            return singleton_ids

    def clear_borgs(self):
        """Evicts all cached borg component shared-states.

        A list of component IDs (corresponding to the evicted
        shared-state instance ``__dict__`` references) is returned.

        """
        with self._borg_cache.lock:
            borg_ids = list(self._borg_cache.keys())
            self._logger.info("evicting cached borg states %s", borg_ids)
            self._borg_cache.clear()
            return borg_ids

    def __contains__(self, component_id):
        """Returns ``True`` if the *component_id* is defined in this
        assembler's context.

        *component_id* must be a valid "relative_module.identifier"
        dotted-name string or a user-provided unique component
        identifier.

        """
        return (component_id in self._context)

    def __repr__(self):
        return "%s:%s<%s>" % (self.__class__.__module__,
                              self.__class__.__name__, self._context)
