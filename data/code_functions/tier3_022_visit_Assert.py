# Source : https://github.com/pytest-dev/pytest/blob/main/src/_pytest/assertion/rewrite.py (line 854)
# License: MIT
# Complexity: 15
# Tier   : tier3

def visit_Assert(self, assert_: ast.Assert) -> list[ast.stmt]:
    """Return the AST statements to replace the ast.Assert instance.

    This rewrites the test of an assertion to provide
    intermediate values and replace it with an if statement which
    raises an assertion error with a detailed explanation in case
    the expression is false.
    """
    if isinstance(assert_.test, ast.Tuple) and len(assert_.test.elts) >= 1:
        import warnings

        from _pytest.warning_types import PytestAssertRewriteWarning

        # TODO: This assert should not be needed.
        assert self.module_path is not None
        warnings.warn_explicit(
            PytestAssertRewriteWarning(
                "assertion is always true, perhaps remove parentheses?"
            ),
            category=None,
            filename=self.module_path,
            lineno=assert_.lineno,
        )

    self.statements: list[ast.stmt] = []
    self.variables: list[str] = []
    self.variable_counter = itertools.count()

    if self.enable_assertion_pass_hook:
        self.format_variables: list[str] = []

    self.stack: list[dict[str, ast.expr]] = []
    self.expl_stmts: list[ast.stmt] = []
    self.push_format_context()
    # Rewrite assert into a bunch of statements.
    top_condition, explanation = self.visit(assert_.test)

    negation = ast.UnaryOp(ast.Not(), top_condition)

    if self.enable_assertion_pass_hook:  # Experimental pytest_assertion_pass hook
        msg = self.pop_format_context(ast.Constant(explanation))

        # Failed
        if assert_.msg:
            assertmsg = self.helper("_format_assertmsg", assert_.msg)
            gluestr = "\n>assert "
        else:
            assertmsg = ast.Constant("")
            gluestr = "assert "
        err_explanation = ast.BinOp(ast.Constant(gluestr), ast.Add(), msg)
        err_msg = ast.BinOp(assertmsg, ast.Add(), err_explanation)
        err_name = ast.Name("AssertionError", ast.Load())
        fmt = self.helper("_format_explanation", err_msg)
        exc = ast.Call(err_name, [fmt], [])
        raise_ = ast.Raise(exc, None)
        statements_fail = []
        statements_fail.extend(self.expl_stmts)
        statements_fail.append(raise_)

        # Passed
        fmt_pass = self.helper("_format_explanation", msg)
        orig = _get_assertion_exprs(self.source)[assert_.lineno]
        hook_call_pass = ast.Expr(
            self.helper(
                "_call_assertion_pass",
                ast.Constant(assert_.lineno),
                ast.Constant(orig),
                fmt_pass,
            )
        )
        # If any hooks implement assert_pass hook
        hook_impl_test = ast.If(
            self.helper("_check_if_assertion_pass_impl"),
            [*self.expl_stmts, hook_call_pass],
            [],
        )
        statements_pass: list[ast.stmt] = [hook_impl_test]

        # Test for assertion condition
        main_test = ast.If(negation, statements_fail, statements_pass)
        self.statements.append(main_test)
        if self.format_variables:
            variables: list[ast.expr] = [
                ast.Name(name, ast.Store()) for name in self.format_variables
            ]
            clear_format = ast.Assign(variables, ast.Constant(None))
            self.statements.append(clear_format)

    else:  # Original assertion rewriting
        # Create failure message.
        body = self.expl_stmts
        self.statements.append(ast.If(negation, body, []))
        if assert_.msg:
            assertmsg = self.helper("_format_assertmsg", assert_.msg)
            explanation = "\n>assert " + explanation
        else:
            assertmsg = ast.Constant("")
            explanation = "assert " + explanation
        template = ast.BinOp(assertmsg, ast.Add(), ast.Constant(explanation))
        msg = self.pop_format_context(template)
        fmt = self.helper("_format_explanation", msg)
        err_name = ast.Name("AssertionError", ast.Load())
        exc = ast.Call(err_name, [fmt], [])
        raise_ = ast.Raise(exc, None)

        body.append(raise_)

    # Clear temporary variables by setting them to None.
    if self.variables:
        variables = [ast.Name(name, ast.Store()) for name in self.variables]
        clear = ast.Assign(variables, ast.Constant(None))
        self.statements.append(clear)
    # Fix locations (line numbers/column offsets).
    for stmt in self.statements:
        for node in traverse_node(stmt):
            if getattr(node, "lineno", None) is None:
                # apply the assertion location to all generated ast nodes without source location
                # and preserve the location of existing nodes or generated nodes with an correct location.
                ast.copy_location(node, assert_)
    return self.statements