# -*- coding: UTF-8 -*-

# Copyright (c) 2006, 2011, 2013-2018 Matthew Zipay.
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

"""The Aglyph assembler creates application objects from component
definitions, injecting dependencies into those objects through
initialization arguments and keywords, attributes, setter methods,
and/or properties.

Application components and their dependencies are defined in an
:class:`aglyph.context.Context`, which is used to initialize an
assembler.

An assembler provides thread-safe caching of **singleton** component
instances, **borg** component shared-states (i.e. instance ``__dict__``
references), and **weakref** component instance weak references.

"""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

from collections import OrderedDict
from functools import partial
from inspect import isclass
import logging
import warnings
import weakref

try:
    import threading
    threading_ = threading
except ImportError:
    import dummy_threading
    threading_ = dummy_threading
    warnings.warn(
        "threading module is not available; aglyph.assembler.Assembler "
            "operations will NOT be thread-safe!",
        RuntimeWarning)

from autologging import logged, traced

from aglyph import (
    AglyphError,
    format_dotted_name,
    _identify,
    resolve_dotted_name,
    __version__,
)
from aglyph._compat import is_string, name_of, new_instance
from aglyph.component import Evaluator, Reference

__all__ = ["Assembler"]

_log = logging.getLogger(__name__)
_log.debug("using %r", threading_)

# thread-local storage for assembly
_assembly = threading_.local()


