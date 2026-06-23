#!/usr/bin/env python3
"""Import a pre-labeled CSV into labeler/items.db (no server required)."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELER = ROOT / "labeler"
sys.path.insert(0, str(LABELER))

from database import get_connection, init_db, insert_item  # noqa: E402
from import_utils import parse_csv_file, summarize_import  # noqa: E402


def import_rows(rows: list[dict]) -> int:
    init_db()
    with get_connection() as conn:
        for row in rows:
            insert_item(conn, row)
        conn.commit()
        total = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Import pre-labeled CSV into labeler DB")
    parser.add_argument(
        "csv_path",
        nargs="?",
        default=str(ROOT / "data" / "items_export_230_prelabeled.csv"),
        help="CSV to import (default: data/items_export_230_prelabeled.csv)",
    )
    parser.add_argument(
        "--prelabeled",
        action="store_true",
        default=True,
        help="Treat labeled rows as needs_review when AI pre-label notes present (default: on)",
    )
    parser.add_argument(
        "--no-prelabeled",
        action="store_true",
        help="Disable AI pre-label import rules",
    )
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Backup and delete labeler/items.db before import",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    db_path = LABELER / "items.db"
    if args.reset_db:
        if db_path.exists():
            backup = LABELER / "items.db.backup-before-import"
            shutil.copy2(db_path, backup)
            print(f"Backed up DB to {backup}")
            db_path.unlink()
            print("Removed old items.db")

    prelabeled = args.prelabeled and not args.no_prelabeled
    rows = parse_csv_file(str(csv_path), prelabeled=prelabeled)
    counts = summarize_import(rows)
    print(f"Importing {len(rows)} rows from {csv_path}")
    print("Status breakdown:", counts)

    total = import_rows(rows)
    print(f"Done. {total} items now in {db_path}")
    print("Start reviewer: cd labeler && ./run.sh")


if __name__ == "__main__":
    main()
