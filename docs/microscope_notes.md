# Claude/Fable Trace Microscope Notes

This repo does **not** currently have the older GitHub Pages gallery app assumed by the external bundle discussion, so the microscope work here starts as a standalone static prototype.

## Current starter architecture

```text
docs/
├── microscope.html
├── microscope.js
├── microscope.css
├── trace-model.js
└── fable/
    ├── sessions.index.json
    └── sessions/
        └── sample-session.json
```

## Intended next step from Colab

Export curated session packages from `fable5_traces_explorer.ipynb` into:

```text
docs/fable/sessions.index.json
docs/fable/sessions/{session_id}.json
docs/fable/exports/{session_id}_events.jsonl
docs/fable/mermaid/{session_id}.flowchart.mmd
```

## Working assumptions

- The Hugging Face `pi_agent` split is event-level.
- The microscope's core unit should be a curated **session package**.
- API reconstruction must stay conservative and explicitly mark missing fields.
- Mermaid views are summaries/overlays, not guaranteed exact replay of the original request graph.

## Suggested next implementation order

1. Extend the Colab notebook with a real session-package export section.
2. Add validation cells for exported JSON files.
3. Expand the browser UI with more tabs:
   - Flowchart
   - GitGraph
   - Sequence
   - Concept Overlay
4. Add CSV / JSONL / Mermaid download buttons.
5. Optionally wire this into GitHub Pages once real sample exports exist.
