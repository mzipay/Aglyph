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

"""Classes and utilities for integrating Aglyph with
`CherryPy <http://www.cherrypy.org/>`_.

.. versionadded:: 2.1.0

An example using XML configuration::

   from aglyph.assembler import Assembler
   from aglyph.context import XMLContext
   from aglyph.integration.cherrypy import AglyphDIPlugin
   import cherrypy

   context = XMLContext("my-aglyph-context.xml")
   assembler = Assembler(context)

   cherrypy.engine.aglyph = AglyphDIPlugin(cherrypy.engine, assembler)
   cherrypy.engine.aglyph.subscribe()

An example using the fluent configuration API::

   from aglyph.integration.cherrypy import AglyphDIPlugin
   from aglyph.context import Context
   import cherrypy

   context = Context("my-aglyph-context")
   context.template(...)
   context.prototype(...)
   context.singleton(...)
   context.borg(...)
   context.weakref(...)
   # and so on
   assembler = Assembler(context)

   cherrypy.engine.aglyph = AglyphDIPlugin(cherrypy.engine, assembler)
   cherrypy.engine.aglyph.subscribe()

In either scenario, you can now use Aglyph to assemble components in
your CherryPy application by publishing an "aglyph-assemble" event to
the `Web Site Process Bus
<https://cherrypy.readthedocs.org/en/latest/pkg/cherrypy.process.html#web-site-process-bus>`_.
This event requires an Aglyph component specification (either an ID or
an object whose dotted name is a component ID)::

   ...
   my_obj = cherrypy.engine.publish("aglyph-assemble", "my-id").pop()
   ...

"""

from __future__ import absolute_import

__author__ = "Matthew Zipay <mattz@ninthtest.info>"

import logging

# for logging, use self.bus.log rather than self.__log
from autologging import traced

from aglyph import __version__
from aglyph._compat import name_of

from cherrypy.process.plugins import SimplePlugin

__all__ = [
    "AglyphDIPlugin",
]

_log = logging.getLogger(__name__)


