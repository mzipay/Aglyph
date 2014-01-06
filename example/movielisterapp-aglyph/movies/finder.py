import sqlite3

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

