# TakeMeter — AgentTraceTakeMeter

Fine-tuned text classifier for developer discourse about **Fable 5, agent traces, and AI coding-agent distillation** on Reddit.

See `planning.md` for label taxonomy and collection plan.

## Labels

- `benchmark_claim`
- `data_quality_skepticism`
- `architecture_analysis`
- `trace_methodology`
- `hype_or_reaction`

## Data collection (scrape script)

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in for praw mode (recommended)
```

### Quick try — json mode (no OAuth, may get HTTP 403)

Reddit often blocks unauthenticated scraping. If this fails on your machine, use **praw mode** below.

```bash
python scripts/scrape_reddit.py --mode json --max-urls 3
```

Outputs:
- `data/raw_discourse_items.csv` — flat items ready for labeling
- `data/raw_reddit_tree.csv` — tree fields (`comment_id`, `post_id`, `parent_id`, ...)

### Full scrape from seed URLs

```bash
python scripts/scrape_reddit.py --mode json
```

### PRAW mode (recommended — search + reliable thread fetch)

1. Create a Reddit **script** app at https://www.reddit.com/prefs/apps (read-only is fine)
2. Copy `.env.example` → `.env` and fill in `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`

```bash
python scripts/scrape_reddit.py --mode praw
python scripts/scrape_reddit.py --mode praw --search   # also run sources/search_queries.txt
```

### If scraping is not good enough

Fall back to the manual labeling web app (FastAPI + SQLite with CRUD, live stats, CSV export). See `docs/dlg-m365-3ab6281a_t-1782123160344_link-to-the-reddits.md` for the Gemini prompt.

## Repo layout

```
data/           raw + labeled CSVs
prompts/        Groq baseline prompt
results/        evaluation_results.json, confusion_matrix.png (from Colab)
scripts/        scrape_reddit.py
sources/        seed_urls.txt, search_queries.txt
```

## Still to fill in after notebook run

- Data collection notes and label distribution
- Fine-tuning approach and hyperparameters
- Baseline comparison results
- Evaluation report, reflection, AI usage, demo video
