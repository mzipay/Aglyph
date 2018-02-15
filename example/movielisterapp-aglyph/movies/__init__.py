from movies.finder import MovieFinder, SQLMovieFinder
from movies.lister import MovieLister

from aglyph.component import Reference as ref
from aglyph.context import Context


context = Context("movies-context")

(context.singleton("delim-finder").
    create("movies.finder.ColonDelimitedMovieFinder").
    init("movies.txt").
    register())

# makes SQLMovieFinder the default impl bound to "movies.finder.MovieFinder"
(context.borg(MovieFinder).
    create(SQLMovieFinder).
    init("movies.db").
    register())

# will initialize MovieLister with an object of SQLMovieFinder
context.prototype(MovieLister).init(ref(MovieFinder)).register()

