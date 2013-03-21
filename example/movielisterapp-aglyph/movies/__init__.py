from aglyph.binder import Binder
from aglyph.component import Component, Reference, Strategy
from aglyph.context import Context

from movies.lister import MovieLister
from movies.finder import MovieFinder, ColonDelimitedMovieFinder


class MoviesBinder(Binder):

    def __init__(self):
        super(MoviesBinder, self).__init__("movies-binder")
        self.bind(MovieLister).init(MovieFinder)
        self.bind(MovieFinder, to=ColonDelimitedMovieFinder,
                  strategy="singleton").init("movies.txt")


# provided as a reference; compare to MoviesBinder above
class MoviesContext(Context):

    def __init__(self):
        super(MoviesContext, self).__init__("movies-context")

        colon_finder = Component("movies.finder.ColonDelimitedMovieFinder",
                                 strategy=Strategy.SINGLETON)
        colon_finder.init_args.append("movies.txt")
        self.add(colon_finder)

        csv_finder = Component("csv-finder", "movies.finder.CSVMovieFinder",
                               Strategy.SINGLETON)
        csv_finder.init_args.append("movies.csv")
        self.add(csv_finder)

        lister = Component("movies.lister.MovieLister")
        lister.init_args.append(Reference(csv_finder.component_id))
        self.add(lister)

