import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "items.db"

VALID_LABELS = {
    "benchmark_claim",
    "data_quality_skepticism",
    "architecture_analysis",
    "trace_methodology",
    "hype_or_reaction",
}

VALID_STATUS = {"unlabeled", "labeled", "skip"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL DEFAULT 'reddit',
                community TEXT,
                source_url TEXT,
                parent_id TEXT,
                created_utc TEXT,
                score INTEGER,
                text TEXT NOT NULL,
                label TEXT,
                notes TEXT,
                status TEXT NOT NULL DEFAULT 'unlabeled',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)
