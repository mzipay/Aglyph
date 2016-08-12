===========================
Getting started with Aglyph
===========================

:Release: |release|

During this brief tutorial, you will download and install Aglyph, build a
simple Python application based on the *MovieLister* component discussed in
`Inversion of Control Containers and the Dependency Injection pattern
<http://martinfowler.com/articles/injection.html>`_, then modify the
application to take advantage of Aglyph dependency injection. This process will
allow you understand the Dependency Injection pattern in general, as well as
the Aglyph approach to Dependency Injection.

This tutorial is a "whirlwind tour" of Aglyph that covers only the basics. Once
you have completed the steps, read the :doc:`cookbook` for additional
guidelines and examples. Also review the :doc:`api-ref` and the
:download:`Aglyph context DTD <../../resources/aglyph-context.dtd>` to
understand the details.

The tutorial assumes that you are familiar with Python development in general,
and that Python 2.7 or 3.3+ is already installed on your system:

* `Download Python <http://www.python.org/download/>`_
* Browse `Dive Into Python 2 <http://www.diveintopython.net/>`_ and/or
  `The Python 2 Tutorial <http://docs.python.org/2/tutorial/index.html>`_
* Browse `Dive Into Python 3 <http://www.diveintopython3.net/>`_ and/or
  `The Python 3 Tutorial <http://docs.python.org/3/tutorial/index.html>`_

.. note::
   It is recommended, but not required, that you read the `Inversion of
   Control Containers and the Dependency Injection pattern
   <http://martinfowler.com/articles/injection.html>`_ and `Python Dependency
   Injection [PDF] <http://www.aleax.it/yt_pydi.pdf>`_ articles before
   beginning this tutorial.

.. _download-and-install:

1. Download and install Aglyph
==============================

There are several options for downloading and installing Aglyph. Choose the
method that best suits your needs or preferences.

Download and install a source or built distribution from SourceSource
---------------------------------------------------------------------

If you use Windows, a source ZIP distribution and EXE and MSI installers are
available from the `Aglyph SourceForge project
<http://sourceforge.net/projects/aglyph/files/aglyph/>`_.

Run the EXE or MSI installer after downloading, or unpack the ZIP distribution
and run the following command from within the distribution directory::

   python setup.py install

Download and install a source distribution from PyPI
----------------------------------------------------

The Aglyph source distribution can be downloaded from the
`Aglyph Python Package Index page <https://pypi.python.org/pypi/Aglyph>`_.

Unpack the archive and run the following command from with the distribution
directory::

   python setup.py install

Clone the Aglyph repository from GitHub
---------------------------------------

To install the latest release from a clone of the `Aglyph repository
<https://github.com/mzipay/Aglyph>`_, execute the following commands from a
shell::

   git clone https://github.com/mzipay/Aglyph.git
   cd Aglyph
   python setup.py install

Install into a virtual environment
----------------------------------

You can also create a `virtualenv <http://www.virtualenv.org/>`_ (details not
covered here) and install Aglyph into it by running the following commands from
a shell (assumes the virtual environment is active)::

   pip install Aglyph

Regardless of installation method, verify that the installation was successful
by importing the :mod:`aglyph` module from a Python interpreter. For example::

   $ python
   Python 3.5.2 (default, Jun 27 2016, 16:22:09)
   [GCC 4.2.1 Compatible Apple LLVM 7.0.2 (clang-700.1.81)] on darwin
   Type "help", "copyright", "credits" or "license" for more information.
   >>> import aglyph
   >>> aglyph.__version__
   '2.1.1'

2. Download, extract, and run the *movielisterapp* application
==============================================================

The sample code for this tutorial can be downloaded
:download:`here (movielisterapp-basic.zip)
<../../resources/movielisterapp-basic.zip>`. If you don't feel like typing
everything out by hand and would prefer to just "follow along," you can also
download :download:`movielisterapp-aglyph.zip
<../../resources/movielisterapp-aglyph.zip>`, which contains the completed
tutorial source code (including the already-populated SQLite database).

