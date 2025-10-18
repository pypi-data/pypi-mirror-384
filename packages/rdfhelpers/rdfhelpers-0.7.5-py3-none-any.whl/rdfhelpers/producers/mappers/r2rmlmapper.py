# Copyright (c) 2022-2025 Ora Lassila & So Many Aircraft
# All rights reserved.
#
# See LICENSE for licensing information

import logging
import tempfile
from rdfhelpers import Composable
from rdfhelpers.producers.common.interface import Mapper, DatabaseConnectionMixin
from rdfhelpers.producers.mappers.xsltmapper import subproc

log = logging.getLogger(__name__)

# This class was designed to work with R2RML-F (https://github.com/chrdebru/r2rml) but conceivably
# can be adapted to work with other (Java-based) R2RML implementations as well. You have to download
# the JAR file yourself and pass the path to it in the parameter r2rml_jar.

class R2RMLMapper(Mapper, DatabaseConnectionMixin):
    def __init__(self, r2rml_jar=None, **kwargs):
        super().__init__(**kwargs)
        self.r2rml_jar = r2rml_jar

    def produce(self, data: Composable, mapping=None, **kwargs) -> Composable:
        return data.call(self.generateFromRelational, mapping=mapping,
                         connection_url=self.connection_url, user=self.user, passwd=self.passwd)

    def call_r2rml_jar(self, connection_url, user, passwd, mapping, output, syntax):
        # Args:
        #   connection_url: a JDBC URL
        #   user:           username to log into the source JDBC database
        #   passwd:         password to log into the source JDBC database
        #   mapping:        path to the file containing the R2RML mapping
        #   output:         path to the output file
        #   syntax:         desired output format (e.g., "TURTLE")
        subproc("java", "-jar", self.r2rml_jar,
                "--connectionURL", connection_url, "--user", user, "--password", passwd,
                "--mappingFile", mapping, "--outputFile", output, "--format",
                syntax)

    def generateFromRelational(self, data, mapping=None, syntax="TURTLE",
                               connection_url=None, user=None, passwd=None):
        with tempfile.NamedTemporaryFile() as output_file:
            log.info("Running java -jar %s", self.r2rml_jar)
            self.call_r2rml_jar(connection_url, user, passwd, mapping, output_file.name, syntax)
            log.info("Parsing r2rml results")
            return data.parse(output_file.name, format=syntax.lower())
