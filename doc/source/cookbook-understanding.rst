=========================================
Understand the general features of Aglyph
=========================================

.. _version-impl-support:

Aglyph supports Python 2 and 3 (CPython), PyPy, Stackless, IronPython, and Jython
=================================================================================

The single Aglyph distribution and API is 100% compatible across Python
language versions 2.7 - 3.4 (excluding 3.0) and the implementations listed
below:

* `CPython <http://www.python.org/>`_
* `PyPy <http://pypy.org/>`_
* `Stackless Python <http://www.stackless.com/>`_
* `IronPython <http://ironpython.net/>`_
* `Jython <http://www.jython.org/>`_

The :doc:`testing` provides detailed information for the Python implementation
releases and platforms under which the Aglyph unit test suite is executed.

.. _no-aglyph-code-in-app-code:

Aglyph does not require framework-specific changes to your application code
===========================================================================

Adding Aglyph Dependency Injection support to a new *or existing* application
is easy, because Aglyph doesn't require any framework-specific code to reside
in your application's business logic code.

Conceptually, Aglyph acts like a layer or proxy that sits *between* your
business logic code and the scaffolding/controlling code that uses it. Put
another way: Aglyph knows about your application components, but your
application components don't know about Aglyph.

.. _any-object-is-a-component:

**Any** object (application-specific, Python standard library, or 3rd-party) can be an Aglyph component
=======================================================================================================

Because Aglyph doesn't require that component source code be modified, either
to be injected with dependencies or to serve *as* a dependency (or both!),
**any** object can serve as a component in your application.

Aglyph will happily assemble any object that is reachable from an absolute
importable dotted name and, optionally, attribute access on that object (via
:attr:`aglyph.component.Component.factory_name` or
:attr:`aglyph.component.Component.member_name`).

The only requirements for a component are that:

1. :attr:`aglyph.component.Component.component_id` must be unique within an
   :class:`aglyph.context.Context`.
2. :attr:`aglyph.component.Component.dotted_name` must be a "dotted_name.NAME"
   or "dotted_name" string that represents a valid absolute import statement
   according to the productions listed below.

.. productionlist::
   absolute_import_stmt: "from" dotted_name "import" NAME
                       : | "import" dotted_name
   dotted_name: NAME ('.' NAME)*

Whether you want to describe a component as an object from your own
application, from the Python standard library, from a 3rd-party library, or
even from an implementation-specific library  (e.g. a .NET class in IronPython,
a Java class in Jython), Aglyph is up to the task. No adapter code, no
monkey-patching, no fuss.

