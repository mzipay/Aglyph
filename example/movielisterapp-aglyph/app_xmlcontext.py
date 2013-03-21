import sys

from aglyph.assembler import Assembler
from aglyph.context import XMLContext

assembler = Assembler(XMLContext("movies-context.xml"))
app = assembler.assemble("movies.lister.MovieLister")
for movie in app.movies_directed_by("Sergio Leone"):
    sys.stdout.write("%s\n" % movie.title)

