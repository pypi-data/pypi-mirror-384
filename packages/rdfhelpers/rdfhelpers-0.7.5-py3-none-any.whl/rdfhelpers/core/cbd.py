# Copyright (c) 2022, Ora Lassila & So Many Aircraft
# All rights reserved.
#
# See LICENSE for licensing information
#
# This module implements the computation of the Concise Bounded Description.
#
from rdflib import Graph, ConjunctiveGraph, BNode
from rdfhelpers.core.templated import graphFrom, Templated

CBD_GOOD = '''
    SELECT ?good {
        {
            SELECT (count(?o1) AS ?count) {
                ?s1 ?p1 ?o1
                FILTER NOT EXISTS { ?o1 ?p2 ?o2 }
                FILTER (isblank(?o1))
            }
        }
        BIND (?count = 0 AS ?good)
    }
'''
CBD_QUERY_1 = '''
    CONSTRUCT { ?s1 ?p1 ?o1 }
    WHERE {
        BIND($uri AS ?s1)
        ?s1 ?p1 ?o1
    }
'''
CBD_QUERY_2 = '''
    CONSTRUCT { ?s1 ?p1 ?o1 }
    WHERE {
        {
            SELECT ?s1 ?p1 ?o1 {
                BIND($uri AS ?s1)
                ?s1 ?p1 ?o1
            }
        } UNION {
            SELECT ?s1 ?p1 ?o1 {
                BIND($uri AS ?s2)
                ?s2 ?p2 ?s1 . FILTER(ISBLANK(?s1))
                ?s1 ?p1 ?o1
            }
        }
    }
'''
CBD_QUERY_3 = '''
    CONSTRUCT { ?s1 ?p1 ?o1 }
    WHERE {
        {
            SELECT ?s1 ?p1 ?o1 {
                BIND($uri AS ?s1)
                ?s1 ?p1 ?o1
            }
        } UNION {
            SELECT ?s1 ?p1 ?o1 {
                BIND($uri AS ?s2)
                ?s2 ?p2 ?s1 . FILTER(ISBLANK(?s1))
                ?s1 ?p1 ?o1
            }
        } UNION {
            SELECT ?s1 ?p1 ?o1 {
                BIND($uri AS ?s3)
                ?s3 ?p3 ?s2 . FILTER(ISBLANK(?s2))
                ?s2 ?p2 ?s1 . FILTER(ISBLANK(?s1))
                ?s1 ?p1 ?o1
            }
        }
    }
'''
CBD_QUERY_4 = '''
    CONSTRUCT { ?s1 ?p1 ?o1 }
    WHERE {
        {
            SELECT ?s1 ?p1 ?o1 {
                BIND($uri AS ?s1)
                ?s1 ?p1 ?o1
            }
        } UNION {
            SELECT ?s1 ?p1 ?o1 {
                BIND($uri AS ?s2)
                ?s2 ?p2 ?s1 . FILTER(ISBLANK(?s1))
                ?s1 ?p1 ?o1
            }
        } UNION {
            SELECT ?s1 ?p1 ?o1 {
                BIND($uri AS ?s3)
                ?s3 ?p3 ?s2 . FILTER(ISBLANK(?s2))
                ?s2 ?p2 ?s1 . FILTER(ISBLANK(?s1))
                ?s1 ?p1 ?o1
            }
        } UNION {
            SELECT ?s1 ?p1 ?o1 {
                BIND($uri AS ?s4)
                ?s4 ?p4 ?s3 . FILTER(ISBLANK(?s3))
                ?s3 ?p3 ?s2 . FILTER(ISBLANK(?s2))
                ?s2 ?p2 ?s1 . FILTER(ISBLANK(?s1))
                ?s1 ?p1 ?o1
            }
        }
    }
'''
CBD_QUERY_WITH_CONTEXT = '''
    SELECT ?s1 ?p1 ?o1 {
        GRAPH $context {
            {
                SELECT ?s1 ?p1 ?o1 {
                    BIND($uri AS ?s1)
                    ?s1 ?p1 ?o1
                }
            } UNION {
                SELECT ?s1 ?p1 ?o1 {
                    BIND($uri AS ?s2)
                    ?s2 ?p2 ?s1 . FILTER(ISBLANK(?s1))
                    ?s1 ?p1 ?o1
                }
            } UNION {
                SELECT ?s1 ?p1 ?o1 {
                    BIND($uri AS ?s3)
                    ?s3 ?p3 ?s2 . FILTER(ISBLANK(?s2))
                    ?s2 ?p2 ?s1 . FILTER(ISBLANK(?s1))
                    ?s1 ?p1 ?o1
                }
            } UNION {
                SELECT ?s1 ?p1 ?o1 {
                    BIND($uri AS ?s4)
                    ?s4 ?p4 ?s3 . FILTER(ISBLANK(?s3))
                    ?s3 ?p3 ?s2 . FILTER(ISBLANK(?s2))
                    ?s2 ?p2 ?s1 . FILTER(ISBLANK(?s1))
                    ?s1 ?p1 ?o1
                }
            }
        }
    }
'''
CBD_LIMITED_QUERY = '''
    SELECT ?s1 ?p1 ?o1 {
        {
            SELECT ?s1 ?p1 ?o1 {
                BIND($uri AS ?s1)
                ?s1 ?p1 ?o1
                FILTER (?p1 IN $properties)
            }
        } UNION {
            SELECT ?s1 ?p1 ?o1 {
                BIND($uri AS ?s2)
                ?s2 ?p2 ?s1 . FILTER(ISBLANK(?s1))
                FILTER (?p2 IN $properties)
                ?s1 ?p1 ?o1
            }
        } UNION {
            SELECT ?s1 ?p1 ?o1 {
                BIND($uri AS ?s3)
                ?s3 ?p3 ?s2 . FILTER(ISBLANK(?s2))
                FILTER (?p3 IN $properties)
                ?s2 ?p2 ?s1 . FILTER(ISBLANK(?s1))
                ?s1 ?p1 ?o1
            }
        } UNION {
            SELECT ?s1 ?p1 ?o1 {
                BIND($uri AS ?s4)
                ?s4 ?p4 ?s3 . FILTER(ISBLANK(?s3))
                FILTER (?p4 IN $properties)
                ?s3 ?p3 ?s2 . FILTER(ISBLANK(?s2))
                ?s2 ?p2 ?s1 . FILTER(ISBLANK(?s1))
                ?s1 ?p1 ?o1
            }
        }
    }
'''
CBD_LIMITED_QUERY_WITH_CONTEXT = '''
    SELECT ?s1 ?p1 ?o1 {
        GRAPH $context {
            {
                SELECT ?s1 ?p1 ?o1 {
                    BIND($uri AS ?s1)
                    ?s1 ?p1 ?o1
                    FILTER (?p1 IN $properties)
                }
            } UNION {
                SELECT ?s1 ?p1 ?o1 {
                    BIND($uri AS ?s2)
                    ?s2 ?p2 ?s1 . FILTER(ISBLANK(?s1))
                    FILTER (?p2 IN $properties)
                    ?s1 ?p1 ?o1
                }
            } UNION {
                SELECT ?s1 ?p1 ?o1 {
                    BIND($uri AS ?s3)
                    ?s3 ?p3 ?s2 . FILTER(ISBLANK(?s2))
                    FILTER (?p3 IN $properties)
                    ?s2 ?p2 ?s1 . FILTER(ISBLANK(?s1))
                    ?s1 ?p1 ?o1
                }
            } UNION {
                SELECT ?s1 ?p1 ?o1 {
                    BIND($uri AS ?s4)
                    ?s4 ?p4 ?s3 . FILTER(ISBLANK(?s3))
                    FILTER (?p4 IN $properties)
                    ?s3 ?p3 ?s2 . FILTER(ISBLANK(?s2))
                    ?s2 ?p2 ?s1 . FILTER(ISBLANK(?s1))
                    ?s1 ?p1 ?o1
                }
            }
        }
    }
'''

