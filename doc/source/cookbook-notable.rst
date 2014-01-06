*****************************
Other notable usage scenarios
*****************************

* :ref:`staticmethod-classmethod-nestedclass-component`
* :ref:`member-component`
* :ref:`impl-specific-component`
* :ref:`custom-xmlcontext-parser`
* :ref:`clear-caches`

.. _staticmethod-classmethod-nestedclass-component:

Describe components for static methods, class methods, or nested classes
========================================================================

.. versionadded:: 2.0.0

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

Using programmatic Binder configuration
---------------------------------------

Here is an equivalent programmatic configuration in a *bindings.py* module::

   from aglyph.binder import Binder
   from aglyph.component import Reference
   
   binder = Binder("delorean-binder")
   binder.bind("default-drive", to="delorean",
               factory="EquipmentFoundry.get_default_capacitor_drive")
   binder.bind("capacitor-nodrive", to="delorean.EquipmentFoundry",
               factory="FluxCapacitor")
   (binder.bind("capacitor-withdrive", to="delorean.EquipmentFoundry",
                factory="FluxCapacitor.with_capacitor_drive").
       init(Reference("default-drive")))

.. _member-component:

Describe components for module or class members
===============================================

.. versionadded:: 2.0.0

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

Using programmatic Binder configuration
---------------------------------------

Here is an equivalent programmatic configuration in a *bindings.py* module::

   from aglyph.binder import Binder
   from aglyph.component import Reference
   
   binder = Binder("cookbook-binder")
   binder.bind("request-handler-class", to="http.server",
               member="BaseHTTPRequestHandler")
   (binder.bind("http-server", to="http.server.HTTPServer").
       init(("localhost", 8080), Reference("request-handler-class")))

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
The `Stackless Python <http://www.stackless.com/>`_ and
`PyPy <http://pypy.org/>`_ Python implementations support the
`stackless.tasklet <http://www.stackless.com/wiki/Tasklets>`_ wrapper, which
allows any callable to run as a microthread.

The examples below demonstrate the Aglyph configuration for a variation of the
sample code given in the `Stackless Python "Tasklets"
<http://www.stackless.com/wiki/Tasklets>`_ Wiki article.

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

Using programmatic Binder configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Below is an example of programmatic configuration, but with a twist - we allow
Aglyph to inject the function argument into the task so that we only need to
assemble and run it. This works because the ``stackless.tasklet.setup`` method
has setter method semantics.

In a *bindings.py* module::

   from aglyph.binder import Binder
   from aglyph.component import Reference
   
   binder = Binder("cookbook-binder")
   binder.bind("aCallable-func", to="cookbook", member="aCallable")
   (binder.bind("aCallable-task", to="stackless.tasklet").
       init(Reference("aCallable-func")).
       attributes(setup="injected by Aglyph"))

Assembling and running this tasklet looks like this:

>>> from bindings import binder
>>> task = binder.lookup("aCallable-task")
>>> task.run()
'aCallable: injected by Aglyph'

Example 2: Describe a component for a .NET XmlReader
----------------------------------------------------
`IronPython <http://ironpython.net/>`_ developers have access to the .NET
Framework Standard Library and any custom assemblies via the ``clr`` module,
allowing any .NET namespace to be loaded into the IronPython runtime and used.

In the examples below, we use `System.Xml.DtdProcessing
<http://msdn.microsoft.com/en-us/library/system.xml.dtdprocessing.aspx>`_,
`System.Xml.ValidationType
<http://msdn.microsoft.com/en-us/library/system.xml.validationtype.aspx>`_,
`System.Xml.XmlReaderSettings
<http://msdn.microsoft.com/en-us/library/system.xml.xmlreadersettings.aspx>`_,
and `System.Xml.XmlReader
<http://msdn.microsoft.com/en-us/library/system.xml.xmlreader.aspx>`_ to
configure an XML reader that parses a fictitious "AppConfig.xml" document.

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

