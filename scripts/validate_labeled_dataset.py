#!/usr/bin/env python3
"""Validate a labeled training CSV before notebook upload."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

VALID_LABELS = {
    "benchmark_claim",
    "data_quality_skepticism",
    "architecture_or_trace_analysis",
    "hype_or_reaction",
}
OLD_LABELS = {"architecture_analysis", "trace_methodology"}
MIN_ROWS = 200
MAX_LABEL_PCT = 0.70


def validate(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    errors: list[str] = []
    if not rows:
        errors.append("CSV is empty")
        return report(errors, rows)

    labeled_rows = rows
    if "status" in rows[0]:
        labeled_rows = [r for r in rows if (r.get("status") or "").strip() == "labeled"]
        other_status = Counter((r.get("status") or "missing").strip() for r in rows)
        print("Rows by status:", dict(other_status))

    if len(labeled_rows) < MIN_ROWS:
        errors.append(f"Fewer than {MIN_ROWS} labeled rows ({len(labeled_rows)})")

    labels = Counter()
    dup_text = 0
    seen_text: set[str] = set()

    for i, row in enumerate(labeled_rows, start=2):
        text = (row.get("text") or "").strip()
        label = (row.get("label") or "").strip()

        if not text:
            errors.append(f"Row {i}: missing text")
            continue
        if text in seen_text:
            dup_text += 1
        seen_text.add(text)

        if not label:
            errors.append(f"Row {i}: missing label")
            continue
        if label in OLD_LABELS:
            errors.append(f"Row {i}: old label {label}")
        elif label not in VALID_LABELS:
            errors.append(f"Row {i}: invalid label {label}")
        else:
            labels[label] += 1

    print(f"\nFile: {path}")
    print(f"Labeled rows: {len(labeled_rows)}")
    print(f"Duplicate text rows: {dup_text}")
    print("\nLabel counts:")
    for label in sorted(VALID_LABELS):
        count = labels.get(label, 0)
        pct = (count / len(labeled_rows) * 100) if labeled_rows else 0
        print(f"  {label}: {count} ({pct:.1f}%)")
        if labeled_rows and pct > MAX_LABEL_PCT * 100:
            errors.append(
                f"Label {label} exceeds {int(MAX_LABEL_PCT * 100)}% of dataset ({pct:.1f}%)"
            )

    return report(errors, labeled_rows)


def report(errors: list[str], rows: list[dict]) -> int:
    if errors:
        print("\nValidation FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("\nValidation passed.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "csv_path",
        nargs="?",
        default="data/labeled_dataset.csv",
        help="CSV to validate",
    )
    args = parser.parse_args()
    sys.exit(validate(Path(args.csv_path)))


if __name__ == "__main__":
    main()
