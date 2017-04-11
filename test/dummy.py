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

"""This module defines "dummy" classes and functions for Aglyph unit and
functional tests.

All keywords and class members use the module constant ``DEFAULT`` as a
default value in order to differentiate them from ``None`` (for easier
testing).

"""

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

from aglyph import __version__

__all__ = [
    "DEFAULT",
    "factory_function",
    "MODULE_MEMBER",
    "ModuleClass",
    "outer_function",
]

#: used as a default value (instead of ``None``; makes tests more explicit)
DEFAULT = object()

#: A sentinel value to force exceptions to be raised.
RAISE = object()


#PYVER: extending object is implicit in Python >= 3.0
class _LifecycleMethodsMixin(object):

    def reset_lifecycle_counts(self):
        self.called_context_after_inject = 0
        self.called_template_after_inject = 0
        self.called_component_after_inject = 0
        self.called_component_before_clear = 0
        self.called_template_before_clear = 0
        self.called_context_before_clear = 0

    def context_after_inject(self):
        self.called_context_after_inject += 1

    def template_after_inject(self):
        self.called_template_after_inject += 1

    def component_after_inject(self):
        self.called_component_after_inject += 1

    def component_before_clear(self):
        self.called_component_before_clear += 1

    def template_before_clear(self):
        self.called_template_before_clear += 1

    def context_before_clear(self):
        self.called_context_before_clear += 1


class ModuleClass(_LifecycleMethodsMixin):

    class NestedClass(_LifecycleMethodsMixin):

        @staticmethod
        def staticmethod_factory():
            return ModuleClass.NestedClass(DEFAULT, keyword=DEFAULT)

        @classmethod
        def classmethod_factory(cls, keyword=DEFAULT):
            return cls(DEFAULT, keyword=keyword)

        def __init__(self, arg, keyword=DEFAULT):
            self.arg = arg
            self.keyword = keyword
            self.attr = DEFAULT
            self._prop = DEFAULT
            self.__value = DEFAULT
            self.reset_lifecycle_counts()

        @property
        def prop(self):
            return self._prop

        @prop.setter
        def prop(self, value):
            self._prop = value

        def get_value(self):
            return self.__value

        def set_value(self, value):
            self.__value = value

    CLASS_MEMBER = NestedClass("module-level class member")

    @staticmethod
    def staticmethod_factory(arg):
        return ModuleClass(arg, keyword=DEFAULT)

    @classmethod
    def classmethod_factory(cls, arg, keyword=DEFAULT):
        return cls(arg, keyword=keyword)

    def __init__(self, arg, keyword=DEFAULT):
        if arg is RAISE:
            raise RuntimeError("__init__ RAISE")
        self.arg = arg
        self.keyword = keyword
        self.attr = DEFAULT
        self._prop = DEFAULT
        self.__value = DEFAULT
        self.reset_lifecycle_counts()

    @property
    def prop(self):
        return self._prop

    @prop.setter
    def prop(self, value):
        if value is RAISE:
            raise RuntimeError("@prop.setter RAISE")
        self._prop = value

    def get_value(self):
        return self.__value

    def set_value(self, value):
        if value is RAISE:
            raise RuntimeError("set_value RAISE")
        self.__value = value

    def method(self):
        pass


MODULE_MEMBER = ModuleClass("dummy module member")


def factory_function(arg, keyword=DEFAULT):
    if arg is RAISE:
        raise RuntimeError("factory_function RAISE")
    return ModuleClass(arg, keyword=keyword)


def outer_function():
    def nested_function():
        return DEFAULT
    return nested_function

