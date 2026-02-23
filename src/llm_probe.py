# -----------------------------------------------------------------------------
# Author:  Luciano Federico Pereira
# ORCID:   https://orcid.org/0009-0002-4591-6568
# Paper:   Empirical Validation of Cognitive-Derived Coding Constraints and
#          Tokenization Asymmetries in LLM-Assisted Software Engineering
# Repo:    https://github.com/lucianofedericopereira/cognitive-coding-constraints
# License: LGPL-2.1
# -----------------------------------------------------------------------------

"""
llm_probe.py — Experiment 2: LLM API calls and response collection.

Submits each function in data/code_functions/ to an LLM 5 times
using the comprehension prompt defined in §3.2.2 of the paper.

Supported backends:
  ollama    — local inference via Ollama (no API key, default)
  openai    — OpenAI API (requires OPENAI_API_KEY)
  anthropic — Anthropic API (requires ANTHROPIC_API_KEY)

Ollama usage:
  1. Install: curl -fsSL https://ollama.com/install.sh | sh
  2. Pull model: ollama pull llama3.2
  3. Run: python llm_probe.py --backend ollama --model llama3.2

All responses are cached in data/cache/ to allow re-running analysis
without re-incurring cost (see utils.cache_get / cache_set).
"""

import os
import time
import random
import csv
from pathlib import Path

from dotenv import load_dotenv
from utils import CODE_FUNCTIONS_DIR, RESULTS_DIR, cache_get, cache_set, get_logger

load_dotenv()
log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
N_ATTEMPTS: int = 5
MAX_RPM: int = 20          # requests per minute ceiling (conservative)
BACKOFF_BASE: float = 2.0  # exponential backoff base (seconds)
MAX_RETRIES: int = 5

PROMPT_TEMPLATE = (
    "Given the following Python function, answer in one sentence: "
    "what does this function do?\n\n```python\n{function_code}\n```"
)

RAW_RESPONSES_CSV = RESULTS_DIR / "exp2_raw_responses.csv"


# ---------------------------------------------------------------------------
# Backend adapters
# ---------------------------------------------------------------------------

def _call_openai(prompt: str, model: str = "gpt-4o") -> dict:
    import openai
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=150,
    )
    msg = response.choices[0].message.content.strip()
    return {
        "response_text": msg,
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
        "model": model,
    }


def _call_anthropic(prompt: str, model: str = "claude-3-5-sonnet-20241022") -> dict:
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=model,
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )
    msg = response.content[0].text.strip()
    return {
        "response_text": msg,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "model": model,
    }


def _call_ollama(prompt: str, model: str = "llama3.2") -> dict:
    """
    Call a locally running Ollama instance via its REST API.
    Ollama must be running: `ollama serve` (starts automatically on most installs).
    Model must be pulled first: `ollama pull llama3.2`

    Token counts are approximated from character length since Ollama's
    /api/generate endpoint does not expose tokenizer counts directly.
    The /api/chat endpoint with stream=False returns eval_count (output tokens)
    and prompt_eval_count (input tokens).
    """
    import requests as req
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0, "num_predict": 150},
    }
    resp = req.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    msg = data["message"]["content"].strip()
    return {
        "response_text": msg,
        "input_tokens": data.get("prompt_eval_count", -1),
        "output_tokens": data.get("eval_count", -1),
        "model": model,
    }


BACKENDS = {
    "ollama": _call_ollama,
    "openai": _call_openai,
    "anthropic": _call_anthropic,
}


# ---------------------------------------------------------------------------
# Rate-limited, cached call
# ---------------------------------------------------------------------------

def _call_with_backoff(prompt: str, backend: str, model: str) -> dict:
    cache_key = {"prompt": prompt, "backend": backend, "model": model}
    cached = cache_get(cache_key)
    if cached is not None:
        log.debug("Cache hit for prompt hash.")
        return cached

    fn = BACKENDS[backend]
    for attempt in range(MAX_RETRIES):
        try:
            t0 = time.perf_counter()
            result = fn(prompt, model=model)
            result["latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            cache_set(cache_key, result)
            return result
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = BACKOFF_BASE ** attempt + random.uniform(0, 1)
            log.warning("API error (%s), retrying in %.1fs …", e, wait)
            time.sleep(wait)


# ---------------------------------------------------------------------------
# Main probe
# ---------------------------------------------------------------------------

def run(backend: str = "ollama", model: str = "llama3.2") -> None:
    files = sorted(CODE_FUNCTIONS_DIR.glob("*.py"))
    if not files:
        log.error("No .py files found in %s — run corpus collection first.", CODE_FUNCTIONS_DIR)
        return

    log.info("Probing %d functions × %d attempts via %s/%s …",
             len(files), N_ATTEMPTS, backend, model)

    min_interval = 60.0 / MAX_RPM

    RAW_RESPONSES_CSV.parent.mkdir(parents=True, exist_ok=True)

    # Resume support: load already-completed (function_id, attempt) pairs
    completed: set[tuple[str, int]] = set()
    write_header = True
    if RAW_RESPONSES_CSV.exists() and RAW_RESPONSES_CSV.stat().st_size > 50:
        import pandas as pd
        existing = pd.read_csv(RAW_RESPONSES_CSV)
        completed = set(zip(existing["function_id"], existing["attempt"].astype(int)))
        write_header = False
        log.info("Resuming — %d / %d calls already cached in CSV.", len(completed), len(files) * N_ATTEMPTS)

    FIELDNAMES = ["function_id", "attempt", "response_text",
                  "input_tokens", "output_tokens", "latency_ms", "model"]

    mode = "a" if not write_header else "w"
    with open(RAW_RESPONSES_CSV, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()

        for path in files:
            function_id = path.stem
            code = path.read_text(encoding="utf-8")
            prompt = PROMPT_TEMPLATE.format(function_code=code)

            for attempt in range(1, N_ATTEMPTS + 1):
                if (function_id, attempt) in completed:
                    continue

                t_start = time.monotonic()
                result = _call_with_backoff(prompt, backend, model)
                writer.writerow({
                    "function_id": function_id,
                    "attempt": attempt,
                    "response_text": result["response_text"],
                    "input_tokens": result["input_tokens"],
                    "output_tokens": result["output_tokens"],
                    "latency_ms": result.get("latency_ms", -1),
                    "model": result.get("model", model),
                })
                f.flush()

                elapsed = time.monotonic() - t_start
                if elapsed < min_interval:
                    time.sleep(min_interval - elapsed)

    log.info("Raw responses written to %s", RAW_RESPONSES_CSV)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LLM comprehension probe (Experiment 2)")
    parser.add_argument("--backend", choices=list(BACKENDS), default="ollama")
    parser.add_argument("--model", default="llama3.2")
    args = parser.parse_args()
    run(backend=args.backend, model=args.model)