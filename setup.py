# -*- coding: UTF-8 -*-

from setuptools import setup

with open("README.md") as f:
    long_description = f.read()

with open("requirements.txt") as f:
    requirements = [line.strip() for line in f]

setup(
    name="Aglyph",
    version="3.0.0.post1",
    description=
        "Aglyph is a Dependency Injection framework for Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Matthew Zipay",
    author_email="mattz@ninthtest.info",
    url="http://ninthtest.info/aglyph-python-dependency-injection/",
    download_url="http://sourceforge.net/projects/aglyph/files/",
    packages=[
        "aglyph",
        "aglyph.integration",
    ],
    install_requires=requirements,
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
        "Programming Language :: Python :: 3.7",
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

