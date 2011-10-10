===============
Aglyph cookbook
===============

This article is a combination FAQ, DO/DON'T list, and "recipe" list for using
Aglyph effectively.

Use Aglyph with Python 2 or Python 3, and with all popular variants
-------------------------------------------------------------------

Aglyph runs on *both* Python 2 and Python 3, and on recent versions of the
`PyPy <http://pypy.org/>`_, `Jython <http://www.jython.org/>`_,
`IronPython <http://ironpython.net/>`_, and
`Stackless Python <http://www.stackless.com/>`_ variants.

Whether your application runs on Python 2 or Python 3, and whether you're
using CPython or a variant, you will:

* use the same distribution of Aglyph
* use the same classes† and methods from the :doc:`Aglyph API <api-ref>`
* configure your Aglyph context (whether XML or pure-Python) in the same way

† *IronPython* developers should refer to :mod:`aglyph.compat.ipyetree`.

Use 3rd-party classes/functions as components 
---------------------------------------------

Using 3rd-party classes/functions as components (either to provide dependencies
to them, use them as dependencies, or both) is no different than using your
application's classes/functions as components.

As long as the 3rd-party class/function in question has an importable
*"relative_module.identifier"* dotted-name string, it can have its dependencies
injected:

In XML::

    <component id="third-party-thing" dotted-name="external.package.Thing">
        ...
    </component>

In pure Python::

    binder.bind("third-party-thing", "external.package.Thing")...

Define dependencies in XML for built-ins not described by the Aglyph DTD
------------------------------------------------------------------------

Aglyph describes only the most common built-in types (``bytes``, ``str``,
``int``, ``float``, ``list``, ``tuple``, and ``dict``) in the DTD, but this
doesn't mean other built-ins *can't* be used.

For this use case, Aglyph XML configuration supports the ``<eval>`` element,
which creates a :func:`functools.partial` that will call the built-in
:func:`eval` function with the element text as an argument::

    <component id="app.Thing">
        <init>
            <arg keyword="fruits">
                <eval><![CDATA[frozenset(["Apple", "Orange", "Banana", "Pear"])]]></eval>
            </arg>
        </init>
    </component>

.. warning::

    The environment for :func:`eval` is **restricted** to a subset of
    built-in constants, classes, and functions for security reasons.

    Most of what you'll need is there (except things like :func:`__import__`,
    :func:`compile`, etc.), but if you encounter ``NameError`` when the
    component is being assembled, it's likely because you're attempting to use
    a built-in that has been removed from the :func:`eval` namespace.

    The complete list of *available* built-ins varies between Python versions
    (e.g. :func:`callable` was removed in Python 3.0 but added back in Python
    3.2).

    The docstring for the ``aglyph.context.XMLContext._parse_eval()``
    method has more details:

    .. automethod:: aglyph.context.XMLContext._parse_eval

