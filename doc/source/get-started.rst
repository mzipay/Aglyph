===========================
Getting started with Aglyph
===========================

During this brief tutorial, you will download and install Aglyph, build a
simple Python application based on the *MovieLister* component discussed in
`Inversion of Control Containers and the Dependency Injection pattern
<http://martinfowler.com/articles/injection.html>`_, then modify the
application to take advantage of Aglyph dependency injection. This process will
allow you understand the Dependency Injection pattern in general, as well as
the Aglyph approach to Dependency Injection.

This tutorial is a "whirlwind tour" of Aglyph that covers only the basics. Once
you have completed the steps, please review the :doc:`api-ref` and the
:download:`aglyph-context-1.0.0 DTD <../../resources/aglyph-context-1.0.0.dtd>`
to understand the details.

The tutorial assumes that you are familiar with Python development in general,
and that Python 2.5+ is already installed. For an introduction to Python,
please see `The Python Tutorial
<http://docs.python.org/py3k/tutorial/index.html>`_ (also, the free `Dive Into
Python <http://diveintopython.net/>`_ and `Dive Into Python 3
<http://diveintopython3.net/>`_ books). Python can be downloaded from `Python
Programming Language – Official Website <http://www.python.org/>`_ (or just use
your preferred package installer, e.g. RPM).

.. note::

    It is recommended, but not required, that you read the `Inversion of
    Control Containers and the Dependency Injection pattern
    <http://martinfowler.com/articles/injection.html>`_ and `Python Dependency
    Injection [PDF] <http://www.aleax.it/yt_pydi.pdf>`_ articles before
    beginning this tutorial.

1. Download and install Aglyph
------------------------------

Download the latest :mod:`distutils` source or built distribution of `Aglyph on
SourceForge <http://sourceforge.net/projects/aglyph/files/aglyph/>`_.

**--- OR ---**

Clone the
`Aglyph Mercurial repository from BitBucket
<https://bitbucket.org/mzipay/aglyph>`_.

If you downloaded the source distribution, unpack it into a temporary directory
and then navigate into that directory. Issue the following commands from a
terminal::

    python setup.py test
    python setup.py install

If you downloaded a built distribution, install it using the appropriate
platform-specific tool.

If you cloned the repository from BitBucket, navigate into the root directory
of the repository and issue the following commands from a terminal::

    python setup.py test
    python setup.py install

Verify that the installation was successful by importing the ``aglyph`` module
from a Python interpreter. For example::

    $ python
    Python 3.3.0 (default, Sep 29 2012, 08:16:19) 
    [GCC 4.2.1 (Apple Inc. build 5666) (dot 3)] on darwin
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import aglyph

2. Download, extract, and run the *movielisterapp* application
--------------------------------------------------------------

