# Source : https://github.com/pytest-dev/pytest/blob/main/src/_pytest/assertion/rewrite.py (line 561)
# License: MIT
# Complexity: 19
# Tier   : tier3

def _get_assertion_exprs(src: bytes) -> dict[int, str]:
    """Return a mapping from {lineno: "assertion test expression"}."""
    ret: dict[int, str] = {}

    depth = 0
    lines: list[str] = []
    assert_lineno: int | None = None
    seen_lines: set[int] = set()

    def _write_and_reset() -> None:
        nonlocal depth, lines, assert_lineno, seen_lines
        assert assert_lineno is not None
        ret[assert_lineno] = "".join(lines).rstrip().rstrip("\\")
        depth = 0
        lines = []
        assert_lineno = None
        seen_lines = set()

    tokens = tokenize.tokenize(io.BytesIO(src).readline)
    for tp, source, (lineno, offset), _, line in tokens:
        if tp == tokenize.NAME and source == "assert":
            assert_lineno = lineno
        elif assert_lineno is not None:
            # keep track of depth for the assert-message `,` lookup
            if tp == tokenize.OP and source in "([{":
                depth += 1
            elif tp == tokenize.OP and source in ")]}":
                depth -= 1

            if not lines:
                lines.append(line[offset:])
                seen_lines.add(lineno)
            # a non-nested comma separates the expression from the message
            elif depth == 0 and tp == tokenize.OP and source == ",":
                # one line assert with message
                if lineno in seen_lines and len(lines) == 1:
                    offset_in_trimmed = offset + len(lines[-1]) - len(line)
                    lines[-1] = lines[-1][:offset_in_trimmed]
                # multi-line assert with message
                elif lineno in seen_lines:
                    lines[-1] = lines[-1][:offset]
                # multi line assert with escaped newline before message
                else:
                    lines.append(line[:offset])
                _write_and_reset()
            elif tp in {tokenize.NEWLINE, tokenize.ENDMARKER}:
                _write_and_reset()
            elif lines and lineno not in seen_lines:
                lines.append(line)
                seen_lines.add(lineno)

    return ret