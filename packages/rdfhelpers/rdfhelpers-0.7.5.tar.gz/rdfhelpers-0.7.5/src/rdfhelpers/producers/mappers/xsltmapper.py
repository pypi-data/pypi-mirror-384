# Copyright (c) 2022-2025 Ora Lassila & So Many Aircraft
# All rights reserved.
#
# See LICENSE for licensing information

import logging
import os.path
import datetime
import tempfile
import subprocess
from dateutil.tz import tzlocal
from rdfhelpers import Composable
from rdfhelpers.producers.common.interface import Mapper

logger = logging.getLogger(__name__)

def subproc(*args):
    subprocess.run(args)

class XSLTMapper(Mapper):
    def __init__(self, mapping=None, **kwargs):
        super().__init__(**kwargs)
        self.mapping = mapping

    def produce(self, data: Composable, source=None, **kwargs) -> Composable:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".rdf") as output_file:
            try:
                output_file.close()
                logger.info("Running xsltproc on %s", source)
                subproc("xsltproc", "-o", output_file.name,
                        "--stringparam", "time", datetime.datetime.now(tzlocal()).isoformat(),
                        os.path.abspath(self.mapping), os.path.abspath(source))
                return data.parse(output_file.name)
            finally:
                os.unlink(output_file.name)
