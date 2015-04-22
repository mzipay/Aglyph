# Aglyph - Dependency Injection for Python

http://ninthtest.net/aglyph-python-dependency-injection/

[![Latest Version](https://pypip.in/version/Aglyph/badge.svg?text=version)](https://pypi.python.org/pypi/Aglyph/)
[![Supported Python versions](https://pypip.in/py_versions/Aglyph/badge.svg)](https://pypi.python.org/pypi/Aglyph/)
[![Supported Python implementations](https://pypip.in/implementation/Aglyph/badge.svg)](https://pypi.python.org/pypi/Aglyph/)
[![License](https://pypip.in/license/Aglyph/badge.svg)](https://pypi.python.org/pypi/Aglyph/)

## Introduction

Aglyph is a Dependency Injection framework for Python that...

* is non-obtrusive (no dependencies beyond the Python standard library; no need
  to decorate your existing sources or adhere to any specific style
  conventions)
* can inject even 3rd-party dependencies **and dependents**
* supports both constructor and setter injection
* can assemble *prototype*, *singleton*, *borg*, and *weakref* components
* is configurable in declarative style, either programmatically or using an XML
  syntax (a
  [commented DTD](https://github.com/mzipay/Aglyph/blob/master/resources/aglyph-context.dtd)
  is provided, though configuration is not validated by default)
* supports templates (i.e. component inheritance) and lifecycle methods
* runs on Python 2 and 3 (same codebase)
* runs (and is proactively tested) on [CPython](http://www.python.org/),
  [Jython](http://www.jython.org/), [IronPython](http://ironpython.net/),
  [PyPy](http://pypy.org/>), and [Stackless Python](http://www.stackless.com/)

## Installation

[![Wheel Status](https://pypip.in/wheel/Aglyph/badge.svg)](https://pypi.python.org/pypi/Aglyph/)

The easiest way to install Aglyph is to use [pip](https://pip.pypa.io/):

```bash
$ pip install Aglyph
```

Alternative source and binary installation options are described below.

To verify that an installation was successful:

```python
>>> import aglyph
>>> aglyph.__version__
'2.1.0'
```

### Source installation

Clone or fork the repository:

```bash
$ git clone https://github.com/mzipay/Aglyph.git
```

Alternatively, download and extract a source _.zip_ or _.tar.gz_ archive from
https://github.com/mzipay/Aglyph/releases or https://pypi.python.org/pypi/Aglyph.

Run the test suite and install the `aglyph` package:

```bash
$ cd Aglyph
$ python setup.py test
$ python setup.py install
```

### Binary installation

Download the Python wheel (_.whl_) or _.egg_ from
https://pypi.python.org/pypi/Aglyph, or an _.exe_/_.msi_ Windows installer from
https://sourceforge.net/projects/aglyph/files/.

Use [pip](https://pip.pypa.io/) or
[wheel](https://pypi.python.org/pypi/wheel) to install the _.whl_;
[setuptools](https://pypi.python.org/pypi/setuptools) to install an
_.egg_; or run the Windows installer.

