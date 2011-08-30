==========================================
Aglyph --- Dependency Injection for Python
==========================================

:Release: |version|

Aglyph is a Dependency Injection framework for Python 2.5+, supporting type 2
(setter) and type 3 (constructor) injection.

Aglyph runs on `CPython <http://www.python.org/>`_ 2.5, 2.6, 2.7, 3.0, 3.1, and
3.2; and on recent versions of the `PyPy <http://pypy.org/>`_,
`Jython <http://www.jython.org/>`_, `IronPython <http://ironpython.net/>`_, and
`Stackless Python <http://www.stackless.com/>`_ variants. See :doc:`testing`
for a complete list of the Python versions and variants on which Aglyph has
been tested.

Aglyph can assemble *prototype* components (a new instance is created every
time), *singleton* components (the same instance is returned every time), and
*borg* components (a new instance is created every time, but all instances of
the same class share the same internal state).

Aglyph can be configured using a declarative XML syntax, or programmatically in
pure Python.

Aglyph is not a "full stack;" only dependency injection support is
provided.

Aglyph does not support type 1 (interface) dependency injection at this
time.

Table of Contents
-----------------

.. toctree::
    :maxdepth: 2

    get-started
    api-ref
    cookbook
    testing

Quick glimpse
-------------

Here is a quick glimpse of how Aglyph is configured and used.

XML configuration
^^^^^^^^^^^^^^^^^

XML configuration follows the document structure described in the
:download:`aglyph-context-1.0.0 DTD <../../resources/aglyph-context-1.0.0.dtd>`
(included in the *resources/* directory of the distribution)::

    <?xml version="1.0" encoding="utf-8"?>
    <context id="quick-glimpse">
        <component id="http.client.HTTPConnection">
            <init>
                <arg><str>www.ninthtest.net</str></arg>
                <arg><int>80</int></arg>
            </init>
        </component>
    </context>

Programmatic configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^

Programmatic configuration is in pure Python, using Aglyph API classes
directly::

    from aglyph.component import Component
    from aglyph.context import Context


    class QuickGlimpseContext(Context):

        def __init__(self):
            super(QuickGlimpseContext, self).__init__("quick-glimpse")
            component = Component("http.client.HTTPConnection")
            component.init_args.append("www.ninthtest.net")
            component.init_args.append(80)
            self.add(component)

Usage
^^^^^

An assembler knows how to create objects from an XML context::

    from aglyph.assembler import Assembler
    from aglyph.context import XMLContext

    assembler = Assembler(XMLContext("quick-glimpse-context.xml"))
    conx = assembler.assemble("http.client.HTTPConnection")

.. warning::

    *IronPython* developers must use an additional class when parsing a context
    from XML, due to the *expat* XML parser being unavailable::

        from aglyph.assembler import Assembler
        from aglyph.compat.ipyetree import XmlReaderTreeBuilder
        from aglyph.context import XMLContext
    
        assembler = Assembler(XMLContext("quick-glimpse-context.xml",
                                         parser=XmlReaderTreeBuilder()))
        conx = assembler.assemble("http.client.HTTPConnection")

    See :mod:`aglyph.compat.ipyetree` for details.

Or from a pure Python context::

    from aglyph.assembler import Assembler
    from quickglimpse import QuickGlimpseContext

    assembler = Assembler(QuickGlimpseContext())
    conx = assembler.assemble("http.client.HTTPConnection")

Download
--------

Download the latest :mod:`distutils` source or built distribution of
`Aglyph on SourceForge <http://sourceforge.net/projects/aglyph/files/aglyph/1.0.0/>`_.

Clone the
`Aglyph Mercurial repository from BitBucket <https://bitbucket.org/mzipay/aglyph>`_.

See :doc:`testing`
for a complete list of the Python versions and variants on which Aglyph has
been tested.

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. seealso::

   `Inversion of Control Containers and the Dependency Injection pattern <http://martinfowler.com/articles/injection.html>`_
      The definitive introduction to Dependency Injection

   `Python Dependency Injection [PDF] <http://www.aleax.it/yt_pydi.pdf>`_
      Alex Martelli's introduction to Dependency Injection (and alternatives) in Python
