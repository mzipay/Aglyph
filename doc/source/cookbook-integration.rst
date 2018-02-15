==================
Integrating Aglyph
==================

:Release: |release|

.. _CherryPy: http://cherrypy.org/
.. _Jinja: http://jinja.pocoo.org/
.. _Web Site Process Bus: https://cherrypy.readthedocs.io/en/latest/pkg/cherrypy.process.html#web-site-process-bus

* :ref:`aglyph-config-cherrpy`
* :ref:`aglyph-di-plugin`
* :ref:`aglyph-di-plugin-lifecycle`

.. _aglyph-config-cherrpy:

Use Aglyph to configure your `CherryPy`_ application
====================================================

CherryPy's custom plugins and tools already provide a DI-like way to manage your
web application's runtime dependencies, but *configuring* those custom plugins
and tools can still result in bootstrap code that tightly couples their
configuration and use. In this example, we'll use Aglyph to configure a CherryPy
application to use `Jinja`_ templating.

Using declarative XML configuration
-----------------------------------

In the *myapp/config/myapp-context.xml* file::

   <?xml version="1.0" encoding="utf-8" ?>
   <context id="myapp-context">
      <component id="jinja2-loader" dotted-name="jinja2.FileSystemLoader">
         <init>
            <arg><str>templates</str></arg>
         </init>
      </component>
      <component id="jinja2.Environment">
         <init>
            <arg reference="jinja2-loader" />
         </init>
      </component>
      <component id="template-tool"
            dotted-name="myapp.tools.jinja2tool.Jinja2Tool">
         <init>
            <arg reference="jinja2.Environment" />
         </init>
      </component>
      <component id="cherrypy-tools" dotted-name="cherrypy" member-name="tools">
         <attributes>
            <attribute name="template" reference="template-tool" />
         </attributes>
      </component>
   </context>

Now in our application's main module we simply use Aglyph to assemble the
*"cherrypy-tools"* component, which has the effect of setting
``cherrypy.tools.template`` to an instance of
``myapp.tools.jinja2tool.Jinja2Tool``::

   from algpyh.assembler import Assembler
   from aglyph.context import XMLContext
    
   assembler = Assembler(XMLContext("config/myapp-context.xml"))
   # note that we do not assign the assembled component - it's unnecessary
   assembler.assemble("cherrypy-tools")

Alternatively, we could assemble just the *"template-tool"* component and
assign it explicitly::

   import cherrypy
   from algpyh.assembler import Assembler
   from aglyph.context import XMLContext
    
   assembler = Assembler(XMLContext("config/myapp-context.xml"))
    
   cherrypy.tools.template = assembler.assemble("template-tool")

Using fluent API configuration
------------------------------

In a *bindings.py* module for the *myapp* application::

   from aglyph.context import Context
   from aglyph.component import Reference as ref

   context = Context("myapp-context")
   (context.component("jinja2-loader").
       create("jinja2.FileSystemLoader").
       init("templates").
       register())
   context.component("jinja2.Environment").init(loader=ref("jinja2-loader")).register()
   (context.component("template-tool").
       create("myapp.tools.jinja2tool.Jinja2Tool").
       init(ref("jinja2.Environment")).
       register())
   (context.component("cherrypy-tools").
       create("cherrypy", member="tools").
       set(template=ref("template-tool")).
       register())

Now in our application's main module we simply use Aglyph to assemble the
*"cherrypy-tools"* component, which has the effect of setting
``cherrypy.tools.template`` to an instance of
``myapp.tools.jinja2tool.Jinja2Tool``::

   from aglyph.assembler import Assembler
   from bindings import context
   
   # note that we do not assign the assembled component - it's unnecessary
   Assembler(context).assemble("cherrypy-tools")

Alternatively, we could assemble just the *"template-tool"* component and
assign it explicitly::

   import cherrypy
   from aglyph.assembler import Assembler
   from bindings import context
    
   cherrypy.tools.template = Assembler(context).assemble("template-tool")

.. _aglyph-di-plugin:

Provide dependency injection support to your application using ``AglyphDIPlugin``
=================================================================================

This example shows how to use
:class:`aglyph.integration.cherrypy.AglyphDIPlugin` (a
:class:`cherrypy.process.plugins.SimplePlugin`), allowing your application's
other plugins, tools, and dispatchers to assemble components via CherryPy's
`Web Site Process Bus`_.

Using declarative XML configuration
-----------------------------------

Using an Aglyph XML context document *myapp/config/myapp-context.xml*,
configure the Aglyph DI plugin in your application's main module like so::

   import cherrypy
   from aglyph.assembler import Assembler
   from aglyph.context import XMLContext
    
   assembler = Assembler(XMLContext("config/myapp-context.xml"))
   cherrypy.engine.aglyph = AglyphDIPlugin(cherrypy.engine, assembler)

Components may now be assembled by publishing **"aglyph-assemble"** messages
to the bus. For example::

   my_obj = cherrypy.engine.publish("aglyph-assemble", "my-component-id").pop()

Using fluent API configuration
------------------------------

Using an application-specific *bindings.py* module, configure the Aglyph DI
plugin in your application's main module like so::

   import cherrypy
   from aglyph.assembler import Assembler
   from bindings import context
    
   cherrypy.engine.aglyph = AglyphDIPlugin(cherrypy.engine, Assembler(context))

Components may now be assembled by publishing **"aglyph-assemble"** messages
to the bus. For example::

   my_obj = cherrypy.engine.publish("aglyph-assemble", "my-component-id").pop()

.. _aglyph-di-plugin-lifecycle:

Manage the lifecycles of your application components
====================================================

The :class:`aglyph.integration.cherrypy.AglyphDIPlugin` subscribes to channels
for controlling the lifecycles of Aglyph **singleton**, **borg**, and
**weakref** components:

* "aglyph-init-singletons"
* "aglyph-clear-singletons"
* "aglyph-init-borgs"
* "aglyph-clear-borgs"
* "aglyph-clear-weakrefs"

Refer to the plugin class documentation for details.