def cbd(source, resource,
        use_sparql=True, context=None, target=None, target_class=Graph, use_describe=False,
        incremental=False,
        **kwargs):
    if use_sparql:
        if context:
            triples = source.query(CBD_QUERY_WITH_CONTEXT, uri=resource, context=context)
        elif use_describe:
            triples = source.query("DESCRIBE $uri", uri=resource)
        elif not incremental:
            triples = source.query(CBD_QUERY_4, uri=resource)
        else:
            triples = source.query(CBD_QUERY_1, uri=resource)
            if not _cbd_good(triples.graph):
                triples = source.query(CBD_QUERY_2, uri=resource)
                if not _cbd_good(triples.graph):
                    triples = source.query(CBD_QUERY_3, uri=resource)
                    if not _cbd_good(triples.graph):
                        triples = source.query(CBD_QUERY_4, uri=resource)
    else:
        # Best choice for a source graph with an in-memory store
        triples = _cbd_no_sparql(source, resource, context=context)
    return graphFrom(triples, add_to=target, graph_class=target_class)

def _cbd_good(triples):
    for good, in triples.query(CBD_GOOD):
        return good.value
    return True

def _cbd_no_sparql(source, resource, context=None):
    triples = list()
    subjects = list([resource])
    subjects_seen = list()
    if isinstance(source, ConjunctiveGraph):
        def get_triples(s): return source.quads((s, None, None, context))
    elif context is None:
        def get_triples(s): return source.triples((s, None, None))
    else:
        raise ValueError("Source graph must be context-aware")
    while subjects:
        subject = subjects.pop()
        if subject not in subjects_seen:
            subjects_seen.append(subject)
            for triple in get_triples(subject):
                triples.append(triple)
                leaf = triple[2]
                if isinstance(leaf, BNode):
                    subjects.append(leaf)
    return triples

