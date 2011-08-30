========================================================================
SECTIONS
========================================================================

* INTRODUCTION
* DOWNLOAD
* INSTALLATION

========================================================================
INTRODUCTION
========================================================================

HOMEPAGE: http://www.ninthtest.net/aglyph-python-dependency-injection/
AUTHOR: Matthew Zipay <mattz@ninthtest.net>
LICENSE: MIT License (see the LICENSE.txt file)

Aglyph is a Dependency Injection framework for Python 2.5+, supporting
type 2 (setter) and type 3 (constructor) injection.

Aglyph runs on CPython (http://www.python.org/) 2.5, 2.6, 2.7, 3.0, 3.1,
and 3.2; and on recent versions of the PyPy (http://pypy.org/>),
Jython (http://www.jython.org/), IronPython (http://ironpython.net/),
and Stackless Python (http://www.stackless.com/) variants.

Aglyph can assemble "prototype" components (a new instance is created
every time), "singleton" components (the same instance is returned every
time), and "borg" components (a new instance is created every time, but
all instances of the same class share the same internal state).

Aglyph can be configured using a declarative XML syntax, or
programmatically in pure Python.

Aglyph is not a "full stack;" only dependency injection support is
provided.

Aglyph does not support type 1 (interface) dependency injection at this
time.

For the definitive introduction to the Dependency Injection pattern,
please read Martin Fowler's article "Inversion of Control Containers and
the Dependency Injection pattern"
(http://martinfowler.com/articles/injection.html).

For a brief overview of Dependency Injection in Python (including a
discussion of alternatives), please read Alex Martelli's article "Python
Dependency Injection" (http://www.aleax.it/yt_pydi.pdf).

========================================================================
DOWNLOAD
========================================================================

Aglyph is packaged and distributed using the standard 'distutils'
module. Download the latest version from:

    http://sourceforge.net/projects/aglyph/files/aglyph/

Both source and built distributions are available from SourceForge.

The source is also available as a cloneable Mercurial repository on
BitBucket:

    https://bitbucket.org/mzipay/aglyph

========================================================================
INSTALLATION
========================================================================

Once you have acquired the latest Aglyph distribution, follow these
instructions to install Aglyph:

If you downloaded a source distribution from SourceForge:

(1) Extract the archive to a temporary location.
(2) Navigate to the "Aglyph" directory in the temporary location.
(3) Run "python setup.py install".

If you downloaded a built distribution from SourceForge, install it
using the appropriate platform-specific tool.

If you cloned the repository from BitBucket, follow these instructions
to install Aglyph:

(1) Navigate to the "Aglyph" directory in your local repository.
(2) Run "python setup.py install".

Verify that the installation was successful by importing the 'aglyph'
module from a Python interpreter:

>>> import aglyph
