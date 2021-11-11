#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

from pytest_mock import MockerFixture

from mysql import Mysql

SQL_SCRIPT = """
something;
-- comment

  -- comment
something else; -- comment
"""


def test_mysql(mocker: MockerFixture):
    pymysql_mock = mocker.patch("mysql.pymysql")
    mysql = Mysql("host", "3306", "user", "password", "db")
    mysql.execute("")
    assert mysql._connection.commit.call_count == 0
    cursor_mock = mocker.Mock()
    cursor_mock.__enter__ = cursor_mock
    cursor_mock.__exit__ = cursor_mock
    pymysql_mock.connect().cursor()().execute.side_effect = [
        Exception("(0, Query was empty"),
        None,
        Exception("Table guacamole already exists."),
    ]

    mysql._connection.cursor.return_value = cursor_mock
    mysql.execute(SQL_SCRIPT)
    assert mysql._connection.commit.call_count == 1
