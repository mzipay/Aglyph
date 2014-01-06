class MovieLister(object):

    def __init__(self, finder):
        self._finder = finder

    def movies_directed_by(self, director):
        for movie in self._finder.find_all():
            if (movie.director == director):
                yield movie