@traced
@logged
class Assembler(object):
    """Create application objects using type 2 (setter) and type 3
    (constructor) dependency injection.

    """

    def __init__(self, context):
        """
        :arg aglyph.context.Context context:
           a context object mapping unique IDs to component and template
           definitions

        """
        #PYVER: arguments to super() are implicit in Python 3
        super(Assembler, self).__init__()
        self._context = context
        self._caches = {
            "singleton": _ReentrantMutexCache(),
            "borg": _ReentrantMutexCache(),
            "weakref": _ReentrantMutexCache(),
        }
        self.__log.info("initialized %s", self)

    def assemble(self, component_spec):
        """Create an object identified by *component_spec* and inject
        its dependencies.

        :arg component_spec:
           a unique component ID, or an object whose dotted name is a
           unique component ID
        :return:
           a complete object with all of its resolved dependencies
        :raise KeyError:
           if *component_spec* does not identify a component in this
           assembler's context
        :raise aglyph.AglyphError:
           if *component_spec* causes a circular dependency

        If *component_spec* is a string, it is assumed to be a unique
        component ID and is used as-is. Otherwise,
        :func:`aglyph.format_dotted_name` is called to convert
        *component_spec* into a dotted name string, which is assumed to
        be the component's unique ID.

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
           :attr:`aglyph.component.Component.unique_id`.

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
           :attr:`aglyph.component.Component.unique_id`.

           .. note::
              Assembly of borg components is a thread-safe operation.

           .. warning::
              The borg assembly strategy is **only** supported for
              components whose objects have an instance ``__dict__``.

              This means that components using builtin classes, or
              components using classes that define or inherit a
              ``__slots__`` member, **cannot** be declated as borg
              components.

        .. versionadded:: 2.1.0
           support for the "weakref" assembly strategy

        **"weakref"**
           In the simplest terms, this is a "prototype" that can exhibit
           "singleton" behavior: as long as there is at least one "live"
           reference to the assembled object in the application runtime,
           then requests to assemble this component will return the same
           (cached) object.

           When the only reference to the assembled object that remains
           is the cached (weak) reference, the Python garbage collector
           is free to destroy the object, at which point it is
           automatically removed from the Aglyph cache.
           Subsequent requests to assemble the same component will cause
           a new object to be created, initialized, wired, cached (as a
           weak reference), and returned.

           .. note::
              Please refer to the :mod:`weakref` module for a detailed
              explanation of weak reference behavior.

        .. versionadded:: 2.0.0
           **Either** :attr:`aglyph.component.Component.factory_name`
           **or** :attr:`aglyph.component.Component.member_name` may be
           defined to exercise more control over how a component object
           is created and initialized. Refer to the linked documentation
           for details.

        .. note::
           This method is called recursively to assemble any dependency
           of *component_spec* that is defined as a
           :class:`aglyph.component.Reference`.

        """
        component_id = _identify(component_spec)
        component = self._context.get_component(component_id)
        if component is None:
            raise KeyError(
                "component %r is not defined in %s" %
                    (component_id, self._context))
        # issues/3: check for circular dependency
        if not hasattr(_assembly, "component_stack"):
            _assembly.component_stack = []
        if (component_id in _assembly.component_stack):
            raise AglyphError(
                "circular dependency detected: %s" %
                    " > ".join(_assembly.component_stack + [component_id]))
        _assembly.component_stack.append(component_id)
        self.__log.debug(
            "current assembly stack: %r", _assembly.component_stack)
        try:
            obj = self._create(component)
            self.__log.info("assembled %r", component_id)
            return obj
        finally:
            _assembly.component_stack.pop()

    def _create(self, component):
        """Create an object of *component*.

        :arg aglyph.component.Component component:
           a component definition
        :return:
           an initialized object
        :raise AglyphError:
           if *component* uses an unrecognized assembly strategy

        This method delegates to the appropriate
        ``_create_\<strategy\>`` method for *component*.

        """
        # allow AttributeError; there is sufficient checking in Component for
        # unrecognized strategy, and getting here with one takes quite a bit of
        # effort (see test_Assembler.test_cant_create_unrecognized_strategy)
        create = getattr(self, "_create_%s" % component.strategy)
        return create(component)

    def _create_prototype(self, component):
        """Create and initialize a prototype object for *component*.

        :arg aglyph.component.Component component:
           a component definition having strategy="prototype"
        :return:
           an initialized prototype object

        A new object is always created and initialized when a
        "prototype" component is assembled.

        This is the default assembly strategy for Aglyph components.

        """
        obj = self._initialize(component)
        self._wire(obj, component)
        self._call_lifecycle_method("after_inject", obj, component.unique_id)
        self.__log.info("created %r", component)
        return obj

    # issues/5: support "_imported" strategy when using member_name
    # (objects of these components are created like prototypes though they
    # exhibit singleton behavior as long as the containing module is
    # referenced in sys.modules)
    _create__imported = _create_prototype

    def _create_singleton(self, component):
        """Return the singleton object for *component*.

        :arg aglyph.component.Component component:
           a component definition having strategy="singleton"
        :return:
           the singleton object with all its dependencies resolved

        If *component* has previously been assembled, the cached object
        is returned. Otherwise, a new object is created, initialized,
        wired, cached, and then returned.

        .. note::
           Assembly of singleton components is a thread-safe operation.

        """
        with self._caches["singleton"] as cache:
            obj = cache.get(component.unique_id)
            if obj is None:
                # singletons are initialized and wired once, then cached
                obj = self._initialize(component)
                self._wire(obj, component)
                self._call_lifecycle_method(
                    "after_inject", obj, component.unique_id)
                cache[component.unique_id] = obj
                self.__log.info(
                    "created and cached %r @ %x", component, id(obj))
            else:
                self.__log.info(
                    "retrieved %r @ %x from cache", component, id(obj))
        return obj

    def _create_borg(self, component):
        """Create and initialize a borg object for *component*.

        :arg aglyph.component.Component component:
           a component definition having strategy="borg"
        :return:
           the borg instance with all its dependencies resolved

        A new instance is always created. If *component* has been
        previously assembled, the cached shared-state is assigned to the
        new instance's ``__dict__`` and the instance is returned.
        Otherwise, the new instance is initialized and wired, its
        ``__dict__`` is cached, and then the instance is returned.

        .. note::
           Assembly of borg components is a thread-safe operation.

        .. warning::
           The borg assembly strategy is **only** supported for
           components whose objects have an instance ``__dict__``.

           This means that components using builtin classes, or
           components using classes that define or inherit a
           ``__slots__`` member, **cannot** be declated as borg
           components.

        """
        with self._caches["borg"] as cache:
            cached_obj = cache.get(component.unique_id)
            if cached_obj is None:
                # borgs are initialized and wired, then the state is cached
                # (an object of the borg is actually cached, but this is just
                # an implementation detail... it's just as effective a
                # container as anything else, and it makes the implementation
                # of clear_borgs() far less expensive - if we only cached the
                # new_obj.__dict__, we'd need to actually assemble each borg in
                # clear_borgs() in order to call any before_clear lifecycle
                # methods)
                new_obj = self._initialize(component)
                self._wire(new_obj, component)
                self._call_lifecycle_method(
                    "after_inject", new_obj, component.unique_id)
                cache[component.unique_id] = new_obj
                self.__log.info(
                    "created and cached shared-state for %r", component)
            else:
                self.__log.info(
                    "retrieved shared-state for %r from cache", component)
                cls = self._resolve_initializer(component)
                new_obj = (
                    new_instance(cls) if (component.member_name is None)
                    else cls)
                new_obj.__dict__ = cached_obj.__dict__
        return new_obj

    def _create_weakref(self, component):
        """Return a weakref object for *component*.

        :arg aglyph.component.Component component:
           a component definition having strategy="weakref"
        :return:
           the weakref object with all its dependencies resolved

        .. note::
           The object returned by this method and, therefore, by
           :meth:`assemble` is the **referent** (i.e. the object which
           is referred to *by* the weak reference).

        If *component* has previously been assembled **and** the
        internally-cached weak reference is still live, then the cached
        referent object is returned. Otherwise, a new object is created,
        initialized, wired, cached as a weak reference, and then
        returned.

        .. warning::
           While assembly of weakref components is a thread-safe
           operation with respect to *explicit* modification of the
           weakref cache (i.e. any other thread attempting to assemble
           a weakref component or to :meth:`clear_weakrefs` will be
           blocked until this method returns), the nature of weak
           references means that entries may still "disappear" from
           the cache *even while the cache lock is held.*

           With respect to assembly, this means that a referent
           component object may "disappear" (i.e. the weak reference
           goes dead) even *after* the cache lock has been acquired
           and the weak reference retrieved from the cache. Practically
           speaking, this should be of no concern to callers, since
           a valid object of the component will be returned either way.

        Please refer to the :mod:`weakref` module for a detailed
        explanation of weak reference behavior.

        """
        with self._caches["weakref"] as cache:
            ref = cache.get(component.unique_id)
            if ref is not None:
                obj = ref()
                if obj is None:
                    # referent is dead; discard the cache entry
                    self.__log.debug(
                        "cached weak reference to object of %r is dead; "
                            "new object will be created",
                        component)
                    cache.pop(component.unique_id)
            else:
                obj = None

            if obj is None:
                # an object is initialized and wired whenever a weak reference
                # to the abject does not exist or is dead; then a weak
                # reference to the object is cached and the object (i.e. the
                # referent) is returned
                obj = self._initialize(component)
                self._wire(obj, component)
                self._call_lifecycle_method(
                    "after_inject", obj, component.unique_id)
                cache[component.unique_id] = weakref.ref(obj)
                self.__log.info(
                    "created and cached weak reference to %r @ %x",
                    component, id(obj))
            else:
                self.__log.info(
                    "retrieved %r @ %x from cached weak reference",
                    component, id(obj))

        return obj

    def _initialize(self, component):
        """Create a new *component* object initialized with its
        dependencies.

        :arg aglyph.component.Component component:
           a component definition
        :return:
           an initialized object of *component*

        This method performs **type 3 (constructor)** dependency
        injection.

        .. versionchanged:: 2.1.0
           If *component* specifies a :attr:`Component.member_name`
           **and** either :attr:`Component.args`
           or :attr:`Component.keywords`, then a :class:`RuntimeWarning`
           is issued.

        """
        initializer = self._resolve_initializer(component)
        if component.member_name is None:
            (args, keywords) = self._resolve_args_and_keywords(component)
            try:
                # issues/2: always use the __call__ protocol to initialize
                obj = initializer(*args, **keywords)
            except Exception as e:
                raise AglyphError(
                    "failed to initialize object of component %r" %
                        component.unique_id,
                    e)
        else:
            obj = initializer
            if component.args or component.keywords:
                msg = (
                    "ignoring args and keywords for component %r "
                    "(uses member_name assembly)")
                self.__log.warning(msg, component.unique_id)
                warnings.warn(msg % component.unique_id, RuntimeWarning)
        return obj

    def _resolve_initializer(self, component):
        """Return the object that is responsible for creating new
        *component* objects.

        :arg aglyph.component.Component component:
           a component definition
        :return:
           a callable if *component.member_name* is undefined, else the
           member itself (which may or may not be a callable)

        .. note::
           If *component.member_name* is defined, the returned object
           may still be callable (for example, *component.member_name*
           may name a class). However, Aglyph will not **call** the
           member.
           This allows injection of dependencies that are references to
           callable objects like classes and functions.

        """
        initializer = resolve_dotted_name(component.dotted_name)
        access_name = component.factory_name or component.member_name
        if access_name:
            for name in access_name.split('.'):
                initializer = getattr(initializer, name) # allow AttributeError
        return initializer

    def _resolve_args_and_keywords(self, component):
        """Assemble or evaluate all positional and keyword arguments
        for *component*.

        :arg aglyph.component.Component component:
           a component definition
        :return:
           the fully-resolved (i.e. recursively assembled or evaluated)
           positional and keyword arguments for the *component*
           initializer
        :rtype:
           a 2-tuple ``(args, keywords)`` where ``args`` is an N-tuple
           and ``keywords`` is a :obj:`dict`

        The values returned from this method are ready to be passed
        directly to the *component* initializer (see :meth:`_initialize`
        and :meth:`_resolve_initializer`).

        .. versionchanged:: 2.1.0
           The returned 2-tuple ``(args, keywords)`` accounts for the
           *component* parent (and parent-of-parent, etc.) arguments and
           keywords.

           For any given component, this method will always return the
           "official" arguments and keywords that should be passed to
           the initializer.

        """
        resolve = self._resolve_value
        args = tuple([resolve(arg) for arg in self._collect_args(component)])
        collected_keywords = self._collect_keywords(component)
        keywords = dict(
            [(name, resolve(value))
            for (name, value) in collected_keywords.items()])
        return (args, keywords)

    def _collect_args(self, component):
        """Return the positional arguments used to initialize objects of
        *component*.

        :arg :class:`aglyph.component.Component` component:
            the component being initialized
        :return:
           the positional arguments for the *component* initializer,
           taking into account any positional arguments described by
           parent components/templates
        :rtype:
           :obj:`list`

        """
        collected_args = component.args
        parent = self._context.get(component.parent_id)
        while parent is not None:
            if parent.args:
                # children extend parents (like partial functions)
                collected_args = parent.args + collected_args
            parent = self._context.get(parent.parent_id)
        return collected_args

    def _collect_keywords(self, component):
        """Return the keyword arguments used to initialize objects of
        *component*.

        :arg aglyph.component.Component component:
           the component being initialized
        :return:
           the keyword arguments for the *component* initializer, taking
           into account any keyword arguments described by parent
           components/templates
        :rtype:
           :obj:`dict`

        """
        collected_keywords = component.keywords
        parent = self._context.get(component.parent_id)
        while parent is not None:
            if parent.keywords:
                parent_keywords = dict(parent.keywords)
                # children extend/override parents (like partial functions)
                parent_keywords.update(collected_keywords)
                collected_keywords = parent_keywords
            parent = self._context.get(parent.parent_id)
        return collected_keywords

    def _wire(self, obj, component):
        """Inject dependencies into *obj* using direct attribute
        assignment, setter methods, and/or properties.

        :param obj:
           an initialized object for *component*
        :param aglyph.component.Component component:
           a component definition

        This method performs **type 2 (setter)** dependency injection.

        .. versionchanged:: 2.1.0
           This method accounts for any attributes defined in the
           *component* parent (and parent-of-parent, etc.).

        """
        resolve = self._resolve_value
        collected_attributes = self._collect_attributes(component)
        for (attr_name, raw_attr_value) in collected_attributes.items():
            # prevent AttributeError - if attr_name names a slot that has not
            # been initialized, we want obj_attr to fail the callable test so
            # that setattr initializes the slot value
            obj_attr = getattr(obj, attr_name, None)
            attr_value = resolve(raw_attr_value)
            if callable(obj_attr):
                # this is a setter method
                obj_attr(attr_value)
            else:
                # this is a simple attribute or property
                setattr(obj, attr_name, attr_value)

    def _collect_attributes(self, component):
        """Return the attributes used to wire objects of *component*.

        :arg aglyph.component.Component component:
           the component definition for the object being wired
        :return:
           the (ordered) attributes for wiring an object of *component*,
           taking into account any attributes described by parent
           components/templates
        :rtype:
           :class:`collections.OrderedDict`

        """
        collected_items = list(component.attributes.items())
        parent = self._context.get(component.parent_id)
        while parent is not None:
            if parent.attributes:
                parent_items = list(parent.attributes.items())
                # children extend/override parents (like partial functions)
                collected_items = parent_items + collected_items
            parent = self._context.get(parent.parent_id)
        return OrderedDict(collected_items)

    def _resolve_value(self, value_spec):
        """Assemble or evaluate the runtime value of an initialization
        or attribute value specification.

        :arg value_spec:
           the value specified for a component initialization argument
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
        #PYVER: Python 2.7 type(value_spec) would just give <type 'instance'>
        if isinstance(value_spec, Reference):
            return self.assemble(value_spec)
        elif isinstance(value_spec, Evaluator):
            # need to pass a reference to the assembler since the
            # evaluation may require further component assembly
            return value_spec(self)
        elif isinstance(value_spec, partial):
            return value_spec()
        else:
            return value_spec

    def _call_lifecycle_method(self, lifecycle_state, obj, component_id):
        """Determine which *obj* lifecycle method to call, and call it.

        :arg str lifecycle_state:
           a lifecycle state identifier recognized by Aglyph
        :arg obj:
           the object on which to call the lifecycle method
        :arg str component_id:
           the component unique ID for *obj*

        """
        component = self._context[component_id]

        lifecycle_method_names = self._get_lifecycle_method_names(
            lifecycle_state, component)

        if lifecycle_method_names:
            self.__log.debug(
                "considering %s method names %r for %r %s",
                lifecycle_state, lifecycle_method_names, component_id, obj)

            # now call the first lifecycle method that is defined for obj
            for method_name in lifecycle_method_names:
                obj_lifecycle_method = getattr(obj, method_name, None)
                if obj_lifecycle_method is not None:
                    # issues/5: if the component specifies member_name, it is
                    # possible that an after_inject method could be called
                    # multiple times on the same object
                    if component.member_name:
                        msg = (
                            "component %r specifies member_name; it is "
                                "possible that the %s %s.%s() method may be "
                                "called MULTIPLE times on %r")
                        self.__log.warning(
                            msg, component_id, lifecycle_state,
                            component.member_name, method_name, obj)
                        warnings.warn(
                            msg % (
                                component_id, lifecycle_state,
                                component.member_name, method_name, obj),
                            RuntimeWarning)

                    try:
                        obj_lifecycle_method()
                    except Exception as e:
                        msg = "ignoring %s raised from %r"
                        self.__log.exception(
                            msg, e.__class__.__name__, obj_lifecycle_method)
                        warnings.warn(
                            msg % (e.__class__.__name__, obj_lifecycle_method),
                            RuntimeWarning)
                    else:
                        self.__log.info(
                            "called %s %r on %r %s",
                            lifecycle_state, obj_lifecycle_method,
                            component_id, obj)
                    finally:
                        # whether or not it raised an exception, the
                        # lifecycle state method has now been called
                        break
                else:
                    # here, we've encountered a "preferred" lifecycle method
                    # name, but the object doesn't define it; while this may be
                    # expected/intended by the developer, it also may suggest
                    # that there is a better way to configure the context, so
                    # at least log a warning
                    self.__log.warning(
                        "%r %s does not define %s method %r",
                        component_id, obj, lifecycle_state, method_name)
        else:
            self.__log.info(
                "no %s lifecycle methods specified for %s %r",
                lifecycle_state, obj, component_id)

    def _get_lifecycle_method_names(self, lifecycle_state, component):
        """Determine the preferred-order list of all lifecycle method
        names that may be applicable for an object of *component*.

        :arg str lifecycle_state:
           a lifecycle state identifier recognized by Aglyph
        :arg aglyph.component.Component component:
           the component

        """
        lifecycle_method_names = []

        # 1. Component.<lifecycle_state>
        method_name = getattr(component, lifecycle_state)
        if method_name is not None:
            lifecycle_method_names.append(method_name)

        # (2) parent Template/Component.<lifecycle_state>
        parent = self._context.get(component.parent_id)
        while parent is not None:
            method_name = getattr(parent, lifecycle_state)
            if method_name is not None:
                lifecycle_method_names.append(method_name)

            # (3) parent-of-parent Template/Component.<lifecycle_state>
            parent = self._context.get(parent.parent_id)

        # (4) Context.<lifecycle_state>
        method_name = getattr(self._context, lifecycle_state)
        if method_name is not None:
            lifecycle_method_names.append(method_name)

        return lifecycle_method_names

    def init_singletons(self):
        """Assemble and cache all singleton component objects.

        .. versionadded: 2.1.0

        :return:
           the initialized singleton component IDs
        :rtype:
           :obj:`list`

        This method may be called at any time to "prime" the internal
        singleton cache. For example, to eagerly initialize all
        singleton components for your application::

           assembler = Assembler(my_context)
           assembler.init_singletons()

        .. note::
           Only singleton components that do not *already* have cached
           objects will be initialized by this method.

           Initialization of singleton component objects is a
           thread-safe operation.

        """
        return self._init_cache("singleton")

    def clear_singletons(self):
        """Evict all cached singleton component objects.

        :return:
           the evicted singleton component IDs
        :rtype:
           :obj:`list`

        Aglyph makes the following guarantees:

        #. All cached singleton objects' "before_clear" lifecycle
           methods are called (if specified) when they are evicted from
           cache.
        #. The singleton cache will be empty when this method
           terminates.

        .. note::
           Any exception raised by a "before_clear" lifecycle method is
           caught, logged, and issued as a :class:`RuntimeWarning`.

           Eviction of cached singleton component objects is a
           thread-safe operation.

        """
        return self._clear_cache("singleton")

    def init_borgs(self):
        """Assemble and cache the shared-states for all borg component
        objects.

        .. versionadded: 2.1.0

        :return:
           the initialized borg component IDs
        :rtype:
           :obj:`list`

        This method may be called at any time to "prime" the internal
        borg cache. For example, to eagerly initialize all borg
        component shared-states for your application::

           assembler = Assembler(my_context)
           assembler.init_borgs()

        .. note::
           Only borg components that do not *already* have cached
           shared-states will be initialized by this method.

           Initialization of borg component shared-states is a
           thread-safe operation.

        """
        return self._init_cache("borg")

    def clear_borgs(self):
        """Evict all cached borg component shared-states.

        :return:
           the evicted borg component IDs
        :rtype:
           :obj:`list`

        Aglyph makes the following guarantees:

        #. All cached borg shared-states' "before_clear" lifecycle
           methods are called (if specified) when they are evicted from
           cache.
        #. The borg cache will be empty when this method terminates.

        .. note::
           Any exception raised by a "before_clear" lifecycle method is
           caught, logged, and issued as a :class:`RuntimeWarning`.

           Eviction of cached borg component shared-states is a
           thread-safe operation.

        """
        return self._clear_cache("borg")

    def clear_weakrefs(self):
        """Evict all cached weakref component objects.

        :return:
           the evicted weakref component IDs
        :rtype:
           :obj:`list`

        Aglyph makes the following guarantees:

        #. **IF** a cached weakref object is still available **AND**
           the component definition specifies a "before_clear" lifecycle
           method, Aglyph will call that method when the object is
           evicted.
        #. The weakref cache will be empty when this method terminates.

        .. note::
           Any exception raised by a "before_clear" lifecycle method is
           caught, logged, and issued as a :class:`RuntimeWarning`.

           Eviction of cached weakref component objects is a thread-safe
           operation.

        .. warning::
           While eviction of weakref components is a thread-safe
           operation with respect to *explicit* modification of the
           weakref cache (i.e. any other thread attempting to
           :meth:`assemble` a weakref component or to
           ``clear_weakrefs()`` will be blocked until this method
           returns), the nature of weak references means that entries
           may still "disappear" from the cache *even while the cache
           lock is held.*

           With respect to cache-clearing, this means that referent
           component objects may no longer be available even *after* the
           cache lock has been acquired and the weakref component IDs
           (keys) are retrieved from the cache. Practically speaking,
           this means that callers must be aware of two things:

           #. Aglyph **cannot** guarantee that "before_clear" lifecycle
              methods are called on weakref component objects, because
              there is no guarantee that a cached weak references is
              "live." (This is the nature of weak references.)
           #. Aglyph will only return the component IDs of weakref
              component objects that were "live" at the moment they were
              cleared.

        Please refer to the :mod:`weakref` module for a detailed
        explanation of weak reference behavior.

        """
        with self._caches["weakref"] as cache:
            eligible_weakref_ids = list(cache.keys())
            cleared_weakref_ids = []
            try:
                for weakref_id in eligible_weakref_ids:
                    ref = cache.pop(weakref_id)
                    obj = ref()
                    if obj is not None:
                        self._call_lifecycle_method(
                            "before_clear", obj, weakref_id)
                        cleared_weakref_ids.append(weakref_id)
                        obj = None
                    else:
                        self.__log.info(
                            "weak reference to object of component %r is "
                                "already dead; any before_clear method "
                                "for this component will NOT be called",
                            weakref_id)
                    ref = None
            finally:
                cache.clear()
        return cleared_weakref_ids

    def _init_cache(self, strategy):
        """Prime the cache for *strategy* objects.

        :arg str strategy:
           "singleton" or "borg"

        .. note::
           The "weakref" strategy is not explicitly supported here
           because priming a weak reference cache is nonsensical.

        """
        with self._caches[strategy] as cache:
            component_ids = []
            for component in self._context.iter_components(strategy):
                if component.unique_id not in cache:
                    self.assemble(component.unique_id)
                    component_ids.append(component.unique_id)
        return component_ids

    def _clear_cache(self, strategy):
        """Evict all objects from the cache for *strategy* objects,
        calling the "before_clear" lifecycle method for each object.

        :arg str strategy:
           "singleton", "borg", or "weakref"

        """
        with self._caches[strategy] as cache:
            component_ids = list(cache.keys())
            try:
                for component_id in component_ids:
                    obj = cache.pop(component_id)
                    self._call_lifecycle_method(
                        "before_clear", obj, component_id)
                    obj = None
            finally:
                cache.clear()
        return component_ids

    def __contains__(self, component_spec):
        """Tell whether or not the component identified by
        *component_spec* is defined in this assembler's context.

        :arg component_spec:
           used to determine the dotted name or component unique ID
        :return:
           ``True`` if *component_spec* identifies a component that is
           defined in this assembler's context, else ``False``

        .. note::
           Any *component_spec* for which this method returns ``True``
           can be assembled by this assembler.

           Accordingly, this method will return ``False`` if
           *component_spec* actually identifies a
           :class:`aglyph.component.Template` defined in this
           assembler's context.

        """
        try:
            component_id = _identify(component_spec)
        except:
            return False
        else:
            return self._context.get_component(component_id) is not None

    def __str__(self):
        return "<%s @%08x %s>" % (
            name_of(self.__class__), id(self), self._context)

    def __repr__(self):
        return "%s.%s(%r)" % (
            self.__class__.__module__, name_of(self.__class__), self._context)


@traced
@logged
class _ReentrantMutexCache(dict):
    """A mapping that uses a reentrant lock object for synchronization.

    Atomic "check-then-act" operations can be performed by
    acquiring the cache lock, performing the check-then-act sequence,
    and finally releasing the cache lock.

    If the lock is held, any attempt to acquire it by a thread OTHER
    than the holding thread will block until the holding thread releases
    the lock. (A reentrant mutex permits the same thread to acquire the
    same lock more than once, allowing nested access to a shared
    resource by a single thread.)

    A ``_ReentrantMutexCache`` object acts as a `context manager
    <https://docs.python.org/3/library/stdtypes.html#typecontextmanager>`_
    using `the with statement
    <https://docs.python.org/3/reference/compound_stmts.html#with>`_::

        cache = _ReentrantMutexCache()
        ...
        with cache:
            # check-then-act

    """

    def __init__(self):
        #PYVER: arguments to super() are implicit under Python 3
        super(_ReentrantMutexCache, self).__init__()
        self.__lock = threading_.RLock()

    def __enter__(self):
        """Acquire the cache lock."""
        self.__lock.acquire()
        return self

    def __exit__(self, e_type, e_obj, tb):
        """Release the cache lock.

        :arg e_type:
           the exception class if an exception occurred while executing
           the body of the ``with`` statement, else ``None``
        :arg Exception e_value:
           the exception object if an exception occurred while executing
           the body of the ``with`` statement, else ``None``
        :arg tb:
           the traceback if an exception occurred while executing the
           body of the ``with`` statement, else ``None``

        .. note::
           If an exception occurred, it will be logged but allowed to
           propagate.

        """
        self.__lock.release()
        if e_obj is not None:
            self.__log.error(
                "exception occurred while cache lock was held: %s", e_obj)

    def __str__(self):
        return "<%s @%08x>" % (name_of(self.__class__), id(self))

    def __repr__(self):
        return "%s.%s()" % (
            self.__class__.__module__, name_of(self.__class__))

