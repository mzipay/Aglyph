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

"""Test cases and runner for the :mod:`aglyph.context` module."""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "2.1.0"

import functools
import logging
import struct
import sys
import unittest

from aglyph import AglyphError
from aglyph.compat import DataType, is_python_2
from aglyph.component import (
    Component,
    Evaluator,
    Reference,
    Strategy,
    Template,
)
from aglyph.context import Context, XMLContext

from test import (enable_debug_logging, find_basename, py_builtin_module,
                  skip_if)

try:
    float("NaN")
    float("Inf")
    float("-Inf")
except ValueError:
    missing_nan_inf = True
    isnan = lambda x: False
    isinf = lambda x: False
else:
    missing_nan_inf = False
    import math
    # PYVER: 'math.isnan()' and 'math.isinf()' are not available in
    # Python < 2.6
    isnan = getattr(math, "isnan", lambda x: isinstance(x, float))
    isinf = getattr(math, "isinf", lambda x: isinstance(x, float))

__all__ = [
    "ContextTest",
    "suite",
    "XMLContextTest"
]

# don't use __name__ here; can be run as "__main__"
_logger = logging.getLogger("test.test_context")

# PYVER: unittest.TestCase.assertIsNone is missing in Jython 2.5.3
if (not hasattr(unittest.TestCase, "assertIsNone")):
    def _assert_is_none(self, obj, msg=None):
        if (obj is not None):
            self.fail(msg if (msg is not None) else "%r is not None" % obj)
    unittest.TestCase.assertIsNone = _assert_is_none

# PYVER: unittest.TestCase.assertIsNotNone is missing in Jython 2.5.3
if (not hasattr(unittest.TestCase, "assertIsNotNone")):
    def _assert_is_not_none(self, obj, msg=None):
        if (obj is None):
            self.fail(msg if (msg is not None) else "%r is None" % obj)
    unittest.TestCase.assertIsNotNone = _assert_is_not_none

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
    # the buffer type for encoded byte data
    DataIO = __import__("StringIO").StringIO
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
    # the buffer type for encoded byte data
    DataIO = __import__("io").BytesIO


class ContextTest(unittest.TestCase):
    """Test the :class:`aglyph.context.Context` class."""

    def setUp(self):
        self.context = Context(str(self))

    def tearDown(self):
        self.context = None

    def test_init_with_id(self):
        context = Context("test_init_with_id")
        self.assertEqual("test_init_with_id", context.context_id)
        self.assertIsNone(context.after_inject)
        self.assertIsNone(context.before_clear)

    def test_init_with_lifecycle_methods(self):
        context = Context("test_init_with_lifecycle_methods",
                          after_inject="context_after_inject",
                          before_clear="context_before_clear")
        self.assertEqual("context_after_inject", context.after_inject)
        self.assertEqual("context_before_clear", context.before_clear)

    def test_get_component_doesnt_return_template(self):
        self.context["a-template"] = Template("a-template")
        self.assertTrue("a-template" in self.context)
        self.assertIsNone(self.context.get_component("a-template"))

    def test_get_component(self):
        self.context["a-component"] = Component("a-component")
        self.assertTrue("a-component" in self.context)
        self.assertIsNotNone(self.context.get_component("a-component"))

    def test_iter_components(self):
        self.context["template1"] = Template("template1")
        self.context["component1"] = Component("component1")
        self.context["template2"] = Template("template2")
        self.context["component2"] = Component("component2")
        expected = ["component1", "component2"]
        self.assertEqual(expected,
                         sorted([c.unique_id
                                 for c in self.context.iter_components()]))

    # Context.add will be removed in 3.0.0
    def test_add_duplicate_id(self):
        component = Component("alpha", "test.dummy.Alpha")
        duplicate = Component("alpha", "test.dummy.create_alpha")
        self.context.add(component)
        self.assertRaises(AglyphError, self.context.add, duplicate)

    # Context.add will be removed in 3.0.0
    def test_add(self):
        component1 = Component("test.dummy.Alpha")
        component2 = Component("alpha", "test.dummy.create_alpha")
        component3 = Component("alpha-alternate", "test.dummy.Alpha")
        self.context.add(component1)
        self.context.add(component2)
        self.context.add(component3)
        self.assertTrue("test.dummy.Alpha" in self.context)
        self.assertTrue("alpha" in self.context)
        self.assertTrue("alpha-alternate" in self.context)

    # Context.add_or_replace will be removed in 3.0.0
    def test_add_or_replace(self):
        component = Component("alpha", "test.dummy.Alpha")
        duplicate = Component("alpha", "test.dummy.create_alpha")
        self.context.add(component)
        self.assertEqual("test.dummy.Alpha", self.context["alpha"].dotted_name)
        replaced = self.context.add_or_replace(duplicate)
        self.assertEqual("test.dummy.create_alpha",
                         self.context["alpha"].dotted_name)
        self.assertTrue(replaced is component)

    # Context.remove will be removed in 3.0.0
    def test_remove_not_in_context(self):
        self.assertFalse("alpha" in self.context)
        self.assertTrue(self.context.remove("alpha") is None)

    # Context.remove will be removed in 3.0.0
    def test_remove(self):
        self.context.add(Component("beta", "test.dummy.Beta"))
        self.assertTrue("beta" in self.context)
        self.assertEqual("beta", self.context.remove("beta").unique_id)
        self.assertFalse("beta" in self.context)


