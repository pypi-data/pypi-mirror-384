# Copyright (c) 2022-2025, Ora Lassila & So Many Aircraft
# All rights reserved.
#
# See LICENSE for licensing information
#
# This module implements some useful stuff when programming with RDFLib.

from rdfhelpers.core.basics import expandQName, URI, getvalue, setvalue, isContainerItemPredicate, \
    makeContainerItemPredicate, diff, getContainerStatements, getContainerItems, \
    setContainerItems, getCollectionItems, makeCollection, FocusedGraph, CBDGraph
from rdfhelpers.core.cbd import cbd, reverse_cbd, cbd_limited_properties
from rdfhelpers.core.templated import SPARQLRepository, graphFrom, identity, mapDict, Templated, \
    TemplatedQueryMixin, TemplateWrapper
from rdfhelpers.core.composable import Composable, ValidationFailure
from rdfhelpers.core.labels import GENERIC_PREFIX_MATCHER, abbreviate, LabelCache, SKOSLabelCache, \
    BNodeTracker, BNodeMarker
from rdfhelpers.core.uri import URICanonicalizer
from rdfhelpers.core.time import now_local

from rdfhelpers.producers.common.interface import Producer, Harvester, Mapper, Generator, \
    FileReaderMixin, Consumer, API

from rdfhelpers.producers.apis.core import XMLAPI, JSONAPI
from rdfhelpers.producers.apis.geonames import GeonamesAPI

from rdfhelpers.producers.harvesters.filesystem import FS, FileSystemHarvester, \
    MinimalGraphProducingFileSystemHarvester, GraphProducingFileSystemHarvester
from rdfhelpers.producers.harvesters.webcrawler import WebCrawler, WebHarvester
from rdfhelpers.producers.harvesters.xmpharvester import XMPHarvester

from rdfhelpers.producers.mappers.tinyrmlmapper import TinyRMLMapper, PlainCSVMapper
from rdfhelpers.producers.mappers.pandasmapper import PandasMapper, ExcelMapper
from rdfhelpers.producers.mappers.r2rmlmapper import R2RMLMapper
from rdfhelpers.producers.mappers.xsltmapper import XSLTMapper
from rdfhelpers.producers.mappers.csvreadermapper import CSVReaderMapper, CSVWMapper

from rdfhelpers.producers.generators.mysqlgenerator import MySQLGenerator
from rdfhelpers.producers.generators.geonames import GeonamesGenerator

from rdfhelpers.producers.consumers.tempfileconsumer import TempfileConsumer
from rdfhelpers.producers.consumers.csvexporter import CSVExporter, StreamingCSVExporter

__all__ = [
    "expandQName", "URI", "getvalue", "setvalue", "isContainerItemPredicate",
    "makeContainerItemPredicate", "diff", "cbd", "reverse_cbd", "cbd_limited_properties",
    "getContainerStatements", "getContainerItems", "setContainerItems", "getCollectionItems",
    "makeCollection", "SPARQLRepository", "FocusedGraph", "CBDGraph", "graphFrom", "identity",
    "mapDict", "Templated", "Composable", "TemplatedQueryMixin", "ValidationFailure",
    "GENERIC_PREFIX_MATCHER", "abbreviate", "LabelCache", "SKOSLabelCache", "BNodeTracker",
    "BNodeMarker", "URICanonicalizer", "Producer", "Harvester", "Mapper", "Generator",
    "FileReaderMixin", "Consumer", "API", "TempfileConsumer", "XMLAPI", "JSONAPI", "GeonamesAPI",
    "FS", "FileSystemHarvester", "MinimalGraphProducingFileSystemHarvester", "WebCrawler",
    "WebHarvester", "GraphProducingFileSystemHarvester", "TinyRMLMapper", "PlainCSVMapper",
    "R2RMLMapper", "CSVReaderMapper", "CSVWMapper", "XSLTMapper", "XMPHarvester", "MySQLGenerator",
    "GeonamesGenerator", "PandasMapper", "ExcelMapper", "TempfileConsumer", "CSVExporter",
    "StreamingCSVExporter", "TemplateWrapper", "now_local"
]
