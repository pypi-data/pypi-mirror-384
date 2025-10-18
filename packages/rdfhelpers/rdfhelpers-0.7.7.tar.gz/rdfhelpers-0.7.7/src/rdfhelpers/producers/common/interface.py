# Copyright (c) 2022-2025 Ora Lassila & So Many Aircraft
# All rights reserved.
#
# See LICENSE for licensing information

import io
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional, Union
from contextlib import nullcontext
import rdfhelpers
import requests
from rdflib import URIRef, PROV
from rdfhelpers import Composable, now_local
from rdfhelpers.producers.common.utilities import record_provenance, NotSpecified

log = logging.getLogger(__name__)

class Producer(ABC):
    def __init__(self, agent: URIRef = None, data_class=None):
        if not agent:
            log.warning("No agent specified, using prov:Agent")
        self.agent = agent or PROV.Agent
        self.activity = None
        self.data_class = data_class or Composable
        self.source = None

    def initialize(self, **kwargs) -> Composable:
        return self.data_class()

    @abstractmethod
    def produce(self, data: Composable, **kwargs) -> Composable:
        ...

    def cleanup(self, data: Composable, **kwargs) -> Composable:
        return data

    def run(self, activity: URIRef = None, provenance=True, **kwargs) -> Composable:
        if not activity:
            log.warning("No activity specified, using prov:Activity")
        self.activity = activity or PROV.Activity
        start_time = now_local()
        data = self.cleanup(self.produce(self.initialize(**kwargs), **kwargs), **kwargs)
        if provenance:
            record_provenance(data, self.agent, start_time=start_time, activity=self.activity)
        return data

class Generator(Producer, ABC):
    pass

class Harvester(Producer, ABC):
    pass

class Mapper(Producer, ABC):
    pass

class FileReaderMixin(Producer, ABC):

    def run(self, source=None, source_kwargs=None, **kwargs) -> Composable:
        if not source:
            raise ValueError("No source file was specified")
        with (self.openSourceFile(source, **(source_kwargs or {})) or nullcontext()) as source:
            try:
                self.source = source
                return super().run(**kwargs)
            finally:
                self.source = None

    @staticmethod
    def openSourceFile(file, **kwargs):
        source = open(file, **kwargs)
        marker = source.read(1)
        if marker != '\ufeff':
            source.seek(0, io.SEEK_SET)
        return source

class DatabaseConnectionMixin(Producer, ABC):
    def __init__(self, connection_url=None, user=None, passwd=None, **kwargs):
        super().__init__(**kwargs)
        self.connection_url = connection_url
        self.user = user
        self.passwd = passwd

class ComposableHelper(Producer):
    # This is a class whose run() method takes a Composable and returns it, intended as a means of
    # creating a producer that simply "produces" existing data
    def run(self, activity: URIRef = None, provenance=True,
            data: rdfhelpers.Composable = None, **kwargs) -> Composable:
        return data

    def produce(self, data: Composable, **kwargs) -> Composable:
        raise NotImplemented()

class Consumer(ABC):

    def run(self, producer: Union[Producer, Composable], **kwargs) -> Any:
        if isinstance(producer, Producer):
            return self.consume(producer.run(**kwargs), **kwargs)
        elif isinstance(producer, Composable):
            return self.consume(producer, **kwargs)
        else:
            raise TypeError("Incompatible producer {}".format(producer))

    @abstractmethod
    def consume(self, data: Optional[Composable], **kwargs) -> Any:
        ...

class Exporter(Consumer, ABC):
    pass

class API(ABC):
    def __init__(self, endpoint):
        self.endpoint = endpoint

    def get(self, **kwargs):
        try:
            response = requests.get(self.endpoint, params=self.makeRequestParams(**kwargs))
            response.raise_for_status()
            return self.translateResponse(response)
        except Exception as e:
            log.error(e)
            raise e

    @staticmethod
    def makeRequestParams(**kwargs):
        return kwargs

    @abstractmethod
    def translateResponse(self, response: requests.Response) -> Any:
        ...
