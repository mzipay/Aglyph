# -*- coding: UTF-8 -*-

# Copyright (c) 2006, 2011, 2013-2016 Matthew Zipay.
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

"""Test case and runner for :class:`aglyph.assembler.Assembler`."""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"

import logging
import unittest

try:
    import threading
    threading_ = threading
    _has_threading = True
except:
    import dummy_threading
    threading_ = dummy_threading
    _has_threading = False

from aglyph import __version__
from aglyph.assembler import Assembler
from aglyph._compat import is_python_2
from aglyph.context import Context, XMLContext

from test import assertRaisesWithMessage, find_basename

__all__ = [
    "AssemblerTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_Assembler")
_log.info("has threading? %r (using %r)", _has_threading, threading_)


class AssemblerTest(unittest.TestCase):

    def setUp(self):
        self._assembler = Assembler(XMLContext(find_basename(
            "test_Assembler-py2.xml" if is_python_2 else
            "test_Assembler-py3.xml")))

    def test_(self):
        self.fail("TODO")


def suite():
    return unittest.makeSuite(AssemblerTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

"""
import gc
import logging
import struct
import sys
import unittest
import weakref
import zipfile

from aglyph import __version__, AglyphError
from aglyph._compat import is_jython, is_pypy, is_python_2
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

if (not gc.isenabled()):
    _logger.info("enabling GC so that weakrefs can be tested correctly")
    gc.enable()

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

    def setUp(self):
        filename = ("assemblertest-context_2.xml" if is_python_2
                    else "assemblertest-context_3.xml")
        context = XMLContext(find_basename(filename))
        self.assembler = Assembler(context)

    def tearDown(self):
        self.assembler = None

    def test_assemble_bad_component_id(self):
        self.assertRaises(KeyError, self.assembler.assemble, "not.in.context")
        self.assertRaises(TypeError, self.assembler.assemble, None)
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

    def test_init_singletons(self):
        singleton_ids = self.assembler.init_singletons()
        expected_singleton_ids = [
            "the-object",
            "epsilon-class-factory",
            "dummy-epsilon",
            "before-clear-raise",
            "context-before-clear",
            "template-before-clear",
            "component-before-clear",
            "nested-before-clear",
        ]
        self.assertEqual(
            sorted(expected_singleton_ids),
            sorted(singleton_ids))

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

    def test_init_borgs(self):
        borg_ids = self.assembler.init_borgs()
        expected_borg_ids = ["alpha", "test.dummy.create_alpha", "zeta",
                             "dummy-zeta"]
        self.assertEqual(
            sorted(expected_borg_ids),
            sorted(borg_ids))

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

    def test_weakref_behavior(self):
        obj = self.assembler.assemble("weak-alpha")
        self.assertEqual(1, weakref.getweakrefcount(obj))
        obj.field = "test_weakref_behavior"
        # should be the same object; obj is still a "live" reference
        self.assertTrue(self.assembler.assemble("weak-alpha") is obj)
        self.assertEqual("test_weakref_behavior",
                         self.assembler.assemble("weak-alpha").field)
        obj = None; del obj
        gc.collect() # this is not guaranteed!
        # should be a different object now since obj was de-referenced
        obj2 = self.assembler.assemble("weak-alpha")
        self.assertEqual(1, weakref.getweakrefcount(obj2))
        self.assertNotEqual(obj2.field, "test_weakref_behavior")

    def test_clear_weakrefs(self):
        obj1 = self.assembler.assemble("weak-alpha")
        self.assertEqual(["weak-alpha"], self.assembler.clear_weakrefs())
        # should NOT be the same object even though obj1 is still referenced
        obj2 = self.assembler.assemble("weak-alpha")
        self.assertFalse(obj2 is obj1)
        obj1 = None
        obj2 = None
        # force GC for testing purposes (note: this may still fail!)
        gc.collect()
        # now there should be nothing to clear since both objects were
        # de-referenced
        self.assertEqual([], self.assembler.clear_weakrefs())

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

    def test_assembler_contains_false_nonexistent(self):
        self.assertFalse("not.in.context" in self.assembler)
        self.assertFalse(None in self.assembler)
        self.assertFalse([] in self.assembler)

    def test_assembler_contains_false_templates(self):
        self.assertFalse("arg-template" in self.assembler)

    def test_assembler_contains_components(self):
        self.assertTrue("alpha" in self.assembler)
        self.assertTrue(test.dummy.Beta in self.assembler)

    def test_attribute_ordering(self):
        iota = self.assembler.assemble(test.dummy.Iota)
        self.assertEqual((3, "FIELD"), iota.field)
        self.assertEqual((1, "VALUE"), iota.get_value())
        self.assertEqual((2, "PROP"), iota.prop)

    def test_assemble_template_fails(self):
        self.assertTrue("arg-template" in self.assembler._context)
        self.assertRaises(KeyError, self.assembler.assemble, "arg-template")

    def test_templated_init_arg(self):
        epsilon = self.assembler.assemble("epsilon-using-arg-template")
        self.assertEqual("ARG", epsilon.arg)

    def test_collect_args(self):
        alpha = self.assembler.assemble("create_alpha-collect-args")
        self.assertEqual("TEMPLATE_ARG", alpha.arg)
        self.assertEqual("COMPONENT_ARG", alpha.keyword)

    def test_collect_keywords(self):
        delta = self.assembler.assemble("create_delta-collect-keywords")
        self.assertEqual("OVERRIDE_KEYWORD", delta.keyword)
        self.assertEqual("FIELD", delta.field)
        self.assertEqual("FIELD", delta.field)

    def test_collect_attributes(self):
        delta = self.assembler.assemble("delta-collect-attributes")
        self.assertEqual("FIELD", delta.field)
        self.assertEqual("OVERRIDE_VALUE", delta.get_value())
        self.assertEqual("PROP", delta.prop)

    def test_after_inject_raise(self):
        eta = self.assembler.assemble("after-inject-raise")
        self.assertTrue(eta.called_after_inject_raise)
        self.assertFalse(eta.called_context_after_inject)
        self.assertFalse(eta.called_template_after_inject)
        self.assertFalse(eta.called_component_after_inject)

    def test_context_after_inject(self):
        eta = self.assembler.assemble("context-after-inject")
        self.assertFalse(eta.called_after_inject_raise)
        self.assertTrue(eta.called_context_after_inject)
        self.assertFalse(eta.called_template_after_inject)
        self.assertFalse(eta.called_component_after_inject)

    def test_template_after_inject(self):
        eta = self.assembler.assemble("template-after-inject")
        self.assertFalse(eta.called_after_inject_raise)
        self.assertFalse(eta.called_context_after_inject)
        self.assertTrue(eta.called_template_after_inject)
        self.assertFalse(eta.called_component_after_inject)

    def test_component_after_inject(self):
        eta = self.assembler.assemble("component-after-inject")
        self.assertFalse(eta.called_after_inject_raise)
        self.assertFalse(eta.called_context_after_inject)
        self.assertFalse(eta.called_template_after_inject)
        self.assertTrue(eta.called_component_after_inject)

    def test_nested_class_after_inject(self):
        theta = self.assembler.assemble("nested-after-inject")
        self.assertTrue(theta.called_prepare)

    def test_before_clear_raise(self):
        eta = self.assembler.assemble("before-clear-raise")
        self.assertFalse(eta.called_before_clear_raise)
        self.assertFalse(eta.called_context_before_clear)
        self.assertFalse(eta.called_template_before_clear)
        self.assertFalse(eta.called_component_before_clear)
        self.assertEqual(["before-clear-raise"],
                         self.assembler.clear_singletons())
        self.assertTrue(eta.called_before_clear_raise)
        self.assertFalse(eta.called_context_before_clear)
        self.assertFalse(eta.called_template_before_clear)
        self.assertFalse(eta.called_component_before_clear)

    def test_context_before_clear(self):
        eta = self.assembler.assemble("context-before-clear")
        self.assertFalse(eta.called_before_clear_raise)
        self.assertFalse(eta.called_context_before_clear)
        self.assertFalse(eta.called_template_before_clear)
        self.assertFalse(eta.called_component_before_clear)
        self.assertEqual(["context-before-clear"],
                         self.assembler.clear_singletons())
        self.assertFalse(eta.called_before_clear_raise)
        self.assertTrue(eta.called_context_before_clear)
        self.assertFalse(eta.called_template_before_clear)
        self.assertFalse(eta.called_component_before_clear)

    def test_template_before_clear(self):
        eta = self.assembler.assemble("template-before-clear")
        self.assertFalse(eta.called_before_clear_raise)
        self.assertFalse(eta.called_context_before_clear)
        self.assertFalse(eta.called_template_before_clear)
        self.assertFalse(eta.called_component_before_clear)
        self.assertEqual(["template-before-clear"],
                         self.assembler.clear_singletons())
        self.assertFalse(eta.called_before_clear_raise)
        self.assertFalse(eta.called_context_before_clear)
        self.assertTrue(eta.called_template_before_clear)
        self.assertFalse(eta.called_component_before_clear)

    def test_component_before_clear(self):
        eta = self.assembler.assemble("component-before-clear")
        self.assertFalse(eta.called_before_clear_raise)
        self.assertFalse(eta.called_context_before_clear)
        self.assertFalse(eta.called_template_before_clear)
        self.assertFalse(eta.called_component_before_clear)
        self.assertEqual(["component-before-clear"],
                         self.assembler.clear_singletons())
        self.assertFalse(eta.called_before_clear_raise)
        self.assertFalse(eta.called_context_before_clear)
        self.assertFalse(eta.called_template_before_clear)
        self.assertTrue(eta.called_component_before_clear)

    def test_nested_class_before_clear(self):
        theta = self.assembler.assemble("nested-before-clear")
        self.assertFalse(theta.called_dispose)
        self.assertEqual(["nested-before-clear"],
                         self.assembler.clear_singletons())
        self.assertTrue(theta.called_dispose)





class DependencySupportProxyTest(unittest.TestCase):

    def setUp(self):
        if ("_binding_" in str(self)):
            self.depsupport = Component("test.dummy.Alpha")
        else:
            self.depsupport = Template("test-template")
        self.proxy = _DependencySupportProxy(self.depsupport)

    def tearDown(self):
        self.depsupport = None
        self.proxy = None

    def _test_init_chaining(self):
        self.assertTrue(self.proxy is self.proxy.init())

    test_binding_init_chaining = _test_init_chaining
    test_description_init_chaining = _test_init_chaining

    def _test_init_empty(self):
        self.assertEqual([], self.depsupport.args)
        self.assertEqual({}, self.depsupport.keywords)
        self.proxy.init()
        self.assertEqual([], self.depsupport.args)
        self.assertEqual({}, self.depsupport.keywords)

    test_binding_init_empty = _test_init_empty
    test_description_init_empty = _test_init_empty

    def _test_init_arg_class(self):
        # new-style class, old-style class
        self.proxy.init(test.dummy.Alpha, test.dummy.Gamma)
        self.assertTrue(self.depsupport.args[0].__class__ is Reference)
        self.assertEqual("test.dummy.Alpha", self.depsupport.args[0])
        self.assertTrue(self.depsupport.args[1].__class__ is Reference)
        self.assertEqual("test.dummy.Gamma", self.depsupport.args[1])

    test_binding_init_arg_class = _test_init_arg_class
    test_description_init_arg_class = _test_init_arg_class

    def _test_init_arg_func(self):
        self.proxy.init(test.dummy.create_alpha)
        self.assertTrue(self.depsupport.args[0].__class__ is Reference)
        self.assertEqual("test.dummy.create_alpha", self.depsupport.args[0])

    test_binding_init_arg_func = _test_init_arg_func
    test_description_init_arg_func = _test_init_arg_func

    def _test_init_arg_module(self):
        self.proxy.init(test.dummy)
        self.assertTrue(self.depsupport.args[0].__class__ is Reference)
        self.assertEqual("test.dummy", self.depsupport.args[0])

    test_binding_init_arg_module = _test_init_arg_module
    test_description_init_arg_module = _test_init_arg_module

    def _test_init_arg_value(self):
        self.proxy.init((2, 3, 5, 7))
        self.assertTrue(type(self.depsupport.args[0]) is tuple)
        self.assertEqual((2, 3, 5, 7), self.depsupport.args[0])

    test_binding_init_arg_value = _test_init_arg_value
    test_description_init_arg_value = _test_init_arg_value

    def _test_init_keyword_class(self):
        self.proxy.init(new_style=test.dummy.Alpha, old_style=test.dummy.Gamma)
        self.assertTrue(
            self.depsupport.keywords["new_style"].__class__ is Reference)
        self.assertEqual("test.dummy.Alpha",
                         self.depsupport.keywords["new_style"])
        self.assertTrue(
            self.depsupport.keywords["old_style"].__class__ is Reference)
        self.assertEqual("test.dummy.Gamma",
                         self.depsupport.keywords["old_style"])

    test_binding_init_keyword_class = _test_init_keyword_class
    test_description_init_keyword_class = _test_init_keyword_class

    def _test_init_keyword_func(self):
        self.proxy.init(function=test.dummy.create_alpha)
        self.assertTrue(
            self.depsupport.keywords["function"].__class__ is Reference)
        self.assertEqual("test.dummy.create_alpha",
                         self.depsupport.keywords["function"])

    test_binding_init_keyword_func = _test_init_keyword_func
    test_description_init_keyword_func = _test_init_keyword_func

    def _test_init_keyword_module(self):
        self.proxy.init(module=test.dummy)
        self.assertTrue(
            self.depsupport.keywords["module"].__class__ is Reference)
        self.assertEqual("test.dummy", self.depsupport.keywords["module"])

    test_binding_init_keyword_module = _test_init_keyword_module
    test_description_init_keyword_module = _test_init_keyword_module

    def _test_init_keyword_value(self):
        self.proxy.init(test=(2, 3, 5, 7))
        self.assertTrue(type(self.depsupport.keywords["test"]) is tuple)
        self.assertEqual((2, 3, 5, 7), self.depsupport.keywords["test"])

    test_binding_init_keyword_value = _test_init_keyword_value
    test_description_init_keyword_value = _test_init_keyword_value

    def _test_attributes_empty(self):
        self.assertEqual({}, self.depsupport.attributes)
        self.proxy.attributes()
        self.assertEqual({}, self.depsupport.attributes)

    test_binding_attributes_empty = _test_attributes_empty
    test_description_attributes_empty = _test_attributes_empty

    def _test_attributes_class(self):
        self.proxy.attributes(new_style=test.dummy.Alpha,
                              old_style=test.dummy.Gamma)
        self.assertTrue(
            self.depsupport.attributes["new_style"].__class__ is Reference)
        self.assertEqual("test.dummy.Alpha",
                         self.depsupport.attributes["new_style"])
        self.assertTrue(
            self.depsupport.attributes["old_style"].__class__ is Reference)
        self.assertEqual("test.dummy.Gamma",
                         self.depsupport.attributes["old_style"])

    test_binding_attributes_class = _test_attributes_class
    test_description_attributes_class = _test_attributes_class

    def _test_attributes_func(self):
        self.proxy.attributes(function=test.dummy.create_alpha)
        self.assertTrue(
            self.depsupport.attributes["function"].__class__ is Reference)
        self.assertEqual("test.dummy.create_alpha",
                         self.depsupport.attributes["function"])

    test_binding_attributes_func = _test_attributes_func
    test_description_attributes_func = _test_attributes_func

    def _test_attributes_module(self):
        self.proxy.attributes(module=test.dummy)
        self.assertTrue(
            self.depsupport.attributes["module"].__class__ is Reference)
        self.assertEqual("test.dummy", self.depsupport.attributes["module"])

    test_binding_attributes_module = _test_attributes_module
    test_description_attributes_module = _test_attributes_module

    def _test_attributes_value(self):
        self.proxy.attributes(test=(2, 3, 5, 7))
        self.assertTrue(type(self.depsupport.attributes["test"]) is tuple)
        self.assertEqual((2, 3, 5, 7), self.depsupport.attributes["test"])

    test_binding_attributes_value = _test_attributes_value
    test_description_attributes_value = _test_attributes_value

    def _test_attributes_nvpairs(self):
        self.proxy.attributes(("field", "FIELD"), ("set_value", "VALUE"))
        self.assertEqual(2, len(self.depsupport.attributes))
        self.assertEqual("FIELD", self.depsupport.attributes["field"])
        self.assertEqual("VALUE", self.depsupport.attributes["set_value"])

    test_binding_attributes_nvpairs = _test_attributes_nvpairs
    test_description_attributes_nvpairs = _test_attributes_nvpairs

    def _test_attributes_nvpairs_and_keywords(self):
        self.proxy.attributes(("field", "FIELD"), set_value="VALUE")
        self.assertEqual(2, len(self.depsupport.attributes))
        self.assertEqual("FIELD", self.depsupport.attributes["field"])
        self.assertEqual("VALUE", self.depsupport.attributes["set_value"])

    test_binding_attributes_nvpairs_and_keywords = \
        _test_attributes_nvpairs_and_keywords
    test_description_attributes_nvpairs_and_keywords = \
        _test_attributes_nvpairs_and_keywords


class BinderTest(unittest.TestCase):

    def setUp(self):
        binder_id = str(self).split()[0]
        self.binder = Binder(binder_id)

    def tearDown(self):
        self.binder = None

    def test_init_after_inject(self):
        eta = lifecycle_methods_binder.lookup("context-after-inject")
        self.assertFalse(eta.called_after_inject_raise)
        self.assertTrue(eta.called_context_after_inject)
        self.assertFalse(eta.called_template_after_inject)
        self.assertFalse(eta.called_component_after_inject)

    def test_init_before_clear(self):
        eta = lifecycle_methods_binder.lookup("context-before-clear")
        self.assertFalse(eta.called_before_clear_raise)
        self.assertFalse(eta.called_context_before_clear)
        self.assertFalse(eta.called_template_before_clear)
        self.assertFalse(eta.called_component_before_clear)
        self.assertEqual(["context-before-clear"],
                         lifecycle_methods_binder.clear_singletons())
        self.assertFalse(eta.called_before_clear_raise)
        self.assertTrue(eta.called_context_before_clear)
        self.assertFalse(eta.called_template_before_clear)
        self.assertFalse(eta.called_component_before_clear)

    def test_bind_defaults(self):
        binding = self.binder.bind("test.dummy.Alpha")
        component = binding._depsupport
        self.assertEqual("test.dummy.Alpha", component.unique_id)
        self.assertEqual("test.dummy.Alpha", component.dotted_name)
        self.assertIsNone(component.factory_name)
        self.assertIsNone(component.member_name)
        self.assertEqual(Strategy.PROTOTYPE, component.strategy)
        self.assertIsNone(component.parent_id)
        self.assertIsNone(component.after_inject)
        self.assertIsNone(component.before_clear)
        self.assertEqual([], component.args)
        self.assertEqual({}, component.keywords)
        self.assertEqual({}, component.attributes)

    def test_bind_reference(self):
        binding = self.binder.bind(test.dummy.Alpha)
        component = binding._depsupport
        self.assertEqual("test.dummy.Alpha", component.unique_id)
        self.assertEqual("test.dummy.Alpha", component.dotted_name)

    def test_bind_to(self):
        binding = self.binder.bind("alpha", to="test.dummy.Alpha")
        component = binding._depsupport
        self.assertEqual("alpha", component.unique_id)
        self.assertEqual("test.dummy.Alpha", component.dotted_name)

    def test_bind_to_reference(self):
        binding = self.binder.bind("alpha", to=test.dummy.Alpha)
        component = binding._depsupport
        self.assertEqual("alpha", component.unique_id)
        self.assertEqual("test.dummy.Alpha", component.dotted_name)

    def test_bind_factory_member_mutually_exclusive(self):
        self.assertRaises(AglyphError, self.binder.bind, "test.dummy",
                          factory="Epsilon.Zeta", member="Epsilon.ATTRIBUTE")

    def test_bind_factory(self):
        binding = self.binder.bind("test.dummy", factory="Epsilon.Zeta")
        self.assertEqual("Epsilon.Zeta", binding._depsupport.factory_name)

    def test_bind_member(self):
        binding = self.binder.bind("test.dummy", member="Epsilon.ATTRIBUTE")
        self.assertEqual("Epsilon.ATTRIBUTE", binding._depsupport.member_name)

    def test_bind_bad_strategy(self):
        self.assertRaises(ValueError, self.binder.bind, "test.dummy.Alpha",
                          strategy="spam")

    def test_bind_explicit_prototype(self):
        binding = self.binder.bind("test.dummy.Alpha", strategy="prototype")
        self.assertEqual("prototype", binding._depsupport.strategy)

    def test_bind_strategy_singleton(self):
        binding = self.binder.bind("test.dummy.Alpha", strategy="singleton")
        self.assertEqual("singleton", binding._depsupport.strategy)

    def test_bind_strategy_borg(self):
        binding = self.binder.bind("test.dummy.Alpha", strategy="borg")
        self.assertEqual("borg", binding._depsupport.strategy)

    def test_bind_strategy_weakref(self):
        binding = self.binder.bind("test.dummy.Alpha", strategy="weakref")
        self.assertEqual("weakref", binding._depsupport.strategy)

    def test_bind_parent(self):
        binding = self.binder.bind("test.dummy.Alpha", parent="alpha-parent")
        self.assertEqual("alpha-parent", binding._depsupport.parent_id)

    def test_bind_parent_reference(self):
        binding = self.binder.bind("test.dummy.Gamma", parent=test.dummy.Alpha)
        self.assertEqual("test.dummy.Alpha", binding._depsupport.parent_id)

    def test_bind_after_inject(self):
        binding = self.binder.bind("test.dummy.Alpha",
                                   after_inject="component_after_inject")
        self.assertEqual("component_after_inject",
                         binding._depsupport.after_inject)

    def test_bind_prototype_rejects_before_clear(self):
        binding = self.binder.bind("test.dummy.Alpha",
                                   before_clear="component_before_clear")
        self.assertIsNone(binding._depsupport.before_clear)

    def test_bind_singleton_before_clear(self):
        binding = self.binder.bind("test.dummy.Alpha", strategy="singleton",
                                   before_clear="component_before_clear")
        self.assertEqual("component_before_clear",
                         binding._depsupport.before_clear)

    def test_bind_borg_before_clear(self):
        binding = self.binder.bind("test.dummy.Alpha", strategy="borg",
                                   before_clear="component_before_clear")
        self.assertEqual("component_before_clear",
                         binding._depsupport.before_clear)

    def test_bind_weakref_before_clear(self):
        binding = self.binder.bind("test.dummy.Alpha", strategy="weakref",
                                   before_clear="component_before_clear")
        self.assertEqual("component_before_clear",
                         binding._depsupport.before_clear)

    def test_describe_defaults(self):
        description = self.binder.describe("test")
        template = description._depsupport
        self.assertEqual("test", template.unique_id)
        self.assertIsNone(template.parent_id)
        self.assertIsNone(template.after_inject)
        self.assertIsNone(template.before_clear)
        self.assertEqual([], template.args)
        self.assertEqual({}, template.keywords)
        self.assertEqual({}, template.attributes)

    def test_describe_parent(self):
        description = self.binder.describe("test", parent="test-parent")
        self.assertEqual("test-parent", description._depsupport.parent_id)

    def test_describe_parent_reference(self):
        description = self.binder.describe("test", parent=test.dummy.Alpha)
        self.assertEqual("test.dummy.Alpha", description._depsupport.parent_id)

    def test_describe_after_inject(self):
        description = self.binder.describe(
            "test", after_inject="template_after_inject")
        self.assertEqual("template_after_inject",
                         description._depsupport.after_inject)

    def test_describe_before_clear(self):
        description = self.binder.describe(
            "test", before_clear="template_before_clear")
        self.assertEqual("template_before_clear",
                         description._depsupport.before_clear)
"""

