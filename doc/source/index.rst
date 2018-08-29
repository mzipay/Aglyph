==========================================
Aglyph --- Dependency Injection for Python
==========================================

:Release: |release|

.. image:: https://img.shields.io/pypi/v/Aglyph.svg
   :alt: Aglyph PyPI version
   :target: https://pypi.python.org/pypi/Aglyph

.. image:: https://img.shields.io/pypi/pyversions/Aglyph.svg
   :alt: Aglyph supported Python version
   :target: https://www.python.org/downloads/

.. image:: https://img.shields.io/pypi/implementation/Aglyph.svg
   :alt: Aglyph supported Python implementation
   :target: http://docs.python-guide.org/en/latest/starting/which-python/#implementations

.. image:: https://img.shields.io/pypi/l/Aglyph.svg
   :alt: Aglyph License
   :target: https://github.com/mzipay/Aglyph/blob/master/LICENSE.txt

.. image:: https://img.shields.io/pypi/wheel/Aglyph.svg
   :alt: Aglyph Wheel availability
   :target: https://pypi.python.org/pypi/Aglyph

.. _CPython: https://www.python.org/
.. _PyPy: http://pypy.org/
.. _Jython: http://www.jython.org/
.. _IronPython: http://ironpython.net/
.. _Stackless Python: https://github.com/stackless-dev/stackless/wiki
.. _Inversion of Control Containers and the Dependency Injection pattern: https://martinfowler.com/articles/injection.html
.. _Python Dependency Injection [PDF]: http://www.aleax.it/yt_pydi.pdf
.. _Semantic Versioning (SemVer): https://semver.org/

Aglyph is a Dependency Injection framework for Python, supporting type 2
(setter) and type 3 (constructor) injection.

Aglyph runs on `CPython`_ 2.7 and 3.4+, and on recent versions of the `PyPy`_,
`Jython`_, `IronPython`_, and `Stackless Python`_ variants. See :doc:`testing`
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
   context-fluent-api
   testing
   roadmap

.. seealso::

   `Inversion of Control Containers and the Dependency Injection pattern`_
      The definitive introduction to Dependency Injection

   `Python Dependency Injection [PDF]`_
      Alex Martelli's introduction to Dependency Injection (and alternatives)
      in Python

Aglyph versioning
-----------------

Aglyph follows :pep:`440` for versioning and maintains
`Semantic Versioning (SemVer)`_ compatibility.

The Aglyph version is always defined as the ``__version__`` member of the
``aglyph/__init__.py`` module:

>>> import aglyph
>>> aglyph.__version__
'3.0.0.post1'

The :download:`Aglyph context DTD <../../resources/aglyph-context.dtd>`
includes the Aglyph version in the filename and in a header comment.

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

