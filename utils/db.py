"""
utils/db.py
Kết nối và thao tác SQLite dùng chung.

Dùng:
    from utils.db import Database

    db = Database("data/app.db")
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
    db.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
    rows = db.fetchall("SELECT * FROM users")
    row  = db.fetchone("SELECT * FROM users WHERE id = ?", (1,))
    db.close()

    # Dùng context manager (tự đóng):
    with Database("data/app.db") as db:
        rows = db.fetchall("SELECT * FROM users")
"""
import sqlite3
import os
from pathlib import Path


class Database:
    def __init__(self, path: str = "data/app.db"):
        # Tự tạo thư mục nếu chưa có
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row   # truy cập theo tên cột
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")

    # ── Query ─────────────────────────────────────────────
    def fetchall(self, sql: str, params: tuple = ()) -> list[dict]:
        """Trả về list[dict] — mỗi dict là 1 dòng."""
        cur = self._conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]

    def fetchone(self, sql: str, params: tuple = ()) -> dict | None:
        """Trả về 1 dict hoặc None."""
        cur = self._conn.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None

    def execute(self, sql: str, params: tuple = ()) -> int:
        """Thực thi INSERT/UPDATE/DELETE. Trả về lastrowid."""
        cur = self._conn.execute(sql, params)
        self._conn.commit()
        return cur.lastrowid

    def executemany(self, sql: str, params_list: list[tuple]) -> None:
        """Thực thi nhiều lần — dùng khi insert nhiều dòng."""
        self._conn.executemany(sql, params_list)
        self._conn.commit()

    def execute_script(self, script: str) -> None:
        """Thực thi nhiều câu SQL (dùng khi tạo schema)."""
        self._conn.executescript(script)
        self._conn.commit()

    # ── Transaction ───────────────────────────────────────
    def begin(self):
        self._conn.execute("BEGIN")

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    # ── Helpers ───────────────────────────────────────────
    def table_exists(self, table_name: str) -> bool:
        row = self.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return row is not None

    def count(self, table: str, where: str = "", params: tuple = ()) -> int:
        sql = f"SELECT COUNT(*) as n FROM {table}"
        if where:
            sql += f" WHERE {where}"
        row = self.fetchone(sql, params)
        return row["n"] if row else 0

    def last_insert_id(self) -> int:
        row = self.fetchone("SELECT last_insert_rowid() as id")
        return row["id"] if row else 0

    # ── Lifecycle ─────────────────────────────────────────
    def close(self):
        if self._conn:
            self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
