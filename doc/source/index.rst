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

Table of Contents
-----------------

.. toctree::
    :maxdepth: 2

    get-started
    api-ref
    cookbook
    testing

.. seealso::

   `Inversion of Control Containers and the Dependency Injection pattern <http://martinfowler.com/articles/injection.html>`_
      The definitive introduction to Dependency Injection

   `Python Dependency Injection [PDF] <http://www.aleax.it/yt_pydi.pdf>`_
      Alex Martelli's introduction to Dependency Injection (and alternatives)
      in Python

Download
--------

Download the latest :mod:`distutils` source or built distribution of `Aglyph on
SourceForge <http://sourceforge.net/projects/aglyph/files/aglyph/>`_.

Clone the
`Aglyph Mercurial repository from BitBucket
<https://bitbucket.org/mzipay/aglyph>`_.

See :doc:`testing`
for a complete list of the Python versions and variants on which Aglyph has
been tested.

Aglyph versioning
^^^^^^^^^^^^^^^^^

The Aglyph version is always defined as the ``__version__`` member of the
``aglyph/__init__.py`` module:

>>> import aglyph
>>> aglyph.__version__
'1.1.0'

The :download:`Aglyph context DTD <../../resources/aglyph-context-1.0.0.dtd>`
includes the version in the filename and in a header comment. This version
represents the most recent Aglyph version in which the DTD *itself* was
changed.

Aglyph increments its MAJOR.MINOR.MICRO version (i.e. ``aglyph.__version__``)
as follows:

* A transparent (non-public) API change increments the MICRO version.
* A backwards-compatible *public* API change increments the MINOR version.
* Any *non-backwards-compatible* API change increments the MAJOR version.

As a result of this approach:

* You can always upgrade/downgrade to a higher/lower MICRO version, assuming
  MAJOR and MINOR are the same.
* You can always upgrade to a higher MINOR version, assuming MAJOR is the same.
* Downgrading to a lower MINOR version (assuming MAJOR is the same) **may**
  require application and/or configuration changes (for example, if you took
  advantage of a new feature that is not available in the lower version).
* Upgrading/downgrading to a higher/lower MAJOR version will **always** require
  application and/or configuration changes.

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
