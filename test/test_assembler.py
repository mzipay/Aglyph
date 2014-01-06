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

"""Test cases and runner for the :mod:`aglyph.assembler` module."""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "2.0.0"

import logging
import struct
import sys
import unittest
import zipfile

from aglyph import AglyphError
from aglyph.compat import is_jython, is_pypy, is_python_2
from aglyph.assembler import Assembler
from aglyph.context import XMLContext

from test import enable_debug_logging, find_basename, skip_if
import test.dummy

__all__ = [
    "AssemblerTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_logger = logging.getLogger("test.test_assembler")

# Python 2/3 compatibility
# * u"..." is valid syntax in Python 2, but raises SyntaxError in Python 3
# * b"..." is valid syntax in Python 3, but raise SyntaxError in Python 2
if (is_python_2):
    # allows a string literal like "fa\u00e7ade" to be used like
    # 'as_text("fa\u00e7ade")', and be interpreted correctly at runtime
    # regardless of Python version 2 or 3
    as_text = lambda s: eval("u'''%s'''" % s)
    # allows a string literal like "fa\xc3\xa7ade" to be used like
    # 'as_data("fa\xc3\xa7ade")', and be interpreted correctly at runtime
    # regardless of Python version 2 or 3
    as_data = lambda s: s
else:  # assume 3
    # allows a string literal like "fa\u00e7ade" to be used like
    # 'as_text("fa\u00e7ade")', and be interpreted correctly at runtime
    # regardless of Python version 2 or 3
    as_text = lambda s: s
    # allows a string literal like "fa\xc3\xa7ade" to be used like
    # 'as_data("fa\xc3\xa7ade")', and be interpreted correctly at runtime
    # regardless of Python version 2 or 3
    as_data = lambda s: struct.pack(('=' + ('B' * len(s))),
                                    *[ord(c) for c in s])


class AssemblerTest(unittest.TestCase):
    """Test the :class:`aglyph.assembler.Assembler` class."""

    def setUp(self):
        filename = ("assemblertest-context_2.xml" if is_python_2
                    else "assemblertest-context_3.xml")
        context = XMLContext(find_basename(filename))
        self.assembler = Assembler(context)

    def tearDown(self):
        self.assembler = None

    def test_assemble_bad_component_id(self):
        self.assertRaises(KeyError, self.assembler.assemble, "not.in.context")
        self.assertRaises(KeyError, self.assembler.assemble, None)
        self.assertRaises(TypeError, self.assembler.assemble, [])

    def test_assemble_the_object(self):
        obj = self.assembler.assemble("the-object")
        self._assert_the_object(obj)

    def _assert_the_object(self, the_object):
        self.assertTrue(isinstance(the_object, object))
        self.assertTrue(self.assembler.assemble("the-object") is the_object)

    def test_assemble_strings(self):
        obj = self.assembler.assemble("strings")
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

    def test_assemble_zipfile_ZipInfo(self):
        obj = self.assembler.assemble("zipfile.ZipInfo")
        self._assert_zipfile_ZipInfo(obj)

    def _assert_zipfile_ZipInfo(self, zipinfo):
        self.assertTrue(isinstance(zipinfo, zipfile.ZipInfo))
        self.assertEqual("aglyph.txt", zipinfo.filename)
        self.assertEqual((2006, 4, 15, 21, 13, 37), zipinfo.date_time)
        self.assertEqual(zipinfo.compress_type, zipfile.ZIP_STORED)
        self.assertEqual("This is a test.", zipinfo.comment)

    def test_assemble_alpha(self):
        obj = self.assembler.assemble("alpha")
        self._assert_dummy_Alpha(obj)

    def test_assemble_dummy_dot_create_alpha(self):
        obj = self.assembler.assemble("test.dummy.create_alpha")
        self._assert_dummy_Alpha(obj)

    def _assert_dummy_Alpha(self, alpha):
        self.assertTrue(isinstance(alpha, test.dummy.Alpha))
        self._assert_the_object(alpha.arg)
        self._assert_strings(alpha.keyword)
        self._assert_the_object(alpha.field)
        self.assertEqual(["seven", 7.9, complex(7, 9)], alpha.get_value())
        self._assert_strings(alpha.prop)

    def test_assemble_dummy_dot_Beta(self):
        obj = self.assembler.assemble("test.dummy.Beta")
        self._assert_dummy_Beta(obj)

    def test_assemble_beta(self):
        obj = self.assembler.assemble("beta")
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
        the_object = self.assembler.assemble("the-object")
        self._assert_zipfile_ZipInfo(d[the_object])
        self.assertTrue(isinstance(d["zip-info"], tuple))
        (zipinfo,) = d["zip-info"]
        self._assert_zipfile_ZipInfo(zipinfo)

    def test_assemble_gamma(self):
        obj = self.assembler.assemble("gamma")
        self._assert_dummy_Gamma(obj)

    def _assert_dummy_Gamma(self, gamma):
        self.assertTrue(isinstance(gamma, test.dummy.Gamma))
        self._assert_the_object(gamma.arg)
        self._assert_strings(gamma.keyword)
        self._assert_the_object(gamma.field)
        self.assertEqual(["seven", 7.9, complex(7, 9)], gamma.get_value())
        self._assert_strings(gamma.prop)

    def test_assemble_dummy_dot_Delta(self):
        obj = self.assembler.assemble("test.dummy.Delta")
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
        the_object = self.assembler.assemble("the-object")
        self._assert_zipfile_ZipInfo(d[the_object])
        self.assertTrue(isinstance(d["zip-info"], tuple))
        (zipinfo,) = d["zip-info"]
        self._assert_zipfile_ZipInfo(zipinfo)

    def test_assemble_Epsilon_staticmethod(self):
        obj = self.assembler.assemble("epsilon-static-factory")
        self._assert_dummy_Epsilon(obj)

    def test_assemble_Epsilon_classmethod(self):
        obj = self.assembler.assemble("epsilon-class-factory")
        self._assert_dummy_Epsilon(obj)

    def test_assemble_factory_singleton(self):
        epsilon1 = self.assembler.assemble("epsilon-class-factory")
        self._assert_dummy_Epsilon(epsilon1)
        epsilon2 = self.assembler.assemble("epsilon-class-factory")
        self.assertTrue(epsilon2 is epsilon1)

    def test_assemble_Zeta_nested_class(self):
        obj = self.assembler.assemble("zeta")
        self._assert_dummy_Epsilon_Zeta(obj)

    def test_assemble_factory_borg(self):
        zeta1 = self.assembler.assemble("zeta")
        self._assert_dummy_Epsilon_Zeta(zeta1)
        zeta1.set_value("shared-state")
        zeta2 = self.assembler.assemble("zeta")
        self.assertFalse(zeta2 is zeta1)
        self.assertEqual("shared-state", zeta2.get_value())

    def test_assemble_Zeta_staticmethod(self):
        obj = self.assembler.assemble("zeta-static-factory")
        self._assert_dummy_Epsilon_Zeta(obj)

    def test_assemble_Zeta_classmethod(self):
        obj = self.assembler.assemble("zeta-class-factory")
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

    def test_assemble_Epsilon_attribute(self):
        obj = self.assembler.assemble("epsilon-attribute")
        self.assertEqual("Epsilon.ATTRIBUTE", obj)

    def test_assemble_Epsilon_Zeta_attribute(self):
        obj = self.assembler.assemble("epsilon-zeta-attribute")
        self.assertEqual("Epsilon.Zeta.ATTRIBUTE", obj)

    def test_assemble_dummy_Zeta_attribute(self):
        obj = self.assembler.assemble("dummy-zeta")
        self.assertTrue(obj is test.dummy.ZETA)
        self.assertEqual("field", obj.field)
        self.assertEqual("value", obj.get_value())
        self.assertEqual("prop", obj.prop)

    def test_assemble_member_singleton(self):
        epsilon1 = self.assembler.assemble("dummy-epsilon")
        self._assert_dummy_Epsilon(epsilon1)
        epsilon2 = self.assembler.assemble("dummy-epsilon")
        self.assertTrue(epsilon2 is epsilon1)

    def test_assemble_member_borg(self):
        zeta1 = self.assembler.assemble("dummy-zeta")
        self._assert_dummy_Epsilon_Zeta(zeta1)
        zeta1.set_value("shared-state")
        zeta2 = self.assembler.assemble("dummy-zeta")
        # in this case, because we're using member access, they ARE the same
        # object (which is correct)
        #self.assertFalse(zeta2 is zeta1)
        self.assertTrue(zeta2 is zeta1)
        self.assertEqual("shared-state", zeta2.get_value())

    def test_assemble_member_is_not_initialized(self):
        # this would fail with "TypeError: 'str' object is not callable" IF
        # initialization were not skipped when component/@member-name is
        # defined
        obj = self.assembler.assemble("zeta-ignore-init")
        self.assertEqual("Epsilon.Zeta.ATTRIBUTE", obj)

    def test_prototype_behavior(self):
        obj1 = self.assembler.assemble("zipfile.ZipInfo")
        obj2 = self.assembler.assemble("zipfile.ZipInfo")
        # different instances on each assembly
        self.assertTrue(obj1 is not obj2)
        # state is not shared between instances
        obj1.filename = "assemblertest.py"
        obj2.comment = "test_prototype_behavior"
        self.assertEqual("assemblertest.py", obj1.filename)
        self.assertEqual("aglyph.txt", obj2.filename)
        self.assertEqual((2006, 4, 15, 21, 13, 37), obj1.date_time)
        self.assertEqual((2006, 4, 15, 21, 13, 37), obj2.date_time)
        self.assertEqual("This is a test.", obj1.comment)
        self.assertEqual("test_prototype_behavior", obj2.comment)
        self.assertEqual(obj1.compress_type, zipfile.ZIP_STORED)
        self.assertEqual(obj2.compress_type, zipfile.ZIP_STORED)

    def test_singleton_behavior(self):
        obj1 = self.assembler.assemble("the-object")
        obj2 = self.assembler.assemble("the-object")
        # always returns the same instance
        self.assertTrue(obj1 is obj2)
        self.assertTrue(obj2 is self.assembler.assemble("the-object"))

    def test_clear_singletons(self):
        obj1 = self.assembler.assemble("the-object")
        obj2 = self.assembler.assemble("the-object")
        self.assertTrue(obj1 is obj2)
        # after cache clear, new singleton instance should be created on next
        # assembly
        self.assembler.clear_singletons()
        obj3 = self.assembler.assemble("the-object")
        self.assertFalse(obj2 is obj3)
        self.assertTrue(obj3 is self.assembler.assemble("the-object"))

    def test_borg_behavior(self):
        obj1 = self.assembler.assemble("alpha")
        obj2 = self.assembler.assemble("alpha")
        # different instances on each assembly
        self.assertFalse(obj1 is obj2)
        # since state is shared, a changed value should be immediately
        # reflected in all current and new instances
        obj2.arg = "changed"
        self.assertEqual("changed", obj1.arg)
        self.assertEqual("changed", obj2.arg)
        obj3 = self.assembler.assemble("alpha")
        self.assertFalse(obj2 is obj3)
        self.assertEqual("changed", obj3.arg)
        # indirect state change should also behave the same way
        strings = self.assembler.assemble("strings")
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
        obj4 = self.assembler.assemble("alpha")
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
        obj1 = self.assembler.assemble("alpha")
        self._assert_the_object(obj1.arg)
        obj1.arg = "changed"
        obj2 = self.assembler.assemble("alpha")
        self.assertEqual("changed", obj2.arg)
        # after clearing borg cache, instances 1,2 still share state, but
        # instances 3,4 now have a NEW shared state
        self.assembler.clear_borgs()
        obj3 = self.assembler.assemble("alpha")
        self._assert_the_object(obj3.arg)
        obj3.arg = "modified"
        obj4 = self.assembler.assemble("alpha")
        self.assertEqual("changed", obj1.arg)
        self.assertEqual("changed", obj2.arg)
        self.assertEqual("modified", obj3.arg)
        self.assertEqual("modified", obj4.arg)

    def test_unhashable_reference_key(self):
        self.assertRaises(TypeError, self.assembler.assemble,
                          "unhashable-reference-key")

    def test_unhashable_eval_key(self):
        self.assertRaises(TypeError, self.assembler.assemble,
                          "unhashable-eval-key")

    @skip_if(is_jython or is_pypy,
             "Jython and PyPy do not respect restricted builtins passed in "
             "the globals to eval()")
    def test_eval_restricted_builtins(self):
        self.assertRaises(NameError, self.assembler.assemble,
                          "restricted-eval")

    def test_circular_dependency(self):
        self.assertRaises(AglyphError, self.assembler.assemble, "component-1")
        self.assertRaises(AglyphError, self.assembler.assemble, "component-2")


def suite():
    """Build the test suite for the :mod:`aglyph.assembler` module."""
    _logger.debug("TRACE")
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AssemblerTest))
    _logger.debug("RETURN %r", suite)
    return suite


if (__name__ == "__main__"):
    enable_debug_logging(suite)
    unittest.TextTestRunner().run(suite())

