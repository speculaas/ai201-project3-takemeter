# AgentTraceTakeMeter Labeler

Local-only annotation tool. Not deployed to the cloud.

## Run

```bash
./run.sh
```

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

Then label on **Annotate** (keys 1–5, Enter to save).

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
