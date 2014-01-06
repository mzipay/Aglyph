import sys

from aglyph.assembler import Assembler
from aglyph.context import XMLContext

context = XMLContext("movies-context.xml")
assembler = Assembler(context)

lister = assembler.assemble("movies.lister.MovieLister")
for movie in lister.movies_directed_by("Sergio Leone"):
    sys.stdout.write("%s\n" % movie.title)

