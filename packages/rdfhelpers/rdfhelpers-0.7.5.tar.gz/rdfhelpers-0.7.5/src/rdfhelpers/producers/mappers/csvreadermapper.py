import csv
from abc import ABC, abstractmethod
from typing import Optional, Iterable
from itertools import zip_longest
from rdflib import URIRef, BNode, Literal
from rdfhelpers import Composable
from rdfhelpers.producers.common.interface import Mapper, FileReaderMixin

class CSVReaderMapper(Mapper, FileReaderMixin, ABC):
    def __init__(self, agent=None, **kwargs):
        super().__init__(agent=agent, **kwargs)
        self.header_row = None

    def openSourceFile(self, file, **kwargs):
        return open(file, newline='')

    def initialize(self, csv_reader_kwargs: dict = None, header_row=True, **kwargs) -> Composable:
        if self.source:
            self.source = csv.reader(self.source, **(csv_reader_kwargs or {}))
            if header_row:
                self.header_row = next(self.source)
        return super().initialize(**kwargs)

    def produce(self, data: Composable, **kwargs) -> Composable:
        for row in self.source:
            data = self.perRow(data, row)
        return data

    @abstractmethod
    def perRow(self, data: Composable, row) -> Composable:
        ...

class CSVWMapper(CSVReaderMapper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base = None
        self.properties = None

    def initialize(self, header_row=True, base=None, **kwargs) -> Composable:
        if not header_row:
            raise ValueError("{} needs a header row".format(self))
        data = super().initialize(header_row=header_row, **kwargs)
        self.base = base
        headers: Optional[Iterable[str]] = self.header_row  # this is to spoof the linter
        self.properties = [URIRef(self.base + "#" + col.replace(' ', '_')) for col in headers]
        return data

    def perRow(self, data: Composable, row) -> Composable:
        s = BNode()
        for p, o in zip_longest(self.properties, row):
            data.add((s, p, Literal(o)))
        return data
