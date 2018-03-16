# -*- coding: UTF-8 -*-

from setuptools import setup

setup(
    name="Aglyph",
    version="3.0.0",
    description=
        "Aglyph is a Dependency Injection framework for Python.",
    long_description="""\
+ supports type 2 (setter) and type 3 (constructor) dependency injection
+ can assemble prototype, singleton, borg, and weakref components
+ supports templates (i.e. component inheritance) and lifecycle methods
+ works with any kind of object creation pattern you'll encounter (constructor, factory function/method, attribute/property access, import)
+ configured declaratively, either programmatically through a fluent API or using a simple XML syntax
+ non-intrusive wiring style does not require modification of any existing sources (no decorators, no naming conventions, no syntactic "magic" needed)
+ can inject not only 3rd-party dependencies, but also dependents (even Java/.NET classes under Jython/IronPython)
+ runs on Python 2.7 and 3.4+ using the same codebase
+ proactively tested on CPython, Jython, IronPython, PyPy and Stackless Python
+ fully logged and traced for easy troubleshooting (note: tracing is disabled by default, and can be activated by setting an environment variable)
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

