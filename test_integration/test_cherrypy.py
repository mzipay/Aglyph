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

"""Test cases and runner for the :mod:`aglyph.integration.cherrypy`
module.

"""

from __future__ import absolute_import

__author__ = "Matthew Zipay <mattz@ninthtest.net>"
__version__ = "2.1.0"

import logging
import unittest

from aglyph.assembler import Assembler
from aglyph.binder import Binder
from aglyph.context import XMLContext, Reference as ref
from aglyph.integration.cherrypy import AglyphDIPlugin

from test import dummy, enable_debug_logging, skip_if
from test_integration import find_basename

try:
    import cherrypy
    cherrypy_is_available = True
except:
    cherrypy_is_available = False

__all__ = [
    "suite"
]

# don't use __name__ here; can be run as "__main__"
_logger = logging.getLogger("test_integration.test_cherrypy")

if (cherrypy_is_available):
    _logger.info("using CherryPy %s", cherrypy.__version__)
    cherrypy.server.unsubscribe()
    cherrypy.config.update(find_basename("cherrypy.ini"))
    _logger.info("unsubscribed cherrypy.server and updated cherrypy.config")
else:
    _logger.error("cherrypy is not available!")


class _PluginTestBinder(Binder):

    def __init__(self):
        super(_PluginTestBinder, self).__init__(
            binder_id="cherrypy-aglyphdiplugin-test-binder")
        self.bind("alpha", to=dummy.Alpha).init(None)
        self.bind(dummy.Beta, strategy="singleton")
        self.bind("gamma", to=dummy.Gamma, strategy="borg").init(None)
        self.bind(dummy.Delta, strategy="weakref")


@skip_if(not cherrypy_is_available, "cherrypy is not available!")
class AglyphDIPluginTest(unittest.TestCase):
    """Test the :class:`aglyph.integration.cherrypy.AglyphDIPlugin`
    class.

    """

    def setUp(self):
        eager_init = "_lazy_" not in str(self)
        cherrypy.engine.aglyph = AglyphDIPlugin(cherrypy.engine,
                                                _PluginTestBinder(),
                                                eager_init=eager_init)
        cherrypy.engine.aglyph.subscribe()
        cherrypy.engine.start()
        self.bus = cherrypy.engine

    def tearDown(self):
        self.bus = None
        cherrypy.engine.stop()
        cherrypy.engine.aglyph.unsubscribe()
        cherrypy.engine.aglyph = None
        del cherrypy.engine.aglyph

    def test_aglyph_assemble(self):
        obj = self.bus.publish("aglyph-assemble", "alpha").pop()
        self.assertTrue(obj.__class__ is dummy.Alpha)

    def test_eager_aglyph_init_singletons(self):
        self.assertTrue("test.dummy.Beta" in
                        cherrypy.engine.aglyph._assembler._cache["singleton"])
        ids = self.bus.publish("aglyph-init-singletons").pop()
        self.assertEqual(0, len(ids))

    def test_lazy_aglyph_init_singletons(self):
        self.assertFalse("test.dummy.Beta" in
                         cherrypy.engine.aglyph._assembler._cache["singleton"])
        ids = self.bus.publish("aglyph-init-singletons").pop()
        self.assertEqual(["test.dummy.Beta"], ids)

    def test_eager_aglyph_clear_singletons(self):
        # all singletons have been assembled
        ids = self.bus.publish("aglyph-clear-singletons").pop()
        self.assertEqual(["test.dummy.Beta"], ids)
        # now clear again without re-assembling
        ids = self.bus.publish("aglyph-clear-singletons").pop()
        self.assertEqual(0, len(ids))

    def test_lazy_aglyph_clear_singletons(self):
        # no singletons have been assembled
        ids = self.bus.publish("aglyph-clear-singletons").pop()
        self.assertEqual(0, len(ids))
        # now assemble a singleton and clear again
        self.bus.publish("aglyph-assemble", "test.dummy.Beta")
        ids = self.bus.publish("aglyph-clear-singletons").pop()
        self.assertEqual(["test.dummy.Beta"], ids)

    def test_eager_aglyph_init_borgs(self):
        self.assertTrue("gamma" in
                        cherrypy.engine.aglyph._assembler._cache["borg"])
        ids = self.bus.publish("aglyph-init-borgs").pop()
        self.assertEqual(0, len(ids))

    def test_lazy_aglyph_init_borgs(self):
        self.assertFalse("gamma" in
                         cherrypy.engine.aglyph._assembler._cache["borg"])
        ids = self.bus.publish("aglyph-init-borgs").pop()
        self.assertEqual(["gamma"], ids)

    def test_eager_aglyph_clear_borgs(self):
        # all borgs have been assembled
        ids = self.bus.publish("aglyph-clear-borgs").pop()
        self.assertEqual(["gamma"], ids)
        # now clear again without re-assembling
        ids = self.bus.publish("aglyph-clear-borgs").pop()
        self.assertEqual(0, len(ids))

    def test_lazy_aglyph_clear_borgs(self):
        # no borgs have been assembled
        ids = self.bus.publish("aglyph-clear-borgs").pop()
        self.assertEqual(0, len(ids))
        # now assemble a borg and clear again
        self.bus.publish("aglyph-assemble", "gamma")
        ids = self.bus.publish("aglyph-clear-borgs").pop()
        self.assertEqual(["gamma"], ids)

    def _test_aglyph_clear_weakrefs(self):
        # no weakrefs have been assembled
        ids = self.bus.publish("aglyph-clear-weakrefs").pop()
        self.assertEqual(0, len(ids))
        # now assemble a weakref and clear again (keep a reference to the
        # object so the weakref doesn't die during the test!)
        obj = self.bus.publish("aglyph-assemble", "test.dummy.Delta").pop()
        ids = self.bus.publish("aglyph-clear-weakrefs").pop()
        self.assertEqual(["test.dummy.Delta"], ids)

    # no difference between eager/lazy, as weakrefs are never eagerly
    # initialized (makes no sense to do so since the references would be dead
    # as soon as the method returned)
    test_eager_aglyph_clear_weakrefs = _test_aglyph_clear_weakrefs
    test_lazy_aglyph_clear_weakrefs = _test_aglyph_clear_weakrefs


def suite():
    """Build the test suite for the :mod:`aglyph.integration.cherrypy`
    module.

    """
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AglyphDIPluginTest))
    _logger.debug("RETURN %r", suite)
    return suite


if (__name__ == "__main__"):
    enable_debug_logging(suite)
    unittest.TextTestRunner().run(suite())

