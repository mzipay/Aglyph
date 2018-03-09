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

"""Test case and runner for :class:`aglyph.assembler.Assembler`."""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import functools
import logging
import unittest
import warnings

try:
    import threading
    threading_ = threading
    _has_threading = True
except:
    import dummy_threading
    threading_ = dummy_threading
    _has_threading = False

from aglyph import __version__, AglyphError
from aglyph._compat import is_python_2
from aglyph.assembler import Assembler
from aglyph.component import Evaluator
from aglyph.context import Context, XMLContext

from test import assertRaisesWithMessage, dummy, find_resource

__all__ = [
    "AssemblerTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_Assembler")
_log.info("has threading? %r (using %r)", _has_threading, threading_)


class AssemblerTest(unittest.TestCase):

    def setUp(self):
        self._assembler = Assembler(
            XMLContext(find_resource("resources/test_Assembler-context.xml")))

    def test_assemble_unknown_component_spec_fails(self):
        self.assertRaises(KeyError, self._assembler.assemble, "not.in.context")

    def test_detects_circular_dependency(self):
        e = AglyphError(
            "circular dependency detected: "
            "circular-2 > circular-3 > circular-1 > circular-2")
        assertRaisesWithMessage(
            self, e, self._assembler.assemble, "circular-2")

    # https://github.com/mzipay/Aglyph/issues/3
    @unittest.skipUnless(
        _has_threading, "can't test thread safety without _thread")
    def test_circular_dependency_check_is_threadsafe(self):
        assemble = self._assembler.assemble
        class AssemblyThread(threading_.Thread):
            def run(self):
                try:
                    assemble("not-circular-1")
                except AglyphError as e:
                    self.e = e
                else:
                    self.e = None
        threads = [AssemblyThread() for i in range(1000)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(0, len([t for t in threads if t.e is not None]))

    def test_cant_create_unrecognized_strategy(self):
        context = Context(self.id())
        (context.prototype("unrecognized-strategy").
            create("test.dummy.ModuleClass").init(None).register())
        context["unrecognized-strategy"]._strategy = "unrecognized"
        assembler = Assembler(context)
        self.assertRaises(
            AttributeError, assembler.assemble, "unrecognized-strategy")

    def test_factory_name_initializer(self):
        obj = self._assembler.assemble("factory-init")
        self.assertEqual(dummy.DEFAULT, obj()) # obj is nested_function

    def test_member_name_initializer(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            obj = self._assembler.assemble("member-init")

        self.assertTrue(obj is dummy.MODULE_MEMBER)

    def test_component_args_extend_parent_args(self):
        obj = self._assembler.assemble("component-args")
        self.assertEqual(1, obj.arg)
        self.assertEqual(2, obj.keyword)

    def test_component_keywords_extend_parent_keywords(self):
        obj = self._assembler.assemble("component-keywords")
        self.assertEqual(2, obj.keyword)

    def test_reference_arg_is_resolved(self):
        obj = self._assembler.assemble("ref-arg")
        self.assertEqual(7, obj.arg)

    def test_reference_keyword_is_resolved(self):
        obj = self._assembler.assemble("ref-kw")
        self.assertEqual(7, obj.keyword)

    def test_evaluator_arg_is_resolved(self):
        assert isinstance(
            self._assembler._context["eval-arg"].args[0], Evaluator)
        obj = self._assembler.assemble("eval-arg")
        self.assertEqual(["test"], obj.arg)

    def test_evaluator_keyword_is_resolved(self):
        assert isinstance(
            self._assembler._context["eval-kw"].keywords["keyword"], Evaluator)
        obj = self._assembler.assemble("eval-kw")
        self.assertEqual(["test"], obj.keyword)

    def test_partial_arg_is_resolved(self):
        context = Context(self.id())
        p = functools.partial(int, "0b1001111", base=2)
        (context.prototype("partial-arg").
            create("test.dummy.ModuleClass").init(p).register())
        assembler = Assembler(context)
        obj = assembler.assemble("partial-arg")
        self.assertEqual(79, obj.arg)

    def test_partial_keyword_is_resolved(self):
        context = Context(self.id())
        p = functools.partial(int, "0b1001111", base=2)
        (context.prototype("partial-kw").
            create(dummy.ModuleClass).init(None, keyword=p).register())
        assembler = Assembler(context)
        obj = assembler.assemble("partial-kw")
        self.assertEqual(79, obj.keyword)

    def test_value_arg_is_resolved(self):
        obj = self._assembler.assemble("value-arg-kw")
        self.assertEqual(79, obj.arg)

    def test_value_keyword_is_resolved(self):
        obj = self._assembler.assemble("value-arg-kw")
        self.assertEqual(97, obj.keyword)

    # https://github.com/mzipay/Aglyph/issues/2
    def test_builtin_immutable_initialized(self):
        s = self._assembler.assemble(
            ("__builtin__" if is_python_2 else "builtins") + ".str")
        self.assertEqual("test", s)

    def test_initialization_failure_raises_AglyphError(self):
        try:
            self._assembler.assemble("failing-class-init")
        except AglyphError as e:
            self.assertTrue(type(e.cause) is RuntimeError)
            self.assertEqual("__init__ RAISE", str(e.cause))
        else:
            self.fail(
                "assemble('failing-class-init') did not raise AglyphError")

    def test_member_init_with_args_issues_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            obj = self._assembler.assemble("member-init-with-args")

            self.assertEqual(
                "ignoring args and keywords for component "
                    "'member-init-with-args' (uses member_name assembly)",
                str(w[0].message))

        self.assertTrue(obj is dummy.ModuleClass.CLASS_MEMBER)

    def test_member_init_with_kwargs_issues_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            obj = self._assembler.assemble("member-init-with-kwargs")

            self.assertEqual(
                "ignoring args and keywords for component "
                    "'member-init-with-kwargs' (uses member_name assembly)",
                str(w[0].message))

        self.assertTrue(obj is dummy.MODULE_MEMBER)

    def test_member_call_lifecycle_method_issues_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            obj = self._assembler.assemble("member-init")

            self.assertEqual(
                "component 'member-init' specifies member_name; it is "
                    "possible that the after_inject "
                    "MODULE_MEMBER.context_after_inject() method may be "
                    "called MULTIPLE times on %r" % obj,
                str(w[0].message))
        self.assertTrue(obj is dummy.MODULE_MEMBER)


def suite():
    return unittest.makeSuite(AssemblerTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

