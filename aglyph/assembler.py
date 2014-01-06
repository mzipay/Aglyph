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

"""The Aglyph assembler creates application objects from component
definitions, injecting dependencies into those objects through
initialization arguments and keywords, attributes, setter methods,
and/or properties.

Application components and their dependencies are defined in an
:class:`aglyph.context.Context`, which is used to initialize an
assembler.

An assembler provides thread-safe caching of **singleton** component
instances and **borg** component shared-states (i.e. instance
``__dict__`` references).

"""

from __future__ import with_statement

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "2.0.0"

import functools
import inspect
import logging

from aglyph import AglyphError, resolve_dotted_name
from aglyph.compat import is_callable, new_instance
from aglyph.cache import ReentrantMutexCache
from aglyph.component import Evaluator, Reference, Strategy

__all__ = ["Assembler"]

_logger = logging.getLogger(__name__)


class Assembler(object):
    """Create application objects using type 2 (setter) and type 3
    (constructor) dependency injection.

    """

    __logger = logging.getLogger("%s.Assembler" % __name__)

    def __init__(self, context):
        """
        :param aglyph.context.Context context:\
           a mapping of unique component identifierss to component\
           definitions

        """
        self.__logger.debug("TRACE %r", context)
        super(Assembler, self).__init__()
        self._context = context
        self._singleton_cache = ReentrantMutexCache()
        self._borg_cache = ReentrantMutexCache()
        self._assembly_stack = []
        self.__logger.info("initialized %r", self)
        self.__logger.debug("RETURN")

    def assemble(self, component_id):
        """Create an object identified by *component_id* and inject
        its dependencies.

        :param str component_id:\
           a "relative_module.identifier" dotted-name or user-defined\
           component identifier
        :return: a complete object with all of its resolved dependencies
        :raise aglyph.AglyphError:\
           if the component defines a circular dependency

        How a component object is assembled (created, initialized,
        wired, and returned) is determined by the component's
        :attr:`aglyph.component.Component.strategy`:

        **"prototype"**
           A new object is always created, initialized, wired, and
           returned.

           This is the default assembly strategy for Aglyph components.

        **"singleton"**
           If the component has been assembled already during the
           current application lifetime **and** there has been no
           intervening call to :meth:`clear_singletons`, then a cached
           reference to the object is returned.

           Otherwise, a new object is created, initialized, wired,
           cached, and returned.

           Singleton component objects are cached by their
           :attr:`aglyph.component.Component.component_id`.

           .. note::
              Assembly of singleton components is a thread-safe
              operation.

        **"borg"**
           If the component has been assembled already during the
           current application lifetime **and** there has been no
           intervening call to :meth:`clear_borgs`, then a new instance
           is created and a cached reference to the shared-state is
           directly assigned to the instance ``__dict__``.

           Otherwise, a new instance is created, initialized, and wired;
           its instance ``__dict__`` is cached; and the instance is
           returned.

           Borg component instance shared-states are cached by their
           :attr:`aglyph.component.Component.component_id`.

           .. note::
              Assembly of borg components is a thread-safe operation.

           .. warning::
              * The borg assembly strategy is **only** supported for
                components that are non-builtin classes.
              * The borg assembly strategy is **not** supported for
                classes that define or inherit a ``__slots__`` member.

        .. versionadded:: 2.0.0
           **Either** :attr:`aglyph.component.Component.factory_name`
           **or** :attr:`aglyph.component.Component.member_name` may be
           defined to exercise more control over how a component object
           is created and initialized. Refer to the linked documentation
           for details.

        .. note::
           This method is called recursively to assemble any dependency
           of *component_id* that is defined as an
           :class:`aglyph.component.Reference`.

        """
        self.__logger.debug("TRACE %r", component_id)
        # check for circular dependency
        if (component_id in self._assembly_stack):
            raise AglyphError("circular dependency detected: %s" %
                              " => ".join(self._assembly_stack +
                                          [component_id]))
        self._assembly_stack.append(component_id)
        self.__logger.debug("current assembly stack: %r", self._assembly_stack)
        try:
            component = self._context[component_id]
            obj = self._create(component)
            if (component.strategy == Strategy.PROTOTYPE):
                self._wire(obj, component)
            self.__logger.info("assembled %r", component_id)
            self.__logger.debug("RETURN %r", type(obj))
            return obj
        finally:
            self._assembly_stack.pop()

    def _create(self, component):
        """Create an object of *component*.

        :param aglyph.component.Component component:\
           a component definition
        :return: an initialized object

        This method delegates to the appropriate
        ``_create_\<strategy\>`` method for *component*.

        """
        # allow AttributeError
        create = getattr(self, "_create_%s" % component.strategy)
        return create(component)

    def _create_prototype(self, component):
        """Create and initialize a prototype object for *component*.

        :param aglyph.component.Component component:\
           a component definition having strategy="prototype"
        :return: an initialized prototype object

        A new object is always created and initialized when a
        "prototype" component is assembled.

        This is the default assembly strategy for Aglyph components.

        """
        self.__logger.debug("TRACE %r", component)
        obj = self._initialize(component)
        self.__logger.info("created %r", component.component_id)
        self.__logger.debug("RETURN %r", type(obj))
        return obj

    def _create_singleton(self, component):
        """Return the singleton object for *component*.

        :param aglyph.component.Component component:\
           a component definition having strategy="singleton"
        :return:\
           the complete singleton object with all resolved dependencies

        If *component* has previously been assembled, the cached object
        is returned. Otherwise, a new object is created, initialized,
        wired, cached, and then returned.

        .. note::
           Assembly of singleton components is a thread-safe operation.

        """
        self.__logger.debug("TRACE %r", component)
        with self._singleton_cache.lock:
            obj = self._singleton_cache.get(component.component_id)
            if (obj is None):
                # singletons are initialized and wired once, then cached
                obj = self._initialize(component)
                self._wire(obj, component)
                self._singleton_cache[component.component_id] = obj
                self.__logger.info("created and cached %r as %r", component,
                                   type(obj))
            else:
                self.__logger.info("retrieved %r from cache as %r", component,
                                   type(obj)) 
            self.__logger.debug("RETURN %r", obj)
            return obj

    def _create_borg(self, component):
        """Create and initialize a borg object for *component*.

        :param aglyph.component.Component component:\
           a component definition having strategy="borg"
        :return:\
           the complete borg instance with all resolved dependencies

        A new instance is always created. If *component* has been
        previously assembled, the cached shared-state is assigned to the
        new instance's ``__dict__`` and the instance is returned.
        Otherwise, the new instance is initialized and wired, its
        ``__dict__`` is cached, and then the instance is returned.

        .. note::
           Assembly of borg components is a thread-safe operation.

        .. warning::
           * The borg assembly strategy is **only** supported for
             components that are non-builtin classes.
           * The borg assembly strategy is **not** supported for
             classes that define or inherit a ``__slots__`` member.

        """
        self.__logger.debug("TRACE %r", component)
        with self._borg_cache.lock:
            shared_state = self._borg_cache.get(component.component_id)
            if (shared_state is None):
                # borgs are initialized and wired, then the state is cached
                instance = self._initialize(component)
                self._wire(instance, component)
                self._borg_cache[component.component_id] = instance.__dict__
                self.__logger.info("created and cached shared-state for %r",
                                   component)
            else:
                self.__logger.info("retrieved shared-state for %r from cache",
                                   component)
                cls = self._resolve_initializer(component)
                instance = (
                    new_instance(cls) if (component.member_name is None)
                    else cls)
                instance.__dict__ = shared_state
            self.__logger.debug("RETURN %r", instance)
            return instance

    def _initialize(self, component):
        """Create a new *component* object initialized with its
        dependencies.

        :param aglyph.component.Component component:\
           a component definition
        :return: an initialized object of *component*

        This method performs **type 3 (constructor)** dependency
        injection.

        """
        self.__logger.debug("TRACE %r", component)
        initializer = self._resolve_initializer(component)
        if (component.member_name is None):
            (args, kwargs) = self._resolve_args_and_keywords(component)
            if (inspect.isclass(initializer)):
                obj = new_instance(initializer)
                obj.__init__(*args, **kwargs)
            else:
                # use the __call__ protocol
                obj = initializer(*args, **kwargs)
        else:
            obj = initializer
            if (component.init_args or component.init_keywords):
                self.__logger.warning(
                    "%r uses member_name assembly - ignoring args=%r and "
                    "keywords=%r", component, component.init_args,
                    component.init_keywords)
        self.__logger.debug("RETURN %r", type(obj))
        return obj

    def _resolve_initializer(self, component):
        """Return the object that is responsible for creating new
        *component* objects.

        :param aglyph.component.Component component:\
           a component definition
        :return:\
           a callable if *component.member_name* is undefined, else the\
           member itself (which may or may not be a callable)

        .. note::
           If *component.member_name* is defined, the returned object
           may still be callable (for example, *component.member_name*
           may name a class). However, Aglyph will not **call** the
           member.
           This allows injection of dependencies that are references to
           callable objects like classes and functions.

        """
        self.__logger.debug("TRACE %r", component)
        initializer = resolve_dotted_name(component.dotted_name)
        access_name = component.factory_name or component.member_name
        if (access_name is not None):
            for name in access_name.split('.'):
                initializer = getattr(initializer, name)
        self.__logger.debug("RETURN %r", initializer)
        return initializer

    def _resolve_args_and_keywords(self, component):
        """Assemble or evaluate all positional and keyword arguments
        for *component*.

        :param aglyph.component.Component component:\
           a component definition
        :return:\
           the fully-resolved (i.e. recursively assembled or evaluated)\
           positional and keyword arguments for the *component*\
           initializer
        :rtype:\
           a 2-tuple ``(args, keywords)`` where ``args`` is an N-tuple\
           and ``keywords`` is a :obj:`dict`

        The values returned from this method are ready to be passed
        directly to the *component* initializer (see :meth:`_initialize`
        and :meth:`_resolve_initializer`).

        """
        self.__logger.debug("TRACE %r", component)
        resolve = self._resolve_value
        args = tuple([resolve(arg) for arg in component.init_args])
        keywords = dict([(name, resolve(value))
                         for (name, value) in component.init_keywords.items()])
        self.__logger.debug("RETURN %r", (args, keywords))
        return (args, keywords)

    def _wire(self, obj, component):
        """Inject dependencies into *obj* using direct attribute
        assignment, setter methods, and/or properties.

        :param obj: an initialized object for *component*
        :param aglyph.component.Component component:\
           a component definition

        This method performs **type 2 (setter)** dependency injection.

        """
        self.__logger.debug("TRACE %r, %r", type(obj), component)
        resolve = self._resolve_value
        for (attr_name, raw_attr_value) in component.attributes.items():
            # allow AttributeError
            obj_attr = getattr(obj, attr_name)
            attr_value = resolve(raw_attr_value)
            if (is_callable(obj_attr)):
                # this is a setter method
                obj_attr(attr_value)
            else:
                # this is a simple attribute or property
                setattr(obj, attr_name, attr_value)
        self.__logger.debug("RETURN")

    def _resolve_value(self, value_spec):
        """Assemble or evaluate the runtime value of an initialization
        or attribute value specification.

        :param value_spec:\
           the value specified for a component initialization argument\
           or component attribute

        If *value_spec* is an :class:`aglyph.component.Reference`, the
        :meth:`assemble` method is called recursively to assemble the
        specified component, which is then returned.

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
        """Evict all cached singleton component objects.

        :return: a list of evicted component identifiers
        :rtype: :obj:`list`

        .. note::
           Eviction of singleton components is a thread-safe operation.

        """
        self.__logger.debug("TRACE")
        with self._singleton_cache.lock:
            singleton_ids = list(self._singleton_cache.keys())
            self._singleton_cache.clear()
            self.__logger.info("singleton cache cleared")
            self.__logger.debug("RETURN %r", singleton_ids)
            return singleton_ids

    def clear_borgs(self):
        """Evict all cached borg component shared-states.

        :return:\
           a list of component identifiers corresponding to the evicted\
           shared-state instance ``__dict__`` references
        :rtype: :obj:`list`

        .. note::
           Eviction of borg component shared-states is a thread-safe
           operation.

        """
        self.__logger.debug("TRACE")
        with self._borg_cache.lock:
            borg_ids = list(self._borg_cache.keys())
            self._borg_cache.clear()
            self.__logger.info("borg cache cleared")
            self.__logger.debug("RETURN %r", borg_ids)
            return borg_ids

    def __contains__(self, component_id):
        """Tell whether or not the component identified by
        *component_id* is defined in this assembler's context.

        :param str component_id:\
           a "relative_module.identifier" dotted-name or user-defined\
           component identifier
        :return:
           ``True`` if *component_id* is defined in this assembler's\
           context, else ``False``

        """
        return (component_id in self._context)

    def __repr__(self):
        return "%s.%s(%r)" % (self.__class__.__module__,
                              self.__class__.__name__, self._context)

