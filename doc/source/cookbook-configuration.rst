******************************************
Choose a configuration approach for Aglyph
******************************************

Aglyph explicitly supports two methods of configuration:

1. Declarative XML configuration conforming to the
   :download:`Aglyph context DTD <../../resources/aglyph-context-2.0.0.dtd>`
2. Programmatic configuration via :class:`aglyph.binder.Binder`

Opinions vary widely on the merits of XML (particularly for configuration), but
in fairness there's also plenty of debate over the merits of "code as
configuration" (or "configuration as code" if you prefer) as well. Aglyph
strives to **not** have an opinion one way or the other by supporting *either*
approach.

However, both approaches to Aglyph configuration have strengths and weaknesses
that you should understand before choosing one over another.

.. _xml-config:

Declarative XML configuration
=============================

An Aglyph context can be defined in an XML document that conforms to the
:download:`Aglyph context DTD <../../resources/aglyph-context-2.0.0.dtd>`.

The XML context document is parsed by :class:`aglyph.context.XMLContext`, which
is just a subclass of :class:`aglyph.context.Context` that knows how to
populate itself from the parsed XML document. Once populated, this context
can then be used to create an :class:`aglyph.assembler.Assembler`:

>>> from aglyph.assembler import Assembler
>>> from aglyph.context import XMLContext
>>> my_app_context = XMLContext("my-application-context.xml")
>>> assembler = Assembler(my_app_context)

.. note::
   The
   :download:`Aglyph context DTD <../../resources/aglyph-context-2.0.0.dtd>` is
   provided primarily as a reference. The :class:`aglyph.context.XMLContext`
   class uses a non-validating parser by default.

   Developers are encouraged to explicitly validate an application's context
   XML document during testing.

   .. seealso::

      :ref:`custom-xmlcontext-parser`
         This recipe could also be used to force Aglyph to use a **validating**
         XML parser.

.. _xml-safe-builtin-mutables:

XMLContext configures mutable builtin objects safely
----------------------------------------------------

Consider the following example::

   <?xml version="1.0" encoding="utf-8"?>
   <context id="cookbook">
       <component id="cookbook.Example">
           <attributes>
               <attribute name="mutable">
                  <list>
                     <int>1</int>
                     <int>2</int>
                     <int>3</int>
                  </list>
               </attribute>
           </attributes>
       </component>
   </context>

Because builtin :obj:`list` objects are mutable, Aglyph will automatically turn
the *"mutable"* attribute above into an :class:`aglyph.component.Evaluator`
(which is very similar to a :obj:`functools.partial`). Whenever the
*"cookbook.Example"* component is assembled, the ``Evaluator`` for the
*"mutable"* attribute is called, which will produce a *new* ``list`` object.

Why is this important? Consider a corresponding ``Binder`` configuration for
the same component::

   binder.bind("cookbook.Example").attributes(mutable=[1, 2, 3])

This configuration leads to a (likely) logic error: **all** objects of the
*"cookbook.Example"* component will share a reference to a single list object.
An example illustrates the problem:

>>> example1 = binder.lookup("cookbook.Example")
>>> example1.mutable
[1, 2, 3]
>>> example1.mutable.append(4)
>>> example2 = binder.lookup("cookbook.Example")
>>> example2.mutable
[1, 2, 3, 4]

Uh-oh! That's almost certainly *not* what we intended. To guard against this
behavior, we would need to modify the binding::

   from functools import partial
   binder.bind("cookbook.Example").attributes(
       mutable=partial(list, [1, 2, 3])
   )

Now we will get a "fresh" list every time the component is assembled, so
modifying the list on one instance will not affect the lists of any other
instances.

(And what if we were actually specifying a list-of-list, or a tuple-of-list, or
a list-of-dict? Now we would need to account for mutability of *each* member!)

This is an easy thing to forget, and can lead to a great deal of (programmatic)
configuration code, which is why
:class:`aglyph.context.XMLContext` handles it automatically for any ``<list>``,
``<tuple>``, and ``<dict>`` declared in the XML context document.

.. seealso::
   :ref:`deferred-resolution`

.. _xml-unicode-charset-conv:

XMLContext is Unicode-aware and supports automatic character set conversion
---------------------------------------------------------------------------

Aglyph properly handles Unicode text and encoded byte data in XML context
documents, regardless of Python version.

Aglyph can also provide your application components with byte data encoded to a
user-specified character set.

