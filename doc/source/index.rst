==========================================
Aglyph --- Dependency Injection for Python
==========================================

:Release: |release|

Aglyph is a Dependency Injection framework for Python, supporting type 2
(setter) and type 3 (constructor) injection.

Aglyph runs on `CPython <http://www.python.org/>`_ 2.7 and 3.3+, and on
recent versions of the `PyPy <http://pypy.org/>`_,
`Jython <http://www.jython.org/>`_, `IronPython <http://ironpython.net/>`_, and
`Stackless Python <http://www.stackless.com/>`_ variants. See :doc:`testing`
for a complete list of the Python versions and variants on which Aglyph has
been tested.

Aglyph can assemble *prototype* components (a new instance is created every
time), *singleton* components (the same instance is returned every time),
*borg* components (a new instance is created every time, but all instances of
the same class share the same internal state), and *weakref* components (the
same instance is returned as long as there is at least one "live" reference to
that instance in the application).

Aglyph can be configured using a declarative XML syntax, or programmatically in
pure Python.

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2

   whats-new
   get-started
   cookbook
   api-ref
   testing
   roadmap

.. seealso::

   `Inversion of Control Containers and the Dependency Injection pattern <http://martinfowler.com/articles/injection.html>`_
      The definitive introduction to Dependency Injection

   `Python Dependency Injection [PDF] <http://www.aleax.it/yt_pydi.pdf>`_
      Alex Martelli's introduction to Dependency Injection (and alternatives)
      in Python

Aglyph versioning
-----------------

Aglyph follows the
`Semantic Versioning Specification (SemVer) <http://semver.org/>`_.

The Aglyph version is always defined as the ``__version__`` member of the
``aglyph/__init__.py`` module:

>>> import aglyph
>>> aglyph.__version__
'2.1.1'

The :download:`Aglyph context DTD <../../resources/aglyph-context.dtd>`
includes the Aglyph version in the filename and in a header comment.

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

