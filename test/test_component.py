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

"""Test cases and runner for the :mod:`aglyph.component` module."""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "2.1.0"

import functools
import logging
import unittest

from aglyph import AglyphError
from aglyph.component import (
    Component,
    Evaluator,
    Reference,
    Strategy,
    Template,
)

from test import enable_debug_logging
from test.dummy import Alpha

__all__ = [
    "ComponentTest",
    "EvaluatorTest",
    "ReferenceTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_logger = logging.getLogger("test.test_component")

# PYVER: unittest.TestCase.assertIsNone is missing in Jython 2.5.3
if (not hasattr(unittest.TestCase, "assertIsNone")):
    def _assert_is_none(self, obj, msg=None):
        if (obj is not None):
            self.fail(msg if (msg is not None) else "%r is not None" % obj)
    unittest.TestCase.assertIsNone = _assert_is_none


class TemplateTest(unittest.TestCase):
    """Test the :class:`aglyph.component.Template` class."""

    def test_defaults(self):
        template = Template("test")
        self.assertEqual("test", template.unique_id)
        self.assertIsNone(template.parent_id)
        self.assertIsNone(template.after_inject)
        self.assertIsNone(template.before_clear)
        self.assertEqual([], template.args)
        self.assertEqual({}, template.keywords)
        self.assertEqual({}, template.attributes)

    def test_readonly_properties(self):
        template = Template("test")
        self.assertRaises(AttributeError, setattr, template, "unique_id", "x")
        self.assertRaises(AttributeError, setattr, template, "parent_id", "x")
        self.assertRaises(AttributeError, setattr, template, "after_inject",
                          "after_inject")
        self.assertRaises(AttributeError, setattr, template, "before_clear",
                          "before_clear")
        self.assertRaises(AttributeError, setattr, template, "args", [])
        self.assertRaises(AttributeError, setattr, template, "keywords", {})
        self.assertRaises(AttributeError, setattr, template, "attributes", {})

    def test_parent_id(self):
        template = Template("test", parent_id="parent")
        self.assertEqual("parent", template.parent_id)

    def test_after_inject(self):
        template = Template("test", after_inject="template_after_inject")
        self.assertEqual("template_after_inject", template.after_inject)

    def test_before_clear(self):
        template = Template("test", before_clear="template_before_clear")
        self.assertEqual("template_before_clear", template.before_clear)

    def test_attributes_are_ordered(self):
        template = Template("test")
        template.attributes["set_value"] = None
        template.attributes["prop"] = None
        template.attributes["field"] = None
        expected_keys = ["set_value", "prop", "field"]
        self.assertEqual(expected_keys, list(template.attributes.keys()))


class ComponentTest(unittest.TestCase):
    """Test the :class:`aglyph.component.Component` class."""

    def test_bad_strategy(self):
        self.assertRaises(ValueError, Component, "test.dummy.Alpha",
                          strategy="spam")

    def test_defaults(self):
        component = Component("test.dummy.Alpha")
        self.assertEqual("test.dummy.Alpha", component.unique_id)
        # Component.component_id will be removed in 3.0.0
        self.assertEqual(component.unique_id, component.component_id)
        self.assertEqual("test.dummy.Alpha", component.dotted_name)
        self.assertIsNone(component.factory_name)
        self.assertIsNone(component.member_name)
        self.assertEqual(Strategy.PROTOTYPE, component.strategy)
        self.assertIsNone(component.parent_id)
        self.assertIsNone(component.after_inject)
        self.assertIsNone(component.before_clear)
        self.assertEqual([], component.args)
        # Component.init_args will be removed in 3.0.0
        self.assertEqual(component.args, component.init_args)
        self.assertEqual({}, component.keywords)
        # Component.init_keywords will be removed in 3.0.0
        self.assertEqual(component.keywords, component.init_keywords)
        self.assertEqual({}, component.attributes)

    def test_unique_id_and_dotted_name(self):
        comonent = Component("alpha", "test.dummy.Alpha")
        self.assertEqual("alpha", comonent.component_id)
        self.assertEqual("test.dummy.Alpha", comonent.dotted_name)

    def test_readonly_properties(self):
        component = Component("alpha", "test.dummy.Alpha")
        self.assertRaises(AttributeError, setattr, component, "unique_id", "x")
        # Component.component_id will be removed in 3.0.0
        self.assertRaises(AttributeError, setattr, component, "component_id",
                          "x")
        self.assertRaises(AttributeError, setattr, component, "dotted_name",
                          "test.dummy.Beta")
        self.assertRaises(AttributeError, setattr, component, "factory_name",
                          "factory")
        self.assertRaises(AttributeError, setattr, component, "member_name",
                          "member")
        self.assertRaises(AttributeError, setattr, component, "strategy",
                          Strategy.SINGLETON)
        self.assertRaises(AttributeError, setattr, component, "parent_id",
                          "parent")
        self.assertRaises(AttributeError, setattr, component, "after_inject",
                          "after_inject")
        self.assertRaises(AttributeError, setattr, component, "before_clear",
                          "before_clear")
        self.assertRaises(AttributeError, setattr, component, "args", [])
        # Component.init_args will be removed in 3.0.0
        self.assertRaises(AttributeError, setattr, component, "init_args", [])
        self.assertRaises(AttributeError, setattr, component, "keywords", {})
        # Component.init_keywords will be removed in 3.0.0
        self.assertRaises(AttributeError, setattr, component, "init_keywords", {})
        self.assertRaises(AttributeError, setattr, component, "attributes", {})

    def test_explicit_prototype_strategy(self):
        component = Component("test.dummy.Alpha", strategy=Strategy.PROTOTYPE)
        self.assertEqual(Strategy.PROTOTYPE, component.strategy)

    def test_explicit_singleton_strategy(self):
        component = Component("test.dummy.Alpha", strategy=Strategy.SINGLETON)
        self.assertEqual(Strategy.SINGLETON, component.strategy)

    def test_explicit_borg_strategy(self):
        component = Component("test.dummy.Alpha", strategy=Strategy.BORG)
        self.assertEqual(Strategy.BORG, component.strategy)

    def test_explicit_weakref_strategy(self):
        component = Component("test.dummy.Alpha", strategy=Strategy.WEAKREF)
        self.assertEqual(Strategy.WEAKREF, component.strategy)

    def test_attributes_are_ordered(self):
        component = Component("test.dummy.Alpha")
        component.attributes["set_value"] = None
        component.attributes["prop"] = None
        component.attributes["field"] = None
        expected_keys = ["set_value", "prop", "field"]
        self.assertEqual(expected_keys, list(component.attributes.keys()))

    def test_factory_name(self):
        component = Component("epsilon-factory",
                              dotted_name="test.dummy.Epsilon",
                              factory_name="class_factory")
        self.assertEqual("epsilon-factory", component.component_id)
        self.assertEqual("test.dummy.Epsilon", component.dotted_name)
        self.assertEqual("class_factory", component.factory_name)
        self.assertTrue(component.member_name is None)

    def test_member_name(self):
        component = Component("epsilon-class", dotted_name="test.dummy",
                              member_name="Epsilon")
        self.assertEqual("epsilon-class", component.component_id)
        self.assertEqual("test.dummy", component.dotted_name)
        self.assertEqual("Epsilon", component.member_name)
        self.assertTrue(component.factory_name is None)

    def test_factory_and_member_names_mutually_exclusive(self):
        self.assertRaises(AglyphError, Component, "epsilon-fail",
                          dotted_name="test.dummy.Epsilon",
                          factory_name="class_factory",
                          member_name="ATTRIBUTE")

    def test_parent_id(self):
        component = Component("test.dummy.Alpha", parent_id="alpha-parent")
        self.assertEqual("alpha-parent", component.parent_id)

    def test_after_inject(self):
        component = Component("test.dummy.Alpha",
                              after_inject="component_after_inject")
        self.assertEqual("component_after_inject", component.after_inject)

    def test_prototype_ignores_before_clear(self):
        component = Component("test.dummy.Alpha",
                              before_clear="component_before_clear")
        self.assertIsNone(component.before_clear)

    def test_component_singleton_before_clear(self):
        component = Component("test.dummy.Alpha", strategy="singleton",
                              before_clear="component_before_clear")
        self.assertEqual("component_before_clear", component.before_clear)

    def test_component_borg_before_clear(self):
        component = Component("test.dummy.Alpha", strategy="borg",
                              before_clear="component_before_clear")
        self.assertEqual("component_before_clear", component.before_clear)

    def test_component_weakref_before_clear(self):
        component = Component("test.dummy.Alpha", strategy="weakref",
                              before_clear="component_before_clear")
        self.assertEqual("component_before_clear", component.before_clear)


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
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TemplateTest))
    suite.addTest(unittest.makeSuite(ComponentTest))
    suite.addTest(unittest.makeSuite(EvaluatorTest))
    suite.addTest(unittest.makeSuite(ReferenceTest))
    _logger.debug("RETURN %r", suite)
    return suite


if (__name__ == "__main__"):
    enable_debug_logging(suite)
    unittest.TextTestRunner().run(suite())

