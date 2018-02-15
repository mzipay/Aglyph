# -*- coding: UTF-8 -*-

# Copyright (c) 2006, 2011, 2013-2018 Matthew Zipay.
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

"""Test cases and runner for the :mod:`aglyph.integration.cherrypy`
module.

"""

from __future__ import absolute_import

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import logging
import unittest

from aglyph import __version__
from aglyph.assembler import Assembler
from aglyph.context import XMLContext
from aglyph.integration.cherrypy import AglyphDIPlugin

from test import dummy
from test_integration import find_basename

# don't use __name__ here; can be run as "__main__"
_logger = logging.getLogger("test_integration.test_cherrypy")

try:
    import cherrypy
    cherrypy_is_available = True
    _logger.info("using CherryPy %s", cherrypy.__version__)
except:
    cherrypy_is_available = False
    _logger.error("cherrypy is not available!")

__all__ = [
    "AglyphDIPluginTest",
    "suite"
]


@unittest.skipIf(not cherrypy_is_available, "cherrypy is not available!")
class AglyphDIPluginTest(unittest.TestCase):
    """Test the :class:`aglyph.integration.cherrypy.AglyphDIPlugin`
    class.

    """

    @classmethod
    def setUpClass(cls):
        cherrypy.server.unsubscribe()
        cherrypy.config.update(find_basename("cherrypy.ini"))
        _logger.info("unsubscribed cherrypy.server and updated cherrypy.config")

    def setUp(self):
        cherrypy.engine.aglyph = AglyphDIPlugin(
            cherrypy.engine,
            Assembler(
                XMLContext(
                    find_basename("cherrypy-aglyphdiplugin-test-context.xml"))),
            eager_init="_lazy_" not in str(self))
        cherrypy.engine.aglyph.subscribe()
        cherrypy.engine.start()
        self.bus = cherrypy.engine

    def tearDown(self):
        self.bus = None
        cherrypy.engine.stop()
        cherrypy.engine.aglyph.unsubscribe()
        cherrypy.engine.aglyph = None
        del cherrypy.engine.aglyph

    @classmethod
    def tearDownClass(cls):
        cherrypy.engine.exit()

    def test_aglyph_assemble(self):
        obj = self.bus.publish("aglyph-assemble", "module-class-1").pop()
        self.assertTrue(obj.__class__ is dummy.ModuleClass)

    def test_eager_aglyph_init_singletons(self):
        self.assertTrue(
            "test.dummy.factory_function" in
                cherrypy.engine.aglyph._assembler._caches["singleton"])
        ids = self.bus.publish("aglyph-init-singletons").pop()
        self.assertEqual(0, len(ids))

    def test_lazy_aglyph_init_singletons(self):
        self.assertFalse(
            "test.dummy.factory_function" in
                cherrypy.engine.aglyph._assembler._caches["singleton"])
        ids = self.bus.publish("aglyph-init-singletons").pop()
        self.assertEqual(["test.dummy.factory_function"], ids)

    def test_eager_aglyph_clear_singletons(self):
        # all singletons have been assembled
        ids = self.bus.publish("aglyph-clear-singletons").pop()
        self.assertEqual(["test.dummy.factory_function"], ids)
        # now clear again without re-assembling
        ids = self.bus.publish("aglyph-clear-singletons").pop()
        self.assertEqual(0, len(ids))

    def test_lazy_aglyph_clear_singletons(self):
        # no singletons have been assembled
        ids = self.bus.publish("aglyph-clear-singletons").pop()
        self.assertEqual(0, len(ids))
        # now assemble a singleton and clear again
        self.bus.publish("aglyph-assemble", "test.dummy.factory_function")
        ids = self.bus.publish("aglyph-clear-singletons").pop()
        self.assertEqual(["test.dummy.factory_function"], ids)

    def test_eager_aglyph_init_borgs(self):
        self.assertTrue(
            "module-class-2" in
                cherrypy.engine.aglyph._assembler._caches["borg"])
        ids = self.bus.publish("aglyph-init-borgs").pop()
        self.assertEqual(0, len(ids))

    def test_lazy_aglyph_init_borgs(self):
        self.assertFalse(
            "module-class-2" in
                cherrypy.engine.aglyph._assembler._caches["borg"])
        ids = self.bus.publish("aglyph-init-borgs").pop()
        self.assertEqual(["module-class-2"], ids)

    def test_eager_aglyph_clear_borgs(self):
        # all borgs have been assembled
        ids = self.bus.publish("aglyph-clear-borgs").pop()
        self.assertEqual(["module-class-2"], ids)
        # now clear again without re-assembling
        ids = self.bus.publish("aglyph-clear-borgs").pop()
        self.assertEqual(0, len(ids))

    def test_lazy_aglyph_clear_borgs(self):
        # no borgs have been assembled
        ids = self.bus.publish("aglyph-clear-borgs").pop()
        self.assertEqual(0, len(ids))
        # now assemble a borg and clear again
        self.bus.publish("aglyph-assemble", "module-class-2")
        ids = self.bus.publish("aglyph-clear-borgs").pop()
        self.assertEqual(["module-class-2"], ids)

    def _test_aglyph_clear_weakrefs(self):
        # no weakrefs have been assembled
        ids = self.bus.publish("aglyph-clear-weakrefs").pop()
        self.assertEqual(0, len(ids))
        # now assemble a weakref and clear again (keep a reference to the
        # object so the weakref doesn't die during the test!)
        obj = self.bus.publish("aglyph-assemble", "factory-function-2").pop()
        ids = self.bus.publish("aglyph-clear-weakrefs").pop()
        self.assertEqual(["factory-function-2"], ids)

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
    unittest.TextTestRunner().run(suite())

