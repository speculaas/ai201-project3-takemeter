# AgentTraceTakeMeter Labeler
<img width="1836" height="846" alt="image" src="https://github.com/user-attachments/assets/f4e63255-0e5e-4207-99d7-fc3c45b89ad6" />

Local-only annotation tool. Not deployed to the cloud.

## Run

```bash
./run.sh
```

Uses `python -m uvicorn` (the ASGI server package) from `labeler/.venv`.

If you see `command not found: uvicorn`, the venv was missing packages — re-run `./run.sh` (it auto-installs) or:

```bash
cd labeler
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Remote machine / SSH:** If you copied the repo from another computer, delete and recreate the venv on that host (`rm -rf labeler/.venv && ./run.sh`) — venvs are not portable across machines.

- **This machine:** http://127.0.0.1:8000
- **Other devices on same Wi‑Fi/LAN:** `run.sh` prints a `http://192.168.x.x:8000` URL

Override bind address/port:

```bash
HOST=0.0.0.0 PORT=8000 ./run.sh
```

## Add new takes

| Method | Where |
|--------|--------|
| Quick paste | **Dashboard** → “Quick add a take” |
| One at a time | **Add / Import** → “Add single item” |
| Many at once | **Add / Import** → paste CSV/JSONL (e.g. from `data/raw_discourse_items.csv`) |
| Scrape first | `python scripts/scrape_reddit.py --mode praw` then bulk-import the CSV |

Then label on **Annotate** (keys 1–4, Enter to confirm reviewed labels).

## Review AI pre-labels

Statuses:

| Status | Meaning |
|--------|---------|
| `needs_review` | AI-suggested label — not final until you confirm |
| `labeled` | Manually reviewed and accepted/corrected |
| `skip` | Excluded from training |
| `unlabeled` | No label yet |

**Annotate** queue options:

- Review AI labels first, then unlabeled (default)
- AI pre-labels only (`needs_review`)
- New unlabeled only

CLI import (no paste needed):

```bash
bash scripts/reset_labeler_db.sh --import
# imports data/items_export_230_prelabeled.csv → 211 needs_review + 19 skip
```

Bulk **Add / Import** in the UI: check **Pre-labeled import** so rows with AI notes import as `needs_review`, not final `labeled`.

Training export includes only `status=labeled` rows.

## Labels (4)

- `benchmark_claim`
- `data_quality_skepticism`
- `architecture_or_trace_analysis`
- `hype_or_reaction`

## Is it safe?

**For local class work: yes**, with these caveats:

- **No login** — anyone who can reach the port can read/edit your data.
- **Only bind to LAN (`0.0.0.0`) on a network you trust** (home Wi‑Fi). Don’t expose port 8000 to the public internet.
- **Data stays on your Mac** in `labeler/items.db` (SQLite). Nothing is sent to a remote server.
- **Not production-grade** — no HTTPS, rate limits, or backups.

## What persists vs. temporary

| Thing | Location | Wiped when? |
|-------|----------|-------------|
| Your labels & takes | `labeler/items.db` | You delete it |
| Python packages | `labeler/.venv/` | You delete it |
| Scrape venv | `.venv/` (repo root) | You delete it |
| Running server | Terminal process | You press **Ctrl+C** or close the terminal |

Nothing auto-expires. Cursor’s background test server is not special — if you didn’t start `./run.sh`, nothing is listening unless you left a terminal open.

## Cleanup when the project is done

```bash
# 1. Stop the server (in the terminal running run.sh)
# Ctrl+C

# 2. Remove virtualenvs (reinstall anytime with pip)
rm -rf labeler/.venv .venv

# 3. Optional: remove local DB if you exported training CSV to data/
rm -f labeler/items.db

# 4. Keep labeled exports in git
#    data/labeled_dataset.csv or training export from the UI
```

Your **GitHub repo** keeps planning docs, scripts, and exported CSVs. The SQLite DB is gitignored on purpose.
