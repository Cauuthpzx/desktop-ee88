"""
utils/db.py
Ket noi va thao tac PostgreSQL dung chung.

Dung:
    from utils.db import Database

    db = Database()                     # doc tu .env
    db.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name TEXT)")
    db.execute("INSERT INTO users (name) VALUES (%s)", ("Alice",))
    rows = db.fetchall("SELECT * FROM users")
    row  = db.fetchone("SELECT * FROM users WHERE id = %s", (1,))
    db.close()

    # Dung context manager (tu dong):
    with Database() as db:
        rows = db.fetchall("SELECT * FROM users")

Luu y:
    - Parameterized query dung %s (khong dung ? nhu SQLite)
    - .env file phai co: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""
from __future__ import annotations

import os
import logging

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _get_dsn() -> str:
    """Build DSN tu bien moi truong."""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "maxhub")
    user = os.getenv("DB_USER", "postgres")
    pwd  = os.getenv("DB_PASSWORD", "")
    return f"host={host} port={port} dbname={name} user={user} password={pwd}"


class Database:
    """PostgreSQL database wrapper — same API as old SQLite version."""

    def __init__(self, dsn: str | None = None):
        self._dsn = dsn or _get_dsn()
        self._conn = psycopg.connect(self._dsn, row_factory=dict_row, autocommit=True)

    # -- Query --------------------------------------------------------
    def fetchall(self, sql: str, params: tuple = ()) -> list[dict]:
        """Tra ve list[dict] — moi dict la 1 dong."""
        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def fetchone(self, sql: str, params: tuple = ()) -> dict | None:
        """Tra ve 1 dict hoac None."""
        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()

    def execute(self, sql: str, params: tuple = ()) -> int:
        """Thuc thi INSERT/UPDATE/DELETE. Tra ve so dong bi anh huong."""
        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.rowcount

    def execute_returning(self, sql: str, params: tuple = ()) -> dict | None:
        """Thuc thi INSERT ... RETURNING *. Tra ve dong vua insert."""
        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()

    def executemany(self, sql: str, params_list: list[tuple]) -> None:
        """Thuc thi nhieu lan — dung khi insert nhieu dong."""
        with self._conn.cursor() as cur:
            cur.executemany(sql, params_list)

    def execute_script(self, script: str) -> None:
        """Thuc thi nhieu cau SQL (dung khi tao schema)."""
        with self._conn.cursor() as cur:
            cur.execute(script)

    # -- Transaction --------------------------------------------------
    def begin(self) -> None:
        """Bat dau transaction (tat autocommit tam thoi)."""
        self._conn.autocommit = False

    def commit(self) -> None:
        self._conn.commit()
        self._conn.autocommit = True

    def rollback(self) -> None:
        self._conn.rollback()
        self._conn.autocommit = True

    # -- Helpers ------------------------------------------------------
    def table_exists(self, table_name: str) -> bool:
        row = self.fetchone(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = %s) AS ok",
            (table_name,),
        )
        return row["ok"] if row else False

    def count(self, table: str, where: str = "", params: tuple = ()) -> int:
        sql = f"SELECT COUNT(*) AS n FROM {table}"
        if where:
            sql += f" WHERE {where}"
        row = self.fetchone(sql, params)
        return row["n"] if row else 0

    # -- Lifecycle ----------------------------------------------------
    def close(self) -> None:
        if self._conn and not self._conn.closed:
            self._conn.close()

    def __enter__(self) -> Database:
        return self

    def __exit__(self, *_) -> None:
        self.close()
