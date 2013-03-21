# -*- coding: utf-8 -*-

# Copyright (c) 2006-2013 Matthew Zipay <mattz@ninthtest.net>
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
__version__ = "1.1.1"

import logging
import unittest

from aglyph import (format_dotted_name, has_importable_dotted_name,
                    identify_by_spec, resolve_dotted_name)

from test import enable_debug_logging
from test.dummy import Alpha, Beta, create_alpha, Delta

# PYVER: "__builtin__" in Python < 3.0, "builtins" in Python >= 3.0
try:
    import __builtin__
    _py_builtins = __builtin__
    _py_builtins_name = "__builtin__"
except ImportError:
    import builtins
    _py_builtins = builtins
    _py_builtins_name = "builtins"

__all__ = [
    "FormatDottedNameTest",
    "HasImportableDottedNameTest",
    "IdentifyBySpecTest",
    "ResolveDottedNameTest",
    "suite",
]

# don't use __name__ here; can be run as "__main__"
_logger = logging.getLogger("test.test_aglyph")


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
        self.assertEqual("%s.dict" % _py_builtins_name,
                         format_dotted_name(dict))

    def test_builtin_function(self):
        self.assertEqual("%s.filter" % _py_builtins_name,
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
        self.assertTrue(dict is resolve_dotted_name("%s.dict" %
                                                    _py_builtins_name))

    def test_builtin_function(self):
        self.assertTrue(filter is resolve_dotted_name("%s.filter" %
                                                      _py_builtins_name))

    def test_bound_function(self):
        self.assertRaises(ImportError, resolve_dotted_name,
                          "test.dummy.Beta.get_value")
        # PYVER: redundant on Python >= 3.0 (actually a new-style class)
        self.assertRaises(ImportError, resolve_dotted_name,
                          "test.dummy.Delta.get_value")
        self.assertRaises(ImportError, resolve_dotted_name, "%s.dict.update" %
                          _py_builtins_name)

    def test_module_not_found(self):
        self.assertRaises(ImportError, resolve_dotted_name, "does.not.exist")

    def test_none(self):
        self.assertRaises(ValueError, resolve_dotted_name, None)


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
        self.assertEqual("%s.dict" % _py_builtins_name, identify_by_spec(dict))

    def test_builtin_function(self):
        self.assertEqual("%s.filter" % _py_builtins_name,
                         identify_by_spec(filter))

    def test_bound_function(self):
        self.assertRaises(TypeError, identify_by_spec, Beta().get_value)
        # PYVER: redundant on Python >= 3.0 (actually a new-style class)
        self.assertRaises(TypeError, identify_by_spec, Delta().get_value)
        self.assertRaises(TypeError, identify_by_spec, dict().update)

    def test_none(self):
        self.assertRaises(TypeError, identify_by_spec, None)


def suite():
    """Build the test suite for the :mod:`aglyph` package."""
    _logger.debug("TRACE")

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

