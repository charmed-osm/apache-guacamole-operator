#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

"""Module that includes functions to communicate with mysql."""
import logging

import ops.charm
import pymysql.cursors
from ops.framework import Object

logger = logging.getLogger(__name__)


class MysqlRequires(Object):
    """Requires side of a Mysql Endpoint."""

    mandatory_fields = ["host", "port", "user", "password", "root_password"]

    def __init__(
        self,
        charm: ops.charm.CharmBase,
        relation_name: str = "mysql",
    ):
        super().__init__(charm, "mysql")
        self.relation_name = relation_name
        self._update_relation()

    @property
    def host(self):
        """Mysql host."""
        return self._get_data_from_unit("host")

    @property
    def port(self):
        """Mysql port."""
        return self._get_data_from_unit("port")

    @property
    def user(self):
        """Mysql user."""
        return self._get_data_from_unit("user")

    @property
    def password(self):
        """Mysql password."""
        return self._get_data_from_unit("password")

    @property
    def database(self):
        """Mysql database."""
        return self._get_data_from_unit("database")

    def is_missing_data_in_unit(self):
        """Check if data is missing in the relation."""
        return not all([self._get_data_from_unit(field) for field in self.mandatory_fields])

    def _get_data_from_unit(self, key: str):
        if not self.relation:
            # This update relation doesn't seem to be needed, but I added it because apparently
            # the data is empty in the unit tests.
            # In reality, the constructor is called in every hook.
            # In the unit tests when doing an update_relation_data, apparently it is not called.
            self._update_relation()
        if self.relation:
            for unit in self.relation.units:
                data = self.relation.data[unit].get(key)
                if data:
                    return data

    def _update_relation(self):
        self.relation = self.model.get_relation(self.relation_name)


class Mysql:
    """Class to connect to mysql and execute sql queries."""

    def __init__(self, host, port, user, password, database) -> None:
        self._connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            cursorclass=pymysql.cursors.DictCursor,
        )
        self._queries = []

    def execute(self, sql: str):
        """Execute sql script."""
        queries = self._load_queries(sql)
        exception = None
        if queries:
            with self._connection:
                with self._connection.cursor() as cursor:
                    for query in queries.copy():
                        try:
                            cursor.execute(query)
                        except Exception as e:
                            if "Query was empty" not in str(e) and "already exists" not in str(e):
                                exception = e
                                break
                        queries.remove(query)
                self._connection.commit()
        if exception:
            logger.error(f"SQL syntax error in :{query}")
            raise exception

    def _load_queries(self, sql: str):
        sql_without_comments = ""
        for line in sql.splitlines():
            line_without_comment = self._remove_comment(line)
            if line_without_comment is not None:
                sql_without_comments += f"{line_without_comment}\n"
        return [f"{query};" for query in sql_without_comments.split(";") if sql_without_comments]

    def _remove_comment(self, line: str):
        uncommented_line = None
        if "--" not in line:
            uncommented_line = line
        else:
            uncommented_line = line.split("--")[0]
        if self._empty_string(uncommented_line):
            uncommented_line = None
        return uncommented_line

    def _empty_string(self, string):
        return not string or all(s == " " or s == "\n" for s in string)
