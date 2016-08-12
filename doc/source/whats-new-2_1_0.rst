============================
What's new in release 2.1.0?
============================

* `Python 2.6 <http://www.python.org/download/releases/2.6/>`_ is no longer
  supported (and Aglyph 2.1.0 will not run on Python 2.6 without patching).
* Aglyph now supports :ref:`lifecycle methods <lifecycle-methods>`, which may
  be declared at the context, template, and/or component level for the "after
  injection" and "before clear" lifecycle states.
* Aglyph now supports a form of component "inheritance" through
  :class:`aglyph.component.Template` (XML ``<template>``). Refer to
  :doc:`cookbook-templating` for examples.
* The :download:`Aglyph context DTD <../../resources/aglyph-context.dtd>` has
  been updated to support both lifecycle methods and templates.
* The :mod:`aglpyh.integration` package has been added to support integrating
  Aglyph with other projects. Aglyph 2.1.0 introduces `CherryPy
  <http://www.cherrypy.org/>`_ integration using the classes defined in
  :mod:`aglyph.integration.cherrypy`. Refer to :doc:`cookbook-integration` for
  examples.
* The caches defined in :mod:`aglyph.cache` are now implemented as `context
  managers <https://docs.python.org/3/library/stdtypes.html#typecontextmanager>`_,
  and the public ``lock`` members have been deprecated.
* A "safe" representation is now used to log assembled objects, ensuring that
  possibly sensitive data is not logged.
* Deprecated classes and functions now issue
  :class:`aglyph.AglyphDeprecationWarning`.

