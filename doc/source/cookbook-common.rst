======================
Common usage scenarios
======================

All examples are shown with XML configuration *and* programmatic configuration,
where appropriate.

* :ref:`simple-component`
* :ref:`builtin-components`
* :ref:`component-reference`
* :ref:`deferred-resolution`
* :ref:`after-inject-lifecycle-method`
* :ref:`before-clear-lifecycle-method`
* :ref:`avoid-circular-deps`

.. _simple-component:

Describe a simple component (a class or an unbound factory function)
====================================================================

The simplest and most common kind of component is one that describes a
module-level class or unbound factory function.

To demonstrate, we will describe a component for the Python standard library
:class:`http.client.HTTPConnection` class.

.. note::
   Although we are using the Python standard library
   :class:`http.client.HTTPConnection` class here, this example applies to
   **any** class or unbound function, whether defined as part of your
   application, the Python standard library, or a 3rd-party library.

Using declarative XML configuration
-----------------------------------

In the XML context document *"cookbook-context.xml"*::

   <?xml version="1.0" encoding="UTF-8" ?>
   <context id="cookbook-context">
       <component id="http.client.HTTPConnection">
           <init>
               <arg><str>www.ninthtest.net</str></arg>
               <arg><int>80</int>
               <arg keyword="timeout"><int>5</int></arg>
           </init>
       </component>
   </context>

To assemble and use this component:

>>> from aglyph.assembler import Assembler
>>> from aglyph.context import XMLContext
>>> assembler = Assembler(XMLContext("cookbook-context.xml"))
>>> conx = assembler.assemble("http.client.HTTPConnection")
>>> conx.request("GET", '/')
>>> response = conx.getresponse()
>>> print(response.status, response.reason)
200 OK

If we want to describe more than one component of the same class or function,
then we need to use something other than the dotted name as the component IDs
so that they are unique::

   <?xml version="1.0" encoding="UTF-8" ?>
   <context id="cookbook-context">
       <component id="ninthtest-net-conx" dotted-name="http.client.HTTPConnection">
           <init>
               <arg><str>www.ninthtest.net</str></arg>
               <arg><int>80</int>
               <arg keyword="timeout"><int>5</int></arg>
           </init>
       </component>
       <component id="python-org-conx" dotted-name="http.client.HTTPConnection">
           <init>
               <arg><str>www.python.org</str></arg>
               <arg><int>80</int>
               <arg keyword="timeout"><int>5</int></arg>
           </init>
       </component>
   </context>

Accordingly, we use the component IDs to assemble these components:

>>> from aglyph.assembler import Assembler
>>> from aglyph.context import XMLContext
>>> assembler = Assembler(XMLContext("cookbook-context.xml"))
>>> ninthtest_net = assembler.assemble("ninthtest-net-conx")
>>> python_org = assembler.assemble("python-org-conx")

Using programmatic Binder configuration
---------------------------------------

Using :class:`aglyph.binder.Binder` to describe a simple component in a
*bindings.py* module::

   from http.client import HTTPConnection
   from aglyph.binder import Binder

   binder = Binder("cookbook-binder")
   binder.bind(HTTPConnection).init("www.ninthtest.net", 80, timeout=5)

To assemble and use the component:

>>> from bindings import binder
>>> conx = binder.lookup("http.client.HTTPConnection")
>>> conx.request("GET", '/')
>>> response = conx.getresponse()
>>> print(response.status, response.reason)
200 OK

And like XML contexts, when we wish to use multiple components of the same
dotted name, we must give them unique component IDs::

   from http.client import HTTPConnection
   from aglyph.binder import Binder
   
   binder = Binder("cookbook-binder")
   (binder.bind("ninthtest-net-conx", to=HTTPConnection).
       init("www.ninthtest.net", 80, timeout=5))
   (binder.bind("python-org-conx", to=HTTPConnection).
       init("www.python.org", 80, timeout=5))

Assembling these components now requires the custom component IDs:

