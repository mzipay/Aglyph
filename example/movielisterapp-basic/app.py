import sys

from movies.lister import MovieLister

lister = MovieLister()
for movie in lister.movies_directed_by("Sergio Leone"):
    sys.stdout.write("%s\n" % movie.title)