Using programmatic Binder configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here is an equivalent programmatic configuration in a *bindings.py* module::

   from aglyph.binder import Binder
   from aglyph.component import Reference
    
   binder = Binder("dotnet-binder")
   binder.bind("dtd-parse", to="System.Xml", member="DtdProcessing.Parse")
   binder.bind("dtd-validate", to="System.Xml", member="ValidationType.DTD")
   (binder.bind("xmlreader-settings", to="System.Xml.XmlReaderSettings").
       attributes(IgnoreComments=True,
                  IgnoreProcessingInstructions=True,
                  IgnoreWhitespace=True,
                  DtdProcessing=Reference("dtd-parse"),
                  ValidationType=Reference("dtd-validate")))
   (binder.bind("app-config-reader", to="System.Xml.XmlReader", factory="Create").
       init("file:///C:/Example/Settings/AppConfig.xml",
            Reference("xmlreader-settings")))

The code to assemble the fictitious application configuration reader looks like
this:

>>> import clr
>>> clr.AddReference("System.Xml")
>>> from bindings import binder
>>> binder.lookup("app-config-reader")
<System.Xml.XmlValidatingReaderImpl object at 0x000000000000002B [System.Xml.XmlValidatingReaderImpl]>

Example 3: Describe a component for a Java™ LinkedHashMap
---------------------------------------------------------
`Jython <http://www.jython.org/>`_ developers have direct access to the
Java™ Platform API and any custom JARs in the runtime *CLASSPATH*.

In the examples below, we use
`java.util.Collections#synchronizedMap(java.util.Map)
<http://docs.oracle.com/javase/6/docs/api/java/util/Collections.html#synchronizedMap(java.util.Map)>`_
and `java.util.LinkedHashMap
<http://docs.oracle.com/javase/6/docs/api/java/util/LinkedHashMap.html>`_ to
configure a thread-safe, insertion-order hash map.

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

Using programmatic Binder configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here is an equivalent programmatic configuration in a *bindings.py* module::

   from aglyph.binder import Binder
   from aglyph.component import Reference
    
   binder = Binder("java-binder")
   binder.bind("java.util.LinkedHashMap")
   (binder.bind("threadsafe-ordered-map", to="java.util.Collections",
                factory="synchronizedMap").
       init(Reference("java.util.LinkedHashMap")))

Assembling the map looks like this:

>>> from bindings import binder
>>> mapping = binder.lookup("threadsafe-ordered-map")
>>> mapping.__class__
<type 'java.util.Collections$SynchronizedMap'>

.. _custom-xmlcontext-parser:

Use a custom XML parser for XMLContext
======================================

Aglyph uses the :mod:`xml.etree.ElementTree` API for processing context
documents. By default, ElementTree uses the `expat
<http://expat.sourceforge.net/>`_ XML parser (via
:class:`xml.etree.ElementTree.XMLParser`) to build element structures.

However, developers may subclass :class:`xml.etree.ElementTree.XMLParser` to
use *any* XML parser; simply pass an instance of the subclass to
:class:`aglyph.context.XMLContext` as the ``parser`` keyword argument.

.. note::
   For an example, please refer to :class:`aglyph.compat.ipytree.CLRXMLParser`,
   which is an :class:`xml.etree.ElementTree.XMLParser` subclass that uses the
   .NET `System.Xml.XmlReader
   <http://msdn.microsoft.com/en-us/library/system.xml.xmlreader.aspx>`_
   parser.

.. _clear-caches:

Clear the Aglyph singleton and/or borg memory caches
====================================================

:class:`aglyph.assembler.Assembler` automatically caches objects of
**singleton** components and share-state dictionaries of **borg** components in
memory. There is no eviction strategy by default.

These caches may be cleared explicitly by calling
:meth:`aglyph.assembler.Assembler.clear_singletons` or
:meth:`aglyph.assembler.Assembler.clear_borgs`, respectively. Each method
returns a list of component IDs that were evicted.

.. note::
   The ``clear_singletons()`` and ``clear_borgs()`` methods are also available
   on :class:`aglyph.binder.Binder` instances.

