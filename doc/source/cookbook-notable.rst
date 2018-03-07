=============================
Other notable usage scenarios
=============================

:Release: |release|

.. _Stackless Python: https://github.com/stackless-dev/stackless/wiki
.. _PyPy: http://pypy.org/
.. _stackless.tasklet: https://stackless.readthedocs.io/en/latest/library/stackless/tasklets.html
.. _Stackless Python "Tasklets": https://github.com/stackless-dev/stackless/wiki/Tasklets
.. _IronPython: http://ironpython.net/
.. _System.Xml.DtdProcessing: https://msdn.microsoft.com/en-us/library/system.xml.dtdprocessing.aspx
.. _System.Xml.ValidationType: https://msdn.microsoft.com/en-us/library/system.xml.validationtype.aspx
.. _System.Xml.XmlReaderSettings: https://msdn.microsoft.com/en-us/library/system.xml.xmlreadersettings.aspx
.. _System.Xml.XmlReader: https://msdn.microsoft.com/en-us/library/system.xml.xmlreader.aspx
.. _Jython: http://www.jython.org/
.. _java.util.Collections#synchronizedMap(java.util.Map): https://docs.oracle.com/javase/8/docs/api/java/util/Collections.html#synchronizedMap(java.util.Map
.. _java.util.LinkedHashMap: https://docs.oracle.com/javase/8/docs/api/java/util/LinkedHashMap.html
.. _Expat: https://libexpat.github.io/

* :ref:`staticmethod-classmethod-nestedclass-component`
* :ref:`member-component`
* :ref:`impl-specific-component`
* :ref:`custom-xmlcontext-parser`
* :ref:`clear-caches`

.. _staticmethod-classmethod-nestedclass-component:

Describe components for static methods, class methods, or nested classes
========================================================================

You may encounter cases where objects for which you want to describe components
are created through static methods (``@staticmethod``), class methods
(``@classmethod``), or nested classes.

Recall that an Aglyph component must have an *importable* dotted name.
Unfortunately, the dotted names for static methods, class methods, and nested
classes are **not** importable.

Aglyph components support an optional
:attr:`aglyph.component.Component.factory_name` property to address these
cases. The ``factory_name`` is itself a dotted name, but it is *relative to*
:attr:`aglyph.component.Component.dotted_name`.

The following sample *delorean.py* module helps to illustrate the concepts, and
will be used in the code examples below::

   class EquipmentFoundry:

       class FluxCapacitor:

           @classmethod
           def with_capacitor_drive(capacitor_drive):
               """Return a fully-operational FluxCapacitor."""

       @staticmethod
       def get_default_capacitor_drive():
           """Return an experimental CapacitorDrive."""

The objects which we wish to describe as components (``FluxCapacitor`` and
``CapacitorDrive``), are created by callables having dotted names that are
**not importable**:

1. The class named ``delorean.EquipmentFoundry.FluxCapacitor``.
2. The class method named
   ``delorean.EquipmentFoundry.FluxCapacitor.with_capacitor_drive``.
3. The static method named
   ``delorean.EquipmentFoundry.get_default_capacitor_drive``.

However, we can use either of the dotted names that *are* importable (the
module named ``delorean`` and the class named ``delorean.EquipmentFoundry``) to
define our components, and specify *relative* dotted names as
:attr:`aglyph.component.Component.factory_name` values to enable Aglyph to
assemble ``FluxCapacitor`` and ``CapacitorDrive`` as components.

Using declarative XML configuration
-----------------------------------

In a *delorean-context.xml* document::

   <?xml version="1.0" encoding="UTF-8" ?>
   <context id="delorean-context">
       <component id="default-drive"
               dotted-name="delorean"
               factory-name="EquipmentFoundry.get_default_capacitor_drive" />
       <component id="capacitor-nodrive"
               dotted-name="delorean.EquipmentFoundry"
               factory-name="FluxCapacitor" />
       <component id="capacitor-withdrive"
               dotted-name="delorean.EquipmentFoundry"
               factory-name="FluxCapacitor.with_capacitor_drive">
           <init>
               <arg ref="default-drive" />
           </init>
       </component>
   </context>

Key things to note in this configuration:

* For **any** of the components, we have the option of using either
  ``delorean`` or ``delorean.EquipmentFoundry`` as a component's dotted name
  because both of these names are importable. Which we choose influences how
  the factory name must be specified - it must be *relative to* the dotted
  name.
* Any factory name is just a dotted name - but split into its individual names,
  it must represent a callable object that can be obtained via attribute access
  on the module or class identified by the dotted name.

We can now assemble the *"capacitor-nodrive"* and *"capacitor-withdrive"*
components as we would any other Aglyph components:

