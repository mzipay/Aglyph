import sys

from movies import MoviesBinder
from movies.lister import MovieLister

binder = MoviesBinder()

lister = binder.lookup(MovieLister)
for movie in lister.movies_directed_by("Sergio Leone"):
    sys.stdout.write("%s\n" % movie.title)

