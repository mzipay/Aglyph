=====================================
Component inheritance using templates
=====================================

:Release: |release|

Aglyph supports a form of inheritance by allowing developers to declare that a
component or template has a "parent."

The initialization arguments (positional and keyword) and attributes of the
parent behave similarly to those of :func:`functools.partial`. Any
positional arguments declared for a child are *appended* to the parent's
declared positional arguments, and any keyword arguments and attributes
declared for a child take precedence over (possibly overriding) the same-named
keyword arguments or attributes declared by the parent.

Besides initialization arguments and attributes, child components or templates
may also inherit lifecycle method declarations from their parents. However, it
is important to understand that Aglyph will only call **one** lifecycle method
on an object for a given lifecycle state. Please refer to
:ref:`The lifecycle method lookup process <lifecycle-method-lookup-process>` to
understand how Aglyph determines *which* lifecycle method to call.

Any component or template may only declare **one** parent. However, there is no
theoretical limit to the depth of parent/child relationships, and either a
component *or* a template may serve as a parent.

.. note::
   The difference between a component and a template is that a component may be
   assembled, while a template **cannot** be assembled and may be used *only*
   as the parent of another component or template.

Following are examples of how to use components and templates together in an
Aglyph configuration context.

* :ref:`parent-template-child-components`
* :ref:`extending-components`
* :ref:`template-lifecycle-methods`

.. _parent-template-child-components:

Use a template to declare common dependencies, and child components to declare specific dependencies
====================================================================================================

In this example, we will declare components for two versions of an HTTP server
- a "simple" version and a "CGI" version. These components have one common
dependency (the server address), which will be declared in the template, and
one component-specific dependency (the request handler class), which will be
declared in each component.

Using declarative XML configuration
-----------------------------------

In the XML context document *"cookbook-context.xml"*::

   <?xml version="1.0" encoding="utf-8" ?>
   <context id="cookbook-context">
      <template id="base-server">
         <init>
           <!-- server_address -->
            <arg>
               <tutple>
                  <str>localhost</str>
                  <int>8000</int>
               </tuple>
            </arg>
         </init>
      </template>
      <component id="http.server.SimpleHTTPRequestHandler"
            dotted-name="http.server" member-name="SimpleHTTPRequestHandler" />
      <component id="simple-server" dotted-named="http.server.HTTPServer"
            parent-id="base-server">
         <init>
            <!-- RequestHandlerClass -->
            <arg reference="http.server.SimpleHTTPRequestHandler" />
         </init>
      </component>
      <component id="http.server.CGIHTTPRequestHandler"
            dotted-name="http.server" member-name="CGIHTTPRequestHandler" />
      <component id="cgi-server" dotted-named="http.server.HTTPServer"
            parent-id="base-server">
         <init>
            <!-- RequestHandlerClass -->
            <arg reference="http.server.CGIHTTPRequestHandler" />
         </init>
      </component>
   </context>

Assembling "simple-server" and "cgi-server", we can see that the server address
is common, but that the request handler class differs:

   >>> from aglyph.assembler import Assembler
   >>> from aglyph.context import XMLContext
   >>> assembler = Assembler(XMLContext("cookbook-context.xml"))
   >>> simple_server = assembler.assemble("simple-server")
   >>> simple_server.server_address
   ('localhost', 8000)
   >>> simple_server.RequestHandlerClass
   <class 'http.server.SimpleHTTPRequestHandler'>
   >>> cgi_server = assembler.assemble("cgi-server")
   >>> cgi_server.server_address
   ('localhost', 8000)
   >>> cgi_server.RequestHandlerClass
   <class 'http.server.CGIHTTPRequestHandler'>

Using fluent API configuration
------------------------------

In a *bindings.py* module::

   from aglyph.context import Context
   from aglyph.component import Reference as ref
    
   context = Context("cookbook-context")
   context.template("base-server").init(("localhost", 8000)).register()
   (context.component("simple-handler").
       create("http.server", member_name="SimpleHTTPRequestHandler").
       register())
   (context.component("simple-server", parent_id_spec="base-server").
       create("http.server.HTTPServer").
       init(ref("simple-handler")).
       register())
   (context.component("cgi-handler").
       create("http.server", member_name="CGIHTTPRequestHandler").
       register())
   (context.component("cgi-server", parent_id_spec="base-server").
       create("http.server.HTTPServer").
       init(ref("cgi-handler")).
       register())

