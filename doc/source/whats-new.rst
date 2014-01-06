***************************
What's new in this release?
***************************

:Release: |release|

* `Python 2.5 <http://www.python.org/download/releases/2.5/>`_ is no longer
  supported (and Aglyph 2.0.0 will not run on Python 2.5 without patching).
* Creating components using :obj:`staticmethod`, :obj:`classmethod`, and nested
  classes (any level) is now supported via
  :attr:`aglyph.component.Component.factory_name`.
* Referencing class objects, nested class objects (any level), functions, or
  attributes as components is now supported via
  :attr:`aglyph.component.Component.member_name`.
* The :doc:`cookbook` has been expanded to include many new recipes, including
  examples of the aforementioned
  :attr:`aglyph.component.Component.factory_name` and
  :attr:`aglyph.component.Component.member_name` configuration options.
* The ``<eval>`` element in declarative XML configuration is **deprecated**.
  Use a ``<component>`` and a ``<reference>`` (or ``@reference`` attribute) to
  configure anything that was previously declared as an ``<eval>``.
* The :func:`aglyph.has_importable_dotted_name` function is **deprecated**.
  The :func:`aglyph.format_dotted_name` function now verifies that the dotted
  name is actually importable.
* The :func:`aglyph.identify_by_spec` function is **deprecated**. This really
  belonged in :class:`aglyph.binder.Binder` to begin with, which is where it
  now resides as a non-public method.
* Multiple calls to :meth:`aglyph.binder._Binding.init` and
  :meth:`aglyph.binder._Binding.attributes` now have a cumulative effect,
  rather than replacing any previously-specified arguments or attributes,
  respectively.
* :mod:`aglyph.compat` and :class:`aglyph.context.XMLContext` have been updated
  to avoid deprecated :mod:`xml.etree.ElementTree` methods.
* Python implementation detection in :mod:`aglyph.compat` has been improved.
* The :class:`aglyph.compat.ipyetree.XmlReaderTreeBuilder` class is
  **deprecated**. IronPython applications no longer need to explicitly pass a
  parser to :class:`aglyph.context.XMLContext` (Aglyph now uses a sensible
  default).
  *(note: with this change, the Aglyph API is now 100% cross-compatible with
  all tested Python versions and variants)*
* The :doc:`get-started` tutorial and accompanying sample code have been
  revamped to better demonstrate the various Aglyph configuration approaches,
  as well as to provide more substantive component examples.

