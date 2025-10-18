# Copyright (c) 2022, Ora Lassila & So Many Aircraft
# All rights reserved.
#
# See LICENSE for licensing information
#
# This module implements some useful functionality for programming with RDFLib.
#

from rdflib import URIRef, BNode, Graph
from rdflib.namespace import NamespaceManager
from rdflib.term import Node, Variable
from rdflib.plugins.sparql.parser import ConstructTriples
from rdflib.plugins.sparql.parserutils import CompValue
from rdfhelpers.core.basics import expandQName

def parseConstructTriples(template):
    # This is ugly, and perhaps there is a more sane way of doing this, but for now, parsing the
    # SPARQL CONSTRUCT clause triple patterns results in a list the single element of which is an
    # object (a ParamValue) that has a list of tokens (unresolved RDF terms).
    # x = ConstructTriples.parseString(template).as_list()
    tokens = []
    for tks in ConstructTriples.parseString(template).as_list():
        tokens += tks.tokenList.as_list()
    return tokens

class Constructor:
    def __init__(self, template, ns_mgr=None, namespaces=None):
        self.ns_mgr = ns_mgr or self.makeNamespaceManager()
        if namespaces:
            if isinstance(namespaces, dict):
                nss = namespaces.items()
            elif isinstance(namespaces, Graph):
                nss = namespaces.namespace_manager.namespaces()
            elif isinstance(namespaces, NamespaceManager):
                nss = namespaces.namespaces()
            else:
                raise ValueError("Illegal value for namespaces: {}".format(namespaces))
            for prefix, namespace in nss:
                self.bind(prefix, namespace)
        self.template = self.parseTemplate(template, ns_mgr=self.ns_mgr)

    @classmethod
    def makeNamespaceManager(cls):
        return NamespaceManager(Graph())

    def bind(self, prefix, namespace, override=True, replace=False):
        self.ns_mgr.bind(prefix, namespace, override=override, replace=replace)

    def resolveTerm(self, item, ns_mgr=None):
        if isinstance(item, Node):
            return item
        elif isinstance(item, CompValue):
            if item.name == "pname":
                return URIRef(expandQName(item['prefix'], item['localname'], ns_mgr or self.ns_mgr))
            elif item.name == "literal":
                return item['string']
        raise ValueError("Unrecognized token {}".format(str(item)))

    def parseTemplate(self, template, ns_mgr=None):
        tokens = [self.resolveTerm(t, ns_mgr=ns_mgr) for t in parseConstructTriples(template)]
        return [tuple(tokens[i:i + 3]) for i in range(0, len(tokens), 3)]

    @staticmethod
    def expandTerm(term, bindings: dict, bnodes: dict):
        if isinstance(term, Variable):
            value = bindings.get(str(term), None)
        elif isinstance(term, BNode):
            value = bnodes.get(term, None)
            if value is None:
                value = BNode()
                bnodes[term] = value
        else:
            value = term
        if value is None:
            return []
        elif isinstance(value, list):
            return value
        else:
            return [value]

    def expandTemplate(self, template, bindings: dict):
        bnodes = dict()
        for s, p, o in template:
            for ss in self.expandTerm(s, bindings, bnodes):
                for pp in self.expandTerm(p, bindings, bnodes):
                    for oo in self.expandTerm(o, bindings, bnodes):
                        yield ss, pp, oo

    def expand(self, **bindings):
        return self.expandTemplate(self.template, bindings)
