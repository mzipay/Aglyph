import sys

from movies.lister import MovieLister

app = MovieLister()
for movie in app.movies_directed_by("Sergio Leone"):
    sys.stdout.write("%s\n" % movie.title)

