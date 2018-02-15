import sys

from aglyph.assembler import Assembler
from movies import context

assembler = Assembler(context)

lister = assembler.assemble("movies.lister.MovieLister")
for movie in lister.movies_directed_by("Sergio Leone"):
    sys.stdout.write("%s\n" % movie.title)