>>> from aglyph.assembler import Assembler
>>> from aglyph.context import XMLContext
>>> assembler = Assembler(XMLContext("delorean-context.xml"))
>>> flux_capacitor_without_drive = assembler.assemble("capacitor-nodrive")
>>> flux_capacitor_with_drive = assembler.assemble("capacitor-withdrive")

.. note::
   If you remember nothing else, remember this:

   1. :attr:`aglyph.component.Component.dotted_name` must be **importable**.
   2. :attr:`aglyph.component.Component.factory_name` must be *relative to*
      the importable ``dotted_name``.

Using fluent API configuration
------------------------------

Here is an equivalent programmatic configuration in a *bindings.py* module::

   from aglyph.context import Context
   from aglyph.component import Reference as ref
   
   context = Context("delorean-context")
   (context.component("default-drive").
       create("delorean", factory="EquipmentFoundry.get_default_capacitor_drive").
       register())
   (context.component("capacitor-nodrive").
       create("delorean.EquipmentFoundry", factory="FluxCapacitor").
       register())
   (context.component("capacitor-withdrive").
       create("delorean.EquipmentFoundry", factory="FluxCapacitor.with_capacitor_drive").
       init(ref("default-drive")).
       register())

.. _member-component:

Describe components for module or class members
===============================================

Similar in nature to the ``factory_name`` property explained in the previous
section, the :attr:`aglyph.component.Component.member_name` property provides a
way to access objects that are not directly importable.

But there are two key differences between ``member_name`` and ``factory_name``:

1. The object identified by a ``member_name`` is not required to be callable.
   Instead, the object itself is considered to **be** the component object.
2. Even if the object identified by a ``member_name`` *is* callable, Aglyph
   will **not** call it.

.. note::
   As a consequence of #1, any initialization arguments or keywords that are
   specified for a component that also specifies a ``member_name`` are
   **ignored** (i.e. Aglyph does **not** initialize the ``member_name``
   object). However, any "setter" dependencies (setter methods, fields,
   properties) defined for such a component **are** processed.

   As a consequence of #2, you can define components whose objects are of *any*
   type, including class types, function types, and (sub)module types.

In the examples below, we will use the Python standard library
:class:`http.server.HTTPServer` class (whose initializer accepts a ``class``
object for the request handler class) to demonstrate one possible use of the
:attr:`aglyph.component.Component.member_name` property.

Using declarative XML configuration
-----------------------------------

In a *cookbook-context.xml* document::

   <?xml version="1.0" encoding="UTF-8" ?>
   <context id="cookbook-context">
       <component id="request-handler-class"
               dotted-name="http.server"
               member-name="BaseHTTPRequestHandler" />
       <component id="http-server" dotted-name="http.server.HTTPServer">
           <init>
               <arg>
                   <tuple>
                       <str>localhost</str>
                       <int>8080</int>
                   </tuple>
               </arg>
               <arg reference="request-handler-class" />
           </init>
       </component>
   </context>

When the *"http-server"* component is assembled, its second initialization
argument is actually the *class* ``http.server.BaseHTTPRequestHandler`` (as
opposed to an *instance* thereof):

>>> from aglyph.assembler import Assembler
>>> from aglyph.context import XMLContext
>>> assembler = Assembler(XMLContext("cookbook-context.xml"))
>>> httpd = assembler.assemble("http-server")
>>> httpd.RequestHandlerClass
<class 'http.server.BaseHTTPRequestHandler'>
>>> assembler.assemble("request-handler-class") is httpd.RequestHandlerClass
True

Using fluent API configuration
------------------------------

Here is an equivalent programmatic configuration in a *bindings.py* module::

   from aglyph.context import Context
   from aglyph.component import Reference as ref
   
   context = Context("cookbook-context")
   (context.component("request-handler-class").
       create("http.server", member="BaseHTTPRequestHandler").
       register())
   (context.component("http-server").
       create("http.server.HTTPServer").
       init(("localhost", 8080), ref("request-handler-class")).
       register())

.. _impl-specific-component:

Describe components for Python implementation-specific objects (Stackless, PyPy, IronPython, Jython)
====================================================================================================

Strictly speaking, there is nothing "special" (from an Aglyph perspective)
about the examples presented in the following subsections. They just build
upon the previous cookbook recipes :ref:`simple-component`,
:ref:`component-reference`, and
:ref:`staticmethod-classmethod-nestedclass-component` to once again demonstrate
that Aglyph can assemble *any* component that can be described using dotted
name notation, even when the class or function is only available to a specific
implementation of Python.

Example 1: Describe a component for a Stackless Python or PyPy tasklet
----------------------------------------------------------------------
The `Stackless Python`_ and `PyPy`_ Python implementations support the
`stackless.tasklet`_ wrapper, which allows any callable to run as a microthread.

