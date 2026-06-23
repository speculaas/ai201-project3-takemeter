# TakeMeter Planning — AgentTraceTakeMeter

Project: classify developer takes on **Fable 5, agent traces, and AI coding-agent distillation** from public developer discourse.

## 1. Community

My chosen online community is a **topic-centered public developer discourse community** around Fable 5 traces, Fable-distilled models, agentic coding tools, and trace/dataset credibility. I sample primarily from Reddit AI/LLM communities and supplement with Hugging Face Discussions when they contain public human-written comments about the same artifacts. I am not claiming the exact same people participate on both platforms; I am treating them as overlapping public developer discourse spaces with shared norms around benchmark credibility, dataset provenance, trace usefulness, architecture/tool-use analysis, hype skepticism, and practical developer usefulness.

**Primary sources:** `r/LocalLLaMA`, `r/ClaudeCode`, `r/ClaudeAI`, `r/ChatGPTCoding`, `r/LangChain`, `r/huggingface`, and similar Reddit AI/LLM communities.

**Supplementary source:** Hugging Face dataset/model Discussion tabs about Fable 5, Fable traces, Fable-distilled models, Claude Code traces, or agentic coding.

Raw Fable trace rows, CoT fields, and model outputs are not labeled as community takes; they are background artifacts that the community reacts to.

## 2. Labels

Four mutually exclusive labels (spec requires 2–4):

| Label | Definition |
|-------|------------|
| `benchmark_claim` | Evaluates Fable 5, Claude Code, distilled models, or agentic coding tools mainly through benchmarks, scores, pass rates, leaderboards, comparisons, or evaluation results. |
| `data_quality_skepticism` | Questions dataset validity, trace count, provenance, licensing, malware risk, overfitting, distillation claims, or whether traces are useful for training. |
| `architecture_or_trace_analysis` | Analyzes technical mechanisms or trace methodology, including CoT summaries, tool calls, traces, agent scaffolding, memory, context windows, LoRA, GGUF, MLX, logging, observability, OpenTelemetry, replay, evaluation pipelines, or trace curation. |
| `hype_or_reaction` | Mostly excitement, dismissal, sarcasm, fear, humor, or low-detail reaction without substantial technical reasoning or evidence. |

## 3. Hard Edge Cases

### Edge case A: `benchmark_claim` vs `data_quality_skepticism`

Example: *"13/13 on a private benchmark means nothing; it is probably overfit to the leaked traces."*

**Decision rule:** If the main point is benchmark validity, private tasks, unreproducible scores, leaderboards, or pass rates → `benchmark_claim`. If the main point is overfitting, trace count, provenance, licensing, malware risk, or training-data trustworthiness → `data_quality_skepticism`.

### Edge case B: `data_quality_skepticism` vs `architecture_or_trace_analysis`

Example: *"Summarized CoT may teach response style but not true reasoning."*

**Decision rule:** If the comment mainly explains how CoT summaries, traces, tool calls, or logging work → `architecture_or_trace_analysis`. If the comment mainly argues the dataset is unusable, misleading, unsafe, or too small → `data_quality_skepticism`.

### Edge case C: `benchmark_claim` vs `hype_or_reaction`

Example: *"Fable 5 beats everything. Open source won."*

**Decision rule:** If the comment gives no concrete benchmark, score, comparison, or evidence → `hype_or_reaction`. If it mentions a specific benchmark, score, leaderboard, or reproducible comparison → `benchmark_claim`.

## 4. Data Collection Plan

1. Collect at least **200 public human-written examples** (target 220–250 candidates before filtering).
2. **Primary source:** Reddit AI/LLM communities (`sources/seed_urls.txt`, optional PRAW search via `sources/search_queries.txt`).
3. **Supplementary source:** Hugging Face Discussions on Fable-related datasets/models.
4. **Collection tools:** `scripts/scrape_reddit.py` (try first) or manual paste into `labeler/` web app.
5. **Each labeled row includes:** `text`, `label`, `notes`, `source_url`, `platform`, `community`, `item_id` (if available), `parent_id` (if available).
6. **Balance:** no single label >70%; collect more from underrepresented labels.
7. **Files:**
   - `data/raw_discourse_items.csv` — scraped candidates (unlabeled)
   - `data/labeled_dataset.csv` — final reviewed training export
8. **LLM pre-labeling:** AI may suggest labels; rows import as `needs_review` until manually confirmed as `labeled` in the labeler.

## Class balance note (current AI pre-labels)

Approximate distribution in `data/labeled_dataset_prelabeled_review_needed.csv`:

- `architecture_or_trace_analysis`: ~120 (57%) — **over target**
- `benchmark_claim`: ~43
- `hype_or_reaction`: ~25
- `data_quality_skepticism`: ~23

During manual review: collect more skepticism/hype examples if possible, or downsample architecture rows before training (`scripts/make_final_dataset.py --max-per-label`). No single label should exceed 70%.

## 5. Evaluation Metrics

- Overall accuracy (fine-tuned vs zero-shot Groq baseline on same test set)
- Per-class precision, recall, F1 — especially for likely confused pairs:
  - `benchmark_claim` vs `data_quality_skepticism`
  - `data_quality_skepticism` vs `architecture_or_trace_analysis`
  - `hype_or_reaction` vs `data_quality_skepticism` (short skeptical comments)
- Confusion matrix
- Wrong-prediction analysis (≥3 examples with explanation)

## 6. Definition of Success

- Overall accuracy **≥70%** on the held-out test set would be useful for this subjective task.
- Per-class F1 **≥0.60** for each label would be strong.
- Fine-tuned DistilBERT should **meaningfully compare against** the Groq zero-shot baseline on the same test set (not just majority-class guessing).
- Confidence scores should roughly track correctness on a small spot-check.

## AI Tool Plan

1. **Label stress-testing:** Ask an LLM to generate boundary posts between `data_quality_skepticism` and `architecture_or_trace_analysis`; tighten definitions if it can't classify them cleanly.
2. **Annotation assistance:** Pre-label candidate batches with Groq using `prompts/groq_baseline_prompt.txt`; **manually review and correct every row** in the labeler; disclose tool used and overrides in README.
3. **Failure analysis:** After training, paste misclassified examples into an LLM to surface patterns; verify each pattern by re-reading examples.
