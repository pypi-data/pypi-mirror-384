# Copyright (c) 2022-2025, Ora Lassila & So Many Aircraft
# All rights reserved.
#
# See LICENSE for licensing information
#
# This module implements a composable RDF processing mechanism.
#
import logging
from typing import Any
import rdflib
from rdfhelpers.core.templated import graphFrom, Templated

try:
    import pyshacl
    SHACL = True
except ModuleNotFoundError:
    pyshacl = None
    SHACL = False

try:
    import tinyrml
    TINYRML = True
except ModuleNotFoundError:
    tinyrml = None
    TINYRML = False

class Composable:
    def __init__(self, contents=None):
        # Copy the graph from the Composable that was passed
        if isinstance(contents, Composable):
            self._graph = contents._graph
        # A graph was passed, use that one
        elif isinstance(contents, rdflib.Graph):
            self._graph = contents
        # An iterable was passed, let's assume it is an iterable of triples
        elif hasattr(contents, "__iter__"):
            self._graph = graphFrom(contents) or rdflib.Graph()
        # Create an empty graph
        elif contents is None:
            self._graph = rdflib.Graph()
        else:
            raise ValueError("Illegal contents: {}".format(contents))

    @property
    def result(self) -> rdflib.Graph:
        return self._graph

    def __len__(self) -> int:
        return len(self._graph)

    def __add__(self, other: Any) -> "Composable":
        if isinstance(other, Composable):
            other_graph = other._graph
        elif isinstance(other, rdflib.Graph):
            other_graph = other
        elif hasattr(other, "__iter__"):
            other_graph = graphFrom(other)
        else:
            raise ValueError("Cannot be added: {}".format(other))
        if other_graph and len(other_graph) > 0:
            return self.__class__(self._graph + other_graph)
        else:
            # TODO: Could we just return self?
            return self.__class__(self._graph)

    def __sub__(self, other: Any) -> "Composable":
        if isinstance(other, Composable):
            other_graph = other._graph
        elif isinstance(other, rdflib.Graph):
            other_graph = other
        elif hasattr(other, "__iter__"):
            other_graph = graphFrom(other)
        else:
            raise ValueError("Cannot be subtracted: {}".format(other))
        if other_graph and len(other_graph) > 0:
            return self.__class__(self._graph - other_graph)
        else:
            # TODO: Could we just return self?
            return self.__class__(self._graph)

    def add(self, *triples) -> "Composable":
        for triple in triples:
            self._graph.add(triple)
        return self

    def bind(self, prefix, namespace) -> "Composable":
        self._graph.bind(prefix, namespace)
        return self

    def parse(self, *args, **kwargs) -> "Composable":
        self._graph.parse(*args, **kwargs)
        return self

    def serialize(self, *args, **kwargs) -> Any:
        return self._graph.serialize(*args, **kwargs)

    def construct(self, template, **kwargs) -> "Composable":
        # TODO: How do we confirm that `template` is a `CONSTRUCT` query?
        return self.__class__(graphFrom(Templated.query(self._graph, template, **kwargs)))

    def query(self, template, **kwargs):
        return Templated.query(self._graph, template, **kwargs)

    def update(self, template, **kwargs) -> "Composable":
        Templated.update(self._graph, template, **kwargs)
        return self

    def call(self, function, **kwargs) -> "Composable":
        _ = function(self, **kwargs)
        return self

    def validate(self, shacl_graph=None, fail_if_necessary=False, source_graph=None, allow_infos=True) -> "Composable":
        if SHACL:
            if isinstance(shacl_graph, rdflib.URIRef):
                # If shacl_graph is a URIRef then we assume it is a named graph identifier in source_graph
                if isinstance(source_graph, rdflib.ConjunctiveGraph):
                    shacl_graph = Composable.fromNamed(source_graph, shacl_graph).result
                else:
                    raise TypeError("Wrong type of source graph: {}".format(source_graph))
            conforms, results_graph, results_text = pyshacl.validate(self._graph, shacl_graph=shacl_graph, allow_infos=allow_infos)
            if not conforms:
                if fail_if_necessary:
                    raise ValidationFailure(results_graph, results_text)
                else:
                    logging.warning("SHACL validation failed: {}".format(results_text))
        else:
            raise ModuleNotFoundError("pyshacl")
        return self

    def mapIterable(self, mapping, iterable, **kwargs) -> "Composable":
        if TINYRML:
            data = tinyrml.Mapper(mapping, **kwargs).process(iterable)
            if len(self._graph) > 0:
                self._graph += data
            else:
                self._graph = data
            return self
        else:
            raise ModuleNotFoundError("tinyrml")

    def injectResult(self, target, context, function, **kwargs):
        logging.warning("Adding data to graph {}".format(context))
        return function(target, self.result, context, **kwargs)

    @classmethod
    def fromNamed(cls, source_graph: rdflib.ConjunctiveGraph, named_graph_uri):
        return cls(contents=source_graph.triples((None, None, None),
                                                 context=named_graph_uri))

class ValidationFailure(Exception):
    def __init__(self, results_graph, results_text):
        super().__init__("SHACL validation failed: {}".format(results_text))
        self.results_graph = results_graph