def cbd_limited_properties(source, resource, properties,
        context=None, target=None, target_class=Graph,
        **kwargs):
    props = "(" + ", ".join([Templated.forSPARQL(s) for s in properties]) + ")"
    if context is None:
        triples = source.query(CBD_LIMITED_QUERY, uri=resource, properties=props)
    else:
        triples = source.query(CBD_LIMITED_QUERY_WITH_CONTEXT, uri=resource, context=context,
                               properties=props)
    return graphFrom(triples, add_to=target, graph_class=target_class, **kwargs)

REVERSE_CBD_QUERY = '''
    SELECT DISTINCT ?o1 ?p1 ?s1 {
        {
            SELECT ?o1 ?p1 ?s1 {
                BIND($uri AS ?s1)
                ?o1 ?p1 ?s1
                FILTER (!(?p1 = rdf:type && ?s1 in (rdfs:Resource, owl:Thing)))
            }
        } UNION {
            SELECT ?o1 ?p1 ?s1 {
                BIND($uri AS ?s2)
                ?s1 ?p2 ?s2 . FILTER(ISBLANK(?s1))
                ?o1 ?p1 ?s1
                FILTER (!(?p1 = rdf:type && ?s1 in (rdfs:Resource, owl:Thing)))
            }
        } UNION {
            SELECT ?o1 ?p1 ?s1 {
                BIND($uri AS ?s3)
                ?s2 ?p3 ?s3 . FILTER(ISBLANK(?s2))
                ?s1 ?p2 ?s2 . FILTER(ISBLANK(?s1))
                ?s1 ?p1 ?o1
                FILTER (!(?p1 = rdf:type && ?s1 in (rdfs:Resource, owl:Thing)))
            }
        } UNION {
            SELECT ?o1 ?p1 ?s1 {
                BIND($uri AS ?s4)
                ?s3 ?p4 ?s4 . FILTER(ISBLANK(?s3))
                ?s2 ?p3 ?s3 . FILTER(ISBLANK(?s2))
                ?s1 ?p2 ?s2 . FILTER(ISBLANK(?s1))
                ?s1 ?p1 ?o1
                FILTER (!(?p1 = rdf:type && ?s1 in (rdfs:Resource, owl:Thing)))
            }
        }
    }

'''
REVERSE_CBD_QUERY_WITH_CONTEXT = '''
    SELECT DISTINCT ?s1 ?p1 ?o1 {
        GRAPH $context {
            {
                SELECT ?o1 ?p1 ?s1 {
                    BIND($uri AS ?s1)
                    ?o1 ?p1 ?s1
                    FILTER (!(?p1 = rdf:type && ?s1 in (rdfs:Resource, owl:Thing)))
                }
            } UNION {
                SELECT ?o1 ?p1 ?s1 {
                    BIND($uri AS ?s2)
                    ?s1 ?p2 ?s2 . FILTER(ISBLANK(?s1))
                    ?o1 ?p1 ?s1
                    FILTER (!(?p1 = rdf:type && ?s1 in (rdfs:Resource, owl:Thing)))
                }
            } UNION {
                SELECT ?o1 ?p1 ?s1 {
                    BIND($uri AS ?s3)
                    ?s2 ?p3 ?s3 . FILTER(ISBLANK(?s2))
                    ?s1 ?p2 ?s2 . FILTER(ISBLANK(?s1))
                    ?s1 ?p1 ?o1
                    FILTER (!(?p1 = rdf:type && ?s1 in (rdfs:Resource, owl:Thing)))
                }
            } UNION {
                SELECT ?o1 ?p1 ?s1 {
                    BIND($uri AS ?s4)
                    ?s3 ?p4 ?s4 . FILTER(ISBLANK(?s3))
                    ?s2 ?p3 ?s3 . FILTER(ISBLANK(?s2))
                    ?s1 ?p2 ?s2 . FILTER(ISBLANK(?s1))
                    ?s1 ?p1 ?o1
                    FILTER (!(?p1 = rdf:type && ?s1 in (rdfs:Resource, owl:Thing)))
                }
            }
        }
    }
'''

def reverse_cbd(source, resource,
                use_sparql=True, context=None, target=None, target_class=Graph, **kwargs):
    if use_sparql:
        if context:
            triples = source.query(REVERSE_CBD_QUERY_WITH_CONTEXT, uri=resource, context=context)
        else:
            triples = source.query(REVERSE_CBD_QUERY, uri=resource)
    else:
        triples = _reverse_cbd_no_sparql(source, resource, context=context)
    return graphFrom(triples, add_to=target, graph_class=target_class, **kwargs)

def _reverse_cbd_no_sparql(source, resource, context=None):
    triples = list()
    objects = list([resource])
    objects_seen = list()
    if isinstance(source, ConjunctiveGraph):
        def get_triples(o): return source.quads((None, None, o, context))
    elif context is None:
        def get_triples(o): return source.triples((None, None, o))
    else:
        raise ValueError("Source graph must be context-aware")
    while objects:
        object = objects.pop()
        if object not in objects_seen:
            objects_seen.append(object)
            for triple in get_triples(object):
                triples.append(triple)
                leaf = triple[0]
                if isinstance(leaf, BNode):
                    objects.append(leaf)
    return triples
