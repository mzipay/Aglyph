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

"""Test case and runner for :class:`aglyph.context.XMLContext`."""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"

from collections import OrderedDict
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

from test import (
    as_encoded_bytes,
    as_unicode_text,
    assertRaisesWithMessage,
    find_basename,
)
from test.test_Context import _BaseContextTest

__all__ = [
    "XMLContextTest",
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_log = logging.getLogger("test.test_XMLContext")
_log.info("bytebuf is %r", bytebuf)

_document_prologue = (
    '<?xml version="1.0" encoding="%s" ?>\n'
    '<!DOCTYPE context SYSTEM "../resources/aglyph-context.dtd">\n'
)


def _context_as_stream(context_xml, document_encoding="utf-8"):
    document_xml = (_document_prologue % document_encoding) + context_xml
    return bytebuf(as_encoded_bytes(document_xml, document_encoding))


class XMLContextTest(_BaseContextTest):

    def setUp(self):
        # for _BaseContextTest
        self._context = XMLContext(find_basename("test_XMLContext-empty.xml"))

    def test_can_read_from_stream(self):
        stream = _context_as_stream('<context id="%s" />' % self.id())
        context = XMLContext(stream)
        self.assertEqual(self.id(), context.context_id)

    def test_can_augment_context_after_parsing(self):
        component = Component(self.id())
        self._context.register(component)
        self.assertTrue(self._context[self.id()] is component)

    # overridden from _BaseContextTest
    def test_context_id_cannot_be_none(self):
        stream = _context_as_stream('<context />')
        e_expected = AglyphError("XMLContext ID must not be None or empty")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    # overridden from _BaseContextTest
    def test_context_id_cannot_be_empty(self):
        stream = _context_as_stream('<context id="" />')
        e_expected = AglyphError("XMLContext ID must not be None or empty")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_context_can_be_empty(self):
        stream = _context_as_stream('<context id="test" />')
        context = XMLContext(stream)
        self.assertEqual(0, len(context))

    def test_template_id_is_required(self):
        stream = _context_as_stream(
            '<context id="test">'
                '<template />'
            '</context>'
        )
        e_expected = AglyphError(
            "Template unique ID must not be None or empty")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_parse_template(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template '
                        'id="%s" '
                        'parent-id="parent" '
                        'after-inject="after_inject" '
                        'before-clear="before_clear" />'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        template = context[self.id()]
        self.assertTrue(type(template) is Template)
        self.assertEqual("parent", template.parent_id)
        self.assertEqual("after_inject", template.after_inject)
        self.assertEqual("before_clear", template.before_clear)
        self.assertEqual([], template.args)
        self.assertEqual({}, template.keywords)
        self.assertTrue(type(template.attributes) is OrderedDict)
        self.assertEqual(OrderedDict(), template.attributes)

    def test_process_dependencies_unexpected_children(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<unexpected />'
                '</template>'
            '</context>'
        ) % self.id())
        e_expected = AglyphError("unexpected element: template/unexpected")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_process_dependencies_init_attributes(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init />'
                    '<attributes />'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        template = context[self.id()]
        self.assertEqual(0, len(template.args))
        self.assertEqual(0, len(template.keywords))
        self.assertEqual(0, len(template.attributes))

    def test_process_dependencies_init(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init />'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        template = context[self.id()]
        self.assertEqual(0, len(template.args))
        self.assertEqual(0, len(template.keywords))

    def test_process_dependencies_attributes(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<attributes />'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        self.assertEqual(0, len(context[self.id()].attributes))

    def test_process_init_unexpected_children(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<unexpected />'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        e_expected = AglyphError("unexpected element: init/unexpected")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_process_init_args(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg><int>79</int></arg>'
                        '<arg keyword="keyword"><int>97</int></arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        template = context[self.id()]
        self.assertEqual(79, template.args[0])
        self.assertEqual(97, template.keywords["keyword"])

    def test_arg_cannot_be_empty(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg />'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        e_expected = AglyphError(
            "<arg> must contain exactly one child element; found no children")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_arg_keyword_cannot_be_empty(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg keyword=""><str>string</str></arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        e_expected = AglyphError("arg/@keyword cannot be empty")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_arg_rejects_multiple_children(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<int>79</int>'
                            '<int>97</int>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        e_expected = AglyphError(
            "<arg> must contain exactly one child element; "
            "found arg/int, arg/int")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_arg_reference_attribute(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg reference="ref1" />'
                        '<arg><reference id="ref2" /></arg>'
                        '<arg keyword="kw1" reference="ref3" />'
                        '<arg keyword="kw2"><reference id="ref4" /></arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        template = context[self.id()]
        self.assertTrue(type(template.args[0]) is Reference)
        self.assertEqual("ref1", template.args[0])
        self.assertTrue(type(template.args[1]) is Reference)
        self.assertEqual("ref2", template.args[1])
        self.assertTrue(type(template.keywords["kw1"]) is Reference)
        self.assertEqual("ref3", template.keywords["kw1"])
        self.assertTrue(type(template.keywords["kw2"]) is Reference)
        self.assertEqual("ref4", template.keywords["kw2"])

    def test_parse_False(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg><False /></arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        self.assertEqual([False], context[self.id()].args)

    def test_parse_True(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg><True /></arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        self.assertEqual([True], context[self.id()].args)

    def test_parse_None(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg><None /></arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        self.assertEqual([None], context[self.id()].args)

    def test_parse_bytes(self):
        # encode document as cp1252 to force explicit transcoding to utf-8
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<bytes>Mötley Crüe</bytes>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id(), document_encoding="cp1252")
        # the default_encoding here is what is used to encode the value - NOT
        # the document encoding!
        context = XMLContext(stream, default_encoding="utf-8")
        self.assertEqual(
            [as_encoded_bytes("Mötley Crüe", "utf-8")],
            context[self.id()].args)

    def test_parse_bytes_encoding_latin1(self):
        # encode document as utf-8 t force explicit transcoding to latin1
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<bytes encoding="latin1">Mötley Crüe</bytes>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        # the explicit encoding="latin1" on the <bytes> element overrides this
        # default encoding
        context = XMLContext(stream, default_encoding="utf-8")
        self.assertEqual(
            [as_encoded_bytes("Mötley Crüe", "latin1")],
            context[self.id()].args)

    @unittest.skipUnless(
        is_python_2, "<str> evaluates to unicode text under Python 3")
    def test_parse_str_as_data(self):
        # encode document as utf-8 to force explicit transcoding to cp1252
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<str encoding="cp1252">Mötley Crüe</str>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream, default_encoding="utf-8")
        self.assertEqual(
            [as_encoded_bytes("Mötley Crüe", "cp1252")],
            context[self.id()].args)

    @unittest.skipUnless(
        is_python_3, "<str> evaluates to encoded bytes under Python 2")
    def test_parse_str_as_text(self):
        # explicit transcoding to cp1252 here should be IGNORED
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<str encoding="cp1252">Mötley Crüe</str>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream, default_encoding="utf-8")
        self.assertEqual(
            [as_unicode_text("Mötley Crüe")], context[self.id()].args)

    def test_parse_unicode(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<unicode>Mötley Crüe</unicode>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream, default_encoding="utf-8")
        self.assertEqual(
            [as_unicode_text("Mötley Crüe")], context[self.id()].args)

    def test_parse_int(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<int>79</int>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        self.assertEqual([79], context[self.id()].args)

    def test_parse_int_empty(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<int />'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        self.assertEqual([0], context[self.id()].args)

    def test_parse_int_base(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<int base="2">1001111</int>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        self.assertEqual([79], context[self.id()].args)

    @unittest.skipUnless(
        is_python_2,
        "int can only evaluate to long under Python 2 (see also PEP-237)")
    def test_parse_int_long(self):
        longint = sys.maxint + 1
        s_longint = str(longint)
        if s_longint[-1] == 'L':
            s_longint = s_longint[:-1]
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<int>%s</int>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % (self.id(), s_longint))
        context = XMLContext(stream)
        self.assertTrue(type(context[self.id()].args[0]) is long)
        self.assertEqual([longint], context[self.id()].args)

    def test_parse_float(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<float>7.9</float>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        self.assertEqual([7.9], context[self.id()].args)

    def test_parse_float_empty(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<float />'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        self.assertEqual([0.0], context[self.id()].args)

    def test_parse_tuple(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<tuple>'
                                '<unicode>Mötley Crüe</unicode>'
                                '<int>79</int>'
                                '<None />'
                            '</tuple>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        evaluator = context[self.id()].args[0]
        self.assertTrue(type(evaluator) is Evaluator)
        self.assertTrue(evaluator.factory is tuple)
        # the argument to the evaluator factory is itself a sequence (list)
        self.assertEqual(
            [[as_unicode_text("Mötley Crüe"), 79, None]], evaluator.args)

    def test_parse_tuple_empty(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<tuple />'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        # no Evaluator for empty tuples (they're immutable)
        self.assertEqual([tuple()], context[self.id()].args)

    def test_parse_list(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<list>'
                                '<unicode>Mötley Crüe</unicode>'
                                '<int>79</int>'
                                '<None />'
                            '</list>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        evaluator = context[self.id()].args[0]
        self.assertTrue(type(evaluator) is Evaluator)
        self.assertTrue(evaluator.factory is list)
        # the argument to the evaluator factory is itself a sequence (list)
        self.assertEqual(
            [[as_unicode_text("Mötley Crüe"), 79, None]], evaluator.args)

    def test_parse_list_empty(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<list />'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        evaluator = context[self.id()].args[0]
        self.assertTrue(type(evaluator) is Evaluator)
        self.assertTrue(evaluator.factory is list)
        self.assertEqual([[]], evaluator.args)

    def test_parse_dict(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<dict>'
                                '<item>'
                                    '<key><str>seventy-nine</str></key>'
                                    '<value><int>79</int></value>'
                                '</item>'
                                '<item>'
                                    '<key><int>97</int></key>'
                                    '<value><str>ninety-seven</str></value>'
                                '</item>'
                            '</dict>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        evaluator = context[self.id()].args[0]
        self.assertTrue(type(evaluator) is Evaluator)
        self.assertTrue(evaluator.factory is dict)
        self.assertEqual(
            [[("seventy-nine", 79), (97, "ninety-seven")]], evaluator.args)

    def test_parse_dict_empty(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<dict />'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        evaluator = context[self.id()].args[0]
        self.assertTrue(type(evaluator) is Evaluator)
        self.assertTrue(evaluator.factory is dict)
        self.assertEqual([[]], evaluator.args)
        self.assertEqual(0, len(evaluator.keywords))

    def test_parse_dict_unexpected_children(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<dict>'
                                '<unexpected />'
                            '</dict>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        e_expected = AglyphError("unexpected element: dict/unexpected")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_parse_dict_item_unexpected_children(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<dict>'
                                '<item>'
                                    '<unexpected />'
                                '</item>'
                            '</dict>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        e_expected = AglyphError(
            "expected item/key, item/value; found item/unexpected")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_dict_item_key_cannot_be_empty(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<dict>'
                                '<item>'
                                    '<key />'
                                    '<value><str>value</str></value>'
                                '</item>'
                            '</dict>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        e_expected = AglyphError(
            "<key> must contain exactly one child element; found no children")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_dict_item_key_unexpected_children(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<dict>'
                                '<item>'
                                    '<key><unexpected /></key>'
                                    '<value><str>value</str></value>'
                                '</item>'
                            '</dict>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        e_expected = AglyphError("unexpected element: key/unexpected")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_dict_item_key_rejects_multiple_children(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<dict>'
                                '<item>'
                                    '<key>'
                                        '<str>key</str>'
                                        '<int>79</int>'
                                    '</key>'
                                    '<value><str>value</str></value>'
                                '</item>'
                            '</dict>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        e_expected = AglyphError(
            "<key> must contain exactly one child element; "
            "found key/str, key/int")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_dict_item_value_cannot_be_empty(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<dict>'
                                '<item>'
                                    '<key><str>key</str></key>'
                                    '<value />'
                                '</item>'
                            '</dict>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        e_expected = AglyphError(
            "<value> must contain exactly one child element; found no children")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_dict_item_value_unexpected_children(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<dict>'
                                '<item>'
                                    '<key><str>key</str></key>'
                                    '<value><unexpected /></value>'
                                '</item>'
                            '</dict>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        e_expected = AglyphError("unexpected element: value/unexpected")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_dict_item_value_rejects_multiple_children(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<dict>'
                                '<item>'
                                    '<key><str>key</str></key>'
                                    '<value>'
                                        '<str>value</str>'
                                        '<int>79</int>'
                                    '</value>'
                                '</item>'
                            '</dict>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        e_expected = AglyphError(
            "<value> must contain exactly one child element; "
            "found value/str, value/int")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_parse_set(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<set>'
                                '<unicode>Mötley Crüe</unicode>'
                                '<int>79</int>'
                                '<None />'
                            '</set>'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        evaluator = context[self.id()].args[0]
        self.assertTrue(type(evaluator) is Evaluator)
        self.assertTrue(evaluator.factory is set)
        # the argument to the evaluator factory is itself a sequence (list)
        self.assertEqual(
            [[as_unicode_text("Mötley Crüe"), 79, None]], evaluator.args)

    def test_parse_set_empty(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<init>'
                        '<arg>'
                            '<set />'
                        '</arg>'
                    '</init>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        evaluator = context[self.id()].args[0]
        self.assertTrue(type(evaluator) is Evaluator)
        self.assertTrue(evaluator.factory is set)
        self.assertEqual([[]], evaluator.args)

    def test_process_attributes_unexpected_children(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<attributes>'
                        '<unexpected />'
                    '</attributes>'
                '</template>'
            '</context>'
        ) % self.id())
        e_expected = AglyphError("unexpected element: attributes/unexpected")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_process_attributes_attribute(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<attributes>'
                        '<attribute name="attr"><int>79</int></attribute>'
                    '</attributes>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        self.assertEqual({"attr": 79}, context[self.id()].attributes)

    def test_attribute_name_is_required(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<attributes>'
                        '<attribute><str>value</str></attribute>'
                    '</attributes>'
                '</template>'
            '</context>'
        ) % self.id())
        e_expected = AglyphError(
            "attribute/@name is required and cannot be empty")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_attribute_name_cannot_be_empty(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<attributes>'
                        '<attribute name=""><str>value</str></attribute>'
                    '</attributes>'
                '</template>'
            '</context>'
        ) % self.id())
        e_expected = AglyphError(
            "attribute/@name is required and cannot be empty")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_attribute_cannot_be_empty(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<attributes>'
                        '<attribute name="attr" />'
                    '</attributes>'
                '</template>'
            '</context>'
        ) % self.id())
        e_expected = AglyphError(
            "<attribute> must contain exactly one child element; "
            "found no children")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_attribute_rejects_multiple_children(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<attributes>'
                        '<attribute name="attr">'
                            '<str>string</str>'
                            '<int>79</int>'
                        '</attribute>'
                    '</attributes>'
                '</template>'
            '</context>'
        ) % self.id())
        e_expected = AglyphError(
            "<attribute> must contain exactly one child element; "
            "found attribute/str, attribute/int")
        assertRaisesWithMessage(self, e_expected, XMLContext, stream)

    def test_attribute_reference_attribute(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<template id="%s">'
                    '<attributes>'
                        '<attribute name="attr1" reference="ref1" />'
                        '<attribute name="attr2">'
                            '<reference id="ref2" />'
                        '</attribute>'
                    '</attributes>'
                '</template>'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        template = context[self.id()]
        self.assertTrue(type(template.attributes["attr1"]) is Reference)
        self.assertEqual("ref1", template.attributes["attr1"])
        self.assertTrue(type(template.attributes["attr2"]) is Reference)
        self.assertEqual("ref2", template.attributes["attr2"])

    def test_parse_component_implicit(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<component id="%s" />'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        component = context[self.id()]
        self.assertTrue(type(component) is Component)
        self.assertEqual(self.id(), component.dotted_name)

    def test_parse_component_explicit(self):
        stream = _context_as_stream((
            '<context id="test">'
                '<component '
                        'id="%s" '
                        'dotted-name="explicit.dotted.name" '
                        'factory-name="factory" '
                        'strategy="singleton" '
                        'parent-id="parent" '
                        'after-inject="after_inject" '
                        'before-clear="before_clear" />'
            '</context>'
        ) % self.id())
        context = XMLContext(stream)
        component = context[self.id()]
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