.. note::
   Both ZIP files are also available under the *examples/* directory if you
   cloned the `Aglyph repository <https://github.com/mzipay/Aglyph>`_.

.. warning::
   Jython users will not be able to run the tutorial code because the standard
   Python :mod:`sqlite3` module (which Jython does not support) is used by the
   example code.

To begin the tutorial, extract the ZIP archive to a temporary location and
navigate into the application directory::

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
*movies/finder.py* module::

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
object. The *movies/movie.py* module holds the ``Movie`` class definition::

   class Movie:
   
       def __init__(self, title, director):
           self.title = title
           self.director = director

Finally, we have a ``MovieLister`` class (defined in the *movies/lister.py*
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

The application can be executed using the *app.py* script, which simply asks
a ``MovieLister`` for all movies directed by Sergio Leone::

   $ python app.py 
   The Colossus of Rhodes
   Once Upon a Time in the West
   Once Upon a Time in America

.. _intro-to-di:

3. A *(very)* brief introduction to Dependency Injection
========================================================

Examine the ``MovieLister`` class (in the *movies/lister.py* module) again.
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

.. _app-changes-to-support-di:

4. Make some general improvements to the *movielisterapp* application
=====================================================================

As written, the basic application is somewhat change-resistant. For example, if
we wish to support another implementation of ``MovieFinder`` (e.g. one that
connects to a database to retrieve movie information), then we would also need
to change the ``MovieLister`` implementation.

A simple solution to this problem is to change ``MovieLister`` so that it can
*accept* a ``MovieFinder`` at initialization time::

   class MovieLister:
   
       def __init__(self, finder):
           self._finder = finder
   
       def movies_directed_by(self, director):
           for movie in self._finder.find_all():
               if (movie.director == director):
                   yield movie

Next, we'll add a ``SQLMovieFinder`` class definition to the
*movies/finder.py* module. This new implementation will use the standard
Python :mod:`sqlite3` module to connect to a SQLite database which stores the
movies information::

   import sqlite3
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
   
   
   class SQLMovieFinder(MovieFinder):
   
       def __init__(self, dbname):
           self._db = sqlite3.connect(dbname)
   
       def find_all(self):
           cursor = self._db.cursor()
           movies = []
           try:
               for row in cursor.execute("select title, director from Movies"):
                   (title, director) = row
                   movies.append(Movie(title, director))
           finally:
               cursor.close()
           return movies
   
       def __del__(self):
           try:
               self._db.close()
           except:
               pass

The ``SQLVMovieFinder`` expects a database name (a filename, or *":memory:"*
for an in-memory database). We'll create a *movies.db* file so that it contains
the same records as the original *movies.txt* file:

>>> import sqlite3
>>> conn = sqlite3.connect("movies.db")
>>> c = conn.cursor()
>>> c.execute("create table Movies (title text, director text)")
>>> for movie_fields in [("The Colossus of Rhodes", "Sergio Leone"),
...                      ("Once Upon a Time in the West", "Sergio Leone"),
...                      ("THX 1138", "George Lucas"),
...                      ("American Graffiti", "George Lucas"),
...                      ("Once Upon a Time in America", "Sergio Leone"),
...                      ("Sixteen Candles", "John Hughes"),
...                      ("The Breakfast Club", "John Hughes"),
...                      ("Weird Science", "John Hughes"),
...                      ("Ferris Bueller's Day Off", "John Hughes")]:
>>>     c.execute("insert into Movies values (?, ?)", movie_fields)
... 
>>> c.close()
>>> conn.commit()
>>> conn.close()

Finally, we'll change *app.py* so that the new ``SQLMovieFinder`` is used to
initialize a ``MovieLister``::

   import sys
   
   from movies.finder import SQLMovieFinder
   from movies.lister import MovieLister
   
   lister = MovieLister(SQLMovieFinder("movies.db"))
   for movie in lister.movies_directed_by("Sergio Leone"):
       sys.stdout.write("%s\n" % movie.title)

Running the application again should give us the same results::

   $ python app.py 
   The Colossus of Rhodes
   Once Upon a Time in the West
   Once Upon a Time in America

The basic application is now more flexible: we can change the ``MovieFinder``
implementation without having to modify the ``MovieLister`` class definition.
However, we are still required to modify *app.py* if we decide to change the
``MovieFinder`` implementation!

.. note::
   An important aspect of Aglyph is that it is **non-intrusive**, meaning that
   it requires only minimal changes to your existing application code in order
   to provide dependency injection capabilities.

   Notice that the changes made in this section, while adding flexibility to
   the application, did not require the use of Aglyph. In fact, as we add
   Aglyph dependency injection support in the next two sections, **no further
   changes** to the *movies/lister.py*, *movies/finder.py*, and
   *movies/movie.py* modules need to be made.

5. Add Dependency Injection support to the *movielisterapp* application
=======================================================================

Recall that Dependency Injection gives reponsibility for injecting dependencies
to an an external object (called an "assembler"). In Aglyph, this "assembler"
is an instance of the :class:`aglyph.assembler.Assembler` class.

An :class:`aglyph.assembler.Assembler` requires a "context," which is a
collection of component definitions. A *component*
(:class:`aglyph.component.Component`) is simply a description of some object,
including how it is created/acquired and its dependencies. Any component can
itself be a dependency of any other component(s).

In Aglyph, a context is defined by the :class:`aglyph.context.Context` class. A
specialized subclass, :class:`aglyph.context.XMLContext`, is provided to allow a
context to be defined declaratively in an XML document. Such XML documents
must conform to the :download:`Aglyph context DTD
<../../resources/aglyph-context.dtd>`.

.. versionadded:: 1.1.0
   The :class:`aglyph.binder.Binder` class offers a "programmatic
   configuration" option for Aglyph. Use an instance of this class to both
   define and assemble your application components.

In this section, we will create a declarative XML context **and** an Aglyph
binder for *movielisterapp*, in order to demonstrate each approach.

.. warning::
   In practice, you should choose **either** :class:`aglyph.context.XMLContext`
   or :class:`aglyph.binder.Binder` for configuring Aglyph.

First, we'll create the XML context document as *movies-context.xml*::

   <?xml version="1.0" encoding="utf-8"?>
   <context id="movies-context">
       <component id="delim-finder"
                  dotted-name="movies.finder.ColonDelimitedMovieFinder">
           <init>
               <arg><str>movies.txt</str></arg>
           </init>
       </component>
       <component id="movies.finder.MovieFinder"
                  dotted-name="movies.finder.SQLMovieFinder">
           <init>
               <arg><str>movies.db</str></arg>
           </init>
       </component>
       <component id="movies.lister.MovieLister">
           <init>
               <arg reference="movies.finder.MovieFinder" />
           </init>
       </component>
   </context>

Some interesting things to note here:

* A ``<context>`` requires an ``id`` attribute, which should uniquely identify
  the context.
* A ``<component>`` requires an ``id`` attribute, and has an optional
  ``dotted-name`` attribute. If ``dotted-name`` is not provided, then the
  ``id`` attribute is assumed to be a dotted name; otherwise, the ``id`` can
  be a user-defined identifier and the ``dotted-name`` **must** be provided
  (this is useful when describing multiple components of the same class, for
  example). A dotted name is a string that represents an **importable** module,
  class, or function.
* Initialization arguments are provided as ``<arg>`` child elements of a parent
  ``<init>`` element. An ``<arg>`` is a postional argument, while an
  ``<arg keyword="...">`` is a keyword argument. (As in Python, the order in
  which positional arguments are declared is significant, while the order of
  keyword arguments is not.)

.. note::
   A dotted name is a *"dotted_name.NAME"* or *"dotted_name"* string that
   represents a valid absolute import statement according to the following
   productions:

   .. productionlist::
      absolute_import_stmt: "from" dotted_name "import" NAME
                          : | "import" dotted_name
      dotted_name: NAME ('.' NAME)*

   .. seealso::
      `Full Grammar specification
      <http://docs.python.org/release/3/reference/grammar.html>`_

Notice that the *movies.lister.MovieLister* component is being injected with a
reference to the *movies.finder.MovieFinder* component, which describes an
instance of ``movies.finder.SQLMovieFinder``. We could easily change back to
using ``movies.finder.ColonDelimitedMovieFinder`` by changing the reference.

Next, we'll create an alternative, programmatic configuration as the
``MoviesBinder`` class (a subclass of :class:`aglyph.binder.Binder`) in the
*movies/__init__.py* module::

   from aglyph.binder import Binder
   
   from movies.lister import MovieLister
   from movies.finder import MovieFinder, SQLMovieFinder
   
   class MoviesBinder(Binder):
   
       def __init__(self):
           super(MoviesBinder, self).__init__("movies-binder")
           (self.bind("delim-finder",
                      to="movies.finder.ColonDelimitedMovieFinder").
               init("movies.txt"))
           self.bind(MovieFinder, to=SQLMovieFinder).init("movies.db")
           self.bind(MovieLister).init(MovieFinder)

There are several interesting things to note about ``MoviesBinder``:

* Because ``ColonDelimitedMovieFinder`` is bound using a custom ID that is
  *not* a dotted name ("delim-finder"), the ``to`` keyword argument is
  required, and **must** specify either the explicit dotted name or a reference
  to the class itself so that Aglyph knows how to import it.
* The ``MovieFinder`` abstract base class is bound to the ``SQLMovieFinder``
  implementation class using references to the classes themselves, which causes
  the binder to *automatically* determine the dotted names. In this case, the
  ID "movies.finder.MovieFinder" is bound to the dotted name
  "movies.finder.SQLMovieFinder".
* ``MovieLister`` isn't bound **to** anything. Why? Python does not support
  interfaces as a language construct (mixins and :mod:`abc` are the
  alternatives). So in this case, ``MovieLister`` actually serves as *both* the
  "interface" and the implementation. Duck-typing means that "anything that
  looks like a MovieLister and acts like a MovieLister" should be treated *as*
  a ``MovieLister``. We could just as easily create a specialized subclass
  (say, ``FancyMovieLister``) and then bind *it* to ``MovieLister`` using
  ``bind(MovieLister, to=FancyMovieLister)``.
* The :meth:`aglyph.binder.Binder.bind` method returns a proxy object that
  allows us to specify the initialization (constructor) dependencies. The
  dependencies must be specified according to the signature of the initializer.
  The ``MovieLister.__init__`` method accepts a single positional argument
  that must be a concrete ``MovieFinder``.
* Notice that when the positional argument for ``MovieLister.__init__`` is
  specified, a reference to the ``MovieFinder`` class is used. Because this
  argument is not a dotted name string, Aglyph will *automatically* determine
  the dotted name of the class ("movies.finder.MovieFinder") and turn it into
  an :class:`aglyph.component.Reference`. Since ``MovieFinder`` was bound to
  ``SQLMovieFinder``, this means that, at runtime, Aglyph will resolve the
  ``Reference("movies.finder.MovieFinder")`` to an instance of
  ``SQLMovieFiner``.

Take a minute to examine the XML context and the ``MoviesBinder`` class; they
produce *identical* configurations for Aglyph. Each will inject the string
*"movies.db"* into a ``SQLMovieFinder``, and then inject the ``SQLMovieFinder``
instance into a ``MovieLister``.

Now that we have created Aglyph configurations for *movielisterapp*, it's time
to modify the *app.py* script to use dependency injection. To demonstrate the
use of both types of configution, we'll create two different versions of the
application script.

.. note::
   As noted earlier, in practice you would choose **one** of the configuration
   options and set up your application entry point appropriately.

The *app_xml.py* script will use the declarative XML context::

   import sys
   from aglyph.assembler import Assembler
   from aglyph.context import XMLContext
   
   context = XMLContext("movies-context.xml")
   assembler = Assembler(context)
   
   lister = assembler.assemble("movies.lister.MovieLister")
   for movie in lister.movies_directed_by("Sergio Leone"):
       sys.stdout.write("%s\n" % movie.title)

This script creates an assembler with a context that is read from the
*movies-context.xml* XML document. Notice that we no longer need to create the
``SQLMovieFinder`` class directly; we have effectively separated the
configuration of ``MovieLister`` from its use in the application.

Running the application produces the same results as usual::

   $ python app_xml.py 
   The Colossus of Rhodes
   Once Upon a Time in the West
   Once Upon a Time in America

The *app_binder.py* script will use the ``MoviesBinder`` configuration::

   import sys
   from movies import MoviesBinder
   from movies.lister import MovieLister
   
   binder = MoviesBinder()
   
   lister = binder.lookup(MovieLister)
   for movie in lister.movies_directed_by("Sergio Leone"):
       sys.stdout.write("%s\n" % movie.title)

Here, we create the binder and then use it to look up the concrete
implementation of ``MovieLister`` that we have configured.

.. note::
   Like the :meth:`aglyph.binder.Binder.bind` method, the
   :meth:`aglyph.binder.Binder.lookup` method can accept a reference to a
   class, and will *automatically* determine the dotted name for that class.
   Because we bound the ID "movies.lister.MovieLister" to the ``MovieLister``
   class, ``binder.lookup(MovieLister)`` is equivalent to
   ``binder.lookup("movies.lister.MovieLister")``, and will produce an instance
   of ``MovieLister`` with its dependencies injected as we expect.

Again, running the application produces the expected results::

   $ python app_binder.py 
   The Colossus of Rhodes
   Once Upon a Time in the West
   Once Upon a Time in America

6. Make changes to the *movielisterapp* application
===================================================

Now that the application is configured to use Aglyph for dependency injection,
let's make some changes to demonstrate application maintenance under Aglyph.

.. note::
   The key point of this final exercise is that we will be able to make
   "significant" changes to the application without having to modify any of the
   application source code.
   This is possible because we have *separated the configuration of objects
   from their use*; this is the goal of Depdendency Injection.

Introducing assembly strategies
-------------------------------

In our existing configurations, all components are using Aglyph's default
assembly strategy, **prototype**, which means that each time a component is
assembled, a new object is created, initialized, wired, and returned.

This is not always desired (or appropriate), so Aglyph also supports
**singleton**, **borg**, and **weakref** assembly strategies.

For details of what each assembly strategy implies, please refer to
:obj:`aglyph.component.Strategy`.

.. seealso::

   `Singleton? We don't need no stinkin' singleton: the Borg design pattern (Python recipe) <http://code.activestate.com/recipes/66531-singleton-we-dont-need-no-stinkin-singleton-the-bo/>`_
      Alex Martelli's original Borg recipe (from ActiveState Python Recipes)

   Module :mod:`weakref`
      Documentation of the :mod:`weakref` standard module.

Modify *movielisterapp* to use a singleton ``ColonDelimitedMovieFinder``
------------------------------------------------------------------------

We note that ``ColonDelimitedMovieFinder`` class parses its data file on every
initialization. We don't expect the data file to change very often, at least
not during application runtime, so we'd prefer to only create an instance of
``ColonDelimitedMovieFinder`` *once*, regardless of how many times during the
application runtime that it is requested (i.e. assembled). For the sake of
demonstration, preted for a moment that *movielisterapp* is a useful
application in which ``MovieFinder`` objects are used by more than just a
``MovieLister`` ;)

To accomplish this goal, we'll modify our configurations so that the
*"delim-finder"* component uses the **singleton** assembly strategy.

Also, we'll change the *movies.lister.MovieLister* component so that it uses
the original ``ColonDelimitedMovieFinder`` instead of ``SQLMovieFinder``.

The modified XML context looks like this::

   <?xml version="1.0" encoding="utf-8"?>
   <context id="movies-context">
       <component id="delim-finder"
                  dotted-name="movies.finder.ColonDelimitedMovieFinder"
                  strategy="singleton">
           <init>
               <arg><str>movies.txt</str></arg>
           </init>
       </component>
       <component id="movies.finder.MovieFinder"
                  dotted-name="movies.finder.SQLMovieFinder">
           <init>
               <arg><str>movies.db</str></arg>
           </init>
       </component>
       <component id="movies.lister.MovieLister">
           <init>
               <arg reference="delim-finder" />
           </init>
       </component>
   </context>

We added ``strategy="singleton"`` to the *"delim-finder"* component, and
changed the ``MovieLister`` argument to specify ``reference="delim-finder"``.

The modifed *movies/__init__.py* module and ``MoviesBinder`` class look like
this (note the additional import of :class:`aglyph.component.Reference`)::

   from aglyph.binder import Binder
   from aglyph.component import Reference
   
   from movies.lister import MovieLister
   from movies.finder import MovieFinder, SQLMovieFinder
   
   
   class MoviesBinder(Binder):
   
       def __init__(self):
           super(MoviesBinder, self).__init__("movies-binder")
           (self.bind("delim-finder",
                      to="movies.finder.ColonDelimitedMovieFinder",
                      strategy="singleton").
               init("movies.txt"))
           (self.bind(MovieFinder, to=SQLMovieFinder, strategy="borg").
               init("movies.db"))
           self.bind(MovieLister).init(Reference("delim-finder"))

We added ``strategy="singleton"`` when binding the *"delim-finder"* component.
Also, because the component ID *"delim-finder"* is not a dotted name, we
need to manually specify that the ``MovieLister`` argument is an
:class:`aglyph.component.Reference` to *"delim-finder"*.

Running either version of the application still produces the expected results::

   The Colossus of Rhodes
   Once Upon a Time in the West
   Once Upon a Time in America

Modify *movielisterapp* again to use a borg ``SQLMovieFinder``
--------------------------------------------------------------

We also note that ``SQLMovieFinder`` doesn't really need to create a new
database connection every time it is assembled. We *could* use the singleton
assembly strategy, but instead we'll use a similar pattern called **borg**. Of
course, we'll also change the application to again use the ``SQLMovieFinder``.

The final modified XML context looks like this::

   <?xml version="1.0" encoding="utf-8"?>
   <context id="movies-context">
       <component id="delim-finder"
                  dotted-name="movies.finder.ColonDelimitedMovieFinder"
                  strategy="singleton">
           <init>
               <arg><str>movies.txt</str></arg>
           </init>
       </component>
       <component id="movies.finder.MovieFinder"
                  dotted-name="movies.finder.SQLMovieFinder"
                  strategy="borg">
           <init>
               <arg><str>movies.db</str></arg>
           </init>
       </component>
       <component id="movies.lister.MovieLister">
           <init>
               <arg reference="movies.finder.MovieFinder" />
           </init>
       </component>
   </context>

The final modifed ``MoviesBinder`` class looks like this::

   class MoviesBinder(Binder):
   
       def __init__(self):
           super(MoviesBinder, self).__init__("movies-binder")
           (self.bind("delim-finder",
                      to="movies.finder.ColonDelimitedMovieFinder",
                      strategy="singleton").
               init("movies.txt"))
           (self.bind(MovieFinder, to=SQLMovieFinder, strategy="borg").
               init("movies.db"))
           self.bind(MovieLister).init(MovieFinder)

Running either the *app_xml.py* or *app_binder.py* version of the application
with the final configuration changes still produces the expected results::

   The Colossus of Rhodes
   Once Upon a Time in the West
   Once Upon a Time in America

Suggested next steps
====================

There are many more context/configuration options available in Aglyph beyond
those that have been presented in this tutorial, including support for type 2
"setter" injection using member variables, setter methods, and properties
(which can also be combined with the type 3 "constructor" injection used in
the *movielisterapp* sample application).

Suggested next steps:

#. Read the :doc:`cookbook`.
#. Read the :doc:`api-ref`.
#. Read the :download:`Aglyph context DTD
   <../../resources/aglyph-context.dtd>`. The DTD is fully commented, and
   explains some of the finer points of using XML configuration.
#. Examine the Aglyph test cases (part of the distribution; located in the
   *tests/* directory).
#. Start with either the :download:`movielisterapp-basic
   <../../resources/movielisterapp-basic.zip>` or
   :download:`movielisterapp-aglyph
   <../../resources/movielisterapp-aglyph.zip>` applications and make your own
   modifications to explore the features of Aglyph.

