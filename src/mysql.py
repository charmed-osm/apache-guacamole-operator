#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

"""Module that includes functions to communicate with mysql."""
import logging

import pymysql.cursors

logger = logging.getLogger(__name__)


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
        if queries:
            with self._connection:
                with self._connection.cursor() as cursor:
                    for query in queries.copy():
                        try:
                            cursor.execute(query)
                        except Exception as e:
                            if "Query was empty" not in str(e) and "already exists" not in str(e):
                                logger.error(f"SQL syntax error in :{query}")
                                raise e
                        queries.remove(query)
                self._connection.commit()

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
