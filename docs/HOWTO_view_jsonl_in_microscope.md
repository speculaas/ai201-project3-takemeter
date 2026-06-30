# How to view a Claude Code `.jsonl` in the Trace Microscope

The microscope (`docs/microscope.html`) inspects **session packages**, not raw
Claude Code transcripts. A Claude Code conversation is **JSON Lines** (one record
per line) at `~/.claude/projects/<encoded-cwd>/<session-uuid>.jsonl`. Use the
converter to turn one into a package the microscope can load.

## 1. Convert the `.jsonl`

```bash
# from the repo root
python3 scripts/jsonl_to_microscope.py /path/to/<session-uuid>.jsonl \
  --session-id my-chat \
  --title "What this conversation was about"
```

This writes:

- `docs/fable/sessions/my-chat.json` — the session package
- `docs/fable/sessions.index.json` — adds/replaces the entry for `my-chat`

The script is **read-only** on the source `.jsonl`. Re-running with the same
`--session-id` overwrites that one package/entry and leaves others untouched.

Useful flags:

| flag | effect |
|------|--------|
| `--session-id <id>` | id + filename (default: source filename stem) |
| `--title "<text>"` | sidebar title (default: first user message) |
| `--model <id>` | record a model id (Claude Code JSONL has none, so it's blank otherwise) |
| `--include-sidechains` | also include sub-agent (Agent/Task) records |
| `--out-dir <dir>` | target a different `docs/fable` directory |

## 2. Serve `docs/` over HTTP

The viewer uses `fetch()`, so it must be served — opening the file with
`file://` will not load the session JSON.

```bash
cd docs
python3 -m http.server 8000
```

Then open <http://localhost:8000/microscope.html> and pick your session from the
sidebar.

> **Mermaid tab needs internet.** `microscope.html` loads `mermaid@11` from a CDN,
> so the Flowchart / GitGraph / Sequence tab requires a connection. The Overview,
> Transcript, Blocks, Raw JSON, and API Reconstruction tabs work fully offline.

## What the converter maps

| Claude Code JSONL | Microscope event | notes |
|---|---|---|
| one record per line | one entry in `events[]` | merged into a single package |
| `uuid` | `id` | |
| `parentUuid` | `parentId` | re-rooted to `null` if the parent was filtered out |
| `type: assistant`/`user` | `type: "message"` | only these become messages |
| block `text` / `thinking` | same | |
| block `tool_use` | block `toolCall` (`name`, `input`, `text` summary) | renders in Blocks/Sequence |
| block `tool_result` | block `toolResult` (`text` preview + `raw`) | |
| `ai-title`, `mode`, `queue-operation`, `system`, `attachment` | dropped | harness bookkeeping |
| `isSidechain: true` | dropped unless `--include-sidechains` | sub-agent runs |

Model / thinking level show as "unknown" because Claude Code transcripts don't
carry `model_change` events — that's expected and flagged under
"Missing API fields" in the Overview/API tabs.

## Removing a converted session

Delete `docs/fable/sessions/<id>.json` and remove its entry from
`docs/fable/sessions.index.json`.
