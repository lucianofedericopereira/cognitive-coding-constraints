# Source : https://github.com/pytest-dev/pytest/blob/main/src/_pytest/assertion/rewrite.py (line 692)
# License: MIT
# Complexity: 22
# Tier   : tier4

def run(self, mod: ast.Module) -> None:
    """Find all assert statements in *mod* and rewrite them."""
    if not mod.body:
        # Nothing to do.
        return

    # We'll insert some special imports at the top of the module, but after any
    # docstrings and __future__ imports, so first figure out where that is.
    doc = getattr(mod, "docstring", None)
    expect_docstring = doc is None
    if doc is not None and self.is_rewrite_disabled(doc):
        return
    pos = 0
    for item in mod.body:
        match item:
            case ast.Expr(value=ast.Constant(value=str() as doc)) if (
                expect_docstring
            ):
                if self.is_rewrite_disabled(doc):
                    return
                expect_docstring = False
            case ast.ImportFrom(level=0, module="__future__"):
                pass
            case _:
                break
        pos += 1
    # Special case: for a decorated function, set the lineno to that of the
    # first decorator, not the `def`. Issue #4984.
    if isinstance(item, ast.FunctionDef) and item.decorator_list:
        lineno = item.decorator_list[0].lineno
    else:
        lineno = item.lineno
    # Now actually insert the special imports.
    aliases = [
        ast.alias("builtins", "@py_builtins", lineno=lineno, col_offset=0),
        ast.alias(
            "_pytest.assertion.rewrite",
            "@pytest_ar",
            lineno=lineno,
            col_offset=0,
        ),
    ]
    imports = [
        ast.Import([alias], lineno=lineno, col_offset=0) for alias in aliases
    ]
    mod.body[pos:pos] = imports

    # Collect asserts.
    self.scope = (mod,)
    nodes: list[ast.AST | Sentinel] = [mod]
    while nodes:
        node = nodes.pop()
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            self.scope = tuple((*self.scope, node))
            nodes.append(_SCOPE_END_MARKER)
        if node == _SCOPE_END_MARKER:
            self.scope = self.scope[:-1]
            continue
        assert isinstance(node, ast.AST)
        for name, field in ast.iter_fields(node):
            if isinstance(field, list):
                new: list[ast.AST] = []
                for i, child in enumerate(field):
                    if isinstance(child, ast.Assert):
                        # Transform assert.
                        new.extend(self.visit(child))
                    else:
                        new.append(child)
                        if isinstance(child, ast.AST):
                            nodes.append(child)
                setattr(node, name, new)
            elif (
                isinstance(field, ast.AST)
                # Don't recurse into expressions as they can't contain
                # asserts.
                and not isinstance(field, ast.expr)
            ):
                nodes.append(field)