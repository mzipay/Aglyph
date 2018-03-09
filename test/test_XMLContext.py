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

"""Test case and runner for :class:`aglyph.context.XMLContext`."""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

from ast import literal_eval
import codecs
from collections import OrderedDict
from functools import partial
import logging
import sys
import unittest

try:
    from io import BytesIO as bytebuf
except:
    from StringIO import StringIO as bytebuf

from aglyph import AglyphError, __version__
from aglyph._compat import is_python_2, is_python_3
from aglyph.component import Component, Evaluator, Reference, Template
from aglyph.context import XMLContext

from test import assertRaisesWithMessage, find_resource, read_resource
from test.test_Context import _BaseContextTest

__all__ = [
    "XMLContextTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_XMLContext")
_log.info("bytebuf is %r", bytebuf)

_u_motleycrue = read_resource("resources/motleycrue.txt")


class XMLContextTest(_BaseContextTest):

    def setUp(self):
        # for _BaseContextTest
        self._context = XMLContext(
            find_resource("resources/test_XMLContext-empty.xml"))
        # for individual tests (may be None)
        self._uresource = read_resource("resources/%s.xml" % self.id())

    def test_can_read_from_stream(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        self.assertEqual("test_can_read_from_stream", context.context_id)

    def test_can_augment_context_after_parsing(self):
        component = Component(self.id())
        self._context.register(component)
        self.assertTrue(self._context[self.id()] is component)

    # overridden from _BaseContextTest
    def test_context_id_cannot_be_none(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        e_expected = AglyphError("XMLContext ID must not be None or empty")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    # overridden from _BaseContextTest
    def test_context_id_cannot_be_empty(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        e_expected = AglyphError("XMLContext ID must not be None or empty")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_context_can_be_empty(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        self.assertEqual(0, len(context))

    def test_template_id_is_required(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        e_expected = ValueError(
            "Template unique ID must not be None or empty")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_parse_template(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        template = context["test"]
        self.assertTrue(type(template) is Template)
        self.assertEqual("parent", template.parent_id)
        self.assertEqual("after_inject", template.after_inject)
        self.assertEqual("before_clear", template.before_clear)
        self.assertEqual([], template.args)
        self.assertEqual({}, template.keywords)
        self.assertTrue(type(template.attributes) is OrderedDict)
        self.assertEqual(OrderedDict(), template.attributes)

    def test_process_dependencies_unexpected_children(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        e_expected = AglyphError("unexpected element: template/unexpected")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_process_dependencies_init_attributes(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        template = context["test"]
        self.assertEqual(0, len(template.args))
        self.assertEqual(0, len(template.keywords))
        self.assertEqual(0, len(template.attributes))

    def test_process_dependencies_init(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        template = context["test"]
        self.assertEqual(0, len(template.args))
        self.assertEqual(0, len(template.keywords))

    def test_process_dependencies_attributes(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        self.assertEqual(0, len(context["test"].attributes))

    def test_process_init_unexpected_children(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        e_expected = AglyphError("unexpected element: init/unexpected")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_process_init_args(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        template = context["test"]
        self.assertEqual(79, template.args[0])
        self.assertEqual(97, template.keywords["keyword"])

    def test_arg_cannot_be_empty(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        e_expected = AglyphError(
            "<arg> must contain exactly one child element; found no children")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_arg_keyword_cannot_be_empty(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        e_expected = AglyphError("arg/@keyword cannot be empty")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_arg_rejects_multiple_children(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        e_expected = AglyphError(
            "<arg> must contain exactly one child element; "
            "found arg/int, arg/int")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_arg_reference_attribute(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        template = context["test"]
        self.assertTrue(type(template.args[0]) is Reference)
        self.assertEqual("ref1", template.args[0])
        self.assertTrue(type(template.args[1]) is Reference)
        self.assertEqual("ref2", template.args[1])
        self.assertTrue(type(template.keywords["kw1"]) is Reference)
        self.assertEqual("ref3", template.keywords["kw1"])
        self.assertTrue(type(template.keywords["kw2"]) is Reference)
        self.assertEqual("ref4", template.keywords["kw2"])

    def test_arg_eval(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        template = context["test"]
        self.assertTrue(type(template.args[0]) is partial)
        self.assertTrue(template.args[0].func is literal_eval)
        self.assertEqual({"primes": [2, 3, 5, 7]}, template.args[0]())
        self.assertTrue(type(template.keywords["kw"]) is partial)
        self.assertTrue(template.keywords["kw"].func is literal_eval)
        self.assertEqual([None, True, False], template.keywords["kw"]())

    def test_parse_False(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        self.assertEqual([False], context["test"].args)

    def test_parse_True(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        self.assertEqual([True], context["test"].args)

    def test_parse_None(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        self.assertEqual([None], context["test"].args)

    def test_parse_bytes(self):
        # encode document as windows-1252 to force explicit transcoding to utf-8
        stream = bytebuf(self._uresource.encode("windows-1252"))
        # the default_encoding here is what is used to encode the value - NOT
        # the document encoding!
        context = XMLContext(stream, default_encoding="utf-8")
        self.assertEqual(
            [_u_motleycrue.encode("utf-8")], context["test"].args)

    def test_parse_bytes_encoding_latin1(self):
        # encode document as utf-8 to force explicit transcoding to latin1
        stream = bytebuf(self._uresource.encode("utf-8"))
        # the explicit encoding="latin1" on the <bytes> element overrides this
        # default encoding
        context = XMLContext(stream, default_encoding="utf-8")
        self.assertEqual(
            [_u_motleycrue.encode("latin1")], context["test"].args)

    @unittest.skipUnless(
        is_python_2, "<str> evaluates to unicode text under Python 3")
    def test_parse_str_as_data(self):
        # encode document as utf-8 to force explicit transcoding to windows-1252
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream, default_encoding="utf-8")
        self.assertEqual(
            [_u_motleycrue.encode("windows-1252")], context["test"].args)

    @unittest.skipUnless(
        is_python_3, "<str> evaluates to encoded bytes under Python 2")
    def test_parse_str_as_text(self):
        # explicit transcoding to windows-1252 here should be IGNORED
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream, default_encoding="utf-8")
        self.assertEqual([_u_motleycrue], context["test"].args)

    def test_parse_unicode(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream, default_encoding="utf-8")
        self.assertEqual([_u_motleycrue], context["test"].args)

    def test_parse_int(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        self.assertEqual([79], context["test"].args)

    def test_parse_int_empty(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        self.assertEqual([0], context["test"].args)

    def test_parse_int_base(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        self.assertEqual([79], context["test"].args)

    @unittest.skipUnless(
        is_python_2,
        "int can only evaluate to long under Python 2 (see also PEP-237)")
    def test_parse_int_long(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        self.assertTrue(type(context["test"].args[0]) is long)
        self.assertEqual([2**64], context["test"].args)

    def test_parse_float(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        self.assertEqual([7.9], context["test"].args)

    def test_parse_float_empty(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        self.assertEqual([0.0], context["test"].args)

    def test_parse_tuple(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        evaluator = context["test"].args[0]
        self.assertTrue(type(evaluator) is Evaluator)
        self.assertTrue(evaluator.factory is tuple)
        # the argument to the evaluator factory is itself a sequence (list)
        self.assertEqual([[_u_motleycrue, 79, None]], evaluator.args)

    def test_parse_tuple_empty(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        # no Evaluator for empty tuples (they're immutable)
        self.assertEqual([tuple()], context["test"].args)

    def test_parse_tuple_nested_eval(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        evaluator = context["test"].args[0]
        self.assertTrue(type(evaluator) is Evaluator)
        self.assertTrue(evaluator.factory is tuple)
        # the argument to the evaluator factory is itself a sequence (list)
        self.assertEqual(1, len(evaluator.args))
        for p in evaluator.args[0]:
            self.assertTrue(type(p) is partial)
            self.assertTrue(p.func is literal_eval)
        self.assertEqual((79, True, "test"), evaluator(None))

    def test_parse_list(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        evaluator = context["test"].args[0]
        self.assertTrue(type(evaluator) is Evaluator)
        self.assertTrue(evaluator.factory is list)
        # the argument to the evaluator factory is itself a sequence (list)
        self.assertEqual([[_u_motleycrue, 79, None]], evaluator.args)

    def test_parse_list_empty(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        evaluator = context["test"].args[0]
        self.assertTrue(type(evaluator) is Evaluator)
        self.assertTrue(evaluator.factory is list)
        self.assertEqual([[]], evaluator.args)

    def test_parse_list_nested_eval(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        evaluator = context["test"].args[0]
        self.assertTrue(type(evaluator) is Evaluator)
        self.assertTrue(evaluator.factory is list)
        # the argument to the evaluator factory is itself a sequence (list)
        self.assertEqual(1, len(evaluator.args))
        for p in evaluator.args[0]:
            self.assertTrue(type(p) is partial)
            self.assertTrue(p.func is literal_eval)
        self.assertEqual([79, True, "test"], evaluator(None))

    def test_parse_dict(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        evaluator = context["test"].args[0]
        self.assertTrue(type(evaluator) is Evaluator)
        self.assertTrue(evaluator.factory is dict)
        self.assertEqual(
            [[("seventy-nine", 79), (97, "ninety-seven")]], evaluator.args)

    def test_parse_dict_empty(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        evaluator = context["test"].args[0]
        self.assertTrue(type(evaluator) is Evaluator)
        self.assertTrue(evaluator.factory is dict)
        self.assertEqual([[]], evaluator.args)
        self.assertEqual(0, len(evaluator.keywords))

    def test_parse_dict_unexpected_children(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        e_expected = AglyphError("unexpected element: dict/unexpected")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_parse_dict_item_unexpected_children(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        e_expected = AglyphError(
            "expected item/key, item/value; found item/unexpected")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_dict_item_key_cannot_be_empty(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        e_expected = AglyphError(
            "<key> must contain exactly one child element; found no children")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_dict_item_key_unexpected_children(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        e_expected = AglyphError("unexpected element: key/unexpected")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_dict_item_key_rejects_multiple_children(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        e_expected = AglyphError(
            "<key> must contain exactly one child element; "
            "found key/str, key/int")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_dict_item_value_cannot_be_empty(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        e_expected = AglyphError(
            "<value> must contain exactly one child element; found no children")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_dict_item_value_unexpected_children(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        e_expected = AglyphError("unexpected element: value/unexpected")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_dict_item_value_rejects_multiple_children(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        e_expected = AglyphError(
            "<value> must contain exactly one child element; "
            "found value/str, value/int")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_parse_dict_nested_eval(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        evaluator = context["test"].args[0]
        self.assertTrue(type(evaluator) is Evaluator)
        self.assertTrue(evaluator.factory is dict)
        # evaluator args is itself a sequence; Aglyph uses list-of-tuples for
        # the keys and values
        self.assertTrue(type(evaluator.args[0][0][0]) is partial)
        self.assertTrue(type(evaluator.args[0][1][1]) is partial)
        self.assertEqual({"seven": 7, 9: "nine"}, evaluator(None))

    def test_parse_set(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        evaluator = context["test"].args[0]
        self.assertTrue(type(evaluator) is Evaluator)
        self.assertTrue(evaluator.factory is set)
        # the argument to the evaluator factory is itself a sequence (list)
        self.assertEqual([[_u_motleycrue, 79, None]], evaluator.args)

    def test_parse_set_empty(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        evaluator = context["test"].args[0]
        self.assertTrue(type(evaluator) is Evaluator)
        self.assertTrue(evaluator.factory is set)
        self.assertEqual([[]], evaluator.args)

    def test_parse_set_nested_eval(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        evaluator = context["test"].args[0]
        self.assertTrue(type(evaluator) is Evaluator)
        self.assertTrue(evaluator.factory is set)
        # the argument to the evaluator factory is itself a sequence (list)
        self.assertEqual(1, len(evaluator.args))
        for p in evaluator.args[0]:
            self.assertTrue(type(p) is partial)
            self.assertTrue(p.func is literal_eval)
        self.assertEqual(set([79, True, "test"]), evaluator(None))

    def test_process_attributes_unexpected_children(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        e_expected = AglyphError("unexpected element: attributes/unexpected")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_process_attributes_attribute(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        self.assertEqual({"attr": 79}, context["test"].attributes)

    def test_attribute_name_is_required(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        e_expected = AglyphError(
            "attribute/@name is required and cannot be empty")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_attribute_name_cannot_be_empty(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        e_expected = AglyphError(
            "attribute/@name is required and cannot be empty")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_attribute_cannot_be_empty(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        e_expected = AglyphError(
            "<attribute> must contain exactly one child element; "
            "found no children")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_attribute_rejects_multiple_children(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        e_expected = AglyphError(
            "<attribute> must contain exactly one child element; "
            "found attribute/str, attribute/int")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_attribute_reference_attribute(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        template = context["test"]
        self.assertTrue(type(template.attributes["attr1"]) is Reference)
        self.assertEqual("ref1", template.attributes["attr1"])
        self.assertTrue(type(template.attributes["attr2"]) is Reference)
        self.assertEqual("ref2", template.attributes["attr2"])

    def test_attribute_eval(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        template = context["test"]
        self.assertTrue(type(template.attributes["primes"]) is partial)
        self.assertTrue(template.attributes["primes"].func is literal_eval)
        self.assertEqual((2, 3, 5, 7), template.attributes["primes"]())

    def test_parse_component_implicit(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        component = context["implicit.dotted.name"]
        self.assertTrue(type(component) is Component)
        self.assertEqual("implicit.dotted.name", component.dotted_name)

    def test_parse_component_explicit(self):
        stream = bytebuf(self._uresource.encode("utf-8"))
        context = XMLContext(stream)
        component = context["test"]
        self.assertTrue(type(component) is Component)
        self.assertEqual("explicit.dotted.name", component.dotted_name)
        self.assertEqual("singleton", component.strategy)
        self.assertEqual("parent", component.parent_id)
        self.assertEqual("after_inject", component.after_inject)
        self.assertEqual("before_clear", component.before_clear)


def suite():
    return unittest.makeSuite(XMLContextTest)


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())

