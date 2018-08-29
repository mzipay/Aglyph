=============================
The Aglyph Context fluent API
=============================

:Release: |release|

* :ref:`fluent-intro`

  * :ref:`fluent-note-component`

* :ref:`fluent-refs`
* :ref:`fluent-templates`
* :ref:`fluent-introspect`
* :ref:`fluent-api-methods`

.. _fluent-intro:

Introduction to the Context fluent API
======================================

The easiest way to configure Aglyph programmatically is to use the
"fluent" API exposed by ``aglyph.context.Context``.

The Context fluent API consists of a set of chained-call-style methods
(exposed on ``Context`` or its subclasses) that can be used to define
components of any kind (prototype, singleton, borg, weakref) as well
as templates.

There are six (6) "entry points" into the Context fluent API:

1. :meth:`aglyph.context.Context.prototype` to define a prototype component
2. :meth:`aglyph.context.Context.singleton` to define a singleton component
3. :meth:`aglyph.context.Context.borg` to define a borg component
4. :meth:`aglyph.context.Context.weakref` to define a weakref component
5. :meth:`aglyph.context.Context.template` to define a template
6. :meth:`aglyph.context.Context.component` to define any kind of component
   *(more on this method later)*

Each entry point returns a "builder" which can be used to further define the
component or template.

For the sake of demonstration, assume we begin with the following
initialization code::

   from aglyph.assembler import Assembler
   from aglyph.component import Reference as ref
   from aglyph.context import Context
   
   context = Context("example-context")

Let's define a singleton component::

   context.singleton("my-singleton")

Here we have provided a unique ID for the component ("my-singleton"). Since
this is not a dotted name, though, Aglyph doesn't know which class to use
to create the object. We will provide the class name with a chained call to
the ``create()`` method::

   context.singleton("my-singleton").create("module.ClassName")

We could also have used the dotted name as the unique ID, in which case
calling ``create()`` would not be necessary.

Now we wish to define the initialization arguments and keywords. We add
another chained call to the ``init()`` method to do so. We can also break
the chained call sequence onto multiple lines for readability::

   (context.singleton("my-singleton").
       create("module.ClassName").
       init("argument", keyword="keyword"))

Finally, we terminate the fluent sequence by calling the ``register()``
method, which actually creates an :class:`aglyph.component.Component` and
adds it to the context::

   (context.singleton("my-singleton").
       create("module.ClassName").
       init("argument", keyword="keyword").
       register())

.. note::
   Terminating the fluent builder with a call to ``register()`` is
   crucial. The component definition is not actually created or stored
   in the context unless/until this method is called!

Now this context can be given to an assembler, and we can create an object::

   assembler = Assembler(context)
   my_singleton = assembler.assemble("my-singleton")

You can find many other examples of using the Context fluent API in the
:doc:`cookbook`.

.. _fluent-note-component:

A note regarding the ``component()`` entry point method
-------------------------------------------------------

The strategy-specific entry point methods (``prototype()``, ``singleton()``,
``borg()`` and ``weakref()``) are implemented in terms of ``component()``.

For example, calling ``singleton("package.ClassName")`` is the shorthand
equivalent of calling
``component("package.ClassName").create(strategy="singleton")``.

If ``component("my-id")`` is used to define a component and no explicit
strategy is specified, then the default strategy ("prototype") is
assumed.

.. warning::
   There is one "special case" that warrants explanation:

   When specifying a *member* using the fluent API (i.e. objects of the
   component are "created" by attribute access on the object identified
   by a dotted name), then the creation strategy is implicitly set to
   "_imported" and SHOULD NOT be set explicitly. In short - consider
   *member* and *strategy* to be mutually exclusive.

.. _fluent-refs:

Using component references with the Context fluent API
======================================================

Let's add another component to the context. This new component needs to be
injected with an object of "my-singleton" via a property. We will use an
:class:`aglyph.component.Reference` to provide the dependency::

   (context.prototype("example-object").
       create("module2.ExampleObject").
       set(thing=ref("my-singleton")).
       register())

Assembling an object of "example-object" will resolve "my-singleton" to the
same object we assembled earlier, and will set that object as the
``module2.ExampleObject.thing`` property.

