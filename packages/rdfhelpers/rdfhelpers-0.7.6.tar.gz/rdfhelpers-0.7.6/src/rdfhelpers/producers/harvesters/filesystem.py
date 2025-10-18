# Copyright (c) 2022-2025 Ora Lassila & So Many Aircraft
# All rights reserved.
#
# See LICENSE for licensing information

import os.path
import sys
import datetime
from typing import Optional
from abc import ABC, abstractmethod
from rdflib import URIRef, Literal, RDF, DCTERMS, Namespace
import xmptools
from rdfhelpers import Composable
from rdfhelpers.producers.common.interface import Harvester
from rdfhelpers.producers.common.utilities import NotSpecified

FS = Namespace("https://somanyaircraft.com/data/schema/filesystem#")

class FileSystemHarvester(Harvester, ABC):
    def __init__(self, agent=None, **kwargs):
        super().__init__(agent=agent or FS.FileSystemHarvester, **kwargs)

    def initialize(self, **kwargs) -> Composable:
        return super().initialize(**kwargs).bind("fs", FS)

    def produce(self, data: Composable, root=None, **kwargs) -> Composable:
        root = NotSpecified.test("root", root)
        for r, subdirs, files in os.walk(root):
            self.perFolder(r, subdirs, files, data)
        return data

    def run(self, activity: URIRef = None, **kwargs) -> Composable:
        return super().run(activity=activity or FS.FileSystemHarvestingActivity, **kwargs)

    @abstractmethod
    def perFolder(self, folder: str, subfolders: list[str], files: list[str], data) -> URIRef:
        ...

    @abstractmethod
    def perFile(self, file, root, data) -> Optional[URIRef]:
        # Should return None if decides not to process file
        ...


class MinimalGraphProducingFileSystemHarvester(FileSystemHarvester):

    def perFolder(self, folder: str, subfolders: list[str], files: list[str], data) -> URIRef:
        # path = os.path.join(folder, folder)
        uri = xmptools.makeFileURI(folder)
        data.add((uri, RDF.type, FS.Folder))
        data.add(*[(xmptools.makeFileURI(s), FS.parent, uri) for s in subfolders])
        for file in files:
            self.perFile(file, folder, data)
        return uri

    def perFile(self, file, root, data) -> Optional[URIRef]:
        path = os.path.join(root, file)
        uri = xmptools.makeFileURI(path)
        link = os.path.islink(path)
        data.add((uri, RDF.type, FS.Link if link else FS.Document),
                 (uri, FS.parent, xmptools.makeFileURI(root)))
        if link:
            data.add((uri, FS.target, xmptools.makeFileURI(os.path.realpath(file))))
        return uri


class GraphProducingFileSystemHarvester(MinimalGraphProducingFileSystemHarvester):

    def addMetadata(self, uri: URIRef, data: Composable) -> URIRef:
        s = os.lstat(xmptools.makeFilePath(uri))
        data.add((uri, DCTERMS.created, Literal(datetime.datetime.fromtimestamp(s.st_birthtime))),
                 (uri, DCTERMS.modified, Literal(datetime.datetime.fromtimestamp(s.st_mtime))))
        return uri

    def perFile(self, file, root, data) -> Optional[URIRef]:
        uri = super().perFile(file, root, data)
        return None if uri is None else self.addMetadata(uri, data)

    def perFolder(self, folder, subfolders, files, data) -> URIRef:
        return self.addMetadata(super().perFolder(folder, subfolders, files, data), data)
