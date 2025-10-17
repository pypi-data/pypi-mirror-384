from __future__ import annotations

from urllib.parse import urlparse, parse_qs

from pymysql import connect
from pymysql.connections import Connection
from pymysql.cursors import Cursor, DictCursor

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
            cursorclass=DictCursor
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
