# Source : https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/sql/compiler.py (line 3159)
# License: MIT
# Complexity: 13
# Tier   : tier3

def visit_compound_select(
    self, cs, asfrom=False, compound_index=None, **kwargs
):
    if self._collect_params:
        self._add_to_params(cs)
    toplevel = not self.stack

    compile_state = cs._compile_state_factory(cs, self, **kwargs)

    if toplevel and not self.compile_state:
        self.compile_state = compile_state

    compound_stmt = compile_state.statement

    entry = self._default_stack_entry if toplevel else self.stack[-1]
    need_result_map = toplevel or (
        not compound_index
        and entry.get("need_result_map_for_compound", False)
    )

    # indicates there is already a CompoundSelect in play
    if compound_index == 0:
        entry["select_0"] = cs

    self.stack.append(
        {
            "correlate_froms": entry["correlate_froms"],
            "asfrom_froms": entry["asfrom_froms"],
            "selectable": cs,
            "compile_state": compile_state,
            "need_result_map_for_compound": need_result_map,
        }
    )

    if compound_stmt._independent_ctes:
        self._dispatch_independent_ctes(compound_stmt, kwargs)

    keyword = self.compound_keywords[cs.keyword]

    text = (" " + keyword + " ").join(
        (
            c._compiler_dispatch(
                self, asfrom=asfrom, compound_index=i, **kwargs
            )
            for i, c in enumerate(cs.selects)
        )
    )

    kwargs["include_table"] = False
    text += self.group_by_clause(cs, **dict(asfrom=asfrom, **kwargs))
    text += self.order_by_clause(cs, **kwargs)
    if cs._has_row_limiting_clause:
        text += self._row_limit_clause(cs, **kwargs)

    if self.ctes:
        nesting_level = len(self.stack) if not toplevel else None
        text = (
            self._render_cte_clause(
                nesting_level=nesting_level,
                include_following_stack=True,
            )
            + text
        )

    self.stack.pop(-1)
    return text