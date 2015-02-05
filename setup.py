# -*- coding: UTF-8 -*-

# workaround for setuptools/logging/multiprocessing bug
# (see http://bugs.python.org/issue15881#msg170215)
try:
    import multiprocessing
except ImportError:
    pass

from setuptools import setup

setup(name="Aglyph",
      version="2.1.0",
      description="Aglyph is a Dependency Injection framework for Python "
                  "2.7+, supporting type 2 (setter) and type 3 (constructor) "
                  "injection.",
      long_description="""\
Aglyph is a Dependency Injection framework for Python 2.7+, supporting
type 2 (setter) and type 3 (constructor) injection.

Aglyph runs on CPython (http://www.python.org/) 2.7 and 3.1 - 3.4, and on
recent versions of the PyPy (http://pypy.org/>),
Jython (http://www.jython.org/), IronPython (http://ironpython.net/),
and Stackless Python (http://www.stackless.com/) variants.

Aglyph can assemble "prototype" components (a new instance is created
every time), "singleton" components (the same instance is returned every
time), "borg" components (a new instance is created every time, but all
instances of the same class share the same internal state), and "weakref"
components (the same instance is returned as long as there is at least one
"live" reference to the instance in the running application).

Aglyph can be configured using a declarative XML syntax, or
programmatically in pure Python.
""",
    author="Matthew Zipay",
    author_email="mattz@ninthtest.net",
    url="http://www.ninthtest.net/aglyph-python-dependency-injection/",
    download_url="http://sourceforge.net/projects/aglyph/files/aglyph/",
    packages=["aglyph", "aglyph.compat", "aglyph.integration"],
    test_suite="test",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules"],
    license="MIT License",
    keywords=["dependency injection", "inversion of control", "DI", "IoC",
              "service locator"])

