# Makefile — empirical-cdcc
# Top-level targets for the reproducibility pipeline.
# Run each target in order: corpus → exp1 → exp2 → exp3 → plots → paper

PYTHON  := python
SRCDIR  := src
RESULTS := results
PLOTS   := results/plots

.PHONY: all corpus exp1 exp2 exp3 plots paper paper-html clean help

# ---------------------------------------------------------------------------
# Default
# ---------------------------------------------------------------------------
all: corpus exp1 exp2 exp3 plots
	@echo "All experiments complete. Run 'make paper' to render the PDF."

# ---------------------------------------------------------------------------
# Corpus construction (Experiment 1 prerequisite)
# ---------------------------------------------------------------------------
corpus:
	@echo "==> Building identifier corpus …"
	$(PYTHON) $(SRCDIR)/corpus_builder.py

# ---------------------------------------------------------------------------
# Experiment 1 — tokenization + cost model
# ---------------------------------------------------------------------------
exp1: corpus
	@echo "==> Running tokenizer analysis …"
	$(PYTHON) $(SRCDIR)/tokenizer_analysis.py
	@echo "==> Running cost projection …"
	$(PYTHON) $(SRCDIR)/cost_model.py

# ---------------------------------------------------------------------------
# Experiment 2 — code metrics + LLM probe + scoring + change-point
# ---------------------------------------------------------------------------
exp2:
	@echo "==> Collecting function corpus …"
	$(PYTHON) $(SRCDIR)/function_collector.py
	@echo "==> Computing code metrics …"
	$(PYTHON) $(SRCDIR)/code_metrics.py
	@echo "==> Probing LLM via Ollama (ollama must be running, model must be pulled) …"
	$(PYTHON) $(SRCDIR)/llm_probe.py --backend ollama --model llama3.2
	@echo "==> Scoring comprehension …"
	$(PYTHON) $(SRCDIR)/comprehension_scorer.py
	@echo "==> Running change-point analysis …"
	$(PYTHON) $(SRCDIR)/changepoint_analysis.py

# ---------------------------------------------------------------------------
# Experiment 3 — cross-model rank correlation
# ---------------------------------------------------------------------------
exp3: exp1
	@echo "==> Computing cross-model Spearman correlations …"
	$(PYTHON) $(SRCDIR)/cross_model_correlation.py

# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
plots: exp1 exp2 exp3
	@echo "==> Generating all figures …"
	mkdir -p $(PLOTS)
	$(PYTHON) $(SRCDIR)/plot_results.py

# ---------------------------------------------------------------------------
# Paper rendering (requires a LaTeX installation or pandoc)
# ---------------------------------------------------------------------------
# Mermaid filter converts ```mermaid blocks → PNG via mmdc (Mermaid CLI).
# Install mmdc once: npm install -g @mermaid-js/mermaid-cli
# If mmdc is absent the filter falls back gracefully to a plain code block.
MERMAID_FILTER := paper/mermaid-filter.lua

paper:
	@echo "==> Rendering paper (requires pandoc + texlive-xetex) …"
	@echo "    Mermaid → PNG via mmdc if available (npm i -g @mermaid-js/mermaid-cli)"
	pandoc paper/empirical_cdcc_paper.md \
	    --lua-filter=$(MERMAID_FILTER) \
	    --pdf-engine=xelatex \
	    --variable geometry:margin=2.5cm \
	    --variable fontsize=11pt \
	    --toc \
	    -o paper/empirical_cdcc_paper.pdf
	@echo "Paper written to paper/empirical_cdcc_paper.pdf"

paper-html:
	@echo "==> Rendering paper as HTML (no LaTeX required) …"
	pandoc paper/empirical_cdcc_paper.md \
	    --lua-filter=$(MERMAID_FILTER) \
	    --standalone \
	    -o paper/empirical_cdcc_paper.html
	@echo "Paper written to paper/empirical_cdcc_paper.html"

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
test:
	@echo "==> Running unit tests …"
	$(PYTHON) -m pytest tests/ -v --tb=short

# ---------------------------------------------------------------------------
# Housekeeping
# ---------------------------------------------------------------------------
clean:
	@echo "==> Removing generated artefacts (keeps cached API responses) …"
	rm -f data/extended_corpus.csv data/code_metrics.csv
	rm -f $(RESULTS)/exp1_token_counts.csv
	rm -f $(RESULTS)/exp2_raw_responses.csv
	rm -f $(RESULTS)/exp2_comprehension_scores.csv
	rm -f $(RESULTS)/exp3_rank_correlations.csv
	rm -rf $(PLOTS)
	rm -rf paper/figures paper/empirical_cdcc_paper.pdf paper/empirical_cdcc_paper.html
	find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

help:
	@echo "Available targets:"
	@echo "  corpus  — build the 200-identifier corpus"
	@echo "  exp1    — tokenization analysis + cost model"
	@echo "  exp2    — code metrics + LLM probe + scoring + change-point"
	@echo "  exp3    — cross-model rank correlations"
	@echo "  plots   — generate all paper figures"
	@echo "  paper      — render PDF via pandoc + xelatex (texlive-xetex)"
	@echo "  paper-html — render HTML via pandoc (no LaTeX needed)"
	@echo "  test    — run unit tests"
	@echo "  clean   — remove generated files (preserves API cache)"
