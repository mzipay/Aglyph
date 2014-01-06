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
        self.bind(MovieLister).init(MovieFinder)