.. _fluent-templates:

Using the Context fluent API to define templates
================================================

Defining templates via the Context fluent API is identical to defining
components, with the exception that there is no ``create()`` method for
template builders. Remember, templates cannot be assembled - they serve
only as a basis for further defining other templates or components.

Here is an example::

   context.template("my-template").init("arg", keyword="kw").register()
   (context.singleton("my-singleton", parent="my-template").
       create("module.ClassName").
       register())

Notice that we have added ``parent="my-template"`` to the singleton method call.

Now when we assemble "my-singleton" its initializer will be called with
the positional argument "arg" and the keyword argument keyword="kw".

.. _fluent-introspect:

Letting Aglyph introspect dotted names
======================================

If preferred, classes (or other callables) that will be defined as
components or templates can be introspected by Aglyph. Let's revisit the
earlier example, slightly modified, to demonstrate this::

   from module import ClassName
   from module2 import ExampleObject

   from aglyph.assembler import Assembler
   from aglyph.component import Reference as ref
   from aglyph.context import Context
   
   context = Context("example-context")

   (context.singleton(ClassName).
       init("argument", keyword="keyword").
       register())

   (context.prototype("example-object").
       create(ExampleObject).
       set(thing=ref(ClassName)).
       register())

   assembler = Assembler(context)
   example = assembler.assemble("example-object")

Notice that we call ``singleton(ClassName)`` as the entry point. Aglyph
will automatically convert ClassName into its dotted name
"module.ClassName" and also use that value as the unique ID. This means
that the expicit call to ``create()`` is now unnecessary, and so it has
been removed.

Next, notice the call to ``create(ExampleObject)``. We used
"example-object" as the component ID, so we must still tell Aglyph the
dotted name of the class. But instead of passing the dotted name as a
string, we again pass the class and let Aglyph determine the value.

Finally, notice that we use ``ref(ClassName)`` when setting the *thing*
property. Like the fluent API entry point methods and ``create()``,
:class:`aglyph.component.Reference` is also capable of introspecting a
dotted name.

.. warning::
   Callable object dotted-name introspection for **nested** callables
   (e.g. nested classes) does not work in Python versions prior to 3.3
   because the introspection depends on the *Qualified name for classes
   and functions* (i.e. ``__qualname__``, specified in :pep:`3155`).

.. _fluent-api-methods:

Overview of the Context fluent API methods
==========================================

The Context fluent API is made up of a number of "mixin" classes that are
combined in different ways to support describing templates and components.

These classes are never instantiated directly; rather, the "entry point"
methods are exposed as members of :class:`aglyph.context.Context` that
return either a :class:`aglyph.context._ComponentBuilder` or a
:class:`aglyph.context._TemplateBuilder`; and those builder classes
inherit relevant methods from the mixin classes.

.. note::
   For reference, here is the class hierarchy for the Context fluent API
   (all classes are defined in the ``aglyph.context`` namespace):

   .. class:: Context(_ContextBuilder)

   .. class:: _TemplateBuilder(_InjectionBuilderMixin, _LifecycleBuilderMixin, _RegistrationMixin)

   .. class:: _ComponentBuilder(_CreationBuilderMixin, _TemplateBuilder)

"Entry point" methods to create component and template builders
---------------------------------------------------------------

.. automethod:: aglyph.context._ContextBuilder.component

.. automethod:: aglyph.context._ContextBuilder.prototype

.. automethod:: aglyph.context._ContextBuilder.singleton

.. automethod:: aglyph.context._ContextBuilder.borg

.. automethod:: aglyph.context._ContextBuilder.weakref

.. automethod:: aglyph.context._ContextBuilder.template

Describing object creation for component builders
-------------------------------------------------

.. automethod:: aglyph.context._CreationBuilderMixin.create

Describing dependencies and lifecycle methods for template and component builders
---------------------------------------------------------------------------------

.. automethod:: aglyph.context._InjectionBuilderMixin.init

.. automethod:: aglyph.context._InjectionBuilderMixin.set

.. automethod:: aglyph.context._LifecycleBuilderMixin.call

Registering the template or component described by a fluent builder
-------------------------------------------------------------------

.. automethod:: aglyph.context._RegistrationMixin.register

