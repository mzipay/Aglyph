# Copyright (c) 2006-2011 Matthew Zipay <mattz@ninthtest.net>
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
__version__ = "1.0.0"

__all__ = ["Alpha", "Beta", "create_alpha", "create_beta", "DEFAULT", "Delta",
           "Gamma"]

#: used as a default instead of ``None`` (easier testing)
DEFAULT = object()


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

    def _set_prop(self, prop):
        self._prop = prop

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
