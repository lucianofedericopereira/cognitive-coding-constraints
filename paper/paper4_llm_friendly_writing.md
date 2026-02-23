# Writing for the Machine: Tokenization-Aware Conventions for LLM-Readable Academic Papers

**Author:** Luciano Federico Pereira
**ORCID:** 0009-0002-4591-6568
**Affiliation:** Independent Researcher
**Status:** Working Paper — Methodological Note
**Companion Papers:**
- Pereira, L.F. (2026a). *Confirmation Bias in Post-LLM Software Architecture: Are We Optimizing for the Wrong Reader?* DOI: [10.5281/zenodo.18627897](https://doi.org/10.5281/zenodo.18627897)
- Pereira, L.F. (2026b). *Cognitive-Derived Constraints for AI-Assisted Software Engineering (CDCC): A Framework for Human–Machine Co-Design.* DOI: [10.5281/zenodo.18735784](https://doi.org/10.5281/zenodo.18735784)
- Pereira, L.F. (2026c). *Empirical Validation of Cognitive-Derived Coding Constraints and Tokenization Asymmetries in LLM-Assisted Software Engineering.* (this series, companion paper)

---

## Abstract

Academic papers are increasingly processed by Large Language Models — for summarization, literature review, code generation from methodology sections, and retrieval-augmented generation. Yet academic writing conventions evolved for human readers and have never been evaluated for their token efficiency. This note derives six writing guidelines from the empirical findings of Pereira (2026c) and the structural principles of the CDCC framework (Pereira, 2026b). We measure each guideline's token effect directly using the `tiktoken` library. The results show that common academic writing habits — nominalization, deep parenthetical nesting, repeated full citations, and dot-notation identifiers in prose — impose measurable token costs of 14–56% per passage relative to equivalent prose written with token efficiency in mind. We propose that the same structural principles that reduce cognitive load for human readers also reduce token cost for LLM readers, extending the CDCC convergence hypothesis from code artifacts to prose artifacts.

**Keywords:** tokenization, BPE, academic writing, LLM, prose efficiency, CDCC, cognitive load, text processing

---

## 1. Introduction

A working paper is read by its author, by reviewers, and by colleagues. In 2026 it is also read — routinely, and often first — by Large Language Models. Researchers feed papers into LLM-powered literature assistants. Engineers ask chat interfaces to explain methodology sections. Retrieval-augmented generation pipelines embed papers in vector stores and retrieve them chunk by chunk. In every case, the LLM processes the text as a sequence of tokens, and the number of tokens determines cost, latency, and the fraction of context window available for reasoning.

Academic writing conventions have never been designed with this consumer in mind. They were designed to communicate complex ideas to expert human readers with deep domain knowledge, long-term memory, and the ability to re-read. The conventions that serve human readers — heavy nominalization for formality, deeply nested parentheticals for precision, repeated full citations for traceability — are not obviously optimal for LLM readers, which process text linearly and charge per token.

Pereira (2026a) showed that a single naming convention choice — dot notation vs. camelCase — produces a 1.12–1.20× token differential at the identifier level, with economically significant consequences at scale. Pereira (2026b) proposed that the same structural boundaries that limit cognitive load for human developers correspond to inflection points in LLM processing quality. Pereira (2026c) measured both effects empirically. This note extends the argument from code identifiers to prose text: the same BPE tokenization logic that penalizes `order.created` relative to `orderCreated` also penalizes nominalized academic prose relative to direct, verb-first writing.

We make no claim that researchers should abandon clarity for token efficiency. The goal is to make researchers *aware* of the token cost of common stylistic choices, so they can make informed decisions — especially in methodology sections, code listings, and identifier-heavy technical descriptions where LLM processing is most consequential.

### 1.1 Scope

This note covers six writing decisions that arise in empirical computer science papers. All measurements use `tiktoken` with `o200k_base` (GPT-4o) and `cl100k_base` (GPT-4 / Claude proxy), consistent with the tokenizer matrix in Pereira (2026c). Prose style guidance draws on Williams (2014), Zobel (2015), and *The Chicago Guide to Writing about Numbers* (Miller, 2015); in all six cases the token-efficient form also aligns with these guides' recommendations, suggesting that good prose and LLM-friendly prose are more aligned than they might appear.

---

## 2. Background

### 2.1 BPE Tokenization and Prose

Byte-Pair Encoding tokenizers (Sennrich et al., 2016) build vocabularies from frequent character sequences. A common English word like "confirms" may encode as a single token; a nominalization like "confirmation" may encode as two or three tokens ("confirm", "ation" or "confirm", "at", "ion") depending on vocabulary coverage. Pereira (2026c) showed this effect at the identifier level: dot notation forces vocabulary boundaries (each segment tokenized independently) while camelCase allows the full compound to be recognized.

The same logic applies to prose. Nominalization compounds short verbs into longer nouns: "utilize" → "utilization" (one token → typically two). Deeply nested parenthetical clauses produce long, rarely-seen token sequences that match poorly against trained vocabulary entries. Repeated full author-year citation strings (`Pereira (2026a)`, `Pereira (2026b)`) are re-tokenized in full each time they appear.

### 2.2 CDCC Structural Limits Applied to Prose

Pereira (2026b) derived structural limits for code artifacts from cognitive science: cyclomatic complexity ≤ 10, lines per function ≤ 50, nesting depth ≤ 4, functions per file ≤ 7±2. Each limit maps to a cognitive constraint (working memory capacity, chunking limits, stack depth). The convergence hypothesis — that these limits also correspond to LLM processing quality inflection points — was partially confirmed in Pereira (2026c): the output/input token ratio decreases sharply with code complexity (Spearman ρ = −0.859, p < 0.001), indicating the model cannot compress arbitrarily complex inputs into a fixed-length output.

The same principle applies to prose. A sentence with four levels of nested clauses imposes the same kind of parsing stack depth on an LLM that a function with four levels of nesting imposes on a human reader. A paragraph that extends for 15 lines without a full stop exceeds the analogue of LoC ≤ 50. We propose these parallels as working hypotheses, not proven claims; the token measurements below provide partial empirical grounding.

---

## 3. Six Writing Guidelines

For each guideline we show: the unfriendly form, the friendly form, and the token count measured with `tiktoken` (`o200k_base` / `cl100k_base`). All examples are drawn from real passages in papers in this series or constructed to be representative.

### 3.1 Avoid Nominalization

**Principle (Williams, 2014):** Prefer verbs over their noun forms. "The utilization of X" → "Using X". "Confirmation was obtained" → "We confirmed".

Nominalization inflates word count and produces multi-token noun phrases that decompose less efficiently than the underlying verbs.

| Form | Example | Tokens (GPT-4o / GPT-4) |
|---|---|---|
| Nominalized | "The utilization of the dot-notation-based event.identifier.scheme produced a measurable tokenization overhead that was quantified through the application of the theoretical BPE analysis framework…" | 68 / 69 |
| Verb-first | "Dot notation produces measurable token overhead. Pereira (2026a) projected this through theoretical BPE analysis; experiments in this paper confirmed it empirically." | 30 / 31 |

**Saving: 56%** on this passage. The verb-first version also follows Williams' principle that readers should encounter the character (subject) before the action (verb) without intervening nominalized abstractions.

### 3.2 Use camelCase for Code Identifiers in Prose

**Principle (Pereira, 2026a, 2026c):** When writing code identifiers inline in prose, prefer camelCase over dot notation. This is consistent with naming identifiers in camelCase when used as variables; the prose context does not change the tokenizer's behaviour.

| Form | Example | Tokens (GPT-4o / GPT-4) |
|---|---|---|
| Dot notation | "`order.created`, `payment.refund.initiated`, `user.registration.confirmed`" | 21 / 20 |
| camelCase | "`orderCreated`, `paymentRefundInitiated`, `userRegistrationConfirmed`" | 18 / 19 |

**Saving: 14%** on this passage. The effect compounds over papers with dozens of event identifiers (Pereira (2026c) contains 200 in its corpus).

*Note:* When dot notation is the *subject of discussion* (e.g., "the event `order.created` uses dot notation"), the dot-notation form must be preserved to avoid misrepresentation.

### 3.3 Limit Parenthetical Nesting Depth

**Principle (Zobel, 2015; CDCC §3 nesting ≤ 4):** Parenthetical clauses within parenthetical clauses impose a parsing stack. Prose with three or more levels of nesting ("(… (… (…) …) …)") is hard for both human and LLM readers to parse.

| Form | Example | Tokens (GPT-4o / GPT-4) |
|---|---|---|
| Nested | "This result (see Table 3, which reproduces the data from Pereira (2026a) Table 1 (originally from a theoretical BPE analysis)) confirms the hypothesis." | 37 / 38 |
| Flat | "This result confirms H1. The data appears in Table 3, reproduced from Pereira (2026a) Table 1." | 26 / 27 |

**Saving: 30%**. The flat form also improves readability by separating the assertion from its evidence into adjacent sentences — a structure both Williams and Zobel recommend.

### 3.4 Avoid Repeating Full Citation Strings

**Principle:** When a work has been cited in the immediately preceding sentence, use "that work", "the same paper", or a short reference instead of repeating the full author-year string.

| Form | Example | Tokens (GPT-4o / GPT-4) |
|---|---|---|
| Repeated | "Pereira (2026b) derived the CDCC thresholds from cognitive science. Pereira (2026b) also proposed the convergence hypothesis." | 34 / 34 |
| Shortened | "Pereira (2026b) derived the CDCC thresholds from cognitive science. That work also proposed the convergence hypothesis." | 24 / 24 |

**Saving: 29%** on this two-sentence pair. Across a paper with 40+ citations, the aggregate saving is substantial. The shortened form also reduces visual repetition, which both Williams and Zobel flag as a writing defect.

### 3.5 Limit Section Heading Depth

**Principle (CDCC §3 nesting ≤ 4):** Section headings like `4.2.1.3 Sub-sub-section` produce deeply numbered strings that consume tokens and provide little semantic value once the reader is inside the section. Two levels (`§4.2 Metric Definitions`) are sufficient for most papers.

| Form | Example | Tokens (GPT-4o / GPT-4) |
|---|---|---|
| Deep numbering | "4.2.1.3 Threshold Detection Sub-analysis" | 12 / 13 |
| Shallow numbering | "§4.2 Threshold Detection" | 6 / 6 |

**Saving: 50%** on the heading itself. When headings appear as cross-references in the body ("see Section 4.2.1.3"), the saving recurs at each mention.

### 3.6 Prefer Short Equation and Figure Labels

**Principle:** LaTeX labels like `\label{eq:the-very-long-equation-for-annual-cost-delta}` appear as raw strings in pre-processed text fed to LLMs. Shorter labels reduce token consumption in the source markup.

| Form | Example | Tokens (GPT-4o) |
|---|---|---|
| Long label | `\label{eq:the-very-long-equation-for-annual-cost-delta}` | 19 |
| Short label | `\label{eq:cost-delta}` | 8 |

**Saving: 58%** on the label string. For papers processed as LaTeX source (e.g., ar5iv, Semantic Scholar pre-processing), label tokens accumulate across dozens of equations and figures.

---

## 4. Validation: Token Count on a Full Abstract

To measure the cumulative effect of all six guidelines applied together, we take the original abstract of Pereira (2026c) and produce a guideline-compliant version.

**Original abstract** (before applying guidelines):

> Two prior theoretical works proposed, respectively, that (1) dot-notation naming conventions in Event-Driven Architectures produce measurable tokenization overhead for transformer-based LLMs (Pereira, 2026a), and (2) that cognitive-science-grounded structural limits for code artifacts may simultaneously reduce cognitive load for human developers and contextual degradation for LLM co-developers (Pereira, 2026b). Both claims were articulated as testable hypotheses but lacked empirical grounding. This paper closes that gap. We present a reproducible experimental framework — implemented in Python and executed against the OpenAI tiktoken library and the Hugging Face tokenizer ecosystem — that empirically measures: (i) token count differentials…

**After style pass** (abstract as it now appears in Pereira (2026c)):

> Two prior theoretical works proposed that dot-notation naming conventions produce measurable token overhead for transformer-based LLMs (Pereira, 2026a) and that cognitive-science-grounded structural limits on code artifacts correspond to inflection points in LLM processing quality (Pereira, 2026b). Both claims remained untested. This paper provides the empirical evidence. We ran three experiments using a reproducible Python pipeline…

| Version | GPT-4o tokens | GPT-4 tokens |
|---|---|---|
| Original | 147 | 148 |
| After style pass | 118 | 119 |

**Saving: 20%** on the abstract. Given that most LLM-powered literature tools process abstracts first (and often only), a 20% reduction in abstract token count is directly consequential for retrieval cost and context window utilization.

---

## 5. Discussion

### 5.1 Alignment with Human Readability Guides

All six guidelines align with recommendations in Williams (2014), Zobel (2015), and *The Chicago Guide to Writing about Numbers* (Miller, 2015). This is not a coincidence. Both human readers and LLM tokenizers are penalized by the same structural properties: long nominalized phrases that require more cognitive/token units to process, deep nesting that increases parsing complexity, repeated redundant strings that consume memory/context without adding information. The CDCC convergence hypothesis (Pereira, 2026b) predicted this alignment: the structural properties that exceed human working memory limits are the same properties that produce disproportionate token costs. This paper provides prose-level evidence consistent with that prediction.

### 5.2 When Not to Apply These Guidelines

Guidelines 3.1 (avoid nominalization) and 3.4 (avoid repeated citations) should yield to precision when the nominalized or repeated form is technically necessary. "Tokenization" as a noun names a process; it cannot always be replaced by "tokenizing". Repeated citations are required in formal contexts where each claim must be independently sourced.

Guideline 3.2 (camelCase identifiers) must not be applied when dot notation is the subject of discussion — substituting `orderCreated` for `order.created` in a sentence that analyzes dot-notation structure would falsify the content.

These are editorial judgements, not mechanical rules. The six guidelines are offered as heuristics for revision, not as algorithmic transformations.

### 5.3 Limitations

**Tokenizer-specificity:** All measurements use `o200k_base` and `cl100k_base`. Results may differ for SentencePiece-based tokenizers (Llama 3, Mistral) where vocabulary coverage of academic terms varies.

**Genre constraint:** Guidelines are derived from empirical computer science papers. They may apply differently in mathematical, humanities, or clinical research writing.

**No ground-truth LLM evaluation:** This paper measures token counts; it does not directly measure whether guideline-compliant prose produces better LLM comprehension or retrieval performance. That evaluation is left for future work, using a methodology analogous to Pereira (2026c) Experiment 2 applied to prose passages.

**Human readability trade-off:** We assert without formal measurement that the guideline-compliant forms are at least as readable as the originals. Williams (2014) and Zobel (2015) provide external support for this claim, but a controlled readability study would strengthen it.

---

## 6. Conclusion

LLMs are a new and growing class of readers of academic papers. The token costs they impose on verbose, nominalized, deeply nested prose are measurable and consequential — 14–56% per passage in our examples, 20% on a full abstract. The six guidelines proposed here reduce these costs while simultaneously improving prose quality for human readers, consistent with standard style guides. The CDCC convergence hypothesis (Pereira, 2026b) predicted that the structural properties harmful to human readers would also prove harmful to LLM readers; this paper provides the first prose-level evidence consistent with that prediction.

We propose a simple revision heuristic: before submitting a paper, count its tokens using `tiktoken`. If the abstract exceeds 200 tokens, apply guidelines 3.1 and 3.3 first. If the methodology section contains dot-notation identifiers, apply 3.2. If the related work section repeats the same author-year string four or more times in a paragraph, apply 3.4. These are small changes. Over a paper read by 10,000 LLM queries, they compound.

---

## References

- Miller, J.E. (2015). *The Chicago Guide to Writing about Numbers* (2nd ed.). University of Chicago Press.
- Pereira, L.F. (2026a). Confirmation Bias in Post-LLM Software Architecture: Are We Optimizing for the Wrong Reader? DOI: 10.5281/zenodo.18627897
- Pereira, L.F. (2026b). Cognitive-Derived Constraints for AI-Assisted Software Engineering (CDCC): A Framework for Human–Machine Co-Design. DOI: 10.5281/zenodo.18735784
- Pereira, L.F. (2026c). Empirical Validation of Cognitive-Derived Coding Constraints and Tokenization Asymmetries in LLM-Assisted Software Engineering. (companion paper, this series)
- Sennrich, R., Haddow, B., & Birch, A. (2016). Neural machine translation of rare words with subword units. *ACL 2016*.
- Williams, J.M. (2014). *Style: Lessons in Clarity and Grace* (11th ed.). Pearson.
- Zobel, J. (2015). *Writing for Computer Science* (3rd ed.). Springer.

---

## Appendix A — Validation Measurements

All measurements use `tiktoken` (`o200k_base` for GPT-4o, `cl100k_base` for GPT-4). Code available in the companion repository.

| Guideline | Unfriendly tokens (4o/4) | Friendly tokens (4o/4) | Saving |
|---|---|---|---|
| 3.1 No nominalization | 68 / 69 | 30 / 31 | **56%** |
| 3.2 camelCase identifiers | 21 / 20 | 18 / 19 | **14%** |
| 3.3 Flat citations | 37 / 38 | 26 / 27 | **30%** |
| 3.4 No repeated citations | 34 / 34 | 24 / 24 | **29%** |
| 3.5 Shallow headings | 12 / 13 | 6 / 6 | **50%** |
| 3.6 Short LaTeX labels | 19 / — | 8 / — | **58%** |
| Full abstract | 147 / 148 | 118 / 119 | **20%** |

---

*This paper is the fourth in a series. Papers 2026a–c are published on Zenodo. This working paper will be submitted to Zenodo upon completion of the companion empirical study (Pereira, 2026c).*
