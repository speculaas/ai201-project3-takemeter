from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from database import (
    VALID_LABELS,
    VALID_STATUS,
    get_connection,
    init_db,
    insert_item,
    row_to_dict,
    utc_now,
)
from import_utils import parse_bulk_content, summarize_import

app = FastAPI(title="AgentTraceTakeMeter Labeler")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ItemCreate(BaseModel):
    platform: str = "reddit"
    community: Optional[str] = None
    source_url: Optional[str] = None
    parent_id: Optional[str] = None
    created_utc: Optional[str] = None
    score: Optional[int] = None
    text: str
    label: Optional[str] = None
    notes: Optional[str] = None
    status: str = "unlabeled"

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("text is required")
        return value.strip()

    @field_validator("label")
    @classmethod
    def valid_label(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in VALID_LABELS:
            raise ValueError(f"invalid label: {value}")
        return value

    @field_validator("status")
    @classmethod
    def valid_status(cls, value: str) -> str:
        if value not in VALID_STATUS:
            raise ValueError(f"invalid status: {value}")
        return value


class ItemUpdate(BaseModel):
    platform: Optional[str] = None
    community: Optional[str] = None
    source_url: Optional[str] = None
    parent_id: Optional[str] = None
    created_utc: Optional[str] = None
    score: Optional[int] = None
    text: Optional[str] = None
    label: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("text cannot be empty")
        return value.strip() if value is not None else value

    @field_validator("label")
    @classmethod
    def valid_label(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in VALID_LABELS:
            raise ValueError(f"invalid label: {value}")
        return value

    @field_validator("status")
    @classmethod
    def valid_status(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in VALID_STATUS:
            raise ValueError(f"invalid status: {value}")
        return value


class BulkImport(BaseModel):
    content: str
    format: str = Field(default="auto", pattern="^(auto|jsonl|csv)$")
    dry_run: bool = False
    prelabeled: bool = False


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/labels")
def list_labels() -> dict[str, list[str]]:
    return {"labels": sorted(VALID_LABELS)}


@app.get("/api/items")
def list_items(
    status: Optional[str] = None,
    label: Optional[str] = None,
    search: Optional[str] = None,
) -> list[dict]:
    clauses: list[str] = []
    params: list[Any] = []

    if status:
        if status not in VALID_STATUS:
            raise HTTPException(400, f"invalid status: {status}")
        clauses.append("status = ?")
        params.append(status)
    if label:
        if label not in VALID_LABELS:
            raise HTTPException(400, f"invalid label: {label}")
        clauses.append("label = ?")
        params.append(label)
    if search:
        clauses.append("(text LIKE ? OR notes LIKE ? OR source_url LIKE ?)")
        pattern = f"%{search}%"
        params.extend([pattern, pattern, pattern])

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"SELECT * FROM items {where} ORDER BY id ASC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [row_to_dict(r) for r in rows]


@app.get("/api/items/next")
def next_item(
    after_id: int = Query(default=0),
    mode: str = Query(default="review_first"),
) -> Optional[dict]:
    if mode not in {"review_first", "needs_review", "unlabeled"}:
        raise HTTPException(400, f"invalid mode: {mode}")

    statuses: list[str]
    if mode == "needs_review":
        statuses = ["needs_review"]
    elif mode == "unlabeled":
        statuses = ["unlabeled"]
    else:
        statuses = ["needs_review", "unlabeled"]

    with get_connection() as conn:
        for status in statuses:
            row = conn.execute(
                """
                SELECT * FROM items
                WHERE status = ? AND id > ?
                ORDER BY id ASC
                LIMIT 1
                """,
                (status, after_id),
            ).fetchone()
            if row:
                return row_to_dict(row)
            row = conn.execute(
                """
                SELECT * FROM items
                WHERE status = ?
                ORDER BY id ASC
                LIMIT 1
                """,
                (status,),
            ).fetchone()
            if row:
                return row_to_dict(row)
    return None


@app.get("/api/items/{item_id}")
def get_item(item_id: int) -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if not row:
        raise HTTPException(404, "item not found")
    return row_to_dict(row)


@app.post("/api/items", status_code=201)
def create_item(payload: ItemCreate) -> dict:
    with get_connection() as conn:
        item_id = insert_item(conn, payload.model_dump())
        conn.commit()
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    return row_to_dict(row)


@app.post("/api/items/bulk")
def bulk_import(payload: BulkImport) -> dict:
    try:
        rows = parse_bulk_content(
            payload.content,
            payload.format,
            prelabeled=payload.prelabeled,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    status_counts = summarize_import(rows)
    if payload.dry_run:
        return {
            "dry_run": True,
            "count": len(rows),
            "status_counts": status_counts,
            "preview": rows[:10],
        }

    inserted = 0
    with get_connection() as conn:
        for row in rows:
            insert_item(conn, row)
            inserted += 1
        conn.commit()
    return {"inserted": inserted}


@app.patch("/api/items/{item_id}")
def update_item(item_id: int, payload: ItemUpdate) -> dict:
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "no fields to update")

    if updates.get("status") == "labeled" and not updates.get("label"):
        with get_connection() as conn:
            existing = conn.execute(
                "SELECT label FROM items WHERE id = ?", (item_id,)
            ).fetchone()
        if not existing or not existing["label"]:
            raise HTTPException(400, "labeled status requires a label")

    if updates.get("status") == "needs_review" and not updates.get("label"):
        with get_connection() as conn:
            existing = conn.execute(
                "SELECT label FROM items WHERE id = ?", (item_id,)
            ).fetchone()
        if not existing or not existing["label"]:
            raise HTTPException(400, "needs_review status requires a label")

    updates["updated_at"] = utc_now()
    set_clause = ", ".join(f"{key} = ?" for key in updates)
    values = list(updates.values()) + [item_id]

    with get_connection() as conn:
        cur = conn.execute(
            f"UPDATE items SET {set_clause} WHERE id = ?", values
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "item not found")
        conn.commit()
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    return row_to_dict(row)


@app.delete("/api/items/{item_id}")
def delete_item(item_id: int) -> dict:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "item not found")
        conn.commit()
    return {"deleted": item_id}


@app.get("/api/stats")
def stats() -> dict:
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        labeled = conn.execute(
            "SELECT COUNT(*) FROM items WHERE status = 'labeled'"
        ).fetchone()[0]
        unlabeled = conn.execute(
            "SELECT COUNT(*) FROM items WHERE status = 'unlabeled'"
        ).fetchone()[0]
        skipped = conn.execute(
            "SELECT COUNT(*) FROM items WHERE status = 'skip'"
        ).fetchone()[0]
        needs_review = conn.execute(
            "SELECT COUNT(*) FROM items WHERE status = 'needs_review'"
        ).fetchone()[0]

        by_label = {label: 0 for label in VALID_LABELS}
        for row in conn.execute(
            "SELECT label, COUNT(*) AS c FROM items WHERE label IS NOT NULL GROUP BY label"
        ):
            by_label[row["label"]] = row["c"]

        by_status = {
            "unlabeled": unlabeled,
            "needs_review": needs_review,
            "labeled": labeled,
            "skip": skipped,
        }

    review_total = needs_review + unlabeled
    progress = round((labeled / total) * 100, 1) if total else 0.0
    return {
        "total": total,
        "labeled": labeled,
        "unlabeled": unlabeled,
        "needs_review": needs_review,
        "skipped": skipped,
        "review_remaining": review_total,
        "by_label": by_label,
        "by_status": by_status,
        "progress_percent": progress,
    }


@app.post("/api/deduplicate")
def deduplicate(remove: bool = Query(default=False)) -> dict:
    with get_connection() as conn:
        dup_text = conn.execute(
            """
            SELECT text, COUNT(*) AS c FROM items
            GROUP BY text HAVING c > 1
            """
        ).fetchall()
        dup_url = conn.execute(
            """
            SELECT source_url, COUNT(*) AS c FROM items
            WHERE source_url IS NOT NULL AND source_url != ''
            GROUP BY source_url HAVING c > 1
            """
        ).fetchall()

        removed = 0
        if remove:
            conn.execute(
                """
                DELETE FROM items
                WHERE id NOT IN (
                    SELECT MIN(id) FROM items GROUP BY text
                )
                """
            )
            removed += conn.total_changes
            conn.execute(
                """
                DELETE FROM items
                WHERE source_url IS NOT NULL AND source_url != ''
                AND id NOT IN (
                    SELECT MIN(id) FROM items
                    WHERE source_url IS NOT NULL AND source_url != ''
                    GROUP BY source_url
                )
                """
            )
            removed += conn.total_changes
            conn.commit()

    return {
        "duplicate_text_groups": len(dup_text),
        "duplicate_url_groups": len(dup_url),
        "removed": removed if remove else 0,
        "dry_run": not remove,
    }


def csv_response(filename: str, rows: list[dict], fieldnames: list[str]) -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/export/csv")
def export_all() -> StreamingResponse:
    with get_connection() as conn:
        rows = [row_to_dict(r) for r in conn.execute("SELECT * FROM items ORDER BY id")]
    fields = [
        "id", "platform", "community", "source_url", "parent_id", "created_utc",
        "score", "text", "label", "notes", "status", "created_at", "updated_at",
    ]
    return csv_response("items_export.csv", rows, fields)


@app.get("/api/export/training_csv")
def export_training() -> StreamingResponse:
    with get_connection() as conn:
        rows = [
            row_to_dict(r)
            for r in conn.execute(
                """
                SELECT id, text, label, notes, source_url, parent_id, platform, community
                FROM items
                WHERE status = 'labeled' AND label IS NOT NULL
                ORDER BY id
                """
            )
        ]
    fields = [
        "text", "label", "notes", "source_url", "id",
        "platform", "community", "parent_id",
    ]
    return csv_response("training_export.csv", rows, fields)


static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
