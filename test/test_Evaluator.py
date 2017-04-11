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

"""Test case and runner for :class:`aglyph.component.Evaluator`."""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

from functools import partial
import logging
import unittest

from aglyph import __version__
from aglyph.component import Evaluator, Reference

from test import dummy
from test.test_InitializationSupport import InitializationSupportTest

__all__ = [
    "EvaluatorTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_Evaluator")


class _MockAssembler(object):

    def assemble(self, component_spec):
        if component_spec == "test.dummy.ModuleClass":
            return dummy.ModuleClass("test")
        elif component_spec == "number":
            return 101
        else:
            raise RuntimeError(
                "_MockAssembler can't assemble %r" % component_spec)


class EvaluatorTest(InitializationSupportTest):

    @classmethod
    def setUpClass(cls):
        cls._assembler = _MockAssembler()

    def setUp(self):
        # for InitializationSupportTest
        self._support = Evaluator(object)

    def test_initarg_is_required(self):
        self.assertRaises(TypeError, Evaluator)

    def test_rejects_non_callable_factory(self):
        self.assertRaises(TypeError, Evaluator, None)

    def test_accepts_callable_factory(self):
        evaluator = Evaluator(int)
        self.assertTrue(evaluator.factory is int)

    def test_accepts_args(self):
        evaluator = Evaluator(int, "79")
        self.assertEqual(["79"], evaluator.args)

    def test_accepts_keywords(self):
        evaluator = Evaluator(int, "1001111", base=2)
        self.assertEqual({"base": 2}, evaluator.keywords)

    def test_initialization_support(self):
        evaluator = Evaluator(int)
        evaluator.args.append("1001111")
        evaluator.keywords.update(base=2)
        self.assertEqual(["1001111"], evaluator.args)
        self.assertEqual({"base": 2}, evaluator.keywords)

    def test_simple_evaluation(self):
        evaluator = Evaluator(int, "1001111", base=2)
        self.assertEqual(79, evaluator(None))

    def test_with_partial_arg(self):
        evaluator = Evaluator(hex, partial(int, "79"))
        self.assertEqual("0x4f", evaluator(None))

    def test_with_partial_keyword(self):
        evaluator = Evaluator(dict, number=partial(int, "79"))
        self.assertEqual({"number": 79}, evaluator(None))

    def test_with_evaluator_arg(self):
        evaluator = Evaluator(hex, Evaluator(int, "79"))
        self.assertEqual("0x4f", evaluator(None))

    def test_with_evaluator_keyword(self):
        evaluator = Evaluator(dict, number=Evaluator(int, "79"))
        self.assertEqual({"number": 79}, evaluator(None))

    def test_with_reference_arg(self):
        evaluator = Evaluator(
            getattr, Reference("test.dummy.ModuleClass"), "arg")
        self.assertEqual("test", evaluator(self._assembler))

    def test_with_reference_keyword(self):
        evaluator = Evaluator(dict, test=Reference("test.dummy.ModuleClass"))
        d = evaluator(self._assembler)
        self.assertEqual(1, len(d))
        self.assertTrue(isinstance(d["test"], dummy.ModuleClass))
        self.assertEqual("test", d["test"].arg)

    def test_with_dict_arg_values_resolved(self):
        arg = {
            "partial": partial(int, "79"),
            "evaluator": Evaluator(int, "97"),
            "reference": Reference("number"),
        }
        evaluator = Evaluator(dict, arg)
        self.assertEqual(
            {"partial": 79, "evaluator": 97, "reference": 101},
            evaluator(self._assembler))

    def test_with_dict_keyword_values_resolved(self):
        arg = {
            "partial": partial(int, "79"),
            "evaluator": Evaluator(int, "97"),
            "reference": Reference("number"),
        }
        evaluator = Evaluator(dict, keyword=arg)
        self.assertEqual(
            {"keyword": {"partial": 79, "evaluator": 97, "reference": 101}},
            evaluator(self._assembler))

    def test_with_nonstr_sequence_arg_values_resolved(self):
        arg = [
            ("partial", partial(int, "79")),
            ("evaluator", Evaluator(int, "97")),
            ("reference", Reference("number"))
        ]
        evaluator = Evaluator(dict, arg)
        self.assertEqual(
            {"partial": 79, "evaluator": 97, "reference": 101},
            evaluator(self._assembler))

    def test_with_nonstr_sequence_keyword_values_resolved(self):
        arg = [
            ("partial", partial(int, "79")),
            ("evaluator", Evaluator(int, "97")),
            ("reference", Reference("number"))
        ]
        evaluator = Evaluator(dict, keyword=arg)
        self.assertEqual(
            {"keyword":
                [("partial", 79), ("evaluator", 97), ("reference", 101)]},
            evaluator(self._assembler))


def suite():
    return unittest.makeSuite(EvaluatorTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