class XMLContextTest(unittest.TestCase):
    """Test the :class:`aglyph.context.XMLContext` class."""

    _CONTEXT_TEMPLATE = as_text("""\
<?xml version="1.0" encoding="%s"?>
<!DOCTYPE context SYSTEM "../resources/aglyph-context.dtd">
<context id="%s">
    %%s
</context>""")

    def setUp(self):
        self.context_template = self._get_context_template()

    def _get_context_template(self, encoding="utf-8"):
        return self._CONTEXT_TEMPLATE % (encoding, str(self).split()[0])

    def tearDown(self):
        self.context_template = None

    def _init_context(self, xml_string, encoding="utf-8"):
        source = DataIO(xml_string.encode(encoding))
        return XMLContext(source)

    def test_init_root_is_not_context(self):
        self.assertRaises(AglyphError, self._init_context, as_text(
                          '<?xml version="1.0"?>\n<not-context/>'))

    def test_init_missing_context_id(self):
        self.assertRaises(KeyError, self._init_context, as_text(
                          '<?xml version="1.0"?>\n<context/>'))

    def test_init_filename(self):
        context = XMLContext(find_basename("empty-context.xml"))
        self.assertEqual("empty-context", context.context_id)

    def test_init_stream(self):
        context = self._init_context(self.context_template % as_text(""))
        self.assertEqual("test_init_stream", context.context_id)

    def test_default_default_encoding(self):
        context = XMLContext(DataIO(as_text("""\
<?xml version="1.0"?>
<context id="test_default_default_encoding"/>""".encode("utf-8"))))
        self.assertEqual(sys.getdefaultencoding(), context.default_encoding)

    def test_explicit_default_encoding(self):
        context = XMLContext(DataIO(as_text("""\
<?xml version="1.0"?>
<context id="test_explicit_default_encoding"/>""".encode("utf-8"))),
                             default_encoding="iso-8859-1")
        self.assertEqual("iso-8859-1", context.default_encoding)

    def test_readonly_properties(self):
        context = self._init_context(self.context_template % as_text(""))
        self.assertRaises(AttributeError, setattr, context, "default_encoding",
                          "is0-8859-1")

    def test_parse_unexpected_element(self):
        self.assertRaises(AttributeError, self._init_context,
                          self.context_template % as_text("""\
<component id="test.dummy.create_alpha">
    <init><arg><unexpected/></arg></init>
</component>"""))

    def test_parse_component_missing_id(self):
        self.assertRaises(KeyError, self._init_context,
                          self.context_template %
                          as_text('<component/>'))

    def test_parse_component_defaults(self):
        context = self._init_context(self.context_template % as_text(
                                     '<component id="test.dummy.Beta"/>'))
        component = context["test.dummy.Beta"]
        self.assertTrue(component.__class__ is Component)
        self.assertEqual("test.dummy.Beta", component.unique_id)
        self.assertEqual("test.dummy.Beta", component.dotted_name)
        self.assertIsNone(component.factory_name)
        self.assertIsNone(component.member_name)
        self.assertEqual("prototype", component.strategy)
        self.assertIsNone(component.parent_id)
        self.assertIsNone(component.after_inject)
        self.assertIsNone(component.before_clear)
        self.assertEqual([], component.args)
        self.assertEqual({}, component.keywords)
        self.assertEqual({}, component.attributes)

    def test_parse_component_unique_id(self):
        context = self._init_context(self.context_template % as_text(
                    '<component id="beta" dotted-name="test.dummy.Beta"/>'))
        component = context["beta"]
        self.assertEqual("beta", component.unique_id)
        self.assertEqual("test.dummy.Beta", component.dotted_name)

    def test_parse_component_prototype_explicit(self):
        context = self._init_context(
            self.context_template % as_text(
                '<component id="test.dummy.Beta" strategy="prototype"/>'))
        self.assertEqual(Strategy.PROTOTYPE,
                         context["test.dummy.Beta"].strategy)

    def test_parse_component_singleton(self):
        context = self._init_context(
            self.context_template % as_text(
                '<component id="test.dummy.Beta" strategy="singleton"/>'))
        self.assertEqual(Strategy.SINGLETON,
                         context["test.dummy.Beta"].strategy)

    def test_parse_component_borg(self):
        context = self._init_context(
            self.context_template % as_text(
                '<component id="test.dummy.Beta" strategy="borg"/>'))
        self.assertEqual(Strategy.BORG, context["test.dummy.Beta"].strategy)

    def test_parse_component_weakref(self):
        context = self._init_context(
            self.context_template % as_text(
                '<component id="test.dummy.Beta" strategy="weakref"/>'))
        self.assertEqual(Strategy.WEAKREF, context["test.dummy.Beta"].strategy)

    def test_parse_component_factory_name(self):
        context = self._init_context(
            self.context_template % as_text(
                '<component id="epsilon" dotted-name="test.dummy.Epsilon" '
                    'factory-name="class_factory" />'))
        self.assertEqual("class_factory", context["epsilon"].factory_name)

    def test_parse_component_member_name(self):
        context = self._init_context(
            self.context_template % as_text(
                '<component id="epsilon-member" '
                    'dotted-name="test.dummy.Epsilon" '
                    'member-name="ATTRIBUTE" />'))
        self.assertEqual("ATTRIBUTE", context["epsilon-member"].member_name)

    def test_parse_component_with_parent(self):
        context = self._init_context(
            self.context_template % as_text(
                '<component id="test.dummy.Alpha" '
                    'parent-id="the-parent-id" />'))
        self.assertEqual("the-parent-id",
                         context["test.dummy.Alpha"].parent_id)

    def test_parse_component_with_after_inject(self):
        context = self._init_context(
            self.context_template % as_text(
                '<component id="test.dummy.Alpha" '
                    'after-inject="component_after_inject" />'))
        self.assertEqual("component_after_inject",
                         context["test.dummy.Alpha"].after_inject)

    def test_parse_component_prototype_ignores_before_clear(self):
        context = self._init_context(
            self.context_template % as_text(
                '<component id="test.dummy.Alpha" '
                    'before-clear="component_before_clear" />'))
        self.assertIsNone(context["test.dummy.Alpha"].before_clear)

    def test_parse_component_singleton_with_before_clear(self):
        context = self._init_context(
            self.context_template % as_text(
                '<component id="test.dummy.Alpha" strategy="singleton" '
                    'before-clear="component_before_clear" />'))
        self.assertEqual("component_before_clear",
                         context["test.dummy.Alpha"].before_clear)

    def test_parse_component_borg_with_before_clear(self):
        context = self._init_context(
            self.context_template % as_text(
                '<component id="test.dummy.Alpha" strategy="borg" '
                    'before-clear="component_before_clear" />'))
        self.assertEqual("component_before_clear",
                         context["test.dummy.Alpha"].before_clear)

    def test_parse_component_weakref_with_before_clear(self):
        context = self._init_context(
            self.context_template % as_text(
                '<component id="test.dummy.Alpha" strategy="weakref" '
                    'before-clear="component_before_clear" />'))
        self.assertEqual("component_before_clear",
                         context["test.dummy.Alpha"].before_clear)

    def test_parse_template_missing_id(self):
        self.assertRaises(KeyError, self._init_context,
                          self.context_template %
                          as_text('<template/>'))

    def test_parse_template_defaults(self):
        context = self._init_context(self.context_template % as_text(
                                     '<template id="test.dummy.Alpha" />'))
        template = context["test.dummy.Alpha"]
        self.assertTrue(template.__class__ is Template)
        self.assertEqual("test.dummy.Alpha", template.unique_id)
        self.assertIsNone(template.parent_id)
        self.assertIsNone(template.after_inject)
        self.assertIsNone(template.before_clear)
        self.assertEqual([], template.args)
        self.assertEqual({}, template.keywords)
        self.assertEqual({}, template.attributes)

    def test_parse_template_with_parent(self):
        context = self._init_context(
            self.context_template % as_text(
                '<template id="a-template" parent-id="the-parent-id" />'))
        self.assertEqual("the-parent-id",
                         context["a-template"].parent_id)

    def test_parse_template_with_after_inject(self):
        context = self._init_context(
            self.context_template % as_text(
                '<template id="a-template" '
                    'after-inject="template_after_inject" />'))
        self.assertEqual("template_after_inject",
                         context["a-template"].after_inject)

    def test_parse_template_with_before_clear(self):
        context = self._init_context(
            self.context_template % as_text(
                '<template id="a-template" '
                    'before-clear="template_before_clear" />'))
        self.assertEqual("template_before_clear",
                         context["a-template"].before_clear)

    def test_parse_init_empty(self):
        context = self._init_context(
            self.context_template % as_text(
                '<component id="test.dummy.Beta"><init/></component>'))
        component = context["test.dummy.Beta"]
        self.assertEqual([], component.init_args)
        self.assertEqual({}, component.init_keywords)

    def test_parse_arg_empty(self):
        # empty element
        self.assertRaises(AglyphError, self._init_context,
                          self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg/></init>
</component>"""))
        # empty text
        self.assertRaises(AglyphError, self._init_context,
                          self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg></arg></init>
</component>"""))

    def test_parse_arg_positional(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><none/></arg></init>
</component>"""))
        component = context["test.dummy.Alpha"]
        self.assertTrue(component.init_args[0] is None)
        self.assertEqual({}, component.init_keywords)

    def test_parse_arg_keyword(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg keyword="keyword"><none/></arg></init>'
</component>"""))
        component = context["test.dummy.Alpha"]
        self.assertEqual([], component.init_args)
        self.assertTrue(component.init_keywords["keyword"] is None)

    def test_parse_arg_positional_and_keyword(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init>
        <arg><none/></arg>
        <arg keyword="keyword"><none/></arg>
    </init>
</component>"""))
        component = context["test.dummy.Alpha"]
        self.assertTrue(component.init_args[0] is None)
        self.assertTrue(component.init_keywords["keyword"] is None)

    def test_parse_attributes_empty(self):
        context = self._init_context(
            self.context_template % as_text(
                '<component id="test.dummy.Beta"><attributes/></component>'))
        self.assertEqual({}, context["test.dummy.Beta"].attributes)

    def test_parse_attribute_empty(self):
        # empty element
        self.assertRaises(AglyphError, self._init_context,
                          self.context_template % as_text("""\
<component id="test.dummy.Beta">
    <attributes>
        <attribute name="field"/>
    </attributes>
</component>"""))
        # empty text
        self.assertRaises(AglyphError, self._init_context,
                          self.context_template % as_text("""\
<component id="test.dummy.Beta">
    <attributes>
        <attribute name="field"></attribute>
    </attributes>
</component>"""))

    def test_parse_attribute(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Beta">
    <attributes>
        <attribute name="field"><none/></attribute>
    </attributes>
</component>"""))
        self.assertTrue(context["test.dummy.Beta"].attributes["field"] is None)

    def test_parse_init_and_attributes_empty(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Beta">
    <init/>
    <attributes/>
</component>"""))
        component = context["test.dummy.Beta"]
        self.assertEqual([], component.init_args)
        self.assertEqual({}, component.init_keywords)
        self.assertEqual({}, component.attributes)

    def test_parse_init_and_attributes_single(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><none/></arg></init>
    <attributes>
        <attribute name="field"><none/></attribute>
    </attributes>
</component>"""))
        component = context["test.dummy.Alpha"]
        self.assertTrue(component.init_args[0] is None)
        self.assertEqual({}, component.init_keywords)
        self.assertTrue(component.attributes["field"] is None)

    def test_parse_init_and_attributes_multi(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init>
        <arg><none/></arg>
        <arg keyword="keyword"><none/></arg>
    </init>
    <attributes>
        <attribute name="field"><none/></attribute>
        <attribute name="set_value"><none/></attribute>
        <attribute name="prop"><none/></attribute>
    </attributes>
</component>"""))
        component = context["test.dummy.Alpha"]
        self.assertTrue(component.init_args[0] is None)
        self.assertTrue(component.init_keywords["keyword"] is None)
        self.assertTrue(component.attributes["field"] is None)
        self.assertTrue(component.attributes["set_value"] is None)
        self.assertTrue(component.attributes["prop"] is None)

    def test_parse_bytes_empty(self):
        # empty element & empty text
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init>
        <arg><bytes/></arg>
        <arg keyword="keyword"><bytes></bytes></arg>
    </init>
</component>"""))
        component = context["test.dummy.Alpha"]
        self.assertEqual(as_data(""), component.init_args[0])
        self.assertEqual(as_data(""), component.init_keywords["keyword"])

    def test_parse_bytes_text_node_default_encoding(self):
        # document encoding is UTF-8 (see _get_context_template())
        # default encoding is 'ascii' on Python 2, 'utf-8' on Python 3
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><bytes>test</bytes></arg></init>
</component>"""))
        component = context["test.dummy.Alpha"]
        self.assertEqual(as_data("test"), component.init_args[0])

    def test_parse_bytes_text_node_latin1_encoding(self):
        # document encoding is UTF-8 (see _get_context_template())
        # default encoding is 'ascii' on Python 2, 'utf-8' on Python 3
        # uses copyright symbol U+00A9 (169)
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><bytes encoding="iso-8859-1">\u00a9</bytes></arg></init>
</component>"""))
        component = context["test.dummy.Alpha"]
        self.assertEqual(as_data("\xa9"), component.init_args[0])

    def test_parse_str_empty(self):
        # empty element & text
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init>
        <arg><str/></arg>
        <arg keyword="keyword"><str></str></arg>
    </init>
