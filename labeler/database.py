import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "items.db"

VALID_LABELS = {
    "benchmark_claim",
    "data_quality_skepticism",
    "architecture_or_trace_analysis",
    "hype_or_reaction",
}

VALID_STATUS = {"unlabeled", "labeled", "skip", "needs_review"}


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


def insert_item(conn: sqlite3.Connection, data: dict) -> int:
    now = utc_now()
    status = data.get("status", "unlabeled")
    label = data.get("label")
    if status == "labeled" and not label:
        raise ValueError("labeled items require a label")
    if status == "needs_review" and not label:
        raise ValueError("needs_review items require a suggested label")

    cursor = conn.execute(
        """
        INSERT INTO items (
            platform, community, source_url, parent_id, created_utc, score,
            text, label, notes, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("platform") or "reddit",
            data.get("community"),
            data.get("source_url"),
            data.get("parent_id"),
            data.get("created_utc"),
            data.get("score"),
            data["text"].strip(),
            label,
            data.get("notes"),
            status,
            now,
            now,
        ),
    )
    return int(cursor.lastrowid)