As in the XML example, assembling the "simple-server" and "cgi-server"
components shows that the server address is common, but that the request
handler class differs:

   >>> from aglyph.assembler import Assembler
   >>> from bindings import context
   >>> assembler = Assembler(context)
   >>> simple_server = assembler.assemble("simple-server")
   >>> simple_server.server_address
   ('localhost', 8000)
   >>> simple_server.RequestHandlerClass
   <class 'http.server.SimpleHTTPRequestHandler'>
   >>> cgi_server = assembler.assemble("cgi-server")
   >>> cgi_server.server_address
   ('localhost', 8000)
   >>> cgi_server.RequestHandlerClass
   <class 'http.server.CGIHTTPRequestHandler'>

.. _extending-components:

"Extend" a component by using another component as the parent
=============================================================

In this example, we have a "default" HTTP server with stock settings and a
"custom" HTTP server that extends the default to redefine several settings.
Either server is fully functional as a standalone component, and so we use the
default server as the parent of the custom server.

This example does not require the use of templates; any component can serve as
the parent of another component.

Using declarative XML configuration
-----------------------------------

In the XML context document *"cookbook-context.xml"*::

   <?xml version="1.0" encoding="utf-8" ?>
   <context id="cookbook-context">
      <component id="request-handler" dotted-name="http.server"
            member-name="CGIHTTPRequestHandler" />
      <component id="default-server" dotted-named="http.server.HTTPServer">
         <init>
           <!-- server_address -->
            <arg>
               <tutple>
                  <str>localhost</str>
                  <int>8000</int>
               </tuple>
            </arg>
            <!-- RequestHandlerClass -->
            <arg reference="request-handler" />
         </init>
      </component>
      <component id="custom-server" dotted-named="http.server.HTTPServer"
            parent-id="default-server">
         <attributes>
            <attribute name="request_queue_size"><int>15</int></attribute>
            <attribute name="timeout"><float>3</float></attribute>
         </attributes>
      </component>
   </context>

Assembling "default-server" and "custom-server", we can see that the server
address and request handler class are the same, but that the custom server has
non-default values for the request queue size and socket timeout:

   >>> from aglyph.assembler import Assembler
   >>> from aglyph.context import XMLContext
   >>> assembler = Assembler(XMLContext("cookbook-context.xml"))
   >>> default_server = assembler.assemble("default-server")
   >>> default_server.server_address
   ('localhost', 8000)
   >>> default_server.RequestHandlerClass
   <class 'http.server.SimpleHTTPRequestHandler'>
   >>> default_server.request_queue_size
   5
   >>> default_server.timeout is None
   True
   >>> custom_server = assembler.assemble("custom-server")
   >>> custom_server.server_address
   ('localhost', 8000)
   >>> custom_server.RequestHandlerClass
   <class 'http.server.SimpleHTTPRequestHandler'>
   >>> custom_server.request_queue_size
   15
   >>> custom_server.timeout
   3.0

Using fluent API configuration
------------------------------

In a *bindings.py* module::

   from aglyph.context import Context
   from aglyph.component import Reference as ref
    
   context = Context("cookbook-context")
   (context.component("request-handler").
       create("http.server", member_name="SimpleHTTPRequestHandler").
       register())
   (context.component("default-server").
      create("http.server.HTTPServer").
      init(("localhost", 8000), ref("request-handler")).
      register())
   (context.component("custom-server", parent_id_spec="default-server").
      create("http.server.HTTPServer").
      set(request_queue_size=15, timeout=3.0).
      register())

As in the XML example, assembling the "default-server" and "custom-server"
components shows that the server address and request handler class are common,
but that the request queue size and timeout differ:

   >>> from aglyph.assembler import Assembler
   >>> from bindings import context
   >>> assembler = Assembler(context)
   >>> default_server = assembler.assemble("default-server")
   >>> default_server.server_address
   ('localhost', 8000)
   >>> default_server.RequestHandlerClass
   <class 'http.server.SimpleHTTPRequestHandler'>
   >>> default_server.request_queue_size
   5
   >>> default_server.timeout is None
   True
   >>> custom_server = assembler.assemble("custom-server")
   >>> custom_server.server_address
   ('localhost', 8000)
   >>> custom_server.RequestHandlerClass
   <class 'http.server.SimpleHTTPRequestHandler'>
   >>> custom_server.request_queue_size
   15
   >>> custom_server.timeout
   3.0

