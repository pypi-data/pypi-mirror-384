# Copyright (c) 2022-2025 Ora Lassila & So Many Aircraft
# All rights reserved.
#
# See LICENSE for licensing information

from abc import ABC, abstractmethod
from typing import Any
import pymysql
from rdfhelpers import Composable
from rdfhelpers.producers.common.interface import Generator, DatabaseConnectionMixin
from rdfhelpers.producers.common.utilities import parse_jdbc_url

try:
    import pymysql
    PYMYSQL = True
except ModuleNotFoundError:
    pymysql = None
    PYMYSQL = False

class MySQLGenerator(Generator, DatabaseConnectionMixin, ABC):
    def __init__(self, **kwargs):
        if not PYMYSQL:
            raise NotImplemented("Support for pyMySQL is not available")
        super().__init__(**kwargs)

    def produce(self, data: Composable, **kwargs) -> Composable:
        host, db, _ = parse_jdbc_url(self.connection_url)
        with pymysql.connect(host=host, user=self.user, password=self.passwd, db=db) as connection:
            return self.queries(data, connection)

    @abstractmethod
    def queries(self, data: Composable, connection) -> Composable:
        # Can call oneQuery as many times on the given connection
        ...

    def oneQuery(self, data, connection, query):
        with connection.cursor() as cursor:
            cursor.execute(query)
            while True:
                row = cursor.fetchone()
                if row:
                    data = self.perRow(data, row)
                else:
                    return data

    @abstractmethod
    def perRow(self, data: Composable, row: list[Any]) -> Composable:
        ...
