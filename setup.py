from distutils.core import setup

setup(name="Aglyph",
      version="1.1.0",
      description="Aglyph is a Dependency Injection framework for Python "
                  "2.5+, supporting type 2 (setter) and type 3 (constructor) "
                  "injection.",
      long_description="""\
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
""",
    author="Matthew Zipay",
    author_email="mattz@ninthtest.net",
    url="http://www.ninthtest.net/aglyph-python-dependency-injection/",
    download_url = "http://sourceforge.net/projects/aglyph/files/aglyph/",
    packages=["aglyph", "aglyph.compat"],
    package_dir = {"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.0",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules"],
    license="MIT License",
    keywords=["dependency injection", "inversion of control", "DI", "IoC",
              "service locator"])
