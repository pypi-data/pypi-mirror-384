import itertools
from typing import Any
from rdfhelpers import Composable
from rdfhelpers.producers.mappers.tinyrmlmapper import TinyRMLMapper

try:
    import pandas
    PANDAS = True
except ModuleNotFoundError:
    pandas = None
    PANDAS = False

class PandasMapper(TinyRMLMapper):
    def __init__(self, mapping=None, **kwargs):
        if not PANDAS:
            raise NotImplemented("Support for pandas not available")
        super().__init__(mapping=mapping, **kwargs)

    def readSource(self, source=None, **kwargs) -> Any:
        # Parameter source should be a pandas.DataFrame
        columns = source.columns
        return ({column: value for column, value in itertools.zip_longest(columns, row)}
                for row in source.itertuples(index=False, name=None))

class ExcelMapper(PandasMapper):

    def run(self, source=None, pandas_kwargs=None, **kwargs) -> Composable:
        return super().run(source=pandas.read_excel(source, **(pandas_kwargs or {})),
                           **kwargs)
