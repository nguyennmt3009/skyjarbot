"""
SQLite connection and schema initialisation.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path

_DB_PATH = Path(__file__).resolve().parent / "skyjarbot.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id   TEXT    NOT NULL,
    scenario_name TEXT    NOT NULL,
    started_at    TEXT    NOT NULL,
    finished_at   TEXT,
    success       INTEGER NOT NULL DEFAULT 0,
    total_steps   INTEGER NOT NULL DEFAULT 0,
    steps_done    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS run_steps (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    step_index  INTEGER NOT NULL,
    step_type   TEXT    NOT NULL,
    description TEXT    NOT NULL,
    started_at  TEXT    NOT NULL,
    finished_at TEXT,
    success     INTEGER NOT NULL DEFAULT 1,
    error_msg   TEXT    NOT NULL DEFAULT ''
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(_SCHEMA)
