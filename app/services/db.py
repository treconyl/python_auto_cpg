from __future__ import annotations

import random
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable

from app.config import settings


def ensure_paths() -> None:
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or settings.DB_PATH
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL;")
    connection.execute(f"PRAGMA busy_timeout = {settings.DB_BUSY_TIMEOUT_MS};")
    return connection


@contextmanager
def session() -> Iterable[sqlite3.Connection]:
    connection = connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def execute_with_retry(connection: sqlite3.Connection, sql: str, params: tuple | None = None) -> sqlite3.Cursor:
    attempts = 0
    params = params or ()

    while True:
        try:
            return connection.execute(sql, params)
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc).lower():
                raise
            attempts += 1
            if attempts >= settings.DB_RETRY_COUNT:
                raise
            delay = random.uniform(settings.DB_RETRY_MIN_DELAY, settings.DB_RETRY_MAX_DELAY)
            time.sleep(delay)


def migrate() -> None:
    with session() as connection:
        execute_with_retry(
            connection,
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                login TEXT UNIQUE NOT NULL,
                current_password TEXT,
                next_password TEXT,
                status TEXT DEFAULT 'pending',
                last_error TEXT,
                last_attempted_at TEXT,
                last_succeeded_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """.strip(),
        )
        execute_with_retry(
            connection,
            """
            CREATE TABLE IF NOT EXISTS proxy_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                api_key TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                last_used_at TEXT,
                status TEXT DEFAULT 'idle',
                stop_requested INTEGER DEFAULT 0,
                meta TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """.strip(),
        )
        execute_with_retry(
            connection,
            """
            CREATE TABLE IF NOT EXISTS garena_test_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER,
                proxy_key_id INTEGER,
                username TEXT,
                password TEXT,
                new_password TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """.strip(),
        )
