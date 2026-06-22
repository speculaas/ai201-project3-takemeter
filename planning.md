# TakeMeter Planning — AgentTraceTakeMeter

Project: classify developer takes on **Fable 5, agent traces, and AI coding-agent distillation** from Reddit/Hugging Face discourse.

## 1. Community

**Primary communities:** `r/LocalLLaMA`, `r/ClaudeCode`, `r/ClaudeAI`, `r/ChatGPTCoding`, `r/LangChain`, `r/huggingface`

These subreddits host active debate about Claude Code, Fable 5 claims, benchmark skepticism, trace datasets, observability tooling (Langfuse, Langtrace, OpenTelemetry), and distilled coding models. Discourse varies between technical analysis, methodology discussion, benchmark claims, data-quality skepticism, and hype/reaction — a good fit for a 2–5 label classifier.

Training data = **human comments/posts reacting to** Fable traces, model cards, demos, and Anthropic claims — not the trace rows themselves.

## 2. Labels

| Label | Definition |
|-------|------------|
| `benchmark_claim` | Evaluates Fable 5, Claude Code, or agentic models mainly via benchmarks, scores, pass rates, or model comparisons. |
| `data_quality_skepticism` | Questions dataset validity, provenance, size, license, safety, malware risk, overfitting, or whether traces are enough for training. |
| `architecture_analysis` | Explains technical mechanisms: CoT summaries, tool calls, ReAct behavior, memory, context windows, LoRA, routing, agent scaffolding. |
| `trace_methodology` | Focuses on how to collect, log, reconstruct, replay, visualize, evaluate, or curate LLM/agent traces. |
| `hype_or_reaction` | Mostly excitement, dismissal, humor, fear, or low-detail reaction without much evidence. |

## 3. Hard Edge Cases

**Boundary:** `architecture_analysis` vs `trace_methodology`

Example: *"You need OpenTelemetry spans for every tool call if you want reusable traces."*

- If the comment explains **what the system does internally** (tool schema design, CoT structure) → `architecture_analysis`
- If the comment explains **how to log/curate/evaluate traces as a workflow** → `trace_methodology`

**Rule:** If the main point is a reproducible logging/eval pipeline, label `trace_methodology`. If the main point is how the agent/model works, label `architecture_analysis`.

## 4. Data Collection Plan

1. **Try automated scrape first:** `python scripts/scrape_reddit.py --mode json --max-urls 3` (no API key)
2. **If scrape is noisy or rate-limited:** use PRAW mode or fall back to manual labeling web app (FastAPI + SQLite)
3. **Target:** 220–250 candidate items; label ≥200 for training
4. **Sources:** seed threads in `sources/seed_urls.txt` + optional subreddit search (`sources/search_queries.txt`)
5. **Balance:** no single label >70%; collect more from underrepresented labels
6. **Files:**
   - `data/raw_discourse_items.csv` — scraped flat items
   - `data/labeled_dataset.csv` — `text,label,notes,source_url,item_id,parent_id`

## 5. Evaluation Metrics

- Overall accuracy (fine-tuned vs zero-shot Groq baseline on same test set)
- Per-class precision, recall, F1 (especially for confused pairs like `architecture_analysis` / `trace_methodology`)
- Confusion matrix
- Wrong-prediction analysis (≥3 examples with explanation)

## 6. Definition of Success

Fine-tuned DistilBERT **meaningfully beats** the zero-shot Groq baseline on the held-out test set, with per-class F1 ≥ 0.50 on most labels and diagnosable failure modes (not just majority-class guessing). Confidence scores should roughly track correctness on a small spot-check.

## AI Tool Plan

1. **Label stress-testing:** Ask an LLM to generate boundary posts between `architecture_analysis` and `trace_methodology`; tighten definitions if it can't classify them.
2. **Annotation assistance:** Optionally pre-label with Groq using label definitions; manually review every row; disclose in README.
3. **Failure analysis:** After training, paste misclassified examples into an LLM to surface patterns; verify each pattern by re-reading examples.