</component>"""))
        component = context["test.dummy.Alpha"]
        self.assertEqual("", component.init_args[0])
        self.assertEqual("", component.init_keywords["keyword"])

    def test_parse_str_text_node_default_encoding(self):
        # document encoding is UTF-8 (see _get_context_template())
        # default encoding is 'ascii' on Python 2, 'utf-8' on Python 3
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><str>test</str></arg></init>
</component>"""))
        component = context["test.dummy.Alpha"]
        # str is encoded bytes in Python < 3.0, Unicode text in >= 3.0
        if (is_python_2):
            self.assertTrue(isinstance(component.init_args[0], DataType))
            self.assertEqual(as_data("test"), component.init_args[0])
        else:
            # b"" != ""
            self.assertEqual(as_text("test"), component.init_args[0])

    def test_parse_str_text_node_latin1_encoding(self):
        # document encoding is UTF-8 (see _get_context_template())
        # default encoding is 'ascii' on Python 2, 'utf-8' on Python 3
        # uses copyright symbol U+00A9 (169)
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><str encoding="iso-8859-1">\u00a9</str></arg></init>
</component>"""))
        component = context["test.dummy.Alpha"]
        # str is encoded bytes in Python < 3.0, Unicode text in >= 3.0
        if (sys.version_info[0] == 2):
            self.assertTrue(isinstance(component.init_args[0], DataType))
            self.assertEqual(as_data("\xa9"), component.init_args[0])
        else:
            self.assertEqual(as_text("\u00a9"), component.init_args[0])

    def test_parse_int_empty(self):
        # empty element & empty text
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init>
        <arg><int/></arg>
        <arg keyword="keyword"><int></int></arg>
    </init>
</component>"""))
        component = context["test.dummy.Alpha"]
        self.assertTrue(isinstance(component.init_args[0], int))
        self.assertEqual(0, component.init_args[0])
        self.assertTrue(isinstance(component.init_keywords["keyword"], int))
        self.assertEqual(0, component.init_keywords["keyword"])

    def test_parse_int_bad_text_node(self):
        xml_string = self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><int>4f</int></arg></init>
