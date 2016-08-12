# Aglyph - Dependency Injection for Python

http://ninthtest.net/aglyph-python-dependency-injection/

[![PyPI version](https://img.shields.io/pypi/v/Aglyph.svg)](https://pypi.python.org/pypi/Aglyph)
![Python version](https://img.shields.io/pypi/pyversions/Aglyph.svg)
![Python implementation](https://img.shields.io/pypi/implementation/Aglyph.svg)
![License](https://img.shields.io/pypi/l/Aglyph.svg)
[![Wheel availability](https://img.shields.io/pypi/wheel/Aglyph.svg)](https://pypi.python.org/pypi/Aglyph)

## Introduction

Aglyph is a Dependency Injection framework for Python that...

* supports type 2 (setter) and type 3 (constructor) dependency injection
* can assemble *prototype*, *singleton*, *borg*, and *weakref* components
* supports templates (i.e. component inheritance) and lifecycle methods
* works with any kind of object creation pattern you'll encounter:
  * constructor
  * factory function or method
  * object creation hidden behind attribute or property access
* is configured declaratively, either programmatically through a fluent API or
  using a simple XML syntax (see the [Aglyph DTD](
  https://github.com/mzipay/Aglyph/blob/master/resources/aglyph-context.dtd))
* is non-intrusive:
  * only one dependency ([Autologging](
    http://ninthtest.net/python-autologging/)) beyond the Python standard
    library
  * does not require modification of existing source code (i.e. no
    decorators, specific naming conventions, or any other kind of
    syntactic "magic" necessary)
* can inject not only 3rd-party dependencies, but also **dependents**
* runs on Python 2.7 and 3.3+ using the same codebase
* is proactively tested on [CPython](https://www.python.org/),
  [Jython](http://www.jython.org/), [IronPython](http://ironpython.net/),
  [PyPy](http://pypy.org/>), and
  [Stackless Python](https://bitbucket.org/stackless-dev/stackless/wiki/Home)
* is fully logged *and traced* for ease of troubleshooting (note: tracing is
  disabled by default, and can be activated by setting an environment variable)

## Installation

The easiest way to install Aglyph is to use [pip](https://pip.pypa.io/):

```bash
$ pip install Aglyph
```

Alternative source and binary installation options are described below.

To verify that an installation was successful:

```python
>>> import aglyph
>>> aglyph.__version__
'3.0.0'
```

### Source installation

Clone or fork the repository:

```bash
$ git clone https://github.com/mzipay/Aglyph.git
```

Alternatively, download and extract a source _.zip_ or _.tar.gz_ archive
from https://github.com/mzipay/Aglyph/releases,
https://pypi.python.org/pypi/Aglyph/ or
https://sourceforge.net/projects/aglyph/files/aglyph/.

Run the test suite and install the `aglyph` package:

```bash
$ cd Aglyph
$ python setup.py test
$ python setup.py install
```

### Binary installation

Download the Python wheel (_.whl_) or _.exe_/_.msi_ Windows installer
from https://pypi.python.org/pypi/Aglyph/ or
https://sourceforge.net/projects/aglyph/files/aglyph/.

Use [pip](https://pip.pypa.io/) or
[wheel](https://pypi.python.org/pypi/wheel) to install the _.whl_, or
run the Windows installer.

