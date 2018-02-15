===========================
Roadmap for future releases
===========================

.. _disdain for XML in the Python community: https://blog.startifact.com/posts/older/about-the-disdain-for-xml-among-python-programmers.html
.. _YAML: http://www.yaml.org/

.. warning::
   Nothing here is set in stone. This list is simply a bucket to record my
   thoughts about the **possible** future of Aglyph.

   The next release may or may not include any of items listed here, and
   might even include items *not* listed here.

* There's quite a bit of `disdain for XML in the Python community`_.
  I personally do not agree with it, but that's the reality. Regardless of
  whether or not the anti-XML sentiments are warranted, though, it does at
  least *suggest* that there might be a place for an alternative
  non-programmatic (i.e. text-based) configuration option for Aglyph. I'm
  mulling over :mod:`json`, :mod:`configparser`, and `YAML`_ at the moment.
* I have encountered several real-world scenarios which suggest that support for
  **bound** factory methods as an object creation strategy is needed. (These
  scenarios come almost exclusively from the Java world, but Aglyph is committed
  to supporting Jython, so...)

