# -----------------------------------------------------------------------------
# Author:  Luciano Federico Pereira
# ORCID:   https://orcid.org/0009-0002-4591-6568
# Paper:   Empirical Validation of Cognitive-Derived Coding Constraints and
#          Tokenization Asymmetries in LLM-Assisted Software Engineering
# Repo:    https://github.com/lucianofedericopereira/cognitive-coding-constraints
# License: LGPL-2.1
# -----------------------------------------------------------------------------

"""
ascii_to_dirtree.py — Convert an ASCII directory tree to LaTeX dirtree syntax.

Usage:
    python src/ascii_to_dirtree.py          # prints dirtree block to stdout
    python src/ascii_to_dirtree.py --patch  # replaces the block in the paper

dirtree syntax:
    .1 root/.
    .2 child/.
    .3 grandchild.txt.

Rules:
    - Root line (no ├/└ prefix) → level 1
    - Each 4-space / │-indent block adds one level
    - Inline annotations (after the name) → appended in \\small\\textit{...}
    - Names containing underscores are escaped for LaTeX
    - Names ending with / are kept as-is (dirtree renders folders differently)
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PAPER = ROOT / "paper" / "empirical_cdcc_paper.md"

# The ASCII tree as it appears in the paper (fenced code block content)
# Parsed from the paper at runtime — see extract_tree_block().

TREE_CHARS = re.compile(r"[├└│─\s]+")


def escape_latex(text: str) -> str:
    """Escape LaTeX special characters in a tree node name."""
    # Order matters: backslash first
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("_", r"\_"),
        ("%", r"\%"),
        ("&", r"\&"),
        ("#", r"\#"),
        ("$", r"\$"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def parse_level(line: str) -> int:
    """
    Return the dirtree level (1-based) for a tree line.

    Root line (no box-drawing chars) → 1
    Each 4-char indent block (│   or    ) → +1 level starting from 2.
    """
    if not re.search(r"[├└│]", line):
        # Root line
        return 1
    # Find position of ├ or └
    m = re.search(r"[├└]", line)
    if m is None:
        return 1
    indent = m.start()
    # Each indentation unit is 4 chars (│   )
    return indent // 4 + 2


def parse_node(line: str) -> tuple[str, str]:
    """
    Return (name, annotation) from a tree line.

    '│   ├── seed_identifiers.csv        40 identifiers from Pereira 2026a'
    → ('seed_identifiers.csv', '40 identifiers from Pereira 2026a')
    """
    # Strip leading tree characters (│, ├, └, ─, spaces)
    stripped = re.sub(r"^[│├└─\s]+", "", line).rstrip()

    # Split name from annotation (2+ spaces)
    parts = re.split(r"\s{2,}", stripped, maxsplit=1)
    name = parts[0].strip()
    annotation = parts[1].strip() if len(parts) > 1 else ""
    return name, annotation


def to_dirtree(ascii_lines: list[str]) -> str:
    """Convert list of ASCII tree lines to a \\dirtree{} block."""
    entries = []
    for raw in ascii_lines:
        line = raw.rstrip()
        if not line:
            continue

        level = parse_level(line)
        name, annotation = parse_node(line)

        name_tex = escape_latex(name)

        if annotation:
            ann_tex = escape_latex(annotation)
            node_text = rf"{name_tex} \small\textit{{{ann_tex}}}"
        else:
            node_text = name_tex

        entries.append(f".{level} {node_text}.")

    lines = ["\\dirtree{%"] + entries + ["}"]
    return "\n".join(lines)


def extract_tree_block(paper_text: str) -> tuple[int, int, list[str]]:
    """
    Find the fenced ASCII tree block in the paper.
    Returns (start_line_idx, end_line_idx, tree_lines).
    The block is delimited by ``` lines.
    """
    lines = paper_text.splitlines()
    in_block = False
    block_lines = []
    start_idx = end_idx = -1

    for i, line in enumerate(lines):
        if line.strip() == "```" and not in_block:
            # Check if next lines look like a directory tree (contain ├ or └)
            lookahead = "\n".join(lines[i+1:i+10])
            if "├" in lookahead or "└" in lookahead or "empirical-cdcc" in lookahead:
                in_block = True
                start_idx = i
                continue
        if in_block:
            if line.strip() == "```":
                end_idx = i
                break
            block_lines.append(line)

    return start_idx, end_idx, block_lines


def patch_paper(dirtree_block: str) -> None:
    """Replace the ASCII tree block in the paper with a raw LaTeX dirtree block."""
    text = PAPER.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    start_idx, end_idx, _ = extract_tree_block(text)
    if start_idx == -1:
        print("ERROR: Could not find ASCII tree block in paper.")
        sys.exit(1)

    raw_latex_block = (
        "```{=latex}\n"
        + dirtree_block
        + "\n```\n"
    )

    # Replace lines start_idx..end_idx (inclusive) with the new block
    new_lines = lines[:start_idx] + [raw_latex_block] + lines[end_idx + 1:]
    PAPER.write_text("".join(new_lines), encoding="utf-8")
    print(f"Paper patched: {PAPER}")


def main() -> None:
    patch = "--patch" in sys.argv

    paper_text = PAPER.read_text(encoding="utf-8")
    start_idx, end_idx, tree_lines = extract_tree_block(paper_text)

    if start_idx == -1:
        print("ERROR: Could not find ASCII tree block in paper.")
        sys.exit(1)

    dirtree_block = to_dirtree(tree_lines)

    if patch:
        patch_paper(dirtree_block)
    else:
        print(dirtree_block)


if __name__ == "__main__":
    main()