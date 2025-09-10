from __future__ import annotations

import sqlite3
from typing import Dict

from .base import Sink


class PgSink(Sink):
    """Simplified PostgreSQL sink using SQLite for tests."""

    def __init__(self, cfg: Dict) -> None:
        dsn: str = cfg.get("dsn", "sqlite:///crawler.db")
        if dsn.startswith("sqlite:///"):
            path = dsn.replace("sqlite:///", "")
        else:  # pragma: no cover - placeholder for real PG
            path = ":memory:"
        self.conn = sqlite3.connect(path)
        self.table = cfg.get("table", "items")
        self.upsert_keys = cfg.get("upsert_keys", [])
        self.columns = None

    def emit(self, item: dict) -> None:
        if self.columns is None:
            self.columns = list(item.keys())
            cols = ", ".join(f"{c} TEXT" for c in self.columns)
            unique = ", ".join(self.upsert_keys)
            self.conn.execute(
                f"CREATE TABLE IF NOT EXISTS {self.table} ({cols}, UNIQUE({unique}))"
            )
        placeholders = ", ".join(["?"] * len(self.columns))
        columns = ", ".join(self.columns)
        update = ", ".join(f"{c}=excluded.{c}" for c in self.columns)
        sql = (
            f"INSERT INTO {self.table} ({columns}) VALUES ({placeholders}) "
            f"ON CONFLICT({', '.join(self.upsert_keys)}) DO UPDATE SET {update}"
        )
        self.conn.execute(sql, [item.get(c) for c in self.columns])
        self.conn.commit()