.. note::

    It is not necessary to use :func:`eval` when creating a context
    programmatically, as any built-in type or function can be used freely.

    The example given above, using programmatic configuration, could be
    simplified as follows::

        binder.bind(Thing).init(fruits=frozenset(
            ["Apple", "Orange", "Banana", "Pear"])

    Because a :class:`frozenset` is immutable, there is no need to use a
    :func:`functools.partial` or an :class:`aglyph.component.Evaluator`. But if
    the example were using a mutable :class:`set`, for example, then a
    :func:`functools.partial` or an :class:`aglyph.component.Evaluator` may
    be appropriate.

Exploit the flexibility of a ``Reference``
------------------------------------------

An :class:`aglyph.component.Reference` is a powerful mechanism for creating
cross-references between components.

A ``Reference`` value is just a component ID, but a ``Reference`` triggers
special behavior within an :class:`aglyph.assembler.Assembler` or
:class:`aglyph.component.Evaluator` when it is encountered during assembly or
evaluation (respectively): wherever the ``Reference`` appears, it will be
automatically replaced with the fully-assembled component it identifies.

In most cases, a ``Reference`` will be used as an initialization argument or
attribute value:

In XML::

    <component id="an-object" dotted-name="builtins.object"/>
    <component id="cookbook.ReferenceExample">
        <init>
            <arg reference"an-object"/>
        </init>
    </component>

In pure Python::

    binder.bind("an-object", object)
    binder.bind("cookbook.ReferenceExample").init(Reference("an-object"))

When using :class:`aglyph.binder.Binder` for programmatic configuration, a
"shortcut" is also available if you are binding by class or function::

    binder.bind(Service, ServiceImpl)
    binder.bind(Provider).init(Service)

In this case, assuming that ``Service`` is in the "cookbook" module, Aglyph
treats ``init(Service)`` the same as ``init(Reference("cookbook.Service"))``.

A ``Reference`` may be used in *any* of the following places, allowing for
extremely flexible configurations:

* an initialization argument value (positional or keyword) for an
  :class:`aglyph.component.Component` or an :class:`aglyph.component.Evaluator`
* an attribute value for an :class:`aglyph.component.Component`
* a key and/or value of a mapping type
* an item of a non-mapping sequence type

In a nutshell: an :class:`aglyph.component.Reference` may be used in *any*
case where a value is being defined, and will be replaced at assembly-time by
the fully-assembled component identified by that reference.

Be careful with ``<eval>``, ``functools.partial``, ``Evaluator``, and ``Reference``
-----------------------------------------------------------------------------------

An XML ``<eval>`` element (which is translated into a :func:`functools.partial`
that calls :func:`eval`), a user-created :func:`functools.partial`, an
:class:`aglyph.component.Evaluator`, and an :class:`aglyph.component.Reference`
all share one common characteristic: **these constructs do not resolve to their
actual values until assembly-time.**

It is crucial to understand this when using these constructs as values in
cases where Python requires a *hashable* type (i.e. an object that implements
the ``__hash__`` protocol). This includes, but is not limited to:

* keys of a :class:`dict` (or any other mapping type)
* items of a :class:`set` or :class:`frozenset`

In these cases, the construct **must** resolve to a *hashable* object, or
Python will raise ``TypeError`` at assembly time. 

Respect Unicode and character encodings in XML configuration
------------------------------------------------------------

Aglyph properly handles Unicode text and encoded-bytes data in XML
configuration files, and can provide your application components with the
correct type (regardless of Python version) on assembly.

Consider the following example::

    <?xml version="1.0" encoding="utf-8"?>
    <context id="cookbook">
        <component id="cookbook.TextAndData">
            <attributes>
                <attribute name="text">
                    <unicode>ΑΦΔ</unicode>
                </attribute>
                <attribute name="data1">
                    <str encoding="utf-8">ΑΦΔ</str>
                </attribute>
                <attribute name="data2">
                    <str encoding="iso-8859-7">ΑΦΔ</str>
                </attribute>
            </attributes>
        </component>
    </context>

When this component is assembled, the ``text`` attribute will be a Unicode
string (:func:`unicode`), and the ``data1`` and ``data2`` attributes will be
encoded bytes (:func:`str`) in the UTF-8 and ISO-8859-7 character sets,
respectively::

    >>> obj = assembler.assemble("cookbook.TextAndData")
    >>> obj.text
    u'\u0391\u03a6\u0394'
    >>> obj.data1
    '\xce\x91\xce\xa6\xce\x94'
    >>> obj.data2
    '\xc1\xd6\xc4'

Differences between Python 2 and Python 3
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The built-in :func:`str` type has changed significantly between Python 2 and
Python 3 (see `Text Vs. Data Instead Of Unicode Vs. 8-bit
<http://docs.python.org/release/3.0/whatsnew/3.0.html#text-vs-data-instead-of-unicode-vs-8-bit>`_).

In short: :func:`str` represented encoded byte data up to and including
Python 2, but representes *Unicode text* as of Python 3.0.

A simple table illustrates the difference in types between Python 2 and 3:

+----------+-------------------+-------------------+
| Version  |    Unicode text   | Encoded byte data |
+==========+===================+===================+
| Python 2 |    ``unicode``    |      ``str``      |
+----------+-------------------+-------------------+
| Python 3 |      ``str``      |     ``bytes``     |
+----------+-------------------+-------------------+

The :download:`Aglyph 1.0.0 context DTD
<../../resources/aglyph-context-1.0.0.dtd>` defines ``<bytes>``, ``<str>``,
and ``<unicode>`` elements that correspond to the types in the table above, but
treats the element content differently depending on the version of Python in
which Aglyph is running:

.. rubric:: Python 2

``<bytes[ encoding="..."]>...</bytes>``
    Element content is returned as a Python 2 :func:`str` encoded byte string
    (identical to ``<str>``)

``<str[ encoding="..."]>...</str>``
    Element content is returned as a Python 2 :func:`str` encoded byte string

``<unicode>...</unicode>``
    Element content is returned as a Python 2 :func:`unicode` Unicode string

.. rubric:: Python 3

``<bytes[ encoding="..."]>...</bytes>``
    Element content is returned as a Python 3 ``bytes`` encoded byte object

``<str>...</str>``
    Element content is returned as a Python 3 ``str`` Unicode string

    .. warning::

        Althoug the DTD permits an *encoding="..."* attribute on ``<str>``
        elements, the attribute is **ignored** in Python 3 (a *WARNING*-level
        log message is generated if it is present)

``<unicode>...</unicode>``
    Element content is returned as a Python 3 ``str`` Unicode string (identical
    to ``<str>``

To summarize the above:

* ``<bytes>`` is interpreted as a ``str`` type in Python 2 and a ``bytes`` type
  in Python 3
* ``<str>`` is always interpreted as a ``str`` type
* ``<unicode>`` is interpreted as a ``unicode`` type in Python 2 and a ``str``
  type in Python 3

.. note::

    For clarity in XML context documents, it is always safe to use ``<bytes>``
    for encoded byte data and ``<unicode>`` for Unicode text (regardless of
    Python version), avoiding entirely the ambiguity of ``<str>``.

Avoid circular dependencies
---------------------------

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

Protect injected dependencies from being modified by reference
--------------------------------------------------------------

Consider the following component (configured programmatically)::

    binder.bind(Thing).attributes(mutable=[1, 2, 3])

If this component is assembled, and the ``mutable`` attribute is modified, that
change will persist in the component definition::

    >>> thing = binder.lookup(Thing)
    >>> thing.mutable
    [1, 2, 3]
    >>> thing.mutable.append(4)
    >>> thing.mutable
    [1, 2, 3, 4]
    >>> another = binder.lookup(Thing)
    >>> another.mutable
    [1, 2, 3, 4]

It is likely that this is *not* desired behavior. To protect against
modify-by-reference, use a :func:`functools.partial` **if** the value does not
contain nested ``Reference`` ``Evaluator`` objects; otherwise, use an
:class:`aglyph.component.Evaluator`::

    binder.bind(Thing).attributes(mutable=functools.partial(list, [1, 2, 3]))
    thing_ref = Reference(format_dotted_name(Thing))
    binder.bind(Other).attributes(field=Evaluator(tuple, [None, thing_ref]))

Now the ``mutable`` attribute can still be modified on an instance of
``Thing``, but newly-assembled instances will always have the value specified
in the component definition. And looking up an instance of ``Other`` will
correctly assemble the nested reference to ``Thing``.

    >>> thing = binder.lookup(Thing)
    >>> thing.mutable
    [1, 2, 3]
    >>> thing.mutable.append(4)
    >>> thing.mutable
    [1, 2, 3, 4]
    >>> another = binder.lookup(Thing)
    >>> another.mutable
    [1, 2, 3]
    >>> other = binder.lookup(Other)
    >>> isinstance(other.field, Thing)
    True

An interesting twist on the first example given above::

    binder.bind(Thing, strategy="singleton").attributes(
        mutable=functools.partial(list, [1, 2, 3]))

Because the component is now a singleton, a change to ``mutable`` that persists
is now *correct* behavior (the same holds true if the assembly strategy had
been "borg").

.. note::
    When using XML configuration, a ``<list>`` or ``<dict>``
    dependency, or a ``<tuple>`` dependency with one or more items, is
    **automatically** defined as an :class:`aglyph.component.Evaluator`.
    Pure-Python configuration does not have the benefit of this
    automatic behavior.

Write wrappers for objects that are not created by importable classes or functions
----------------------------------------------------------------------------------

There are several object creation cases that Aglyph does **not** directly
support:

#. obtaining an object by using a *@staticmethod* or *@classmethod*
#. creating an object of an "inner class"
#. obtaining an object by calling an instance (bound) method of a class, or
   directly accessing an instance member

Example::

    class Spam(object):

        # case 1
        @staticmethod
        def get_instance(...):
            ...

        # case 1
        @classmethod
        def create(cls, ...):
            ...

        # case 2
        class Eggs(object):
            ...

        def __init__(self, ...):
            # case 3
            self.thing = ...

        # case 3
        def acquire_something(self, ...):
            ...

However, there are times when you can't avoid these cases (e.g. you're using a
3rd-party library). In this case, you can create "wrapper" functions::

    def get_spam_instance(...):
        return Spam.get_instance(...)

    def get_spam_eggs(...):
        return Spam.Eggs(...)

    def create_spam(...):
        return Spam.create(...)

    def get_thing_from_spam(...):
        return Spam(...).eggs

    def get_something_from_spam(...):
        return Spam(...).acquire_something(...)

There's no need to use these functions in your application proper; they're
simply conveniences for Aglyph. It is recommended that you place them into a
separate module (if you're using programmatic configuration, the module where
your :class:`aglyph.binder.Binder` is defined is a logical choice). This way,
you can define components and injection dependencies for the importable
functions. For example::

    binder.bind(get_spam_instance).init(...).attributes(...)
    binder.bind("eggs", get_spam_eggs).init(...).attributes(...)
    ...