>>> from bindings import binder
>>> ninthtest_net = binder.lookup("ninthtest-net-conx")
>>> python_org = binder.lookup("python-org-conx")

.. _builtin-components:

Describe any Python builtin type as a component
===============================================

Python builtin types (e.g. :obj:`int`, :obj:`list`) can be identified by an
importable dotted name, and so may specified as components in Aglyph.

Using declarative XML configuration
-----------------------------------

.. warning::
   The name of the module in which builtin types are defined differs between
   Python 2 and 3, so any Aglyph XML configuration that uses this approach
   will, by definition, **not** be compatible across Python versions.

   The example given below uses the Python 3 :mod:`builtins` module. To make
   this example work on Python 2, the ``__builtin__`` module would be used
   instead.

In the XML context document *"cookbook-context.xml"*::

   <?xml version="1.0" encoding="UTF-8" ?>
   <context id="cookbook-context">
       <component id="foods" dotted-name="builtins.frozenset">
           <init>
               <arg>
                   <list>
                       <str>spam</str>
                       <str>eggs</str>
                   </list>
               </arg>
           </init>
       </component>
       <component id="opened-file" dotted-name="builtins.open">
           <init>
               <arg><str>/path/to/file.txt</str></arg>
               <arg keyword="encoding"><str>ISO-8859-1</str></arg>
           </init>
       </component>
   </context>

Using programmatic Binder configuration
---------------------------------------

Because the builtin types are accessible without having to do an explicit
import, the Binder configuration is very simple.

In a *bindings.py* module::

   from aglyph.binder import Binder
   
   binder = Binder("cookbook-binder")
   binder.bind("foods", to=frozenset).init(["spam", "eggs"])
   (binder.bind("opened-file", to=open).
       init("/path/to/file.txt", encoding="ISO-8859-1"))

.. _component-reference:

Use a reference to another component as a dependency
====================================================

An :class:`aglyph.component.Reference` is a powerful mechanism for creating
cross-references between components.

A ``Reference`` value is just a component ID, but a ``Reference`` triggers
special behavior within an :class:`aglyph.assembler.Assembler` or
:class:`aglyph.component.Evaluator` when it is encountered during assembly or
evaluation (respectively): wherever the ``Reference`` appears, it will be
automatically replaced with the fully-assembled component it identifies.

A ``Reference`` may be used in *any* of the following places, allowing for
extremely flexible configurations:

* an initialization argument value (positional or keyword) for an
  :class:`aglyph.component.Component` or an :class:`aglyph.component.Evaluator`
* an attribute value for an :class:`aglyph.component.Component`
* a key and/or value of a :obj:`dict`
* an item of any sequence type (e.g. :obj:`list`, :obj:`tuple`)

In a nutshell: an :class:`aglyph.component.Reference` may be used in *any*
case where a value is being defined, and will be replaced at assembly-time by
the fully-assembled component identified by that reference.

To demonstrate, we will describe components for the Python standard library
:class:`urllib.request.Request` class and :func:`urllib.request.urlopen`
function. (The former will be referenced as a dependency for the latter.)

Using declarative XML configuration
-----------------------------------

In the *"cookbook-context.xml"* document::

   <?xml version="1.0" encoding="UTF-8" ?>
   <context id="cookbook-context">
       <component id="ninthtest-home-page" dotted-name="urllib.request.Request">
           <init>
               <arg><str>http://www.ninthtest.net/</str></arg>
           </init>
       </component>
       <component id="ninthtest-url" dotted-name="urllib.request.urlopen">
           <init>
               <arg reference="ninthtest-home-page" />
               <arg keyword="timeout"><int>5</int></arg>
           </init>
       </component>
   </context>

When the *"ninthtest-url"* component is assembled, the assembler will
automatically assemble and inject the *"ninthtest-home-page"* component:

