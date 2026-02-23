# Empirical Validation of Cognitive-Derived Coding Constraints and Tokenization Asymmetries in LLM-Assisted Software Engineering

**Author:** Luciano Federico Pereira  
**ORCID:** 0009-0002-4591-6568  
**Affiliation:** Independent Researcher  
**Status:** Working Paper — Empirical Study  
**Companion Papers:**  
- Pereira, L.F. (2026a). *Confirmation Bias in Post-LLM Software Architecture: Are We Optimizing for the Wrong Reader?* DOI: [10.5281/zenodo.18627897](https://doi.org/10.5281/zenodo.18627897)  
- Pereira, L.F. (2026b). *Cognitive-Derived Constraints for AI-Assisted Software Engineering (CDCC): A Framework for Human–Machine Co-Design.* DOI: [10.5281/zenodo.18735784](https://doi.org/10.5281/zenodo.18735784)

---

## Abstract

Two prior theoretical works proposed that dot-notation naming conventions produce measurable token overhead for transformer-based LLMs (Pereira, 2026a) and that cognitive-science-grounded structural limits on code artifacts correspond to inflection points in LLM processing quality (Pereira, 2026b). Both claims remained untested. This paper provides the empirical evidence. We ran three experiments using a reproducible Python pipeline: (i) token count differentials across naming conventions applied to a corpus of 200 enterprise event identifiers; (ii) an econometric analysis of LLM output production as a function of code structural complexity on 100 Python functions probed via a local Llama 3.2 model (Ollama); and (iii) cross-model tokenizer variance across GPT-4o (`o200k_base`), GPT-4 (`cl100k_base`), and a Claude proxy. Dot notation produces 1.12–1.20× more tokens than camelCase across all tested tokenizers (p < 0.001), yielding a projected cost difference of $54,499 per year at enterprise call volumes. Efficiency rankings are perfectly consistent across all tokenizer vocabularies (Spearman ρ = 1.000). For Experiment 2, a log-log production function fit to the 100-function corpus yields an output elasticity of β = 0.102 (p < 0.001), confirming strong diminishing marginal returns: a 1% increase in input complexity produces only a 0.10% increase in LLM output. CDCC-compliant functions exhibit a 3.3× higher output/input ratio than violating functions (0.141 vs. 0.043), establishing CDCC thresholds as the empirical efficiency frontier for LLM-code interaction. The results confirm the theoretical projections of Pereira (2026a) and provide econometric support for the CDCC convergence hypothesis of Pereira (2026b).

**Keywords:** tokenization, BPE, naming conventions, cognitive load, CDCC, LLM, empirical software engineering, code metrics, production function, diminishing marginal returns, Pareto efficiency

---

## 1. Introduction

The industrialization of AI-assisted software development has introduced a new class of artifact consumer: the Large Language Model. Unlike human readers, whose cognitive processing obeys well-documented working memory limits (Miller, 1956; Cowan, 2001), LLMs process source code as token sequences. Token length directly determines computational cost, context window utilization, and the statistical coherence of generated outputs.

Pereira (2026a) identified a structural blind spot in contemporary software architecture: naming conventions are chosen for human readability, not for AI efficiency. Theoretical BPE analysis showed that dot notation produces significantly more tokens per identifier than camelCase or snake_case, incurring measurable cost and context penalties in LLM-assisted workflows.

Pereira (2026b) extended this observation to a broader claim: the structural boundaries known to reduce cognitive load for human developers — McCabe complexity thresholds, function length limits, dependency depth constraints — may also correspond to inflection points in LLM processing quality. Pereira (2026b) framed this convergence as an open research program but provided no empirical data.

The present paper operationalizes both claims. We define concrete experimental protocols, implement them as reproducible Python pipelines, and report results across multiple tokenizer backends and real-world code corpora.

### 1.1 Research Questions

- **RQ1:** Do naming conventions produce statistically significant token count differentials across a controlled corpus of event identifiers, and are the differentials consistent across GPT, Claude, and open-source tokenizer vocabularies?
- **RQ2:** Do CDCC structural thresholds (e.g., cyclomatic complexity ≤ 10, LoC ≤ 50, nesting depth ≤ 4) define an efficiency frontier for LLM output production? Specifically, does the LLM output/input token ratio exhibit diminishing marginal returns as a function of code complexity, and do CDCC-violating functions occupy a Pareto-dominated region of this production space?
- **RQ3:** Is the tokenization overhead of dot notation sufficient to produce economically meaningful cost differentials at enterprise scale, consistent with the actuarial model in Pereira (2026a)?
- **RQ4:** Does cross-model tokenizer variance affect the ranking of naming conventions by efficiency, or is camelCase's advantage robust across vocabulary differences?

---

## 2. Background and Prior Work

### 2.1 Byte-Pair Encoding and Naming Convention Tokenization

BPE tokenization (Sennrich et al., 2016), used by GPT-family models, and its variants (WordPiece, SentencePiece) build vocabularies by merging frequent character pairs. Pereira (2026a) argued that dot notation disrupts compound token recognition: the `.` character forces a vocabulary boundary, preventing the tokenizer from encoding `order.created` as a unified or two-token unit, while `orderCreated` (camelCase) may be encoded as fewer tokens depending on vocabulary coverage.

This paper empirically measures that effect across a controlled corpus.

### 2.2 Cognitive-Derived Coding Constraints (CDCC)

Pereira (2026b) synthesized cognitive science literature to derive principled structural thresholds:

| Constraint | CDCC Threshold | Cognitive Basis |
|---|---|---|
| Cyclomatic complexity | ≤ 10 | Working memory capacity (Miller, 1956) |
| Lines of code per function | ≤ 50 | Subitizing and chunking limits |
| Functions per file/module | ≤ 7 ± 2 | Miller's Law |
| Import/dependency depth | ≤ 5 | Cognitive stack depth (Sweller, 1988) |
| Nesting depth | ≤ 4 | Dual-process overload threshold |

The convergence hypothesis states that code artifacts violating these thresholds should also exhibit degraded LLM processing, measurable as increased token consumption per semantic unit or decreased answer quality on comprehension tasks.

### 2.3 Gap in the Literature

No published work has empirically tested whether BPE tokenizer behavior varies systematically with human-oriented naming conventions at corpus scale, nor whether CDCC thresholds correspond to measurable LLM behavioral inflection points. This paper provides the first such data.

---

## 3. Methodology

### 3.1 Experiment 1 — Tokenization Differential by Naming Convention (RQ1, RQ3, RQ4)

#### 3.1.1 Corpus Construction

A corpus of **N = 200** enterprise event identifiers is constructed using the following procedure:

1. **Seed set:** 40 identifiers from Pereira (2026a) Table 1 (theoretical analysis corpus).
2. **Extension:** 160 additional identifiers sampled from open-source event catalogs (AWS EventBridge schema registry, Kafka topic naming guides, and Laravel event class names from top-starred repositories on GitHub).
3. **Normalization:** Each identifier is stored in its canonical semantic form (e.g., "order created", "payment refund initiated") and then rendered in four notation variants: dot, camelCase, snake_case, kebab-case.

#### 3.1.2 Tokenizers Tested

| Model Family | Tokenizer | Library |
|---|---|---|
| GPT-4o | `o200k_base` | `tiktoken` |
| GPT-3.5 / GPT-4 | `cl100k_base` | `tiktoken` |
| Llama 3 *(optional)* | `meta-llama/Meta-Llama-3-8B` | `transformers` (Hugging Face) |
| Mistral *(optional)* | `mistralai/Mistral-7B-v0.1` | `transformers` |
| Claude proxy | `cl100k_base` (closest public approximation) | `tiktoken` |

> **Note:** Anthropic does not publish Claude's tokenizer. `cl100k_base` is used as a documented approximation; variance between this proxy and actual Claude tokenization is acknowledged as a study limitation. Hugging Face tokenizers (Llama 3, Mistral) require local model downloads (~4–8 GB each) and are skipped gracefully if not installed; primary results use tiktoken-based encodings (GPT-4o, GPT-4, Claude proxy).

#### 3.1.3 Metrics

For each identifier × tokenizer combination:

- **Token count** (`n_tokens`)
- **Token efficiency ratio** = semantic_word_count / n_tokens (higher = more efficient)
- **Inter-notation ratio** = n_tokens(dot) / n_tokens(camelCase) (replication of Pereira 2026a's 1.67x theoretical claim)

Statistical analysis: Wilcoxon signed-rank test across paired notation samples (non-parametric, since token count distributions are discrete and non-normal).

#### 3.1.4 Cost Projection (RQ3)

Using the empirical inter-notation ratios, recompute the actuarial model from Pereira (2026a):

```
annual_cost_delta = (mean_ratio - 1.0) × daily_api_calls × tokens_per_call × cost_per_1k_tokens × 365
```

Report confidence intervals using bootstrapped ratio distributions.

---

### 3.2 Experiment 2 — LLM Output Production Function under Code Complexity (RQ2)

#### 3.2.1 Code Corpus

A set of **N = 100** Python functions is collected from open-source repositories (permissive licenses: MIT, Apache 2.0), stratified by cyclomatic complexity:

- 25 functions with complexity ≤ 5 (well within CDCC)
- 25 functions with complexity 6–10 (at CDCC boundary)
- 25 functions with complexity 11–20 (moderate violation)
- 25 functions with complexity > 20 (severe violation)

Each function is annotated with: LoC, nesting depth, argument count, and CDCC-compliance status (via `code_metrics.py`).

#### 3.2.2 LLM Comprehension Probe

Each function is submitted to Llama 3.2 (3B, via Ollama) with the prompt:

```
Given the following Python function, answer in one sentence: what does this function do?

[function code]
```

The same function is submitted five times to build a response pool per function. Input and output token counts are recorded for each response.

#### 3.2.3 Output Production Function

We model LLM output generation as a production function, drawing on the economic framework of constrained production under scarcity (Simon, 1955; Varian, 1992). The key observable is the **output/input token ratio** — the proportion of output tokens generated per input token consumed. As input complexity grows, a system with bounded processing capacity must compress more aggressively, yielding a declining ratio.

We fit a **log-log production function** to isolate the output elasticity:

$$\log(\text{output\_tokens}) = \alpha + \beta \cdot \log(\text{input\_tokens}) + \varepsilon$$

where β is the **output elasticity** with respect to input complexity:

- β = 1 → constant returns (output scales proportionally with input)
- β < 1 → **diminishing marginal returns** (each additional input token yields less output)
- β > 1 → increasing returns (unlikely for constrained generative systems)

This framing maps directly to four established principles:

1. **Diminishing marginal returns** (classical economics): additional input yields less output per unit as scale grows.
2. **Bounded rationality** (Simon, 1955): agents satisfice rather than optimize when problem complexity exceeds their effective processing capacity.
3. **Opportunity cost of attention**: resources allocated to comprehending a complex input are unavailable for generating output — a constraint analogous to finite context window attention budget.
4. **Working memory saturation** (Miller, 1956; Cowan, 2001): beyond a capacity threshold, additional information degrades rather than improves output quality, mirroring the CDCC convergence hypothesis.

#### 3.2.4 CDCC Efficiency Frontier

Functions are partitioned into CDCC-compliant and CDCC-violating groups using the thresholds from Pereira (2026b). We compare the mean output/input ratio between groups via a Mann-Whitney U test (non-parametric, given non-normal distributions). The **CDCC threshold is hypothesised to define the efficiency frontier**: compliant functions should occupy the Pareto-efficient region (high output per input token), while violating functions are Pareto-dominated (high input cost, disproportionately low output).

---

### 3.3 Experiment 3 — Cross-Model Tokenizer Variance (RQ4)

Compute Spearman rank correlation of naming convention efficiency rankings across all tokenizers in §3.1.2. If rankings are highly correlated (ρ > 0.85), the camelCase advantage is robust across vocabulary differences. If not, model-specific tuning recommendations are warranted.

---

## 4. Implementation — Python Codebase

> This section defines the module structure for the accompanying repository. Each subsection corresponds to a Python module. Inline comments describe expected inputs, outputs, and key dependencies.

### 4.1 Repository Structure

```{=latex}
\dirtree{%
.1 empirical-cdcc/.
.2 README.md.
.2 requirements.txt.
.2 Makefile.
.2 data/.
.3 seed\_identifiers.csv \small\textit{40 identifiers from Pereira 2026a}.
.3 extended\_corpus.csv \small\textit{200 identifiers — generated by corpus\_builder.py}.
.3 code\_functions/ \small\textit{100 Python function files (.py)}.
.3 code\_metrics.csv \small\textit{CDCC metrics per function}.
.3 cache/ \small\textit{cached LLM API responses}.
.2 src/.
.3 corpus\_builder.py \small\textit{Experiment 1: corpus construction}.
.3 tokenizer\_analysis.py \small\textit{Experiment 1: multi-tokenizer token counting}.
.3 cost\_model.py \small\textit{Experiment 1: actuarial cost projection}.
.3 function\_collector.py \small\textit{Experiment 2: download \& stratify 100 functions}.
.3 code\_metrics.py \small\textit{Experiment 2: cyclomatic complexity, LoC, nesting}.
.3 llm\_probe.py \small\textit{Experiment 2: LLM probe (Ollama/OpenAI/Anthropic)}.
.3 comprehension\_scorer.py \small\textit{Experiment 2: production function analysis}.
.3 changepoint\_analysis.py \small\textit{Experiment 2: piecewise regression}.
.3 cross\_model\_correlation.py \small\textit{Experiment 3: Spearman rank correlation}.
.3 plot\_results.py \small\textit{Figures 1–5 (PDF)}.
.3 utils.py \small\textit{shared helpers, paths, cache, logging}.
.2 notebooks/.
.3 01\_tokenization\_results.ipynb.
.3 02\_cdcc\_comprehension.ipynb.
.3 03\_cross\_model\_variance.ipynb.
.2 results/.
.3 exp1\_token\_counts.csv.
.3 exp2\_comprehension\_scores.csv.
.3 exp3\_rank\_correlations.csv.
.3 plots/ \small\textit{Figures 1–5 as PDF}.
.2 tests/.
.3 test\_corpus\_builder.py.
.3 test\_cost\_model.py.
.3 test\_code\_metrics.py.
.3 test\_comprehension\_scorer.py.
.2 .github/workflows/.
.3 ci.yml \small\textit{unit tests + corpus smoke + plot smoke}.
.2 paper/.
.3 empirical\_cdcc\_paper.pdf \small\textit{final rendered paper}.
}
```

### 4.2 Module Specifications

#### `corpus_builder.py`

**Purpose:** Build the 200-identifier corpus from seed set + extended sources.

**Tasks:**
- Load `seed_identifiers.csv` (columns: `id`, `semantic_form`, `domain`)
- For each semantic form, generate four notation variants: `dot`, `camelCase`, `snake_case`, `kebab_case`
- Output: `extended_corpus.csv` with columns: `id`, `semantic_form`, `domain`, `dot`, `camelCase`, `snake_case`, `kebab_case`

**Key logic:**
```python
def to_dot(semantic: str) -> str: ...       # "order created" → "order.created"
def to_camel(semantic: str) -> str: ...     # "order created" → "orderCreated"
def to_snake(semantic: str) -> str: ...     # "order created" → "order_created"
def to_kebab(semantic: str) -> str: ...     # "order created" → "order-created"
```

#### `tokenizer_analysis.py`

**Purpose:** Count tokens for each identifier × tokenizer combination.

**Dependencies:** `tiktoken`, `transformers`

**Tasks:**
- Load `extended_corpus.csv`
- For each tokenizer in the test matrix, encode each notation variant
- Compute `n_tokens`, `token_efficiency_ratio`, `inter_notation_ratio`
- Output: `results/exp1_token_counts.csv`

**Key logic:**
```python
TOKENIZERS = {
    "gpt4o": tiktoken.get_encoding("o200k_base"),
    "gpt4":  tiktoken.get_encoding("cl100k_base"),
    "llama3": AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B"),
    "mistral": AutoTokenizer.from_pretrained("mistralai/Mistral-7B-v0.1"),
}

def count_tokens(text: str, tokenizer) -> int: ...
def compute_ratio(df: pd.DataFrame, base: str = "dot") -> pd.DataFrame: ...
```

**Statistical test:**
```python
from scipy.stats import wilcoxon
# Paired test: dot vs camelCase token counts across corpus
stat, p = wilcoxon(df["dot_tokens"], df["camelCase_tokens"])
```

#### `cost_model.py`

**Purpose:** Reproduce and extend the actuarial model from Pereira (2026a) using empirical ratios.

**Inputs:** `exp1_token_counts.csv`, user-provided parameters (daily API calls, token cost)

**Outputs:** `annual_cost_delta` with 95% CI via bootstrap

**Key parameters (defaults):**
```python
DAILY_API_CALLS = 1_000_000
TOKENS_PER_CALL = 150        # mean event identifier context
COST_PER_1K_TOKENS = 0.005   # USD, GPT-4o input pricing
N_BOOTSTRAP = 10_000
```

#### `code_metrics.py`

**Purpose:** Compute CDCC-relevant structural metrics for each function in the code corpus.

**Dependencies:** `radon` (cyclomatic complexity, LoC, Halstead), `ast` (nesting depth)

**Output columns:** `function_id`, `complexity`, `loc`, `nesting_depth`, `arg_count`, `cdcc_violation` (bool)

```python
import radon.complexity as rc
import radon.metrics as rm

def get_complexity(source: str) -> int: ...
def get_nesting_depth(source: str) -> int: ...  # AST walk
def is_cdcc_compliant(metrics: dict) -> bool:
    return (
        metrics["complexity"] <= 10 and
        metrics["loc"] <= 50 and
        metrics["nesting_depth"] <= 4
    )
```

#### `function_collector.py`

**Purpose:** Download 100 Python functions from permissive-license open-source repositories and stratify them into the four complexity tiers required for Experiment 2.

**Dependencies:** `requests`, `radon`, `ast`

**Tasks:**
- Fetch Python source files from raw.githubusercontent.com (no auth required)
- Extract all function definitions via `ast.walk`
- Compute cyclomatic complexity with `radon.complexity.cc_visit`
- Stratify into four tiers (25 functions each): ≤5, 6–10, 11–20, >20
- Save each function to `data/code_functions/<tier>_<idx>_<name>.py` with a header comment recording source URL, license, complexity, and tier

**Source repositories:** pytest (MIT), rich (MIT), fastapi (MIT), pydantic (MIT), httpx (BSD-3), aiohttp (Apache-2.0), tornado (Apache-2.0), sqlalchemy (MIT), celery (BSD-3).

---

#### `llm_probe.py`

**Purpose:** Submit each function to an LLM and collect responses.

**Dependencies:** `requests` (Ollama, default), `openai` (optional), `anthropic` (optional)

**Default backend:** Ollama (`http://localhost:11434/api/chat`, model `llama3.2`). The script can be switched to OpenAI or Anthropic via the `--backend` flag. No API key is required for the Ollama path.

**Tasks:**
- For each function in `code_functions/`, submit the comprehension prompt 5 times
- Record: `function_id`, `attempt`, `response_text`, `input_tokens`, `output_tokens`, `latency_ms`
- Output: raw responses CSV

**Prompt template:**
```python
PROMPT_TEMPLATE = """Given the following Python function, answer in one sentence: what does this function do?

```python
{function_code}
```"""
```

**Rate limiting:** exponential backoff with jitter, configurable `MAX_RPM`.

#### `comprehension_scorer.py`

**Purpose:** Compute SAS (manual annotation reconciliation) and SCS (embedding cosine similarity).

**Dependencies:** `sentence-transformers`, `sklearn`, `krippendorff` (or `sklearn.metrics` for Cohen's κ)

```python
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

def compute_scs(responses: list[str], model_name: str = "all-MiniLM-L6-v2") -> float:
    """Self-consistency score: mean pairwise cosine similarity of response embeddings."""
    ...

def compute_cohens_kappa(rater_a: list, rater_b: list) -> float: ...
```

#### `changepoint_analysis.py`

**Purpose:** Detect empirical change-points in LLM performance as a function of code complexity; test alignment with CDCC thresholds.

**Dependencies:** `ruptures` (change-point detection), `scipy`, `statsmodels`

```python
import ruptures as rpt

def detect_changepoints(signal: np.ndarray, n_bkps: int = 2) -> list[int]: ...
def test_threshold_alignment(detected: list[int], cdcc_threshold: int, tolerance: int = 2) -> dict: ...
```

#### `cross_model_correlation.py`

**Purpose:** Compute Spearman rank correlations of naming convention efficiency rankings across tokenizers (RQ4).

```python
from scipy.stats import spearmanr

def rank_by_efficiency(df: pd.DataFrame, tokenizer: str) -> pd.Series: ...
def cross_model_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame: ...
```

---

## 5. Results and Hypotheses

> **Status:** All three experiments complete.

| Hypothesis | Metric | Expected | Empirical Result | Status |
|---|---|---|---|---|
| H1: camelCase < dot (tokens) | inter_notation_ratio | > 1.0 | **1.199× (GPT-4o), 1.116× (GPT-4)** — p < 0.001 | Confirmed |
| H2: ranking robust across tokenizers | Spearman ρ | > 0.85 | **ρ = 1.000** for all tokenizer pairs — p < 0.001 | Confirmed |
| H3: CDCC-compliant functions have higher output/input ratio | ratio difference | > 0 | **0.141 (compliant) vs. 0.043 (violating)** — 3.3× gap, p < 0.001 | Confirmed |
| H4: LLM output exhibits diminishing marginal returns w.r.t. input complexity | β < 1 in log-log model | β < 1 | **β = 0.102** — strongly sub-linear; each 1% more input → 0.10% more output | Confirmed |
| H5: cost delta > $10K/year at enterprise scale | annual_cost_delta | > $10,000 | **$54,499/year** (GPT-4o, 95% CI: $46,902–$62,301) — p < 0.001 | Confirmed |

### 5.1 Experiment 1 — Tokenization Differential (RQ1, RQ3, RQ4)

**Token count differentials** (N=200 identifiers, Wilcoxon signed-rank, dot vs camelCase):

| Tokenizer | Mean dot/camelCase ratio | W statistic | p-value |
|---|---|---|---|
| GPT-4o (`o200k_base`) | **1.199** | 49.5 | < 0.001 |
| GPT-4 (`cl100k_base`) | **1.116** | 138.0 | < 0.001 |
| Claude proxy (`cl100k_base`) | **1.116** | 138.0 | < 0.001 |

The empirical ratio (1.12–1.20×) is statistically significant but lower than the 1.67× theoretical projection from Pereira (2026a). This discrepancy is discussed in §6.

**Cost projection** (1M API calls/day, 150 tokens/call, $0.005/1k tokens, GPT-4o):

- Point estimate: **$54,499 / year**
- 95% bootstrap CI: **[$46,902, $62,301]**

H5 is confirmed: the empirical delta substantially exceeds the $10K threshold.

### 5.2 Experiment 3 — Cross-model Tokenizer Variance (RQ4)

Spearman rank correlations of notation efficiency rankings across all tokenizer pairs:

| Pair | ρ | p-value | Robust (ρ > 0.85) |
|---|---|---|---|
| GPT-4o vs GPT-4 | 1.000 | 0.000 | Yes |
| GPT-4o vs Claude proxy | 1.000 | 0.000 | Yes |
| GPT-4 vs Claude proxy | 1.000 | 0.000 | Yes |

H2 is confirmed: the camelCase efficiency advantage is perfectly consistent across all tokenizers tested.

### 5.3 Experiment 2 — LLM Output Production Function (RQ2)

LLM probe complete: 500 responses (100 functions × 5 attempts) via Ollama/Llama 3.2 3B.

**Code corpus (N=100):**

| Tier | Complexity range | Count | CDCC status | Mean input tokens |
|---|---|---|---|---|
| Tier 1 | ≤ 5 | 25 | Compliant | 200 |
| Tier 2 | 6–10 | 25 | Compliant (boundary) | 384 |
| Tier 3 | 11–20 | 25 | Violating | 713 |
| Tier 4 | > 20 | 25 | Violating | 1,363 |

Overall: **47 compliant / 53 violating** (47%).

**Production function estimate:**

Fitting the log-log model log(output) = α + β · log(input) across the 100 functions:

- α = 2.843 (intercept)
- **β = 0.102** (output elasticity, p < 0.001)
- Interpretation: a 1% increase in input complexity produces only a **0.10% increase in output tokens** — strongly sub-linear, confirming diminishing marginal returns.

This elasticity is well below 1, consistent with a system operating under bounded rationality (Simon, 1955): as input complexity increases, the LLM satisfices by producing proportionally less output rather than scaling generation effort linearly.

**Output/input ratio by complexity tier:**

| Tier | Complexity range | Mean output tokens | Mean output/input ratio |
|---|---|---|---|
| Tier 1 | ≤ 5 | 29.5 | 0.174 |
| Tier 2 | 6–10 | 34.3 | 0.098 |
| Tier 3 | 11–20 | 32.4 | 0.053 |
| Tier 4 | > 20 | 37.1 | 0.031 |

Spearman ρ = −0.859 (p < 0.001) between complexity and output/input ratio. Note that absolute output length does increase slightly with complexity (29.5 → 37.1 tokens), but the input grows far faster — the ratio collapses by 5.6× from Tier 1 to Tier 4.

**CDCC efficiency frontier (H3):**

| CDCC status | N | Mean output/input ratio | Std |
|---|---|---|---|
| Compliant | 47 | **0.141** | 0.069 |
| Violating | 53 | **0.043** | 0.020 |

Mann-Whitney U test: p < 0.001. The 3.3× gap confirms that CDCC-compliant functions occupy the Pareto-efficient region of the LLM production space: they extract substantially more output per input token than violating functions. CDCC-violating functions are Pareto-dominated — they impose a larger input burden while receiving a disproportionately compressed response.

This finding aligns with the opportunity cost interpretation: when the model must allocate more of its effective context budget to comprehending a complex function, fewer resources remain for generation. The CDCC threshold (complexity ≤ 10, LoC ≤ 50, nesting ≤ 4) demarcates the boundary where this tradeoff tips from efficient to sub-optimal — an empirical analogue to the Miller (1956) working memory capacity limit, now observed in a transformer architecture.

---

## 6. Limitations

**Tokenizer opacity:** Anthropic does not publish Claude's tokenizer. `cl100k_base` is used as the closest public approximation; the identical results between the GPT-4 and Claude proxy columns reflect this shared encoding, not measured Claude behaviour.

**Theoretical vs empirical ratio discrepancy:** Pereira (2026a) projected a 1.67× dot/camelCase ratio via theoretical BPE analysis; empirical measurement yields 1.12–1.20×. The difference stems from corpus composition: identifiers with few compound words (e.g., "user registered") produce smaller differentials than the multi-word identifiers assumed in the theoretical model. The ratio remains statistically significant, and the projected cost delta ($54,499/year) still exceeds the $10K threshold by a factor of five.

**LLM model for Experiment 2:** Responses were collected using Llama 3.2 (3B parameters) served locally via Ollama, rather than a frontier API model (GPT-4o, Claude 3.x). The production function parameters (β, efficiency ratios) may differ under larger models with greater effective context capacity. Replication with frontier models is a priority for future work.

**Production function specification:** The log-log model assumes a constant elasticity of substitution across all complexity levels. A piecewise or non-linear specification may better capture threshold effects at specific CDCC boundaries. The elasticity estimate (β = 0.102) should be interpreted as a global average, not as a locally constant rate.

**Causal inference:** The observed output/input ratio gap between CDCC-compliant and violating functions does not establish that CDCC thresholds cause the production function shift. Confounders — function domain, abstraction level, library specificity — are partially controlled by stratification but not eliminated by design.

**Code corpus selection bias:** Functions were collected from popular, actively maintained open-source repositories (pytest, rich, fastapi, pydantic, httpx, aiohttp, tornado, sqlalchemy, celery) using permissive licenses (MIT, Apache 2.0, BSD-3). This may skew toward higher-quality, better-structured code than typical enterprise or legacy codebases. Future work should extend the corpus to include legacy systems.

**API cost model assumptions:** Token pricing evolves; cost projections use GPT-4o input pricing current at time of writing ($0.005/1k tokens) and should be recalculated against updated rate tables.

**Causal inference:** Correlations between CDCC violations and LLM performance degradation do not establish causality. Confounders (e.g., domain complexity, abstraction level) are partially controlled but not eliminated.

---

## 7. Ethical Considerations

All code functions are collected from repositories with permissive open-source licenses (MIT, Apache 2.0). No proprietary or private code is included. LLM API usage complies with provider terms of service. No personally identifiable information is processed.

---

## 8. Reproducibility

This repository is designed for full reproducibility:

- All random seeds are fixed (`RANDOM_SEED = 42`) and documented in `src/utils.py`
- All LLM responses are cached to `data/cache/` (SHA-256 keyed JSON); re-running analysis does not re-invoke the model
- Experiment 2 uses **Llama 3.2 (3B) via Ollama** (local inference, no API key required). Setup: `ollama pull llama3.2`
- The function corpus (`data/code_functions/`, N=100) is collected deterministically by `function_collector.py` using a fixed random seed and pinned repository branches
- A `Makefile` provides top-level targets: `make corpus`, `make exp1`, `make exp2`, `make exp3`, `make plots`, `make paper`
- A `requirements.txt` pins all dependency versions
- A GitHub Actions CI pipeline (`ci.yml`) validates the corpus build and unit tests on every push (Python 3.11 and 3.12)
- Results are deterministic conditional on cached LLM responses and fixed seeds

---

## 9. References

- Brooks, F.P. (1975). *The Mythical Man-Month*. Addison-Wesley.
- Cowan, N. (2001). The magical number 4 in short-term memory. *Behavioral and Brain Sciences*, 24(1), 87–114.
- Kahneman, D. (2011). *Thinking, Fast and Slow*. Farrar, Straus and Giroux.
- Miller, G.A. (1956). The magical number seven, plus or minus two. *Psychological Review*, 63(2), 81–97.
- Pereira, L.F. (2026a). Confirmation Bias in Post-LLM Software Architecture: Are We Optimizing for the Wrong Reader? DOI: 10.5281/zenodo.18627897
- Pereira, L.F. (2026b). Cognitive-Derived Constraints for AI-Assisted Software Engineering (CDCC): A Framework for Human–Machine Co-Design. DOI: 10.5281/zenodo.18735784
- Raymond, E.S. (1999). *The Cathedral and the Bazaar*. O'Reilly Media.
- Sennrich, R., Haddow, B., & Birch, A. (2016). Neural machine translation of rare words with subword units. *ACL 2016*.
- Simon, H.A. (1955). A behavioral model of rational choice. *Quarterly Journal of Economics*, 69(1), 99–118.
- Sweller, J. (1988). Cognitive load during problem solving. *Cognitive Science*, 12(2), 257–285.
- Varian, H.R. (1992). *Microeconomic Analysis* (3rd ed.). W.W. Norton & Company.
- Watson, A.H., & McCabe, T.J. (1996). Structured Testing: A Testing Methodology Using the Cyclomatic Complexity Metric. NIST Special Publication 500-235.

---

## Appendix A — Seed Identifier Corpus

The 40 seed identifiers from Pereira (2026a) Table 1, rendered in all notation variants, are available in `data/seed_identifiers.csv`. Domain labels: `order_management`, `payment`, `inventory`, `user_auth`, `notification`, `shipping`, `analytics`.

## Appendix B — CDCC Threshold Summary Table

Reproduced from Pereira (2026b) Table 2 for reference:

| Dimension | CDCC Limit | Violation Signal |
|---|---|---|
| Cyclomatic complexity | ≤ 10 | Branch explosion beyond WM capacity |
| Lines per function | ≤ 50 | Scroll-induced context loss |
| Functions per file | ≤ 9 (7±2) | Miller's Law saturation |
| Import depth | ≤ 5 | Cognitive stack overflow |
| Nesting depth | ≤ 4 | System 2 overload (Kahneman) |

---

*This document serves as both the paper draft and the specification for the accompanying Python codebase. Sections marked with code blocks define the implementation contract for each module. The paper will be finalized and submitted to Zenodo upon completion of experiments.*

---

## Appendix C — Seed Outline: Paper 4 (Proposed)

> **Working title:** *Writing for the Machine: Tokenization-Aware Conventions for LLM-Readable Academic Papers*
>
> **Framing:** A short methodological note (2,000–3,000 words) deriving practical writing guidelines from the empirical findings of this paper (Pereira, 2026c) and the CDCC framework (Pereira, 2026b). Where papers 2026a–c examined source code artifacts, Paper 4 examines *prose artifacts*: section headings, equation labels, variable names in code listings, identifier conventions in inline references, and structural choices (sentence length, nesting, list depth) — all of which affect how LLMs tokenize and process academic text.

### Hypothesised guidelines (to be derived empirically or by inference)

| Writing decision | LLM-unfriendly form | LLM-friendly form | Predicted token saving |
|---|---|---|---|
| Section heading identifiers | `4.2.1.3 Sub-sub-section` | `§4.2 Metric Definitions` | Fewer tokens, clearer anchor |
| Code identifier style in prose | `order.created`, `user.registered` | `orderCreated`, `userRegistered` | H1: ~1.15× fewer tokens |
| Long nominalized sentences | "The utilization of the framework resulted in improvements" | "The framework improved outcomes" | Shorter, fewer redundant tokens |
| Deeply nested parentheticals | "(see §3.1.2, which references Table 2 (adapted from X (2020)))" | Split into two sentences | Reduces nesting depth; aligns with CDCC §3 |
| LaTeX math labels | `\label{eq:the-very-long-equation-label}` | `\label{eq:cost-delta}` | Shorter cross-reference strings |
| Repeated full citations | "Pereira (2026b) showed... Pereira (2026b) also..." | "Pereira (2026b) showed... That work also..." | Avoids re-tokenizing long author/year strings |

### Proposed structure

1. **Introduction** — LLMs are readers; writing choices have measurable token costs
2. **Background** — BPE mechanics applied to prose (not code); dot-notation in identifiers vs. prose headings
3. **Guidelines** — Six actionable conventions with predicted effects, grounded in Experiments 1–3
4. **Validation protocol** — Short reproducibility check: apply guidelines to two versions of the same paper section; measure token counts with tiktoken
5. **Limitations** — Guidelines are tokenizer-specific; may conflict with human readability conventions
6. **Conclusion** — CDCC for prose: the same principles that bound cognitive load in code also bound LLM processing cost in text

### Connection to existing work

- Grounds every guideline in a measured result from this paper or a published CDCC threshold
- Companion to Pereira (2026a): extends the naming-convention argument from event identifiers to prose structure
- Companion to Pereira (2026b): extends the CDCC structural limits from code to academic writing conventions
- Empirical validation: tiktoken measurements on a small set of paragraph variants, consistent with the methodology of §3.1