</component>""")
        self.assertRaises(ValueError, self._init_context, xml_string)

    def test_parse_int_text_node(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><int>79</int></arg></init>
</component>"""))
        component = context["test.dummy.Alpha"]
        self.assertTrue(isinstance(component.init_args[0], int))
        self.assertEqual(79, component.init_args[0])

    def test_parse_int_long(self):
        if (is_python_2):
            long_int = eval("sys.maxint + 1")
            long_int_type = eval("long")
        else:  # assume 3
            long_int = eval("sys.maxsize + 1")
            long_int_type = int
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><int>%d</int></arg></init>
</component>""" % long_int))
        component = context["test.dummy.Alpha"]
        self.assertTrue(isinstance(component.init_args[0], long_int_type))
        self.assertEqual(long_int, component.init_args[0])

    def test_parse_int_float(self):
        xml_string = self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><int>7.9</int></arg></init>
</component>""")
        self.assertRaises(ValueError, self._init_context, xml_string)

    def test_parse_int_base(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><int base="16">4f</int></arg></init>
</component>"""))
        component = context["test.dummy.Alpha"]
        self.assertTrue(isinstance(component.init_args[0], int))
        self.assertEqual(79, component.init_args[0])

    def test_parse_float_empty(self):
        # empty element & empty text
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init>
        <arg><float/></arg>
        <arg keyword="keyword"><float></float></arg>
    </init>
</component>"""))
        component = context["test.dummy.Alpha"]
        self.assertTrue(isinstance(component.init_args[0], float))
        self.assertEqual(0.0, component.init_args[0])
        self.assertTrue(isinstance(component.init_keywords["keyword"], float))
        self.assertEqual(0.0, component.init_keywords["keyword"])

    def test_parse_float_bad_text_node(self):
        xml_string = self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><float>4f</float></arg></init>
