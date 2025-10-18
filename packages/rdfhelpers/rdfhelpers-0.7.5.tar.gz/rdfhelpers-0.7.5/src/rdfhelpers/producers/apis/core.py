import rdfhelpers.producers.common.interface
import requests
import xml.etree.ElementTree
from typing import Any

class XMLAPI(rdfhelpers.producers.common.interface.API):

    def translateResponse(self, response: requests.Response) -> Any:
        return xml.etree.ElementTree.fromstring(response.text)

    @classmethod
    def element2dict(cls, element: xml.etree.ElementTree.Element, children: list[str]) -> dict:
        return {child: child_element.text
                for child, child_element in [(child, element.find(child)) for child in children]
                if child_element is not None}

class JSONAPI(rdfhelpers.producers.common.interface.API):

    def translateResponse(self, response: requests.Response) -> Any:
        return response.json()