The examples below demonstrate the Aglyph configuration for a variation of the
sample code given in the `Stackless Python "Tasklets"`_ Wiki article.

Using declarative XML configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In a *cookbook-context.xml* document::

   <?xml version="1.0" encoding="UTF-8" ?>
   <context id="cookbook-context">
       <component id="aCallable-func" dotted-name="cookbook"
               member-name="aCallable" />
       <component id="aCallable-task" dotted-name="stackless.tasklet">
           <init>
               <arg reference="aCallable-func" />
           </init>
       </component>
   </context>

Assembling and running this tasklet looks like this:

>>> from aglyph.assembler import Assembler
>>> from aglyph.context import XMLContext
>>> assembler = Assembler(XMLContext("cookbook-context.xml"))
>>> task = assembler.assemble("aCallable-task")
>>> task.setup("assembled by Aglyph")
>>> task.run()
'aCallable: assembled by Aglyph'

Using fluent API configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Below is an example of programmatic configuration, but with a twist - we allow
Aglyph to inject the function argument into the task so that we only need to
assemble and run it. This works because the ``stackless.tasklet.setup`` method
has setter method semantics.

In a *bindings.py* module::

   from aglyph.context import Context
   from aglyph.component import Reference as ref
   
   context = Context("cookbook-context")
   context.component("aCallable-func").create("cookbook", member="aCallable").register()
   (context.component("aCallable-task").
       create("stackless.tasklet").
       init(ref("aCallable-func")).
       set(setup="injected by Aglyph").
       register())

Assembling and running this tasklet looks like this:

>>> from aglyph.assembler import Assembler
>>> from bindings import context
>>> assembler = Assembler(context)
>>> task = assembler.assemble("aCallable-task")
>>> task.run()
'aCallable: injected by Aglyph'

Example 2: Describe a component for a .NET XmlReader
----------------------------------------------------
`IronPython`_ developers have access to the .NET Framework Standard Library and
any custom assemblies via the ``clr`` module, allowing any .NET namespace to be
loaded into the IronPython runtime and used.

In the examples below, we use `System.Xml.DtdProcessing`_,
`System.Xml.ValidationType`_, `System.Xml.XmlReaderSettings`_, and
`System.Xml.XmlReader`_ to configure an XML reader that parses a fictitious
"AppConfig.xml" document.

.. warning::
   When using IronPython, the .NET namespace for any class referenced in an
   Aglyph component **must** be loaded prior to asking Aglyph to assemble the
   component. (Otherwise, those classes would not be importable in IronPython.)

   In the examples given below, this means that the following statements must
   be executed *before* :meth:`aglyph.assembler.Assembler.assemble` or
   :meth:`aglyph.binder.Binder.lookup` is called (because the "System.Xml"
   namespace is not present by default):

   >>> import clr
   >>> clr.AddReference("System.Xml")

Using declarative XML configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In a *dotnet-context.xml* document::

   <?xml version="1.0" ?>
   <context id="dotnet-context">
       <component id="dtd-parse" dotted-name="System.Xml"
               member-name="DtdProcessing.Parse" />
       <component id="dtd-validate" dotted-name="System.Xml"
               member-name="ValidationType.DTD" />
       <component id="xmlreader-settings" dotted-name="System.Xml.XmlReaderSettings">
           <attributes>
               <attribute name="IgnoreComments"><true /></attribute>
               <attribute name="IgnoreProcessingInstructions"><true /></attribute>
               <attribute name="IgnoreWhitespace"><true /></attribute>
               <attribute name="DtdProcessing" reference="dtd-parse" />
               <attribute name="ValidationType" reference="dtd-validate" />
           </attributes>
       </component>
       <component id="app-config-reader" dotted-name="System.Xml.XmlReader"
               factory-name="Create">
           <init>
               <arg><str>file:///C:/Example/Settings/AppConfig.xml</str></arg>
               <arg reference="xmlreader-settings" />
           </init>
       </component>
   </context>

With the Aglyph context in place, we can now assemble an XML reader for our
fictitious application configuration reader:

>>> import clr
>>> clr.AddReference("System.Xml")
>>> from aglyph.assembler import Assembler
>>> from aglyph.context import XMLContext
>>> assembler = Assembler(XMLContext("dotnet-context.xml"))
>>> assembler.assemble("app-config-reader")
<System.Xml.XmlValidatingReaderImpl object at 0x000000000000002B [System.Xml.XmlValidatingReaderImpl]>

