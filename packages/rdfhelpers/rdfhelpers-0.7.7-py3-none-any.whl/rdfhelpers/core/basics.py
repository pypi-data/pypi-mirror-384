# Copyright (c) 2022, Ora Lassila & So Many Aircraft
# All rights reserved.
#
# See LICENSE for licensing information
#
# This module implements some useful functionality for programming with RDFLib.
#

from rdflib import URIRef, BNode, Graph, RDF
from rdflib.paths import ZeroOrMore
from rdfhelpers.core.templated import graphFrom
from rdfhelpers.core.cbd import cbd
import re
# from warnings import deprecated

# GLOSSARY
#
# This code uses certain terms or words in specific meanings:
# - "container" -- a composite object, an instance of any of the subclasses of rdfs:Container.
# - "context" -- something implemented as a named graph in the back-end.

# HELPFUL STUFF

# @deprecated("Use rdflib.NamespaceManager.expand_curie instead")
def expandQName(prefix, local_name, ns_mgr):
    ns = ns_mgr.store.namespace(prefix)
    if ns is not None:
        return str(ns) + local_name
    else:
        raise KeyError("Namespace prefix {} is not bound".format(prefix))

def URI(u):
    return u if isinstance(u, URIRef) or u is None else URIRef(u)

def ntriples(graph, destination=None):
    result = graph.serialize(destination=destination, format="nt", encoding="utf-8")
    return result.decode("utf-8") if destination is None else None

# Helpful graph accessors

def getvalue(graph, node, predicate):
    return next(graph.objects(node, predicate), None)

def setvalue(graph, node, predicate, value):
    graph.remove((node, predicate, None))
    if value is not None:
        graph.add((node, predicate, value))

def addvalues(graph, node, predicates_and_values: dict):
    for predicate, value in predicates_and_values.items():
        graph.add((node, predicate, value))

def setvalues(graph, node, predicates_and_values: dict):
    for predicate, value in predicates_and_values.items():
        setvalue(graph, node, predicate, value)

def diff(graph1, graph2):
    return graph1 - graph2, graph2 - graph1

# CONTAINERS

LI_MATCH_PATTERN = re.compile(str(RDF) + "_([0-9]+)")
LI_CREATE_PATTERN = str(RDF) + "_{0}"

def isContainerItemPredicate(uri):
    match = LI_MATCH_PATTERN.match(uri)
    return int(match.group(1)) if match else None

def makeContainerItemPredicate(index):
    return LI_CREATE_PATTERN.format(index)

def getContainerStatements(graph, source, predicate):
    containers = list(graph.objects(URI(source), predicate))
    n = len(containers)
    if n == 1:
        return sorted([statement for statement in graph.triples((containers[0], None, None))
                       if isContainerItemPredicate(statement[1])],
                      key=lambda tr: tr[1])
    elif n == 0:
        return None
    else:
        raise ValueError("Expected only one value for {0}".format(predicate))

def getContainerItems(graph, node, predicate):
    statements = getContainerStatements(graph, node, predicate)
    return [statement[2] for statement in statements] if statements else None

def setContainerItems(graph, node, predicate, values, newtype=RDF.Seq):
    # Having to write code like this is a clear indication that triples are the wrong
    # abstraction for graphs, way too low level. Just sayin'.
    if values:
        statements = getContainerStatements(graph, node, predicate)
        if statements:
            container = statements[0][0]
            for statement in statements:
                graph.remove(statement)
        else:
            container = BNode()
            graph.add((node, predicate, container))
            graph.add((container, RDF.type, newtype))
        i = 1
        for value in values:
            graph.add((container, URIRef(makeContainerItemPredicate(i)), value))
            i += 1
    else:
        container = getvalue(graph, node, predicate)
        if container:
            graph.remove((node, predicate, container))
            graph.remove((container, None, None))

def getCollectionItems(graph, collection):
    return graph.objects(collection, (RDF.rest*ZeroOrMore)/RDF.first)

def makeCollection(graph, items):
    if items:
        head = BNode()
        prev = None
        current = head
        for item in items:
            if prev:
                graph.add((prev, RDF.rest, current))
            graph.add((current, RDF.first, item))
            prev = current
            current = BNode()
        graph.add((prev, RDF.rest, RDF.nil))
        return head
    else:
        return None

# FOCUSED GRAPH
#
# Instances of FocusedGraph have a specified "focus node".

class FocusedGraph(Graph):
    def __init__(self, focus=None, source=None, focus_class=None, **kwargs):
        super().__init__(**kwargs)
        if source:
            if isinstance(source, str):
                self.parse(source)
            elif isinstance(source, list):
                graphFrom(source, self)
            else:
                raise TypeError("Cannot use {} as a graph source".format(source))
        self._focus = focus or self.findFocus(focus_class=focus_class, **kwargs)

    @property
    def focus(self):
        return self._focus

    def findFocus(self, focus_class=None, **kwargs):
        if focus_class:
            focus = next(self.triples((None, RDF.type, focus_class)), None)
            if focus:
                return focus[0]
        raise ValueError("No focus found")

    def getvalue(self, predicate):
        return getvalue(self, self._focus, predicate)

    def setvalue(self, predicate, value):
        setvalue(self, self._focus, predicate, value)

# CBD GRAPH

class CBDGraph(FocusedGraph):
    def __init__(self, focus, data, context=None, **kwargs):
        super().__init__(focus=focus, **kwargs)
        self.data = data
        self.context = context
        cbd(data, focus, target=self, context=context)

    def diff(self):
        context = self.context
        return diff(self, cbd(self, None, self.focus, context))
