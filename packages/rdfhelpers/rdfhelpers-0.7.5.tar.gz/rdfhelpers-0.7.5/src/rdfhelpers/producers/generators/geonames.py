import logging
from typing import Iterable
from rdflib import Namespace
from rdfhelpers import Composable
import rdfhelpers.producers.common.interface
from rdfhelpers.producers.apis.geonames import GeonamesAPI
from rdfhelpers.producers.common.utilities import NotSpecified

log = logging.getLogger(__name__)

class GeonamesGenerator(rdfhelpers.producers.common.interface.Generator):
    def __init__(self, api: GeonamesAPI =None, **kwargs):
        super().__init__(**kwargs)
        self.api = NotSpecified.test("api", api)

    def produce(self, data: Composable, identifiers: Iterable =None, **kwargs) -> Composable:
        for identifier in identifiers:
            uri = "https://sws.geonames.org/{}/".format(identifier)
            try:
                data.parse(uri + "about.rdf")
            except Exception as e:
                log.error("Loading %s failed: %s", uri, e)
        return data

    QC_CLEANUP = """
        PREFIX gn: <https://www.geonames.org/ontology#>
        PREFIX gn_old: <http://www.geonames.org/ontology#>
        PREFIX wgs84_pos: <http://www.w3.org/2003/01/geo/wgs84_pos#>
        CONSTRUCT {
            ?thing a gn:Feature, skos:Concept ; ?p_new ?o ; skos:prefLabel ?name
        }
        WHERE {
            VALUES ?p_old {gn_old:name rdfs:seeAlso gn_old:countryCode gn_old:featureCode wgs84_pos:lat wgs84_pos:long}
            ?thing a gn_old:Feature ; ?p_old ?o ; gn_old:name ?name
            BIND (IF(STRSTARTS(str(?p_old), str(gn_old:)),
                     IRI(CONCAT(str(gn:), SUBSTR(str(?p_old), STRLEN(str(gn_old:))+1))),
                     ?p_old)
                  AS ?p_new)
        }
    """

    GN = Namespace("https://www.geonames.org/ontology#")
    GN_NO_SSL = Namespace("http://www.geonames.org/ontology#")
    WGS84_POS = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")

    def cleanup(self, data: Composable, **kwargs) -> Composable:
        return super().cleanup(data, **kwargs)\
                .construct(self.QC_CLEANUP)\
                .bind("gn", self.GN)\
                .bind("wgs84_pos", self.WGS84_POS)