>>> from aglyph.assembler import Assembler
>>> from aglyph.context import XMLContext
>>> assembler = Assembler(XMLContext("cookbook-context.xml"))
>>> ninthtest_url = assembler.assemble("ninthtest-url")
>>> print(ninthtest_url.status, ninthtest_url.reason)
200 OK

Using programmatic Binder configuration
---------------------------------------

In a *bindings.py* module::

   from urllib.request import Request, urlopen
   from aglyph.binder import Binder
   from aglyph.component import Reference
   
   binder = Binder("cookbook-binder")
   (binder.bind("ninthtest-home-page", to=Request).
       init("http://www.ninthtest.net/"))
   (binder.bind("ninthtest-url", to=urlopen).
       init(Reference("ninthtest-home-page"), timeout=5))

When the *"ninthtest-url"* component is assembled, the binder will
automatically assemble and inject the *"ninthtest-home-page"* component:

>>> from bindings import binder
>>> ninthtest_url = binder.lookup("ninthtest-url")
>>> print(ninthtest_url.status, ninthtest_url.reason)
200 OK

.. _deferred-resolution:

Defer the resolution of injection values until assembly time
============================================================

When specifying the values that should be injected into an object of a
component as it is assembled, it is sometimes desired (or necessary) that
those values be resolved **at the time the component is being assembled.**

The textbook example of such a case is a component that accepts some mutable
sequence type (e.g. a :obj:`list`) as an injection value. If the value (the
list) were resolved at the time the component is being defined, then all
objects of that component would share a reference to the same list This means
that changes to the list belonging to *any* instance will actually apply to
*all* instances.

In almost all cases, this is not desired behavior. What we actually desire is
for each instance of the component to have its *own* copy of the list.

The solution to this problem is to specify a dependency such that its actual
value is determined on-the-fly when the component is being assembled. Aglyph
supports several ways of accomplishing this.

.. _deferred-reference:

Use a Reference to defer the assembly of a component
----------------------------------------------------

Whenever an :class:`aglyph.component.Reference` is used to identify a component
as a dependency, that component is not assembled until the *parent* component
is assembled.

Using declarative XML configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Aglyph automatically creates an :class:`aglyph.component.Reference` for any
``<reference>`` element encountered, or for any ``<arg>``, ``<attribute>``,
``<key>``, or ``<value>`` element that specifies a ``reference`` attribute::

   <?xml version="1.0" encoding="UTF-8" ?>
   <context id="cookbook-context">
       <component id="cookbook-formatter" dotted-name="logging.Formatter">
           <init>
               <arg><str>%(asctime)s %(levelname)s %(message)s</str></arg>
           </init>
       </component>
       <component id="cookbook-handler" dotted-name="logging.handlers.RotatingFileHandler">
           <init>
               <arg><str>/var/log/cookbook.log</str></arg>
               <arg keyword="maxBytes"><int>1048576</int></arg>
               <arg keyword="backupCount"><int>3</int></arg>
           </init>
           <attributes>
               <attribute name="setFormatter">
                   <reference id="cookbook-formatter" />
               </attribute>
           </attributes>
       </component>
       <component id="cookbook-logger" dotted-name="logging.getLogger" strategy="singleton">
           <init>
               <arg><str>cookbook</str></arg>
           </init>
           <attributes>
               <attribute name="addHandler" ref="cookbook-handler" />
           </attributes>
       </component>
   </context>

Using programmatic Binder configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In a *bindings.py* module::

   from aglyph.binder import Binder
   from aglyph.component import Reference

   binder = Binder("cookbook-binder")
   (binder.bind("cookbook-formatter", to="logging.Formatter").
       init("%(asctime)s %(levelname)s %(message)s"))
   (binder.bind("cookbook-handler", to="logging.handlers.RotatingFileHandler").
       init("/var/log/cookbook.log", maxBytes=1048576, backupCount=3).
       attributes(setFormatter=Reference("cookbook-formatter")))
   (binder.bind("cookbook-logger", to="logging.getLogger", strategy="singleton").
       init("cookbook").
       attributes(addHandler=Reference("cookbook-handler")))

