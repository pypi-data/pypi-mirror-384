# Copyright (c) 2022, Ora Lassila & So Many Aircraft
# All rights reserved.
#
# See LICENSE for licensing information
#
# This module implements some useful functionality for programming with RDFLib.
#

import collections
import itertools
import re
import logging
from rdflib import URIRef, Literal
from rdfhelpers.core.templated import Templated

GENERIC_PREFIX_MATCHER = re.compile("ns[0-9]+")

def abbreviate(uri, namespace_manager):
    try:
        prefix, _, name = namespace_manager.compute_qname(uri)
        if GENERIC_PREFIX_MATCHER.match(prefix):
            return str(uri)
        else:
            return "{}:{}".format(prefix, name)
    except ValueError:
        return str(uri)
    except UnboundLocalError as e:
        # TODO: fix this, somehow...
        logging.error("This is probably an error in rdflib: {}".format(e))
        return str(uri)

# LABEL CACHING
#
# Cache the values of rdfs:label (and sub-properties thereof) for faster access. Select
# either all vertices with a label (the default) or customize vertex selection.
class LabelCache:
    def __init__(self, db, label_query=None, selector=None, language="en", prepopulate=False):
        self.db = db
        self.label_query = label_query or self.LABELQUERY
        self.selector = selector
        self.language = language
        self._labels = dict()
        self._search_index = collections.defaultdict(set)
        if prepopulate:
            self.repopulate()

    LABELQUERY = '''
        SELECT ?r ?label {
            ?label_prop rdfs:subPropertyOf* rdfs:label .
            $selector
            $resource ?label_prop ?real_label
            BIND ($resource AS ?r)
            OPTIONAL { ?r skos:prefLabel ?pref_label }
            BIND (COALESCE(?pref_label, ?real_label) AS ?candidate_label)
            ?candidate_label rdf:_1? ?label
            FILTER (!isblank(?label))
            FILTER ((str(lang(?label)) = "") || langMatches(lang(?label), "$language") || langMatches(lang(?label), "x-default"))
        }
        $limit
    '''

    ALLLABELSQUERY = '''
        SELECT DISTINCT ?label {
            {
                $resource skos:prefLabel|skos:altLabel|dc:title ?label
            }
            UNION
            {
                ?p rdfs:subPropertyOf* rdfs:label .
                $resource ?p ?label
            }
            BIND (IF(langMatches(lang(?label), "$language"), 0, 1) AS ?priority)
        }
        ORDER BY ?priority
    '''

    def getLabel(self, resource):
        if not isinstance(resource, URIRef):
            resource = URIRef(resource)
        label = self._labels.get(resource, None)
        if label:
            return label
        else:
            label = None
            for _, lb in Templated.query(self.db, self.label_query,
                                         resource=resource, selector=self.selector, limit="LIMIT 1",
                                         language=self.language):
                label = lb
                self.updateSearchIndex(resource, label)
                break
            if label is None:
                label = self.makeQName(resource)
            if label is not None:
                self._labels[resource] = label
            return label or str(resource)

    def invalidateLabel(self, resource):
        self._labels[resource if isinstance(resource, URIRef) else URIRef(resource)] = None

    def repopulate(self):
        self._labels = {resource: label for resource, label
                        in Templated.query(self.db, self.label_query,
                                           resource="?res", selector=self.selector, limit=None,
                                           language=self.language)}
        self._search_index = collections.defaultdict(set)
        for resource, label in self._labels.items():
            self.updateSearchIndex(resource, label)

    def updateSearchIndex(self, resource, label):
        if label:
            for p in itertools.pairwise(label.upper()):
                self._search_index[p[0]+p[1]].add(resource)

    def findResources(self, substring):
        search_string = substring.upper()
        if len(substring) < 2:
            raise ValueError("Search string too short")
        if len(substring) == 2:
            return self._search_index[search_string]
        else:
            return [resource for resource in self.findResources(search_string[0:2])
                    if str(self.getLabel(resource)).upper().find(search_string) >= 0]

    def findResourcesForAutocomplete(self, substring):
        # this value can be "JSONified" (e.g., flask.json.jsonify)
        return [{"value": resource, "label": self.getLabel(resource)} for resource
                in self.findResources(substring)]

    def getAllLabels(self, resource, exclude_default_namespace=True):
        if not isinstance(resource, URIRef):
            resource = URIRef(resource)
        labels = [label for label, in Templated.query(self.db, self.ALLLABELSQUERY,
                                                      resource=resource, language=self.language)]
        qname = self.makeQName(resource)
        if qname == str(resource):
            return labels + [qname]
        elif exclude_default_namespace and qname.startswith(':'):
            return labels + [str(resource)]
        else:
            return labels + [qname, str(resource)]

    def makeQName(self, uri):
        return abbreviate(uri, self.db.namespace_manager)

# SKOS CONCEPT LABEL CACHING
#
# Similar to regular label caching, but the default selection of vertices includes only the
# concepts of a specified concept scheme. Also provides a mapping from labels to concepts.
class SKOSLabelCache(LabelCache):
    def __init__(self, db, scheme, selector=None):
        self._concepts = dict()
        selector = Templated.convert(selector or "?res skos:broader*/^skos:hasTopConcept $scheme .",
                                     {"scheme": scheme})
        super().__init__(db, selector=selector)

    def invalidateLabel(self, resource):
        label = self.getLabel(resource)
        super().invalidateLabel(resource)
        self._concepts[label] = None

    def updateSearchIndex(self, resource, label):
        super().updateSearchIndex(resource, label)
        self._concepts[label] = resource

    def repopulate(self):
        self._concepts = dict()
        super().repopulate()

    def getConcept(self, label):
        return self._concepts.get(label if isinstance(label, Literal) else Literal(label), None)

    def listConcepts(self):
        return self._labels.keys()

#

class BNodeMarker:
    def __init__(self, bnode, i):
        self.bnode = bnode
        self.i = i

    def __lt__(self, other):
        return self.i < other.i

    def __gt__(self, other):
        return self.i > other.i

class BNodeTracker:
    def __init__(self, marker_class=BNodeMarker):
        self.bnodes = dict()
        self.index = 0
        self.marker_class = marker_class

    def get(self, bnode):
        marker = self.bnodes.get(bnode, None)
        if marker is None:
            marker = self.marker_class(bnode, self.index)
            self.index += 1
            self.bnodes[bnode] = marker
        return marker

    def seen(self, bnode):
        return self.bnodes.get(bnode, False) and True
