# Copyright (c) 2022-2025 Ora Lassila & So Many Aircraft
# All rights reserved.
#
# See LICENSE for licensing information

import datetime
import os.path
import logging
import collections
from typing import Optional
import dateutil.parser
import rdflib
from rdflib import SKOS, RDF, Literal, URIRef, Namespace, XSD
from rdfhelpers import Composable, identity, now_local, FileSystemHarvester, FS
from rdfhelpers.producers.common.utilities import record_provenance, strip_xdefault, mod_time, \
    LONG_AGO, NotSpecified
from xmptools import DC, DCT, JPEG_EXTENSIONS, TIFF_EXTENSIONS, DNG_EXTENSIONS, RAW_EXTENSIONS, \
    XMP_EXTENSIONS, makeFileURI, XMPMetadata, PHOTOSHOP

# TODO: This should move to xmptools
IPTC4XMPCORE = Namespace("http://iptc.org/std/Iptc4xmpCore/1.0/xmlns/")

logger = logging.getLogger(__name__)

class XMPHarvester(FileSystemHarvester):
    def __init__(self, agent=None, topics=None, cache_dir=None, photo_class=None,
                 identifier_prop=None, **kwargs):
        super().__init__(agent=agent or FS.PhotoMetadataHarvester, **kwargs)
        self.current_dir = None
        self.current_dir_data = None
        self.cache_dir = NotSpecified.test("cache_dir", cache_dir)
        if isinstance(topics, rdflib.Graph):
            self.topics = Composable(topics)
        elif isinstance(topics, Composable):
            self.topics = topics
        else:
            self.topics = Composable().parse(topics)
        self.photo_class = NotSpecified.test("photo_class", photo_class)
        self.identifier_prop = NotSpecified.test("identifier_prop", identifier_prop)

    def run(self, activity: URIRef = None, **kwargs) -> Composable:
        return super().run(activity=activity or FS.PhotoMetadataHarvestingActivity, **kwargs)

    def perFile(self, file, root, data) -> Optional[URIRef]:
        if self.is_image_file(file):
            xmp, path, exception = None, None, None
            try:
                xmp, path = XMPMetadata.fromFile(os.path.join(root, file))
            except Exception as e:
                exception = e
            if path is None:
                path = os.path.join(root, file)
            if xmp is None:
                logger.warning("No XMP collected for %s", path)
            else:
                _, ext = os.path.splitext(xmp.url)
                if ext in XMP_EXTENSIONS:
                    xmp = xmp.adjustImageURI()
                self.cleanupPerFile(xmp, file)
                for triple in xmp:
                    if not str(triple[1]).startswith(self.CRS_TABLEPROP_PREFIX):
                        data.add(triple)
            return xmp.url
        else:
            _, ext = os.path.splitext(file)
            if ext not in XMP_EXTENSIONS:
                if file != ".DS_Store":
                    logger.warning("Not an image file: %s", os.path.join(root, file))
            return None

    def perFolder(self, folder, subfolders, files, data) -> URIRef:
        logger.info("Attempting to harvest XMP from %s", folder)
        uri = makeFileURI(folder)
        metadata_file = os.path.join(self.cache_dir, self.makeFolderIdentifier(folder) + ".ttl")
        if not files:
            if os.path.exists(metadata_file):
                os.remove(metadata_file)
        elif self.should_generate_metadata(metadata_file, folder, files):
            logger.info("Harvesting XMP from %s", folder)
            folder_data = Composable()
            start_time = now_local()
            for file in files:
                self.perFile(file, folder, folder_data)
            if len(folder_data) > 0:
                self.perFolderFinalize(folder_data, folder, start_time, metadata_file)
            elif os.path.exists(metadata_file):
                logger.info("Unneeded metadata file %s removed", metadata_file)
                os.remove(metadata_file)
        return uri

    def perFolderFinalize(self,
                          folder_data: Composable, folder: str, start_time: datetime, destination):
        logger.info("Writing metadata for %s in %s", folder, destination)
        record_provenance(folder_data, self.agent,
                          start_time=start_time, activity=self.activity,
                          title="Photo metadata for {}".format(folder))
        folder_data.serialize(destination=destination)

    IMAGE_EXTENSIONS = JPEG_EXTENSIONS + TIFF_EXTENSIONS + DNG_EXTENSIONS + RAW_EXTENSIONS
    CRS_TABLEPROP_PREFIX = "http://ns.adobe.com/camera-raw-settings/1.0/Table_"
    CORE_PROPERTIES = [IPTC4XMPCORE.Location, PHOTOSHOP.City, PHOTOSHOP.State, PHOTOSHOP.Country,
                       DCT.creator, DCT.rights, DCT.description, DCT.subject, DCT.title]

    @staticmethod
    def should_generate_metadata(path, root, files):
        time = mod_time(path)
        for file in files:
            mt = mod_time(os.path.join(root, file))
            if mt > time:
                return True
        return time <= LONG_AGO

    def is_image_file(self, file):
        _, ext = os.path.splitext(file)
        return ext in self.IMAGE_EXTENSIONS

    @staticmethod
    def makeFolderIdentifier(path):
        return path.replace('/', '_')

    def matchTopic(self, label):
        for topic in self.topics.subjects(SKOS.prefLabel, label):
            return topic
        return label

    QU_ADD_IPHONE = """
        PREFIX aux: <http://ns.adobe.com/exif/1.0/aux/>
        PREFIX tiff: <http://ns.adobe.com/tiff/1.0/>
        INSERT {
            $xmp tiff:Make "Apple" ; tiff:Model ?lens
        }
        WHERE {
            FILTER NOT EXISTS { $xmp tiff:Model ?model }
            $xmp aux:Lens ?lens
            FILTER (strstarts(?lens, "iPhone"))
        }
    """

    def cleanupPerFile(self, xmp: XMPMetadata, file):
        self.container2repeated(xmp, DC.creator, new_predicate=DCT.creator)
        self.container2repeated(xmp, DC.rights, new_predicate=DCT.rights,
                                value_mapper=strip_xdefault)
        self.container2repeated(xmp, DC.title, new_predicate=DCT.title)
        self.container2repeated(xmp, DC.description, new_predicate=DCT.description)
        self.container2repeated(xmp, DC.subject, new_predicate=DCT.subject,
                                value_mapper=lambda v: self.matchTopic(v))
        xmp.add((xmp.url, RDF.type, self.photo_class))
        xmp.add((xmp.url, self.identifier_prop, Literal(file)))
        xmp.update(self.QU_ADD_IPHONE, xmp=xmp.url)

    QS_MULTIPLE_CONTAINERS = """
        SELECT ?container ?item {
            $node $predicate ?container .
            ?container ?p ?item
            FILTER (STRSTARTS(STR(?p), "http://www.w3.org/1999/02/22-rdf-syntax-ns#_"))
        }
        ORDER BY ?container ?item
    """

    def container2repeated(self, xmp, old_predicate, new_predicate=None, value_mapper=identity):
        try:
            xmp.container2repeated(old_predicate, new_predicate=new_predicate,
                                   remove_predicate=True, value_mapper=value_mapper)
        except ValueError as e:
            if str(e).startswith("Expected only one value"):
                logger.warning("Multiple values for %s in %s", old_predicate, xmp.url)
                containers = collections.defaultdict(list)
                for c, i in xmp.query(self.QS_MULTIPLE_CONTAINERS,
                                      node=xmp.url, predicate=old_predicate):
                    containers[c].append(i)
                items = None
                for c in containers.keys():
                    if items is None:
                        items = containers[c]
                    elif items != containers[c]:
                        raise e
                for c in list(containers.keys())[1:]:
                    xmp.remove((xmp.url, old_predicate, c))
                    xmp.remove((c, None, None))
                xmp.container2repeated(old_predicate, new_predicate=new_predicate,
                                       remove_predicate=True, value_mapper=value_mapper)

    def normalizeDateProperty(self, xmp: XMPMetadata, prop):
        for o in xmp.objects(xmp.url, prop):
            if isinstance(o, rdflib.Literal):
                new_o = self.normalizeDate(o)
                if o != new_o:
                    xmp.remove((xmp.url, prop, o))
                    xmp.add((xmp.url, prop, new_o))

    @classmethod
    def normalizeDate(cls, date_literal: Literal) -> Literal:
        if date_literal.datatype in { XSD.date, XSD.dateTime }:
            return date_literal
        date_literal = str(date_literal)
        if len(date_literal) == 10:
            if ":" in date_literal:
                date_literal = date_literal.replace(":", "-")
            return Literal(date_literal, datatype=XSD.date)
        else:
            try:
                return Literal(dateutil.parser.isoparse(date_literal))
            except ValueError:
                return Literal(date_literal, datatype=XSD.dateTime)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    SMA = Namespace("https://somanyaircraft.com/data/schema/core#")
    SMACAT = Namespace("https://somanyaircraft.com/data/schema/catalog#")
    XMPHarvester(root="/Volumes/basement/sma/aircraft/2025/20250520",
                 topics_file="/Users/ora/Documents/Aircraft/SoManyAircraft/dev/im2kg/data/topics.ttl",
                 cache_dir="/Users/ora/Documents/Aircraft/SoManyAircraft/dev/rdfproducers/cache",
                 photo_class=SMACAT.Photo,
                 identifier_prop=SMA.identifier)\
        .run()
