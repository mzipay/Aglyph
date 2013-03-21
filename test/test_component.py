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

"""Test cases and runner for the :mod:`aglyph.component` module."""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "1.1.1"

import functools
import logging
import unittest

from aglyph.component import Component, Evaluator, Reference, Strategy

from test import enable_debug_logging
from test.dummy import Alpha

__all__ = [
    "ComponentTest",
    "EvaluatorTest",
    "ReferenceTest",
    "suite",
]

# don't use __name__ here; can be run as "__main__"
_logger = logging.getLogger("test.test_component")


class ComponentTest(unittest.TestCase):
    """Test the :class:`aglyph.component.Component` class."""

    def test_id_is_dotted_name(self):
        component = Component("test.dummy.Alpha")
        self.assertEqual("test.dummy.Alpha", component.component_id)
        self.assertEqual("test.dummy.Alpha", component.dotted_name)

    def test_unique_id_and_dotted_name(self):
        comonent = Component("alpha", "test.dummy.Alpha")
        self.assertEqual("alpha", comonent.component_id)
        self.assertEqual("test.dummy.Alpha", comonent.dotted_name)

    def test_bad_strategy(self):
        self.assertRaises(ValueError, Component, "test.dummy.Alpha",
                          strategy="spam")

    def test_default_strategy(self):
        component = Component("test.dummy.Alpha")
        self.assertEqual(Strategy.PROTOTYPE, component.strategy)

    def test_readonly_properties(self):
        component = Component("alpha", "test.dummy.Alpha")
        self.assertRaises(AttributeError, setattr, component, "component_id",
                          "beta")
        self.assertRaises(AttributeError, setattr, component, "dotted_name",
                          "test.dummy.Beta")
        self.assertRaises(AttributeError, setattr, component, "strategy",
                          Strategy.SINGLETON)

    def test_explicit_prototype_strategy(self):
        component = Component("test.dummy.Alpha", strategy=Strategy.PROTOTYPE)
        self.assertEqual(Strategy.PROTOTYPE, component.strategy)

    def test_explicit_singleton_strategy(self):
        component = Component("test.dummy.Alpha", strategy=Strategy.SINGLETON)
        self.assertEqual(Strategy.SINGLETON, component.strategy)

    def test_explicit_borg_strategy(self):
        component = Component("test.dummy.Alpha", strategy=Strategy.BORG)
        self.assertEqual(Strategy.BORG, component.strategy)

    def test_default_dependencies(self):
        component = Component("test.dummy.Alpha")
        self.assertEqual([], component.init_args)
        self.assertEqual({}, component.init_keywords)
        self.assertEqual({}, component.attributes)