</component>""")
        self.assertRaises(ValueError, self._init_context, xml_string)

    def test_parse_float_text_node(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><float>7.9</float></arg></init>
</component>"""))
        component = context["test.dummy.Alpha"]
        self.assertTrue(isinstance(component.init_args[0], float))
        self.assertAlmostEqual(7.9, component.init_args[0])

    def test_parse_float_int(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><float>79</float></arg></init>
</component>"""))
        component = context["test.dummy.Alpha"]
        self.assertTrue(isinstance(component.init_args[0], float))
        self.assertAlmostEqual(79.0, component.init_args[0])

    @skip_if(missing_nan_inf, "missing NaN, Inf, -Inf")
    def test_parse_float_special_text_node(self):
        # this test cannot be written reliably, as what is accepted/returned
        # is dependent entirely on the underlying system libraries
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Beta">
    <attributes>
        <attribute name="field"><float>NaN</float></attribute>
        <attribute name="set_value"><float>Inf</float></attribute>
        <attribute name="prop"><float>-Inf</float></attribute>
    </attributes>
</component>"""))
        component = context["test.dummy.Beta"]
        self.assertTrue(isnan(component.attributes["field"]))
        self.assertTrue(isinf(component.attributes["set_value"]))
        self.assertTrue(isinf(component.attributes["prop"]))

    def test_parse_tuple_empty(self):
        # empty element & empty text
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init>
        <arg><tuple/></arg>
        <arg keyword="keyword"><tuple></tuple></arg>
    </init>
