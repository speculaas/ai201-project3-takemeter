# Difficult-to-label examples

Three real cases from manual review and model error analysis.

## Case 1 — `benchmark_claim` vs `architecture_or_trace_analysis`

- **Text:** "I just now learned that the lines of code metric is a delta and so it wasn't tracking the actual number of lines of code correctly. My actual lines of code accepted … is 27,925. In 7.5 hours."
- **Source URL:** https://www.reddit.com/r/ClaudeCode/comments/1pjon1r/comment/ntf5xl9/
- **Possible labels:** `benchmark_claim`, `architecture_or_trace_analysis`
- **Final label:** `benchmark_claim`
- **Why this was difficult:** The comment discusses how a metric is computed (delta vs total), which sounds architectural, but the main point is a personal productivity/usage score (lines accepted per session).
- **Decision rule applied:** If the comment centers on benchmark-like metrics, scores, or comparative performance claims → `benchmark_claim`. Tooling/logging mechanics alone → `architecture_or_trace_analysis`.

## Case 2 — `data_quality_skepticism` vs `architecture_or_trace_analysis`

- **Text:** "I added synthetic CoT (because Fable doesnt save any in claude code) to fill in the gaps and improve performance for smaller models. The CoT generator used gpt-oss:120b …"
- **Source URL:** https://huggingface.co/datasets/Glint-Research/Fable-5-traces/discussions/1#6a2ddc193e2ed0b9120989bb
- **Possible labels:** `data_quality_skepticism`, `architecture_or_trace_analysis`
- **Final label:** `data_quality_skepticism` (reviewer corrected from AI pre-label of architecture)
- **Why this was difficult:** It explains *how* CoT was generated (methodology), but the thrust is whether synthetic CoT is trustworthy training signal for distillation.
- **Decision rule applied:** If the main argument is dataset validity, provenance, or whether traces/CoT are useful for training → `data_quality_skepticism`. If it mainly explains mechanism without challenging usefulness → `architecture_or_trace_analysis`.

## Case 3 — `benchmark_claim` vs `data_quality_skepticism` vs `hype_or_reaction`

- **Text:** "Open source hallucinates less. Do we believe this chart?" (Reddit post sharing an Artificial Analysis chart)
- **Source URL:** https://www.reddit.com/r/LocalLLaMA/ (chart skepticism thread)
- **Possible labels:** `benchmark_claim`, `data_quality_skepticism`, `hype_or_reaction`
- **Final label:** `benchmark_claim`
- **Why this was difficult:** Short skeptical question about a leaderboard/chart could be read as data-quality doubt or low-detail reaction.
- **Decision rule applied:** References a specific chart/benchmark comparison → `benchmark_claim`. Deep critique of dataset provenance → `data_quality_skepticism`. Pure dismissal without evidence → `hype_or_reaction`.
