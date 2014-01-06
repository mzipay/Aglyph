# -*- coding: UTF-8 -*-

# Copyright (c) 2006-2014 Matthew Zipay <mattz@ninthtest.net>
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

"""Test cases and runner for the :mod:`aglyph.binder` module."""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "2.0.0"

import functools
import logging
import struct
import unittest
import zipfile

from aglyph import AglyphError
from aglyph.binder import Binder
from aglyph.compat import is_python_2
from aglyph.component import Evaluator, Reference

from test import enable_debug_logging
import test.dummy

__all__ = [
    "BinderTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_logger = logging.getLogger("test.test_binder")

# Python 2/3 compatibility
# * u"..." is valid syntax in Python 2, but raises SyntaxError in Python 3
# * b"..." is valid syntax in Python 3, but raise SyntaxError in Python 2
# * need an I/O buffer that is appropriate for the encoded bytes data type
if (is_python_2):
    # allows a string literal like "fa\u00e7ade" to be used like
    # 'as_text("fa\u00e7ade")', and be interpreted correctly at runtime
    # regardless of Python version 2 or 3
    as_text = lambda s: eval("u'''%s'''" % s)
    # allows a string literal like "fa\xc3\xa7ade" to be used like
    # 'as_data("fa\xc3\xa7ade")', and be interpreted correctly at runtime
    # regardless of Python version 2 or 3
    as_data = lambda s: s
else:  # assume is_python_3
    # allows a string literal like "fa\u00e7ade" to be used like
    # 'as_text("fa\u00e7ade")', and be interpreted correctly at runtime
    # regardless of Python version 2 or 3
    as_text = lambda s: s
    # allows a string literal like "fa\xc3\xa7ade" to be used like
    # 'as_data("fa\xc3\xa7ade")', and be interpreted correctly at runtime
    # regardless of Python version 2 or 3
    as_data = lambda s: struct.pack(('=' + ('B' * len(s))),
                                    *[ord(c) for c in s])


class _DummyBinder(Binder):
    """The :class:`aglyph.binder.Binder` object used in all tests."""

    def __init__(self, binder_id):
        super(_DummyBinder, self).__init__(binder_id)
        self.bind("the-object", to=object, strategy="singleton")
        strings = {}
        strings["bytes-no-encoding"] = as_data("facade")
        strings["bytes-with-encoding"] = as_text("fa\u00e7ade").encode(
                                                                "iso-8859-1")
        strings["str-no-encoding"] = "facade"
        if (is_python_2):
            strings["str-with-encoding"] = (as_text("fa\u00e7ade").
                                            encode("iso-8859-1"))
        else:  # assume 3
            strings["str-with-encoding"] = as_text("fa\u00e7ade")
        strings["unicode"] = as_text("fa\u00e7ade")
        self.bind("strings", to=dict).init(list(strings.items()))
        (self.bind(zipfile.ZipInfo).
            init("aglyph.txt", (2006, 4, 15, 21, 13, 37)).
            attributes(comment="This is a test."))
        the_object_ref = Reference("the-object")
        strings_ref = Reference("strings")
        (self.bind("alpha", to=test.dummy.Alpha, strategy="borg").
            init(the_object_ref, strings_ref).
            attributes(field=the_object_ref,
                       # important for this to be a partial because otherwise
                       # modify-by-reference would affect future injections!
                       # if one of the args or keywords is a Reference, use
                       # an Evaluator instead of partial - recursive assembly
                       # won't work with a partial!
                       set_value=functools.partial(list, [as_data("seven"),
                                                   7.9, complex(7, 9)]),
                       prop=strings_ref))
        (self.bind(test.dummy.create_alpha, strategy="borg").
            init(the_object_ref, strings_ref).
            attributes(field=the_object_ref,
                       # important for this to be a partial because otherwise
                       # modify-by-reference would affect future injections!
                       # if one of the args or keywords is a Reference, use
                       # an Evaluator instead of partial - recursive assembly
                       # won't work with a partial!
                       set_value=functools.partial(list, [as_data("seven"),
                                                   7.9, complex(7, 9)]),
                       prop=strings_ref))
        zipinfo_ref = Reference("zipfile.ZipInfo")
        # needs to be an Evaluator (not a partial!) so that nested
        # References are recursively assembled
        prop_eval = Evaluator(dict, [(the_object_ref, zipinfo_ref),
                                     ("zip-info", (zipinfo_ref,))])
        self.bind(test.dummy.Beta).init(
            keyword=(None, False, True)).attributes(
                field=the_object_ref,
                # _Binding.resolve automatically turns this into a Reference
                set_value=zipfile.ZipInfo,
                prop=prop_eval)
        (self.bind("beta", to=test.dummy.create_beta).
            init(keyword=(None, False, True)).
            attributes(field=the_object_ref, set_value=zipinfo_ref,
                       prop=prop_eval))
        (self.bind("gamma", to="test.dummy.Gamma").
            init(the_object_ref, strings_ref).
            attributes(field=the_object_ref,
                       # important for this to be a partial because otherwise
                       # modify-by-reference would affect future injections!
                       # if one of the args or keywords is a Reference, use
                       # an Evaluator instead of partial - recursive assembly
                       # won't work with a partial!
                       set_value=functools.partial(list, [as_data("seven"),
                                                   7.9, complex(7, 9)]),
                       prop=strings_ref))
        self.bind(test.dummy.Delta).init(
            keyword=(None, False, True)).attributes(
                field=the_object_ref,
                # _Binding.resolve automatically turns this into a Reference
                set_value=zipfile.ZipInfo,
                prop=prop_eval)
        unhash_ref_key_eval = Evaluator(dict, [(strings_ref, None)])
        self.bind("unhashable-reference-key",
                  to=test.dummy.Alpha).init(unhash_ref_key_eval)
        component_1_ref = Reference("component-1")
        component_2_ref = Reference("component-2")
        self.bind("component-1", to=test.dummy.Alpha).init(component_2_ref)
        self.bind("component-2", to=test.dummy.Beta).attributes(
            field=component_1_ref)
        (self.bind("epsilon-static-factory", to="test.dummy.Epsilon",
                   factory="static_factory").
            init("arg", keyword="keyword").
            attributes(field="field", set_value="value", prop="prop"))
        (self.bind("epsilon-class-factory", to="test.dummy.Epsilon",
                   factory="class_factory", strategy="singleton").
            init("arg", keyword="keyword").
            attributes(field="field", set_value="value", prop="prop"))
        (self.bind("zeta", to="test.dummy", factory="Epsilon.Zeta",
                   strategy="borg").
            init(keyword="keyword").
            attributes(field="field", set_value="value", prop="prop"))
        (self.bind("zeta-static-factory", to="test.dummy.Epsilon",
                   factory="Zeta.static_factory").
            init(keyword="keyword").
            attributes(field="field", set_value="value", prop="prop"))
        (self.bind("zeta-class-factory", to="test.dummy",
                   factory="Epsilon.Zeta.class_factory").
            init(keyword="keyword").
            attributes(field="field", set_value="value", prop="prop"))
        self.bind("epsilon-attribute", to="test.dummy",
                  member="Epsilon.ATTRIBUTE")
        self.bind("epsilon-zeta-attribute", to="test.dummy.Epsilon",
                  member="Zeta.ATTRIBUTE", strategy="singleton")
        (self.bind("dummy-zeta", to="test.dummy", member="ZETA",
                   strategy="borg").
            attributes(field="field", set_value="value", prop="prop"))
        (self.bind("zeta-ignore-init", to="test.dummy",
                   member="Epsilon.Zeta.ATTRIBUTE").
            init(the_object_ref, keyword="ignored"))


class BinderTest(unittest.TestCase):
    """Test the :class:`aglyph.binder.Binder` class."""

    def setUp(self):
        binder_id = self.id().rsplit('.', 1)[-1]
        self.binder = _DummyBinder(binder_id)

    def tearDown(self):
        self.binder = None

    def test_lookup_bad_component_id(self):
        self.assertRaises(KeyError, self.binder.lookup, "not.in.context")
        self.assertRaises(TypeError, self.binder.lookup, None)
        self.assertRaises(TypeError, self.binder.lookup, [])

    def test_lookup_the_object(self):
        obj = self.binder.lookup("the-object")
        self._assert_the_object(obj)

    def _assert_the_object(self, the_object):
        self.assertTrue(isinstance(the_object, object))
        self.assertTrue(self.binder.lookup("the-object") is the_object)

    def test_lookup_strings(self):
        obj = self.binder.lookup("strings")
        self._assert_strings(obj)

    def _assert_strings(self, strings):
        self.assertTrue(isinstance(strings, dict))
        d = {"bytes-no-encoding": as_data("facade"),
             "bytes-with-encoding": as_data("fa\xe7ade"),
             "str-no-encoding": "facade",
             "unicode": as_text("fa\u00e7ade")}
        if (is_python_2):
            d["str-with-encoding"] = as_data("fa\xe7ade")
        else:  # assume 3
            d["str-with-encoding"] = as_text("fa\u00e7ade")
        self.assertEqual(d, strings)

    def test_lookup_zipfile_ZipInfo(self):
        obj = self.binder.lookup(zipfile.ZipInfo)
        self._assert_zipfile_ZipInfo(obj)

    def _assert_zipfile_ZipInfo(self, zipinfo):
        self.assertTrue(isinstance(zipinfo, zipfile.ZipInfo))
        self.assertEqual("aglyph.txt", zipinfo.filename)
        self.assertEqual((2006, 4, 15, 21, 13, 37), zipinfo.date_time)
        self.assertEqual(zipinfo.compress_type, zipfile.ZIP_STORED)
        self.assertEqual("This is a test.", zipinfo.comment)

    def test_lookup_alpha(self):
        obj = self.binder.lookup("alpha")
        self._assert_dummy_Alpha(obj)

    def test_lookup_dummy_dot_create_alpha(self):
        obj = self.binder.lookup(test.dummy.create_alpha)
        self._assert_dummy_Alpha(obj)

    def _assert_dummy_Alpha(self, alpha):
        self.assertTrue(isinstance(alpha, test.dummy.Alpha))
        self._assert_the_object(alpha.arg)
        self._assert_strings(alpha.keyword)
        self._assert_the_object(alpha.field)
        self.assertEqual([as_data("seven"), 7.9, complex(7, 9)],
                         alpha.get_value())
        self._assert_strings(alpha.prop)

    def test_lookup_dummy_dot_Beta(self):
        obj = self.binder.lookup(test.dummy.Beta)
        self._assert_dummy_Beta(obj)

    def test_lookup_beta(self):
        obj = self.binder.lookup("beta")
        self._assert_dummy_Beta(obj)

    def _assert_dummy_Beta(self, beta):
        self.assertTrue(isinstance(beta, test.dummy.Beta))
        self.assertTrue(beta.arg is test.dummy.DEFAULT)
        self.assertEqual((None, False, True), beta.keyword)
        self._assert_the_object(beta.field)
        self._assert_zipfile_ZipInfo(beta.get_value())
        d = beta.prop
        self.assertTrue(isinstance(d, dict))
        self.assertEqual(2, len(d))
        the_object = self.binder.lookup("the-object")
        self._assert_zipfile_ZipInfo(d[the_object])
        self.assertTrue(isinstance(d["zip-info"], tuple))
        (zipinfo,) = d["zip-info"]
        self._assert_zipfile_ZipInfo(zipinfo)

    def test_lookup_gamma(self):
        obj = self.binder.lookup("gamma")
        self._assert_dummy_Gamma(obj)

    def _assert_dummy_Gamma(self, gamma):
        self.assertTrue(isinstance(gamma, test.dummy.Gamma))
        self._assert_the_object(gamma.arg)
        self._assert_strings(gamma.keyword)
        self._assert_the_object(gamma.field)
        self.assertEqual([as_data("seven"), 7.9, complex(7, 9)],
                         gamma.get_value())
        self._assert_strings(gamma.prop)

    def test_lookup_dummy_dot_Delta(self):
        obj = self.binder.lookup(test.dummy.Delta)
        self._assert_dummy_Delta(obj)

    def _assert_dummy_Delta(self, delta):
        self.assertTrue(isinstance(delta, test.dummy.Delta))
        self.assertTrue(delta.arg is test.dummy.DEFAULT)
        self.assertEqual((None, False, True), delta.keyword)
        self._assert_the_object(delta.field)
        self._assert_zipfile_ZipInfo(delta.get_value())
        d = delta.prop
        self.assertTrue(isinstance(d, dict))
        self.assertEqual(2, len(d))
        the_object = self.binder.lookup("the-object")
        self._assert_zipfile_ZipInfo(d[the_object])
        self.assertTrue(isinstance(d["zip-info"], tuple))
        (zipinfo,) = d["zip-info"]
        self._assert_zipfile_ZipInfo(zipinfo)

    def test_lookup_Epsilon_staticmethod(self):
        obj = self.binder.lookup("epsilon-static-factory")
        self._assert_dummy_Epsilon(obj)

    def test_lookup_Epsilon_classmethod(self):
        obj = self.binder.lookup("epsilon-class-factory")
        self._assert_dummy_Epsilon(obj)

    def test_lookup_Zeta_nested_class(self):
        obj = self.binder.lookup("zeta")
        self._assert_dummy_Epsilon_Zeta(obj)

    def test_lookup_Zeta_staticmethod(self):
        obj = self.binder.lookup("zeta-static-factory")
        self._assert_dummy_Epsilon_Zeta(obj)

    def test_lookup_Zeta_classmethod(self):
        obj = self.binder.lookup("zeta-class-factory")
        self._assert_dummy_Epsilon_Zeta(obj)

    def _assert_dummy_Epsilon(self, epsilon):
        self.assertTrue(isinstance(epsilon, test.dummy.Epsilon))
        self.assertEqual("arg", epsilon.arg)
        self.assertEqual("keyword", epsilon.keyword)
        self.assertEqual("field", epsilon.field)
        self.assertEqual("value", epsilon.get_value())
        self.assertEqual("prop", epsilon.prop)

    def _assert_dummy_Epsilon_Zeta(self, zeta):
        self.assertTrue(isinstance(zeta, test.dummy.Epsilon.Zeta))
        self.assertTrue(zeta.arg is test.dummy.DEFAULT)
        self.assertEqual("keyword", zeta.keyword)
        self.assertEqual("field", zeta.field)
        self.assertEqual("value", zeta.get_value())
        self.assertEqual("prop", zeta.prop)

    def test_lookup_Epsilon_attribute(self):
        obj = self.binder.lookup("epsilon-attribute")
        self.assertEqual("Epsilon.ATTRIBUTE", obj)

    def test_lookup_Epsilon_Zeta_attribute(self):
        obj = self.binder.lookup("epsilon-zeta-attribute")
        self.assertEqual("Epsilon.Zeta.ATTRIBUTE", obj)

    def test_lookup_dummy_Zeta_attribute(self):
        obj = self.binder.lookup("dummy-zeta")
        self.assertTrue(obj is test.dummy.ZETA)
        self.assertEqual("field", obj.field)
        self.assertEqual("value", obj.get_value())
        self.assertEqual("prop", obj.prop)

    def test_lookup_member_is_not_initialized(self):
        # this would fail with "TypeError: 'str' object is not callable" IF
        # initialization were not skipped when component/@member-name is
        # defined
        obj = self.binder.lookup("zeta-ignore-init")
        self.assertEqual("Epsilon.Zeta.ATTRIBUTE", obj)

    def test_prototype_behavior(self):
        obj1 = self.binder.lookup("zipfile.ZipInfo")
        obj2 = self.binder.lookup("zipfile.ZipInfo")
        # different instances on each assembly
        self.assertTrue(obj1 is not obj2)
        # state is not shared between instances
        obj1.filename = "bindertest.py"
        obj2.comment = "test_prototype_behavior"
        self.assertEqual("bindertest.py", obj1.filename)
        self.assertEqual("aglyph.txt", obj2.filename)
        self.assertEqual((2006, 4, 15, 21, 13, 37), obj1.date_time)
        self.assertEqual((2006, 4, 15, 21, 13, 37), obj2.date_time)
        self.assertEqual("This is a test.", obj1.comment)
        self.assertEqual("test_prototype_behavior", obj2.comment)
        self.assertEqual(obj1.compress_type, zipfile.ZIP_STORED)
        self.assertEqual(obj2.compress_type, zipfile.ZIP_STORED)

    def test_singleton_behavior(self):
        obj1 = self.binder.lookup("the-object")
        obj2 = self.binder.lookup("the-object")
        # always returns the same instance
        self.assertTrue(obj1 is obj2)
        self.assertTrue(obj2 is self.binder.lookup("the-object"))

    def test_clear_singletons(self):
        obj1 = self.binder.lookup("the-object")
        obj2 = self.binder.lookup("the-object")
        self.assertTrue(obj1 is obj2)
        # after cache clear, new singleton instance should be created on next
        # assembly
        self.binder.clear_singletons()
        obj3 = self.binder.lookup("the-object")
        self.assertFalse(obj2 is obj3)
        self.assertTrue(obj3 is self.binder.lookup("the-object"))

    def test_borg_behavior(self):
        obj1 = self.binder.lookup("alpha")
        obj2 = self.binder.lookup("alpha")
        # different instances on each assembly
        self.assertFalse(obj1 is obj2)
        # since state is shared, a changed value should be immediately
        # reflected in all current and new instances
        obj2.arg = "changed"
        self.assertEqual("changed", obj1.arg)
        self.assertEqual("changed", obj2.arg)
        obj3 = self.binder.lookup("alpha")
        self.assertFalse(obj2 is obj3)
        self.assertEqual("changed", obj3.arg)
        # indirect state change should also behave the same way
        strings = self.binder.lookup("strings")
        self.assertEqual(strings, obj3.keyword)
        shared_strings = obj3.keyword
        shared_strings["test_borg_behavior"] = "shared"
        # "strings" is a prototype, and so change should NOT be reflected in
        # "strings" instances...
        self.assertNotEqual(strings, shared_strings)
        # ... but SHOULD be reflected in all current and new "alpha" instances
        # (note that only .keyword shares the shared_strings state, and not
        # .prop, because "strings" is a prototype - i.e. the instance of
        # "strings" that is assigned to .prop is a different instance than
        # that assigned to .keyword, so the modify-by-reference to
        # shared_strings doesn't affect the dictionary assigned to .prop)
        obj4 = self.binder.lookup("alpha")
        self.assertFalse(obj3 is obj4)
        self.assertEqual("changed", obj4.arg)
        self.assertEqual(shared_strings, obj1.keyword)
        self.assertEqual(strings, obj1.prop)
        self.assertEqual(shared_strings, obj2.keyword)
        self.assertEqual(strings, obj2.prop)
        self.assertEqual(shared_strings, obj3.keyword)
        self.assertEqual(strings, obj3.prop)
        self.assertEqual(shared_strings, obj4.keyword)
        self.assertEqual(strings, obj4.prop)

    def test_clear_borgs(self):
        obj1 = self.binder.lookup("alpha")
        self._assert_the_object(obj1.arg)
        obj1.arg = "changed"
        obj2 = self.binder.lookup("alpha")
        self.assertEqual("changed", obj2.arg)
        # after clearing borg cache, instances 1,2 still share state, but
        # instances 3,4 now have a NEW shared state
        self.binder.clear_borgs()
        obj3 = self.binder.lookup("alpha")
        self._assert_the_object(obj3.arg)
        obj3.arg = "modified"
        obj4 = self.binder.lookup("alpha")
        self.assertEqual("changed", obj1.arg)
        self.assertEqual("changed", obj2.arg)
        self.assertEqual("modified", obj3.arg)
        self.assertEqual("modified", obj4.arg)

    def test_unhashable_reference_key(self):
        self.assertRaises(TypeError, self.binder.lookup,
                          "unhashable-reference-key")

    def test_circular_dependency(self):
        self.assertRaises(AglyphError, self.binder.lookup, "component-1")
        self.assertRaises(AglyphError, self.binder.lookup, "component-2")


def suite():
    """Build the test suite for the :mod:`aglyph.binder` module."""
    _logger.debug("TRACE")
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BinderTest))
    _logger.debug("RETURN %r", suite)
    return suite


if (__name__ == "__main__"):
    enable_debug_logging(suite)
    unittest.TextTestRunner().run(suite())