</component>"""))
        component = context["test.dummy.Alpha"]
        # empty tuple is never an Evaluator
        self.assertEqual(tuple(), component.init_args[0])
        self.assertEqual(tuple(), component.init_keywords["keyword"])

    def test_parse_tuple_single_item(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><tuple><none/></tuple></arg></init>
</component>"""))
        component = context["test.dummy.Alpha"]
        # tuple with item(s) is always an Evaluator
        self.assertTrue(isinstance(component.init_args[0], Evaluator))
        obj = component.init_args[0](None)
        self.assertTrue(isinstance(obj, tuple))
        self.assertEqual((None,), obj)

    def test_parse_tuple_multi_item(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">'
    <init><arg><tuple><false/><true/></tuple></arg></init>
</component>"""))
        component = context["test.dummy.Alpha"]
        # tuple with item(s) is always an Evaluator
        self.assertTrue(isinstance(component.init_args[0], Evaluator))
        obj = component.init_args[0](None)
        self.assertTrue(isinstance(obj, tuple))
        self.assertEqual((False, True), obj)

    def test_parse_list_empty(self):
        # empty element & empty text
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init>
        <arg><list/></arg>
        <arg keyword="keyword"><list></list></arg>
    </init>
</component>"""))
        component = context["test.dummy.Alpha"]
        # lists are ALWAYS Evaluators, even when empty
        self.assertTrue(isinstance(component.init_args[0], Evaluator))
        obj = component.init_args[0](None)
        self.assertTrue(isinstance(obj, list))
        self.assertEqual([], obj)
        self.assertTrue(isinstance(component.init_keywords["keyword"],
                                   Evaluator))
        obj = component.init_keywords["keyword"](None)
        self.assertTrue(isinstance(obj, list))
        self.assertEqual([], obj)

    def test_parse_list_single_item(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><list><none/></list></arg></init>
</component>"""))
        component = context["test.dummy.Alpha"]
        self.assertTrue(isinstance(component.init_args[0], Evaluator))
        obj = component.init_args[0](None)
        self.assertTrue(isinstance(obj, list))
        self.assertEqual([None], obj)

    def test_parse_list_multi_item(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><list><false/><true/></list></arg></init>
</component>"""))
        component = context["test.dummy.Alpha"]
        self.assertTrue(isinstance(component.init_args[0], Evaluator))
        obj = component.init_args[0](None)
        self.assertTrue(isinstance(obj, list))
        self.assertEqual([False, True], obj)

    def test_parse_dict_empty(self):
        # empty element & empty text
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init>
        <arg><dict/></arg>
        <arg keyword="keyword"><dict></dict></arg>
    </init>
