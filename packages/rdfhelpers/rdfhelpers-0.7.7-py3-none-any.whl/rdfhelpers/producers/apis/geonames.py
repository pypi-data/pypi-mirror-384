from rdfhelpers.producers.common.utilities import NotSpecified
from rdfhelpers.producers.apis.core import XMLAPI
import logging
from typing import Iterable, Union

log = logging.getLogger(__name__)

class GeonamesAPI(XMLAPI):
    def __init__(self, username=None, components=None):
        super().__init__(endpoint="http://api.geonames.org/search?")
        self.username = NotSpecified.test("username", username)
        self.components = components or ["geonameId"]

    def makeRequestParams(self, **kwargs):
        return {"username": self.username} | super().makeRequestParams(**kwargs)

    def get(self, **kwargs) -> Union[Iterable[dict], Iterable[str]]:
        results = list()
        single = len(self.components) == 1
        for child in super().get(**kwargs):
            if child.tag == "geoname":
                if single:
                    results.append(child.find(self.components[0]).text)
                else:
                    results.append(self.element2dict(child, self.components))
        return results
