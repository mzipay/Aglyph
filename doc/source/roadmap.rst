***************************
Roadmap for future releases
***************************

.. warning::
   Nothing here is set in stone. This list is simply a bucket to record my
   thoughts about the **possible** future of Aglyph.

   The next release may or may not include any of items listed here, and
   might even include items *not* listed here.

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
* I've been enjoying tinkering with `CherryPy <http://www.cherrypy.org/>`_
  recently, and am considering putting together an Aglyph plugin.

