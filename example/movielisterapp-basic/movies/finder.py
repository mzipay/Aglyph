from movies.movie import Movie


class MovieFinder(object):

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

