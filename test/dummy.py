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

"""This module defines "dummy" classes and functions for Aglyph unit and
functional tests.

All keywords and class members use the module constant ``DEFAULT`` as a
default value in order to differentiate them from ``None`` (for easier
testing).

"""

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "2.1.0"

__all__ = [
    "Alpha",
    "Beta",
    "create_alpha",
    "create_beta",
    "create_delta",
    "DEFAULT",
    "Delta",
    "Eta",
    "Gamma",
    "Epsilon",
    "EPSILON",
    "LIFECYCLE_EXCEPTION",
    "ZETA",
]

#: used as a default instead of ``None`` (easier testing)
DEFAULT = object()

#: used to signal that a lifecycle method should raise an exception
LIFECYCLE_EXCEPTION = object()


# PYVER: extending object is implicit in Python >= 3.0
class Alpha(object):
    """New-stlye class with initializer positional and keyword
    arguments, field, setter method, and property.

    """

    def __init__(self, arg, keyword=DEFAULT):
        # PYVER: identity arguments to super() are implicit in Python >= 3.0
        super(Alpha, self).__init__()
        self.arg = arg
        self.keyword = keyword
        self.field = DEFAULT
        self._value = DEFAULT
        self._prop = DEFAULT

    def get_value(self):
        return self._value

    def set_value(self, value):
        self._value = value

    def _get_prop(self):
        return self._prop

    def _set_prop(self, value):
        self._prop = value

    # PYVER: Jython 2.5.3 can't handle @prop.setter
    prop = property(_get_prop, _set_prop)


def create_alpha(arg, keyword=DEFAULT):
    """Factory function for Alpha."""
    return Alpha(arg, keyword=keyword)


class Beta(Alpha):
    """New-stlye class with initializer keyword argument, field, setter
    method, and property.

    """

    def __init__(self, keyword=DEFAULT):
        # PYVER: identity arguments to super() are implicit in Python >= 3.0
        super(Beta, self).__init__(DEFAULT, keyword=keyword)


def create_beta(keyword=DEFAULT):
    """Factory function for Beta."""
    return Beta(keyword=keyword)


# PYVER: redundant on Python >= 3.0 (actually a new-style class)
class Gamma:
    """Old-stlye class with initializer positional and keyword
    arguments, field, and setter method.

    """

    def __init__(self, arg, keyword=DEFAULT):
        self.arg = arg
        self.keyword = keyword
        self.field = DEFAULT
        self._value = DEFAULT
        # old-style classes do not support properties
        self.prop = DEFAULT

    def get_value(self):
        return self._value

    def set_value(self, value):
        self._value = value


# PYVER: redundant on Python >= 3.0 (actually a new-style class)
class Delta(Gamma):
    """Old-stlye class with initializer keyword argument, field, and
    setter method.

    """

    def __init__(self, keyword=DEFAULT):
        # PYVER: super() is preferred in Python >= 3.0
        Gamma.__init__(self, DEFAULT, keyword=keyword)


def create_delta(keyword=DEFAULT, field=DEFAULT, value=DEFAULT, prop=DEFAULT):
    delta = Delta(keyword=keyword)
    delta.field = field
    delta.set_value(value)
    delta.prop = prop
    return delta


class Epsilon(Alpha):
    """Class used to test factory and member assembly."""

    ATTRIBUTE = "Epsilon.ATTRIBUTE"

    class Zeta(Beta):

        ATTRIBUTE = "Epsilon.Zeta.ATTRIBUTE"

        @staticmethod
        def static_factory(keyword=DEFAULT):
            return Epsilon.Zeta(keyword=keyword)

        @classmethod
        def class_factory(cls, keyword=DEFAULT):
            return cls(keyword=keyword)

    @staticmethod
    def static_factory(arg, keyword=DEFAULT):
        return Epsilon(arg, keyword=keyword)

    @classmethod
    def class_factory(cls, arg, keyword=DEFAULT):
        return cls(arg, keyword=keyword)


#: Module-level member used to test member assembly.
EPSILON = Epsilon("arg", keyword="keyword")

#: Module-level member used to test member assembly.
ZETA = Epsilon.Zeta(keyword="keyword")


class Eta(Beta):
    """Class used to test lifecycle methods."""

    class Theta(Delta):

        def __init__(self):
            Delta.__init__(self)
            self.called_prepare = False
            self.called_dispose = False

        def prepare(self):
            if (not self.called_prepare):
                self.called_prepare = True
            else:
                raise Exception("already called prepare()")

        def dispose(self):
            if (not self.called_dispose):
                self.called_dispose = True
            else:
                raise Exception("already called dispose()")

    THETA = Theta()

    def __init__(self):
        super(Eta, self).__init__()
        self.called_context_after_inject = False
        self.called_context_before_clear = False
        self.called_template_after_inject = False
        self.called_template_before_clear = False
        self.called_component_after_inject = False
        self.called_component_before_clear = False
        self.called_after_inject_raise = False
        self.called_before_clear_raise = False

    def context_after_inject(self):
        if (not self.called_context_after_inject):
            self.called_context_after_inject = True
        else:
            raise Exception("already called context_after_inject()")

    def context_before_clear(self):
        if (not self.called_context_before_clear):
            self.called_context_before_clear = True
        else:
            raise Exception("already called context_before_clear()")

    def template_after_inject(self):
        if (not self.called_template_after_inject):
            self.called_template_after_inject = True
        else:
            raise Exception("already called template_after_inject()")

    def template_before_clear(self):
        if (not self.called_template_before_clear):
            self.called_template_before_clear = True
        else:
            raise Exception("already called template_before_clear()")

    def component_after_inject(self):
        if (not self.called_component_after_inject):
            self.called_component_after_inject = True
        else:
            raise Exception("already called component_after_inject()")

    def component_before_clear(self):
        if (not self.called_component_before_clear):
            self.called_component_before_clear = True
        else:
            raise Exception("already called component_before_clear()")

    def after_inject_raise(self):
        self.called_after_inject_raise = True
        raise Exception("after_inject_raise")

    def before_clear_raise(self):
        self.called_before_clear_raise = True
        raise Exception("before_clear_raise")


class Iota(object):

    def __init__(self):
        # PYVER: identity arguments to super() are implicit in Python >= 3.0
        super(Iota, self).__init__()
        self.__ordinality = 1
        self._field = DEFAULT
        self._value = DEFAULT
        self._prop = DEFAULT

    def _get_field(self):
        return self._field

    def _set_field(self, value):
        self._field = (self.__ordinality, value)
        self.__ordinality += 1

    # PYVER: Jython 2.5.3 can't handle @field.setter
    field = property(_get_field, _set_field)

    def get_value(self):
        return self._value

    def set_value(self, value):
        self._value = (self.__ordinality, value)
        self.__ordinality += 1

    def _get_prop(self):
        return self._prop

    def _set_prop(self, value):
        self._prop = (self.__ordinality, value)
        self.__ordinality += 1

    # PYVER: Jython 2.5.3 can't handle @prop.setter
    prop = property(_get_prop, _set_prop)

