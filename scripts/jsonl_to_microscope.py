#!/usr/bin/env python3
"""Convert a Claude Code session .jsonl into a microscope session package.

Claude Code stores a conversation as JSON Lines (one record per line) under
~/.claude/projects/<encoded-cwd>/<session-uuid>.jsonl. The microscope viewer in
docs/microscope.html expects a single "session package" JSON of the shape
{ "session_id": ..., "events": [ {id, parentId, type:"message", message}, ... ] }
listed in docs/fable/sessions.index.json.

This script does that conversion (stdlib only) and updates the index.

It is READ-ONLY on the source .jsonl. It writes two things:
  docs/fable/sessions/<session_id>.json   (the package)
  docs/fable/sessions.index.json          (adds/replaces one entry)

Usage:
  python scripts/jsonl_to_microscope.py path/to/session.jsonl
  python scripts/jsonl_to_microscope.py session.jsonl --session-id my-chat --title "Export dialog work"
  python scripts/jsonl_to_microscope.py session.jsonl --include-sidechains
  python scripts/jsonl_to_microscope.py session.jsonl --out-dir /some/other/docs/fable
"""
import argparse
import json
import sys
from pathlib import Path

# Conversation lives only in these record types; everything else is harness
# bookkeeping (ai-title, mode, queue-operation, last-prompt, system, attachment).
CONVO_TYPES = {"user", "assistant"}


def iter_records(jsonl_path):
    """Yield parsed JSON objects, tolerating blank lines / a trailing partial line."""
    with open(jsonl_path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"  ! skipping unparseable line {lineno}: {exc}", file=sys.stderr)


def convert_block(block):
    """Map a Claude content block to a microscope-friendly block.

    text -> text, thinking -> thinking, tool_use -> toolCall, tool_result -> toolResult.
    A `text` summary is added to tool blocks so transcript/sequence previews read well.
    """
    if not isinstance(block, dict):
        return {"type": "text", "text": str(block)}
    btype = block.get("type")
    if btype == "text":
        return {"type": "text", "text": block.get("text", "")}
    if btype == "thinking":
        return {"type": "thinking", "thinking": block.get("thinking", "")}
    if btype == "tool_use":
        name = block.get("name", "tool")
        inp = block.get("input", {})
        return {
            "type": "toolCall",
            "name": name,
            "input": inp,
            "id": block.get("id"),
            "text": f"{name}({json.dumps(inp, ensure_ascii=False)[:200]})",
        }
    if btype == "tool_result":
        content = block.get("content")
        text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
        return {
            "type": "toolResult",
            "tool_use_id": block.get("tool_use_id"),
            "text": text[:2000],
            "raw": content,
        }
    # Unknown block: keep it, give it a text preview.
    return {"type": btype or "unknown", "text": json.dumps(block, ensure_ascii=False)[:400], "raw": block}


def convert_message(message):
    """Normalize message.content (string or list) into a list of converted blocks."""
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    if isinstance(content, str):
        blocks = [{"type": "text", "text": content}]
    elif isinstance(content, list):
        blocks = [convert_block(b) for b in content]
    else:
        blocks = []
    return {"role": message.get("role"), "content": blocks}


def build_events(records, include_sidechains):
    # First pass: keep conversational records, collect their uuids.
    kept = []
    for rec in records:
        if rec.get("type") not in CONVO_TYPES:
            continue
        if rec.get("isSidechain") and not include_sidechains:
            continue
        if not isinstance(rec.get("message"), dict):
            continue
        kept.append(rec)

    kept_ids = {rec.get("uuid") for rec in kept if rec.get("uuid")}

    events = []
    for rec in kept:
        parent = rec.get("parentUuid")
        # Re-root any record whose parent we filtered out, so the tree has no dangling edges.
        if parent not in kept_ids:
            parent = None
        events.append({
            "type": "message",
            "id": rec.get("uuid"),
            "parentId": parent,
            "timestamp": rec.get("timestamp"),
            "cwd": rec.get("cwd"),
            "isSidechain": bool(rec.get("isSidechain")),
            "message": convert_message(rec.get("message")),
            "version": rec.get("version"),
        })
    return events


def first_user_text(events):
    for ev in events:
        msg = ev.get("message") or {}
        if msg.get("role") == "user":
            for blk in msg.get("content", []):
                if blk.get("type") == "text" and blk.get("text", "").strip():
                    return blk["text"].strip()
    return None


def update_index(index_path, entry):
    index = []
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"  ! {index_path} was not valid JSON; starting a fresh index", file=sys.stderr)
            index = []
    if not isinstance(index, list):
        index = []
    index = [e for e in index if e.get("session_id") != entry["session_id"]]
    index.append(entry)
    index.sort(key=lambda e: e.get("session_id", ""))
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("jsonl", help="Path to the Claude Code session .jsonl")
    parser.add_argument("--session-id", help="Session id (default: source filename stem)")
    parser.add_argument("--title", help="Human title shown in the sidebar")
    parser.add_argument("--model", default=None, help="Model id to record (optional)")
    parser.add_argument("--include-sidechains", action="store_true",
                        help="Include sub-agent (Agent/Task) records too")
    parser.add_argument("--out-dir", default=None,
                        help="docs/fable directory (default: <repo>/docs/fable next to this script)")
    args = parser.parse_args(argv)

    jsonl_path = Path(args.jsonl).expanduser()
    if not jsonl_path.is_file():
        parser.error(f"no such file: {jsonl_path}")

    out_dir = Path(args.out_dir).expanduser() if args.out_dir \
        else Path(__file__).resolve().parent.parent / "docs" / "fable"
    sessions_dir = out_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    session_id = args.session_id or jsonl_path.stem
    # Filesystem-safe id.
    safe_id = "".join(c if (c.isalnum() or c in "-_.") else "-" for c in session_id).strip("-") or "session"

    records = list(iter_records(jsonl_path))
    events = build_events(records, args.include_sidechains)
    if not events:
        parser.error("no conversational (user/assistant) records found — nothing to convert")

    num_messages = sum(1 for e in events if e.get("message"))
    title = args.title or first_user_text(events) or session_id
    if len(title) > 80:
        title = title[:77] + "..."

    package = {
        "session_id": safe_id,
        "title": title,
        "source": str(jsonl_path),
        "model": args.model,
        "events": events,
    }
    pkg_path = sessions_dir / f"{safe_id}.json"
    pkg_path.write_text(json.dumps(package, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    index_path = out_dir / "sessions.index.json"
    update_index(index_path, {
        "session_id": safe_id,
        "title": title,
        "model": args.model,
        "thinkingLevel": None,
        "num_events": len(events),
        "num_messages": num_messages,
        "sample": False,
        "path": f"fable/sessions/{safe_id}.json",
    })

    print(f"Wrote {pkg_path}")
    print(f"Updated {index_path}")
    print(f"  session_id={safe_id}  events={len(events)}  messages={num_messages}")
    print(f"  title: {title}")
    print("\nView it:")
    print(f"  cd {out_dir.parent}")
    print("  python3 -m http.server 8000")
    print("  open http://localhost:8000/microscope.html")


if __name__ == "__main__":
    main()
