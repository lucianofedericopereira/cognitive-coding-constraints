"""
llm_probe.py — Experiment 2: LLM API calls and response collection.

Submits each function in data/code_functions/ to an LLM 5 times
using the comprehension prompt defined in §3.2.2 of the paper.

Supported backends: openai (default), anthropic.
Set OPENAI_API_KEY or ANTHROPIC_API_KEY in the environment (or .env).

All responses are cached in data/cache/ to enable re-running analysis
without re-incurring API costs (see utils.cache_get / cache_set).
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


BACKENDS = {
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

def run(backend: str = "openai", model: str = "gpt-4o") -> None:
    files = sorted(CODE_FUNCTIONS_DIR.glob("*.py"))
    if not files:
        log.error("No .py files found in %s — run corpus collection first.", CODE_FUNCTIONS_DIR)
        return

    log.info("Probing %d functions × %d attempts via %s/%s …",
             len(files), N_ATTEMPTS, backend, model)

    min_interval = 60.0 / MAX_RPM

    RAW_RESPONSES_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(RAW_RESPONSES_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "function_id", "attempt", "response_text",
            "input_tokens", "output_tokens", "latency_ms", "model",
        ])
        writer.writeheader()

        for path in files:
            function_id = path.stem
            code = path.read_text(encoding="utf-8")
            prompt = PROMPT_TEMPLATE.format(function_code=code)

            for attempt in range(1, N_ATTEMPTS + 1):
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
    parser.add_argument("--backend", choices=list(BACKENDS), default="openai")
    parser.add_argument("--model", default="gpt-4o")
    args = parser.parse_args()
    run(backend=args.backend, model=args.model)
