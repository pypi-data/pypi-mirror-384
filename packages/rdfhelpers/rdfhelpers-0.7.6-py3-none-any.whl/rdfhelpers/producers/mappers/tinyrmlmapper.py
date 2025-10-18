# Copyright (c) 2022-2025 Ora Lassila & So Many Aircraft
# All rights reserved.
#
# See LICENSE for licensing information

from abc import ABC, abstractmethod
from collections.abc import Iterable
import csv
from typing import Any
from rdfhelpers import Composable
from rdflib import URIRef

from rdfhelpers.producers.common.interface import Mapper, FileReaderMixin

class TinyRMLMapper(Mapper, ABC):
    def __init__(self, mapping=None, **kwargs):
        super().__init__(**kwargs)
        self.mapping = mapping

    @abstractmethod
    def readSource(self, source, **kwargs) -> Any:
        ...

    def produce(self, data: Composable, source=None, tinyrml_kwargs=None, **kwargs) -> Composable:
        return data.mapIterable(self.mapping, self.readSource(self.source or source, **kwargs),
                                **(tinyrml_kwargs or {}))

class PlainCSVMapper(FileReaderMixin, TinyRMLMapper):
    # Pass source_file= and mapping= to self.run()

    def readSource(self, source, **kwargs) -> Iterable[dict]:
        return csv.DictReader(source)

    def openSourceFile(self, file, **kwargs):
        return super().openSourceFile(file, newline='', **kwargs)
