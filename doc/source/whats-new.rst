==================================
What's new in release 3.0.0.post1?
==================================

.. _Python 3.7: https://docs.python.org/3.7/whatsnew/3.7.html
.. _IronPython: http://ironpython.net/
.. _Autologging: http://ninthtest.info/python-autologging/
.. _Sphinx: http://www.sphinx-doc.org/
.. _PyPI: https://pypi.org/
.. _Setuptools: https://setuptools.readthedocs.io/
.. _Markdown Descriptions on PyPI: https://dustingram.com/articles/2018/03/16/markdown-descriptions-on-pypi
.. _Alabaster: https://alabaster.readthedocs.io/

This is just a small "housekeeping" (post-)release.

.. note::
   There is no immediate reason to upgrade from **3.0.0**, as no core
   functionality has changed.

   The updates to :doc:`testing` are valid for release **3.0.0** as well as
   this post-release.

* `Python 3.7`_ is now officially supported.
  (Cumulatively, Python 2.7, 3.4, 3.5, 3.6 and 3.7 are officially supported.)
* :doc:`testing` has been updated with recent Python versions, variants and
  platforms to match the officially supported versions.
* A small change in the ``aglyph._compat`` module related to `IronPython`_
  detection (the purpose of which is to keep detection logic the same
  between Aglyph and `Autologging`_).
* Some documentation-related  updates:

  * upgraded the `Sphinx`_ version (and therefore the documentation
    *Makefile*) used to generate the HTML docs
  * switch to using the (default) `Alabaster`_ `Sphinx`_ theme
  * added a warning in :doc:`context-fluent-api` regarding the absence of
    ``__qualname__`` in Python versions < 3.3

* `PyPI`_/`Setuptools`_ changes:

  * use `Markdown Descriptions on PyPI`_
  * locked the `Autologging`_ version to ``1.2.0`` (see *requirements.txt*)

* One deprecation: the ``aglyph.version_info`` module attribute (which should
  not have been public in the first place)

Previous releases of Aglyph
===========================

.. toctree::
   :maxdepth: 1

   whats-new-3_0_0
   whats-new-2_1_1
   whats-new-2_1_0
   whats-new-2_0_0
   whats-new-1_1_1
   whats-new-1_1_0

