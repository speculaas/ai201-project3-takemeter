# Dataset bundle sample — AgentTraceTakeMeter

Final reviewed training export: `data/labeled_dataset.csv` (211 `labeled` rows + 19 `skip` rows in full export).

## Schema

```csv
text,label,notes,source_url,platform,community,item_id,parent_id
```

## Label distribution (211 reviewed training rows)

| Label | Count | Share |
|-------|------:|------:|
| `architecture_or_trace_analysis` | 106 | 50.2% |
| `benchmark_claim` | 45 | 21.3% |
| `data_quality_skepticism` | 31 | 14.7% |
| `hype_or_reaction` | 29 | 13.7% |

## Real examples (one per label)

### benchmark_claim

> I just now learned that the lines of code metric is a delta … My actual lines of code accepted … is 27,925. In 7.5 hours.

### data_quality_skepticism

> I added synthetic CoT (because Fable doesnt save any in claude code) to fill in the gaps and improve performance for smaller models

### architecture_or_trace_analysis

> Not sure how to best contribute this to the dataset, but here's a claude code session I did with fable on my work laptop … https://gist.github.com/…

### hype_or_reaction

> They nerf it so much more than Claude Code does, that it often becomes actually worse than using Google's models in Antigravity

## Collection sources

- Reddit: `r/LocalLLaMA`, `r/ClaudeCode`, `r/ClaudeAI`, `r/ChatGPTCoding`, `r/LangChain`, `r/huggingface`, `r/ollama`
- Hugging Face Discussions on Fable-5-traces and related datasets/models
- Seeds: `sources/seed_urls.txt`, `sources/search_queries.txt`
