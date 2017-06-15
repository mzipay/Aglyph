# -*- coding: UTF-8 -*-

# Copyright (c) 2006, 2011, 2013-2017 Matthew Zipay.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

"""Utilities and common setup for all unit test modules."""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

from inspect import getsourcefile
import logging
import logging.config
import os
import unittest

from aglyph._compat import is_python_3

# always force tracing when running test suite
os.environ["AUTOLOGGING_TRACED_NOOP"] = ""
os.environ["AGLYPH_TRACED"] = "1"

from autologging import TRACE

__all__ = [
    "as_encoded_bytes",
    "as_unicode_text",
    "assertRaisesWithMessage",
    "find_basename",
    "suite",
]


#PYVER: can use TestCase.assertRaises as a context manager in 3.1+
def assertRaisesWithMessage(
        test_case, e_expected, callable_, *args, **keywords):
    """Assert that *callable_* raises a specific exception, whose type
    and message must match those of *e_expected*.

    """
    try:
        callable_(*args, **keywords)
    except type(e_expected) as e_actual:
        test_case.assertEqual(str(e_expected), str(e_actual))
    else:
        test_case.fail("did not raise %r" % e_expected)


def as_encoded_bytes(s, to_encoding):
    """Return *s* as encoded byte data.

    The string *s* should be defined in a test module as a UTF-8
    string literal.

    """
    return (
        s.encode(to_encoding) if is_python_3 else
        s.decode("utf-8").encode(to_encoding))


def as_unicode_text(s):
    """Return *s* as unicode text.

    The string *s* should be defined in a test module as a UTF-8
    string literal.

    """
    return s if is_python_3 else s.decode("utf-8")


def find_basename(basename):
    """Locate *basename* relative to the ``test`` package."""
    init_filename = getsourcefile(find_basename)
    return os.path.join(os.path.dirname(init_filename), basename)


def suite():
    from test import (
        # aglyph
        test_format_dotted_name,
        test_identify,
        test_importable,
        test_resolve_dotted_name,
        # aglyph._compat
        test_compat,
        test_is_string,
        test_name_of,
        test_new_instance,
        test_DoctypeTreeBuilder,
        test_CLRXMLParser,
        test_AglyphDefaultXMLParser,
        # aglyph.component
        test_Reference,
        test_InitializationSupport,
        test_Evaluator,
        test_DependencySupport,
        test_Template,
        test_Component,
        # aglyph.context
        test_CreationBuilderMixin,
        test_InjectionBuilderMixin,
        test_LifecycleBuilderMixin,
        test_RegistrationMixin,
        test_Context,
        test_XMLContext,
        # aglyph.assembler
        test_ReentrantMutexCache,
        test_Assembler,
    )

    suite = unittest.TestSuite()

    # aglyph
    suite.addTest(test_importable.suite())
    suite.addTest(test_format_dotted_name.suite())
    suite.addTest(test_resolve_dotted_name.suite())
    suite.addTest(test_identify.suite())
    # aglyph._compat
    suite.addTest(test_compat.suite())
    suite.addTest(test_is_string.suite())
    suite.addTest(test_name_of.suite())
    suite.addTest(test_new_instance.suite())
    suite.addTest(test_DoctypeTreeBuilder.suite())
    suite.addTest(test_CLRXMLParser.suite())
    suite.addTest(test_AglyphDefaultXMLParser.suite())
    # aglyph.component
    suite.addTest(test_Reference.suite())
    suite.addTest(test_InitializationSupport.suite())
    suite.addTest(test_Evaluator.suite())
    suite.addTest(test_DependencySupport.suite())
    suite.addTest(test_Template.suite())
    suite.addTest(test_Component.suite())
    # aglyph.context
    suite.addTest(test_CreationBuilderMixin.suite())
    suite.addTest(test_InjectionBuilderMixin.suite())
    suite.addTest(test_LifecycleBuilderMixin.suite())
    suite.addTest(test_RegistrationMixin.suite())
    suite.addTest(test_Context.suite())
    suite.addTest(test_XMLContext.suite())
    # aglyph.assembler
    suite.addTest(test_ReentrantMutexCache.suite())
    suite.addTest(test_Assembler.suite())

    return suite


logging.config.dictConfig({
    "version": 1,
    "formatters": {
        "with-thread-id": {
            "format":
                "[%(levelname)-9s %(thread)08x %(name)s %(funcName)s]\n"
                    "%(message)s",
        },
    },
    "handlers": {
        "combined-file": {
            "class": "logging.FileHandler",
            "formatter": "with-thread-id",
            "filename": os.path.normpath(
                os.path.join(
                    os.path.dirname(suite.__code__.co_filename), "..",
                    "test.log")),
            "mode": 'w'
        },
    },
    "loggers": {
        "test": {
            "level": logging.DEBUG,
            "propagate": False,
            "handlers": ["combined-file"],
        },
        "aglyph": {
            "level": TRACE,
            "propagate": False,
            "handlers": ["combined-file"],
        }
    },
})

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test")

# all the way down here so that the logging configuration is in place before
# anything from the "aglyph" namespace is imported
from aglyph import __version__