Using fluent API configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here is an equivalent programmatic configuration in a *bindings.py* module::

   from aglyph.context import Context
   from aglyph.component import Reference
    
   context = Context("dotnet-context")
   (context.component("dtd-parse").
       create("System.Xml", member="DtdProcessing.Parse").
       register())
   (context.component("dtd-validate").
       create("System.Xml", member="ValidationType.DTD").
       register())
   (context.component("xmlreader-settings").
       create("System.Xml.XmlReaderSettings").
       set(
           IgnoreComments=True,
           IgnoreProcessingInstructions=True,
           IgnoreWhitespace=True,
           DtdProcessing=Reference("dtd-parse"),
           ValidationType=Reference("dtd-validate")).
       register())
   (context.component("app-config-reader").
       create("System.Xml.XmlReader", factory_name="Create").
       init(
           "file:///C:/Example/Settings/AppConfig.xml",
           Reference("xmlreader-settings")).
       register())

The code to assemble the fictitious application configuration reader looks like
this:

>>> import clr
>>> clr.AddReference("System.Xml")
>>> from aglyph.assembler import Assembler
>>> from bindings import context
>>> assembler = Assembler(context)
>>> assembler.assemble("app-config-reader")
<System.Xml.XmlValidatingReaderImpl object at 0x000000000000002B [System.Xml.XmlValidatingReaderImpl]>

Example 3: Describe a component for a Java™ LinkedHashMap
---------------------------------------------------------
`Jython`_ developers have direct access to the Java™ Platform API and any custom
JARs in the runtime *CLASSPATH*.

In the examples below, we use
`java.util.Collections#synchronizedMap(java.util.Map)`_ and `java.util.LinkedHashMap`_
to configure a thread-safe, insertion-order hash map.

Using declarative XML configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In a *java-context.xml* document::

   <?xml version="1.0" encoding="UTF-8" ?>
   <context id="java-context">
       <component id="java.util.LinkedHashMap" />
       <component id="threadsafe-ordered-map" dotted-name="java.util.Collections"
               factory-name="synchronizedMap">
           <init>
               <arg reference="java.util.LinkedHashMap" />
           </init>
       </component>
   </context>

To assemble our map:

>>> from aglyph.assembler import Assembler
>>> from aglyph.context import XMLContext
>>> assembler = Assembler(XMLContext("java-context.xml"))
>>> mapping = assembler.assemble("threadsafe-ordered-map")
>>> mapping.__class__
<type 'java.util.Collections$SynchronizedMap'>

Using fluent API configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here is an equivalent programmatic configuration in a *bindings.py* module::

   from aglyph.context import Context
   from aglyph.component import Reference
    
   context = Context("java-context")
   context.component("java.util.LinkedHashMap")
   (context.component("threadsafe-ordered-map").
       create("java.util.Collections", factory="synchronizedMap").
       init(Reference("java.util.LinkedHashMap")).
       register())

Assembling the map looks like this:

>>> from aglyph.assembler import Assembler
>>> from bindings import context
>>> assembler = Assembler(context)
>>> mapping = assembler.assemble("threadsafe-ordered-map")
>>> mapping.__class__
<type 'java.util.Collections$SynchronizedMap'>

.. _custom-xmlcontext-parser:

Use a custom XML parser for XMLContext
======================================

Aglyph uses the :mod:`xml.etree.ElementTree` API for processing context
documents. By default, ElementTree uses the `Expat`_ XML parser (via
:class:`xml.etree.ElementTree.XMLParser`) to build element structures.

However, developers may subclass :class:`xml.etree.ElementTree.XMLParser` to
use *any* XML parser; simply pass an instance of the subclass to
:class:`aglyph.context.XMLContext` as the ``parser`` keyword argument.

.. note::
   For a real, working example, please refer to ``aglyph._compat.CLRXMLParser``,
   which is an :class:`xml.etree.ElementTree.XMLParser` subclass that uses the
   .NET `System.Xml.XmlReader`_ parser.

.. _clear-caches:

Clear the Aglyph singleton, weakref, and borg memory caches
===========================================================

:class:`aglyph.assembler.Assembler` automatically caches objects of
**singleton** and **weakref** components, as well as the shared-state
dictionaries of **borg** components, in memory. There is no automatic eviction
strategy.

These caches may be cleared explicitly by calling
:meth:`aglyph.assembler.Assembler.clear_singletons`,
:meth:`aglyph.assembler.Assembler.clear_weakrefs`,  or
:meth:`aglyph.assembler.Assembler.clear_borgs`, respectively. Each method
returns a list of component IDs that were evicted.

.. warning::
   There are some limitations on weakref caching, particularly with respect to
   :ref:`lifecycle methods <lifecycle-methods>`. Please see
   :meth:`aglyph.assembler.Assembler.clear_weakrefs` for details.

