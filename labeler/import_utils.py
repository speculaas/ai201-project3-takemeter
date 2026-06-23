"""Shared CSV import logic for labeler API and CLI scripts."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from database import VALID_LABELS, VALID_STATUS

OLD_LABELS = {
    "architecture_analysis",
    "trace_methodology",
}


def parse_score(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(float(value))


def is_ai_prelabeled(notes: str | None) -> bool:
    if not notes:
        return False
    lower = notes.lower()
    return "ai pre-label" in lower or "pre-label" in lower


def resolve_import_status(row: dict[str, Any], *, prelabeled: bool = False) -> str:
    explicit = (row.get("status") or "").strip().lower()
    label = (row.get("label") or "").strip() or None
    notes = row.get("notes") or ""

    if explicit == "labeled_reviewed":
        return "labeled" if label else "unlabeled"
    if explicit == "skip":
        return "skip"
    if explicit == "needs_review":
        return "needs_review" if label else "unlabeled"
    if explicit == "unlabeled":
        return "unlabeled"
    if explicit == "labeled":
        if prelabeled or is_ai_prelabeled(notes):
            return "needs_review" if label else "unlabeled"
        return "labeled" if label else "unlabeled"

    if not label:
        return "unlabeled"

    if prelabeled or is_ai_prelabeled(notes):
        return "needs_review"

    # Training-style export with labels but no status column.
    return "needs_review"


def normalize_import_row(row: dict[str, Any], *, prelabeled: bool = False) -> dict[str, Any]:
    item_id = row.get("item_id") or row.get("comment_id") or row.get("id")
    parent_id = row.get("parent_id") or ""
    if parent_id == "":
        parent_id = None

    label = (row.get("label") or "").strip() or None
    if label and label not in VALID_LABELS:
        if label in OLD_LABELS:
            label = "architecture_or_trace_analysis"
        else:
            raise ValueError(f"invalid label: {label}")

    status = resolve_import_status(row, prelabeled=prelabeled)
    if status == "labeled" and not label:
        raise ValueError("labeled status requires a label")

    return {
        "platform": row.get("platform") or "reddit",
        "community": row.get("community") or row.get("subreddit"),
        "source_url": row.get("source_url") or row.get("permalink"),
        "parent_id": parent_id,
        "created_utc": row.get("created_utc"),
        "score": parse_score(row.get("score")),
        "text": (row.get("text") or "").strip(),
        "label": label,
        "notes": row.get("notes"),
        "status": status,
        "external_id": str(item_id) if item_id not in (None, "") else None,
    }


def parse_bulk_content(
    content: str,
    fmt: str,
    *,
    prelabeled: bool = False,
) -> list[dict[str, Any]]:
    content = content.strip()
    if not content:
        return []

    rows: list[dict[str, Any]] = []

    if fmt == "auto":
        fmt = "jsonl" if content.lstrip().startswith("{") else "csv"

    if fmt == "jsonl":
        for line_no, line in enumerate(content.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSONL line {line_no}: {exc}") from exc
            if not row.get("text"):
                continue
            rows.append(normalize_import_row(row, prelabeled=prelabeled))
        return rows

    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise ValueError("CSV has no header row")
    for row in reader:
        if not (row.get("text") or "").strip():
            continue
        rows.append(normalize_import_row(row, prelabeled=prelabeled))
    return rows


def parse_csv_file(path: str, *, prelabeled: bool = False) -> list[dict[str, Any]]:
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows: list[dict[str, Any]] = []
        for row in reader:
            if not (row.get("text") or "").strip():
                continue
            rows.append(normalize_import_row(row, prelabeled=prelabeled))
        return rows


def summarize_import(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {status: 0 for status in VALID_STATUS}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return counts
