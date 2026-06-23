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

## AI Usage Plan / Disclosure

I may use an LLM to pre-label batches of collected comments using the label definitions in `planning.md`. Every pre-labeled example will be manually reviewed and corrected before inclusion in the final dataset. I will disclose this workflow in the final README, including which tool was used, what it produced, and what I changed or overrode. The final labels are my reviewed annotations, not unverified model outputs.

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
scripts/        scrape_reddit.py
labeler/        local labeling web app (FastAPI)
sources/        seed_urls.txt, search_queries.txt
```

## Still to fill in after notebook run

- Data collection notes and label distribution
- Fine-tuning approach and hyperparameters
- Baseline comparison results
- Evaluation report, reflection, demo video