@traced
class AglyphDIPlugin(SimplePlugin):
    """A `CherryPy <http://www.cherrypy.org/>`_ `plugin
    <https://cherrypy.readthedocs.org/en/latest/extend.html#plugins>`_
    that provides Aglyph dependency injection support to CherryPy
    applications.

    The Aglyph DI plugin subscribes to the following channels:

    aglyph-assemble
       Publish a component ID to this channel to assemble the component.

    aglyph-init-singletons
       Publish to this channel to pre-assemble and cache all *singleton*
       components.

    aglyph-clear-singletons
       Publish to this channel to clear all cached *singleton*
       components.

    aglyph-init-borgs
       Publish to this channel to pre-assemble and cache the
       shared-states of all *borg* components.

    aglyph-clear-borgs
       Publish to this channel to clear all cached *borg* components.

    aglyph-clear-weakrefs
       Publish to this channel to clear all cached *weakref* components.

    """

    def __init__(self, bus, assembler, eager_init=True):
        """
        :arg cherrypy.process.wspbus.Bus bus:
           the CherryPy Web Site Process Bus
        :arg aglyph.assembler.Assembler assembler:
           the configured Aglyph assembler (or binder)
        :keyword bool eager_init:
           if ``True``, all *singleton* and *borg* components in the
           assembler's context will be pre-assembed and cached when the
           Aglyph DI plugin is started

        """
        SimplePlugin.__init__(self, bus)
        self._assembler = assembler
        self._eager_init = eager_init

    @property
    def eager_init(self):
        """Return the current value of the eager initialization flag."""
        return self._eager_init

    @eager_init.setter
    def eager_init(self, flag):
        """Set the eager initialization flag.

        :arg bool flag:
           whether (``True``) or not (``False``) the Aglyph DI plugin
           should pre-assemble and cache all *singleton* and *borg*
           components when the plugin is (re)started

        """
        self._eager_init = flag

    def start(self):
        """Subscribe to all Aglyph DI channels.

        aglyph-assemble
           Publish a component ID to this channel to assemble the
           component.

        aglyph-init-singletons
           Publish to this channel to pre-assemble and cache all
           *singleton* components.

        aglyph-clear-singletons
           Publish to this channel to clear all cached *singleton*
           components.

        aglyph-init-borgs
           Publish to this channel to pre-assemble and cache the
           shared-states of all *borg* components.

        aglyph-clear-borgs
           Publish to this channel to clear all cached *borg*
           components.

        aglyph-clear-weakrefs
           Publish to this channel to clear all cached *weakref*
           components.

        .. note::
           If :attr:`eager_init` is ``True``, all *singleton* and *borg*
           components are pre-assembled and cached before the channels
           are subscribed.

        """
        if self._eager_init:
            self.bus.log(
                "initializing Aglyph singleton and borg component objects")
            self.init_singletons()
            self.init_borgs()
        self.bus.log("starting Aglyph dependency injection support")
        self.bus.subscribe("aglyph-assemble", self.assemble)
        self.bus.subscribe("aglyph-init-singletons", self.init_singletons)
        self.bus.subscribe("aglyph-clear-singletons", self.clear_singletons)
        self.bus.subscribe("aglyph-init-borgs", self.init_borgs)
        self.bus.subscribe("aglyph-clear-borgs", self.clear_borgs)
        self.bus.subscribe("aglyph-clear-weakrefs", self.clear_weakrefs)

    def stop(self):
        """Unsubscribe from all Aglyph DI channels.

        .. note::
           After all Aglyph DI channels have been unsubscribed, the
           *singleton*, *borg*, and *weakref* caches are automatically
           cleared.

        """
        self.bus.log("stopping Aglyph dependency injection support")
        self.bus.unsubscribe("aglyph-assemble", self.assemble)
        self.bus.unsubscribe("aglyph-init-singletons", self.init_singletons)
        self.bus.unsubscribe("aglyph-clear-singletons", self.clear_singletons)
        self.bus.unsubscribe("aglyph-init-borgs", self.init_borgs)
        self.bus.unsubscribe("aglyph-clear-borgs", self.clear_borgs)
        self.bus.unsubscribe("aglyph-clear-weakrefs", self.clear_weakrefs)
        self.bus.log(
            "clearing Aglyph singleton, borg, and weakref component objects")
        self.clear_singletons()
        self.clear_borgs()
        self.clear_weakrefs()

    def assemble(self, component_spec):
        """Return the object assembled according to *component_spec*.

        :arg component_spec:
           a string representing a component dotted name or unique ID;
           or an importable class, function, or module
        :return:
           a complete object with all of its resolved dependencies

        This method handles messages published to the
        **aglyph-assemble** channel.

        """
        self.bus.log("assembling %r" % component_spec)
        return self._assembler.assemble(component_spec)

    def init_singletons(self):
        """Assemble and cache all singleton component objects.

        :return:
           the initialized singleton component IDs
        :rtype:
           :obj:`list`

        This method handles messages published to the
        **aglyph-init-singletons** channel.

        """
        singleton_ids = self._assembler.init_singletons()
        if singleton_ids:
            self.bus.log("initialized singletons %s" % repr(singleton_ids))
        return singleton_ids

    def clear_singletons(self):
        """Evict all cached singleton component objects.

        :return:
           the evicted singleton component IDs
        :rtype:
           :obj:`list`

        This method handles messages published to the
        **aglyph-clear-singletons** channel.

        """
        singleton_ids = self._assembler.clear_singletons()
        if singleton_ids:
            self.bus.log("cleared singletons %s" % repr(singleton_ids))
        return singleton_ids

    def init_borgs(self):
        """Assemble and cache the shared-states for all borg component
        objects.

        :return:
           the initialized borg component IDs
        :rtype:
           :obj:`list`

        This method handles messages published to the
        **aglyph-init-borgs** channel.

        """
        borg_ids = self._assembler.init_borgs()
        if borg_ids:
            self.bus.log("initialized borgs %s" % repr(borg_ids))
        return borg_ids

    def clear_borgs(self):
        """Evict all cached borg component shared-states.

        :return:
           the evicted borg component IDs
        :rtype:
           :obj:`list`

        This method handles messages published to the
        **aglyph-clear-borgs** channel.

        """
        borg_ids = self._assembler.clear_borgs()
        if borg_ids:
            self.bus.log("cleared borgs %s" % repr(borg_ids))
        return borg_ids

    def clear_weakrefs(self):
        """Evict all cached weakref component objects.

        :return:
           the evicted weakref component IDs
        :rtype:
           :obj:`list`

        This method handles messages published to the
        **aglyph-clear-weakrefs** channel.

        """
        weakref_ids = self._assembler.clear_weakrefs()
        if weakref_ids:
            self.bus.log("cleared weakrefs %s" % repr(weakref_ids))
        return weakref_ids

    def __str__(self):
        return "<%s @%08x %s>" % (
            name_of(self.__class__), id(self), self._assembler)

    def __repr__(self):
        return "%s.%s(%r, %r, eager_init=%r)" % (
            self.__class__.__module__, name_of(self.__class__),
            self.bus, self._assembler, self._eager_init)

