import csv
from typing import Optional
from rdfhelpers import Composable
from rdfhelpers.producers.common.interface import Exporter
from rdfhelpers.producers.common.utilities import NotSpecified

class CSVExporter(Exporter):

    def consume(self, data: Optional[Composable],
                select_query: str = None, writer=None, header_row=True,
                **kwargs):
        w = NotSpecified.test("writer", writer)
        results = data.query(NotSpecified.test("select_query", select_query))
        if header_row:
            w.writerow(results.vars)
        for row in results:
            w.writerow(row)

    @classmethod
    def writer(cls, csvfile, **kwargs):
        # Helper method to create a writer, takes the same parameters as csv.writer()
        return csv.writer(csvfile, **kwargs)

class DummyStream:
    # CSVWriter requires something with a write method, but writerow() returns whatever write
    # returns. Thus, one can now simply yield writerow() results when streaming in Flask.
    @staticmethod
    def write(thing): return thing

class StreamingCSVExporter(CSVExporter):

    def consume(self, data: Optional[Composable], select_query: str = None, header_row=True,
                **kwargs):
        # Returns a generator that yields the rows of the CSV file (including the header row)
        w = self.writer(DummyStream())
        def generate():
            results = data.query(NotSpecified.test("select_query", select_query))
            if header_row:
                yield w.writerow(results.vars)
            for row in results:
                yield w.writerow(row)
        return generate()