Consider the following example::

   <?xml version="1.0" encoding="utf-8"?>
   <context id="cookbook">
       <component id="cookbook.TextAndData">
           <attributes>
               <attribute name="text">
                   <unicode>ΑΦΔ</unicode>
               </attribute>
               <attribute name="data1">
                   <bytes>ΑΦΔ</bytes>
               </attribute>
               <attribute name="data2">
                   <bytes encoding="iso-8859-7">ΑΦΔ</bytes>
               </attribute>
           </attributes>
       </component>
   </context>

The first thing to notice is that ``<bytes>ΑΦΔ</bytes>`` is missing a character
encoding. This can be problematic on Python 2, because the default string
encoding used by the Unicode implementation is typically ASCII::

   $ python2.7
   Python 2.7.6 (default, Nov 12 2013, 13:10:34) 
   [GCC 4.2.1 (Apple Inc. build 5666) (dot 3)] on darwin
   Type "help", "copyright", "credits" or "license" for more information.
   >>> import sys
   >>> sys.getdefaultencoding()
   'ascii'
   >>> from aglyph.context import XMLContext
   >>> context = XMLContext("cookbook-context.xml")
   Traceback (most recent call last):
     ...
   UnicodeEncodeError: 'ascii' codec can't encode characters in position 0-2: ordinal not in range(128)

One solution would be to add the ``encoding=`` attribute. Alternatively, you
can instruct ``XMLContext`` to use a different default encoding (it uses the
value of :func:`sys.getdefaultencoding` by default)::

   $ python2.7
   Python 2.7.6 (default, Nov 12 2013, 13:10:34) 
   [GCC 4.2.1 (Apple Inc. build 5666) (dot 3)] on darwin
   Type "help", "copyright", "credits" or "license" for more information.
   >>> from aglyph.assembler import Assembler
   >>> from aglyph.context import XMLContext
   >>> context = XMLContext("cookbook-context.xml", default_encoding="UTF-8")
   >>> assembler = Assembler(context)
   >>> text_and_data = assembler.assemble("cookbook.TextAndData")
   >>> text_and_data.text
   u'\u0391\u03a6\u0394'
   >>> text_and_data.data1
   '\xce\x91\xce\xa6\xce\x94'
   >>> text_and_data.data2
   '\xc1\xd6\xc4'

If we run the same example under Python 3 (which uses "UTF-8" as the default
encoding), we still get correct results, but without the need to explicitly set
the default encoding on the ``XMLContext``::

   $ python3.3
   Python 3.3.3 (default, Nov 23 2013, 16:24:30) 
   [GCC 4.2.1 (Apple Inc. build 5666) (dot 3)] on darwin
   Type "help", "copyright", "credits" or "license" for more information.
   >>> from aglyph.assembler import Assembler
   >>> from aglyph.context import XMLContext
   >>> context = XMLContext("cookbook-context.xml")
   >>> assembler = Assembler(context)
   >>> text_and_data = assembler.assemble("cookbook.TextAndData")
   >>> text_and_data.text
   'ΑΦΔ'
   >>> text_and_data.data1
   b'\xce\x91\xce\xa6\xce\x94'
   >>> text_and_data.data2
   b'\xc1\xd6\xc4'

One important thing to notice is the difference in the *types* of the Unicode
and byte strings, dependent upon which version of Python is used.

Unicode and character encoding differences between Python 2 and Python 3
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The builtin :obj:`str` type has changed significantly between Python 2 and
Python 3 (see `Text Vs. Data Instead Of Unicode Vs. 8-bit
<http://docs.python.org/release/3.0/whatsnew/3.0.html#text-vs-data-instead-of-unicode-vs-8-bit>`_).

In short: :obj:`str` represented encoded byte data up to and including
Python 2, but representes *Unicode text* as of Python 3.0:

+----------+-------------------+-------------------+
| Version  |    Unicode text   | Encoded byte data |
+==========+===================+===================+
| Python 2 |    ``unicode``    |      ``str``      |
+----------+-------------------+-------------------+
| Python 3 |      ``str``      |     ``bytes``     |
+----------+-------------------+-------------------+

The :download:`Aglyph context DTD
<../../resources/aglyph-context-2.0.0.dtd>` defines ``<bytes>``, ``<str>``,
and ``<unicode>`` elements that correspond to the types in the table above, but
treats the element content differently depending on the version of Python under
which Aglyph is running:

+----------+-----------------------+-------------------+---------------------+
| Version  | ``<unicode>`` content | ``<str>`` content | ``<bytes>`` content |
+==========+=======================+===================+=====================+
| Python 2 |      ``unicode``      |      ``str``      |       ``str``       |
+----------+-----------------------+-------------------+---------------------+
| Python 3 |        ``str``        |      ``str``      |      ``bytes``      |
+----------+-----------------------+-------------------+---------------------+

