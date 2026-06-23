#!/usr/bin/env python3
"""Build final training CSV from a reviewed labeler export."""

from __future__ import annotations

import argparse
import csv
import random
import sys
from collections import Counter
from pathlib import Path

VALID_LABELS = {
    "benchmark_claim",
    "data_quality_skepticism",
    "architecture_or_trace_analysis",
    "hype_or_reaction",
}
OUTPUT_FIELDS = [
    "text", "label", "notes", "source_url", "id",
    "platform", "community", "parent_id",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--input",
        default="data/items_export_230_prelabeled.csv",
        help="Labeler export or reviewed CSV",
    )
    parser.add_argument(
        "-o", "--output",
        default="data/labeled_dataset.csv",
        help="Output training CSV",
    )
    parser.add_argument(
        "--max-per-label",
        type=int,
        default=0,
        help="Optional cap per label (0 = no cap)",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    if not in_path.exists():
        raise SystemExit(f"Input not found: {in_path}")

    with in_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    kept: list[dict] = []
    for row in rows:
        status = (row.get("status") or "labeled").strip()
        label = (row.get("label") or "").strip()
        text = (row.get("text") or "").strip()
        if status != "labeled" or not label or not text:
            continue
        if label not in VALID_LABELS:
            print(f"Skipping invalid label: {label}", file=sys.stderr)
            continue
        kept.append(row)

    if args.max_per_label > 0:
        rng = random.Random(args.seed)
        by_label: dict[str, list[dict]] = {label: [] for label in VALID_LABELS}
        for row in kept:
            by_label[row["label"]].append(row)
        capped: list[dict] = []
        for label, group in by_label.items():
            rng.shuffle(group)
            capped.extend(group[: args.max_per_label])
        kept = capped

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in kept:
            writer.writerow(row)

    counts = Counter(row["label"] for row in kept)
    print(f"Wrote {len(kept)} rows to {out_path}")
    print("Label distribution:")
    for label in sorted(VALID_LABELS):
        print(f"  {label}: {counts.get(label, 0)}")


if __name__ == "__main__":
    main()
