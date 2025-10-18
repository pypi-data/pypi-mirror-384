# Copyright (c) 2022-2025, Ora Lassila & So Many Aircraft
# All rights reserved.
#
# See LICENSE for licensing information
#
# This module implements some useful functionality for querying with RDFLib.
#
import logging
import rdflib.plugins.sparql.processor
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib import Literal, URIRef
import string
import numbers

def identity(x):
    return x

# Make a new dictionary with values mapped using a callable
def mapDict(dictionary, mapper=identity):
    return {key: mapper(value) for key, value in dictionary.items()}

# TEMPLATED QUERIES
#
# This mechanism can be used in lieu of RDFLib's "initBindings=" parameter for SPARQL queries *and
# updates* with the added benefit that replacements are not limited to SPARQL terms.
class Templated:

    @classmethod
    def query(cls, graph, template, **kwargs):
        q = cls.convert(template, kwargs) if kwargs else template
        logging.debug(q)
        return graph.query(q)

    @classmethod
    def update(cls, graph, template, **kwargs):
        q = cls.convert(template, kwargs) if kwargs else template
        logging.debug(q)
        graph.update(q)

    @classmethod
    def ask(cls, graph, ask_template, **kwargs):
        try:
            return graph.query(ask_template, **kwargs).askAnswer
        except Exception as e:
            logging.error("Maybe not an ASK query...")
            raise e

    @classmethod
    def convert(cls, template, kwargs):
        return string.Template(template).substitute(**mapDict(kwargs, mapper=cls.forSPARQL))

    @classmethod
    def forSPARQL(cls, thing):
        if isinstance(thing, URIRef) or isinstance(thing, Literal):
            return thing.n3()
        elif isinstance(thing, str):
            return thing  # if thing[0] == '?' else cls.forSPARQL(Literal(thing))
        elif isinstance(thing, bool):
            return "true" if thing else "false"
        elif isinstance(thing, numbers.Number):
            return thing
        elif thing is None:
            return ""
        else:
            raise ValueError("Cannot make a SPARQL compatible value: %s", thing)

class TemplatedQueryMixin:  # abstract, can be mixed with Graph or Store

    def query(self, querystring, **kwargs):
        return Templated.query(super(), querystring, **kwargs)

    def update(self, querystring, **kwargs):
        Templated.update(super(), querystring, **kwargs)

    def ask(self, querystring, **kwargs):
        return Templated.ask(self, querystring, **kwargs)  # no super() since the ask method is new

class TemplateWrapper:
    def __init__(self, graph):
        self._graph = graph

    def query(self, querystring, **kwargs):
        return Templated.query(self._graph, querystring, **kwargs)

    def update(self, querystring, **kwargs):
        Templated.update(self._graph, querystring, **kwargs)


# Make a new Graph instance from triples (an iterable)
def graphFrom(triples, add_to=None, graph_class=rdflib.Graph, **kwargs):
    if add_to is None:
        add_to = graph_class(**kwargs)
    for triple in triples:
        add_to.add(triple)
    return add_to if len(add_to) > 0 else None

# SPARQL REPOSITORY

class SPARQLRepository(TemplatedQueryMixin, SPARQLUpdateStore):
    def __init__(self, query_endpoint=None, update_endpoint=None, **kwargs):
        super().__init__(query_endpoint=query_endpoint,
                         update_endpoint=update_endpoint or query_endpoint,
                         **kwargs)

    # Why do I get a complaint about this? SPARQLUpdateStore is not an abstract class...
    def triples_choices(self, _, context=None):
        pass