</component>"""))
        component = context["test.dummy.Alpha"]
        # dicts are ALWAYS Evaluators, even when empty
        self.assertTrue(isinstance(component.init_args[0], Evaluator))
        obj = component.init_args[0](None)
        self.assertTrue(isinstance(obj, dict))
        self.assertEqual({}, obj)

    def test_parse_dict_single_item(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init>
        <arg>
            <dict><item><key><none/></key><value><none/></value></item></dict>
        </arg>
    </init>
</component>"""))
        component = context["test.dummy.Alpha"]
        self.assertTrue(isinstance(component.init_args[0], Evaluator))
        obj = component.init_args[0](None)
        self.assertTrue(isinstance(obj, dict))
        self.assertEqual({None: None}, obj)

    def test_parse_dict_multi_item(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init>
        <arg>
            <dict>
                <item><key><true/></key><value><none/></value></item>
                <item><key><false/></key><value><none/></value></item>
            </dict>
        </arg>
    </init>
</component>"""))
        component = context["test.dummy.Alpha"]
        self.assertTrue(isinstance(component.init_args[0], Evaluator))
        obj = component.init_args[0](None)
        self.assertTrue(isinstance(obj, dict))
        self.assertEqual({True: None, False: None}, obj)

    def test_parse_dict_item_missing_key(self):
        self.assertRaises(AglyphError, self._init_context,
                          self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><dict><item><value><none/></value></item></dict></arg></init>
</component>"""))

    def test_parse_dict_item_missing_value(self):
        self.assertRaises(AglyphError, self._init_context,
                          self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><dict><item><key><none/></key></item></dict></arg></init>
</component>"""))

    def test_parse_dict_item_key_empty(self):
        # empty element
        self.assertRaises(AglyphError, self._init_context,
                         self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init>
        <arg><dict><item><key/><value><none/></value></item></dict></arg>
    </init>
</component>"""))
        # empty text
        self.assertRaises(AglyphError, self._init_context,
                          self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init>
        <arg><dict><item><key></key><value><none/></value></item></dict></arg>
    </init>
</component>"""))

    def test_parse_dict_item_value_empty(self):
        # empty element
        self.assertRaises(AglyphError, self._init_context,
                          self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init>
        <arg><dict><item><key><none/></key><value/></item></dict></arg>
    </init>
</component>"""))
        # empty text
        self.assertRaises(AglyphError, self._init_context,
                          self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init>
        <arg><dict><item><key><none/></key><value></value></item></dict></arg>
    </init>
</component>"""))

    def test_parse_reference_arg(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="obj" dotted-name="%s.object"/>
<component id="test.dummy.Alpha">
    <init>
        <arg><reference id="obj"/></arg>
        <arg keyword="keyword" reference="test.dummy.Beta"/>
    </init>
</component>
<component id="test.dummy.Beta"/>""" % py_builtin_module.__name__))
        component = context["test.dummy.Alpha"]
        self.assertTrue(isinstance(component.init_args[0], Reference))
        self.assertEqual("obj", component.init_args[0])
        self.assertTrue(
            isinstance(component.init_keywords["keyword"], Reference))
        self.assertEqual("test.dummy.Beta", component.init_keywords["keyword"])

    def test_parse_reference_attribute(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="obj" dotted-name="%s.object"/>
<component id="test.dummy.Beta">
    <attributes>
        <attribute name="field"><reference id="obj"/></attribute>
        <attribute name="set_value" reference="test.dummy.Alpha"/>
    </attributes>
</component>
<component id="test.dummy.Alpha">
    <init><arg><none/></arg></init>
</component>""" % py_builtin_module.__name__))
        component = context["test.dummy.Beta"]
        self.assertTrue(isinstance(component.attributes["field"], Reference))
        self.assertEqual("obj", component.attributes["field"])
        self.assertTrue(isinstance(component.attributes["set_value"],
                                   Reference))
        self.assertEqual("test.dummy.Alpha", component.attributes["set_value"])

    def test_parse_reference_list(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="obj" dotted-name="%s.object"/>
<component id="test.dummy.Alpha">
    <init><arg><list><reference id="obj"/></list></arg></init>
</component>""" % py_builtin_module.__name__))
        evaluator = context["test.dummy.Alpha"].init_args[0]
        self.assertTrue(isinstance(evaluator, Evaluator))
        self.assertTrue(evaluator.func is list)
        self.assertTrue(isinstance(evaluator.args[0][0], Reference))
        self.assertEqual("obj", evaluator.args[0][0])

    def test_parse_reference_tuple(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="obj" dotted-name="%s.object"/>
<component id="test.dummy.Alpha">
    <init><arg><tuple><reference id="obj"/></tuple></arg></init>
</component>""" % py_builtin_module.__name__))
        evaluator = context["test.dummy.Alpha"].init_args[0]
        self.assertTrue(isinstance(evaluator, Evaluator))
        self.assertTrue(evaluator.func is tuple)
        self.assertTrue(isinstance(evaluator.args[0][0], Reference))
        self.assertEqual("obj", evaluator.args[0][0])

    def test_parse_reference_key(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="obj1" dotted-name="%(py_builtin_module_name)s.object"/>
<component id="%(py_builtin_module_name)s.frozenset" strategy="singleton"/>
<component id="test.dummy.Alpha">
    <init>
        <arg>
            <dict>
                <item>
                    <key><reference id="obj"/></key>
                    <value><none/></value>
                </item>
                <item>
                    <key reference="%(py_builtin_module_name)s.frozenset"/>
                    <value><none/></value>
                </item>
            </dict>
        </arg>
    </init>
</component>""" % {"py_builtin_module_name": py_builtin_module.__name__}))
        evaluator = context["test.dummy.Alpha"].init_args[0]
        self.assertTrue(isinstance(evaluator, Evaluator))
        self.assertTrue(evaluator.func is dict)
        self.assertTrue(isinstance(evaluator.args[0][0][0], Reference))
        self.assertEqual("obj", evaluator.args[0][0][0])
        self.assertTrue(isinstance(evaluator.args[0][1][0], Reference))
        self.assertEqual("%s.frozenset" % py_builtin_module.__name__,
                         evaluator.args[0][1][0])

    def test_parse_reference_value(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="obj1" dotted-name="%(py_builtin_module_name)s.object"/>
<component id="%(py_builtin_module_name)s.frozenset" strategy="singleton"/>
<component id="test.dummy.Alpha">
    <init>
        <arg>
            <dict>
                <item>
                    <key><false/></key>
                    <value><reference id="obj"/></value>
                </item>
                <item>
                    <key><true/></key>
                    <value reference="%(py_builtin_module_name)s.frozenset"/>
                </item>
            </dict>
        </arg>
    </init>
</component>""" % {"py_builtin_module_name": py_builtin_module.__name__}))
        evaluator = context["test.dummy.Alpha"].init_args[0]
        self.assertTrue(isinstance(evaluator, Evaluator))
        self.assertTrue(evaluator.func is dict)
        self.assertTrue(isinstance(evaluator.args[0][0][1], Reference))
        self.assertEqual("obj", evaluator.args[0][0][1])
        self.assertTrue(isinstance(evaluator.args[0][1][1], Reference))
        self.assertEqual("%s.frozenset" % py_builtin_module.__name__,
                         evaluator.args[0][1][1])

    def test_parse_eval_empty(self):
        # empty element
        self.assertRaises(AglyphError, self._init_context,
                          self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><eval/></arg></init>
</component>"""))
        # empty text
        self.assertRaises(AglyphError, self._init_context,
                          self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><eval></eval></arg></init>
</component>"""))

    def test_parse_eval_arg(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init>
        <arg><eval>complex(7, 9)</eval></arg>
        <arg keyword="keyword"><eval>set([2, 3, 5, 7])</eval></arg>
    </init>
</component>"""))
        partial_arg = context["test.dummy.Alpha"].init_args[0]
        self.assertTrue(isinstance(partial_arg, functools.partial))
        self.assertTrue(partial_arg.func is eval)
        self.assertEqual("complex(7, 9)", partial_arg.args[0])
        self.assertEqual(complex(7, 9), partial_arg())
        partial_kw = context["test.dummy.Alpha"].init_keywords["keyword"]
        self.assertTrue(isinstance(partial_kw, functools.partial))
        self.assertTrue(partial_kw.func is eval)
        self.assertEqual("set([2, 3, 5, 7])", partial_kw.args[0])
        self.assertEqual(set([2, 3, 5, 7]), partial_kw())

    def test_parse_eval_attribute(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Beta">'
    <attributes>
        <attribute name="field"><eval>complex(7, 9)</eval></attribute>
    </attributes>
</component>"""))
        partial_attr = context["test.dummy.Beta"].attributes["field"]
        self.assertTrue(isinstance(partial_attr, functools.partial))
        self.assertTrue(partial_attr.func is eval)
        self.assertEqual("complex(7, 9)", partial_attr.args[0])
        self.assertEqual(complex(7, 9), partial_attr())

    def test_parse_eval_list(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><list><eval>complex(7, 9)</eval></list></arg></init>
</component>"""))
        evaluator = context["test.dummy.Alpha"].init_args[0]
        partial_item = evaluator.args[0][0]
        self.assertTrue(isinstance(partial_item, functools.partial))
        self.assertTrue(partial_item.func is eval)
        self.assertEqual("complex(7, 9)", partial_item.args[0])
        self.assertEqual(complex(7, 9), partial_item())

    def test_parse_eval_tuple(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init><arg><tuple><eval>complex(7, 9)</eval></tuple></arg></init>
</component>"""))
        evaluator = context["test.dummy.Alpha"].init_args[0]
        partial_item = evaluator.args[0][0]
        self.assertTrue(isinstance(partial_item, functools.partial))
        self.assertTrue(partial_item.func is eval)
        self.assertEqual("complex(7, 9)", partial_item.args[0])
        self.assertEqual(complex(7, 9), partial_item())

    def test_parse_eval_key(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init>
        <arg>
            <dict>
                <item>
                    <key><eval>complex(7, 9)</eval></key>
                    <value><none/></value>
                </item>
            </dict>
        </arg>
    </init>
</component>"""))
        evaluator = context["test.dummy.Alpha"].init_args[0]
        partial_key = evaluator.args[0][0][0]
        self.assertTrue(isinstance(partial_key, functools.partial))
        self.assertTrue(partial_key.func is eval)
        self.assertEqual("complex(7, 9)", partial_key.args[0])
        self.assertEqual(complex(7, 9), partial_key())

    def test_parse_eval_value(self):
        context = self._init_context(self.context_template % as_text("""\
<component id="test.dummy.Alpha">
    <init>
        <arg>
            <dict>
                <item>
                    <key><none/></key>
                    <value><eval>complex(7, 9)</eval></value>
                </item>
            </dict>
        </arg>
    </init>
</component>"""))
        evaluator = context["test.dummy.Alpha"].init_args[0]
        partial_value = evaluator.args[0][0][1]
        self.assertTrue(isinstance(partial_value, functools.partial))
        self.assertTrue(partial_value.func is eval)
        self.assertEqual("complex(7, 9)", partial_value.args[0])
        self.assertEqual(complex(7, 9), partial_value())

    def test_parse_template_init(self):
        context = self._init_context(self.context_template % as_text("""\
<template id="a-template">
    <init>
        <arg><none /></arg>
        <arg keyword="keyword"><str /></arg>
    </init>
</template>"""))
        self.assertEqual([None], context["a-template"].args)
        self.assertEqual({"keyword": ""}, context["a-template"].keywords)
        self.assertEqual({}, context["a-template"].attributes)

    def test_parse_template_attributes(self):
        context = self._init_context(self.context_template % as_text("""\
<template id="a-template">
    <attributes>
        <attribute name="field"><none /></attribute>
    </attributes>
</template>"""))
        self.assertEqual([], context["a-template"].args)
        self.assertEqual({}, context["a-template"].keywords)
        self.assertEqual({"field": None}, context["a-template"].attributes)


def suite():
    """Build the test suite for the :mod:`aglyph.context` module."""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ContextTest))
    suite.addTest(unittest.makeSuite(XMLContextTest))
    _logger.debug("RETURN %r", suite)
    return suite


if (__name__ == "__main__"):
    enable_debug_logging(suite)
    unittest.TextTestRunner().run(suite())