.. _deferred-partial-evaluator:

Use a partial function or an Evaluator to defer the evaluation of a runtime value
---------------------------------------------------------------------------------

Though almost all scenarios can be addressed by using components and
References, in some cases you may prefer that a dependency is *not* defined as
another component. In Aglyph, you can defer the evaluation of such a value
until component assembly time by using either a :obj:`functools.partial` object
or an :class:`aglyph.component.Evaluator`.

A partial function and an Evaluator serve the same purpose, and share the same
signature - *(func, \*args, \*\*keywords)* - but an Evaluator is capable of
recognizing and assembling any :class:`aglyph.component.Reference` that appears
in *args* or *keywords*, while a partial function is not.

.. note::
   When the arguments and/or keywords to a callable must specify an
   :class:`aglyph.component.Reference`, use
   :class:`aglyph.component.Evaluator`. Otherwise, use either
   :obj:`functools.partial` *or* an Evaluator.

Using declarative XML configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When using XML configuration, an :class:`aglyph.component.Evaluator` is
*automatically* created for any ``<list>``, ``<tuple>``, or ``<dict>``.

There is no support for explicitly specifying either a :obj:`functools.partial`
or an :class:`aglyph.component.Evaluator`. There is nothing *preventing* you
from declaring a component of :obj:`functools.partial` or
:class:`aglyph.component.Evaluator`, though the usefulness of the latter is
questionable (and would very strongly suggest that a simpler configuration
is possible).

In the following *"cookbook-context.xml"* document, the "states" keyword
argument is automatically turned into an :class:`aglyph.component.Evaluator`::

   <?xml version="1.0" ?>
   <context id="cookbook-context">
       <component id="cookbook.WorkflowManager">
           <init>
               <arg keyword="states">
                   <dict>
                       <item>
                           <key><str>UNA</str></key>
                           <value><str>Unassigned</str></value>
                       </item>
                       <item>
                           <key><str>OPE</str></key>
                           <value><str>Open (Assigned)</str></value>
                       </item>
                       <item>
                           <key><str>CLO</str></key>
                           <value><str>Closed</str></value>
                       </item>
                   </dict>
               </arg>
           </init>
       </component>
   </context>

Using programmatic Binder configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. warning::
   Unlike XML configuration, there is no provision for automatically creating
   an :class:`aglyph.component.Evaluator` when using Binder. Any value that
   should be the result of a :obj:`functools.partial` or an
   :class:`aglyph.component.Evaluator` must be **explicitly** specified as
   such.

In a *bindings.py* module::

   import functools
   from aglyph.binder import Binder

   binder = Binder("cookbook-binder")
   (binder.bind("cookbook.WorkflowManager").
       init(states=functools.partial(dict,
                                     UNA="Unassigned",
                                     OPE="Open (Assigned)",
                                     CLO="Closed")))

.. _after-inject-lifecycle-method:

Declare a method to be called on an object after its dependencies have been injected
====================================================================================

.. versionadded:: 2.1.0

At times it may be desirable (or necessary) to call an "initialization" method
on an assembled object before it is returned to the caller for use. For this
purpose, Aglyph allows you to declare such a method name at the context,
template, and/or component level.

.. note::
   Please refer to :ref:`The lifecycle method lookup process
   <lifecycle-method-lookup-process>` to understand how Aglyph determines
   *which* lifecycle method to call on an object when multiple options are
   declared at the context, template, and/or component level for a given
   object.

In the following examples, we assume that all of the objects implement a
``prepare()`` method. In such cases, a context-level ``after_inject`` lifecycle
method may be appropriate. Alternatively, it could be declared in a template
(see :doc:`cookbook-templating`).

Regardless of the configuration approach, the behavior is that the assembled
object's ``prepare()`` method is called **before** the object is returned from
the assembler or binder to the caller.

Using declarative XML configuration
-----------------------------------

