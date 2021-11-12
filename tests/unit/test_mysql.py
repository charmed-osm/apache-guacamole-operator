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
    # Mocks and creation of mysql object
    cursor_mock = mocker.Mock()
    cursor_mock.__enter__ = cursor_mock
    cursor_mock.__exit__ = cursor_mock
    connection_mock = mocker.Mock()
    connection_mock.cursor.return_value = cursor_mock
    connection_mock.__enter__ = connection_mock
    connection_mock.__exit__ = connection_mock
    pymysql_mock = mocker.patch("mysql.pymysql")
    pymysql_mock.connect.return_value = connection_mock
    mysql = Mysql("host", "3306", "user", "password", "db")
    # Test empty SQL
    mysql.execute("")
    assert mysql._connection.commit.call_count == 0
    # Test not-empty SQL, and exceptions that can be ignored
    pymysql_mock.connect().cursor()().execute.side_effect = [
        Exception("(0, Query was empty"),
        None,
        Exception("Table guacamole already exists."),
    ]
    mysql.execute(SQL_SCRIPT)
    assert mysql._connection.commit.call_count == 1
    # Test unknown exceptions
    try:
        pymysql_mock.connect().cursor()().execute.side_effect = Exception("Unknown")
        mysql.execute(SQL_SCRIPT)
        assert False
    except Exception as e:
        assert str(e) == "Unknown"
