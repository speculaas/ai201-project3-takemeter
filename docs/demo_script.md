# Demo video script (~3–4 minutes)

Use this as a talk track while screen-recording. Show the GitHub repo + Colab notebook + labeler if time allows.

---

## 0:00 — Hook (15 sec)

> "I built **AgentTraceTakeMeter** — a classifier for developer discourse about Fable 5 traces, agentic coding tools, and whether trace datasets are credible. It reads a Reddit or Hugging Face comment and assigns one of four labels."

## 0:15 — Problem & community (30 sec)

Show `planning.md` or README **Community** section.

> "My community isn't one subreddit — it's overlapping public developer discourse on Reddit AI/LLM subs plus Hugging Face discussions about the same artifacts. I'm classifying *human reactions*, not raw trace rows."

## 0:45 — Labels (45 sec)

Show the 4-label table.

> "Four labels: benchmark claims, data-quality skepticism, architecture/trace analysis, and hype or reaction. The hard part is boundary cases — e.g. a chart skepticism post vs a dataset provenance rant."

## 1:30 — Data & labeling workflow (60 sec)

Show `data/labeled_dataset.csv` row count + labeler screenshots or `labeler/` README.

> "I collected ~230 candidates, used AI to *suggest* labels, then manually reviewed every row in a local FastAPI labeler. Rows import as `needs_review` until I confirm them. Final export: 211 reviewed examples."

Optional: quick Annotate demo — confirm one label with Enter.

## 2:30 — Training & baseline (45 sec)

Open Colab notebook results or `results/evaluation_results.json`.

> "I fine-tuned DistilBERT on a 70/15/15 split and compared against a Groq zero-shot baseline using the same prompt as `prompts/groq_baseline_prompt.txt`."

## 3:15 — Results (45 sec)

Show comparison table + confusion matrix image.

> "Baseline hit **68.6%** accuracy on the 35-example test set. Fine-tuned DistilBERT got **45.7%** — it collapsed to predicting `architecture_or_trace_analysis` for almost everything because that class is ~50% of the data and comments often mention tools/traces in passing."

## 4:00 — Reflection & next steps (30 sec)

> "The zero-shot LLM understood label definitions better than a small fine-tuned model on this noisy, subjective text. Next steps: train on `status=labeled` only, rebalance classes, and add a filter step before fine-tuning. The labeler + review workflow still made the dataset auditable for class."

## 4:30 — Close (10 sec)

> "Repo link, notebook link, and evaluation artifacts are in the README. Thanks!"

---

## Recording checklist

- [ ] GitHub repo visible in browser
- [ ] `results/confusion_matrix.png` in README
- [ ] Colab notebook with executed cells (or terminal showing metrics)
- [ ] Optional: 10-second labeler Annotate clip
- [ ] Upload video link in README or course submission form
