# Empirical Validation of Cognitive-Derived Coding Constraints and Tokenization Asymmetries in LLM-Assisted Software Engineering

**Author:** Luciano Federico Pereira
**ORCID:** [0009-0002-4591-6568](https://orcid.org/0009-0002-4591-6568)
**Status:** Working Paper — Empirical Study

**Companion Papers:**
- Pereira, L.F. (2026a). *Confirmation Bias in Post-LLM Software Architecture.* DOI: [10.5281/zenodo.18627897](https://doi.org/10.5281/zenodo.18627897)
- Pereira, L.F. (2026b). *Cognitive-Derived Constraints for AI-Assisted Software Engineering (CDCC).* DOI: [10.5281/zenodo.18735784](https://doi.org/10.5281/zenodo.18735784)

---

## Overview

This repository contains the complete Python implementation and data for the empirical study. Three experiments are included:

| Experiment | Research Questions | Status |
|---|---|---|
| **Exp 1** — Tokenization differential by naming convention | RQ1, RQ3, RQ4 | ✅ Complete |
| **Exp 2** — CDCC thresholds and LLM code comprehension | RQ2 | ⏳ Run locally (requires Ollama) |
| **Exp 3** — Cross-model tokenizer variance | RQ4 | ✅ Complete |

### Key Results (Exp 1 & 3)

- **H1:** dot/camelCase token ratio = **1.199×** (GPT-4o), **1.116×** (GPT-4) — statistically significant (p < 0.001, Wilcoxon)
- **H2:** Spearman ρ = **1.000** across all tokenizer pairs — camelCase advantage is fully robust
- **H5:** Annual cost delta = **$54,499** (95% CI: $46,902–$62,301) at 1M API calls/day

---

## Setup

### Requirements

- Python 3.11+
- [Ollama](https://ollama.com) (for Experiment 2 — local LLM inference, no API key needed)

```bash
# 1. Clone and create virtual environment
python3 -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install Ollama and pull model (Experiment 2 only)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2
```

---

## Running the Experiments

```bash
make corpus   # Build 200-identifier corpus
make exp1     # Tokenization analysis + cost model
make exp3     # Cross-model Spearman correlations
make exp2     # Function collection + LLM probe + scoring + change-point
make plots    # Generate all figures (PDF)
```

Each target is incremental — outputs are written to `results/` and `data/`.
LLM responses are cached in `data/cache/` so re-runs do not re-invoke the model.
If `make exp2` is interrupted, re-running it resumes from the last completed function.

---

## Repository Structure

```
src/
  corpus_builder.py          # Builds 200-identifier naming convention corpus
  tokenizer_analysis.py      # Multi-tokenizer token counting (tiktoken + HF)
  cost_model.py              # Actuarial cost projection with bootstrap CI
  function_collector.py      # Downloads 100 Python functions from open-source repos
  code_metrics.py            # Cyclomatic complexity, LoC, nesting depth
  llm_probe.py               # LLM comprehension probe (Ollama / OpenAI / Anthropic)
  comprehension_scorer.py    # SCS (embedding cosine) + SAS (manual annotation)
  changepoint_analysis.py    # PELT change-point detection + CDCC threshold alignment
  cross_model_correlation.py # Spearman rank correlations across tokenizers
  plot_results.py            # Generates Figures 1–5 as PDF
  utils.py                   # Shared paths, logging, cache, random seed

data/
  seed_identifiers.csv       # 40 seed event identifiers (Pereira 2026a)
  extended_corpus.csv        # 200-identifier corpus (generated)
  code_functions/            # 100 Python functions, 25 per complexity tier
  annotations/               # Manual SAS annotation templates (rater_a/b.csv)
  cache/                     # SHA-256 keyed LLM response cache

results/
  exp1_token_counts.csv
  exp2_comprehension_scores.csv
  exp3_rank_correlations.csv
  plots/                     # Figures 1–5 (PDF)

tests/
  test_corpus_builder.py
  test_cost_model.py
  test_code_metrics.py
  test_comprehension_scorer.py
```

---

## Code Corpus Sources (Experiment 2)

Functions collected from the following permissive-license repositories:

| Repository | License |
|---|---|
| pytest-dev/pytest | MIT |
| Textualize/rich | MIT |
| fastapi/fastapi | MIT |
| pydantic/pydantic | MIT |
| encode/httpx | BSD-3 |
| aio-libs/aiohttp | Apache 2.0 |
| tornadoweb/tornado | Apache 2.0 |
| sqlalchemy/sqlalchemy | MIT |
| celery/celery | BSD-3 |

---

## Reproducibility

- Random seed fixed at `42` (`src/utils.py`)
- All LLM responses cached in `data/cache/` — reruns are deterministic
- CI runs on every push (GitHub Actions, Python 3.11 + 3.12)
- Results committed to `results/` for direct inspection without rerunning experiments

## License

Code: MIT
Data (function corpus): inherited from respective upstream licenses (MIT, Apache 2.0, BSD-3)