The sample code for this tutorial can be downloaded
:download:`here <../../resources/movielisterapp-basic.zip>` (or find it under
the *examples/* directory if you cloned the `Aglyph Mercurial repository from
BitBucket <https://bitbucket.org/mzipay/aglyph>`_). Extract the ZIP
archive to a temporary location and navigate into the application directory::

    $ unzip movielisterapp-basic.zip
    ...
    $ cd movielisterapp-basic

The *movies.txt* file is a simple colon-delimited text file that contains a
number of *title:director* records, one per line::

    The Colossus of Rhodes:Sergio Leone
    Once Upon a Time in the West:Sergio Leone
    THX 1138:George Lucas
    American Graffiti:George Lucas
    Once Upon a Time in America:Sergio Leone
    Sixteen Candles:John Hughes
    The Breakfast Club:John Hughes
    Weird Science:John Hughes
    Ferris Bueller's Day Off:John Hughes

This data file is read by a particular implementation of the ``MovieFinder``
class (``ColonDelimitedMovieFinder``), both of which can be found in the
``movies/finder.py`` module::

    from movies.movie import Movie
    
    
    class MovieFinder:
    
        def find_all(self):
            raise NotImplementedError()
    
    
    class ColonDelimitedMovieFinder(MovieFinder):
    
        def __init__(self, filename):
            movies = []
            f = open(filename)
            for line in f:
                (title, director) = line.strip().split(':')
                movies.append(Movie(title, director))
            f.close()
            self._movies = movies
    
        def find_all(self):
            return self._movies

As you can see, each record is processed as a simple ``Movie`` data holder
object. The ``movies/movie.py`` module holds the ``Movie`` class definition::

    class Movie:
    
        def __init__(self, title, director):
            self.title = title
            self.director = director

Finally, we have a ``MovieLister`` class (defined in the ``movies/lister.py``
module), which uses a ``ColonDelimitedMovieFinder`` to find the movies directed
by a particular director::

    from movies.finder import ColonDelimitedMovieFinder


    class MovieLister:
    
        def __init__(self):
            self._finder = ColonDelimitedMovieFinder("movies.txt")
    
        def movies_directed_by(self, director):
            for movie in self._finder.find_all():
                if (movie.director == director):
                    yield movie

The application can be executed using the ``app.py`` script, which simply asks
a ``MovieLister`` for all movies directed by "Sergio Leone"::

    $ python app.py 
    The Colossus of Rhodes
    Once Upon a Time in the West
    Once Upon a Time in America

A *(very)* brief introduction to Dependency Injection
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Examine the ``MovieLister`` class (in the ``movies/lister.py`` module) again.
There are three things to note:

#. The ``MovieLister`` class depends on a concrete implementation of
   ``MovieFinder``.
#. The ``ColonDelimitedMovieFinder`` class depends on a filename.
#. The ``MovieLister`` is responsible for resolving *both* dependencies.

As a consequence of (3), neither the concrete ``MovieFinder`` implementation
nor the name/location of the data file can be changed without modifying
``MovieLister``.

In other words, it is ``MovieLister`` that controls dependency
resolution. It is this aspect of control that is being inverted ("Inversion of
Control") when we talk about **Dependency Injection**. Rather than having
``MovieLister`` be responsible for *resolving* its dependencies, we instead
give control to some other object (an "assembler"), which has the
responsibility of *injecting* dependencies into ``MovieLister``.

The dependency injection approach provides several benefits:

* easier testing ("mock" or "stub" objects for testing are easier to manage)
* lower general maintenance cost (e.g. the manner in which application/domain
  objects get initialized and connected to one another is "homogenized" in the
  assembler's configuration, which makes application-wide changes easier to
  apply and test)
* the separation of object *configuration* from object *use* means generally
  smaller and simpler application code that is focused on object behavior

Aglyph can inject dependencies using initializers -- ``__init__`` methods -- or
"factory" functions (type 2 "constructor" injection); or member variables,
setter methods, and properties (type 3 "setter" injection).

In order to take advantage of type 2 "constructor" injection, the ``__init__``
method or "factory" function must *accept* dependencies, which means we need
to make some simple changes to *movielisterapp*...

3. Make some general improvements to the *movielisterapp* application
---------------------------------------------------------------------

As written, the basic application is somewhat change-resistant. For example, if
we wish to support another implementation of ``MovieFinder`` (e.g. a
``CSVMovieFinder``), then we would also need to change the ``MovieLister``
implementation.

A simple solution to this problem is to change ``MovieLister`` so that it can
*accept* a ``MovieFinder`` at initialization time::

    class MovieLister:
    
        def __init__(self, finder):
            self._finder = finder
    
        def movies_directed_by(self, director):
            for movie in self._finder.find_all():
                if (movie.director == director):
                    yield movie

Next, we'll add the ``CSVMovieFinder`` class definition to the
``movies/finder.py`` module::

    import csv
    from movies.movie import Movie
    
    
    class MovieFinder:
    
        def find_all(self):
            raise NotImplementedError()
    
    
    class ColonDelimitedMovieFinder(MovieFinder):
    
        def __init__(self, filename):
            movies = []
            f = open(filename)
            for line in f:
                (title, director) = line.strip().split(':')
                movies.append(Movie(title, director))
            f.close()
            self._movies = movies
    
        def find_all(self):
            return self._movies
    
    
    class CSVMovieFinder(MovieFinder):
    
        def __init__(self, filename):
            movies = []
            f = open(filename)
            for (title, director) in csv.reader(f):
                movies.append(Movie(title, director))
            f.close()
            self._movies = movies
    
        def find_all(self):
            return self._movies

The ``CSVMovieFinder`` expects a CSV filename. We'll create *movies.csv* so
that it contains the same records as the original *movies.txt* file::

    The Colossus of Rhodes,Sergio Leone
    Once Upon a Time in the West,Sergio Leone
    THX 1138,George Lucas
    American Graffiti,George Lucas
    Once Upon a Time in America,Sergio Leone
    Sixteen Candles,John Hughes
    The Breakfast Club,John Hughes
    Weird Science,John Hughes
    Ferris Bueller's Day Off,John Hughes

Finally, we'll change ``app.py`` so that the new ``CSVMovieFinder`` is used to
initialize a ``MovieLister``::

    import sys
    
    from movies.finder import CSVMovieFinder
    from movies.lister import MovieLister
    
    app = MovieLister(CSVMovieFinder("movies.csv"))
    for movie in app.movies_directed_by("Sergio Leone"):
        sys.stdout.write("%s\n" % movie.title)

Running the application again should give us the same results::

    $ python app.py 
    The Colossus of Rhodes
    Once Upon a Time in the West
    Once Upon a Time in America

The basic application is now more flexible: we can change the ``MovieFinder``
implementation without having to modify the ``MovieLister`` class definition.
However, we are still required to modify ``app.py`` if we decide to change the
``MovieFinder`` implementation.

.. note::

    An important aspect of Aglyph is that it is **non-intrusive**, meaning that
    it requires only minimal changes to your existing application code in order
    to provide dependency injection capabilities.

    Notice that the changes made in this section, while adding flexibility to
    the application, did not require the use of Aglyph. In fact, as we add
    Aglyph dependency injection support in the next two sections, *no further
    changes to the ``movies/lister.py``, ``movies/finder.py``, or
    ``movies/movie.py`` module need to be made.*

4. Add Dependency Injection support to the *movielisterapp* application
-----------------------------------------------------------------------------

Recall that Dependency Injection gives reponsibility for injecting dependencies
to an an external object (called an "assembler"). In Aglyph, this "assembler"
is defined by the :class:`aglyph.assembler.Assembler` class.

An ``aglyph.assembler.Assembler`` requires a "context," which is a collection
of component definitions. A *component definition* is simply a
description of some callable (an importable class or function), including its
dependencies. Any component can itself be a dependency of any other
component(s).

In Aglyph, a context is defined by the :class:`aglyph.context.Context` class. A
specialized subclass, :class:`aglyph.context.XMLContext`, is provided to allow a
context to be defined declaratively in an XML document. Such XML documents
must conform to the :download:`aglyph-context-1.0.0 DTD
<../../resources/aglyph-context-1.0.0.dtd>`.

The ``aglyph.context.Context`` class may also be used directly to define a
context in pure Python. This approach requires the use of the
:class:`aglyph.component.Component` class, and (optionally) one of more of:

* :class:`aglyph.component.Reference` (used to indicate that a dependency refers
  to another component in the same context)
* :class:`aglyph.component.Evaluator` (similar to :func:`functools.partial`)
* :class:`aglyph.component.Strategy` (used to control how an object of a
  component is created)

.. versionchanged:: 1.1.0
    The preferred approach to programmatic configuration is now
    :class:`aglyph.binder.Binder`, which is more succinct than using
    ``Context`` and ``Component`` directly.

.. note::

    Using ``Context`` and ``Component`` directly is still supported (and, in
    fact, ``Binder`` uses them internally). You can view ``Binder`` as a
    "layer of abstraction" on top of ``Context`` and ``Component``.

We will start by creating an Aglyph context for the *movielisterapp*
application. **For illustrative purposes, both an XML context and a
pure-Python configuration will be created; in practice, one OR the other is
recommended.**

First, we'll create the XML context document as *movies-context.xml*::

    <?xml version="1.0" encoding="utf-8"?>
    <context id="movies-context">
        <component id="movies.finder.ColonDelimitedMovieFinder">
            <init>
                <arg><str>movies.txt</str></arg>
            </init>
        </component>
        <component id="csv-finder" dotted-name="movies.finder.CSVMovieFinder">
            <init>
                <arg><str>movies.csv</str></arg>
            </init>
        </component>
        <component id="movies.lister.MovieLister">
            <init>
                <arg reference="csv-finder"/>
            </init>
        </component>
    </context>

Some interesting things to note here:

* A ``<context>`` requires an ``id`` attribute, which should uniquely identify
  the context.
* A ``<component>`` requires an ``id`` attribute, and has an optional
  ``dotted-name`` attribute (as well as an optional ``strategy`` attribute,
  which will be covered later). If ``dotted-name`` is not provided, then the
  ``id`` attribute is assumed to be a dotted-name; otherwise, the ``id`` can
  be a user-defined identifier and the ``dotted-name`` **must** be provided
  (this is useful when describing multiple components of the same class, for
  example). A *dotted-name* is a string that represents an **importable** class
  or function.
* Initialization arguments are provided as ``<arg>`` elements in an ``<init>``
  section. An ``<arg>`` is a postional argument (the order in which they're
  defined in the XML is significant!), while an ``<arg keyword="...">`` is a
  keyword argument.

Notice that the *movies.lister.MovieLister* component is being injected with a
reference to the *csv-finder* component, which describes an instance of
``movies.finder.CSVMovieFinder``. We could easily change back to using
``movies.finder.ColonDelimitedMovieFinder`` by changing the reference.

Next, we'll create the pure-Python configuration as the ``MoviesBinder`` class
(a subclass of ``aglyph.binder.Binder``) in the ``movies/__init__.py`` module::

    from aglyph.binder import Binder

    from movies.lister import MovieLister
    from movies.finder import MovieFinder, CSVMovieFinder


    class MoviesBinder(Binder):

        def __init__(self):
            super(MoviesBinder, self).__init__("movies-binder")
            self.bind(MovieLister).init(MovieFinder)
            self.bind(MovieFinder, to=CSVMovieFinder).init("movies.csv")

Some interesting things to note here:

* When we bind ``MovieLister``, we don't bind it **to** anything. Why? Python
  does not support interfaces as a language construct (mixins and :mod:`abc`
  are the alternatives). So in this case, ``MovieLister`` actually serves as
  *both* the "interface" and the implementation. Duck-typing means that
  "anything that looks like a MovieLister and acts like a MovieLister" should
  be treated *as* a ``MovieLister``. We could just as easily create a
  specialized subclass (say, ``FancyMovieLister``) and then bind *it* to
  ``MovieLister`` using ``bind(MovieLister, FancyMovieLister)``.
* ``MovieFinder`` can't be used on its own (it's a pre-:mod:`abc` abstract base
  class), and so we bind it to our preferred implementation,
  ``CSVMovieFinder``.
* The :meth:`aglyph.binder.Binder.bind` method returns a proxy object that
  allows us to specify the initialization (constructor) dependencies. The
  dependencies are provided according to the signature of the initializer;
  ``Binder`` knows that a class or function passed as a dependency refers to
  another bound component.

Take a minute to examine the XML context and the pure-Python configuration;
they will produce *identical* results. Each will inject the string
*"movies.csv"* into a ``CSVMovieFinder``, and then inject the
``CSVMovieFinder`` instance into a ``MovieLister``.

.. note::

    Aglyph assembles components according to a *strategy* (sometimes called a
    "scope"). Aglyph supports three strategies:

    ``Strategy.PROTOTYPE`` = *"prototype"*
        a new object is always be created 

    ``Strategy.SINGLETON`` = *"singleton"*
        only one obejct is created; this object is cached by the assembler

    ``Strategy.BORG`` = *"borg"*
        a new object is always created; however, the internal state is cached
        by the assembler and then assigned directly to the ``__dict__`` of all
        new objects

    The assembly strategy for a component may be specified in the XML
    context or in pure Python. The following examples define a singleton
    component.

    In XML::

        <component id="the-object" dotted-name="builtins.object" strategy="singleton"/>

    In Python::

        Binder().bind("the-object", to=object, strategy="singleton")
        # -or-
        Component("the-object", "__builtin__.object", Strategy.SINGLETON)

    If a strategy is not explicitly specified as part of the component
    definition, the default strategy is **prototype**.

Now that we have created a context for *movielisterapp*, it's time to modify
the ``app.py`` script to use dependency injection. To demonstrate the use of
both an XML context and a pure-Python configuration, we'll create two different
"run" scripts.

The ``app_xmlcontext.py`` script will use the XML context::

    import sys
    
    from aglyph.assembler import Assembler
    from aglyph.context import XMLContext
    
    assembler = Assembler(XMLContext("movies-context.xml"))
    app = assembler.assemble("movies.lister.MovieLister")
    for movie in app.movies_directed_by("Sergio Leone"):
        sys.stdout.write("%s\n" % movie.title)

.. warning::

    *IronPython* developers will need to create a slightly different
    ``app_xmlcontext.py`` script::

        import sys
        
        from aglyph.assembler import Assembler
        from aglyph.compat.ipyetree import XmlReaderTreeBuilder
        from aglyph.context import XMLContext
        
        assembler = Assembler(XMLContext("movies-context.xml",
                                         parser=XmlReaderTreeBuilder()))
        app = assembler.assemble("movies.lister.MovieLister")
        for movie in app.movies_directed_by("Sergio Leone"):
            sys.stdout.write("%s\n" % movie.title)

    This is necessary because of the way that *IronPython* treats Unicode
    strings. See :mod:`aglyph.compat.ipyetree` for details.

This script creates an assembler with a context that is read from the
*movies-conext.xml* XML document. Notice that we no longer need to create the
``CSVMovieFinder`` class directly; we have effectively separated the
configuration of ``MovieLister`` from its use in the application.

Running the application produces the same results as usual::

    $ python app_xmlcontext.py 
    The Colossus of Rhodes
    Once Upon a Time in the West
    Once Upon a Time in America

The ``app_binder.py`` script will use the pure-Python configuration::

    import sys
    
    from movies import MoviesBinder
    from movies.lister import MovieLister

    binder = MoviesBinder()
    lister = binder.lookup(MovieLister)
    for movie in lister.movies_directed_by("Sergio Leone"):
        sys.stdout.write("%s\n" % movie.title)

Here, we create the binder and then use it to look up the concrete
implementation of ``MovieLister`` that we have configured.

Again, running the application produces the expected results::

    $ python app_binder.py 
    The Colossus of Rhodes
    Once Upon a Time in the West
    Once Upon a Time in America

5. Make changes to the *movielisterapp* application
---------------------------------------------------

Now that the application is configured to use Aglyph for dependency injection,
let's make some changes to demonstrate application maintenance under Aglyph.

First, we note that both the ``ColonDelimitedMovieFinder`` and
``CSVMovieFinder`` classes read and parse their respective data files on every
initialization. We don't expect the data files to change very often, at least
not during application runtime, so we'd prefer to only create either of these
objects *once*. (For the moment, preted that *movielisterapp* is a useful
application in which ``MovieFinder`` objects are used by more than just a
``MovieLister`` ;))

To accomplish this goal, we'll modify the XML context so that the
*movies.finder.ColonDelimitedMovieFinder* and *csv-finder* components use the
**singleton** assembly strategy.

Recall that singleton assembly means only
*one* object is created by Aglyph, and then cached. Subsequent assembly
requests for the same component will return the cached object.

Also, we'll change the *movies.lister.MovieLister* component so that it uses
the original ``ColonDelimitedMovieFinder`` class instead of ``CSVMovieFinder``.

The modified XML context looks like this::

    <?xml version="1.0" encoding="utf-8"?>
    <context id="movies-context">
        <component id="movies.finder.ColonDelimitedMovieFinder"
                strategy="singleton">
            <init>
                <arg><str>movies.txt</str></arg>
            </init>
        </component>
        <component id="csv-finder" dotted-name="movies.finder.CSVMovieFinder"
                strategy="singleton">
            <init>
                <arg><str>movies.csv</str></arg>
            </init>
        </component>
        <component id="movies.lister.MovieLister">
            <init>
                <arg reference="movies.finder.ColonDelimitedMovieFinder"/>
            </init>
        </component>
    </context>

Running the application still produces the expected results::

    $ python app_xmlcontext.py 
    The Colossus of Rhodes
    Once Upon a Time in the West
    Once Upon a Time in America

To make the same change using the pure-Python configuration, the
``MoviesBinder`` configuration class would be changed like so::

    from aglyph.binder import Binder

    from movies.lister import MovieLister
    from movies.finder import MovieFinder, ColonDelimitedMovieFinder


    class MoviesBinder(Binder):

        def __init__(self):
            super(MoviesBinder, self).__init__("movies-binder")
            self.bind(MovieLister).init(MovieFinder)
            self.bind(MovieFinder, to=ColonDelimitedMovieFinder,
                      strategy="singleton").init("movies.txt")

Finally, running the application one last time produces the expected results::

    $ python app_binder.py 
    Once Upon a Time in the West
    Once Upon a Time in America

.. note::

    The key point of this final exercise is that we were able to make
    "significant" changes without having to modify the application code itself.
    This is possible because we have *separated the configuration of objects
    from their use*; this is the goal of Depdendency Injection.

6. Suggested next steps
-----------------------

The final modified version of the *movielisterapp* application can be
downloaded :download:`here <../../resources/movielisterapp-aglyph.zip>` as a
reference (or find it under the *example/* directory if you cloned the `Aglyph
Mercurial repository from BitBucket <https://bitbucket.org/mzipay/aglyph>`_).

There are many more context/configuration options available in Aglyph beyond
those that have been presented in this tutorial, including support for type 2
"setter" injection using member variables, setter methods, and properties
(which can also be combined with the type 3 "constructor" injection used in
the *movielisterapp* sample application).

Suggested next steps:

#. Read the :doc:`api-ref`.
#. Read the :download:`aglyph-context-1.0.0 DTD
   <../../resources/aglyph-context-1.0.0.dtd>`. The DTD is fully commented, and
   explains some of the finer points of using XML configuration.
#. Read the :doc:`cookbook`.
#. Examine the Aglyph test cases (part of the distribution; located in the
   *tests/* directory).
#. Start with either the :download:`movielisterapp-basic
   <../../resources/movielisterapp-basic.zip>` or
   :download:`movielisterapp-aglyph
   <../../resources/movielisterapp-aglyph.zip>` applications and make your own
   modifications to explore the features of Aglyph.
