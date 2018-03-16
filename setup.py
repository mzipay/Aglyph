# -*- coding: UTF-8 -*-

from setuptools import setup

setup(
    name="Aglyph",
    version="3.0.0",
    description=
        "Aglyph is a Dependency Injection framework for Python.",
    long_description="""\
* supports type 2 (setter) and type 3 (constructor) dependency injection
* can assemble *prototype*, *singleton*, *borg*, and *weakref* components
* supports templates (i.e. component inheritance) and lifecycle methods
* works with any kind of object creation pattern you'll encounter:
  * constructor
  * factory function or method
  * object creation hidden behind attribute or property access
* is configured declaratively, either programmatically through a fluent API or
  using a simple XML syntax (see the `Aglyph DTD
  <https://github.com/mzipay/Aglyph/blob/master/resources/aglyph-context.dtd>`_)
* is non-intrusive:
  * only one dependency (`Autologging
    <http://ninthtest.info/python-autologging/>`_) beyond the Python standard
    library
  * does not require modification of existing source code (i.e. no
    decorators, specific naming conventions, or any other kind of
    syntactic "magic" necessary)
* can inject not only 3rd-party dependencies, but also **dependents**
* runs on Python 2.7 and 3.4+ using the same codebase
* is proactively tested on `CPython <https://www.python.org/>`_,
  `Jython <http://www.jython.org/>`_, `IronPython <http://ironpython.net/>`_,
  `PyPy <http://pypy.org/>`_, and
  `Stackless Python <https://bitbucket.org/stackless-dev/stackless/wiki/Home>`_
* is fully logged *and traced* for ease of troubleshooting (note: tracing is
  disabled by default, and can be activated by setting an environment variable)
""",
    author="Matthew Zipay",
    author_email="mattz@ninthtest.info",
    url="http://ninthtest.info/aglyph-python-dependency-injection/",
    download_url="http://sourceforge.net/projects/aglyph/files/",
    packages=[
        "aglyph",
        "aglyph.integration",
    ],
    install_requires=[
        "Autologging>=1.1.0",
    ],
    test_suite="test.suite",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: CherryPy",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: IronPython",
        "Programming Language :: Python :: Implementation :: Jython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Programming Language :: Python :: Implementation :: Stackless",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    license="MIT License",
    keywords=[
        "dependency injection",
        "DI",
        "inversion of control",
        "IoC",
        "service locator"
    ]
)

