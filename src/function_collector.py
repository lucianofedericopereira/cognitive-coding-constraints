# -----------------------------------------------------------------------------
# Author:  Luciano Federico Pereira
# ORCID:   https://orcid.org/0009-0002-4591-6568
# Paper:   Empirical Validation of Cognitive-Derived Coding Constraints and
#          Tokenization Asymmetries in LLM-Assisted Software Engineering
# Repo:    https://github.com/lucianofedericopereira/cognitive-coding-constraints
# License: LGPL-2.1
# -----------------------------------------------------------------------------

"""
function_collector.py — Collect 100 Python functions for Experiment 2.

Downloads Python source files from a curated list of MIT / Apache 2.0
open-source repositories via the GitHub raw content API, extracts all
top-level functions, computes cyclomatic complexity with radon, and
saves exactly 25 functions per complexity tier to data/code_functions/.

Tiers (from §3.2.1):
  tier1 — complexity ≤ 5      (25 functions)
  tier2 — complexity 6–10     (25 functions)
  tier3 — complexity 11–20    (25 functions)
  tier4 — complexity > 20     (25 functions)

Each saved file contains a single function with a header comment
documenting the source repo, file path, license, and measured metrics.

Dependencies: requests, radon (both already in requirements.txt)
No GitHub token required (uses unauthenticated raw.githubusercontent.com).
"""

import ast
import textwrap
import random
import time
import requests
from pathlib import Path

import radon.complexity as rc

from utils import CODE_FUNCTIONS_DIR, RANDOM_SEED, get_logger

log = get_logger(__name__)
random.seed(RANDOM_SEED)

# ---------------------------------------------------------------------------
# Curated source files — MIT and Apache 2.0 repos, pinned to main/master
# Format: (repo_owner, repo_name, branch, file_path, license)
# ---------------------------------------------------------------------------
SOURCE_FILES = [
    # pytest — MIT
    ("pytest-dev", "pytest", "main", "src/_pytest/assertion/rewrite.py", "MIT"),
    ("pytest-dev", "pytest", "main", "src/_pytest/python.py", "MIT"),
    ("pytest-dev", "pytest", "main", "src/_pytest/runner.py", "MIT"),
    ("pytest-dev", "pytest", "main", "src/_pytest/config/__init__.py", "MIT"),
    ("pytest-dev", "pytest", "main", "src/_pytest/fixtures.py", "MIT"),
    # rich — MIT
    ("Textualize", "rich", "master", "rich/text.py", "MIT"),
    ("Textualize", "rich", "master", "rich/table.py", "MIT"),
    ("Textualize", "rich", "master", "rich/console.py", "MIT"),
    ("Textualize", "rich", "master", "rich/highlighter.py", "MIT"),
    ("Textualize", "rich", "master", "rich/markup.py", "MIT"),
    # fastapi — MIT
    ("fastapi", "fastapi", "master", "fastapi/routing.py", "MIT"),
    ("fastapi", "fastapi", "master", "fastapi/dependencies/utils.py", "MIT"),
    ("fastapi", "fastapi", "master", "fastapi/encoders.py", "MIT"),
    ("fastapi", "fastapi", "master", "fastapi/utils.py", "MIT"),
    # pydantic — MIT
    ("pydantic", "pydantic", "main", "pydantic/main.py", "MIT"),
    ("pydantic", "pydantic", "main", "pydantic/fields.py", "MIT"),
    ("pydantic", "pydantic", "main", "pydantic/_internal/_generate_schema.py", "MIT"),
    # httpx — BSD-3 (permissive — included for coverage)
    ("encode", "httpx", "master", "httpx/_client.py", "BSD-3"),
    ("encode", "httpx", "master", "httpx/_utils.py", "BSD-3"),
    # aiohttp — Apache 2.0
    ("aio-libs", "aiohttp", "master", "aiohttp/client.py", "Apache-2.0"),
    ("aio-libs", "aiohttp", "master", "aiohttp/web_request.py", "Apache-2.0"),
    ("aio-libs", "aiohttp", "master", "aiohttp/web_response.py", "Apache-2.0"),
    ("aio-libs", "aiohttp", "master", "aiohttp/connector.py", "Apache-2.0"),
    # tornado — Apache 2.0
    ("tornadoweb", "tornado", "master", "tornado/web.py", "Apache-2.0"),
    ("tornadoweb", "tornado", "master", "tornado/httpclient.py", "Apache-2.0"),
    ("tornadoweb", "tornado", "master", "tornado/ioloop.py", "Apache-2.0"),
    # sqlalchemy — MIT
    ("sqlalchemy", "sqlalchemy", "main", "lib/sqlalchemy/orm/session.py", "MIT"),
    ("sqlalchemy", "sqlalchemy", "main", "lib/sqlalchemy/sql/compiler.py", "MIT"),
    ("sqlalchemy", "sqlalchemy", "main", "lib/sqlalchemy/engine/base.py", "MIT"),
    # celery — BSD-3 (permissive)
    ("celery", "celery", "main", "celery/app/base.py", "BSD-3"),
    ("celery", "celery", "main", "celery/utils/functional.py", "BSD-3"),
]

