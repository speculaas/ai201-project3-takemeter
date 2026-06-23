# TakeMeter — AgentTraceTakeMeter

Fine-tuned text classifier for **topic-centered public developer discourse** about Fable 5 traces, Fable-distilled models, agentic coding tools, and trace/dataset credibility.

See `planning.md` for label taxonomy and collection plan.

## Community

My chosen online community is a topic-centered public developer discourse community around Fable 5 traces, Fable-distilled models, agentic coding tools, and trace/dataset credibility. I sample primarily from Reddit AI/LLM communities and supplement with Hugging Face Discussions when they contain public human-written comments about the same artifacts. I am not claiming the exact same people participate on both platforms; I am treating them as overlapping public developer discourse spaces with shared norms around benchmark credibility, dataset provenance, trace usefulness, architecture/tool-use analysis, hype skepticism, and practical developer usefulness.

Raw Fable trace rows, CoT fields, and model outputs are not labeled as community takes; they are background artifacts that the community reacts to.

## Labels (4)

- `benchmark_claim`
- `data_quality_skepticism`
- `architecture_or_trace_analysis`
- `hype_or_reaction`

## Data collection (scrape script)

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` for PRAW mode (recommended).

### Quick try — json mode (no OAuth, may get HTTP 403)

Reddit often blocks unauthenticated scraping. If this fails, use **praw mode** below.

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

### PRAW mode (recommended)

1. Create a Reddit **script** app at https://www.reddit.com/prefs/apps (read-only is fine)
2. Copy `.env.example` → `.env` and fill in `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`

```bash
python scripts/scrape_reddit.py --mode praw
python scripts/scrape_reddit.py --mode praw --search
```

### Labeling web app

```bash
cd labeler
./run.sh
```

Open http://127.0.0.1:8000 (or the LAN URL printed by `run.sh`). Use **Dashboard → Quick add** or **Add / Import** for new takes; **Annotate** to label (keys 1–4).

See `labeler/README.md` for LAN access, safety, and cleanup.

## Manual review of AI pre-labels

Pre-labeled files are in `data/`:

- `data/items_export_230_prelabeled.csv` — full 230-row export (211 AI labels + 19 skip)
- `data/labeled_dataset_prelabeled_review_needed.csv` — 211-row training-style subset (import as pre-labeled)

### Avoid duplicate imports (reset DB first)

```bash
# Option A: one command (backup + wipe + import)
bash scripts/reset_labeler_db.sh --import

# Option B: manual (what you discussed)
cp labeler/items.db labeler/items.db.backup-before-reset
rm labeler/items.db
python3 scripts/import_prelabeled.py
```

### Review in the labeler

```bash
cd labeler
./run.sh
```

1. Open **Annotate** — queue defaults to **Review AI labels first**
2. Rows with `needs_review` show the AI suggestion pre-selected and a yellow badge
3. Press **1–4** to change label if needed, **Enter** to confirm (marks `labeled`), **s** to skip
4. Watch dashboard counts — current AI distribution is architecture-heavy (~57%)

### Export and validate final dataset

```bash
# From labeler Dashboard → Export training CSV, save as:
# data/labeled_dataset.csv

python3 scripts/validate_labeled_dataset.py data/labeled_dataset.csv
```

Optional downsampling if `architecture_or_trace_analysis` still dominates:

```bash
python3 scripts/make_final_dataset.py \
  -i data/items_export_230_prelabeled.csv \
  -o data/labeled_dataset.csv \
  --max-per-label 85
```

(Only use `make_final_dataset.py` after rows are `status=labeled` in an export.)

## AI Usage Plan / Disclosure

I used an AI assistant to pre-label candidate comments using the label definitions in `planning.md`. Each pre-labeled row was manually reviewed in the local labeler before inclusion in the final dataset. Rows that were off-topic, too short, synthetic seed examples, or too context-dependent were marked `skip` and excluded from training.

**Suggested workflow:**

1. Collect 220–250 candidate comments (scrape or manual).
2. Optional: LLM pre-label with notes.
3. Review and correct every label in the local labeler.
4. Export `data/labeled_dataset.csv`.
5. Document AI assistance and manual overrides in this README.

## Repo layout

```
data/           raw + labeled CSVs, difficult_cases.md
prompts/        Groq baseline prompt
results/        evaluation_results.json, confusion_matrix.png (from Colab)
scripts/        scrape_reddit.py, import_prelabeled.py, validate_labeled_dataset.py
labeler/        local labeling web app (FastAPI)
sources/        seed_urls.txt, search_queries.txt
```

## Still to fill in after notebook run

- Data collection notes and label distribution
- Fine-tuning approach and hyperparameters
- Baseline comparison results
- Evaluation report, reflection, demo video