Note the use of the *after-inject* attribute on the ``<context>`` element::

   <?xml version="1.0" ?>
   <context id="cookbook-context" after-inject="prepare">
      <component id="object-a" dotted-name="cookbook.PreparableObjectA" />
      <component id="object-b" dotted-name="cookbook.PreparableObjectB" />
      <component id="object-c" dotted-name="cookbook.PreparableObjectC" />
   </context>

Using programmatic Binder configuration
---------------------------------------

Note the use of the *after_inject* keyword argument to
:class:`aglyph.binder.Binder`::

   from aglyph.binder import Binder

   binder = Binder("cookbook-binder", after_inject="prepare")
   binder.bind("object-a", to="cookbook.PreparableObjectA")
   binder.bind("object-b", to="cookbook.PreparableObjectB")
   binder.bind("object-c", to="cookbook.PreparableObjectC")

.. _before-clear-lifecycle-method:

Declare a method to be called on a *singleton*, *borg*, or *weakref* object before it is cleared from cache
===========================================================================================================

.. versionadded:: 2.1.0

At times it may be desirable (or necessary) to call a "finalization" method on
a cached object before it is cleared from Aglyph's internal cache. For this
purpose, Aglyph allows you to declare such a method name at the context,
template, and/or component level.

.. note::
   Please refer to :ref:`The lifecycle method lookup process
   <lifecycle-method-lookup-process>` to understand how Aglyph determines
   *which* lifecycle method to call on an object when multiple options are
   declared at the context, template, and/or component level for a given
   object.

Following is an example that declares a *singleton* `GNU dbm
<http://www.gnu.org.ua/software/gdbm/>`_ key/data store using Python's
:mod:`dbm.gnu` module. The store is configured to be opened in "fast" mode,
meaning that writes are not synchronized. When using GDBM, it is important that
every file opened is also closed (which causes any pending writes to be
synchronized - i.e. written to disk). The example shows how to declare that the
``close()`` method is to be called before the cached GDBM object is evicted
from the Aglyph singleton cache.

Using declarative XML configuration
-----------------------------------

Here we declare the ``close()`` method for the ``before_clear`` lifecycle state
of the component by using the *before-clear* attribute of the ``<component>``
element::

   <?xml version="1.0" ?>
   <context id="cookbook-context">
      <component id="store" dotted-name="dbm.gnu" factory-name="open"
            strategy="singleton" before-clear="close">
         <init>
            <arg><str>/var/cookbook-store.db</str></arg>
            <arg><str>cf</str></arg>
         </init>
      </component>
   </context>

Using programmatic Binder configuration
---------------------------------------

Here we use the *before_clear* keyword argument when binding the GDBM store
object::

   from aglyph.binder import Binder

   binder = Binder("cookbook-binder")
   (binder.bind("store", to="dbm.gnu", factory="open",
                strategy="singleton", before_clear="close").
       init("/var/cookbook-store.db", "cf"))

.. warning::
   Be careful when declaring ``before_clear`` lifecycle methods for *weakref*
   component objects, as the nature of weak references means that Aglyph
   **cannot** guarantee that the object still exists when the
   :meth:`aglyph.assembler.Assembler.clear_weakrefs` method is called! Please
   refer to :mod:`weakref` for details.

.. _avoid-circular-deps:

Avoid circular dependencies
===========================

Consider two components, **A** and **B**. If **B** is a dependency of **A**,
and **A** is also a dependency of **B**, then a circular dependency exists::

   <component id="cookbook.A">
       <init>
           <arg reference="cookbook.B"/>
       </init>
   </comonent>
   <component id="cookbook.B">
       <init>
           <arg reference="cookbook.A"/>
       </init>
   </comonent>

Aglyph will raise :class:`aglyph.AglyphError` when it detects a circular
reference during assembly.

.. note::
   In software design in general, circular dependencies are frowned upon
   because they can lead to problems ranging from increased maintenance costs
   to infinite recursion and memory leaks. The existence of a circular
   dependency usually implies that the design can be improved to avoid such a
   relationship.