# ---------------------------------------------------------------------------
# Tier definitions
# ---------------------------------------------------------------------------
TIERS = [
    ("tier1", lambda cc: cc <= 5),
    ("tier2", lambda cc: 6 <= cc <= 10),
    ("tier3", lambda cc: 11 <= cc <= 20),
    ("tier4", lambda cc: cc > 20),
]
FUNCTIONS_PER_TIER = 25


# ---------------------------------------------------------------------------
# GitHub raw download
# ---------------------------------------------------------------------------

def download_source(owner: str, repo: str, branch: str, path: str) -> str | None:
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.text
        log.warning("HTTP %d for %s", resp.status_code, url)
        return None
    except Exception as e:
        log.warning("Download failed for %s: %s", url, e)
        return None


# ---------------------------------------------------------------------------
# Function extraction
# ---------------------------------------------------------------------------

def extract_functions(source: str) -> list[dict]:
    """
    Parse *source* and return a list of dicts with keys:
      name, source_code, lineno, complexity
    Only top-level and class-method functions are included.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    lines = source.splitlines()
    results = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        start = node.lineno - 1
        end = node.end_lineno
        func_source = "\n".join(lines[start:end])
        try:
            func_source_dedented = textwrap.dedent(func_source)
            blocks = rc.cc_visit(func_source_dedented)
            complexity = max((b.complexity for b in blocks), default=1)
        except Exception:
            complexity = 1

        results.append({
            "name": node.name,
            "source_code": func_source_dedented,
            "lineno": node.lineno,
            "complexity": complexity,
        })

    return results


# ---------------------------------------------------------------------------
# Main collector
# ---------------------------------------------------------------------------

def collect() -> None:
    CODE_FUNCTIONS_DIR.mkdir(parents=True, exist_ok=True)

    # Buckets: tier_name → list of (func_dict, meta_dict)
    buckets: dict[str, list] = {tier: [] for tier, _ in TIERS}

    log.info("Downloading %d source files …", len(SOURCE_FILES))
    for owner, repo, branch, path, license_ in SOURCE_FILES:
        log.info("  %s/%s %s", owner, repo, path)
        source = download_source(owner, repo, branch, path)
        if source is None:
            continue

        funcs = extract_functions(source)
        log.info("    → %d functions extracted", len(funcs))

        meta = {
            "repo": f"{owner}/{repo}",
            "branch": branch,
            "file": path,
            "license": license_,
            "url": f"https://github.com/{owner}/{repo}/blob/{branch}/{path}",
        }

        for func in funcs:
            cc = func["complexity"]
            for tier_name, predicate in TIERS:
                if predicate(cc):
                    buckets[tier_name].append((func, meta))
                    break

        time.sleep(0.3)  # be polite to GitHub CDN

    # ---------------------------------------------------------------------------
    # Sample and save
    # ---------------------------------------------------------------------------
    saved_total = 0
    for tier_name, _ in TIERS:
        pool = buckets[tier_name]
        random.shuffle(pool)
        selected = pool[:FUNCTIONS_PER_TIER]

        if len(selected) < FUNCTIONS_PER_TIER:
            log.warning(
                "Tier %s: only %d functions available (need %d).",
                tier_name, len(selected), FUNCTIONS_PER_TIER,
            )

        for i, (func, meta) in enumerate(selected, 1):
            filename = f"{tier_name}_{i:03d}_{func['name'][:40]}.py"
            filepath = CODE_FUNCTIONS_DIR / filename
            header = (
                f"# Source : {meta['url']} (line {func['lineno']})\n"
                f"# License: {meta['license']}\n"
                f"# Complexity: {func['complexity']}\n"
                f"# Tier   : {tier_name}\n\n"
            )
            filepath.write_text(header + func["source_code"], encoding="utf-8")
            saved_total += 1

    log.info(
        "Saved %d functions to %s",
        saved_total, CODE_FUNCTIONS_DIR,
    )
    for tier_name, _ in TIERS:
        count = len(list(CODE_FUNCTIONS_DIR.glob(f"{tier_name}_*.py")))
        log.info("  %s: %d / %d", tier_name, count, FUNCTIONS_PER_TIER)


if __name__ == "__main__":
    collect()