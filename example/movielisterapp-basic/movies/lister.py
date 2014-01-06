from movies.finder import ColonDelimitedMovieFinder


class MovieLister(object):

    def __init__(self):
        self._finder = ColonDelimitedMovieFinder("movies.txt")

    def movies_directed_by(self, director):
        for movie in self._finder.find_all():
            if (movie.director == director):
                yield movie

