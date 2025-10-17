from rdflib import Graph
from solidipes.loaders.file import File


class RDF(File):
    supported_mime_types = {"text/plain": ["rdf", "ttl"]}

    from ..viewers.rdf import RDF as RDFViewer

    _compatible_viewers = [RDFViewer]

    @File.loadable
    def rdf(self):
        g = Graph()
        g.parse(self.file_info.path)
        return g