To summarize the above:

* ``<unicode>`` is interpreted as a ``unicode`` type in Python 2 and a ``str``
  type in Python 3
* ``<str>`` is always interpreted as a ``str`` type
* ``<bytes>`` is interpreted as a ``str`` type in Python 2 and a ``bytes`` type
  in Python 3

.. note::
   For clarity in XML context documents, it is always safe to use ``<bytes>``
   for encoded byte data and ``<unicode>`` for Unicode text (regardless of
   Python version), avoiding entirely the ambiguity of ``<str>``.

.. warning::
   Althoug the DTD permits an *encoding="..."* attribute on ``<str>`` elements,
   the attribute is **ignored** in Python 3 (a *WARNING*-level log message is
   emitted to the *aglyph.context.XMLContext* channel if it is present).

.. _binder-config:

Programmatic configuration using Binder
=======================================

.. versionadded:: 1.1.0

An :class:`aglyph.binder.Binder` can be used to both define *and* assemble
components, and can be used in "chained call" fashion to minimize the amount of
code necessary to configure Aglyph.

The easiest way to use ``Binder`` is to create an instance of it within its own
module, configure it, then import the instance from elsewhere in your
application to make use of it.

For example, in a *cookbook/bindings.py* module::

   from aglyph.binder import Binder
   
   binder = Binder("my-app-binder")
   binder.bind("cookbook.Example").init("sample").attributes(priority=1)
   # ... as many bindings as needed ...

The :meth:`aglyph.binder.Binder.bind` method returns a proxy object that has
``init`` and ``attributes`` methods which you can use to specify the arguments
and attributes/properties/setters, respectively.

Elsewhere in your application, you can assemble a *"cookbook.Example"* object
like this::

   from cookbook.bindings import binder
   
   example = binder.lookup("cookbook.Example")

Referring to other components using ``Binder`` is a matter of using
:class:`aglyph.component.Reference` to specify argument or attribute values::

   from aglyph.binder import Binder
   from aglyph.component import Reference
   
   binder = Binder("my-app-binder")
   binder.bind("cookbook.Thing").init("value")
   binder.bind("cookbook.Transmogrifier").init(Reference("cookbook.Thing"))

.. note::
   The :doc:`cookbook-common` cookbook article provides a number of detailed
   examples of using ``Binder`` for Aglyph configuration.

Binder can generate component IDs and References automatically
--------------------------------------------------------------

``Binder`` supports a form of "shorthand" which can be used when a component's
ID will be its importable dotted name.

Let's rewrite the previous example to demonstrate::

   from cookbook import Thing, Transmogrifier
   from aglyph.binder import Binder
   from aglyph.component import Reference
   
   binder = Binder("my-app-binder")
   binder.bind(Thing).init("value")
   binder.bind(Transmogrifier).init(Thing)

Notice that we are now passing the ``Thing`` and ``Transmogrifier`` classes
directly to the ``bind`` and ``init`` methods.

The :meth:`aglyph.binder.Binder.bind` method's *component_spec* argument and
*to* keyword will automatically convert any class, unbound function, or module
into an importable dotted name string. Likewise, the ``init`` and
``attributes`` methods of the proxy object returned by ``bind()`` will convert
any *value* that is a class, unbound function, or module into an
:class:`aglyph.component.Reference` to that object.

So in the above example, ``bind(Thing)`` actually expands to
``bind("cookbook.Thing")``, ``bind(Transmogrifier)`` to
``bind("cookbook.Transmogrifier")``, and ``init(Thing)`` to
``init(Reference("cookbook.Thing"))``.

.. warning::
   The technique shown here will **not** work for components that are assigned
   a user-specified component ID that is not a Python dotted name. In those
   cases, ``Reference("user-component-id")`` **must** be used to specify a
   reference.

Custom configuration using Context
==================================

Do **neither** declarative XML nor programmatic configuration suit your fancy?

An :class:`aglyph.context.Context` is just a :obj:`dict` that maps component ID
strings (i.e. :attr:`aglyph.component.Component.component_id`) to
:class:`aglyph.component.Component` instances, so embrace the open source
philosophy and "roll your own" configuration mechanism!

.. note::
   Both :class:`aglyph.context.XMLContext` and :class:`aglyph.binder.Binder`
   are simply adaptors that create and populate an internal
   :class:`aglyph.context.Context`!

