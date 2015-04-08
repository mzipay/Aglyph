===========================
Roadmap for future releases
===========================

.. warning::
   Nothing here is set in stone. This list is simply a bucket to record my
   thoughts about the **possible** future of Aglyph.

   The next release may or may not include any of items listed here, and
   might even include items *not* listed here.

* Support for `Python 3.1 <https://www.python.org/download/releases/3.1.5/>`_
  **will be dropped**. This *may* happen as early as release 2.2.0, but
  *definitely* before 3.0.0.
* There isn't really a need for :class:`aglyph.assembler.Assembler` and
  :class:`aglyph.binder.Binder` to be separate classes. I will likely absorb
  all of the Binder functionality into Assembler and deprecate Binder. (This
  will involve significant changes to the public API, so this change will
  definitely **not** be made in the 2.x.y series of releases.)
* There's quite a bit of `disdain for XML in the Python community
  <http://blog.startifact.com/posts/older/about-the-disdain-for-xml-among-python-programmers.html>`_.
  I personally do not agree with it, but that's the reality. Regardless of
  whether or not the anti-XML sentiments are warranted, though, it does at
  least *suggest* that there might be a place for an alternative
  non-programmatic (i.e. text-based) configuration option for Aglyph. I'm
  mulling over :mod:`json`, :mod:`configparser`, and
  `YAML <http://www.yaml.org/>`_ at the moment.
* Strictly speaking, a decorator-based configuration approach violates Aglyph's
  "non-intrusive" principle. However, decorators (and annotations in Java,
  particularly as used for DI within the `Spring Framework
  <http://projects.spring.io/spring-framework/>`_) have *exploded* in
  popularity over the past several years. Since Aglyph also tries to maintain
  an opinionless stance on configuration, some kind of decorator-based approach
  might be an option.

