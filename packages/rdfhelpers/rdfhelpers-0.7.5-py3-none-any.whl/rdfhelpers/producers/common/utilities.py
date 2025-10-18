# Copyright (c) 2022-2025 Ora Lassila & So Many Aircraft
# All rights reserved.
#
# See LICENSE for licensing information

import datetime
import os
import os.path
from urllib.parse import urlparse, parse_qs
import rdflib
from rdfhelpers import now_local

QU_HARVEST_PROV = """
    PREFIX oink: <https://somanyaircraft.com/data/schema/oink#>
    INSERT {
        <> prov:wasGeneratedBy [
                a $activity ;
                prov:startedAtTime $start ;
                prov:endedAtTime ?now ;
                prov:wasAssociatedWith $producer
            ] ;
            rdfs:label ?_label
    }
    WHERE {
        BIND (NOW() AS ?now)
        VALUES ?_label { $title }
    }
"""

def record_provenance(data, agent, activity, start_time, title=None, _update=QU_HARVEST_PROV,
                      **kwargs):
    data.update(_update,
                start=rdflib.Literal(start_time or now_local()),
                activity=activity,
                producer=agent,
                title=rdflib.Literal(title) if title else "UNDEF",
                **kwargs)

def strip_xdefault(literal):
    if literal.language == "x-default":
        return rdflib.Literal(str(literal))
    else:
        return literal

LONG_AGO = datetime.datetime.fromisoformat("1900-01-01").timestamp()

def mod_time(path):
    return os.stat(path).st_mtime if os.path.exists(path) else LONG_AGO

def should_process(target, *sources) -> bool:
    target_mod_time = mod_time(os.path.realpath(target))
    for source in sources:
        if target_mod_time < mod_time(os.path.realpath(source)):
            return True
    return False

class NotSpecified(ValueError):
    def __init__(self, parameter: str):
        super().__init__("Parameter \"{}\" was not specified".format(parameter))

    @classmethod
    def test(cls, parameter: str, value):
        if value is None:
            raise NotSpecified(parameter)
        else:
            return value

def parse_jdbc_url(url, dbtype="mysql"):
    u1 = urlparse(url)
    if u1.scheme != "jdbc":
        raise ValueError("Not jdbc scheme: {}".format(u1.scheme))
    else:
        u2 = urlparse(u1.path)
        if u2.scheme != dbtype:
            raise ValueError("Not {} db type: {}".format(dbtype, u2.scheme))
        else:
            return u2.hostname, u2.path.lstrip("/"), parse_qs(u1.query)
