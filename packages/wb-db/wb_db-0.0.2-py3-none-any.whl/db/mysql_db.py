from __future__ import annotations

from typing import Any
from urllib.parse import urlparse, parse_qs

import pandas as pd
from pymysql import connect
from pymysql.connections import Connection
from pymysql.cursors import Cursor, SSCursor

from db.db import DB


class MysqlDB(DB):
    """
    import db

    mysql_db = db.MysqlDB.from_uri("mysql+pymysql://root:root@127.0.0.1:3306/db?charset=utf8mb4")

    mysql_db = db.MysqlDB(
        host="localhost",
        port=3306,
        username="root",
        password="root",
        dbname="db",
        charset="utf8mb4"
    )
    """

    def __init__(
            self,
            host: str = "localhost",
            port: int = 3306,
            username: str = "root",
            password: str = "",
            dbname: str | None = None,
            charset: str = "utf8mb4"
    ):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._dbname = dbname
        self._charset = charset

        self._connection: Connection | None = None
        self._cursor: Cursor | None = None

    def _open(self) -> None:
        self._connection, self._cursor = self.open_connect()

    def _close(self) -> None:
        self.close_connect(self._connection, self._cursor)

    @classmethod
    def from_uri(cls, uri: str) -> MysqlDB:
        parsed = urlparse(uri)
        return cls(
            **dict(
                host=parsed.hostname,
                port=parsed.port,
                username=parsed.username,
                password=parsed.password,
                dbname=parsed.path.lstrip("/"),
                charset=parse_qs(parsed.query).get("charset", ["utf8mb4"])[0]
            )
        )

    def open_connect(self) -> tuple[Connection, Cursor]:
        connection = connect(
            user=self._username,
            password=self._password,
            host=self._host,
            database=self._dbname,
            port=self._port,
            charset=self._charset,
            cursorclass=SSCursor
        )
        cursor = connection.cursor()
        return connection, cursor

    @staticmethod
    def close_connect(connection: Connection | None = None, cursor: Cursor | None = None) -> None:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()

    @property
    def connection(self) -> Connection:
        return self._connection

    @property
    def cursor(self) -> Cursor:
        return self._cursor

    def query(
            self,
            sql: str,
            param: tuple[Any, ...] | dict[str, Any] | None = None,
            connection_cursor: tuple[Connection, Cursor] | None = None,
            use_new_connect: bool = False,
            return_df: bool = False
    ) -> list[dict[str, Any]] | pd.DataFrame:
        if connection_cursor is not None:
            connection, cursor = connection_cursor
        else:
            if use_new_connect:
                connection_cursor = self.open_connect()
                connection, cursor = connection_cursor
            else:
                connection, cursor = self._connection, self._cursor

        cursor.execute(sql, param)
        result = cursor.fetchall()

        columns = [i[0] for i in cursor.description]
        rows = [dict(zip(columns, i)) for i in result]

        if connection_cursor is not None:
            self.close_connect(*connection_cursor)

        if return_df:
            return pd.DataFrame(rows)

        return rows

    def execute(
            self,
            sql: str,
            param: tuple[Any, ...] | dict[str, Any] | None = None,
            connection_cursor: tuple[Connection, Cursor] | None = None,
            use_new_connect: bool = False
    ) -> int:
        """
        # tuple[Any, ...]
        mysql_db.execute("SELECT * FROM users WHERE id=%s AND name=%s;", (1, "Alice"))

        # dict[str, Any]
        mysql_db.execute("INSERT INTO users (name, age) VALUES (%(name)s, %(age)s);", {"name": "Bob", "age": 25})

        # None
        mysql_db.execute("DELETE FROM users WHERE id=10;")


        Args:
            sql:
            param:
            connection_cursor:
            use_new_connect:

        Returns:

        """
        if connection_cursor is not None:
            connection, cursor = connection_cursor
        else:
            if use_new_connect:
                connection_cursor = self.open_connect()
                connection, cursor = connection_cursor
            else:
                connection, cursor = self._connection, self._cursor

        affected_rows = cursor.execute(sql, param)
        connection.commit()

        if connection_cursor is not None:
            self.close_connect(*connection_cursor)

        return affected_rows

    def executemany(
            self,
            sql: str,
            params: list[tuple[Any, ...]] | list[dict[str, Any]],
            connection_cursor: tuple[Connection, Cursor] | None = None,
            use_new_connect: bool = False
    ) -> int:
        """
        # list[tuple[Any, ...]]
        cursor.executemany(
            "INSERT INTO users (name, age) VALUES (%s, %s);",
            [("Alice", 20), ("Bob", 25)]
        )

        # list[dict[str, Any]]
        cursor.executemany(
            "INSERT INTO users (name, age) VALUES (%(name)s, %(age)s);",
            [{"name": "Alice", "age": 20}, {"name": "Bob", "age": 25}]
        )


        Args:
            sql:
            params:
            connection_cursor:
            use_new_connect:

        Returns:

        """
        if connection_cursor is not None:
            connection, cursor = connection_cursor
        else:
            if use_new_connect:
                connection_cursor = self.open_connect()
                connection, cursor = connection_cursor
            else:
                connection, cursor = self._connection, self._cursor

        affected_rows = cursor.executemany(sql, params)
        connection.commit()

        if connection_cursor is not None:
            self.close_connect(*connection_cursor)

        return affected_rows