.. _template-lifecycle-methods:

Use templates to declare the lifecycle methods used by similar components
=========================================================================

In this example, assume that a *cookbook.py* module contains the following
class and method definitions::

   class Hydrospanner:
      def calibrate(self):
         ...
      def disengage(self):
         ...

   class Nervesplicer:
      def prepare(self):
         self.sterilize()
         self.calibrate()
      def sterilize(self):
         ...
      def calibrate(self):
         ...
      def disengage(self):
         ...

   class Macrofuser:
      def ignite(self):
         ...
      def extinguish(self):
         ...

   class Vibrotorch:
      def ignite(self):
         ...
      def extinguish(self):
         ...

In the example configurations below, the *"mechanical-tool"* template (used as
a parent by the ``Hydrospanner`` and ``Nervesplicer`` components) declares the
``calibrate`` and ``disengage`` lifecycle methods, and the *"incendiary-tool"*
template (used as a parent by the ``Macrofuser`` and ``Vibrotorch`` components)
declares the ``ignite`` and ``extinguish`` lifecycle methods.

.. note::
   The ``Nervesplicer`` component represents a special case. While it declares
   *"mechanical-tool"* as its parent, and implements the ``calibrate``
   initialization method, there is an additional initilization method
   (``sterilize``) which should be called. To accomplish this, the
   ``Nervesplicer.prepare()`` initialization method is implemented to call
   ``sterilize()`` *and* ``calibrate()``, and is declared as the "after
   injection" lifecycle method for ``Nervesplicer``, specifically.

The configurations shown below result in the following behaviors during the
application's lifetime:

* When the *"cookbook.Hydrospanner"* component is assembled and has not yet
  been cached, its ``calibrate`` method is called before the object is cached
  and returned to the caller.
* When the *"cookbook.Nervesplicer"* component is assembled and has not yet
  been cached, its ``prepare`` method is called before the object is cached and
  returned to the caller.
* When **either** the *"cookbook.Hydrospanner"* or *"cookbook.Nervesplicer"*
  component is cleared from cache (via
  :meth:`aglyph.assembler.Assembler.clear_singletons`), its ``disengage``
  method is called.
* When **either** the *"cookbook.Macrofuser"* or *"cookbook.Vibrotorch"*
  component is assembled and has not yet been cached, its ``ignite`` method is
  called before the object is cached and returned to the caller.
* When **either** the *"cookbook.Macrofuser"* or *"cookbook.Vibrotorch"*
  component is cleared from cache (via
  :meth:`aglyph.assembler.Assembler.clear_singletons`), its ``extinguish``
  method is called.

Using declarative XML configuration
-----------------------------------

In a *coookbook-context.xml* document::

   <?xml version="1.0" encoding="utf-8" ?>
   <context id="cookbook-context">
      <template id="mechanical-tool"
            after-inject="calibrate" before-clear="disengage" />
      <component id="cookbook.Hydrospanner" strategy="singleton"
            parent-id="mechanical-tool" />
      <component id="cookbook.Nervesplicer" strategy="singleton"
            parent-id="mechanical-tool" after-inject="prepare" />
      <template id="incendiary-tool"
            after-inject="ignite" before-clear="extinguish" />
      <component id="cookbook.Macrofuser" strategy="singleton"
            parent-id="incendiary-tool" />
      <component id="cookbook.Vibrotorch" strategy="singleton"
            parent-id="incendiary-tool" />
   </context>

Using fluent API configuration
------------------------------

In a *bindings.py* module::

   from aglyph.context import Context
    
   context = Context("cookbook-context")
   (context.template("mechanical-tool").
       call(after_inject="calibrate", before_clear="disengage").
       register())
   context.singleton("cookbook.Hydrospanner", parent_id_spec="mechanical-tool").register()
   (context.singleton("cookbook.Nervesplicer", parent_id_spec="mechanical-tool").
       call(after_inject="prepare").
       register())
   (context.template("incendiary-tool").
       call(after_inject="ignite", before_clear="extinguish").
       register())
   context.singleton("cookbook.Macrofuser", parent_id_spec="incendiary-tool").register()
   context.singleton("cookbook.Vibrotorch", parent_id_spec="incendiary-tool").register()

