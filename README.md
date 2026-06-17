# Executive Attention Synthesizer

**Cross-signal convergence detection.** Identifies where multiple organizational realities are pointing at the same underlying problem.

Part of the [Ground Truth Decisioning System](https://thomasmeerschwam.com) — five tools that convert organizational signal into executive judgment.

---

## What it does

Organizations maintain multiple, incompatible views of reality: performance data, meeting decisions, pipeline forecasts, initiative portfolios. Each system tells a different story. This tool finds the one they're all trying to tell.

It detects convergence — when multiple organizational domains independently surface signal pointing at the same underlying theme — and produces a structured executive attention report:

- **Requires Attention Now** — convergent findings across ≥2 organizational domains
- **Decision Cannot Be Postponed** — convergent findings with a named time constraint
- **What the Signals Suggest** — the structural hypothesis: what the organization appears to believe vs. what the signals suggest is actually true

---

## Architecture

```
Business Context (type + stage + optional text)
        ↓                              ↓
  Output Ranking              Claude Interpretation
  (deterministic)             (reasoning layer)

Signal Extraction → Theme Mapping → Convergence Scoring → Classification → Claude
  [deterministic]   [deterministic]   [deterministic]    [deterministic]  [reasoning]
```

The convergence engine is a measurement system, not an opinion system. Business context influences output ranking and Claude's interpretive framing — it never touches convergence scores.

**Scoring formula:**
```
theme_score = distinct_tool_count × max_severity × signal_count_modifier
```

Convergence threshold: score ≥ 6, distinct tools ≥ 2.

---

## Inputs

Upload `.txt` exports from any of the four preceding Ground Truth tools:

| Tool | Domain | Signal |
|---|---|---|
| WBR Generator | Performance | What happened? |
| Meeting Intelligence | Decision | What was decided? |
| Pipeline Synthesizer | Commercial | What will happen? |
| Initiative Intelligence | Strategic | Are we executing? |

**One input minimum. Four inputs maximum.** The tool finds convergence across whatever signal is available.

---

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file:
```
ANTHROPIC_API_KEY=your_key_here
```

Run:
```bash
streamlit run app.py
```

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | Python |
| API | Anthropic Claude Sonnet (structured tool use) |
| Theme mapping | Python keyword dictionaries (`theme_config.py`) |
| Hosting | Streamlit Community Cloud |

---

## File structure

```
executive-attention-synthesizer/
├── app.py                    # Main Streamlit app
├── theme_config.py           # Keyword maps, theme taxonomy, ranking tables
├── signal_extraction.py      # Parses tool outputs → signal objects
├── convergence.py            # Theme aggregation, scoring, classification, bundles
├── claude_reasoning.py       # Claude API call, structured tool use, prompt design
├── export.py                 # .txt export builder
├── requirements.txt
├── components/
│   └── output_display.py     # Streamlit output rendering
└── README.md
```

---

## Extending the theme taxonomy

All keyword maps live in `theme_config.py`. To add coverage for new organizational language:

1. Add keywords to the relevant theme in `THEME_KEYWORDS`
2. Add severity markers to `SEVERITY_3_MARKERS` or `SEVERITY_2_MARKERS` if needed
3. No other files need to change

---

## Known limitations (v1)

- No persistence — single-run, stateless
- Input format dependency — extraction is calibrated to Ground Truth tool output structures; edited outputs may degrade signal quality
- Keyword-based theme mapping — idiosyncratic organizational language may not match dictionaries; use the Optional Context field to compensate
- Theme taxonomy fixed in v1 — theme inflation or gaps become visible after test runs against real data

---

thomasmeerschwam.com · Ground Truth Decisioning System
