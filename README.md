# Empirical Validation of Cognitive-Derived Coding Constraints and Tokenization Asymmetries in LLM-Assisted Software Engineering

**Author:** Luciano Federico Pereira
**ORCID:** [0009-0002-4591-6568](https://orcid.org/0009-0002-4591-6568)
**Status:** Working Paper — Empirical Study
**License:** LGPL-2.1

**Companion Papers:**
- Pereira, L.F. (2026a). *Confirmation Bias in Post-LLM Software Architecture: Are We Optimizing for the Wrong Reader?* DOI: [10.5281/zenodo.18627897](https://doi.org/10.5281/zenodo.18627897)
- Pereira, L.F. (2026b). *Cognitive-Derived Constraints for AI-Assisted Software Engineering (CDCC): A Framework for Human–Machine Co-Design.* DOI: [10.5281/zenodo.18735784](https://doi.org/10.5281/zenodo.18735784)

---

## Overview

This repository contains the complete Python pipeline and data for the empirical study. The paper frames LLM output generation as an **economic production function** and tests whether cognitive-science-derived code structure thresholds (CDCC) define an empirical Pareto efficiency frontier for LLM processing.

Three experiments are included:

| Experiment | Research Questions | Key Result |
|---|---|---|
| **Exp 1** — Tokenization differential by naming convention | RQ1, RQ3, RQ4 | dot notation 1.12–1.20× more tokens than camelCase |
| **Exp 2** — LLM output production function under code complexity | RQ2 | β = 0.102 (diminishing marginal returns); 3.3× CDCC gap |
| **Exp 3** — Cross-model tokenizer variance | RQ4 | Spearman ρ = 1.000 across all tokenizer pairs |

### Key Results

- **H1:** dot/camelCase token ratio = **1.199×** (GPT-4o), **1.116×** (GPT-4) — $p < 0.001$, Wilcoxon signed-rank
- **H2:** Spearman ρ = **1.000** across all tokenizer pairs — camelCase advantage is universal
- **H3:** CDCC-compliant functions achieve **0.141** output/input ratio vs **0.043** for violating functions (3.3× gap, $p < 0.001$, Mann-Whitney U)
- **H4:** Production function elasticity **β = 0.102** — each 1% increase in input complexity yields only 0.10% more output (strong diminishing marginal returns)
- **H5:** Annual cost delta = **$54,499** (95% CI: $46,902–$62,301) at 1M API calls/day

---

## Setup

**Requirements:** Python 3.11+ · [Ollama](https://ollama.com) (Experiment 2 only — local inference, no API key needed)

```bash
# Clone and create virtual environment
git clone https://github.com/lucianofedericopereira/cognitive-coding-constraints
cd cognitive-coding-constraints
python3 -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# For Experiment 2: install Ollama and pull model
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2
```

---

## Running the Experiments

```bash
make corpus   # Build 200-identifier corpus (Exp 1 prerequisite)
make exp1     # Tokenization analysis + cost model
make exp3     # Cross-model Spearman correlations
make exp2     # Function corpus + LLM probe + production function scoring
make plots    # Generate all 6 figures (PDF)
make paper-tex  # Compile paper PDF (requires xelatex + bibtex)
```

Each target is incremental — outputs are written to `results/` and `data/`. LLM responses are cached in `data/cache/` (SHA-256 keyed JSON) so re-runs do not re-invoke the model.

---

## Repository Structure

```
src/
  corpus_builder.py          # Builds 200-identifier naming convention corpus
  tokenizer_analysis.py      # Multi-tokenizer token counting (tiktoken)
  cost_model.py              # Actuarial cost projection with bootstrap CI
  function_collector.py      # Downloads 100 Python functions from open-source repos
  code_metrics.py            # Cyclomatic complexity, LoC, nesting depth, CDCC flags
  llm_probe.py               # LLM comprehension probe via Ollama (5 responses/function)
  comprehension_scorer.py    # Log-log production function fit + Mann-Whitney U test
  cross_model_correlation.py # Spearman rank correlations across tokenizer pairs
  plot_results.py            # Generates Figures 1–6 as PDF
  changepoint_analysis.py    # PELT change-point detection (supplementary)
  utils.py                   # Shared paths, logging, cache, random seed

data/
  seed_identifiers.csv       # 40 seed event identifiers (Pereira 2026a, Table 1)
  code_functions/            # 100 Python functions, 25 per complexity tier
  code_metrics.csv           # CDCC metrics per function (generated)
  cache/                     # SHA-256 keyed LLM response cache

results/
  exp1_token_counts.csv
  exp2_comprehension_scores.csv
  exp3_rank_correlations.csv
  plots/                     # Figures 1–6 (PDF)

paper/
  empirical_cdcc_paper.tex   # LaTeX source
  references.bib             # BibTeX bibliography
  empirical_cdcc_paper.pdf   # Compiled paper

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
- Experiment 2 uses Llama 3.2 (3B) at `temperature=0` (greedy decoding)
- CI validates corpus build and unit tests on every push (GitHub Actions, Python 3.11 + 3.12)
- Pre-computed results in `results/` allow inspection without re-running experiments

---

## License

Code: **LGPL-2.1**
Data (function corpus): inherited from respective upstream licenses (MIT, Apache 2.0, BSD-3)
