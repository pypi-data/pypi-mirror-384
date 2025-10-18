import logging
import rdflib

log = logging.getLogger(__name__)

class URICanonicalizer:
    def __init__(self, datasets=True):
        self.use_reasoner = False
        self.datasets = datasets
        self.canonical_uris = dict()
        self.alternate_uris = dict()

    def canonicalURI(self, uri):
        uri = rdflib.URIRef(uri)
        return self.canonical_uris.get(uri, uri)

    def alternateURI(self, uri):
        uri = rdflib.URIRef(uri)
        return self.alternate_uris.get(uri, None)

    def setCanonicalURI(self, canonical_uri, alternate_uri):
        c = rdflib.URIRef(canonical_uri)
        a = rdflib.URIRef(alternate_uri)
        self.canonical_uris[a] = c
        self.alternate_uris[c] = a

    QU_URI_FIX_MULTI = """
        DELETE { GRAPH ?g { $alternate_uri ?p ?o } }
        INSERT { GRAPH ?g { $canonical_uri ?p ?o } }
        WHERE  { GRAPH ?g { $alternate_uri ?p ?o } };
        DELETE { GRAPH ?g { ?s ?p $alternate_uri } }
        INSERT { GRAPH ?g { ?s ?p $canonical_uri } }
        WHERE  { GRAPH ?g { ?s ?p $alternate_uri } }
    """

    QU_URI_FIX_SINGLE = """
        DELETE { $alternate_uri ?p ?o }
        INSERT { $canonical_uri ?p ?o }
        WHERE  { $alternate_uri ?p ?o };
        DELETE { ?s ?p $alternate_uri }
        INSERT { ?s ?p $canonical_uri }
        WHERE  { ?s ?p $alternate_uri }
    """

    def canonicalizeURI(self, graph, canonical_uri, alternate_uri):
        log.debug("Adjusting: " + str(alternate_uri) + " --> " + str(canonical_uri))
        graph.update(self.QU_URI_FIX_MULTI if self.datasets else self.QU_URI_FIX_SINGLE,
                     canonical_uri=canonical_uri, alternate_uri=alternate_uri)
