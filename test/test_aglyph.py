# -*- coding: UTF-8 -*-

# Copyright (c) 2006-2015 Matthew Zipay <mattz@ninthtest.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Master test case and runner for Aglyph."""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "2.1.0"

import logging
import unittest

from aglyph import (
    format_dotted_name, 
    has_importable_dotted_name,
    identify_by_spec,
    resolve_dotted_name,
    _safe_repr,
)
from aglyph.compat import StringTypes

from test import enable_debug_logging, find_basename, py_builtin_module
from test.dummy import Alpha, Beta, create_alpha, Delta, Gamma

__all__ = [
    "FormatDottedNameTest",
    "HasImportableDottedNameTest",
    "IdentifyBySpecTest",
    "ResolveDottedNameTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_logger = logging.getLogger("test.test_aglyph")

# PYVER: unittest.TestCase.assertIsNone is missing in Jython 2.5.3
if (not hasattr(unittest.TestCase, "assertIsNone")):
    def _assert_is_none(self, obj, msg=None):
        if (obj is not None):
            self.fail(msg if (msg is not None) else "%r is not None" % obj)
    unittest.TestCase.assertIsNone = _assert_is_none

# PYVER: unittest.TestCase.assertIsNotNone is missing in Jython 2.5.3
if (not hasattr(unittest.TestCase, "assertIsNotNone")):
    def _assert_is_not_none(self, obj, msg=None):
        if (obj is None):
            self.fail(msg if (msg is not None) else "%r is None" % obj)
    unittest.TestCase.assertIsNotNone = _assert_is_not_none


class HasImportableDottedNameTest(unittest.TestCase):
    """Test the :func:`aglyph.has_importable_dotted_name` function."""

    def test_new_style_class(self):
        self.assertTrue(has_importable_dotted_name(Alpha))

    # PYVER: redundant on Python >= 3.0 (actually a new-style class)
    def test_old_style_class(self):
        self.assertTrue(has_importable_dotted_name(Delta))

    def test_user_defined_function(self):
        self.assertTrue(has_importable_dotted_name(create_alpha))

    def test_builtin_type(self):
        self.assertTrue(has_importable_dotted_name(dict))

    def test_builtin_function(self):
        self.assertTrue(has_importable_dotted_name(filter))

    def test_bound_function(self):
        self.assertFalse(has_importable_dotted_name(Beta().get_value))
        # PYVER: redundant on Python >= 3.0 (actually a new-style class)
        self.assertFalse(has_importable_dotted_name(Delta().get_value))
        self.assertFalse(has_importable_dotted_name(dict().update))

    def test_none(self):
        self.assertFalse(has_importable_dotted_name(None))


class FormatDottedNameTest(unittest.TestCase):
    """Test the :func:`aglyph.format_dotted_name` function."""

    def test_new_style_class(self):
        self.assertEqual("test.dummy.Alpha", format_dotted_name(Alpha))

    # PYVER: redundant on Python >= 3.0 (actually a new-style class)
    def test_old_style_class(self):
        self.assertEqual("test.dummy.Delta", format_dotted_name(Delta))

    def test_user_defined_function(self):
        self.assertEqual("test.dummy.create_alpha",
                         format_dotted_name(create_alpha))

    def test_builtin_type(self):
        self.assertEqual("%s.dict" % py_builtin_module.__name__,
                         format_dotted_name(dict))

    def test_builtin_function(self):
        self.assertEqual("%s.filter" % py_builtin_module.__name__,
                         format_dotted_name(filter))

    def test_bound_function(self):
        self.assertRaises(TypeError, format_dotted_name, Beta().get_value)
        # PYVER: redundant on Python >= 3.0 (actually a new-style class)
        self.assertRaises(TypeError, format_dotted_name, Delta().get_value)
        self.assertRaises(TypeError, format_dotted_name, dict().update)

    def test_none(self):
        self.assertRaises(TypeError, format_dotted_name, None)


class ResolveDottedNameTest(unittest.TestCase):
    """Test the :func:`aglyph.resolve_dotted_name` function."""

    def test_new_style_class(self):
        self.assertTrue(Beta is resolve_dotted_name("test.dummy.Beta"))

    # PYVER: redundant on Python >= 3.0 (actually a new-style class)
    def test_old_style_class(self):
        self.assertTrue(
            Delta is resolve_dotted_name("test.dummy.Delta"))

    def test_user_defined_function(self):
        self.assertTrue(create_alpha is
                        resolve_dotted_name("test.dummy.create_alpha"))

    def test_builtin_type(self):
        self.assertTrue(dict is
                        resolve_dotted_name("%s.dict" %
                                            py_builtin_module.__name__))

    def test_builtin_function(self):
        self.assertTrue(filter is
                        resolve_dotted_name("%s.filter" %
                                            py_builtin_module.__name__))

    def test_bound_function(self):
        self.assertRaises(ImportError, resolve_dotted_name,
                          "test.dummy.Beta.get_value")
        # PYVER: redundant on Python >= 3.0 (actually a new-style class)
        self.assertRaises(ImportError, resolve_dotted_name,
                          "test.dummy.Delta.get_value")
        self.assertRaises(ImportError, resolve_dotted_name, "%s.dict.update" %
                          py_builtin_module.__name__)

    def test_module_not_found(self):
        self.assertRaises(ImportError, resolve_dotted_name, "does.not.exist")


class IdentifyBySpecTest(unittest.TestCase):
    """Test the :func:`aglyph.identify_by_spec` function."""

    def test_string(self):
        self.assertEqual("test_spec_is_string",
                         identify_by_spec("test_spec_is_string"))

    def test_new_style_class(self):
        self.assertEqual("test.dummy.Alpha", identify_by_spec(Alpha))

    # PYVER: redundant on Python >= 3.0 (actually a new-style class)
    def test_old_style_class(self):
        self.assertEqual("test.dummy.Delta", identify_by_spec(Delta))

    def test_user_defined_function(self):
        self.assertEqual("test.dummy.create_alpha",
                         identify_by_spec(create_alpha))

    def test_builtin_type(self):
        self.assertEqual("%s.dict" % py_builtin_module.__name__,
                         identify_by_spec(dict))

    def test_builtin_function(self):
        self.assertEqual("%s.filter" % py_builtin_module.__name__,
                         identify_by_spec(filter))

    def test_bound_function(self):
        self.assertRaises(TypeError, identify_by_spec, Beta().get_value)
        # PYVER: redundant on Python >= 3.0 (actually a new-style class)
        self.assertRaises(TypeError, identify_by_spec, Delta().get_value)
        self.assertRaises(TypeError, identify_by_spec, dict().update)

    def test_none(self):
        self.assertRaises(TypeError, identify_by_spec, None)


class SafeReprTest(unittest.TestCase):

    def test_safe_repr(self):
        # don't care what the values are, as long as no exception is raised and
        # the repr is not empty
        for obj in (
                None,       # builtin constant
                int,        # builtin type
                79,         # builtin type object
                open,       # builtin function
                Alpha,      # new-style class
                Beta(),     # new-style class object
                Gamma,      # old-style class
                Delta(),    # old-style class instance
                ):
            r = _safe_repr(obj)
            self.assertTrue(isinstance(r, StringTypes))
            self.assertNotEqual("", r, repr(r))


def suite():
    """Build the test suite for the :mod:`aglyph` package."""
    import test.test_assembler
    import test.test_binder
    import test.test_cache
    import test.test_component
    import test.test_context

    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HasImportableDottedNameTest))
    suite.addTest(unittest.makeSuite(FormatDottedNameTest))
    suite.addTest(unittest.makeSuite(ResolveDottedNameTest))
    suite.addTest(unittest.makeSuite(IdentifyBySpecTest))
    suite.addTest(unittest.makeSuite(SafeReprTest))
    suite.addTest(test.test_cache.suite())
    suite.addTest(test.test_component.suite())
    suite.addTest(test.test_context.suite())
    suite.addTest(test.test_assembler.suite())
    suite.addTest(test.test_binder.suite())

    _logger.debug("RETURN %r", suite)
    return suite


if (__name__ == "__main__"):
    enable_debug_logging(suite)
    unittest.TextTestRunner().run(suite())