class EvaluatorTest(unittest.TestCase):
    """Test the :class:`aglyph.component.Evaluator` class."""

    def test_func_not_callable(self):
        self.assertRaises(TypeError, Evaluator, None)

    def test_func_with_no_args_or_keywords(self):
        evaluator = Evaluator(int)
        self.assertTrue(evaluator.func is int)
        self.assertEqual((), evaluator.args)
        self.assertEqual({}, evaluator.keywords)
        self.assertEqual(0, evaluator(None))

    def test_func_with_only_args(self):
        evaluator = Evaluator(int, "4f", 16)
        self.assertTrue(evaluator.func is int)
        self.assertEqual(("4f", 16), evaluator.args)
        self.assertEqual({}, evaluator.keywords)
        self.assertEqual(79, evaluator(None))

    def test_func_with_only_keywords(self):
        def f(a=None, b=None):
            if (None not in [a, b]):
                return a * b
        evaluator = Evaluator(f, a=7, b=9)
        self.assertTrue(evaluator.func is f)
        self.assertEqual((), evaluator.args)
        self.assertEqual({'a': 7, 'b': 9}, evaluator.keywords)
        self.assertEqual(63, evaluator(None))

    def test_func_with_both_args_and_keywords(self):
        f = lambda x: int(x, 0)
        evaluator = Evaluator(max, "0xa", "0xF", key=f)
        self.assertTrue(evaluator.func is max)
        self.assertEqual(("0xa", "0xF"), evaluator.args)
        self.assertEqual({"key": f}, evaluator.keywords)
        # natural sort would identify "0xa" as the max
        self.assertEqual("0xF", evaluator(None))

    def test_readonly_properties(self):
        evaluator = Evaluator(int, "79")
        self.assertRaises(AttributeError, setattr, evaluator, "func", min)
        self.assertRaises(AttributeError, setattr, evaluator, "args", ("0xb",
                                                                       "0xE"))
        self.assertRaises(AttributeError, setattr, evaluator, "keywords",
                          {"key": lambda x: x.upper()})

    def test_resolve_reference(self):
        class MockAssembler(object):
            def assemble(self, component_id):
                return component_id.upper()
        evaluator = Evaluator(Alpha, Reference("test-ref"))
        alpha = evaluator(MockAssembler())
        self.assertEqual("TEST-REF", alpha.arg)

    def test_resolve_evaluator(self):
        evaluator = Evaluator(int, Evaluator(hex, 79), 0)
        self.assertEqual(79, evaluator(None))

    def test_resolve_partial(self):
        evaluator = Evaluator(int, functools.partial(hex, 79), 0)
        self.assertEqual(79, evaluator(None))

    def test_resolve_dict(self):
        evaluator = Evaluator(Alpha, {"key": "value"})
        alpha = evaluator(None)
        self.assertEqual({"key": "value"}, alpha.arg)

    def test_resolve_sequence(self):
        evaluator = Evaluator(Alpha, (2, 3, 5, 7))
        alpha = evaluator(None)
        self.assertEqual((2, 3, 5, 7), alpha.arg)

    def test_resolve_nested(self):
        class MockAssembler(object):
            def assemble(self, component_id):
                return component_id.upper()
        evaluator = Evaluator(Alpha, {"key": Reference("test-ref")})
        alpha = evaluator(MockAssembler())
        self.assertEqual({"key": "TEST-REF"}, alpha.arg)


# PYVER: unicode is undefined in Python >= 3.0 (str is a Unicode string in
#        Python >= 3.0)
try:
    _ustr = eval("unicode")
except NameError:
    _ustr = str

# PYVER: u"..." syntax is illegal in Python >= 3.0, and b"..." syntax is
#        illegal in Python < 3.0
try:
    _dummy_dot_Alpha_ascii = eval("u'test.dummy.Alpha'.encode('ascii')")
    _Delta_ustr = eval("u'\u0394'")
    _Delta_utf8 = eval("u'\u0394'.encode('utf-8')")
except SyntaxError:
    _dummy_dot_Alpha_ascii = eval("b'test.dummy.Alpha'")
    _Delta_ustr = eval("'\u0394'")
    _Delta_utf8 = eval("'\u0394'.encode('utf-8')")


class ReferenceTest(unittest.TestCase):
    """Test the :class:`aglyph.component.Reference` class."""

    def test_dotted_name_ascii(self):
        ref = Reference("test.dummy.Alpha")
        self.assertTrue(isinstance(ref, _ustr))
        self.assertEqual(_dummy_dot_Alpha_ascii, ref.encode("ascii"))

    def test_component_id_unicode_error(self):
        # Greek capital letter Delta (U+0394)
        ref = Reference(_Delta_ustr)
        self.assertTrue(isinstance(ref, _ustr))
        self.assertRaises(UnicodeEncodeError, ref.encode, "ascii")

    def test_component_id_unicode_encode(self):
        # Greek capital letter Delta (U+0394)
        ref = Reference(_Delta_ustr)
        self.assertTrue(isinstance(ref, _ustr))
        self.assertEqual(_Delta_utf8, ref.encode("utf-8"))


def suite():
    """Build the test suite for the :mod:`aglyph.component` module."""
    _logger.debug("TRACE")
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ComponentTest))
    suite.addTest(unittest.makeSuite(EvaluatorTest))
    suite.addTest(unittest.makeSuite(ReferenceTest))
    _logger.debug("RETURN %r", suite)
    return suite


if (__name__ == "__main__"):
    enable_debug_logging(suite)
    unittest.TextTestRunner().run(suite())
