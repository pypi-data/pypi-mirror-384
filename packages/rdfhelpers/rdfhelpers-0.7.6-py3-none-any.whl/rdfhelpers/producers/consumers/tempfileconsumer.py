import tempfile
import logging
from datetime import datetime, timezone
import contextlib
import threading
from abc import abstractmethod, ABC
from typing import Optional
from rdflib import Literal, Graph, URIRef
from xmptools import makeFileURI
from rdfhelpers import Composable
from rdfhelpers import Producer, Consumer

log = logging.getLogger(__name__)

class TempfileConsumer(Consumer, ABC):
    def __init__(self):
        self.lock = threading.Lock()

    @contextlib.contextmanager
    def transaction(self, graph):
        try:
            with self.lock:
                yield graph
                graph.commit()
        except Exception as e:
            log.error(e)
            graph.rollback()
            raise e

    @abstractmethod
    def consume(self, data: URIRef,
                graph: Graph = None, tempfile_uri=None, start_time=None,
                **kwargs):
        # The parameter data is assumed to be a URL of a temporary file into which the output of
        # the producer has been serialized.
        # TODO: Figure out how we can stream stuff into the temporary file and read it piecemeal
        ...

    def run(self, producer: Producer, graph: Graph = None, **kwargs):
        start_time = datetime.now(tz=timezone.utc)
        with tempfile.NamedTemporaryFile(suffix=".nt") as temp:
            log.debug("Using temporary file {}".format(temp.name))
            producer.run(**kwargs).serialize(destination=temp.name,
                                             format="ntriples", encoding="utf-8")
            with self.transaction(graph):
                self.consume(makeFileURI(temp.name), graph=graph, start_time=Literal(start_time),
                             **kwargs)
