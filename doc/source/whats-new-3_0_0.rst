============================
What's new in release 3.0.0?
============================

.. _Python 3.2 lifespan: https://www.python.org/dev/peps/pep-0392/#lifespan
.. _Python 3.3 lifespan: https://www.python.org/dev/peps/pep-0398/#lifespan
.. _Python 3.6: https://docs.python.org/3.6/whatsnew/3.6.html
.. _Eval really is dangerous: https://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html
.. _Autologging: http://ninthtest.info/python-autologging/

* The `Python 3.2 lifespan`_ and `Python 3.3 lifespan`_ have ended; those
  versions are no longer actively supported in Aglyph.
* `Python 3.6`_ is now supported.
  (Cumulatively, Python 2.7, 3.4, 3.5, and 3.6 are currently supported.)
* All deprecated functions, classes, and behaviors have been replaced or
  removed, most notably:

  * The ``aglyph.binder`` module has been removed;
    programmatic configuration is now handled by :doc:`context-fluent-api`.
  * The ``aglyph.cache`` module has been removed (it is an internal
    implementation detail and should not be part of the public API).
  * The ``aglyph.compat`` package has become the *non-public*
    ``aglyph._compat`` module (it is an internal implementation detail and
    should not be part of the public API).
  * The built-in :func:`eval` function is no longer supported (see
    `Eval really is dangerous`_) in  favor of the safer :func:`ast.literal_eval`.

* Aglyph is now fully logged and traced via `Autologging`_. Tracing is
  **disabled** by default and can enabled by setting the *"AGLYPH_TRACED"*
  environment variable.

