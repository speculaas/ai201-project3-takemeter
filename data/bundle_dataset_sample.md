# Dataset bundle sample (template)

I do not have the full raw dataset yet. This file documents the expected schema and a few **illustrative** examples for the 4-label taxonomy. Replace with real annotated rows in `labeled_dataset.csv` after collection and review.

## Required columns (training export)

```csv
text,label,notes,source_url,platform,community,item_id,parent_id
```

## Label set (4 labels)

| Label | When to use |
|-------|-------------|
| `benchmark_claim` | Benchmarks, scores, pass rates, leaderboards, model comparisons |
| `data_quality_skepticism` | Dataset/trace validity, provenance, size, license, malware, overfitting |
| `architecture_or_trace_analysis` | How traces/tools/CoT/logging/observability work or should be collected |
| `hype_or_reaction` | Hype, dismissal, sarcasm, low-detail reaction without evidence |

## Illustrative examples (not final training data)

### benchmark_claim

> 13/13 on a custom benchmark means nothing unless the tasks are public and reproducible.

### data_quality_skepticism

> 4.6k Fable trace rows is tiny for distillation — I'd be skeptical this generalizes beyond the exact sessions collected.

### architecture_or_trace_analysis

> You need OpenTelemetry spans for every tool call if you want reusable traces for eval datasets.

### hype_or_reaction

> Fable 5 is going to change everything!!! Anthropic cooked again.

## Workflow (when raw data arrives)

1. Collect candidates → `data/raw_discourse_items.csv`
2. Optional LLM pre-label (disclose in README)
3. Manual review in `labeler/`
4. Export final → `data/labeled_dataset.csv`
5. Document ≥3 difficult cases in `data/difficult_cases.md`
