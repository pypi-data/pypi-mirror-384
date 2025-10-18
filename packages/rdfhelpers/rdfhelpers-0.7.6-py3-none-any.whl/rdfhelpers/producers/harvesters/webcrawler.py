# Copyright (c) 2022-2025 Ora Lassila & So Many Aircraft
# All rights reserved.
#
# See LICENSE for licensing information

import logging
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import os.path
import sys
from abc import abstractmethod
import rdflib
import requests
from rdflib import Literal, URIRef
from rdfhelpers import Composable
from rdfhelpers.producers.common.interface import Harvester
from rdfhelpers.producers.harvesters.filesystem import FS

try:
    import bs4
    BS4 = True
except ModuleNotFoundError:
    bs4 = None
    BS4 = False

try:
    import pyRdfa
    PYRDFA = True
except ModuleNotFoundError:
    pyRdfa = None
    PYRDFA = False

log = logging.getLogger(__name__)

SCHEMA = rdflib.Namespace(rdflib.URIRef("https://schema.org/"))

class WebCrawler(Harvester):
    def __init__(self, schemes=None, extensions=None, html_parser="html.parser",
                 ignore_robotstxt=False, user_agent=None, **kwargs):
        if not BS4:
            raise NotImplemented("Support for beautifulsoup4 not available")
        if not PYRDFA:
            raise NotImplemented("Support for pyRdfa not available")
        super().__init__(**kwargs)
        self.schemes = schemes or self.DEFAULT_SCHEMES
        self.extensions = extensions or self.DEFAULT_EXTENSIONS
        self.html_parser = html_parser
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        if ignore_robotstxt:
            self.robotparser = None
        else:
            self.robotparser = RobotFileParser()
        self.crawled = None
        self.visited = None
        self.failed = None

    DEFAULT_USER_AGENT = "SMAWebCrawler"

    def seen(self, url, queue=None):
        return (queue and url in queue) or url in self.visited or url in self.crawled

    DEFAULT_SCHEMES = {"http", "https"}
    DEFAULT_EXTENSIONS = {'', '.html'}

    def initialize(self, root=None, **kwargs) -> Composable:
        if self.robotparser:
            u = urlparse(root)
            self.robotparser.set_url(urljoin(u.scheme + "//" + u.netloc, "robots.txt"))
            self.robotparser.read()
        self.crawled = set()
        self.visited = set()
        self.failed = set()
        return super().initialize(**kwargs)\
            .bind("xhtml", URIRef("http://www.w3.org/1999/xhtml/vocab#"))\
            .bind("fs", URIRef("https://somanyaircraft.com/data/schema/filesystem#"))\
            .bind("ogp", URIRef("https://ogp.me/ns#"))\
            .bind("cc", URIRef("http://creativecommons.org/ns#"))

    def produce(self, data: Composable, root=None, **kwargs) -> Composable:
        log.info("Crawling %s", root)
        netloc = urlparse(root).netloc
        queue = { root }
        while queue:
            url = queue.pop()
            if not self.robotparser or self.robotparser.can_fetch(self.user_agent, url):
                try:
                    u = urlparse(url)
                    if u.scheme in self.schemes:
                        _, ext = os.path.splitext(u.path)
                        if ext in self.extensions and u.netloc == netloc:
                            response = requests.get(url)
                            response.raise_for_status()
                            real_url = response.url
                            soup = bs4.BeautifulSoup(response.content, self.html_parser)
                            for link in soup.find_all("a", href=True):
                                href = link["href"]
                                if not href.startswith("?") and not href.startswith("#"):
                                    link_url = urljoin(real_url, href)
                                    if not self.seen(link_url, queue=queue):
                                        queue.add(link_url)
                            self.crawled.add(real_url)
                            data = self.extract(data, real_url, response.content)
                        elif u.netloc == netloc:
                            response = requests.head(url)
                            response.raise_for_status()
                except requests.exceptions.RequestException:
                    log.warning("Request failed for %s", url)
                    self.failed.add(url)
            else:
                log.warning("Robot exclusion for {}".format(url))
            self.visited.add(url)
        return data

    @abstractmethod
    def extract(self, data: Composable, url, content) -> Composable:
        # Should return data with extracted stuff added
        ...

class WebHarvester(WebCrawler):
    def __init__(self, agent: URIRef = None, **kwargs):
        super().__init__(agent=agent or FS.WebHarvester, **kwargs)

    CLEANUP_UPDATE = '''
        PREFIX xhv: <http://www.w3.org/1999/xhtml/vocab#>
        PREFIX fs: <https://somanyaircraft.com/data/schema/filesystem#>
        DELETE { ?s xhv:role xhv:alert }
        WHERE { ?s xhv:role xhv:alert };
        INSERT { ?page a ?class ; fs:filepath ?path ; fs:website ?site }
        WHERE {
            BIND(IRI($site) as ?site)
            ?page a ?class
            FILTER (strstarts(str(?class), str(schema:)))
            FILTER (strstarts(str(?page), $site))
            BIND (concat("/", strafter(str(?page), $site)) as ?path)
        }
    '''

    def cleanup(self, data: Composable, root=None, **kwargs) -> Composable:
        return super().cleanup(data, **kwargs)\
            .bind("rdfa", pyRdfa.ns_rdfa)\
            .update(self.CLEANUP_UPDATE, site=Literal(root))

    def run(self, activity: URIRef = None, **kwargs) -> Composable:
        return super().run(activity=activity or FS.WebHarvestingActivity, **kwargs)

    def extract(self, data: Composable, url, content) -> Composable:
        # TODO: This fetches the page again. Can we extract RDFa from the content we already have?
        graph = pyRdfa.pyRdfa().graph_from_source(url)
        types = list(graph.triples((rdflib.URIRef(url), rdflib.RDF.type, None)))
        if len(types) == 0:
            # All pages must have some type. Is schema:WebPage the correct one? Who knows...
            graph.add((rdflib.URIRef(url), rdflib.RDF.type, SCHEMA.WebPage))
        return data.add(*graph)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    WebHarvester(agent=FS.WebCralwer)\
        .run(root="https://www.somanyaircraft.com", activity=FS.WebCrawlingActivity)\
        .serialize(sys.stdout.buffer)
